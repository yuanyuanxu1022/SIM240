#!/usr/bin/env python3
"""Outer batch driver for already-prepared FVM reference cases.

PURPOSE
    The frozen `run_one.py` launches exactly one case per process and
    explicitly refuses to "advance to another mesh, direction, Gate, retry
    or acceptance assessment".  A multi-level chain (coarse -> mid -> fine
    -> tight) must therefore be driven from OUTSIDE that frozen script.

    This driver bridges the gap WITHOUT touching any frozen file:

      * it invokes the unmodified `run_one.py` once per case via a fresh
        subprocess, exactly as an operator would by hand;
      * it never relaxes an acceptance threshold, never edits case inputs,
        and never re-runs a case that already produced a receipt;
      * it writes a per-case result record (state, exit code, acceptance,
        power balance, K, failure reason) to `batch_results.json` and a
        human-readable log.

FAILURE POLICY (2026-11-12, per operator instruction)
    Default `--continue-on-failure` is ON: a failed case is RECORDED and
    the batch moves on to the next case.  This is an execution-bookkeeping
    convenience only.  It does NOT change any scientific verdict:
      * a case whose receipt reports a non-zero solver exit or a non-accepted
        post-hoc state stays FAILED in the record and in postprocess.assess();
      * a case that cannot start (e.g. its seed source failed acceptance) is
        recorded as LAUNCH_REFUSED with the original exception text, and the
        downstream case is attempted anyway -- it will be refused by the
        frozen seed validation itself, which is the authoritative gate.
    Use `--stop-on-failure` to restore the old halt-at-first-error behaviour.

    IMPORTANT: a failure record is never rewritten to a pass.  The original
    receipt on disk is left untouched.

USAGE
    source /opt/openfoam13/etc/bashrc
    /usr/bin/python3 run_chain.py --chain all_remaining
    /usr/bin/python3 run_chain.py --chain h125_d120_T --dry-run
    /usr/bin/python3 run_chain.py --chain all_remaining --stop-on-failure
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# The frozen release was validated against the system interpreter, which is
# the one carrying numpy 1.26.4.  Never inherit sys.executable here: the
# managed runtime used by interactive tooling has no numpy and would abort
# every case at the postprocessing import.
PYTHON = '/usr/bin/python3'

SERIES = {
    'h125_d120_T': ['h125_d120_T_coarse', 'h125_d120_T_mid',
                    'h125_d120_T_fine', 'h125_d120_T_tight'],
    'h25_d100_T': ['h25_d100_T_tight'],
    # Everything still outstanding after the 2026-11-12 01:39 batch stopped.
    # Order matters: seed source must be attempted before its dependent.
    'all_remaining': ['h25_d100_T_tight',
                      'h125_d120_T_coarse', 'h125_d120_T_mid',
                      'h125_d120_T_fine', 'h125_d120_T_tight'],
}

LOG = ROOT / 'chain_batch.log'
RESULTS = ROOT / 'batch_results.json'


def note(msg: str) -> None:
    line = time.strftime('%Y-%m-%dT%H:%M:%S') + '  ' + msg
    print(line, flush=True)
    with LOG.open('a', encoding='utf-8') as fh:
        fh.write(line + '\n')


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_receipt(case: Path) -> dict:
    for candidate in (case / 'runtime' / 'receipt.json',
                      case / 'referenceEvidence' / 'receipt.json'):
        if candidate.is_file():
            try:
                return json.loads(candidate.read_text())
            except (OSError, ValueError):
                return {}
    return {}


def is_alive(case: Path) -> bool:
    """A running case keeps rewriting log.solver.  If that file has not moved
    for two minutes the process is gone (killed or interrupted)."""
    log = case / 'runtime' / 'log.solver'
    if not log.is_file():
        return False
    try:
        return (time.time() - log.stat().st_mtime) < 120
    except OSError:
        return False


def state(case_id: str) -> dict:
    case = ROOT / 'prepared' / case_id
    runtime = case / 'runtime'
    rec = read_receipt(case)
    out = {'case_id': case_id,
           'exists': case.is_dir(),
           'started': runtime.is_dir(),
           'receipt': bool(rec),
           'exit_code': rec.get('independent_exit_code'),
           'accepted': (rec.get('stopping') or {}).get('post_hoc_acceptance'),
           'run_id': rec.get('run_id')}
    if out['started'] and not out['receipt']:
        out['alive'] = is_alive(case)
    return out


def read_metrics(case_id: str) -> dict:
    """Independent readback via the frozen postprocess module, for the record.
    Absolute paths are mandatory: seed validation compares map_argv strings."""
    try:
        sys.path.insert(0, str(ROOT))
        import postprocess as pp
        rel = digest(ROOT / 'release_manifest.json')
        exe = digest(ROOT / 'bin' / 'paper1StokesReference')
        result = pp.read_case(ROOT / 'prepared' / case_id, rel, exe)
        metrics = result.get('metrics') or {}
        return {'readback_status': result['status'],
                'issues': result.get('issues', []),
                'power_balance_percent': metrics.get('power_balance_percent'),
                'K_m3': metrics.get('K_m3')}
    except Exception as error:  # noqa: BLE001 - record, never mask
        return {'readback_status': 'READBACK_ERROR',
                'issues': [f'{type(error).__name__}: {error}']}


def save_results(rows: list[dict]) -> None:
    RESULTS.write_text(json.dumps(rows, indent=2) + '\n')


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--chain', required=True, choices=sorted(SERIES))
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--stop-on-failure', action='store_true',
                    help='halt at the first failure instead of continuing')
    ap.add_argument('--no-readback', action='store_true',
                    help='skip the independent postprocess readback step')
    args = ap.parse_args()
    keep_going = not args.stop_on_failure

    cases = SERIES[args.chain]
    note(f'chain {args.chain} start; order = {" -> ".join(cases)}; '
         f'failure policy = {"continue" if keep_going else "stop"}')

    rows: list[dict] = []
    for index, case_id in enumerate(cases, 1):
        case = ROOT / 'prepared' / case_id
        tag = f'[{index}/{len(cases)}] {case_id}'
        st = state(case_id)
        row: dict = {'case_id': case_id, 'action': None,
                     'started_at': time.strftime('%Y-%m-%dT%H:%M:%S')}

        if not st['exists']:
            row.update(action='MISSING', verdict='FAILED',
                       reason='prepared directory missing')
            note(f'{tag}: directory missing')
        elif st['receipt']:
            # Already has a receipt.  Never re-run.  Just record what it says.
            row.update(action='SKIP_ALREADY_HAS_RECEIPT',
                       run_id=st['run_id'], solver_exit=st['exit_code'],
                       post_hoc_acceptance=st['accepted'],
                       verdict='ACCEPTED' if (st['exit_code'] == 0
                                              and st['accepted'] == 'accepted')
                       else 'FAILED',
                       reason='existing receipt preserved verbatim')
            note(f'{tag}: receipt already present, exit={st["exit_code"]}, '
                 f'acceptance={st["accepted"]} -> {row["verdict"]}; NOT re-running')
        elif st['started'] and st.get('alive'):
            row.update(action='SKIP_STILL_RUNNING', verdict='RUNNING',
                       reason='log.solver still being written')
            note(f'{tag}: already running; skipping')
        elif st['started']:
            row.update(action='SKIP_INTERRUPTED_RESIDUE', verdict='INCOMPLETE',
                       reason='runtime/ exists without receipt and no live process; '
                              'left untouched for human review, no auto-cleanup')
            note(f'{tag}: interrupted residue without receipt; left untouched')
        else:
            cmd = [PYTHON, str(ROOT / 'run_one.py'), '--case', case_id, '--execute']
            note(f'{tag}: launching {" ".join(cmd)}')
            row['action'] = 'LAUNCH'
            if args.dry_run:
                row.update(verdict='DRY_RUN')
                rows.append(row)
                save_results(rows)
                continue
            started = time.time()
            proc = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)
            elapsed = time.time() - started
            row['elapsed_seconds'] = round(elapsed, 1)
            row['launcher_exit'] = proc.returncode
            if proc.stdout.strip():
                row['stdout_tail'] = proc.stdout.strip().splitlines()[-1]
            if proc.returncode != 0:
                # Launch refused (e.g. seed source not accepted, evidence exists).
                row.update(verdict='LAUNCH_REFUSED',
                           reason=(proc.stderr.strip().splitlines()[-1]
                                   if proc.stderr.strip() else 'non-zero exit'))
                note(f'{tag}: launch refused after {elapsed/60:.1f} min: {row["reason"]}')
            else:
                st = state(case_id)
                row.update(run_id=st['run_id'], solver_exit=st['exit_code'],
                           post_hoc_acceptance=st['accepted'],
                           verdict='ACCEPTED' if (st['exit_code'] == 0
                                                  and st['accepted'] == 'accepted')
                           else 'FAILED',
                           reason='see receipt')
                note(f'{tag}: finished in {elapsed/3600:.2f} h, '
                     f'exit={st["exit_code"]}, acceptance={st["accepted"]} '
                     f'-> {row["verdict"]}')

        if not args.no_readback and row['action'] != 'SKIP_STILL_RUNNING':
            row.update(read_metrics(case_id))
            note(f'{tag}: readback {row.get("readback_status")} '
                 f'power={row.get("power_balance_percent")} K={row.get("K_m3")}')

        rows.append(row)
        save_results(rows)

        failed = row.get('verdict') in ('FAILED', 'LAUNCH_REFUSED',
                                        'INCOMPLETE', 'READBACK_ERROR')
        if failed and not keep_going:
            note(f'{tag}: failure policy is stop; halting chain')
            note(f'results written to {RESULTS}')
            return 1

    summary = {
        'chain': args.chain,
        'finished_at': time.strftime('%Y-%m-%dT%H:%M:%S'),
        'total': len(rows),
        'accepted': sum(1 for r in rows if r.get('verdict') == 'ACCEPTED'),
        'failed': sum(1 for r in rows if r.get('verdict') in
                      ('FAILED', 'LAUNCH_REFUSED', 'INCOMPLETE')),
        'running': sum(1 for r in rows if r.get('verdict') == 'RUNNING'),
    }
    note(f'chain complete: {summary}')
    note(f'results written to {RESULTS}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

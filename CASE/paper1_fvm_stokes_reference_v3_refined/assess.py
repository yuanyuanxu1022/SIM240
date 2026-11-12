#!/usr/bin/env python3
"""Accept a refined case, and compare it against the v2 fine level it replaces.

WHY NOT postprocess.read_case()
    v2's validate_seed() enforces a canonical coarse->mid->fine->tight chain
    with `levels` differing by exactly one, and resolves `seed_from` relative
    to the case's own parent directory.  A refined case is seeded from the v2
    *fine* level on a *different* mesh, in a different study tree, so that
    chain validator would reject it for structural reasons that say nothing
    about correctness.  This script therefore re-derives the verdict from the
    same frozen primitives instead of reusing the chain validator:
        pp.metrics()      -> K, power balance, section fluxes
        pp.steady_stop()  -> convergence, using the identical v2.1 RULE
    plus the 0.1 % ceilings, applied EXPLICITLY.

    Nothing is waived.  In particular, v2 applies its 0.1 % ceilings only when
    level is fine/tight/flat; our level is `refined`, which that branch would
    skip.  Renaming a level must never amount to a waiver, so the ceilings are
    re-applied here by hand.

USAGE
    /usr/bin/python3 assess.py --case h25_d100_T_refined
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
V2 = ROOT.parent / 'paper1_fvm_stokes_reference_v2'
sys.path.insert(0, str(V2))
import postprocess as pp  # noqa: E402

CEILINGS = dict(power_balance_percent=0.1,
                section_flux_spread_percent=0.1,
                section_vs_volume_percent=0.1)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--case', required=True)
    ap.add_argument('--output', type=Path)
    args = ap.parse_args()

    case = (ROOT / 'prepared' / args.case).resolve()
    meta = json.loads((case / 'case.json').read_text())
    manifest = json.loads((ROOT / 'prepared_manifest.json').read_text())
    receipt_path = case / 'runtime/receipt.json'
    if not receipt_path.is_file():
        raise SystemExit('no receipt yet; the case has not finished')
    receipt = json.loads(receipt_path.read_text())
    evidence = case / 'referenceEvidence'
    log_path = case / 'runtime/log.solver'

    problems: list[str] = []
    values: dict = {}
    stop: dict = {}

    if not log_path.is_file():
        problems.append('solver log missing')
    else:
        log_text = log_path.read_text()
        if (evidence / 'cells.csv').is_file():
            try:
                rows = pp.csv_float(evidence / 'cells.csv')
                amps = pp.amplitudes(rows)
                faces = pp.csv_float(evidence / 'x_faces.csv') if meta['direction'] == 'T' else []
                values = pp.metrics(meta, rows, faces)
                stop = pp.steady_stop(log_text, meta, manifest['acceptance_rule'],
                                      receipt.get('independent_exit_code'), amps, values)
            except (ValueError, KeyError, OSError) as error:
                problems.append(f'metrics could not be computed: {error}')
        else:
            problems.append('no referenceEvidence/cells.csv; nothing to accept')

    if stop:
        if stop.get('post_hoc_acceptance') != 'accepted':
            problems.extend(stop.get('reasons', ['stopping criterion not accepted']))
        stated = receipt.get('stopping') or {}
        if stated and stated != stop:
            problems.append('recorded stopping block disagrees with independent re-parse')

    # Explicit ceilings (see module docstring).
    for key, ceiling in CEILINGS.items():
        value = values.get(key)
        if value is None:
            problems.append(f'{key}: missing, cannot be verified')
        elif value > ceiling:
            problems.append(f'{key} = {value:.6f} % exceeds {ceiling} %')

    # Mesh-independent identity: the refined case must reproduce the geometry
    # it claims to refine, otherwise the comparison below would be meaningless.
    supersedes = meta.get('supersedes')
    comparison = None
    if supersedes:
        old_case = (V2 / 'prepared' / supersedes).resolve()
        old_meta = json.loads((old_case / 'case.json').read_text())
        for key in ('h_nm', 'd_nm', 'w_nm', 'P_nm', 'direction',
                    'nu_m2_s', 'acceleration_m_s2', 'Aplan_m2'):
            if old_meta[key] != meta[key]:
                problems.append(f'geometry/physics mismatch vs v2 fine: {key}')
        old_ev = old_case / 'referenceEvidence'
        if (old_ev / 'cells.csv').is_file():
            old_rows = pp.csv_float(old_ev / 'cells.csv')
            old_faces = pp.csv_float(old_ev / 'x_faces.csv') if old_meta['direction'] == 'T' else []
            old_values = pp.metrics(old_meta, old_rows, old_faces)
            k_old, k_new = old_values.get('K_m3'), values.get('K_m3')
            comparison = dict(
                v2_case=supersedes,
                v2_dx_nm=old_meta['dx_nm'], v2_cells=old_meta['expected_cells'],
                v2_power_balance_percent=old_values.get('power_balance_percent'),
                v2_K_m3=k_old,
                refined_dx_nm=meta['dx_nm'], refined_cells=meta['expected_cells'],
                refined_power_balance_percent=values.get('power_balance_percent'),
                refined_K_m3=k_new,
                K_change_percent=(abs(k_new / k_old - 1) * 100 if k_old and k_new else None))

    accepted = not problems
    report = dict(case_id=args.case,
                  level=meta['level'], dx_nm=meta['dx_nm'],
                  cells=meta['expected_cells'],
                  run_id=receipt.get('run_id'),
                  solver_exit=receipt.get('independent_exit_code'),
                  seeded_from=receipt.get('seed', {}).get('seed_from'),
                  convergence=stop.get('post_hoc_acceptance'),
                  stop_reason=stop.get('actual_stop_reason'),
                  ceilings_applied=CEILINGS,
                  accepted=accepted,
                  problems=problems,
                  metrics=values,
                  grid_comparison=comparison,
                  note='Accepted only under the SAME 0.1 % ceilings that the v2 '
                       'fine level failed.  No threshold relaxed, no FAIL rewritten.')
    text = json.dumps(report, indent=2)
    print(text)
    if args.output:
        args.output.write_text(text + '\n')
    return 0 if accepted else 1


if __name__ == '__main__':
    raise SystemExit(main())

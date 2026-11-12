#!/usr/bin/env python3
"""Run one refined-mesh case and record a receipt.  Never rewrites a receipt.

The numerical work is done by the SAME solver binary as the frozen v2 release,
and the stopping decision is made by the SAME postprocess.steady_stop parser
with the SAME acceptance rule.  Only the mesh is new.

    source /opt/openfoam13/etc/bashrc
    /usr/bin/python3 run.py --case h25_d100_T_refined --execute

Exit code is 0 when the solver finished and the receipt was written, 1 when
the run was refused or the solver failed.  A refused/failed run is recorded,
never silently retried.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import resource
import signal
import subprocess
import sys
import time
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent
V2 = ROOT.parent / 'paper1_fvm_stokes_reference_v2'
FOAM_BIN = Path('/opt/openfoam13/platforms/linux64GccDPInt32Opt/bin')
SOLVER = V2 / 'bin/paper1StokesReference'

sys.path.insert(0, str(V2))
import postprocess as pp  # noqa: E402


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def limits() -> None:
    # 8 GB address space: the refined h125 case is estimated near 2.2 GB, and
    # the v2 cap of 4 GB would be too tight for it.  File size stays bounded.
    resource.setrlimit(resource.RLIMIT_AS, (8 * 1024**3, 8 * 1024**3))
    resource.setrlimit(resource.RLIMIT_FSIZE, (1024 * 1024**2, 1024 * 1024**2))
    os.nice(5)


def command(args: list, log: Path, seconds: int, env: dict) -> dict:
    started = time.monotonic()
    with log.open('xb') as stream:
        proc = subprocess.Popen(args, stdout=stream, stderr=subprocess.STDOUT,
                                env=env, start_new_session=True, preexec_fn=limits)
        try:
            code = proc.wait(timeout=seconds)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGKILL)
            proc.wait()
            code = 124
    return dict(argv=[str(a) for a in args], independent_exit_code=code,
                elapsed_seconds=time.monotonic() - started, wall_limit_seconds=seconds)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--case', required=True)
    ap.add_argument('--execute', action='store_true')
    args = ap.parse_args()
    if not args.execute:
        ap.error('--execute is required; preparation alone never launches a solver')

    if os.environ.get('WM_PROJECT_VERSION') != '13':
        raise RuntimeError('source /opt/openfoam13/etc/bashrc first')

    manifest_path = ROOT / 'prepared_manifest.json'
    manifest = json.loads(manifest_path.read_text())
    for rel, expected in manifest['sha256'].items():
        path = ROOT / rel
        if not path.is_file() or digest(path) != expected:
            raise RuntimeError('prepared input drift: ' + rel)
    if digest(SOLVER) != manifest['solver_sha256']:
        raise RuntimeError('solver binary drift; refusing to run')

    case = ROOT / 'prepared' / args.case
    if not case.is_dir():
        raise RuntimeError('unknown case: ' + args.case)
    runtime = case / 'runtime'
    evidence = case / 'referenceEvidence'
    if runtime.exists() or evidence.exists():
        raise RuntimeError('previous run exists; no overwrite, resume or retry.  '
                           'Archive the old directory first if a re-run is intended.')

    meta = json.loads((case / 'case.json').read_text())
    rule = pp.acceptance_rule(case)  # also asserts metadata matches the plan

    runtime.mkdir()
    run_id = args.case + '_' + time.strftime('%Y%m%dT%H%M%S') + '_' + uuid.uuid4().hex[:8]
    env = os.environ.copy()
    env.update(OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1')
    receipt = dict(run_id=run_id, case_id=args.case,
                   study='v3_refined_mesh_remedy',
                   solver_sha256=manifest['solver_sha256'],
                   solver_path=str(SOLVER),
                   openfoam_version=env['WM_PROJECT_VERSION'],
                   execution_scope='this case only',
                   solver_converged=False, commands=[])
    (runtime / 'started.json').write_text(json.dumps(receipt, indent=2) + '\n')
    (runtime / 'prepared_manifest_snapshot.json').write_bytes(manifest_path.read_bytes())

    for tool in ('blockMesh', 'checkMesh'):
        info = command([str(FOAM_BIN / tool), '-case', str(case)],
                       runtime / ('log.' + tool), 600, env)
        receipt['commands'].append(info)
        if info['independent_exit_code'] != 0:
            (runtime / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
            raise RuntimeError(tool + ' failed; no solver launched')
    if 'Mesh OK.' not in (runtime / 'log.checkMesh').read_text():
        raise RuntimeError('checkMesh has no Mesh OK; stop')

    if meta.get('seed_from'):
        source = Path(meta['seed_from'])
        src_receipt_path = source / 'runtime/receipt.json'
        src_receipt = json.loads(src_receipt_path.read_text())
        if digest(src_receipt_path) != meta['seed_source_receipt_sha256']:
            raise RuntimeError('seed source receipt drifted since preparation')
        src_meta = json.loads((source / 'case.json').read_text())
        if any(src_meta[k] != meta[k] for k in ('h_nm', 'd_nm', 'direction')):
            raise RuntimeError('seed geometry mismatch')
        info = command([str(FOAM_BIN / 'mapFields'), str(source), '-case', str(case),
                        '-sourceTime', str(meta['seed_time']), '-consistent',
                        '-mapMethod', 'interpolate', '-noFunctionObjects'],
                       runtime / 'log.mapFields', 1800, env)
        receipt['commands'].append(info)
        if info['independent_exit_code'] != 0:
            (runtime / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
            raise RuntimeError('mapFields failed; no solver launched')
        target = case / ('%.6g' % meta['start_time'])
        names = ('v',) if meta['direction'] == 'P' else ('U', 'p')
        for name in names:
            if not (target / name).is_file():
                raise RuntimeError('seeded field was not written: ' + name)
        preserved = runtime / 'seed_inputs'
        preserved.mkdir()
        for name in names:
            (preserved / name).write_bytes((target / name).read_bytes())
        info2 = command([str(FOAM_BIN / 'checkMesh'), '-case', str(case)],
                        runtime / 'log.checkMesh.seeded', 600, env)
        receipt['commands'].append(info2)
        if 'Mesh OK.' not in (runtime / 'log.checkMesh.seeded').read_text():
            raise RuntimeError('seeded mesh check failed')
        receipt['seed'] = dict(seed_from=str(source), source_time=str(meta['seed_time']),
                               source_run_id=src_receipt.get('run_id'),
                               source_receipt_sha256=meta['seed_source_receipt_sha256'],
                               source_final_field_sha256=src_receipt.get('native_field_sha256'),
                               target_time=meta['start_time'],
                               target_field_sha256={n: digest(target / n) for n in names},
                               map_exit_code=info['independent_exit_code'],
                               map_log_sha256=digest(runtime / 'log.mapFields'),
                               note='Initial field only; steady Stokes has a unique '
                                    'solution, so this sets the iteration count, not '
                                    'the answer.  Acceptance metrics are recomputed '
                                    'from the refined-mesh field.')

    info = command(['/usr/bin/time', '-v', '-o', str(runtime / 'resource.txt'),
                    str(SOLVER), '-case', str(case)],
                   runtime / 'log.solver', int(meta['wall_clock_seconds']), env)
    receipt['commands'].append(info)
    receipt['independent_exit_code'] = info['independent_exit_code']
    (runtime / 'exit_code.txt').write_text(str(info['independent_exit_code']) + '\n')

    log_text = (runtime / 'log.solver').read_text()
    values = None
    amps = None
    if (evidence / 'cells.csv').exists():
        try:
            rows = pp.csv_float(evidence / 'cells.csv')
            amps = pp.amplitudes(rows)
            faces = pp.csv_float(evidence / 'x_faces.csv') if meta['direction'] == 'T' else []
            values = pp.metrics(meta, rows, faces)
        except (ValueError, KeyError, OSError) as error:
            receipt['metrics_error'] = f'{type(error).__name__}: {error}'
    stop = pp.steady_stop(log_text, meta, rule, info['independent_exit_code'], amps, values)
    receipt['stopping'] = stop
    receipt['solver_converged'] = stop['post_hoc_acceptance'] == 'accepted'
    if values:
        receipt['metrics'] = {k: values[k] for k in
                              ('K_m3', 'J_m2_s', 'power_balance_percent',
                               'section_flux_spread_percent', 'section_vs_volume_percent')
                              if k in values}
    receipt['native_field_sha256'] = {}
    times = []
    for entry in case.iterdir():
        if entry.is_dir():
            try:
                times.append((float(entry.name), entry))
            except ValueError:
                continue
    if times:
        final = sorted(times)[-1][1]
        for name in (('v',) if meta['direction'] == 'P' else ('U', 'p', 'phi')):
            path = final / name
            if path.is_file():
                receipt['native_field_sha256'][str(path.relative_to(case))] = digest(path)
    receipt['runtime_logs_sha256'] = {p.name: digest(p) for p in runtime.iterdir()
                                      if p.is_file() and p.name not in
                                      ('started.json', 'receipt.json')}
    (runtime / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    if evidence.exists():
        (evidence / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')

    print(json.dumps(dict(run_id=run_id,
                          case_id=args.case,
                          dx_nm=meta['dx_nm'],
                          cells=meta['expected_cells'],
                          exit_code=info['independent_exit_code'],
                          solver_converged=receipt['solver_converged'],
                          actual_stop_reason=stop['actual_stop_reason'],
                          post_hoc_acceptance=stop['post_hoc_acceptance'],
                          power_balance_percent=values['power_balance_percent'] if values else None,
                          K_m3=values['K_m3'] if values else None), indent=2))
    return 0 if info['independent_exit_code'] == 0 else 1


if __name__ == '__main__':
    raise SystemExit(main())

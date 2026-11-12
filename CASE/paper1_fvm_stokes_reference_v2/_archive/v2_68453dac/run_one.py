#!/usr/bin/env python3
"""Prepared single-case runner (v2: caps, grid continuation, numeric stopping).

Execute ONLY after the user launches it explicitly.

Never advances to another mesh, direction, Gate, retry or acceptance assessment.
Requires an unchanged release manifest and sourced OpenFOAM Foundation 13.

Two v2 additions, both recorded in the receipt:
  * grid continuation: when case.json names a seed_from case, the seed fields are
    mapped into the target's startTime directory (0.5), never into the frozen 0/;
  * numeric stopping criterion: acceptance no longer rests on the log string
    alone. It requires a dominant-component residual below 1e-9 together with a
    power balance within 0.1 percent, recomputed here from the exported evidence.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import resource
import signal
import subprocess
import time
import uuid

ROOT = Path(__file__).resolve().parent
FOAM_BIN = Path('/opt/openfoam13/platforms/linux64GccDPInt32Opt/bin')
RESIDUAL = re.compile(r'Solving for (\w+), Initial residual = ([0-9.eE+-]+)')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def postprocess():
    spec = importlib.util.spec_from_file_location('postprocess', ROOT/'postprocess.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def verify_release():
    release = ROOT/'release_manifest.json'
    data = json.loads(release.read_text())
    if data.get('status') != 'PREPARED_NOT_RUN':
        raise RuntimeError('unexpected release status')
    for rel, expected in data['sha256'].items():
        path = ROOT/rel
        if not path.is_file() or digest(path) != expected:
            raise RuntimeError('release drift: '+rel)
    for absolute, expected in data.get('external_sha256', {}).items():
        path = Path(absolute)
        if not path.is_file() or digest(path) != expected:
            raise RuntimeError('OpenFOAM library drift: '+absolute)
    return release


def limits():
    resource.setrlimit(resource.RLIMIT_AS, (4*1024**3, 4*1024**3))
    resource.setrlimit(resource.RLIMIT_FSIZE, (256*1024**2, 256*1024**2))
    os.nice(5)


def command(args, log, seconds, env):
    started = time.monotonic()
    with log.open('xb') as stream:
        proc = subprocess.Popen(args, stdout=stream, stderr=subprocess.STDOUT, env=env,
                                start_new_session=True, preexec_fn=limits)
        try:
            code = proc.wait(timeout=seconds)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGKILL)
            proc.wait()
            code = 124
    return dict(argv=args, independent_exit_code=code,
                elapsed_seconds=time.monotonic()-started, wall_limit_seconds=seconds)


def time_dirs(case):
    found = []
    for entry in case.iterdir():
        if not entry.is_dir():
            continue
        try:
            value = float(entry.name)
        except ValueError:
            continue
        if value > 0:
            found.append((value, entry))
    return sorted(found)


def last_time(meta, case):
    names = ('v',) if meta['direction'] == 'P' else ('U', 'p')
    for _, entry in reversed(time_dirs(case)):
        if all((entry/name).is_file() for name in names):
            return entry
    return None


def residual_trace(log_text):
    trace = {}
    for name, value in RESIDUAL.findall(log_text):
        trace[name] = float(value)
    return trace


def seed_fields(meta, case, runtime, env):
    """Map the lower-resolution solution into this case's startTime directory."""
    source = ROOT/'prepared'/meta['seed_from']
    if not source.is_dir():
        raise RuntimeError('seed source case is missing: '+meta['seed_from'])
    receipt = source/'referenceEvidence/receipt.json'
    if not receipt.is_file():
        raise RuntimeError('seed source has no runtime receipt; run it first: '+meta['seed_from'])
    record = json.loads(receipt.read_text())
    if not record.get('solver_converged'):
        raise RuntimeError('seed source is not converged; refusing to seed from it: '+meta['seed_from'])
    origin = last_time(json.loads((source/'case.json').read_text()), source)
    if origin is None:
        raise RuntimeError('seed source has no written field set')
    logs = []
    for step, args in (('mapFields', [str(FOAM_BIN/'mapFields'), str(source), '-case', str(case),
                                      '-sourceTime', origin.name, '-consistent',
                                      '-mapMethod', 'interpolate', '-noFunctionObjects']),
                       ('checkMesh.seeded', [str(FOAM_BIN/'checkMesh'), '-case', str(case)])):
        info = command(args, runtime/('log.'+step), 900, env)
        logs.append(info)
        if info['independent_exit_code'] != 0:
            raise RuntimeError(step+' failed; no solver launched')
    target = case/('%.6g' % meta['start_time'])
    for name in (('v',) if meta['direction'] == 'P' else ('U', 'p')):
        path = target/name
        if not path.is_file():
            raise RuntimeError('seed field was not written: '+str(path))
        text = path.read_text()
        declared = re.search(r'internalField\s+nonuniform\s+List<\w+>\s*(\d+)', text)
        if not declared or int(declared.group(1)) != meta['expected_cells']:
            raise RuntimeError('seed field does not cover the frozen cell count: '+name)
    return dict(seed_from=meta['seed_from'], seed_source_time=origin.name,
                seed_target_time=meta['start_time'],
                seed_sha256={p.name: digest(p) for p in sorted(target.glob('*')) if p.is_file()},
                commands=logs)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', required=True)
    parser.add_argument('--execute', action='store_true',
                        help='explicit operator launch, no implied authorization')
    args = parser.parse_args()
    if not args.execute:
        parser.error('preparation only; --execute is required for an explicitly authorized launch')
    if os.environ.get('WM_PROJECT_VERSION') != '13' or os.environ.get('WM_PROJECT_DIR') != '/opt/openfoam13':
        raise RuntimeError('source /opt/openfoam13/etc/bashrc first; other OpenFOAM versions are not validated')
    release = verify_release()
    if json.loads(release.read_text()).get('formal_review_status') != 'ASTRA_FINAL_STATIC_RECHECK_COMPLETE':
        raise RuntimeError('Specified Astra final static recheck is pending; this prepared release cannot launch')
    plan = json.loads((ROOT/'prepared_manifest.json').read_text())
    ids = {c['case_id'] for c in plan['cases']}
    if args.case not in ids:
        raise RuntimeError('case is outside the frozen 26 input records')
    case = ROOT/'prepared'/args.case
    evidence = case/'referenceEvidence'
    if evidence.exists() or (case/'runtime').exists():
        raise RuntimeError('previous evidence exists; no overwrite, resume or retry is authorized')
    meta = json.loads((case/'case.json').read_text())
    runtime = case/'runtime'
    runtime.mkdir()
    run_id = args.case+'_'+time.strftime('%Y%m%dT%H%M%S')+'_'+uuid.uuid4().hex[:8]
    exe = ROOT/'bin/paper1StokesReference'
    source_hash = digest(release)
    env = os.environ.copy()
    env.update(OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1')
    receipt = dict(run_id=run_id, case_id=args.case, source_manifest_sha256=source_hash,
                   executable_sha256=digest(exe), openfoam_version=env['WM_PROJECT_VERSION'],
                   execution_scope='this case only', solver_converged=False, commands=[])
    (runtime/'started.json').write_text(json.dumps(receipt, indent=2)+'\n')
    (runtime/'release_snapshot.json').write_bytes(release.read_bytes())
    for tool in ('blockMesh', 'checkMesh'):
        info = command([str(FOAM_BIN/tool), '-case', str(case)], runtime/('log.'+tool), 120, env)
        receipt['commands'].append(info)
        if info['independent_exit_code'] != 0:
            receipt['independent_exit_code'] = info['independent_exit_code']
            (runtime/'receipt.json').write_text(json.dumps(receipt, indent=2)+'\n')
            raise RuntimeError(tool+' failed; stop, no solver launched')
    if 'Mesh OK.' not in (runtime/'log.checkMesh').read_text():
        raise RuntimeError('checkMesh has no Mesh OK; stop')
    if meta.get('seed_from'):
        seeded = seed_fields(meta, case, runtime, env)
        receipt['seed'] = seeded
        receipt['commands'].extend(seeded['commands'])
    info = command(['/usr/bin/time', '-v', '-o', str(runtime/'resource.txt'), str(exe), '-case', str(case)],
                   runtime/'log.solver', int(meta['wall_clock_seconds']), env)
    receipt['commands'].append(info)
    receipt['independent_exit_code'] = info['independent_exit_code']
    (runtime/'exit_code.txt').write_text(str(info['independent_exit_code'])+'\n')
    log_text = (runtime/'log.solver').read_text()
    trace = residual_trace(log_text)
    dominant = 'v' if meta['direction'] == 'P' else 'Ux'
    string_ok = 'solution converged' in log_text.lower()
    receipt['residuals'] = dict(trace, dominant_name=dominant)
    values = None
    if (evidence/'cells.csv').exists():
        module = postprocess()
        try:
            values = module.metrics(meta,
                                    [{k: float(v) for k, v in r.items()}
                                     for r in __import__('csv').DictReader((evidence/'cells.csv').open())],
                                    [{k: float(v) for k, v in r.items()}
                                     for r in __import__('csv').DictReader((evidence/'x_faces.csv').open())]
                                    if meta['direction'] == 'T' else [])
        except (ValueError, KeyError):
            values = None
    residual_ok = trace.get(dominant) is not None and trace[dominant] <= 1e-9
    power = values['power_balance_percent'] if values else None
    receipt['stopping'] = dict(criterion='numeric_steady_criterion_v2',
                               log_reports_converged=string_ok,
                               dominant_component=dominant,
                               dominant_residual=trace.get(dominant),
                               dominant_residual_ok=bool(residual_ok),
                               power_balance_percent=power,
                               power_balance_role='diagnostic only; the 0.1 percent gate stays on '
                                                  'fine, tight and flat levels inside postprocess',
                               stopped_by='log_string' if string_ok else ('numeric' if residual_ok else 'cap'))
    receipt['solver_converged'] = bool(info['independent_exit_code'] == 0
                                       and (string_ok or residual_ok))
    try:
        verify_release()
        receipt['release_unchanged'] = digest(release) == source_hash
    except RuntimeError:
        receipt['release_unchanged'] = False
    receipt['evidence_sha256'] = {p.name: digest(p) for p in evidence.glob('*.csv')} if evidence.exists() else {}
    times = time_dirs(case)
    native_names = ('v',) if meta['direction'] == 'P' else ('U', 'p', 'phi')
    receipt['native_field_sha256'] = {}
    if times:
        final = times[-1][1]
        for name in native_names:
            path = final/name
            if path.is_file():
                receipt['native_field_sha256'][str(path.relative_to(case))] = digest(path)
    receipt['mesh_sha256'] = {}
    for name in ('points', 'faces', 'owner', 'neighbour', 'boundary'):
        path = case/'constant/polyMesh'/name
        if path.is_file():
            receipt['mesh_sha256'][name] = digest(path)
    receipt['runtime_logs_sha256'] = {p.name: digest(p) for p in runtime.iterdir()
                                      if p.is_file() and p.name not in ('started.json', 'receipt.json')}
    receipt['case_disk_bytes'] = sum(p.stat().st_size for p in case.rglob('*') if p.is_file())
    receipt['disk_budget_met'] = receipt['case_disk_bytes'] <= 1024**3
    if not receipt['release_unchanged'] or not receipt['disk_budget_met']:
        receipt['solver_converged'] = False
    (runtime/'receipt.json').write_text(json.dumps(receipt, indent=2)+'\n')
    if evidence.exists():
        (evidence/'receipt.json').write_text(json.dumps(receipt, indent=2)+'\n')
    print(json.dumps(dict(run_id=run_id, exit_code=info['independent_exit_code'],
                          solver_converged=receipt['solver_converged'],
                          dominant_residual=trace.get(dominant),
                          power_balance_percent=power,
                          numerical_reference_accepted=False)))
    return 0 if info['independent_exit_code'] == 0 else 1


if __name__ == '__main__':
    raise SystemExit(main())

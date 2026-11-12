#!/usr/bin/env python3
"""Prepared single-case runner (v2: caps, grid continuation, numeric stopping).

Execute ONLY after the user launches it explicitly.

Never advances to another mesh, direction, Gate, retry or acceptance assessment.
Requires an unchanged release manifest and sourced OpenFOAM Foundation 13.

v2.1: full-field stopping rule shared with offline reader, T-flat-only
zero-component exception, receipt-bound mapping and preserved seed inputs.
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
import shutil
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


def seed_fields(meta, case, runtime, env):
    """Map the lower-resolution solution into this case's startTime directory."""
    source = ROOT/'prepared'/meta['seed_from']
    if not source.is_dir():
        raise RuntimeError('seed source case is missing: '+meta['seed_from'])
    receipt = source/'referenceEvidence/receipt.json'
    if not receipt.is_file():
        raise RuntimeError('seed source has no runtime receipt; run it first: '+meta['seed_from'])
    record = json.loads(receipt.read_text())
    module=postprocess()
    release=ROOT/'release_manifest.json'
    source_meta=json.loads((source/'case.json').read_text())
    if module.read_case(source,digest(release),digest(ROOT/'bin/paper1StokesReference'))['status']!='LOCAL_CHECKS_PASS':
        raise RuntimeError('seed source fails independent readback')
    if any(source_meta[k]!=meta[k] for k in ('h_nm','d_nm','direction')):
        raise RuntimeError('seed geometry mismatch')
    fields=record['native_field_sha256']
    times={str(Path(p).parent) for p in fields}
    if len(times)!=1: raise RuntimeError('seed final time binding missing')
    origin=source/next(iter(times))
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
    preserved=runtime/'seed_inputs';preserved.mkdir()
    names=('v',) if meta['direction']=='P' else ('U','p')
    for name in names: shutil.copyfile(target/name,preserved/name)
    if 'Mesh OK.' not in (runtime/'log.checkMesh.seeded').read_text():
        raise RuntimeError('seeded mesh check failed')
    return dict(seed_from=meta['seed_from'],source_run_id=record['run_id'],
                source_receipt_sha256=digest(receipt),
                source_release_sha256=record['source_manifest_sha256'],
                source_time=origin.name,source_field_sha256=fields,
                source_mesh_sha256=record['mesh_sha256'],
                target_time=meta['start_time'],
                target_field_sha256={name:digest(target/name) for name in names},
                map_tool_path=str(FOAM_BIN/'mapFields'),map_tool_sha256=digest(FOAM_BIN/'mapFields'),
                map_argv=logs[0]['argv'],map_exit_code=logs[0]['independent_exit_code'],
                map_log_sha256=digest(runtime/'log.mapFields'),
                mesh_exit_code=logs[1]['independent_exit_code'],
                mesh_log_sha256=digest(runtime/'log.checkMesh.seeded'),commands=logs)


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
    if meta['d_nm']>0:
        module=postprocess()
        for di in ('P','T'):
            flat=ROOT/'prepared'/f'h75_d0_{di}_flat'
            if module.read_case(flat,digest(release),digest(ROOT/'bin/paper1StokesReference'))['status']!='LOCAL_CHECKS_PASS':
                raise RuntimeError('both current-release flat controls must pass before grooves')
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
    module=postprocess()
    values=None; amps=None
    if (evidence/'cells.csv').exists():
        try:
            rows=module.csv_float(evidence/'cells.csv')
            amps=module.amplitudes(rows)
            values=module.metrics(meta,rows,module.csv_float(evidence/'x_faces.csv') if meta['direction']=='T' else [])
        except (ValueError,KeyError,OSError):
            values=None
    rule=module.acceptance_rule(case)
    stop=module.steady_stop(log_text,meta,rule,info['independent_exit_code'],amps,values)
    receipt['stopping']=stop
    receipt['solver_converged']=stop['post_hoc_acceptance']=='accepted'
    power=values['power_balance_percent'] if values else None
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
                          actual_stop_reason=stop['actual_stop_reason'],
                          post_hoc_acceptance=stop['post_hoc_acceptance'],
                          power_balance_percent=power,
                          numerical_reference_accepted=False)))
    return 0 if info['independent_exit_code'] == 0 else 1


if __name__ == '__main__':
    raise SystemExit(main())

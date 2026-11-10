#!/usr/bin/env python3
"""Freeze provenance, build, test arithmetic, and run zero-step precheck only."""
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

CASE = Path(__file__).resolve().parents[1]
ROOT = CASE.parents[2]
BASE = ROOT / 'CASE/03_grid_convergence/G2_EX240_grid_convergence/build/generated/g2_ex240_dx1p25.cpp'
REVIEW = ROOT / 'CASE/reports/fine_T_diagnostic_review_20261013_v1/review.json'
BASE_SHA = '898cbe394a4528ae3ef925002ccb16eb33da433651276457e5913b128174281e'


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b''):
            digest.update(chunk)
    return digest.hexdigest()


def bound(files):
    return all(Path(path).is_file() and sha(Path(path)) == digest
               for path, digest in files.items())


def capture(command, env=None):
    completed = subprocess.run(command, capture_output=True, text=True, env=env)
    return {'command': command, 'exit_code': completed.returncode,
            'stdout': completed.stdout, 'stderr': completed.stderr}


def write_new(path, payload):
    with path.open('x') as stream:
        json.dump(payload, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


def kv(path):
    return dict(line.split('=', 1) for line in path.read_text().splitlines() if '=' in line)


def main():
    destination = CASE / 'reports/build_precheck.json'
    if destination.exists():
        raise FileExistsError('Frozen build evidence already exists')
    review = json.loads(REVIEW.read_text())
    assert sha(BASE) == BASE_SHA == review['baseline_sha256']
    historical = dict(review['historical_inputs'])
    context = ROOT / 'docs/reports/SIM240_AI_CONTEXT.md'
    previous_context_sha = historical.pop(str(context))
    # This is a rolling status document, not a frozen run input. Report its
    # later update explicitly; all actual historical inputs remain hash-bound.
    context_drift = {'path': str(context), 'review_sha256': previous_context_sha,
                     'current_sha256': sha(context)}
    assert bound(historical), 'Frozen historical evidence changed'
    assert bound(review['current_library_files']), 'Reviewed OpenLB library changed'
    own = {str(path): sha(path) for folder in ('src', 'scripts')
           for path in (CASE / folder).iterdir() if path.is_file()}
    own[str(CASE / 'PROTOCOL.md')] = sha(CASE / 'PROTOCOL.md')
    own[str(CASE / 'README.md')] = sha(CASE / 'README.md')
    own[str(CASE / '.gitignore')] = sha(CASE / '.gitignore')

    record = {'time': datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),
              'protocol': 'fine_T_C_v1', 'base_source_sha256': BASE_SHA,
              'source_and_recipe_files': own,
              'historical_inputs': historical,
              'rolling_context_drift': context_drift,
              'current_library_files': review['current_library_files'],
              'OpenLB_HEAD': review['OpenLB_HEAD'],
              'OpenLB_status': review['OpenLB_status'],
              'OpenLB_tracked_diff': review['OpenLB_tracked_diff'],
              'compiler': review['compiler'],
              'environment_basis': 'CONTROLLED_CURRENT_ENVIRONMENT_NOT_HISTORICAL_REBUILD',
              'commands': [], 'time_stepping_started': False,
              'formal_reference_accepted': False, 'run_ready': False}

    with tempfile.TemporaryDirectory(prefix='fine_t_C_arithmetic_') as temporary:
        test_binary = Path(temporary) / 'test_mass_stats'
        test_build = capture(['g++', '-O2', '-Wall', '-Wextra', '-Werror', '-std=c++20',
                              '-I' + str(CASE / 'src'),
                              str(CASE / 'scripts/test_mass_stats.cpp'),
                              '-o', str(test_binary)])
        record['commands'].append(test_build)
        assert test_build['exit_code'] == 0, test_build['stderr']
        test_run = capture([str(test_binary)])
        record['commands'].append(test_run)
        assert test_run['exit_code'] == 0 and 'mass_stats_PASS=true' in test_run['stdout']
        record['arithmetic_test_PASS'] = True

    build = capture(['make', '-C', str(CASE / 'src'), 'compile'])
    record['commands'].append(build)
    assert build['exit_code'] == 0, build['stderr']
    binary = CASE / 'build/fine_T_statfix_C'
    record['binary'] = {'path': str(binary), 'sha256': sha(binary)}
    dependencies = capture(['ldd', str(binary)])
    record['commands'].append(dependencies)
    assert dependencies['exit_code'] == 0
    dynamic_paths = re.findall(r'(?:=>\s*)?(/\S+)\s+\(', dependencies['stdout'])
    record['dynamic_libraries'] = {path: sha(Path(path).resolve()) for path in dynamic_paths}
    available = int(next(line.split()[1] for line in Path('/proc/meminfo').read_text().splitlines()
                         if line.startswith('MemAvailable:'))) * 1024
    free_disk = shutil.disk_usage(CASE).free
    record['resources_before_precheck'] = {'available_RAM_bytes': available,
                                           'disk_free_bytes': free_disk}
    assert available >= 8 * 1024**3 and free_disk >= 2 * 1024**3

    run_id = 'precheck_C_' + datetime.now(ZoneInfo('Asia/Shanghai')).strftime('%Y%m%dT%H%M%S%z')
    run = CASE / 'runs' / run_id
    run.mkdir(parents=True, exist_ok=False)
    write_new(run / 'manifest.json',
              {'run_id': run_id, 'mode': 'precheck', 'direction': 'T',
               'source_files': own, 'binary': record['binary'], 'compute_threads': 1,
               'expected_collide_and_stream_calls': 0})
    with (run / 'run_manifest.txt').open('x') as stream:
        stream.write('run_id=' + run_id + '\nmode=precheck\ndirection=T\n'
                     + 'source_sha=' + sha(CASE / 'src/fine_T_statfix_C.cpp') + '\n')
    env = os.environ.copy()
    env.update({'OMP_NUM_THREADS': '1', 'OPENBLAS_NUM_THREADS': '1'})
    command = [str(binary), 'precheck', 'T', str(run)]
    with (run / 'run.log').open('x') as stream:
        completed = subprocess.run(command, stdout=stream, stderr=subprocess.STDOUT, env=env)
    with (run / 'exit_code.txt').open('x') as stream:
        stream.write(str(completed.returncode) + '\n')
    raw = kv(run / 'result.txt') if (run / 'result.txt').exists() else {}
    checks = [completed.returncode == 0, raw.get('exit_code') == '0',
              raw.get('formal_simulation') == 'false',
              raw.get('collide_and_stream_calls') == '0',
              raw.get('geometry_PASS') == 'true', raw.get('converter_PASS') == 'true',
              raw.get('q_audit_PASS') == 'true', raw.get('fluid_nodes') == '3686400',
              raw.get('candidate_links') == '521472',
              raw.get('installed_links') == '521472',
              raw.get('fallback_count') == '0', raw.get('unresolved_links') == '0']
    checks += [key in raw and abs(float(raw[key]) - 0.5) <= 1.0e-10
               for key in ('q_min', 'q_max')]
    record['precheck'] = {'run_id': run_id, 'directory': str(run), 'command': command,
                          'independent_exit_code': completed.returncode,
                          'result': raw, 'boundary_audit': kv(run / 'boundary_audit.txt')}
    record['precheck_PASS'] = all(checks)
    record['historical_inputs_unchanged'] = bound(historical)
    record['current_library_unchanged'] = bound(review['current_library_files'])
    record['source_and_recipe_unchanged'] = bound(own)
    record['precheck_output_sha256'] = {str(path.relative_to(run)): sha(path)
                                         for path in run.rglob('*') if path.is_file()}
    record['run_ready'] = all([record['precheck_PASS'], record['historical_inputs_unchanged'],
                               record['current_library_unchanged'],
                               record['source_and_recipe_unchanged']])
    write_new(destination, record)
    print(json.dumps({'record': str(destination), 'arithmetic_test_PASS': True,
                      'precheck_PASS': record['precheck_PASS'],
                      'run_ready': record['run_ready'],
                      'formal_reference_accepted': False}, ensure_ascii=False))
    assert record['run_ready'], 'Precheck is not run-ready; inspect frozen record'


if __name__ == '__main__':
    main()

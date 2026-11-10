#!/usr/bin/env python3
"""Prepare one immutable fine-T C run, or execute it only when user invokes --execute."""
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

CASE = Path(__file__).resolve().parents[1]
RECORD = CASE / 'reports/build_precheck.json'


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b''):
            digest.update(chunk)
    return digest.hexdigest()


def check_bound(files):
    for path, digest in files.items():
        if not Path(path).is_file() or sha(Path(path)) != digest:
            raise RuntimeError('Frozen input changed: ' + path)


def write_new(path, content):
    with path.open('x') as stream:
        stream.write(content)


def json_new(path, content):
    write_new(path, json.dumps(content, ensure_ascii=False, indent=2,
                               allow_nan=False) + '\n')


def validate(record):
    if not (record['run_ready'] and record['precheck_PASS']
            and record['historical_inputs_unchanged']
            and record['current_library_unchanged']
            and record['source_and_recipe_unchanged']):
        raise RuntimeError('Build and zero-step precheck were not accepted')
    for key in ('source_and_recipe_files', 'historical_inputs',
                'current_library_files', 'dynamic_libraries'):
        check_bound(record[key])
    check_bound({record['binary']['path']: record['binary']['sha256']})


def prepare(record):
    run_id = 'fine_t_C_' + datetime.now(ZoneInfo('Asia/Shanghai')).strftime('%Y%m%dT%H%M%S%z')
    run = CASE / 'runs' / run_id
    run.mkdir(parents=True, exist_ok=False)
    parameters = {'mesa_gap_nm': 75, 'groove_depth_nm': 100,
                  'groove_width_nm': 120, 'period_nm': 240,
                  'Lx_nm': 240, 'Ly_nm': 240, 'dx_nm': 1.25,
                  'dt_s': 2.604166666666667e-13, 'tau': 1,
                  'rho_kg_m3': 1000, 'nu_m2_s': 1e-6, 'mu_Pa_s': 1e-3,
                  'acceleration_x_m_s2': 1e5, 'ranks': 1,
                  'compute_threads': 1, 'cuboids': 1, 'overlap': 3,
                  'maximum_steps': 60000, 'convergence_window': 1000,
                  'collision': 'ForcedBGK', 'descriptor': 'D3Q19_FORCE',
                  'periodicity': 'x_y', 'wall': 'Bouzidi_zero_velocity_exact_EX240',
                  'corrected_mass_tolerance_strict': 1e-10,
                  'mass_ledger_agreement_tolerance': 1e-13,
                  'density_tolerance': 1e-6, 'Mach_tolerance_strict': 0.05,
                  'section_tolerance': 1e-5, 'cross_flux_tolerance_m2_s': 1e-12,
                  'J_window_std_tolerance': 1e-6, 'J_window_span_tolerance': 5e-6}
    command = [record['binary']['path'], 'steady', 'T', str(run)]
    manifest = {'run_id': run_id, 'mode': 'formal_new_reference',
                'direction': 'T', 'formal_reference_accepted': False,
                'parameters': parameters, 'command': command,
                'environment_overrides': {'OMP_NUM_THREADS': '1',
                                          'OPENBLAS_NUM_THREADS': '1'},
                'source_files': record['source_and_recipe_files'],
                'historical_inputs': record['historical_inputs'],
                'current_library_files': record['current_library_files'],
                'dynamic_libraries': record['dynamic_libraries'],
                'binary': record['binary'], 'build_record_sha256': sha(RECORD),
                'OpenLB_HEAD': record['OpenLB_HEAD'],
                'environment_basis': record['environment_basis']}
    json_new(run / 'manifest.json', manifest)
    write_new(run / 'run_manifest.txt',
              'run_id=' + run_id + '\nmode=formal_new_reference\ndirection=T\n'
              + 'source_sha=' + sha(CASE / 'src/fine_T_statfix_C.cpp') + '\n'
              + 'binary_sha=' + record['binary']['sha256'] + '\n'
              + 'protocol_sha=' + sha(CASE / 'PROTOCOL.md') + '\n'
              + 'formal_reference_accepted=false\n')
    write_new(run / 'RUN_READY.txt',
              'Prepared only. No OpenLB time step has run. User starts this run independently.\n')
    print(json.dumps({'run_id': run_id, 'directory': str(run),
                      'prepared_only': True, 'formal_reference_accepted': False},
                     ensure_ascii=False))


def execute(run_id, record):
    if not re.fullmatch(r'fine_t_C_\d{8}T\d{6}\+0800', run_id):
        raise ValueError('Only an explicitly prepared scheme-C run_id is accepted')
    run = CASE / 'runs' / run_id
    manifest = json.loads((run / 'manifest.json').read_text())
    if (manifest['run_id'] != run_id or manifest['build_record_sha256'] != sha(RECORD)
            or manifest['command'] != [record['binary']['path'], 'steady', 'T', str(run)]
            or manifest['direction'] != 'T' or manifest['mode'] != 'formal_new_reference'):
        raise RuntimeError('Run manifest does not match frozen build')
    for key in ('source_files', 'historical_inputs', 'current_library_files',
                'dynamic_libraries'):
        check_bound(manifest[key])
    check_bound({manifest['binary']['path']: manifest['binary']['sha256']})
    if any((run / name).exists() for name in ('run.log', 'result.txt',
                                              'diagnostics.csv', 'exit_code.txt')):
        raise FileExistsError('Refusing repeated execution')
    available = int(next(line.split()[1] for line in Path('/proc/meminfo').read_text().splitlines()
                         if line.startswith('MemAvailable:'))) * 1024
    if available < 8 * 1024**3 or shutil.disk_usage(run).free < 2 * 1024**3:
        raise RuntimeError('Need at least 8 GiB available RAM and 2 GiB free disk')
    if not Path('/usr/bin/time').is_file():
        raise RuntimeError('/usr/bin/time is required')
    command = ['/usr/bin/time', '-v', '-o', str(run / 'timing.txt'), *manifest['command']]
    env = os.environ.copy()
    env.update(manifest['environment_overrides'])
    print('Starting user-invoked formal run ' + run_id, flush=True)
    with (run / 'run.log').open('x') as stream:
        completed = subprocess.run(command, stdout=stream,
                                   stderr=subprocess.STDOUT, env=env)
    write_new(run / 'exit_code.txt', str(completed.returncode) + '\n')
    evidence = {str(path.relative_to(run)): sha(path)
                for path in run.rglob('*') if path.is_file()}
    json_new(run / 'completion.json',
             {'run_id': run_id, 'independent_exit_code': completed.returncode,
              'output_sha256': evidence, 'formal_reference_accepted': False,
              'scientific_review_required': True})
    print(json.dumps({'run_id': run_id, 'exit_code': completed.returncode,
                      'scientific_review_required': True}, ensure_ascii=False), flush=True)
    return completed.returncode


def main():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--prepare-only', action='store_true')
    group.add_argument('--execute', action='store_true')
    parser.add_argument('--run-id')
    args = parser.parse_args()
    if args.prepare_only and args.run_id:
        parser.error('--prepare-only does not take --run-id')
    if args.execute and not args.run_id:
        parser.error('--execute requires --run-id')
    record = json.loads(RECORD.read_text())
    validate(record)
    if args.prepare_only:
        prepare(record)
    else:
        raise SystemExit(execute(args.run_id, record))


if __name__ == '__main__':
    main()

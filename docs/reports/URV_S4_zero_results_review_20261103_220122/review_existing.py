"""Independent existing-evidence review. Only six saved-field reader subprocesses allowed."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from itertools import repeat
from unittest.mock import patch
import contextlib
import copy
import csv
import io
import json
import math
import os
import resource
import subprocess
import sys
import time
import numpy as np

ROOT = Path('/home/dell/yuanyuanxu/SIM240')
OUT = Path(__file__).resolve().parent
CASE = ROOT / 'CASE/unseen_v2_reference_S4_reuse_v1'
CHECK = ROOT / 'CASE/unseen_v2_reference_checker_S4_reuse_v1'
AUDIT = CASE / 'audits/URV_S4_ZERO_v1_20261103_01'
RELEASE = CASE / 'evidence/S4_zero_launch_release_v1_20261103_01.json'
RELEASE_SHA = 'a62e6f3c96292bec5ab73796789718f28ba2b88232af9f55104697dc30b81d09'
A = CASE / 'evidence/preparation_A.json'
A_SHA = 'e9d12e68eaa324bd8e78ad57825710936f9e00518faf39337923b930ad82a165'
sys.path[:0] = [str(CHECK / 'analysis'), str(CASE / 'scripts')]
from evidence import need, sha, kv, rows, close, exact_parameters, geometry, EvidenceError
import stage_s4 as stage
from zero_evidence_s4 import validate_zero_outputs, validate_initial_readback


def save(path, value):
    with Path(path).open('x') as f:
        json.dump(value, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write('\n')


def load(path):
    return json.loads(Path(path).read_text())


def write_csv(path, records):
    with path.open('x', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)


def scalar_oracles(dx, count):
    # The frozen MRP/A1 scalar paths at rho=1. No historical density replay.
    partial = ((1. * 1000.) * dx) * dx
    volume_term = (dx * dx) * dx
    mass = volume = 0.
    for _ in range(count):
        mass = math.fma(partial, dx, mass)
        volume += volume_term
    return dict(legacy_mass=mass, rounded_volume=volume,
                compensated_mass=math.fsum(repeat(partial * dx, count)))


def double_slice(run, cfg, p):
    data = rows(run / 'field_slice.csv')
    need(len(data) * p['ny'] == p['nodes'], 'slice missing fluid core nodes')
    v = {k: np.array([float(r[k]) for r in data]) for k in data[0]}
    need(all(np.isfinite(a).all() for a in v.values()), 'nonfinite double slice')
    ix = np.rint(v['x'] / p['dx'] - .5).astype(int)
    iz = np.rint(v['z'] / p['dx'] - .5).astype(int)
    need(close(v['x'], (ix + .5) * p['dx']) and close(v['z'], (iz + .5) * p['dx']), 'slice coordinates/units')
    need(len(set(zip(ix, iz))) == len(data), 'duplicate double slice node')
    groove = (v['x'] >= (p['P'] - p['w']) / 2) & (v['x'] < (p['P'] + p['w']) / 2)
    need(np.all((ix >= 0) & (ix < p['nx']) & (v['z'] >= 0) &
                (v['z'] < p['h'] + p['d'] * groove)), 'slice overlaps solid')
    need(np.all(v['material'] == 1) and np.all(v['rho'] == 1) and np.all(v['pressure'] == 0), 'initial rho/material/pressure')
    speed = p['a'] * p['dt'] / 2
    for axis in 'xyz':
        expected = speed if axis == ('y' if cfg['direction'] == 'P' else 'x') else 0.
        need(close(v['u' + axis], expected), 'double slice initial half-force velocity')
    need(close(v['speed'], speed) and np.all(v['Phi'] >= 0), 'slice speed/dissipation')
    for filename, key in [('velocity_profile.csv', 'velocity'), ('pressure_profile.csv', 'pressure'),
                          ('energy_dissipation.csv', 'Phi')]:
        profile = rows(run / filename)
        count = p['ny'] if cfg['direction'] == 'P' else p['nx']
        need(len(profile) == count, 'profile node count')
        position = np.array([float(r['position']) for r in profile])
        value = np.array([float(r[key]) for r in profile])
        need(close(position, (np.arange(count) + .5) * p['dx']) and np.isfinite(value).all(), 'profile positions/finite')
        if key == 'velocity':
            need(close(value, speed), 'profile initial velocity')
        elif key == 'pressure':
            need(np.all(value == 0), 'profile initial pressure')
        else:
            need(np.all(value >= 0), 'negative initial dissipation')
    return dict(double_slice_rows=len(data), rho_min=1., rho_max=1.,
                pressure_min_Pa=0., pressure_max_Pa=0.,
                Phi_min=float(v['Phi'].min()), Phi_max=float(v['Phi'].max()))


def reader_limits():
    resource.setrlimit(resource.RLIMIT_AS, (8 * 1024**3, 8 * 1024**3))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))


def main():
    need(not (CASE / 'evidence/preparation_B.json').exists(), 'B already exists; no overwrite')
    need(not (CASE / 'evidence/preparation_B.sha256').exists(), 'B sidecar already exists')
    for name in ('SIM240_AI_CONTEXT.md', 'AI_HANDOFF_20261015.md'):
        with (OUT / ('before_' + name)).open('xb') as f:
            f.write((ROOT / 'docs/reports' / name).read_bytes())
    bound = stage.verify_seal(RELEASE, RELEASE_SHA)
    stage.validate_zero_authority(bound)
    plan = stage.validate_zero_plan(bound)
    prepared = stage.verify_seal(A, A_SHA)
    need(A.with_suffix('.sha256').read_text().strip() == A_SHA, 'A sidecar changed')
    need(RELEASE.with_suffix('.sha256').read_text().strip() == RELEASE_SHA, 'zero release sidecar changed')
    stage.require_pristine(bound['prepared_runs'])
    need(not (CASE / 'launch_attempts').exists() and not (CASE / 'analysis_results').exists(), 'formal work has already started')
    need((CASE / 'audit_attempts' / RELEASE_SHA).is_dir(), 'authorized audit attempt not recorded')

    protected = dict(bound['inputs_sha256'])
    for directory in (CASE, CHECK, ROOT / 'docs/reports/URV_S4_zero_launch_release_20261103_212632',
                      ROOT / 'docs/reports/URV_S4_zero_status_20261103_214035'):
        for p in directory.rglob('*'):
            if p.is_file() and '__pycache__' not in p.parts:
                need(not p.is_symlink(), 'protected file symlink')
                protected[str(p)] = sha(p)
    save(OUT / 'protected_inputs_and_outputs_before.json', protected)
    for directory in (ROOT / 'docs/reports/URV_S4_zero_launch_release_20261103_212632',
                      ROOT / 'docs/reports/URV_S4_zero_status_20261103_214035'):
        for name, h in load(directory / 'document_manifest.json').items():
            need(sha((ROOT / name) if (ROOT / name).is_file() else (directory / name)) == h, 'prior report changed: ' + name)
    receipt = load(AUDIT / 'verification.json')
    raw = load(receipt['raw_manifest_path'])
    need(sha(receipt['raw_manifest_path']) == receipt['raw_manifest_sha256'], 'raw manifest changed')
    files = {str(p): sha(p) for p in AUDIT.rglob('*') if p.is_file()}
    need({p: h for p, h in files.items() if p not in (str(AUDIT / 'verification.json'),
         str(AUDIT / 'audit_files_sha256.json'))} == raw, 'raw file set/content drift')
    view = copy.deepcopy(prepared)
    view['preparation_A_path'] = str(A)
    view['preparation_A_sha256'] = A_SHA
    view['zero_audit_path'] = str(AUDIT / 'verification.json')
    view['zero_audit_sha256'] = sha(AUDIT / 'verification.json')
    view['inputs_sha256'].update(bound['inputs_sha256'])
    view['inputs_sha256'].update(files)
    for p in (A, A.with_suffix('.sha256'), RELEASE, RELEASE.with_suffix('.sha256')):
        view['inputs_sha256'][str(p)] = sha(p)
    # File-only full frozen R1/R2 checks. Every subprocess is denied here.
    with patch('subprocess.Popen', side_effect=AssertionError('no child in raw evidence verification')):
        stage.verify_zero_receipt(view)

    calls, initials, summaries = [], [], []
    oracle_cache = {}
    for index, (record, actual) in enumerate(zip(plan, receipt['records'])):
        run = Path(record['output_directory'])
        cfg = kv(record['run_config_path'])
        p = exact_parameters(cfg)
        effective = kv(run / 'effective_config.txt')
        process = load(run / 'process_receipt.json')
        need(0 <= process['elapsed_seconds'] <= 300, 'native elapsed exceeds original cap')
        need(actual['elapsed_seconds'] == process['elapsed_seconds'], 'native receipt elapsed mismatch')
        available = actual['resources_before']
        need(available['MemAvailable_bytes'] >= 12 * 1024**3 and
             available['disk_free_bytes'] >= (100 if index == 0 else 8) * 1024**3, 'original resource guard evidence')
        need(sum(q.stat().st_size for q in run.rglob('*') if q.is_file()) <= 4 * 1024**3, 'zero output budget')
        checked_geometry = validate_zero_outputs(record)
        need(checked_geometry == actual['geometry'], 'worker/replayed geometry mismatch')
        if record['mode'] == 'precheck':
            result = kv(run / 'result.txt')
            g = geometry(cfg)
            need(result['run_id'] == record['run_id'] and result['case'] == record['run_id'] and
                 result['direction'] == effective['direction'], 'precheck identity/direction')
            need(result['formal_simulation'] == 'false' and result['collide_and_stream_calls'] == '0' and
                 result['exit_code'] == '0', 'precheck exit/zero execution')
            need(result['geometry_PASS'] == result['converter_PASS'] == result['q_audit_PASS'] == 'true', 'precheck flags')
            need(int(result['fluid_nodes']) == p['nodes'] and
                 int(result['candidate_links']) == int(result['installed_links']) == g['candidate_links'] and
                 int(result['fallback_count']) == 0 and
                 abs(float(result['q_min']) - .5) <= 1e-10 and abs(float(result['q_max']) - .5) <= 1e-10, 'precheck detailed geometry')
        if record['mode'] == 'initialize':
            result = kv(run / 'result.txt')
            cache_key = (float(effective['dx_m']), p['nodes'])
            if cache_key not in oracle_cache:
                oracle_cache[cache_key] = scalar_oracles(*cache_key)
            oracle = oracle_cache[cache_key]
            need(float(result['mass']) == oracle['legacy_mass'], 'MRP initial FMA path differs')
            need(float(result['fluid_volume_m3']) == oracle['rounded_volume'], 'A1 rounded volume differs')
            need(float(result['corrected_mass']) == oracle['compensated_mass'], 'compensated initial mass differs')
            speed = p['a'] * p['dt'] / 2
            expected_mach = speed * p['dt'] / p['dx'] * math.sqrt(3)
            need(close(float(result['max_Mach']), expected_mach) and float(result['max_Mach']) < .05, 'initial Mach conversion')
            slices = double_slice(run, cfg, p)
            report = AUDIT / ('field_readback_' + record['planned_case_id'] + '.json')
            payload = validate_initial_readback(record, report, AUDIT)
            reader_process = load(report.with_suffix('.process.json'))
            need(0 <= reader_process['elapsed_seconds'] <= 300, 'original reader exceeds cap')
            initial_j = np.array([float(v) for v in result['J_vector_m2_s'].split(',')])
            axis = 1 if cfg['direction'] == 'P' else 0
            summaries.append(dict(planned_case_id=record['planned_case_id'], direction=cfg['direction'],
                acceleration_m_s2=p['a'], dx_nm=float(cfg['dx_nm']), fluid_nodes=p['nodes'],
                wall_links=checked_geometry['candidate_links'], q_min=float(kv(run/'boundary_audit.txt')['q_min']),
                q_max=float(kv(run/'boundary_audit.txt')['q_max']),
                material_counts={k:int(kv(run/'boundary_audit.txt')[k]) for k in ('material_0','material_1','material_2','material_3')}, initial_volume_m3=float(result['fluid_volume_m3']),
                nominal_volume_m3=p['P'] * p['Ly'] * p['H'],
                volume_relative_error=abs(float(result['fluid_volume_m3']) / (p['P'] * p['Ly'] * p['H']) - 1),
                initial_legacy_mass_kg=float(result['mass']), MRP_initial_arithmetic_exact=True,
                initial_compensated_mass_kg=float(result['corrected_mass']),
                A1_initial_volume_path_exact=True, compensated_initial_mass_exact=True,
                density_delta=float(result['density_delta']), max_density_deviation=float(result['max_density_deviation']),
                J_main_m2_s=float(initial_j[axis]), expected_initial_J_m2_s=p['H'] * speed,
                initial_J_relative_error=abs(float(initial_j[axis]) / (p['H'] * speed) - 1),
                max_Mach=float(result['max_Mach']), saved_VTK_payload_files=len(payload), **slices))
            initials.append((record, report))
        calls.append(dict(planned_case_id=record['planned_case_id'], run_id=record['run_id'],
                          mode=record['mode'], native_exit=0, time_steps=0,
                          geometry_recomputed=checked_geometry is not None,
                          elapsed_seconds=process['elapsed_seconds']))
    progress = sorted((AUDIT / 'progress').glob('*.json'))
    need(len(progress) == 18 and [p.name for p in progress] == [f'{i:02d}.json' for i in range(1, 19)], 'progress coverage')
    need([load(p) for p in progress] == receipt['records'], 'progress and final records differ')
    save(OUT / 'native_review.json', dict(PASS=True, native_records=calls, initial_statistics=summaries,
         raw_manifest_files=len(raw), total_audit_files=len(files),
         MRP_scope='initial rho=1 scalar arithmetic only; no new h75 density replay',
         density_capture='NOT_APPLICABLE_S0_ONLY'))
    write_csv(OUT / 'native_calls.csv', calls)
    write_csv(OUT / 'initial_statistics.csv', summaries)
    log = CASE / 'S4_zero_controller_v1_20261103_01.log'
    (OUT / 'completed_controller_log_snapshot.txt').write_bytes(log.read_bytes())
    readers = []
    env = dict(os.environ, OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1',
               NUMEXPR_NUM_THREADS='1', QT_QPA_PLATFORM='offscreen', PYTHONDONTWRITEBYTECODE='1')
    env.pop('LD_LIBRARY_PATH', None)
    env.pop('LD_PRELOAD', None)
    original_popen = subprocess.Popen
    for record, original_report in initials:
        output = OUT / ('field_reread_' + record['planned_case_id'] + '.json')
        logfile = output.with_suffix('.log')
        argv = ['/usr/bin/pvpython', '--force-offscreen-rendering', '-B', str(CHECK / 'analysis/read_fields.py'),
                '--run', record['output_directory'], '--out', str(output)]
        def allow_only_reader(command, *args, **kwargs):
            need(command == argv, 'non-reader subprocess forbidden during review')
            return original_popen(command, *args, **kwargs)
        started = time.monotonic()
        with patch('subprocess.Popen', side_effect=allow_only_reader), logfile.open('x') as stream:
            result = subprocess.run(argv, stdout=stream, stderr=subprocess.STDOUT, env=env,
                                    timeout=300, preexec_fn=reader_limits)
        elapsed = time.monotonic() - started
        need(result.returncode == 0, 'independent saved-field reread failed; no retry')
        fresh = load(output)
        original = load(original_report)
        need(fresh == original, 'fresh saved-field receipt differs from original')
        need(fresh['PASS'] is True and fresh['actual_reader'] is True and fresh['solver_executed'] is False,
             'reader did not actually verify saved fields')
        need(len(fresh['frames']) == 1 and fresh['frames'][0]['step'] == 0, 'fresh initial frame count')
        readers.append(dict(planned_case_id=record['planned_case_id'], argv=argv, independent_exit_code=0,
            timed_out=False, elapsed_seconds=elapsed, report_path=str(output), report_sha256=sha(output),
            actual_reader=True, fresh_and_original_receipt_exactly_equal=True,
            unique_core_fluid_nodes=fresh['frames'][0]['unique_fluid_nodes'],
            payload_files=len(fresh['payload_sha256']), frames=1))
        save(OUT / ('reader_' + str(len(readers)) + '_process.json'), readers[-1])
        print('independent initial-field reread PASS ' + record['planned_case_id'], flush=True)
    need(len(readers) == 6, 'exact six saved-field rereads required')
    need(all(sha(p) == h for p, h in protected.items()), 'protected input/output changed during review')
    stage.unchanged(bound['inputs_sha256'])
    stage.require_pristine(bound['prepared_runs'])
    save(OUT / 'independent_review_acceptance.json', dict(
        reviewed_at=datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(), audit_id=stage.AUDIT_ID,
        release_path=str(RELEASE), release_sha256=RELEASE_SHA, preparation_A_sha256=A_SHA,
        ZERO_STEP_INDEPENDENT_REVIEW_PASS=True, ZERO_STEP_GEOMETRY_PASS=True,
        R1_actual_parameters_rechecked=True, R2_record_field_payload_chain_rechecked=True,
        eighteen_records_reviewed=len(calls), initial_field_reports_reviewed=6,
        actual_VTK_field_rereads=len(readers), initialized_frames_reread=6,
        raw_manifest_files_verified=len(raw), audit_files_verified=len(files),
        release_inputs_verified=len(bound['inputs_sha256']), protected_files_verified=len(protected),
        MRP_initial_arithmetic_exact=True, A1_initial_volume_path_exact=True,
        density_capture='NOT_APPLICABLE_S0_ONLY', new_h75_density_replay=False,
        reader_records=readers, B_sealing_condition_satisfied=True,
        native_solver_calls_this_review=0, time_steps_this_review=0, builds_this_review=0,
        original_files_changed=False, solver_executed=False,
        NUMERICAL_GATE='NOT_EVALUATED', geometry_PASS=None, RESULT_PASS=False,
        GRID_CHECKS_PASS='NOT_EVALUATED', REFERENCE_QUALIFIED_FOR_CASE=False,
        reference_qualified=False, MODEL_COMPARISON='NOT_EVALUATED', physical_validation='NOT_EVALUATED',
        submission_ready=False, formal_started=False, performance_started=False, next_stage_started=False))
    print(json.dumps(dict(ZERO_STEP_INDEPENDENT_REVIEW_PASS=True, native_records=18,
                         saved_field_rereads=6, raw_files=len(raw), audit_files=len(files),
                         protected_files=len(protected), B_sealing_condition_satisfied=True)))


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        save(OUT / 'review_failure.json', dict(ZERO_STEP_INDEPENDENT_REVIEW_PASS=False,
            error=type(error).__name__ + ': ' + str(error), B_sealing_condition_satisfied=False,
            formal_started=False, performance_started=False, retry_authorized=False))
        raise

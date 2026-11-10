"""Audit only existing completed S0 outputs; no solver or fitting invocation.

Frozen check_results.py is rerun separately without modification. Supplementary
checks after a regression refusal diagnose remaining evidence and cannot issue
acceptance or turn that refusal into a pass.
"""
from pathlib import Path
from fractions import Fraction
from datetime import datetime
import csv
import json
import math
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
CASE = ROOT / 'CASE/unseen_v2_reference_S0_v1_2'
CHECKER = ROOT / 'CASE/unseen_v2_reference_checker_v1_2'
sys.path.insert(0, str(CHECKER / 'analysis'))
from evidence import sha, need, save, kv, rows, exact_parameters, check_boundary, window_metrics, close
from check_results import binding, diagnostics, check_slice, compare_legacy

EXPECTED = 'eb73d1ec7989cee26aecf1a43c9b8fd818a77fdd5d9ba8fef5e805d9451a5f4a'


def differences(raw, baseline, direction):
    old = rows(baseline / 'diagnostics.csv'); new = rows(raw / 'diagnostics.csv')
    need(len(old) == len(new), 'old/new trajectory lengths differ')
    common = sorted(set(old[0]) & set(new[0])); need(len(common) == 20, 'legacy column count')
    summary = {}; changed = []
    for key in common:
        a = np.array([float(r[key]) for r in old]); b = np.array([float(r[key]) for r in new])
        selected = np.flatnonzero(a != b); absolute = np.abs(a - b)
        record = dict(differing_rows=int(len(selected)), exact=not len(selected),
            max_absolute_difference=float(absolute.max()),
            first_different_step=int(selected[0]) if len(selected) else None,
            last_different_step=int(selected[-1]) if len(selected) else None,
            largest_difference_step=int(absolute.argmax()) if len(selected) else None)
        if len(selected):
            record.update(old_at_largest_difference=old[int(absolute.argmax())][key],
                new_at_largest_difference=new[int(absolute.argmax())][key])
            if key == 'mass':
                record['units'] = 'kg'
                record['max_difference_relative_to_old_initial_mass'] = float(absolute.max() / a[0])
                record['max_binary64_ULP_distance'] = int(np.max(np.abs(
                    a.view(np.int64) - b.view(np.int64))))
        summary[key] = record
        for i in selected:
            changed.append(dict(step=int(i), column=key, old_text=old[i][key],
                new_text=new[i][key], signed_difference=float(b[i] - a[i]),
                absolute_difference=float(absolute[i])))
    target = OUT / f'legacy_differences_{direction}.csv'
    with target.open('x', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['step', 'column', 'old_text', 'new_text',
                                              'signed_difference', 'absolute_difference'])
        writer.writeheader(); writer.writerows(sorted(changed, key=lambda r: (r['step'], r['column'])))
    return dict(columns=summary, common_column_count=len(common), rows_compared=len(new),
        identical_columns=[k for k, v in summary.items() if v['exact']],
        differing_columns=[k for k, v in summary.items() if not v['exact']],
        changed_entries=len(changed), changed_entry_csv=str(target),
        initial_old_mass_kg=float(old[0]['mass']), initial_new_mass_kg=float(new[0]['mass']),
        legacy_error_definition='(mass(step)-mass(0))/mass(0)',
        old_legacy_max_mass_error=float(max(abs(float(v['mass_error'])) for v in old)),
        new_legacy_max_mass_error=float(max(abs(float(v['mass_error'])) for v in new)))


def frame_plan(run, config, result, fields, completion, protocol):
    p = exact_parameters(config); frames = rows(run / 'frame_index.csv')
    schedule = rows(run / 'frame_schedule.csv'); steps = int(result['steps_completed'])
    need(len(schedule) == len(protocol['time']['frame_tstar']), 'frame schedule incomplete')
    expected = {0, steps}
    for request, item in zip(protocol['time']['frame_tstar'], schedule):
        target = math.ceil(Fraction(str(request)) * 6 * (Fraction(config['h_nm']) / Fraction(config['dx_nm']))**2)
        need(float(item['requested_tstar']) == request and int(item['target_step']) == target,
             'saved target steps changed')
        need(int(item['reached']) == int(target <= steps), 'saved reached flag')
        if target <= steps:
            expected.add(target)
    actual = [int(v['step']) for v in frames]
    need(actual == sorted(expected) and len(actual) == int(result['frames_written']), 'actual frame plan')
    for f in frames:
        need(close(float(f['time_s']), int(f['step']) * p['dt'], atol=1e-24), 'frame seconds')
        need(close(float(f['tstar']), p['nu'] * int(f['step']) * p['dt'] / p['h']**2,
                   atol=1e-14), 'frame nondimensional time')
    need(fields['PASS'] and fields['actual_reader'], 'actual VTK read failed')
    need([f['step'] for f in fields['frames']] == actual, 'reader frame coverage')
    for path, digest in fields['payload_sha256'].items():
        need(completion['output_sha256'][str(Path(path).relative_to(run))] == digest,
             'VTK closure not in raw completion binding')
    worst = 0.
    for f in fields['frames']:
        error = np.abs(np.array(f['J_m2_s']) - np.array(f['diagnostic_J_m2_s']))
        bounds = np.array(f['roundoff_bound_m2_s'])
        need(np.all(error <= bounds), 'export roundoff bound exceeded')
        ratios = np.divide(error, bounds, out=np.zeros(3), where=bounds > 0)
        worst = max(worst, float(ratios.max()))
    return dict(frame_count=len(actual), steps=actual,
        scheduled_requests=len(schedule), future_frames_not_extended=True,
        actual_VTK_reader_PASS=True, VTK_version=fields['VTK_version'],
        complete_VTK_payload_count=len(fields['payload_sha256']),
        unique_fluid_nodes_each_frame=sorted(set(f['unique_fluid_nodes'] for f in fields['frames'])),
        worst_flux_export_error_over_roundoff_bound=worst)


def main():
    release = CASE / 'evidence/S0_launch_release_20261101_01.json'
    bound = binding(release, EXPECTED)
    protocol = json.loads((CHECKER / 'common/protocol.json').read_text())
    limits = json.loads((CHECKER / 'common/acceptance_spec.json').read_text())
    results = []
    for record in bound['approved_runs']:
        run = Path(record['output_directory']); config = kv(run / 'run_config.txt')
        direction = config['direction']; native = kv(run / 'result.txt'); p = exact_parameters(config)
        completion = json.loads((run / 'completion.json').read_text())
        need(completion['release_sha256'] == EXPECTED and completion['run_id'] == record['run_id'], 'completion identity')
        need(completion['independent_process_exit_code'] == 0 and not completion['timed_out'], 'process failure')
        need(completion['elapsed_seconds'] <= 3600, 'wall cap exceeded')
        need(completion['inputs_unchanged'] is True and completion['inputs_before_sha256'] ==
             completion['inputs_after_sha256'] == bound['inputs_sha256'], 'full before/after input maps')
        hashes = completion['output_sha256']
        actual_files = {str(f.relative_to(run)) for f in run.rglob('*') if f.is_file()}
        need(actual_files == set(hashes) | {'completion.json'}, 'raw manifest is not exhaustive')
        need(all(sha(run / name) == digest for name, digest in hashes.items()), 'raw file hash mismatch')
        need(all(not f.is_symlink() for f in run.rglob('*')), 'raw symlink')
        resource = completion['resources_before']
        need(resource['MemAvailable_bytes'] >= 12 * 1024**3, 'recorded RAM gate')
        need(resource['disk_free_bytes'] >= (100 if direction == 'P' else 8) * 1024**3, 'recorded disk gate')
        data_rows = rows(run / 'diagnostics.csv')
        data = {key: np.array([float(row[key]) for row in data_rows]) for key in data_rows[0]}
        # Frozen pure-arithmetic numerical gate is evaluated independently of
        # the strict legacy regression refusal; no rule is bypassed for acceptance.
        scalar = diagnostics(config, native, data)
        geometry = check_boundary(config, kv(run / 'boundary_audit.txt'))
        check_slice(run, config, scalar['K_m3'])
        n = p['window']; main = data['Jy'] if direction == 'P' else data['Jx']
        cross = -data['Jx'] if direction == 'P' else data['Jy']
        std, span, transverse = window_metrics(main, cross, n)
        accepted = (std <= 1e-6) & (span <= 5e-6) & (transverse <= 1e-12)
        first_stop = int(np.flatnonzero(accepted)[0] + n - 1)
        reference = bound['h75_regression_references'][direction]; baseline = Path(reference['directory'])
        need(sha(baseline / 'result.txt') == reference['result_sha256'] and
             sha(baseline / 'diagnostics.csv') == reference['diagnostics_sha256'], 'old control source binding')
        legacy = compare_legacy(run, baseline)
        details = differences(run, baseline, direction)
        old_K = float(kv(baseline / 'result.txt')['Keff_m3'])
        deltaK = abs(scalar['K_m3'] / old_K - 1)
        same_files = {}
        for name in ['field_slice.csv', 'velocity_profile.csv', 'pressure_profile.csv',
                     'energy_dissipation.csv', 'frame_index.csv', 'frame_schedule.csv']:
            need((baseline / name).is_file(), 'baseline comparison file missing')
            same_files[name] = dict(byte_identical=sha(run / name) == sha(baseline / name),
                                   new_sha256=sha(run / name), old_sha256=sha(baseline / name))
        field_path = OUT / ('recheck_P/fields.json' if direction == 'P' else 'T_supplementary_fields.json')
        fields = json.loads(field_path.read_text())
        frames = frame_plan(run, config, native, fields, completion, protocol)
        K_gate = deltaK <= limits['statistics_port_regression']['K_relative_max']
        accepted_result = bool(K_gate and legacy['all_exact'])
        need(accepted_result == (direction == 'P'), 'unexpected regression disposition; inspect all evidence')
        frozen_dir = OUT / ('recheck_' + direction)
        if direction == 'P':
            frozen_acceptance = json.loads((frozen_dir / 'acceptance.json').read_text())
            need(frozen_acceptance['RESULT_PASS'] is True, 'P frozen checker did not pass')
        else:
            failure = json.loads((frozen_dir / 'failure.json').read_text())
            need(failure['RESULT_PASS'] is False and 'legacy trajectory difference' in failure['error'],
                 'T frozen refusal changed')
        r = dict(direction=direction, drive_axis='+y' if direction == 'P' else '+x',
            run_id=record['run_id'], planned_case_id=record['planned_case_id'],
            independent_native_exit_code=0, native_elapsed_seconds=completion['elapsed_seconds'],
            completion_sha256=sha(run / 'completion.json'), input_bindings=len(bound['inputs_sha256']),
            exhaustive_raw_file_count=len(hashes), all_input_and_output_hashes_match=True,
            numerical_gate_independently_recomputed='PASS', geometry_PASS=True,
            RESULT_PASS=accepted_result, regression_gate_PASS=accepted_result,
            official_checker_exit_code=0 if direction == 'P' else 2,
            S0_disposition='PASS' if accepted_result else 'HOLD_LEGACY_MASS_TRAJECTORY_DIFFERENCE',
            no_post_hoc_tolerance_added=True, scalar=scalar,
            transport=dict(J_m2_s=scalar['J_main_m2_s'], K_m3=scalar['K_m3'],
                H_m=p['H'], mean_velocity_m_s=scalar['J_main_m2_s'] / p['H'],
                R_eff_Pa_s_per_m3=1000 * p['a'] / scalar['J_main_m2_s'],
                old_K_m3=old_K, relative_K_change=deltaK, K_gate_PASS=K_gate),
            numerical_metrics=dict(corrected_mass_relative_max=scalar['corrected_mass_max'],
                delta_mass_relative_max=float(np.abs(data['delta_mass_error']).max()),
                ledger_agreement_max=scalar['ledger_agreement_max'], legacy_mass_relative_max=scalar['legacy_mass_max'],
                density_deviation_max=float(data['max_density_deviation'].max()),
                Mach_max=float(data['Mach'].max()), Re_H=scalar['Re_H'],
                final_section_relative_difference=float(data['section_relative_difference'][-1]),
                final_sample_relative_std=float(std[-1]), final_relative_span=float(span[-1]),
                final_cross_flux_window_abs_max_m2_s=float(transverse[-1]),
                all_finite=True, positive_final_main_flux=True),
            stopping=dict(diagnostic_rows=len(data_rows), window_steps=n,
                all_full_windows_recomputed=len(std), first_acceptable_step=first_stop,
                actual_final_step=int(native['steps_completed']), maximum_steps=p['cap'],
                first_acceptable_window_is_final=first_stop == int(native['steps_completed'])),
            geometry=geometry, frames=frames, legacy=legacy, legacy_detailed=details,
            old_new_exported_files=same_files, legacy_mass_source_line_unchanged=True,
            precise_cause_of_legacy_difference='NOT_ESTABLISHED',
            possible_cause_not_proven='floating-point accumulation or compiled evaluation path; no compiled-cause audit performed',
            original_native_RESULT_PASS=native['RESULT_PASS'],
            old_native_RESULT_PASS=kv(baseline / 'result.txt').get('RESULT_PASS'),
            REFERENCE_QUALIFIED_FOR_CASE=False, MODEL_COMPARISON='NOT_EVALUATED', physical_validation='NOT_EVALUATED')
        save(OUT / f'analysis_{direction}.json', r); results.append(r)
    need(all(sha(p) == h for p, h in bound['inputs_sha256'].items()), 'bound input changed during review')
    protected = json.loads((OUT / 'protected_inputs_before.json').read_text())
    need(all(sha(p) == h for p, h in protected.items()), 'protected original data changed')
    save(OUT / 'summary.json', dict(review_id='URV-S0-RESULTS-20261101',
        reviewed_at_local=datetime.now().astimezone().isoformat(), protocol_id='URV-v1',
        stage='S0_REGRESSION', disposition='HOLD', S0_RESULT_PASS=False,
        P_RESULT_PASS=results[0]['RESULT_PASS'], T_RESULT_PASS=results[1]['RESULT_PASS'],
        numerical_gate_independently_recomputed={'P': 'PASS', 'T': 'PASS'}, geometry_PASS={'P': True, 'T': True},
        run_ids=[r['run_id'] for r in results], existing_results_only=True,
        source_input_bindings=len(bound['inputs_sha256']), protected_original_file_count=len(protected),
        all_original_files_unchanged=True, independent_checker_reruns=2,
        actual_saved_frames_read_this_review=20, native_solver_invocations=0,
        solver_recompile=False, acceptance_threshold_changes=False,
        original_T_failure_preserved=True, T_supplementary_checks_do_not_override_regression_refusal=True,
        next_stage_started=False, S1_authorized=False,
        REFERENCE_QUALIFIED_FOR_CASE=False, MODEL_COMPARISON='NOT_EVALUATED',
        physical_validation='NOT_EVALUATED', strict_error_bound_established=False, submission_ready=False,
        next_action='Focused read-only audit of T legacy mass/mass_error discrepancy; retain HOLD and original failure, no automatic rerun or S1.'))
    print(json.dumps(dict(S0='HOLD', P='PASS', T='HOLD', protected_files_unchanged=len(protected),
        T_differing_columns=results[1]['legacy_detailed']['differing_columns'], saved_frames_read=20)))


if __name__ == '__main__':
    main()

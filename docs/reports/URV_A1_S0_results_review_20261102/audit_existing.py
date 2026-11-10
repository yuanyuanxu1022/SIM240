#!/usr/bin/env python3
"""Read-only full-trajectory and capture-closure audit; no native invocation."""
from pathlib import Path
import csv
import hashlib
import json
import struct
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
CASE = ROOT / 'CASE/unseen_v2_reference_S0_mrp_v1_a1'
CHECKER = ROOT / 'CASE/unseen_v2_reference_checker_mrp_v1_a1'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def rows(path):
    with Path(path).open() as stream:
        return list(csv.DictReader(stream))


def kv(path):
    return dict(line.split('=', 1) for line in Path(path).read_text().splitlines() if '=' in line)


def bits(value):
    return struct.pack('>d', float(value)).hex()


def main():
    release = CASE / 'evidence/S0_launch_release_A1_20261102_01.json'
    bound = json.loads(release.read_text())
    schedule = json.loads((CHECKER / 'revision/density_capture_schedule.json').read_text())
    historical_csv = ROOT / 'docs/reports/URV_S0_results_review_20261101/legacy_differences_T.csv'
    historical = rows(historical_csv)
    assert sha(historical_csv) == schedule['source_sha256']
    result = {'release_sha256': sha(release), 'directions': {}, 'historical_differences': len(historical)}
    recreated = []
    for direction in ('P', 'T'):
        rid = f'URV_S0_{direction}_A1_20261102_01'
        run = CASE / 'runs' / rid / 'steady'
        new = rows(run / 'diagnostics.csv')
        old = rows(Path(bound['h75_regression_references'][direction]['directory']) / 'diagnostics.csv')
        v12 = rows(bound['mass_repair_baselines'][direction]['v12_diagnostics'])
        columns = bound['h75_regression_references'][direction]['legacy_columns']
        assert len(columns) == 20 and len(new) == len(old) == len(v12)
        comparisons = {}
        for name in columns:
            n = np.array([float(row[name]) for row in new])
            o = np.array([float(row[name]) for row in old])
            comparisons[name] = dict(exact=bool(np.array_equal(n, o)),
                                     differences=int(np.count_nonzero(n != o)),
                                     max_absolute_difference=float(np.max(np.abs(n - o))))
        assert all(value['exact'] for value in comparisons.values())
        corrected = ['corrected_mass', 'corrected_mass_error', 'delta_mass_error',
                     'mass_ledger_agreement', 'density_delta']
        corrected_exact = {key: all(float(a[key]) == float(b[key]) for a, b in zip(new, v12))
                           for key in corrected}
        assert all(corrected_exact.values())
        idx = json.loads((run / 'mass_capture/rho_capture_index.json').read_text())
        records = idx['records']
        planned = schedule['directions'][direction]
        assert len(records) == planned['total_capture_count_including_initial_reference']
        capture_steps = {r['step'] for r in records if r['phase'] == 'diagnostic'}
        assert capture_steps == set(planned['diagnostic_steps'])
        payload_bytes = sum((run / 'mass_capture' / record['file']).stat().st_size for record in records)
        assert payload_bytes == len(records) * 460800
        first = next(r for r in records if r['phase'] == 'initial_reference')
        zero = next(r for r in records if r['phase'] == 'diagnostic' and r['step'] == 0)
        assert first['sha256'] == zero['sha256']
        constants = {(r['rho_phys_hex64'], r['dx_hex64']) for r in records}
        environments = {(r['fe_round'], r['mxcsr_control'], r['double_bytes'],
                         r['iec559'], r['cpu_fma']) for r in records}
        assert len(constants) == len(environments) == 1
        volumes = {r['native_volume_hex64'] for r in records}
        assert len(volumes) == 1
        physical = json.loads(Path(bound['mass_repair_baselines'][direction]['v12_output_manifest']).read_text())
        assert len(physical) == 27 and all(sha(run / path) == value for path, value in physical.items())
        completion = json.loads((run / 'completion.json').read_text())
        output_hashes = completion['output_sha256']
        raw_files = {str(p.relative_to(run)) for p in run.rglob('*') if p.is_file()}
        assert raw_files == set(output_hashes) | {'completion.json'}
        assert all(sha(run / path) == value for path, value in output_hashes.items())
        if direction == 'T':
            for record in historical:
                step, key = int(record['step']), record['column']
                assert bits(old[step][key]) == bits(record['old_text'])
                assert bits(new[step][key]) == bits(record['old_text'])
                assert bits(v12[step][key]) == bits(record['new_text'])
                difference = float(v12[step][key]) - float(new[step][key])
                assert bits(difference) == bits(record['signed_difference'])
                recreated.append(dict(step=step, column=key,
                    old_text=record['old_text'], A1_text=new[step][key],
                    v12_text=v12[step][key], v12_minus_A1=difference,
                    historical_signed_difference=record['signed_difference'],
                    A1_minus_old=float(new[step][key]) - float(old[step][key])))
        raw_result = kv(run / 'result.txt')
        gate_keys = ['max_mass_abs_relative', 'legacy_max_mass_abs_relative',
                     'max_delta_mass_abs_relative', 'max_mass_ledger_agreement',
                     'max_density_deviation', 'max_Mach', 'section_relative_difference',
                     'window_main_rel_std', 'window_main_rel_span', 'window_cross_abs_max',
                     'fluid_volume_m3', 'q_min', 'q_max', 'J_main_m2_s', 'Keff_m3']
        result['directions'][direction] = dict(run_id=rid, diagnostic_rows=len(new),
            steps_completed=int(raw_result['steps_completed']), legacy_columns=comparisons,
            corrected_full_trajectory_exact=corrected_exact, capture_records=len(records),
            diagnostic_captures=len(capture_steps), captured_density_values=len(records) * 57600,
            rho_payload_bytes=payload_bytes, rho_shape_per_capture=57600,
            initial_and_diagnostic_zero_payload_equal=True,
            constants_hex64=list(next(iter(constants))), floating_environment=list(next(iter(environments))),
            volume_hex64=list(volumes)[0], physical_output_files_exact=len(physical),
            physical_VTK_files_exact=sum(p.startswith('vtkData/') for p in physical),
            actual_raw_files=len(raw_files), completion_output_files=len(output_hashes),
            actual_raw_closure_exact=True, gates={key: float(raw_result[key]) for key in gate_keys},
            native_RESULT_PASS=raw_result['RESULT_PASS'], native_PASS=raw_result['PASS'],
            native_exit_code=completion['independent_process_exit_code'],
            native_wall_seconds=completion['elapsed_seconds'])
    assert len(recreated) == 380
    steps = {r['step'] for r in recreated}
    assert len(steps) == 190 and steps == set(schedule['directions']['T']['difference_steps'])
    summary = dict(entries=380, time_steps=190, first_step=min(steps), last_step=max(steps),
        max_abs_mass_difference=max(abs(r['v12_minus_A1']) for r in recreated if r['column'] == 'mass'),
        max_abs_mass_error_difference=max(abs(r['v12_minus_A1']) for r in recreated if r['column'] == 'mass_error'),
        recreated_values_exact=True, restored_A1_vs_old_differences=0)
    result['T_difference_reconstruction'] = summary
    with (OUT / 'T_380_entry_reconstruction.csv').open('x', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(recreated[0])); writer.writeheader(); writer.writerows(recreated)
    with (OUT / 'data_audit.json').open('x') as stream:
        stream.write(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'P_rows':result['directions']['P']['diagnostic_rows'],
                      'T_rows':result['directions']['T']['diagnostic_rows'], **summary}))


if __name__ == '__main__':
    main()

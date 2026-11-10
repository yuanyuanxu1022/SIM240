"""Independent build-equivalence checker for the server 1.25 nm rerun.

Recomputes the statistical window and the effective permeability K from the raw
diagnostics, then compares K with the local-build reference.  It does NOT accept
a stage, does not qualify a reference, and never runs the solver.

The per-run gates below are copied verbatim from the frozen
acceptance_spec.json of the local S4 checker; they are not re-derived here.
"""
from pathlib import Path
import argparse, json, math, sys
import numpy as np

CASE = Path(__file__).resolve().parents[2] / 'unseen_v2_reference_S4_tge_server_v2'
CHECKER = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CHECKER / 'analysis'))
from evidence import (need, sha, kv, rows, save, close, exact_parameters,
                      check_boundary, window_metrics)  # noqa: E402
import server_stage as s  # noqa: E402

GATES = dict(compensated_mass_relative_strict=1e-10, ledger_agreement_max=1e-13,
             density_deviation_max=1e-06, Mach_strict=0.05, section_relative_max=1e-05,
             window_relative_sample_std_max=1e-06, window_relative_span_max=5e-06,
             cross_flux_abs_m2_s_max=1e-12)
RE_H_MAX = 0.01

SCHEMA = ['step', 'J', 'rho', 'Mach', 'mass', 'time_s', 'mass_error',
          'max_density_deviation', 'Jx', 'Jy', 'Jz', 'Q_section1', 'Q_section2',
          'section_relative_difference', 'pressure_min', 'pressure_max',
          'window_rel_std', 'window_rel_span', 'window_cross_abs_max', 'finite',
          'corrected_mass', 'corrected_mass_error', 'delta_mass_error',
          'mass_ledger_agreement', 'density_delta']


def read_diagnostics(run):
    table = rows(run / 'diagnostics.csv')
    need(table and list(table[0]) == SCHEMA, 'diagnostic schema mismatch')
    return {k: np.array([float(r[k]) for r in table]) for k in SCHEMA}


def scalars(run, config):
    p = exact_parameters(config)
    n = p['window']
    data = read_diagnostics(run)
    steps = int(kv(run / 'result.txt')['steps_completed'])
    need(len(data['J']) == steps + 1 and n <= len(data['J']), 'incomplete trajectory')
    need(np.array_equal(data['step'], np.arange(len(data['J']))), 'reordered steps')
    need(all(np.isfinite(v).all() for v in data.values()), 'nonfinite diagnostics')
    need(np.all(data['finite'] == 1), 'nonfinite measurement flag')
    need(close(data['time_s'], np.arange(len(data['J'])) * p['dt'], rtol=1e-13, atol=1e-24),
         'time units')
    need(np.all(data['corrected_mass'] > 0), 'nonpositive corrected mass')
    need(close(data['corrected_mass'][0], 1000 * p['nodes'] * p['dx'] ** 3),
         'initial mass/units')

    legacy = (data['mass'] - data['mass'][0]) / data['mass'][0]
    corrected = (data['corrected_mass'] - data['corrected_mass'][0]) / data['corrected_mass'][0]
    ledger = np.abs(corrected - (data['density_delta'] - data['density_delta'][0])
                    / (p['nodes'] + data['density_delta'][0]))
    need(close(legacy, data['mass_error'], rtol=1e-10, atol=1e-16), 'legacy mass recomputation')
    need(close(corrected, data['corrected_mass_error'], rtol=1e-10, atol=1e-16),
         'corrected mass recomputation')
    need(close(ledger, data['mass_ledger_agreement'], rtol=1e-10, atol=1e-16),
         'ledger recomputation')

    main = data['Jy'] if config['direction'] == 'P' else data['Jx']
    cross = -data['Jx'] if config['direction'] == 'P' else data['Jy']
    need(close(main, data['J'], rtol=1e-13, atol=1e-30), 'directional main flux')
    std, span, crossmax = window_metrics(main, cross, n)
    need(close(std, data['window_rel_std'][n - 1:], rtol=1e-5, atol=1e-12), 'window std recomputation')
    need(close(span, data['window_rel_span'][n - 1:], rtol=1e-5, atol=1e-12), 'window span recomputation')
    need(close(crossmax, data['window_cross_abs_max'][n - 1:], rtol=1e-5, atol=1e-28),
         'cross flux recomputation')

    accepted = ((std <= GATES['window_relative_sample_std_max'])
                & (span <= GATES['window_relative_span_max'])
                & (crossmax <= GATES['cross_flux_abs_m2_s_max']))
    need(bool(accepted[-1]) and not np.any(accepted[:-1]),
         'final step is not the first acceptable statistical window')

    worst_mass = float(np.abs(corrected).max())
    worst_ledger = float(ledger.max())
    worst_rho = float(data['max_density_deviation'].max())
    worst_mach = float(data['Mach'].max())
    need(worst_mass < GATES['compensated_mass_relative_strict'], 'corrected mass gate')
    need(worst_ledger <= GATES['ledger_agreement_max'], 'ledger gate')
    need(worst_rho <= GATES['density_deviation_max'], 'density gate')
    need(worst_mach < GATES['Mach_strict'], 'Mach gate')
    need(float(data['section_relative_difference'][-1]) <= GATES['section_relative_max'],
         'section mismatch gate')
    re_h = worst_mach / math.sqrt(3) * p['dx'] / p['dt'] * (p['h'] + p['d']) / p['nu']
    need(re_h <= RE_H_MAX, 'Reynolds guard')
    need(main[-1] > 0, 'nonpositive final flux')

    k_value = p['nu'] * float(main[-1]) / p['a']
    return dict(K_m3=k_value, J_main_m2_s=float(main[-1]), steps=steps,
                window_steps=n, diagnostic_rows=len(data['J']),
                final_window_std=float(std[-1]), final_window_span=float(span[-1]),
                corrected_mass_max=worst_mass, ledger_agreement_max=worst_ledger,
                max_density_deviation=worst_rho, max_Mach=worst_mach, Re_H=re_h,
                predicted_nodes=p['nodes'])


def run_checks(run, config, expected_sha):
    result = kv(run / 'result.txt')
    need(result['formal_simulation'] == 'true', 'not a formal run')
    need(result['direction'] == ('parallel' if config['direction'] == 'P' else 'perpendicular'),
         'direction mismatch')
    need(result['exit_code'] == '0', 'native exit flag')
    need(result['finite'] == 'true', 'nonfinite result')
    p = exact_parameters(config)
    need(int(result['fluid_nodes']) == p['nodes'], 'fluid node count')
    need(int(result['window_steps']) == p['window'] and int(result['maximum_steps']) == p['cap'],
         'window/cap mismatch')
    need(int(result['steps_completed']) <= p['cap'], 'excessive step count')
    boundary = kv(run / 'boundary_audit.txt')
    geometry = check_boundary(config, boundary)
    completion = s.load(run / 'completion.json')
    need(completion['release_sha256'] == expected_sha, 'completion release mismatch')
    need(completion['independent_process_exit_code'] == 0 and completion['timed_out'] is False
         and completion['resource_stop_reason'] is None, 'native process failure')
    need(completion['inputs_unchanged'] is True, 'input drift during run')
    return result, geometry, completion


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--release', type=Path, required=True)
    ap.add_argument('--release-sha256', required=True)
    ap.add_argument('--run', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()

    bound = s.verify_seal(args.release, args.release_sha256)
    run = args.run.resolve()
    record = next((r for r in bound['prepared_runs']
                   if Path(r['output_directory']).resolve() == run), None)
    need(record is not None, 'run is not one of the prepared formal runs')
    config = kv(record['run_config_path'])

    result, geometry, completion = run_checks(run, config, args.release_sha256)
    scalar = scalars(run, config)

    criterion = bound['lineage']['build_equivalence_criterion']
    need(record['run_id'] == criterion['applies_to_run_id'],
         'build equivalence applies only to the declared source run')
    reference = criterion['reference_K_m3']
    rtol = criterion['relative_tolerance']
    relative = scalar['K_m3'] / reference - 1
    passed = abs(relative) <= rtol

    elapsed = float(completion['elapsed_seconds'])
    throughput = scalar['steps'] / elapsed if elapsed > 0 else None

    report = dict(
        protocol_id='URV-v1', kind='BUILD_EQUIVALENCE_ACCEPTANCE_NOT_STAGE_ACCEPTANCE',
        release_sha256=args.release_sha256, run_id=record['run_id'],
        planned_case_id=record['planned_case_id'], direction=config['direction'],
        dx_nm=float(config['dx_nm']),
        NUMERICAL_GATE='NOT_EVALUATED', RESULT_PASS=False, geometry_PASS=geometry is not None,
        BUILD_EQUIVALENCE_PASS=passed,
        build_equivalence=dict(reference_run_id=criterion['source_run_id'],
                               reference_K_m3=reference, server_K_m3=scalar['K_m3'],
                               relative_difference=relative, relative_tolerance=rtol,
                               declared_before_measurement=criterion['declared_before_measurement']),
        scalar=scalar,
        geometry=geometry,
        measured_performance=dict(elapsed_seconds=elapsed,
                                  peak_rss_bytes=completion.get('peak_rss_bytes'),
                                  steps_per_second=throughput,
                                  seconds_per_step=(elapsed / scalar['steps']) if scalar['steps'] else None,
                                  wall_cap_seconds=completion.get('solver_wall_cap_seconds')),
        completion_sha256=sha(run / 'completion.json'),
        original_S4_stage_accepted=False, reference_qualified=False,
        MODEL_COMPARISON='NOT_EVALUATED', physical_validation='NOT_EVALUATED',
        submission_ready=False, next_stage_started=False, S5_started=False,
        note='This record establishes build equivalence and measured performance only. '
             'It does not accept the S4 stage, does not qualify a reference and does not '
             'touch the original transverse grid FAIL.')

    need(not (args.out / 'acceptance.json').exists(), 'refusing to overwrite acceptance')
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / 'acceptance.json').write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps(dict(BUILD_EQUIVALENCE_PASS=passed,
                          relative_difference=relative,
                          server_K_m3=scalar['K_m3'],
                          reference_K_m3=reference,
                          peak_rss_bytes=completion.get('peak_rss_bytes'),
                          steps_per_second=throughput,
                          elapsed_seconds=elapsed), indent=2))
    return 0 if passed else 2


if __name__ == '__main__':
    raise SystemExit(main())

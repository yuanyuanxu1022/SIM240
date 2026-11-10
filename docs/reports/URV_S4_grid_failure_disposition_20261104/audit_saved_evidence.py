"""Read saved evidence only; never imports execution/checker entry points."""
from pathlib import Path
import csv
import hashlib
import json
import math
import statistics

ROOT = Path('/home/dell/yuanyuanxu/SIM240')
OUT = Path(__file__).resolve().parent
CASE = ROOT / 'CASE/unseen_v2_reference_S4_reuse_v1'
PREVIOUS = ROOT / 'docs/reports/URV_S4_completed_review_20261104_143205'


def load(path):
    return json.loads(Path(path).read_text())


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def kv(path):
    return dict(line.split('=', 1) for line in Path(path).read_text().splitlines()
                if '=' in line and not line.startswith('#'))


def save(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def main():
    # Do not overwrite a completed audit by accidentally rerunning this file.
    assert not (OUT / 'verification.json').exists(), 'completed audit exists'
    release = CASE / 'evidence/S4_formal_launch_release_v1_20261104_01.json'
    expected = 'e5f7de1e584b776f8cc9bf1dbb31f198422ce10984ba8ad7d729220afdcdd19b'
    assert sha(release) == expected
    bound = load(release)
    old_protected = load(PREVIOUS / 'protected_inputs_and_outputs.json')
    drift = [p for p, digest in old_protected.items()
             if not Path(p).is_file() or sha(p) != digest]
    save('prior_protection_recheck.json', dict(count=len(old_protected), drift=drift))
    assert not drift, 'existing protected evidence drift; stop review'
    assert all(sha(p) == digest for p, digest in bound['inputs_sha256'].items())
    protected = dict(old_protected)
    for p in PREVIOUS.rglob('*'):
        if p.is_file() and '__pycache__' not in p.parts:
            protected[str(p)] = sha(p)
    protected[str(release)] = expected
    spec_path = ROOT / 'CASE/unseen_v2_reference_checker_S4_reuse_v1/common/acceptance_spec.json'
    spec = load(spec_path)
    assert spec['reference']['medium_fine_relative_change_max'] == 0.01
    assert spec['reference']['fine_GCI_estimate_max'] == 0.01
    rows = []
    accepted = {}
    raw_count = 0
    for rec in bound['prepared_runs']:
        run = Path(rec['output_directory'])
        config = kv(rec['run_config_path'])
        assert sha(rec['run_config_path']) == rec['run_config_sha256']
        result = kv(run / 'result.txt')
        effective = kv(run / 'effective_config.txt')
        completion = load(run / 'completion.json')
        acceptance_path = CASE / 'analysis_results' / rec['run_id'] / 'acceptance.json'
        acceptance = load(acceptance_path)
        assert acceptance['completion_sha256'] == sha(run / 'completion.json')
        assert acceptance['release_sha256'] == completion['release_sha256'] == expected
        assert completion['inputs_before_sha256'] == completion['inputs_after_sha256'] == bound['inputs_sha256']
        assert completion['inputs_unchanged'] is True
        assert completion['run_id'] == acceptance['run_id'] == rec['run_id']
        assert completion['planned_case_id'] == acceptance['planned_case_id'] == rec['planned_case_id']
        assert completion['independent_process_exit_code'] == 0
        assert completion['timed_out'] is False and completion['resource_stop_reason'] is None
        assert acceptance['RESULT_PASS'] is True and acceptance['geometry_PASS'] is True
        assert acceptance['NUMERICAL_GATE'] == 'PASS' and acceptance['independent_exit_code'] == 0
        actual = {str(p.relative_to(run)) for p in run.rglob('*')
                  if p.is_file() and p.name != 'completion.json'}
        assert actual == set(completion['output_sha256'])
        for name, digest in completion['output_sha256'].items():
            path = run / name
            assert not path.is_symlink() and path.resolve().is_relative_to(run.resolve())
            assert sha(path) == digest
            protected[str(path)] = digest
            raw_count += 1
        with (run / 'diagnostics.csv').open() as stream:
            data = list(csv.DictReader(stream))
        n = int(effective['window_steps'])
        tail = [float(r['J']) for r in data[-n:]]
        final_K = float(config['nu_m2_s']) * tail[-1] / float(config['acceleration_m_s2'])
        assert math.isclose(final_K, float(result['Keff_m3']), rel_tol=1e-13)
        assert math.isclose(final_K, acceptance['scalar']['K_m3'], rel_tol=1e-13)
        span = (max(tail) - min(tail)) / abs(statistics.mean(tail))
        std = statistics.stdev(tail) / abs(statistics.mean(tail))
        assert math.isclose(span, float(result['window_main_rel_span']), rel_tol=1e-8, abs_tol=1e-12)
        assert math.isclose(std, float(result['window_main_rel_std']), rel_tol=1e-6, abs_tol=1e-12)
        assert span <= 5e-6 and std <= 1e-6
        rows.append(dict(run_id=rec['run_id'], planned_case_id=rec['planned_case_id'],
            direction=config['direction'], dx_nm=float(config['dx_nm']), K_m3=final_K,
            thin_gap_cells=float(config['h_nm']) / float(config['dx_nm']),
            window_steps=n, final_step=int(data[-1]['step']),
            final_time_s=float(data[-1]['time_s']), final_window_span=span,
            final_window_std=std,
            tail_mean_vs_last_relative=abs(statistics.mean(tail) / tail[-1] - 1),
            completion_sha256=sha(run / 'completion.json'),
            acceptance_sha256=sha(acceptance_path), per_run_acceptance=True))
        accepted[rec['run_id']] = acceptance
    metrics = []
    previous_grid = load(PREVIOUS / 'independent_grid_report.json')
    for direction in ('P', 'T'):
        selected = sorted([r for r in rows if r['direction'] == direction], key=lambda r: -r['dx_nm'])
        assert [r['dx_nm'] for r in selected] == [5, 2.5, 1.25]
        cfgs = [kv(next(r['run_config_path'] for r in bound['prepared_runs']
                       if r['run_id'] == point['run_id'])) for point in selected]
        excluded = {'run_id', 'output_directory', 'dx_nm'}
        assert all({k: v for k, v in cfg.items() if k not in excluded} ==
                   {k: v for k, v in cfgs[0].items() if k not in excluded} for cfg in cfgs)
        coarse, mid, fine = [r['K_m3'] for r in selected]
        a, b = coarse - mid, mid - fine
        assert a * b > 0 and min(abs(a), abs(b)) / fine > 1e-14
        p = math.log(abs(a / b)) / math.log(2)
        change = abs(mid / fine - 1)
        gci = 1.25 * change / math.expm1(p * math.log(2))
        original = next(r for r in previous_grid['directions'] if r['direction'] == direction)
        for name, value in [('p', p), ('medium_fine_change', change), ('GCI_fine_estimate', gci)]:
            assert math.isclose(value, original['grid_estimate'][name], rel_tol=1e-11)
        metrics.append(dict(direction=direction, same_physics_except_grid=True,
            K_m3=[coarse, mid, fine], monotonic=True, observed_p=p,
            medium_fine_change=change, medium_fine_limit=0.01,
            GCI_fine_estimate=gci, GCI_limit=0.01,
            GRID_CHECKS_PASS=change <= 0.01 and gci <= 0.01,
            excess_percentage_points=max(0, change - 0.01) * 100,
            neighbor_change_over_largest_final_span=change / max(r['final_window_span'] for r in selected),
            caution='Window variation is not a bound on remaining temporal error; three-grid p is not independent asymptotic proof.'))
    assert metrics[0]['GRID_CHECKS_PASS'] is True and metrics[1]['GRID_CHECKS_PASS'] is False
    save('six_saved_runs.json', rows)
    save('independent_arithmetic.json', metrics)
    save('protected_evidence.json', protected)
    final_drift = [p for p, digest in protected.items() if sha(p) != digest]
    assert not final_drift
    save('verification.json', dict(review_complete=True, release_sha256=expected,
        bound_inputs_verified=len(bound['inputs_sha256']),
        previous_protected_files_verified=len(old_protected),
        all_protected_files_unchanged=len(protected), original_output_files_verified=raw_count,
        directions_recomputed=2, saved_diagnostics_read=6, full_checker_replays=0,
        native_calls=0, builds=0, VTK_reader_calls=0, new_grids=0, retries=0,
        extensions=0, threshold_changes=0, S5_started=False, simulation_authorized=False,
        S4_STAGE_ACCEPTED=False, reference_qualified=False, MODEL_COMPARISON='NOT_EVALUATED',
        physical_validation='NOT_EVALUATED', submission_ready=False))
    print(json.dumps(dict(raw_files=raw_count, protected=len(protected), grid=metrics), ensure_ascii=False))


if __name__ == '__main__':
    main()

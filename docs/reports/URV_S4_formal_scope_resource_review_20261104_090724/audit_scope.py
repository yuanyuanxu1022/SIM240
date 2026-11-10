"""File-only S4 scope/resource review. Never imports a runner or starts a child."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from unittest.mock import patch
import ast
import csv
import json
import shutil
import sys

ROOT = Path('/home/dell/yuanyuanxu/SIM240')
OUT = Path(__file__).resolve().parent
CASE = ROOT / 'CASE/unseen_v2_reference_S4_reuse_v1'
CHECK = ROOT / 'CASE/unseen_v2_reference_checker_S4_reuse_v1'
S2 = ROOT / 'CASE/unseen_v2_reference_S2_reuse_v1'
B = CASE / 'evidence/preparation_B.json'
B_SHA = '7ca2ce3c27076a80d7d692bb13f3030854cf44b683dfe6bcec54ed15c288b06c'
S2_RELEASE = S2 / 'evidence/S2_formal_launch_release_LRP_v1_20261102_02.json'
S2_SHA = 'd08297ebda69d9698d40762f778eb43299fa3c01c35e5591b6d31b4e06ef26cd'
sys.path.insert(0, str(CHECK / 'analysis'))
from evidence import need, sha, kv, exact_parameters
import stage_s4 as stage


def load(p):
    return json.loads(Path(p).read_text())


def save(name, value):
    with (OUT / name).open('x') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


def remember(protected, p):
    p = Path(p)
    need(p.is_file() and not p.is_symlink(), 'missing/symlink evidence: ' + str(p))
    value = sha(p)
    need(str(p) not in protected or protected[str(p)] == value, 'changed protected input')
    protected[str(p)] = value
    return value


def main():
    bound = stage.verify_seal(B, B_SHA)
    stage.verify_zero_receipt(bound)
    need(B.with_suffix('.sha256').read_text().strip() == B_SHA, 'B sidecar mismatch')
    need(len(bound['inputs_sha256']) == 3248, 'unexpected B closure')
    independent = load(bound['independent_zero_review_path'])
    need(sha(bound['independent_zero_review_path']) == bound['independent_zero_review_sha256'], 'review binding')
    need(independent['ZERO_STEP_INDEPENDENT_REVIEW_PASS'] is True and
         independent['eighteen_records_reviewed'] == 18 and independent['actual_VTK_field_rereads'] == 6,
         'independent zero prerequisites incomplete')
    stage.require_pristine(bound['prepared_runs'])
    need(not (CASE / 'launch_attempts').exists() and not (CASE / 'analysis_results').exists(), 'S4 formal path used')
    need(not list(CASE.rglob('completion.json')) and not list(CASE.rglob('diagnostics.csv')), 'S4 time advancement evidence exists')

    protected = dict(bound['inputs_sha256'])
    remember(protected, B)
    remember(protected, B.with_suffix('.sha256'))
    package_files = {}
    for folder in (CASE, CHECK):
        for p in folder.rglob('*'):
            if p.is_file() and '__pycache__' not in p.parts:
                package_files[str(p)] = remember(protected, p)
    old_review = ROOT / 'docs/reports/URV_S4_zero_results_review_20261103_220122'
    for name, digest in load(old_review / 'document_manifest.json').items():
        need(remember(protected, ROOT / name) == digest, 'old S4 review drift: ' + name)
    remember(protected, old_review / 'document_manifest.json')
    for p in (ROOT / 'docs/reports/URV_S4_prerun_scope_review_20261103_200311/PROTOCOL.md',
              ROOT / 'docs/reports/URV_S2_completed_review_20261103_095422/REPORT.md',
              ROOT / 'docs/reports/URV_S2_completed_review_20261103_095422/independent_review.json',
              ROOT / 'docs/reports/URV_S2_perf_results_review_20261102/REPORT.md',
              ROOT / 'docs/reports/URV_S2_perf_results_review_20261102/independent_review.json',
              ROOT / 'docs/reports/URV_S3_formal_scope_review_20261103/PROTOCOL.md'):
        remember(protected, p)

    need(remember(protected, S2_RELEASE) == S2_SHA, 'S2 release changed')
    s2_bound = load(S2_RELEASE)
    for name, digest in s2_bound['inputs_sha256'].items():
        need(remember(protected, name) == digest, 'S2 LRP binding drift')
    s2_review = load(ROOT / 'docs/reports/URV_S2_completed_review_20261103_095422/independent_review.json')
    need(s2_review['S2_SIX_RUN_ACCEPTANCE'] is True and s2_review['release_sha256'] == S2_SHA,
         'S2 completion review missing')
    need(s2_bound['provenance'] == bound['provenance'], 'different S2/S4 build provenance')
    baseline = []
    for rec in s2_bound['approved_runs']:
        run = Path(rec['output_directory'])
        cpath = run / 'completion.json'
        apath = S2 / 'analysis_results' / rec['run_id'] / 'acceptance.json'
        remember(protected, cpath)
        remember(protected, apath)
        c, a, cfg = load(cpath), load(apath), kv(rec['run_config_path'])
        raw = kv(run / 'result.txt')
        need(c['run_id'] == a['run_id'] == rec['run_id'] and
             a['completion_sha256'] == sha(cpath) and
             c['release_sha256'] == a['release_sha256'] == S2_SHA, 'S2 packet association')
        need(c['inputs_before_sha256'] == c['inputs_after_sha256'] == s2_bound['inputs_sha256'] and c['inputs_unchanged'] is True,
             'S2 historical binding failed')
        need(c['independent_process_exit_code'] == a['independent_exit_code'] == 0 and
             c['timed_out'] is False and c['resource_stop_reason'] is None and
             a['RESULT_PASS'] is True and a['NUMERICAL_GATE'] == 'PASS' and a['geometry_PASS'] is True,
             'S2 packet not accepted')
        actual = {str(p.relative_to(run)) for p in run.rglob('*') if p.is_file() and p.name != 'completion.json'}
        need(actual == set(c['output_sha256']), 'S2 raw file set changed')
        for name, digest in c['output_sha256'].items():
            p = (run / name).resolve()
            need(p.is_relative_to(run) and remember(protected, p) == digest, 'S2 raw content drift')
        steps = int(raw['steps_completed'])
        need(a['scalar']['diagnostic_rows'] == steps + 1, 'S2 step count')
        baseline.append(dict(run_id=rec['run_id'], direction=cfg['direction'], dx_nm=float(cfg['dx_nm']),
            h_nm=float(cfg['h_nm']), d_nm=float(cfg['d_nm']), nodes=exact_parameters(cfg)['nodes'],
            steps=steps, elapsed_seconds=c['elapsed_seconds'], elapsed_hours=c['elapsed_seconds']/3600,
            average_seconds_per_completed_step=c['elapsed_seconds']/steps,
            output_files=len(c['output_sha256']), output_bytes=sum((run/n).stat().st_size for n in actual),
            completion_sha256=sha(cpath), acceptance_sha256=sha(apath), RESULT_PASS=True))

    perf_dir = ROOT / 'docs/reports/URV_S2_perf_results_review_20261102'
    perf = load(perf_dir / 'independent_review.json')
    need(perf['both_directions_independently_sufficient'] is True, 'S2 PERF reviewed evidence absent')
    recovery_path = ROOT / 'docs/reports/URV_S2_LRP_launch_release_20261102/recovery_manifest.json'
    recovery = load(recovery_path)
    remember(protected, recovery_path)
    need(s2_bound['inputs_sha256'].get(str(recovery_path)) == sha(recovery_path), 'LRP recovery record not bound by accepted S2')
    exception = recovery['exception']
    need(recovery['protocol'] == 'S2-LRP-v1' and recovery['PERF_resource_prerequisite'] == 'RETAINED_WITH_DOCUMENTED_LOG_EXCEPTION', 'LRP scope changed')
    changed = []; intact = 0
    for name, digest in load(perf_dir / 'raw_evidence_sha256.json').items():
        current = remember(protected, name)
        if current != digest:
            need(name == exception['original_path'] and digest == exception['expected_original_sha256'] and current == exception['current_sha256'], 'new unapproved PERF evidence drift')
            snap = Path(exception['snapshot_path'])
            need(remember(protected, snap) == current == exception['snapshot_sha256'] and
                 s2_bound['inputs_sha256'].get(str(snap)) == current and Path(name).stat().st_size == exception['current_size_bytes'], 'LRP exact snapshot drift')
            changed.append(dict(path=name, original_sha256=digest, current_sha256=current, snapshot_path=str(snap)))
        else: intact += 1
    need(len(changed) == 1 and intact == 61, 'historical PERF difference set changed')
    save('PERF_log_exception.json', dict(protocol='S2-LRP-v1', recovery_record_path=str(recovery_path), recovery_record_sha256=sha(recovery_path), unchanged_raw_files=intact, known_log_changes=changed, old_full_raw_closure_intact=False, resource_use='RETAINED_WITH_DOCUMENTED_LOG_EXCEPTION', new_exception_created=False))
    remember(protected, perf_dir / 'raw_evidence_sha256.json')
    perf_summary = [dict(direction=r['direction'], source_run_id=r['run_id'],
        status=r['PERF_OUTCOME'], observed_RSS_peak_GiB=r['observed_RSS_peak_GiB'],
        last_complete_step=r['last_complete_step'], exact_collide_and_stream_calls=r['exact_collide_and_stream_calls'],
        complete_window_observed=r['full_window_cost_observed']) for r in perf['direction_reviews']]

    scopes, scenarios = [], []
    for index, rec in enumerate(bound['prepared_runs'], 1):
        cfg = kv(rec['run_config_path'])
        p = exact_parameters(cfg)
        cap = stage.RESOURCES['solver_wall_cap_seconds_by_dx_nm'][str(int(float(cfg['dx_nm']))) if float(cfg['dx_nm']) == 5 else str(float(cfg['dx_nm']))]
        scopes.append(dict(order=index, **rec, direction=cfg['direction'], dx_nm=float(cfg['dx_nm']),
            parameters=p, solver_wall_cap_seconds=cap, per_checker_wait_cap_seconds=3600,
            approved=False, formal_started=False))
        if float(cfg['dx_nm']) == 1.25:
            old = next(r for r in baseline if r['direction'] == cfg['direction'] and r['dx_nm'] == 1.25)
            ratio = p['nodes']/old['nodes']
            per_step = old['average_seconds_per_completed_step']
            scenarios.append(dict(direction=cfg['direction'], old_actual_hours=old['elapsed_hours'],
                old_actual_steps=old['steps'], S4_max_steps=p['cap'], S4_to_S2_fluid_node_ratio=ratio,
                S2_mean_seconds_per_step=per_step,
                if_S2_mean_cost_per_step_and_S4_full_step_cap_hours=per_step*p['cap']/3600,
                if_node_scaled_cost_per_step_and_S4_full_step_cap_hours=ratio*per_step*p['cap']/3600,
                twelve_hour_step_budget_if_S2_mean_cost=43200/per_step,
                twelve_hour_step_budget_if_node_scaled_cost=43200/(ratio*per_step),
                convergence_prediction=False, measured_S4_throughput=False, time_guarantee=False))

    # Inspect frozen code rather than running any controller or synthesizing execution authority.
    runner = CASE / 'scripts/run_S4.py'
    checker = CHECK / 'analysis/check_results.py'
    authority = CHECK / 'analysis/stage_s4.py'
    for p in (runner, checker, authority): ast.parse(p.read_text())
    runner_text, checker_text, authority_text = runner.read_text(), checker.read_text(), authority.read_text()
    need('timeout=3600' in runner_text and 'timeout=3600' in checker_text, 'checker/reader budgets changed')
    need("decision.get('per_checker_wait_cap_seconds') == 3600" in authority_text and
         "decision.get('resource_decision_accepted') is True" in authority_text,
         'resource adoption guard missing')
    need('for record in bound[\'prepared_runs\']' in runner_text and 'solver_runs=6' in runner_text,
         'six-run control coverage')
    need("S4_grid_report.json" in runner_text and "S4_completed.json" in runner_text, 'grid completion endpoints')
    need("'S5_authorized'" in authority_text, 'S5 boundary missing')
    with (OUT / 'six_run_scope.csv').open('x', newline='') as stream:
        fields = ['order','run_id','planned_case_id','direction','dx_nm','solver_wall_cap_seconds','per_checker_wait_cap_seconds']
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction='ignore')
        writer.writeheader(); writer.writerows(scopes)
    save('six_run_scope.json', scopes)
    save('resource_evidence.json', dict(S2_completed_baselines=baseline, S2_finite_PERF=perf_summary,
        conditional_scenarios=scenarios, S4_sustained_performance_measured=False,
        S4_peak_memory_measured=False, S4_convergence_steps_known=False,
        historical_PERF_log_exception='S2-LRP preserved; this review does not reclassify the old binding as drift-free'))

    # One resource snapshot; not a reservation and not an execution binding check.
    mem = next(int(s.split()[1])*1024 for s in Path('/proc/meminfo').read_text().splitlines() if s.startswith('MemAvailable:'))
    disk = shutil.disk_usage(CASE).free
    active = []
    for folder in Path('/proc').iterdir():
        if not folder.name.isdecimal(): continue
        try:
            args = (folder/'cmdline').read_bytes().split(b'\0')
            names = [Path(x.decode(errors='replace')).name for x in args if x]
            if any(n == 'urv_reference' or n.startswith(('run_S4.py','audit_S4_zero.py','run_S2_perf.py')) for n in names):
                active.append(dict(pid=int(folder.name), executable=names[0] if names else None,
                                   relevant_arguments=[n for n in names if n == 'urv_reference' or n.endswith('.py')]))
        except (FileNotFoundError, ProcessLookupError, PermissionError): pass
    save('resource_snapshot.json', dict(client_date='2026-11-04',observed_at=datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),
        MemAvailable_bytes=mem, MemAvailable_GiB=mem/1024**3, disk_free_bytes=disk,disk_free_GiB=disk/1024**3,
        required_RAM_GiB=12,required_initial_disk_GiB=100, snapshot_meets_thresholds=mem>=12*1024**3 and disk>=100*1024**3,
        active_relevant_processes=active, snapshot_is_reservation=False,
        conflict_scope='target native/S4 controller processes only; fresh comprehensive conflict check required at binding'))
    need(sum(s['solver_wall_cap_seconds'] for s in scopes) == 34*3600, 'solver budget arithmetic')
    need(sum(s['per_checker_wait_cap_seconds'] for s in scopes) == 6*3600, 'checker budget arithmetic')
    save('protected_inputs_before.json', protected)
    save('package_file_set_before.json', package_files)
    need(all(sha(p) == h for p,h in protected.items()), 'read-only review changed evidence')
    save('scope_audit.json', dict(PASS=True,B_sha256=B_SHA,B_inputs_verified=3248,
        original_B_and_raw_evidence_unchanged=True,S4_zero_prerequisites_verified=True,
        formal_output_directories_pristine=6,S2_raw_outputs_verified=sum(r['output_files'] for r in baseline),
        S2_completed_baselines=6,protected_files=len(protected),frozen_runner_static_compatible=True,
        requires_implementation_for_full_original_six=False,requires_new_PERF_for_recommended_risk_accepted_route=False,
        requires_explicit_resource_adoption=True,requires_separate_formal_authorization=True,
        solver_budget_hours=34,checker_wait_budget_hours=6,strict_batch_wall_cap_established=False,
        native_calls=0,VTK_reads=0,builds=0,tests_rerun=0,CASE_writes=0,
        formal_authorization_generated=False,formal_release_generated=False,start_command_generated=False,
        formal_started=False,PERF_started=False,S5_started=False))
    print(json.dumps(dict(PASS=True,B_inputs=3248,S2_raw_outputs=222,protected_files=len(protected),
        scopes=6,native_calls=0,VTK_reads=0,CASE_writes=0,conditional_scenarios=scenarios),ensure_ascii=False))


if __name__ == '__main__':
    with patch('subprocess.Popen', side_effect=AssertionError('No child in file-only scope review')):
        main()

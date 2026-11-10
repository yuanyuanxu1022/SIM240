"""Review existing S4 packets only; never launch a solver or modify frozen evidence."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import csv, hashlib, json, math, os, resource, subprocess, sys
import numpy as np

ROOT = Path('/home/dell/yuanyuanxu/SIM240')
OUT = Path(__file__).resolve().parent
CASE = ROOT/'CASE/unseen_v2_reference_S4_reuse_v1'
CHECKER = ROOT/'CASE/unseen_v2_reference_checker_S4_reuse_v1'
RELEASE = CASE/'evidence/S4_formal_launch_release_v1_20261104_01.json'
DIGEST = 'e5f7de1e584b776f8cc9bf1dbb31f198422ce10984ba8ad7d729220afdcdd19b'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
load = lambda p: json.loads(Path(p).read_text())

def save(name, value):
    with (OUT/name).open('x') as f:
        json.dump(value, f, ensure_ascii=False, indent=2); f.write('\n')

def limits():
    resource.setrlimit(resource.RLIMIT_AS, (8*1024**3, 8*1024**3))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))

def main():
    snapshot = load(OUT/'status_snapshot.json')
    assert not snapshot['processes']
    assert all(r['completion_exists'] and r['automatic_acceptance_exists'] for r in snapshot['runs'])
    assert sha(RELEASE) == DIGEST
    bound = load(RELEASE)
    protected = dict(bound['inputs_sha256'])
    assert all(sha(p) == h for p, h in protected.items())
    for tree in [CASE/'runs', CASE/'analysis_results', CASE/'evidence', CASE/'launch_attempts',
                 CHECKER, ROOT/'docs/reports/URV_S4_formal_launch_release_20261104_092838',
                 ROOT/'docs/reports/URV_S4_formal_scope_resource_review_20261104_090724',
                 ROOT/'docs/reports/URV_S4_zero_results_review_20261103_220122']:
        for p in tree.rglob('*'):
            if p.is_file():
                assert not p.is_symlink()
                h = sha(p)
                assert str(p) not in protected or protected[str(p)] == h
                protected[str(p)] = h
    for p in [RELEASE, RELEASE.with_suffix('.sha256'), CASE/'S4_formal_controller_v1_20261104_01.log']:
        protected[str(p)] = sha(p)
    save('protected_inputs_and_outputs.json', protected)
    sys.path.insert(0, str(CHECKER/'analysis'))
    import stage_s4, s4_grid, evidence
    stage_s4.verify_seal(RELEASE, DIGEST)
    stage_s4.validate_formal_authority(bound)
    assert len(bound['prepared_runs']) == 6
    attempt = CASE/'launch_attempts'/DIGEST
    automatic_grid = load(attempt/'S4_grid_report.json')
    assert not (attempt/'S4_completed.json').exists()
    assert (CASE/'S4_formal_controller_v1_20261104_01.log').read_text() == 'EvidenceError: S4 grid evidence failed; no retry/extension/next stage\n'
    env = dict(os.environ, OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1',
               QT_QPA_PLATFORM='offscreen', PYTHONDONTWRITEBYTECODE='1')
    env.pop('LD_LIBRARY_PATH', None); env.pop('LD_PRELOAD', None)
    reviewed = []; accepted = {}; frame_count = 0
    for record in bound['prepared_runs']:
        rid = record['run_id']; run = Path(record['output_directory']); target = OUT/('replay_'+rid)
        command = ['/home/dell/miniconda3/bin/python3', '-B', str(CHECKER/'analysis/check_results.py'),
                   '--run', str(run), '--release', str(RELEASE), '--release-sha256', DIGEST, '--out', str(target)]
        assert Path(command[2]).name == 'check_results.py' and '--execute' not in command
        with (OUT/(rid+'_checker.log')).open('x') as log:
            proc = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, env=env,
                                  timeout=3600, preexec_fn=limits)
        save('checker_exit_'+rid+'.json', dict(command=command, exit_code=proc.returncode, solver_executed=False))
        assert proc.returncode == 0, (rid, proc.returncode)
        a = load(target/'acceptance.json'); fields = load(target/'fields.json')
        assert a == load(CASE/'analysis_results'/rid/'acceptance.json')
        assert fields == load(CASE/'analysis_results'/rid/'fields.json')
        assert fields['PASS'] and fields['actual_reader']
        accepted[rid] = a; frame_count += len(fields['frames'])
        c = load(run/'completion.json')
        assert c['inputs_before_sha256'] == c['inputs_after_sha256'] == bound['inputs_sha256']
        assert c['inputs_unchanged'] and c['release_sha256'] == DIGEST
        assert c['independent_process_exit_code'] == 0 and not c['timed_out'] and c['resource_stop_reason'] is None
        assert c['elapsed_seconds'] <= c['solver_wall_cap_seconds']
        assert c['density_capture'] == 'NOT_APPLICABLE_S0_ONLY'
        assert c['resources_before']['MemAvailable_bytes'] >= 12*1024**3
        assert c['resources_before']['disk_free_bytes'] >= 8*1024**3
        raw = {str(p.relative_to(run)):sha(p) for p in run.rglob('*') if p.is_file() and p.name != 'completion.json'}
        assert raw == c['output_sha256']
        cfg = evidence.kv(run/'run_config.txt'); r = evidence.kv(run/'result.txt'); p = evidence.exact_parameters(cfg)
        with (run/'diagnostics.csv').open() as f: rows = list(csv.DictReader(f))
        x = {k:np.array([float(z[k]) for z in rows]) for k in rows[0]}
        assert np.array_equal(x['step'], np.arange(len(rows))) and all(np.isfinite(z).all() for z in x.values())
        assert len(rows) == int(r['steps_completed'])+1
        J = float(x['J'][-1]); K = p['nu']*J/p['a']; assert K == a['scalar']['K_m3']
        mass = (x['corrected_mass']-x['corrected_mass'][0])/x['corrected_mass'][0]
        delta = (x['density_delta']-x['density_delta'][0])/(p['nodes']+x['density_delta'][0])
        legacy = (x['mass']-x['mass'][0])/x['mass'][0]
        n = p['window']; last = x['J'][-n:]; prev = x['J'][-n-1:-1]
        std = float(np.std(last, ddof=1)/abs(np.mean(last))); span = float(np.ptp(last)/abs(np.mean(last)))
        prevstd = float(np.std(prev, ddof=1)/abs(np.mean(prev))); prevspan = float(np.ptp(prev)/abs(np.mean(prev)))
        cross = -x['Jx'] if cfg['direction'] == 'P' else x['Jy']
        allstd, allspan, allcross = evidence.window_metrics(x['J'], cross, n)
        passes = (allstd <= 1e-6)&(allspan <= 5e-6)&(allcross <= 1e-12)
        assert passes[-1] and not passes[:-1].any()
        assert prevstd > 1e-6 or prevspan > 5e-6 or max(abs(cross[-n-1:-1])) > 1e-12
        rho = float(x['max_density_deviation'].max()); mach = float(x['Mach'].max())
        reynolds = mach/math.sqrt(3)*p['dx']/p['dt']*(p['h']+p['d'])/p['nu']
        den = np.maximum(abs(x['Q_section1']), abs(x['Q_section2']))
        sec = np.divide(abs(x['Q_section1']-x['Q_section2']), den, out=np.zeros_like(den), where=den > 0)
        volume = float(r['fluid_volume_m3'])/(p['P']*p['Ly']*p['H'])-1
        v = dict(run_id=rid, direction=cfg['direction'], dx_nm=float(cfg['dx_nm']), acceleration_m_s2=p['a'],
                 steps=len(rows)-1, diagnostic_rows=len(rows), full_windows=len(allstd), window_steps=n,
                 solver_seconds=c['elapsed_seconds'], solver_cap_seconds=c['solver_wall_cap_seconds'],
                 J_m2_s=J, K_m3=K, U_mean_m_s=J/p['H'], R_Pa_s_per_m3=.001/K,
                 window_std=std, window_span=span, previous_window_std=prevstd, previous_window_span=prevspan,
                 first_accepted_window_is_final=True, cross_flux_window_max=float(allcross[-1]),
                 corrected_mass_max=float(abs(mass).max()), legacy_mass_max=float(abs(legacy).max()),
                 ledger_max=float(abs(mass-delta).max()), density_deviation_max=rho, Mach_max=mach, Re_H_max=reynolds,
                 section_final=float(sec[-1]), volume_relative_error=volume, core_fluid_nodes=p['nodes'],
                 installed_links=int(r['installed_links']), fallback=int(r['fallback_count']), unresolved=int(r['unresolved_links']),
                 q_min=float(r['q_min']), q_max=float(r['q_max']), field_frames=len(fields['frames']),
                 raw_files=len(raw), raw_bytes=sum((run/f).stat().st_size for f in raw),
                 completion_sha256=sha(run/'completion.json'), original_and_replay_acceptance_equal=True,
                 original_and_replay_fields_equal=True, checker_exit=0, NUMERICAL_GATE=a['NUMERICAL_GATE'],
                 geometry_PASS=a['geometry_PASS'], RESULT_PASS=a['RESULT_PASS'], REFERENCE_QUALIFIED_FOR_CASE=False,
                 density_capture='NOT_APPLICABLE_S0_ONLY', smooth_profile='NOT_APPLICABLE_GROOVED_CASE')
        assert abs(mass).max() < 1e-10 and abs(mass-delta).max() <= 1e-13 and rho <= 1e-6 and mach < .05 and reynolds <= .01
        assert std <= 1e-6 and span <= 5e-6 and sec[-1] <= 1e-5 and abs(volume) <= 1e-10
        assert v['raw_bytes'] <= 4*1024**3
        reviewed.append(v); save('progress_'+str(len(reviewed))+'.json', v)
        print(json.dumps(dict(done=rid, K=K, steps=v['steps'], frames=v['field_frames'])), flush=True)
    reports = [s4_grid.grid_for_direction(bound, d, accepted, DIGEST) for d in ('P', 'T')]
    expected = dict(stage='S4_THIN_GRID', directions=reports, GRID_CHECKS_PASS=all(r['GRID_CHECKS_PASS'] for r in reports),
                    reference_qualified=False, MODEL_COMPARISON='NOT_EVALUATED', next_stage_started=False)
    assert expected == automatic_grid
    independent_grid = []
    for report in reports:
        d = report['direction']; pts = [v for v in reviewed if v['direction'] == d]
        coarse, medium, fine = [v['K_m3'] for v in pts]
        a, b = coarse-medium, medium-fine
        assert a*b > 0 and min(abs(a), abs(b))/fine > 1e-14
        order = math.log(abs(a/b))/math.log(2)
        change = abs(medium/fine-1); gci = 1.25*change/math.expm1(order*math.log(2))
        assert math.isclose(order, report['grid_estimate']['p'], rel_tol=1e-14)
        assert math.isclose(gci, report['grid_estimate']['GCI_fine_estimate'], rel_tol=1e-14)
        assert change == report['grid_estimate']['medium_fine_change']
        ok = math.isfinite(order) and order > 0 and change <= .01 and gci <= .01
        assert ok == report['GRID_CHECKS_PASS']
        independent_grid.append(dict(direction=d, K_m3=[coarse, medium, fine], observed_order=order,
            medium_fine_change_percent=100*change, GCI_fine_percent=100*gci,
            change_gate_PASS=change <= .01, GCI_gate_PASS=gci <= .01, GRID_CHECKS_PASS=ok,
            exact_controller_receipt=True))
    assert reports[0]['GRID_CHECKS_PASS'] and not reports[1]['GRID_CHECKS_PASS']
    drift = [p for p, h in protected.items() if sha(p) != h]
    assert not drift, drift
    result = dict(reviewed_at=datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),
        protocols=['URV-v1','MRP','A1','S4-MIP-v1','S4-FRD-v1'], release_sha256=DIGEST,
        inputs_verified=len(bound['inputs_sha256']), protected_files_unchanged=len(protected),
        full_checker_replays=6, actual_VTK_reader_invocations=6, total_field_frames_read=frame_count,
        all_receipts_and_fields_exact=True, runs=reviewed, grid=independent_grid,
        diagnostic_rows=sum(v['diagnostic_rows'] for v in reviewed), full_windows=sum(v['full_windows'] for v in reviewed),
        formal_solver_seconds=sum(v['solver_seconds'] for v in reviewed),
        SIX_RUN_ACCEPTANCE=True, S4_GRID_CHECKS_PASS=False, S4_STAGE_ACCEPTED=False,
        disposition='ENDED_STOPPED_AT_TRANSVERSE_GRID_GATE', independent_parent_controller_exit_code='NOT_RECORDED',
        solver_calls=0, builds=0, retries=0, extensions=0, S5_started=False,
        REFERENCE_QUALIFIED_FOR_CASE=False, reference_qualified=False, MODEL_COMPARISON='NOT_EVALUATED',
        physical_validation='NOT_EVALUATED', strict_error_bound_established=False, submission_ready=False,
        F04='OPEN', human_scientific_final_review=False)
    save('independent_review.json', result)
    save('independent_grid_report.json', expected)
    with (OUT/'run_summary.csv').open('x') as f:
        writer = csv.DictWriter(f, fieldnames=list(reviewed[0])); writer.writeheader(); writer.writerows(reviewed)
    print('REVIEW_COMPLETE '+str(OUT), flush=True)

if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        save('review_failure.json', dict(error=type(error).__name__+': '+str(error), solver_executed=False))
        raise

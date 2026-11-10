"""Read existing S2 zero evidence only. The only subprocesses are VTK readers."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from itertools import repeat
import csv
import json
import math
import os
import resource
import subprocess
import sys
import time
import numpy as np

REPORT = Path(__file__).resolve().parent
ROOT = REPORT.parents[2]
CASE = ROOT/'CASE/unseen_v2_reference_S2_reuse_v1'
CHECKER = ROOT/'CASE/unseen_v2_reference_checker_S2_reuse_v1'
sys.path.insert(0, str(CHECKER/'analysis'))
from evidence import need, sha, kv, rows, save, close, exact_parameters, check_boundary
from stage_s2 import verify_seal, validate_zero_authority, validate_zero_plan, CASES, MODES

RELEASE = CASE/'evidence/S2_zero_launch_release_reuse_v1_20261102_01.json'
RELEASE_SHA = '4b6759d061bc59079556c3a3b4bb34a7a8970b2f6529d4fa0cebeb1bdc1925c0'
AUDIT = CASE/'audits/URV_S2_ZERO_20261102_01'


def reader_limits():
    resource.setrlimit(resource.RLIMIT_AS, (8*1024**3, 8*1024**3))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))


def write_csv(path, records):
    with path.open('x', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(records[0]))
        writer.writeheader(); writer.writerows(records)


def scalar_oracles(dx, count):
    # rho=1 initial condition: binary64 operations matching the frozen observer.
    # This is initial scalar arithmetic verification, not density replay.
    partial = ((1.*1000.)*dx)*dx
    volume_term = (dx*dx)*dx
    mass = volume = 0.
    for _ in range(count):
        mass = math.fma(partial, dx, mass)
        volume += volume_term
    return dict(legacy=mass, volume=volume, corrected=math.fsum(repeat(partial*dx, count)))


def initial_slice(run, cfg, p):
    records = rows(run/'field_slice.csv')
    need(len(records)*p['ny'] == p['nodes'], 'double slice core coverage')
    values = {k: np.array([float(row[k]) for row in records]) for k in records[0]}
    need(all(np.isfinite(v).all() for v in values.values()), 'nonfinite initial double slice')
    x, z = values['x'], values['z']
    ix = np.rint(x/p['dx']-.5).astype(int); iz = np.rint(z/p['dx']-.5).astype(int)
    need(close(x, (ix+.5)*p['dx']) and close(z, (iz+.5)*p['dx']), 'slice lattice/units')
    need(len(set(zip(ix, iz))) == len(records), 'duplicate slice core cell')
    groove = (x >= (p['P']-p['w'])/2) & (x < (p['P']+p['w'])/2)
    need(np.all((ix>=0)&(ix<p['nx'])&(z>=0)&(z<p['h']+p['d']*groove)), 'slice solid or overlap')
    need(np.all(values['material']==1) and np.all(values['rho']==1) and np.all(values['pressure']==0),
         'initial material/density/pressure mismatch')
    speed = p['a']*p['dt']/2
    for axis in 'xyz':
        expected = speed if axis == ('y' if cfg['direction']=='P' else 'x') else 0.
        need(close(values['u'+axis], expected), 'initial double velocity/half-force mismatch')
    need(close(values['speed'], speed) and np.all(values['Phi']>=0), 'initial speed/dissipation')
    for filename, key in [('velocity_profile.csv','velocity'), ('pressure_profile.csv','pressure'),
                          ('energy_dissipation.csv','Phi')]:
        profile = rows(run/filename)
        slices = p['ny'] if cfg['direction']=='P' else p['nx']
        need(len(profile)==slices, 'initial profile coverage')
        positions = np.array([float(r['position']) for r in profile])
        data = np.array([float(r[key]) for r in profile])
        need(close(positions, (np.arange(slices)+.5)*p['dx']) and np.isfinite(data).all(), 'profile units/finite')
        if key=='velocity': need(close(data, speed), 'initial profile velocity')
        elif key=='pressure': need(np.all(data==0), 'initial profile pressure')
        else: need(np.all(data>=0), 'initial profile dissipation')
    return dict(double_slice_rows=len(records), rho_min=1., rho_max=1.,
                pressure_min_Pa=0., pressure_max_Pa=0., Phi_min=float(values['Phi'].min()),
                Phi_max=float(values['Phi'].max()), expected_U_main_m_s=speed)


def main():
    bound = verify_seal(RELEASE, RELEASE_SHA)
    validate_zero_authority(bound); plan = validate_zero_plan(bound)
    worker = json.loads((AUDIT/'verification.json').read_text())
    need(worker['audit_release_sha256']==RELEASE_SHA and Path(worker['audit_release_path'])==RELEASE,
         'worker/release identity')
    need(worker['preparation_A_sha256']==bound['preparation_A_sha256'], 'worker/A identity')
    need([(x['planned_case_id'],x['mode']) for x in worker['records']] == [(c,m) for c in CASES for m in MODES],
         'worker coverage/order')
    raw_manifest = Path(worker['raw_manifest_path'])
    need(sha(raw_manifest)==worker['raw_manifest_sha256'], 'raw manifest binding')
    raw = json.loads(raw_manifest.read_text())
    actual = {str(p) for p in AUDIT.rglob('*') if p.is_file()}
    need(actual==set(raw)|{str(raw_manifest),str(AUDIT/'verification.json')}, 'raw output inventory')
    need(all(sha(p)==h for p,h in raw.items()), 'raw output hash drift')
    progress = sorted((AUDIT/'progress').glob('*.json'))
    need(len(progress)==18, 'progress incomplete')
    summaries = []; calls = []; initial = []; oracles = {}
    for index, (record, work) in enumerate(zip(plan,worker['records'])):
        run = Path(record['output_directory']); cfg = kv(record['run_config_path']); p = exact_parameters(cfg)
        need(json.loads(progress[index].read_text())==work, 'progress/worker record mismatch')
        need(work['run_id']==record['run_id'] and Path(work['output'])==run, 'worker native identity')
        need(work['native_exit_code']==0 and work['collide_and_stream_calls']==0, 'worker native exit/steps')
        process = json.loads((run/'process_receipt.json').read_text())
        need(process['independent_process_exit_code']==0 and not process['timed_out'] and
             process['resource_stop_reason'] is None and process['solver_wall_cap_seconds']==300 and
             0<=process['elapsed_seconds']<=300, 'independent native process guard')
        need((run/'exit_code.txt').read_text().strip()=='0', 'independent exit file')
        execution = kv(run/'execution_audit.txt')
        need(execution['preparation_only_build']=='0' and execution['collide_and_stream_calls']=='0', 'native advancement')
        need(not (run/'diagnostics.csv').exists() and not (run/'mass_capture').exists(), 'steady or S0 capture present')
        mem = work['resources_before']['MemAvailable_bytes']; disk = work['resources_before']['disk_free_bytes']
        need(mem>=12*1024**3 and disk>=(100 if index==0 else 8)*1024**3, 'original resource guards')
        effective = kv(run/'effective_config.txt')
        need(effective['run_id']==record['run_id'] and effective['mode']==record['mode'] and
             effective['formal_simulation']=='false', 'effective identity/mode')
        need(effective['direction']==('parallel' if cfg['direction']=='P' else 'perpendicular'), 'direction mapping')
        for key,value in [('h_m',p['h']),('d_m',p['d']),('w_m',p['w']),('Lx_m',p['P']),('Ly_m',p['Ly']),
                          ('dx_m',p['dx']),('dt_s',p['dt']),('nu_m2_s',p['nu']),('acceleration_m_s2',p['a']),
                          ('plan_area_m2',p['P']*p['Ly']),('nominal_volume_m3',p['H']*p['P']*p['Ly'])]:
            need(close(float(effective[key]),value), 'parameter/unit mismatch '+key)
        need(int(effective['nx'])==p['nx'] and int(effective['ny'])==p['ny'] and
             int(effective['window_steps'])==p['window'] and int(effective['maximum_steps'])==p['cap'], 'exact-step arithmetic')
        geometry = None
        if record['mode']!='describe':
            geometry = check_boundary(cfg,kv(run/'boundary_audit.txt'))
            need(geometry==work['geometry'], 'worker and independently recomputed geometry differ')
        if record['mode']=='precheck':
            result = kv(run/'result.txt')
            need(result['run_id']==record['run_id'] and result['formal_simulation']=='false' and
                 result['collide_and_stream_calls']=='0' and result['exit_code']=='0', 'precheck identity/exit')
            need(result['geometry_PASS']==result['converter_PASS']==result['q_audit_PASS']=='true','precheck flags')
            need(int(result['fluid_nodes'])==p['nodes'] and int(result['candidate_links'])==int(result['installed_links'])==geometry['candidate_links'] and
                 int(result['fallback_count'])==0, 'precheck nodes/links')
        if record['mode']=='initialize':
            result = kv(run/'result.txt'); volume = float(result['fluid_volume_m3'])
            need(result['run_id']==record['run_id'] and result['formal_simulation']=='false' and
                 result['collide_and_stream_calls']==result['steps_completed']=='0' and result['exit_code']=='0', 'initial identity/exit')
            need(result['NUMERICAL_GATE']=='NOT_EVALUATED' and result['RESULT_PASS']=='false', 'zero scientific status')
            need(result['geometry_PASS']==result['q_audit_PASS']==result['finite']=='true', 'initial flags')
            need(int(result['fluid_nodes'])==p['nodes'] and int(result['frames_written'])==1, 'initial frame/count')
            need(close(volume,p['P']*p['Ly']*p['H'],rtol=1e-10) and close(float(result['nominal_volume_m3']),p['P']*p['Ly']*p['H']), 'initial volume gate')
            dx = float(effective['dx_m']); cache = (dx,p['nodes'])
            if cache not in oracles: oracles[cache]=scalar_oracles(dx,p['nodes'])
            oracle = oracles[cache]
            need(float(result['mass'])==oracle['legacy'], 'MRP initial legacy FMA path mismatch')
            need(volume==oracle['volume'], 'A1 initial rounded volume path mismatch')
            need(float(result['corrected_mass'])==oracle['corrected'], 'initial compensated mass mismatch')
            need(float(result['density_delta'])==float(result['max_density_deviation'])==0, 'initial rho/delta')
            U = p['a']*p['dt']/2; expected = np.zeros(3); expected[1 if cfg['direction']=='P' else 0]=p['H']*U
            nativeJ = np.array([float(x) for x in result['J_vector_m2_s'].split(',')])
            need(close(nativeJ,expected,rtol=1e-6,atol=1e-30), 'initial half-force flux')
            expectedMach = U*p['dt']/p['dx']*math.sqrt(3)
            need(close(float(result['max_Mach']),expectedMach) and float(result['max_Mach'])<.05, 'initial Mach')
            frame = rows(run/'frame_index.csv')
            need(len(frame)==1 and int(frame[0]['step'])==0 and float(frame[0]['time_s'])==float(frame[0]['tstar'])==0,
                 'initial frame timing')
            slices = initial_slice(run,cfg,p)
            reader = json.loads(Path(work['field_readback']).read_text())
            need(sha(work['field_readback'])==work['field_readback_sha256'] and reader['PASS'] is True and reader['actual_reader'] is True,
                 'stored independent field receipt binding')
            reader_process = json.loads(Path(work['field_readback']).with_suffix('.process.json').read_text())
            need(reader_process['independent_exit_code']==0 and not reader_process['timed_out'] and
                 0<=reader_process['elapsed_seconds']<=300, 'original field-reader process guard')
            initial.append((record,work))
            summaries.append(dict(planned_case_id=record['planned_case_id'],direction=cfg['direction'],dx_nm=float(cfg['dx_nm']),
                fluid_nodes=p['nodes'],wall_links=geometry['candidate_links'],q_min=geometry['q_min'],q_max=geometry['q_max'],
                volume_m3=volume,volume_relative_error=abs(volume/(p['H']*p['P']*p['Ly'])-1),
                legacy_mass_kg=float(result['mass']),legacy_initial_FMA_exact=True,corrected_mass_kg=float(result['corrected_mass']),
                compensated_initial_exact=True,A1_volume_path_exact=True,density_delta=0.,max_density_deviation=0.,
                J_main_m2_s=float(nativeJ[1 if cfg['direction']=='P' else 0]),expected_initial_J_m2_s=p['H']*U,
                Mach=float(result['max_Mach']),slice_rows=slices['double_slice_rows'],Phi_min=slices['Phi_min'],Phi_max=slices['Phi_max']))
        calls.append(dict(run_id=record['run_id'],planned_case_id=record['planned_case_id'],mode=record['mode'],
                          native_exit=0,actual_time_steps=0,geometry_checked=geometry is not None,elapsed_s=process['elapsed_seconds']))
        print('native evidence PASS '+record['planned_case_id']+' '+record['mode'],flush=True)
    save(REPORT/'native_review.json',dict(PASS=True,calls=calls,initial_statistics=summaries,
        raw_manifest_files=len(raw),total_audit_files=len(actual),source_inputs_current=True,
        density_capture='NOT_APPLICABLE_S0_ONLY',MRP_check_scope='initial scalar arithmetic only, no new rho capture/replay'))
    write_csv(REPORT/'initial_statistics.csv',summaries)
    write_csv(REPORT/'native_calls.csv',calls)
    env = dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1',
               QT_QPA_PLATFORM='offscreen',PYTHONDONTWRITEBYTECODE='1')
    reads = []
    for record, work in initial:
        out = REPORT/('field_reread_'+record['planned_case_id']+'.json')
        log = REPORT/('field_reread_'+record['planned_case_id']+'.log')
        command = ['/usr/bin/pvpython','--force-offscreen-rendering','-B',str(CHECKER/'analysis/read_fields.py'),
                   '--run',record['output_directory'],'--out',str(out)]
        started = time.monotonic()
        with log.open('x') as stream:
            process = subprocess.run(command,stdout=stream,stderr=subprocess.STDOUT,env=env,preexec_fn=reader_limits,timeout=300)
        elapsed = time.monotonic()-started
        need(process.returncode==0,'fresh VTK reader failed')
        fresh = json.loads(out.read_text()); old = json.loads(Path(work['field_readback']).read_text())
        need(fresh['PASS'] is True and fresh['actual_reader'] is True and fresh['solver_executed'] is False and
             len(fresh['frames'])==1 and fresh['frames'][0]['step']==0,'fresh reader actual/frame/status')
        need(fresh['payload_sha256']==old['payload_sha256'] and fresh['frames']==old['frames'], 'fresh/stored reader mismatch')
        need(all(sha(p)==h for p,h in fresh['payload_sha256'].items()), 'VTK payload hash drift')
        reads.append(dict(planned_case_id=record['planned_case_id'],argv=command,independent_exit_code=0,
            elapsed_seconds=elapsed,receipt_path=str(out),receipt_sha256=sha(out),actual_reader=True,
            frames=1,core_nodes=fresh['frames'][0]['unique_fluid_nodes'],payload_files=len(fresh['payload_sha256']),
            stored_and_fresh_receipts_equal=True))
        save(REPORT/'reader_progress'/f'{len(reads):02d}.json',reads[-1])
        print('fresh field reread PASS '+record['planned_case_id'],flush=True)
    need(len(reads)==6,'six fresh field reads required')
    protected=json.loads((REPORT/'protected_inputs_before.json').read_text())
    need(all(sha(p)==h for p,h in protected.items()),'protected original input or raw output changed during review')
    save(REPORT/'independent_review_acceptance.json',dict(
        reviewed_at=datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),
        audit_id='URV_S2_ZERO_20261102_01',release_sha256=RELEASE_SHA,
        ZERO_STEP_INDEPENDENT_REVIEW_PASS=True,ZERO_STEP_GEOMETRY_PASS=True,
        native_records_reviewed=18,actual_native_calls_this_review=0,actual_VTK_field_rereads=6,
        initialized_frames_reread=6,actual_time_steps_this_review=0,field_reader_records=reads,
        raw_manifest_files_verified=len(raw),total_audit_files_verified=len(actual),
        protected_existing_files_verified=len(protected),original_files_changed=False,
        density_capture='NOT_APPLICABLE_S0_ONLY',MRP_initial_arithmetic_exact=True,A1_initial_volume_path_exact=True,
        NUMERICAL_GATE='NOT_EVALUATED',RESULT_PASS=False,geometry_PASS=None,
        REFERENCE_QUALIFIED_FOR_CASE=False,MODEL_COMPARISON='NOT_EVALUATED',physical_validation='NOT_EVALUATED',
        B_sealing_condition_satisfied=True,performance_started=False,formal_started=False))


if __name__=='__main__':
    try:
        main()
    except Exception as error:
        save(REPORT/'review_failure.json',dict(ZERO_STEP_INDEPENDENT_REVIEW_PASS=False,
             error=type(error).__name__+': '+str(error),B_sealing_condition_satisfied=False,
             native_solver_called=False,performance_started=False,formal_started=False))
        raise

"""R1/R2 pure file checks; no native execution, VTK imports, or authority grants."""
from pathlib import Path
import json
import xml.etree.ElementTree as ET
import numpy as np
from evidence import need,sha,kv,rows,close,exact_parameters,check_boundary

MODES=('describe','precheck','initialize')

def load(path):return json.loads(Path(path).read_text())

def regular(path):
    p=Path(path)
    need(p.is_absolute() and p.is_file() and str(p.resolve())==str(p),'noncanonical/missing zero file')
    need(not any(x.is_symlink() for x in [p,*p.parents]),'zero evidence symlink refused')
    return p

def expected_initial(cfg):
    p=exact_parameters(cfg);v=np.zeros(3);v[1 if cfg['direction']=='P' else 0]=p['H']*p['a']*p['dt']/2
    return v

def validate_zero_outputs(record):
    run=Path(record['output_directory']);cfg=kv(regular(record['run_config_path']));p=exact_parameters(cfg)
    mode=record['mode'];need(mode in MODES and cfg['mode']==mode,'zero forbids steady or mismatched mode')
    need(record['run_id']==cfg['run_id'] and cfg['output_directory']==str(run),'zero config identity/output mismatch')
    need(kv(regular(run/'run_manifest.txt'))==dict(run_id=record['run_id'],mode=mode),'zero manifest mismatch')
    effective=kv(regular(run/'effective_config.txt'))
    need(effective['run_id']==record['run_id'] and effective['mode']==mode,'native zero identity mismatch')
    need(effective['formal_simulation']=='false','effective zero mode marked formal')
    need(effective['direction']==('parallel' if cfg['direction']=='P' else 'perpendicular'),'effective direction mismatch')
    values=dict(h_m=p['h'],d_m=p['d'],w_m=p['w'],Lx_m=p['P'],Ly_m=p['Ly'],phi=p['w']/p['P'],
        dx_m=p['dx'],dt_s=p['dt'],nominal_volume_m3=p['P']*p['Ly']*p['H'],plan_area_m2=p['P']*p['Ly'],
        acceleration_m_s2=p['a'],nu_m2_s=p['nu'])
    for key,value in values.items():need(close(float(effective[key]),value),'effective physical conversion mismatch: '+key)
    for key,value in dict(nx=p['nx'],ny=p['ny'],window_steps=p['window'],maximum_steps=p['cap']).items():
        need(int(effective[key])==value,'effective exact grid/time mismatch: '+key)
    # The native format has no lattice-force column. Check the implied conversion
    # from independently checked a/dx/dt, then check its initial physical response.
    f=float(effective['acceleration_m_s2'])*float(effective['dt_s'])**2/float(effective['dx_m'])
    need(close(f,p['a']*p['dt']**2/p['dx']),'effective lattice force conversion')
    process=load(regular(run/'process_receipt.json'))
    need(process.get('independent_process_exit_code')==0 and process.get('timed_out') is False and
         process.get('resource_stop_reason') is None,'zero native process failed/timed out/resource stop')
    need(process.get('solver_wall_cap_seconds')==300 and np.isfinite(process['elapsed_seconds']) and process['elapsed_seconds']>=0,'zero process budget/elapsed evidence')
    need(regular(run/'exit_code.txt').read_text().strip()=='0','zero independent exit file')
    execution=kv(regular(run/'execution_audit.txt'))
    need(execution['protocol']=='URV-v1' and execution['preparation_only_build']=='0' and execution['collide_and_stream_calls']=='0','nonzero advancement/wrong zero build')
    need(regular(run/'run.log').stat().st_size>0,'missing zero native log')
    need(not (run/'diagnostics.csv').exists() and not (run/'mass_capture').exists(),'unexpected steady/capture evidence in zero run')
    geometry=None
    if mode!='describe':geometry=check_boundary(cfg,kv(regular(run/'boundary_audit.txt')))
    if mode=='initialize':
        result=kv(regular(run/'result.txt'))
        need(result['run_id']==record['run_id'],'initial result identity mismatch')
        need(result['formal_simulation']=='false' and result['steps_completed']==result['collide_and_stream_calls']=='0','initial nonzero/steady result')
        need(result['NUMERICAL_GATE']=='NOT_EVALUATED' and result['RESULT_PASS']=='false','zero scientific promotion')
        need(result['finite']==result['geometry_PASS']==result['q_audit_PASS']=='true','initial state flag failed')
        need(result['exit_code']=='0' and int(result['fluid_nodes'])==p['nodes'] and int(result['frames_written'])==1,'initial exit/node/frame count')
        need(close(float(result['fluid_volume_m3']),p['P']*p['Ly']*p['H'],rtol=1e-10),'initial volume')
        need(close(float(result['nominal_volume_m3']),p['P']*p['Ly']*p['H']),'initial nominal volume')
        need(close(float(result['corrected_mass']),1000*p['nodes']*p['dx']**3),'initial corrected mass')
        need(float(result['density_delta'])==float(result['max_density_deviation'])==0,'initial density')
        J=np.asarray([float(v) for v in result['J_vector_m2_s'].split(',')]);need(J.shape==(3,) and close(J,expected_initial(cfg),rtol=1e-8,atol=1e-30),'initial force direction/half-step flux')
        frames=rows(regular(run/'frame_index.csv'))
        need(len(frames)==1 and int(frames[0]['step'])==0 and float(frames[0]['time_s'])==float(frames[0]['tstar'])==0 and frames[0]['reason']=='initial','initial native frame index')
    return geometry

def payload_closure(master,run):
    run=Path(run);hashes={}
    def visit(value):
        p=regular(Path(value).absolute())
        need(p.is_relative_to(run/'vtkData') and p.suffix in ('.pvd','.vtm','.vti'),'initial VTK payload escapes own run or unexpected format')
        if str(p) in hashes:return
        hashes[str(p)]=sha(p)
        if p.suffix in ('.pvd','.vtm'):
            for ds in ET.parse(p).getroot().iter('DataSet'):
                if 'file' in ds.attrib:visit((p.parent/ds.attrib['file']).resolve())
    visit(master);return hashes

def validate_initial_readback(record,report,folder):
    need(record['mode']=='initialize','field receipt for noninitialize call')
    run=Path(record['output_directory']);cfg=kv(record['run_config_path']);p=exact_parameters(cfg)
    report=regular(report);expected=Path(folder)/('field_readback_'+record['planned_case_id']+'.json')
    need(report==expected,'readback belongs to another configuration/path')
    process=load(regular(report.with_suffix('.process.json')))
    need(process.get('independent_exit_code')==0 and process.get('timed_out') is False and np.isfinite(process['elapsed_seconds']) and process['elapsed_seconds']>=0,'field reader failed/timed out')
    log=regular(Path(folder)/('field_reader_'+record['planned_case_id']+'.log'))
    value=load(report)
    need(value.get('PASS') is True and value.get('actual_reader') is True and value.get('solver_executed') is False and len(value['frames'])==1,'actual single initial field report required')
    need(value['velocity_units']=='m/s' and value['pressure_units']=='Pa_periodic_perturbation' and value['dissipation_units']=='m2/s3','initial field units')
    frame=value['frames'][0];need(frame['step']==0 and frame['unique_fluid_nodes']==p['nodes'],'wrong initial field frame/nodes')
    raw=np.asarray([float(v) for v in kv(regular(run/'result.txt'))['J_vector_m2_s'].split(',')])
    exported=np.asarray(frame['J_m2_s'],dtype=float);diagnostic=np.asarray(frame['diagnostic_J_m2_s'],dtype=float);error=np.asarray(frame['roundoff_bound_m2_s'],dtype=float)
    need(all(v.shape==(3,) and np.isfinite(v).all() for v in (raw,exported,diagnostic,error)) and np.all(error>=0),'invalid field flux/roundoff evidence')
    need(close(diagnostic,raw,rtol=1e-12,atol=1e-30) and np.all(np.abs(exported-raw)<=error),'field/own initial result flux mismatch')
    need(close(exported,expected_initial(cfg),rtol=1e-6,atol=1e-30),'field force direction/half-step flux')
    need(frame['pressure_range_Pa']==[0.,0.],'initial field not equilibrium pressure')
    need(set(frame['arrays'])=={'material','velocity_m_s','pressure_Pa','dissipation_m2_s3'},'missing initial physical arrays')
    masters=list((run/'vtkData').glob('*.pvd'));need(len(masters)==1,'one own VTK master required')
    datasets=list(ET.parse(masters[0]).getroot().iter('DataSet'))
    need(len(datasets)==1 and float(datasets[0].attrib['timestep'])==0,'initial VTK time/frame mapping')
    payload=payload_closure(masters[0],run)
    need(value.get('payload_sha256')==payload,'field payload closure differs from own initialization')
    need(any(Path(p).suffix=='.vti' for p in payload),'no actual initial VTK payload')
    return payload

def validate_audit_records(bound,audit,released,folder):
    """Reparse each zero record; do not trust counts or PASS booleans alone."""
    plan=released['zero_prepared_runs'];records=audit['records']
    need(len(records)==len(plan)==18,'eighteen original zero records required')
    need(audit['preparation_A_sha256']==released['preparation_A_sha256']==bound['preparation_A_sha256'],'audit original A mismatch')
    need(audit.get('formal_simulation_started') is False and audit.get('next_stage_started') is False and
         audit.get('NUMERICAL_GATE')=='NOT_EVALUATED' and audit.get('RESULT_PASS') is False,'zero receipt scientific/next-stage promotion')
    seen=set()
    for record,expected in zip(records,plan):
        need(all(record.get(k)==expected[k] for k in ('planned_case_id','run_id','mode')) and record.get('output')==expected['output_directory'],'zero raw identity/output association mismatch')
        need(record['native_exit_code']==0 and record['collide_and_stream_calls']==0,'zero summary failure/advancement')
        validate_zero_outputs(expected)
        if expected['mode']=='initialize':
            report=Path(folder)/('field_readback_'+expected['planned_case_id']+'.json')
            need(record.get('field_readback')==str(report) and record.get('field_readback_sha256')==sha(regular(report)),'wrong per-case readback reference')
            need(str(report) not in seen,'duplicate field receipt');seen.add(str(report))
            payload=validate_initial_readback(expected,report,folder)
            for path,h in payload.items():
                need(bound['inputs_sha256'].get(path)==h,'initial payload absent from bound raw evidence')
    need(len(seen)==6,'six unique initial field readbacks required')

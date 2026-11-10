#!/usr/bin/env python3
"""Six bounded native zero-step calls; steady mode is never accepted here."""
from pathlib import Path
import json,os,resource,subprocess,sys,time

CASE=Path(__file__).resolve().parents[1]
CHECKER=CASE.parent/'unseen_v2_reference_checker_S1_a1_v1'
sys.path.insert(0,str(CHECKER/'analysis'))
from evidence import need,sha,kv,save,exact_parameters,check_boundary,close

AUDIT_ID='URV_S1_ZERO_20261102_01'
ELF_SHA='5c3836e97c99feab88cd8e41773237f6ff642a10558f151b11e112563382b07b'
MODES=('describe','precheck','initialize')

def limits():
    resource.setrlimit(resource.RLIMIT_AS,(8*1024**3,8*1024**3))
    resource.setrlimit(resource.RLIMIT_CORE,(0,0))

def call(binary,config,run,mode):
    need(mode in MODES and kv(config)['mode']==mode,'zero audit forbids time stepping')
    need(sha(binary)==ELF_SHA,'A1 binary identity drift')
    env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',
             NUMEXPR_NUM_THREADS='1',QT_QPA_PLATFORM='offscreen',PYTHONDONTWRITEBYTECODE='1')
    start=time.monotonic()
    with (run/'run.log').open('x') as log:
        process=subprocess.run([str(binary),str(config)],cwd=CASE,stdout=log,stderr=subprocess.STDOUT,
                               env=env,preexec_fn=limits,timeout=300)
    (run/'exit_code.txt').write_text(str(process.returncode)+'\n')
    need(process.returncode==0,'native zero audit failed; no retry permitted')
    execution=kv(run/'execution_audit.txt')
    need(execution['preparation_only_build']=='0' and execution['collide_and_stream_calls']=='0',
         'wrong binary or time stepping in zero audit')
    return dict(native_exit_code=process.returncode,elapsed_seconds=time.monotonic()-start,
                collide_and_stream_calls=0,output=str(run)),env

def main():
    folder=CASE/'audits'/AUDIT_ID;folder.mkdir(parents=True,exist_ok=False)
    binary=CASE/'build/urv_reference'
    prepared=CASE/'evidence/preparation_manifest.json'
    original=json.loads(prepared.read_text())['inputs_sha256']
    need(all(sha(p)==h for p,h in original.items()),'frozen A1 preparation input drift')
    need(sha(binary)==ELF_SHA,'A1 native SHA mismatch')
    records=[]
    for direction in ('P','T'):
        for mode in MODES:
            run=folder/direction/mode;run.mkdir(parents=True)
            config=dict(mode=mode,run_id=f'ZERO_{AUDIT_ID}_{direction}_{mode}',output_directory=str(run),
                direction=direction,dx_nm='1.25',h_nm='30',d_nm='0',w_nm='120',period_nm='240',Ly_nm='240',
                nu_m2_s='1e-06',acceleration_m_s2='100000',window_tstar='0.75',max_time_H_diffusion='8',
                frame_tstar='0,0.01,0.02,0.05,0.1,0.2,0.5,1,2,4,8')
            path=run/'run_config.txt';path.write_text(''.join(k+'='+v+'\n' for k,v in config.items()))
            (run/'run_manifest.txt').write_text(f"run_id={config['run_id']}\nmode={mode}\n")
            record,env=call(binary,path,run,mode);record.update(direction=direction,mode=mode)
            p=exact_parameters(config);effective=kv(run/'effective_config.txt')
            need(int(effective['window_steps'])==p['window']==2592,'wrong window')
            need(int(effective['maximum_steps'])==p['cap']==27648,'wrong step cap')
            need(close(float(effective['dt_s']),p['dt']),'dt conversion')
            if mode!='describe':
                geometry=check_boundary(config,kv(run/'boundary_audit.txt'))
                record['geometry']=geometry
            if mode=='initialize':
                result=kv(run/'result.txt')
                need(result['formal_simulation']=='false' and result['steps_completed']=='0', 'not a zero-step result')
                need(result['NUMERICAL_GATE']=='NOT_EVALUATED' and result['RESULT_PASS']=='false', 'zero-step/steady confusion')
                need(result['finite']=='true' and result['geometry_PASS']=='true' and result['q_audit_PASS']=='true','initialization flag failed')
                need(int(result['fluid_nodes'])==884736 and int(result['frames_written'])==1,'initial frame/count')
                need(close(float(result['fluid_volume_m3']),p['H']*p['P']*p['Ly'],rtol=1e-10),'initial volume')
                need(close(float(result['corrected_mass']),1000*p['nodes']*p['dx']**3),'initial corrected mass')
                need(float(result['density_delta'])==0 and float(result['max_density_deviation'])<1e-6,'initial density')
                need(not (run/'diagnostics.csv').exists() and not (run/'mass_capture').exists(), 'unexpected steady/capture path entered')
                reader=folder/f'field_readback_{direction}.json'
                with (folder/f'field_reader_{direction}.log').open('x') as log:
                    read=subprocess.run(['/usr/bin/pvpython','--force-offscreen-rendering','-B',str(CHECKER/'analysis/read_fields.py'),
                        '--run',str(run),'--out',str(reader)],stdout=log,stderr=subprocess.STDOUT,env=env,preexec_fn=limits,timeout=300)
                need(read.returncode==0 and json.loads(reader.read_text())['PASS'],'independent VTK field readback failed')
                record['initial_statistics']={key:result[key] for key in ['mass','corrected_mass','density_delta','fluid_volume_m3','J_vector_m2_s','max_Mach','max_density_deviation']}
                record['field_readback']=str(reader)
            need(all(sha(p)==h for p,h in original.items()),'bound A1 input changed during zero audit')
            records.append(record);save(folder/'progress'/f'{len(records):02d}.json',record)
            print(json.dumps(dict(direction=direction,mode=mode,native_exit=0,actual_time_steps=0)),flush=True)
    outputs={str(p):sha(p) for p in folder.rglob('*') if p.is_file()}
    save(folder/'audit_files_sha256.json',outputs)
    save(folder/'verification.json',dict(audit_id=AUDIT_ID,ZERO_STEP_AUDIT_PASS=True,binary_sha256=ELF_SHA,
        native_describe=2,native_precheck=2,native_initialize=2,initialized_frames_read=2,
        actual_time_steps=0,steady_mode_invocations=0,records=records,original_bound_inputs_unchanged=True,
        density_capture='NOT_APPLICABLE_S0_ONLY',formal_simulation_started=False,
        NUMERICAL_GATE='NOT_EVALUATED',RESULT_PASS=False,reference_qualified=False,next_stage_started=False))
    return 0

if __name__=='__main__':sys.exit(main())

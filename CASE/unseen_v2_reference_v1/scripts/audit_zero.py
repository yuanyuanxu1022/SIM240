#!/usr/bin/env python3
"""Bounded, single-process audit of all 24 configs; no time-advancing mode allowed."""
from pathlib import Path
import argparse
import csv
import json
import os
import resource
import subprocess
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'analysis'))
from evidence import sha,kv,rows,save,need,exact_parameters,check_boundary,close

CASE=Path(__file__).resolve().parents[1]
PROJECT=CASE.parents[1]

def limit():
    resource.setrlimit(resource.RLIMIT_AS,(8*1024**3,8*1024**3))
    resource.setrlimit(resource.RLIMIT_CORE,(0,0))

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--audit-id',required=True)
    args=ap.parse_args()
    need(args.audit_id.replace('_','').isalnum(), 'invalid audit identifier')
    folder=CASE/'audits'/args.audit_id
    folder.mkdir(parents=True,exist_ok=False)
    env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',QT_QPA_PLATFORM='offscreen')
    binary=CASE/'build/urv_reference';before={str(p):sha(p) for p in [binary,*list((CASE/'src').glob('*')),*list((CASE/'analysis').glob('*.py')),*list((CASE/'common').glob('*'))] if p.is_file()}
    matrix=rows(CASE/'common/case_matrix.csv');records=[]
    template=PROJECT/'docs/reports/Unseen_V2_reference_protocol_20261101/describe_only_templates'
    for row in matrix:
        ident=row['planned_case_id'];record=dict(planned_case_id=ident,modes={})
        for mode in ['describe','precheck','initialize']:
            run=folder/ident/mode;run.mkdir(parents=True)
            cfg=kv(template/(ident+'.txt'))
            cfg.update(mode=mode,run_id='ZERO_'+args.audit_id+'_'+ident+'_'+mode,output_directory=str(run))
            (run/'run_config.txt').write_text(''.join(k+'='+v+'\n' for k,v in cfg.items()))
            (run/'run_manifest.txt').write_text('run_id='+cfg['run_id']+'\nmode='+mode+'\n')
            need(mode!='steady', 'time stepping prohibited in audit')
            started=time.monotonic()
            with (run/'run.log').open('w') as log:
                proc=subprocess.run([str(binary),str(run/'run_config.txt')],stdout=log,stderr=subprocess.STDOUT,
                    env=env,preexec_fn=limit,timeout=240,check=False)
            elapsed=time.monotonic()-started
            (run/'exit_code.txt').write_text(str(proc.returncode)+'\n')
            need(proc.returncode==0, str(run)+' native audit failed')
            execution=kv(run/'execution_audit.txt')
            need(execution['preparation_only_build']=='1' and execution['collide_and_stream_calls']=='0', 'time step executed')
            effective=kv(run/'effective_config.txt');p=exact_parameters(cfg)
            need(int(effective['window_steps'])==p['window']==int(row['window_steps']), 'window rounding')
            need(int(effective['maximum_steps'])==p['cap']==int(row['maximum_steps']), 'cap rounding')
            need(close(float(effective['dt_s']),p['dt']), 'native time conversion')
            need(int(row['expected_fluid_nodes'])==p['nodes'], 'matrix node count')
            if mode!='describe':
                independent=check_boundary(cfg,kv(run/'boundary_audit.txt'))
                need(independent['fluid_nodes']==p['nodes'], 'geometry volume')
            if mode=='initialize':
                result=kv(run/'result.txt')
                need(result['formal_simulation']=='false' and result['steps_completed']=='0' and result['finite']=='true', 'initialization flags')
                need(result['NUMERICAL_GATE']=='NOT_EVALUATED' and result['RESULT_PASS']=='false', 'zero step is not steady acceptance')
                need(close(float(result['fluid_volume_m3']),p['H']*p['P']*p['Ly'],rtol=1e-10), 'initial measured volume')
                need(close(float(result['corrected_mass']),1000*p['nodes']*p['dx']**3), 'initial corrected physical mass')
                need(float(result['density_delta'])==0, 'initial density delta')
                reader=[ '/usr/bin/pvpython','--force-offscreen-rendering','-B',str(CASE/'analysis/read_fields.py'),'--run',str(run),'--out',str(run/'field_readback.json')]
                with (run/'reader.log').open('w') as log:
                    read=subprocess.run(reader,stdout=log,stderr=subprocess.STDOUT,env=env,preexec_fn=limit,timeout=180,check=False)
                need(read.returncode==0, str(run)+' field reader failed')
                need(json.loads((run/'field_readback.json').read_text())['PASS'], 'field readback')
            record['modes'][mode]=dict(native_exit=proc.returncode,collide_and_stream_calls=0,elapsed_seconds=elapsed,output=str(run))
            print(json.dumps(dict(case=ident,mode=mode,exit=proc.returncode,seconds=round(elapsed,3))),flush=True)
        records.append(record)
        save(folder/'progress'/f'{len(records):02d}.json',record)
    # Attempting steady must fail before creating any output, even with a matching manifest.
    blocked=folder/'negative_steady';blocked.mkdir()
    cfg=kv(template/(matrix[0]['planned_case_id']+'.txt'))
    cfg.update(mode='steady',run_id='ZERO_BLOCKED_STEADY',output_directory=str(blocked))
    (blocked/'run_config.txt').write_text(''.join(k+'='+v+'\n' for k,v in cfg.items()))
    (blocked/'run_manifest.txt').write_text('run_id=ZERO_BLOCKED_STEADY\nmode=steady\n')
    with (blocked/'run.log').open('w') as log:
        proc=subprocess.run([str(binary),str(blocked/'run_config.txt')],stdout=log,stderr=subprocess.STDOUT,env=env,preexec_fn=limit,timeout=30)
    (blocked/'exit_code.txt').write_text(str(proc.returncode)+'\n')
    need(proc.returncode==2 and not (blocked/'effective_config.txt').exists(), 'native steady interlock failed')
    need(all(sha(p)==s for p,s in before.items()), 'audit changed bound inputs')
    files={str(p):sha(p) for p in folder.rglob('*') if p.is_file()}
    save(folder/'audit_files_sha256.json',files)
    save(folder/'verification.json',dict(PREPARATION_PASS=True,audit_id=args.audit_id,
        matrix_cases=len(records),native_describe=24,native_precheck=24,native_initialize=24,
        initialized_frames_read=24,unique_geometries=8,actual_time_steps=0,
        formal_simulation_started=False,steady_mode_rejected=True,records=records,
        bound_inputs_sha256=before,NUMERICAL_GATE='NOT_EVALUATED',RESULT_PASS=False,
        reference_qualified=False,physical_validation='NOT_EVALUATED'))
    print('ZERO_STEP_AUDIT_PASS=true',flush=True)

if __name__=='__main__': main()

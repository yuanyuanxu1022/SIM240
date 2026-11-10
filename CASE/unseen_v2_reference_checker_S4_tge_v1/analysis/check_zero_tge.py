"""Pure independent inspection of existing 3+1 zero receipts; no VTK/native calls."""
from pathlib import Path
import argparse,json,sys
from tge_stage import (CASE,CHECKER,AUDIT_ID,CASE_ID,ELF_SHA,MODES,need,sha,load,
    covered,verify_seal,validate_zero_authority,unchanged)
from zero_evidence_s4 import validate_zero_outputs,validate_initial_readback

def validate_completed_zero(bound,path):
    validate_zero_authority(bound,path)
    folder=CASE/'audits'/AUDIT_ID;receipt=folder/'verification.json';audit=load(receipt)
    need(audit.get('audit_id')==AUDIT_ID and audit.get('ZERO_STEP_AUDIT_PASS') is True and
         audit.get('binary_sha256')==ELF_SHA and audit.get('native_describe')==audit.get('native_precheck')==audit.get('native_initialize')==1 and
         audit.get('initialized_frames_read')==1 and audit.get('actual_time_steps')==audit.get('steady_mode_invocations')==0,
         'wrong 3+1 receipt counts or advancement')
    need(audit.get('audit_release_sha256')==sha(path) and audit.get('preparation_A_sha256')==bound['preparation_A_sha256'] and
         audit.get('audit_release_path')==str(path),'zero receipt release binding mismatch')
    need(audit.get('RESULT_PASS') is False and audit.get('NUMERICAL_GATE')=='NOT_EVALUATED' and
         audit.get('reference_qualified') is False and audit.get('next_stage_started') is False and
         audit.get('formal_simulation_started') is False,'zero promotes scientific status')
    records=audit.get('records',[]);need(len(records)==3,'three zero records required')
    for actual,expected in zip(records,bound['zero_prepared_runs']):
        need(all(actual.get(k)==expected[k] for k in ('run_id','planned_case_id','mode')) and
             actual.get('output')==expected['output_directory'],'zero record association mismatch')
        need(actual.get('native_exit_code')==0 and actual.get('collide_and_stream_calls')==0,'zero process summary failure')
        validate_zero_outputs(expected)
        if expected['mode']=='initialize':
            report=folder/('field_readback_'+CASE_ID+'.json')
            need(actual.get('field_readback')==str(report) and actual.get('field_readback_sha256')==sha(report),'field receipt changed')
            validate_initial_readback(expected,report,folder)
    manifest=folder/'audit_files_sha256.json';need(audit['raw_manifest_sha256']==sha(manifest) and audit['raw_manifest_path']==str(manifest),'raw manifest mismatch')
    raw=load(manifest)
    current={str(p):sha(p) for p in folder.rglob('*') if p.is_file() and p not in (receipt,manifest)}
    need(raw==current,'zero raw file set/content drift')
    unchanged(bound)
    return dict(INDEPENDENT_ZERO_REVIEW_PASS=True,native_calls=0,VTK_calls=0,
        original_S4_stage_accepted=False,formal_simulation_started=False,reference_qualified=False)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--release',type=Path,required=True);ap.add_argument('--release-sha256',required=True)
    args=ap.parse_args()
    try:
        p=args.release.resolve();b=verify_seal(p,args.release_sha256)
        print(json.dumps(validate_completed_zero(b,p)));code=0
    except Exception as e:print(type(e).__name__+': '+str(e),file=sys.stderr);code=2
    raise SystemExit(code)

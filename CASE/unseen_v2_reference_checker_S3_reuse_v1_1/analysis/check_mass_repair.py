#!/usr/bin/env python3
"""Supplementary MRP acceptance, after unchanged URV checker. Never solves."""
from pathlib import Path
import argparse,csv,json,struct,sys
from evidence import need,sha,kv,rows,save
from contracts import output_location,release_inputs
from check_results import binding,check_run
from mass_capture import (validate_index,secure_file,replay_file,unbits,bits,arithmetic_self_check)

CORRECTED=['corrected_mass','corrected_mass_error','delta_mass_error','mass_ledger_agreement','density_delta']

def bound_baseline(bound,direction):
    record=bound['mass_repair_baselines'][direction]
    for role in ['v12_diagnostics','v12_output_manifest']:
        path=Path(record[role]);need(bound['inputs_sha256'].get(str(path))==sha(path),'unbound MRP baseline')
    return record

def review(run,bound,original_acceptance):
    run=Path(run);cfg=kv(run/'run_config.txt');direction=cfg['direction']
    need(original_acceptance['RESULT_PASS'] is True,'original URV acceptance must pass first')
    need(original_acceptance['run_id']==cfg['run_id'],'URV acceptance identity')
    completion=json.loads((run/'completion.json').read_text());hashes=completion['output_sha256']
    root=run/'mass_capture';idxpath=secure_file(root,'rho_capture_index.json')
    need(hashes.get(str(idxpath.relative_to(run)))==sha(idxpath),'index absent from completion')
    index=json.loads(idxpath.read_text());binary=bound['provenance']['native_binary']
    validate_index(index,root,cfg['run_id'],direction,bound['inputs_sha256'][binary])
    raw=secure_file(root,'rho_capture_raw.json')
    need(index['raw_index_sha256']==sha(raw),'raw capture index changed')
    raw_doc=json.loads(raw.read_text())
    for key in ['protocol_id','run_id','direction','map_file','native_executable']:
        need(raw_doc[key]==index[key],'raw/final capture metadata mismatch')
    need(len(raw_doc['records'])==len(index['records']),'raw/final capture length')
    for a,b in zip(raw_doc['records'],index['records']):
        need(all(b.get(k)==v for k,v in a.items()),'raw/final record mismatch')
    for path in root.iterdir():
        need(not path.is_symlink() and path.is_file(),'unexpected capture object')
        need(hashes.get(str(path.relative_to(run)))==sha(path),'capture output not completion-bound')
    baseline=bound_baseline(bound,direction)
    new=rows(run/'diagnostics.csv');v12=rows(baseline['v12_diagnostics'])
    old=rows(Path(bound['h75_regression_references'][direction]['directory'])/'diagnostics.csv')
    need(len(new)==len(v12)==len(old),'full trajectory row count mismatch')
    differences=[]
    for i,(a,b) in enumerate(zip(new,v12)):
        for key in CORRECTED:
            if float(a[key])!=float(b[key]):differences.append(dict(step=i,column=key,new=a[key],v12=b[key]))
    replays=[];initial=None;native_mismatch=[];history_mismatch=[]
    records=sorted(index['records'],key=lambda r:(r['phase']!='initial_reference',r['step']))
    for record in records:
        values=replay_file(root/record['file'],unbits(record['rho_phys_hex64']),unbits(record['dx_hex64']))
        replays.append(dict(phase=record['phase'],step=record['step'],**values))
        for key,native in [('fused_mass','native_mass_hex64'),('corrected_mass','native_corrected_mass_hex64'),
                           ('density_delta','native_density_delta_hex64')]:
            if bits(values[key])!=record[native]:native_mismatch.append(dict(phase=record['phase'],step=record['step'],column=key))
        if record['phase']=='initial_reference':initial=values;continue
        need(initial is not None,'initial reference must precede replay')
        step=record['step'];a=new[step];o=old[step];b=v12[step]
        need(int(a['step'])==int(o['step'])==int(b['step'])==step,'step alignment')
        fused_error=(values['fused_mass']-initial['fused_mass'])/initial['fused_mass']
        split_error=(values['split_mass']-initial['split_mass'])/initial['split_mass']
        for field,actual,expected in [('native_mass',values['fused_mass'],float(a['mass'])),
            ('native_mass_error',fused_error,float(a['mass_error'])),
            ('old_mass',values['fused_mass'],float(o['mass'])),('old_mass_error',fused_error,float(o['mass_error'])),
            ('v12_mass',values['split_mass'],float(b['mass'])),('v12_mass_error',split_error,float(b['mass_error']))]:
            if bits(actual)!=bits(expected):history_mismatch.append(dict(step=step,column=field,actual_hex64=bits(actual),expected_hex64=bits(expected)))
    field_differences=[]
    for relative,digest in json.loads(Path(baseline['v12_output_manifest']).read_text()).items():
        path=run/relative
        if not path.is_file() or sha(path)!=digest:field_differences.append(relative)
    # Strict byte guard for known identity-independent raw arrays/VTK payloads.
    # A differing container needs separate explicit review; never waive numerical changes here.
    success=not(differences or native_mismatch or history_mismatch or field_differences)
    return dict(protocol_id='URV-MRP-v1',run_id=cfg['run_id'],direction=direction,
        MASS_CAPTURE_INTEGRITY=True,SAME_INPUT_REPLAY=not(native_mismatch or history_mismatch),
        CORRECTED_LEDGER_UNCHANGED=not differences,PHYSICAL_OUTPUT_GUARD=not field_differences,
        URV_RESULT_PASS=True,S0_REVISION_DISPOSITION='DIRECTION_ACCEPTED' if success else 'HOLD',
        RESULT_PASS=success,HISTORICAL_EXCLUSIVE_ATTRIBUTION='NOT_ESTABLISHED',
        corrected_differences=differences,native_replay_differences=native_mismatch,
        history_reproduction_differences=history_mismatch,physical_output_differences=field_differences,
        replays=replays,arithmetic_oracle=arithmetic_self_check(),reference_qualified=False,next_stage_started=False)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run',type=Path,required=True)
    ap.add_argument('--release',type=Path,required=True);ap.add_argument('--release-sha256',required=True)
    ap.add_argument('--out',type=Path,required=True)
    args=ap.parse_args();output=None
    try:
        # Protect all inputs before first write, even on malformed contracts (R1).
        paths=release_inputs(args.release)
        output=output_location(args.out,[args.run],paths+[args.release])
        bound=binding(args.release,args.release_sha256)
        # Regenerate the original acceptance using unchanged code and current raw
        # bindings. An arbitrary acceptance.json claiming PASS is never trusted.
        original=check_run(args.run,args.release,args.release_sha256,output/'original_urv')
        result=review(args.run,bound,original)
        save(output/'mass_repair_review.json',result)
        need(result['RESULT_PASS'],'supplementary mass evidence failed; differences retained')
        return 0
    except Exception as error:
        if output is not None:save(output/'failure.json',{'error':str(error),'RESULT_PASS':False,'S0':'HOLD'})
        print(str(error),file=sys.stderr);return 2
if __name__=='__main__':sys.exit(main())

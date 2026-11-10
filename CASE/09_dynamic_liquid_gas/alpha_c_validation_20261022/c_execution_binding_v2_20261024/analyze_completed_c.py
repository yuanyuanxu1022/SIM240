#!/usr/bin/env python3
"""Accept existing v2 C results only; reuse the unchanged frozen numerical analyzer."""
import argparse
import json
import sys
from pathlib import Path
from binding import (ROOT,PARENT,BATCH,EXECUTION_ID,GATES,binding_path,file_hashes,post_mismatches,
                     require,sha,summarize,validate_completed,verify_binding)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--check-inputs',action='store_true')
    group.add_argument('--output',type=Path)
    args=parser.parse_args()
    bound,protocol=verify_binding();bs=sha(binding_path())
    if args.check_inputs:
        print('C_ANALYSIS_INPUTS_OK; same execution binding; completion not evaluated; no solver/output created');return 0
    output=args.output.resolve()
    require(not output.exists(),'analysis output exists; no overwrite')
    require(output.is_relative_to(ROOT) and not output.is_relative_to(ROOT/'output') and not output.is_relative_to(ROOT/'evidence'),
            'analysis output must be a new directory inside execution package, outside raw data')
    manifest,cases=validate_completed(ROOT,bound)
    before=file_hashes(ROOT)
    # This import reads numerical helper code only. It cannot start a solver.
    sys.path.insert(0,str(PARENT))
    from analyze_c import analyze_case
    results=[]
    for case in cases:
        data=ROOT/'output'/BATCH/(BATCH+'_'+case['id'])
        results.append(analyze_case(case,data,protocol['thresholds']))
    require(file_hashes(ROOT)==before,'C raw evidence changed during analysis')
    require(not post_mismatches(bound,bs),'bound inputs changed during analysis')
    summary=summarize(results)
    payload=dict(stage='c',execution_id=EXECUTION_ID,batch_id=BATCH,
        physics_protocol_id=protocol['protocol_id'],execution_binding_sha256=bs,
        alpha_dependency=bound['alpha_dependency'],input_sha256=before,all_cases=results,**summary)
    # Serialize fully before mkdir, so a type error cannot leave a false verdict directory.
    serialized=json.dumps(payload,indent=2,allow_nan=False)+'\n'
    output.mkdir(parents=True,exist_ok=False);(output/'verdict.json').write_text(serialized)
    print('C_COMPLETE_CONTRACT',summary['complete_C_contract_pass'],'; physical Gates NOT_EVALUATED; no next stage')
    return 0 if summary['complete_C_contract_pass'] else 1

if __name__=='__main__':
    try:sys.exit(main())
    except Exception as exc:print('C_ANALYSIS_FAILED:',repr(exc),file=sys.stderr);sys.exit(2)

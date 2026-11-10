#!/usr/bin/env python3
"""Analyze existing completed stage only; never executes a solver or advances a Gate."""
import argparse
import json
from pathlib import Path
import sys
from analyze_alpha import require,analyze_case as alpha_case,matrix_checks
from analyze_c import analyze_case as c_case
from run_suite import BASE,PROTOCOL,batch_id,entries,sha

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--stage',choices=['alpha','c'],required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    require(not args.output.exists(),'analysis output exists; no overwrite')
    batch=batch_id(args.stage);evidence=BASE/'evidence'/batch;manifest_path=evidence/'manifest.json'
    manifest=json.loads(manifest_path.read_text())
    require(manifest['stage']==args.stage and manifest['batch_id']==batch and manifest['protocol_id']==PROTOCOL['protocol_id'],'manifest identity mismatch')
    require(int((evidence/'exit_code.txt').read_text())==0 and manifest.get('finished_utc') and manifest['independent_exit_code']==0 and manifest['source_hashes_unchanged'],'batch incomplete/failed')
    require(manifest['source_binding']==json.loads((BASE/'evidence/build_binding.json').read_text()),'manifest/current source binding mismatch')
    for p,h in manifest['source_binding']['sha256'].items():require(Path(p).is_file() and sha(p)==h,'bound file changed: '+p)
    expected=entries(args.stage);require([e['case_id'] for e in manifest['cases']]==[c['id'] for c in expected],'missing/reordered/duplicate cases')
    results=[];input_hashes={str(manifest_path):sha(manifest_path)}
    for entry,case in zip(manifest['cases'],expected):
        sub=evidence/entry['run_id'];directory=BASE/'output'/batch/entry['run_id']
        require(entry['parameters']==case and entry['stage']==args.stage,'child parameter mismatch')
        require(int((sub/'exit_code.txt').read_text())==0 and entry.get('finished_utc') and entry['independent_exit_code']==0,'child incomplete/failed')
        require(json.loads((sub/'manifest.json').read_text())==entry,'independent child manifest mismatch')
        fn=alpha_case if args.stage=='alpha' else c_case
        results.append(fn(case,directory,PROTOCOL['thresholds']))
        for parent in (sub,directory):
            for p in parent.rglob('*'):
                if p.is_file():input_hashes[str(p.resolve())]=sha(p)
    comparisons=matrix_checks(results,PROTOCOL['thresholds']) if args.stage=='alpha' else []
    payload=dict(stage=args.stage,batch_id=batch,all_cases=results,matrix_checks=comparisons,
                 input_manifest_sha256=sha(manifest_path),build_binding_sha256=sha(BASE/'evidence/build_binding.json'),
                 input_sha256=input_hashes,NUMERICAL_GATE='NOT_EVALUATED',RESULT_PASS='NOT_EVALUATED',geometry_PASS='NOT_EVALUATED')
    if args.stage=='alpha':
        passed=all(r['operator_contract_pass'] for r in results) and all(c['passed'] for c in comparisons)
        payload['operator_contract_pass']=bool(passed)
    else:
        payload['implementation_contract_pass']=all(r['implementation_contract_pass'] for r in results)
        payload['physical_amount_drift_within_budget']=all(r['physical_amount_drift_within_budget'] for r in results)
        passed=payload['implementation_contract_pass'] and payload['physical_amount_drift_within_budget'] and all(r['safety_pass'] for r in results)
        payload['complete_C_contract_pass']=bool(passed)
    args.output.mkdir(parents=True,exist_ok=False);(args.output/'verdict.json').write_text(json.dumps(payload,indent=2)+'\n')
    print('stage=',args.stage,'frozen_contract_pass=',passed,'; no next stage started; physical Gates NOT_EVALUATED');return 0 if passed else 1

if __name__=='__main__':
    try:sys.exit(main())
    except Exception as exc:print('ANALYSIS_FAILED:',repr(exc),file=sys.stderr);sys.exit(2)

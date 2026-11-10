#!/usr/bin/env python3
"""One explicit frozen stage only. Default is precheck; no retry/resume/next stage."""
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

BASE=Path(__file__).resolve().parent
PROTOCOL=json.loads((BASE/'protocol.json').read_text())

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def now():return dt.datetime.now(dt.timezone.utc).isoformat()
def batch_id(stage):return PROTOCOL['batch_prefix']+'_'+stage
def entries(stage):return PROTOCOL['stages'][stage]

def binding_check():
    bound=json.loads((BASE/'evidence/build_binding.json').read_text())
    bad=[p for p,h in bound['sha256'].items() if not Path(p).is_file() or sha(p)!=h]
    if bad:raise RuntimeError('frozen input mismatch: '+repr(bad))
    return bound

def check_stage(stage):
    binding=binding_check();batch=batch_id(stage)
    reserve=(3 if stage=='alpha' else 12)*1024**3
    if shutil.disk_usage(BASE).free<reserve:raise RuntimeError('insufficient free disk for frozen evidence output')
    for where in ('output','evidence'):
        if (BASE/where/batch).exists():raise RuntimeError('batch exists; no overwrite/resume')
    if stage=='c':
        verdict_path=BASE/'analysis_alpha/verdict.json'
        if not verdict_path.is_file():raise RuntimeError('C waits for completed alpha analysis; no automatic stage transition')
        verdict=json.loads(verdict_path.read_text())
        if verdict.get('stage')!='alpha' or verdict.get('operator_contract_pass') is not True:
            raise RuntimeError('alpha operator contract has not passed')
        source=BASE/'evidence'/batch_id('alpha')/'manifest.json'
        if verdict.get('input_manifest_sha256')!=sha(source):raise RuntimeError('alpha analysis is not bound to current completed manifest')
        if verdict.get('build_binding_sha256')!=sha(BASE/'evidence/build_binding.json'):raise RuntimeError('alpha analysis uses another frozen build')
        if not verdict.get('input_sha256'):raise RuntimeError('alpha evidence hashes missing')
        for p,h in verdict['input_sha256'].items():
            if not Path(p).is_file() or sha(p)!=h:raise RuntimeError('alpha analysis input changed')
    return binding

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--stage',choices=['alpha','c'],required=True);parser.add_argument('--run',action='store_true');args=parser.parse_args()
    binding=check_stage(args.stage);batch=batch_id(args.stage)
    print(f'PRECHECK_OK stage={args.stage} cases={len(entries(args.stage))} frozen_hashes={len(binding["sha256"])}; no solver started yet',flush=True)
    if not args.run:return 0
    evidence=BASE/'evidence'/batch;output=BASE/'output'/batch;evidence.mkdir(exist_ok=False);output.mkdir(parents=True,exist_ok=False)
    manifest=dict(batch_id=batch,stage=args.stage,protocol_id=PROTOCOL['protocol_id'],started_utc=now(),source_binding=binding,cases=[],
                  NUMERICAL_GATE='NOT_EVALUATED',RESULT_PASS='NOT_EVALUATED',geometry_PASS='NOT_EVALUATED')
    manifest_path=evidence/'manifest.json';code=0
    try:
        for case in entries(args.stage):
            run_id=f'{batch}_{case["id"]}';child=evidence/run_id;child.mkdir()
            exe='alpha_diffusion' if args.stage=='alpha' else 'coupled_check'
            command=[str(BASE/'build'/exe),case['id'],str(output/run_id)]
            entry=dict(run_id=run_id,case_id=case['id'],stage=args.stage,parameters=case,command=command,cwd=str(BASE),started_utc=now())
            manifest['cases'].append(entry);manifest_path.write_text(json.dumps(manifest,indent=2)+'\n')
            print('START',run_id,flush=True)
            with (child/'console.log').open('w') as log:p=subprocess.run(command,cwd=BASE,stdout=log,stderr=subprocess.STDOUT)
            (child/'exit_code.txt').write_text(str(p.returncode)+'\n')
            entry.update(finished_utc=now(),independent_exit_code=p.returncode)
            (child/'manifest.json').write_text(json.dumps(entry,indent=2)+'\n');manifest_path.write_text(json.dumps(manifest,indent=2)+'\n')
            if p.returncode:code=p.returncode;break
    except KeyboardInterrupt:manifest['exception']='KeyboardInterrupt; partial evidence retained';code=130
    except Exception as exc:manifest['exception']=repr(exc);code=3
    finally:
        bad=[p for p,h in binding['sha256'].items() if not Path(p).is_file() or sha(p)!=h]
        if bad:code=code or 5
        manifest.update(finished_utc=now(),independent_exit_code=code,source_hashes_unchanged=not bad,source_mismatches=bad)
        manifest_path.write_text(json.dumps(manifest,indent=2)+'\n');(evidence/'exit_code.txt').write_text(str(code)+'\n')
    print('BATCH_EXIT=',code,'; analysis not run; next stage not started',flush=True);return code

if __name__=='__main__':
    try:sys.exit(main())
    except Exception as exc:print('PRECHECK_FAILED:',repr(exc),file=sys.stderr);sys.exit(2)

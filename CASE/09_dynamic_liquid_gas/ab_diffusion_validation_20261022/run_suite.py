#!/usr/bin/env python3
"""Fixed A2+B batch. Default precheck only; no retry, overwrite, analysis or next stage."""
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import subprocess
import sys

BASE=Path(__file__).resolve().parent
PROTOCOL=json.loads((BASE/'protocol.json').read_text())
BATCH=PROTOCOL['batch_id']
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def now():return dt.datetime.now(dt.timezone.utc).isoformat()
def entries():
    for name in PROTOCOL['A2_cases']:yield 'a2',name
    for case in PROTOCOL['B_cases']:yield 'b',case['id']
def check_binding():
    binding=json.loads((BASE/'evidence/build_binding.json').read_text())
    bad=[p for p,h in binding['sha256'].items() if not Path(p).is_file() or sha(p)!=h]
    if bad:raise RuntimeError(f'binding mismatch: {bad}')
    for parent in ['output','evidence']:
        if (BASE/parent/BATCH).exists():raise RuntimeError('batch exists; no overwrite/resume')
    return binding
def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run',action='store_true');args=parser.parse_args()
    binding=check_binding()
    print(f'PRECHECK_OK: {len(binding["sha256"])} hashes; 4 A2 + 18 B; no solver started yet',flush=True)
    if not args.run:return 0
    evidence=BASE/'evidence'/BATCH;output=BASE/'output'/BATCH
    evidence.mkdir(exist_ok=False);output.mkdir(exist_ok=False)
    manifest=dict(batch_id=BATCH,started_utc=now(),source_binding=binding,protocol=PROTOCOL,cases=[],NUMERICAL_GATE='NOT_EVALUATED',RESULT_PASS='NOT_EVALUATED',geometry_PASS='NOT_EVALUATED')
    path=evidence/'manifest.json';code=0
    try:
        for stage,name in entries():
            run_id=f'{BATCH}_{stage}_{name}';sub=evidence/run_id;sub.mkdir()
            command=[str(BASE/'build/ab_check'),stage,name,str(output/run_id)]
            entry=dict(run_id=run_id,stage=stage,case_id=name,command=command,cwd=str(BASE),started_utc=now())
            manifest['cases'].append(entry);path.write_text(json.dumps(manifest,indent=2)+'\n')
            print('START',run_id,flush=True)
            with (sub/'console.log').open('w') as log:run=subprocess.run(command,cwd=BASE,stdout=log,stderr=subprocess.STDOUT)
            (sub/'exit_code.txt').write_text(str(run.returncode)+'\n')
            entry.update(finished_utc=now(),independent_exit_code=run.returncode)
            (sub/'manifest.json').write_text(json.dumps(entry,indent=2)+'\n');path.write_text(json.dumps(manifest,indent=2)+'\n')
            if run.returncode:code=run.returncode;break
    except KeyboardInterrupt:
        manifest['exception']='KeyboardInterrupt; incomplete evidence retained';code=130
    except Exception as exc:
        manifest['exception']=repr(exc);code=3
    finally:
        bad=[p for p,h in binding['sha256'].items() if not Path(p).is_file() or sha(p)!=h]
        if bad:code=code or 5
        manifest.update(finished_utc=now(),independent_exit_code=code,source_hashes_unchanged=not bad,source_mismatches=bad)
        path.write_text(json.dumps(manifest,indent=2)+'\n');(evidence/'exit_code.txt').write_text(str(code)+'\n')
    print(f'BATCH_EXIT={code}; analysis not run; no Gate released',flush=True);return code
if __name__=='__main__':
    try:sys.exit(main())
    except Exception as exc:print(f'PRECHECK_FAILED: {exc}',file=sys.stderr);sys.exit(2)

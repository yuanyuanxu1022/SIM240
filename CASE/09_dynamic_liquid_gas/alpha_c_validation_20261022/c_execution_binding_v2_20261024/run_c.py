#!/usr/bin/env python3
"""Fixed C batch only. Default precheck reads inputs; --run must be explicit."""
import argparse
import fcntl
import json
import shutil
import subprocess
import sys
from pathlib import Path
from binding import (ROOT,PARENT,BATCH,EXECUTION_ID,PARENT_ID,GATES,binding_path,command,
                     now,paths,post_mismatches,require,sha,verify_binding)

def precheck():
    bound,protocol=verify_binding()
    require(shutil.disk_usage(ROOT).free>=12*1024**3,'need 12GiB free disk')
    for p in paths(ROOT)+(PARENT/'output/alpha_c_20261022_v1_c',PARENT/'evidence/alpha_c_20261022_v1_c'):
        require(not p.exists(),'C batch exists; no overwrite/resume: '+str(p))
    require((PARENT/'build/coupled_check').is_file(),'C binary missing')
    return bound,protocol

def execute():
    # Execution is reachable only after main has seen explicit --run.
    with (ROOT/'.c_execution.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        bound,protocol=precheck();binding_sha=sha(binding_path())
        ev,out=paths();ev.mkdir(parents=True,exist_ok=False);out.mkdir(parents=True,exist_ok=False)
        manifest=dict(schema_version=2,execution_id=EXECUTION_ID,protocol_id=EXECUTION_ID,
            physics_protocol_id=PARENT_ID,batch_id=BATCH,stage='c',started_utc=now(),
            execution_binding_sha256=binding_sha,source_binding=bound,
            alpha_dependency=bound['alpha_dependency'],cases=[],**GATES)
        code=0
        try:
            for case in protocol['stages']['c']:
                verify_binding()
                rid=BATCH+'_'+case['id'];child=ev/rid;child.mkdir()
                entry=dict(run_id=rid,case_id=case['id'],stage='c',parameters=case,
                    command=command(case,out/rid),cwd=str(PARENT),started_utc=now())
                manifest['cases'].append(entry);(ev/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
                try:
                    with (child/'console.log').open('w') as log:
                        process=subprocess.run(entry['command'],cwd=PARENT,stdout=log,stderr=subprocess.STDOUT)
                    code=process.returncode;entry.update(independent_exit_code=code,finished_utc=now())
                    (child/'exit_code.txt').write_text(str(code)+'\n')
                except BaseException as exc:
                    entry.update(spawn_or_wait_exception=repr(exc),finished_utc=now());raise
                finally:(child/'manifest.json').write_text(json.dumps(entry,indent=2)+'\n')
                if code:break
        except KeyboardInterrupt:manifest['exception']='KeyboardInterrupt; partial evidence retained';code=130
        except Exception as exc:manifest['exception']=repr(exc);code=3
        finally:
            bad=post_mismatches(bound,binding_sha)
            if bad:code=code or 5
            manifest.update(finished_utc=now(),independent_exit_code=code,source_hashes_unchanged=not bad,source_mismatches=bad)
            (ev/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');(ev/'exit_code.txt').write_text(str(code)+'\n')
        print('C_BATCH_EXIT',code,'; no analysis or next stage started');return code

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run',action='store_true')
    args=parser.parse_args()
    bound,protocol=precheck()
    print('C_PRECHECK_OK cases=4 binding_files='+str(len(bound['sha256']))+'; physical inputs/thresholds unchanged; no solver started',flush=True)
    if not args.run:return 0
    return execute()

if __name__=='__main__':
    try:sys.exit(main())
    except Exception as exc:print('C_PRECHECK_FAILED:',repr(exc),file=sys.stderr);sys.exit(2)

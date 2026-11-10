#!/usr/bin/env python3
"""Launch one frozen LP2000 diagnostic; never chain, resume or analyze runs."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

HERE=Path(__file__).resolve().parent
OLB=Path('/home/dell/openlb')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def preflight(initialize_only=False):
    protocol=json.loads((HERE/'protocol.json').read_text())
    binding=json.loads((HERE/'evidence/build_binding.json').read_text())
    if not protocol['diagnostic_inputs_and_analysis_frozen'] or protocol['formal_validation_released']:
        raise ValueError('unexpected protocol scope')
    if protocol['steps']!=2000 or protocol['case']!='laplace':
        raise ValueError('frozen case/length changed')
    if binding['build_exit_code']!=0:
        raise ValueError('no successful bound build')
    for name,digest in binding['sha256'].items():
        p=Path(name)
        if not p.is_file() or sha(p)!=digest:
            raise ValueError('bound input changed: '+name)
    rid='target_lp2000_initialization_20261021_v1' if initialize_only else protocol['run_id']
    if (HERE/'output'/rid).exists() or (HERE/'evidence'/rid).exists():
        raise ValueError('refusing existing run-id: '+rid)
    steps=0 if initialize_only else 2000
    command=[str(HERE/'src/target_prevalidation'),'--case','laplace','--run-id',rid,'--steps',str(steps)]
    return protocol,binding,rid,steps,command

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--check-only',action='store_true',help='read-only preflight; no solver call or run directory')
    parser.add_argument('--initialize-only',action='store_true',help='one zero-step preparation audit, no time advancement')
    args=parser.parse_args()
    protocol,binding,rid,steps,command=preflight(args.initialize_only)
    if args.check_only:
        print(json.dumps(dict(ready_to_launch=True,run_id=rid,steps=steps,command=command,
                              started=False,formal_validation=False)))
        return 0
    record=HERE/'evidence'/rid
    record.mkdir(exist_ok=False)
    hashes=dict(binding['sha256'])
    hashes[str(HERE/'evidence/build_binding.json')]=sha(HERE/'evidence/build_binding.json')
    manifest=dict(run_id=rid,protocol_id=protocol['protocol_id'],case='laplace',steps_requested=steps,
                  start_from_step=0,checkpoint_resume=False,command=command,cwd=str(HERE),
                  started_utc=datetime.now(timezone.utc).isoformat(),source_hashes=hashes,
                  openlb_head=subprocess.check_output(['git','-C',str(OLB),'rev-parse','HEAD'],text=True).strip(),
                  openlb_status=subprocess.check_output(['git','-C',str(OLB),'status','--short'],text=True),
                  model_not_GHY=True,formal_validation=False,
                  NUMERICAL_GATE='NOT_EVALUATED',RESULT_PASS='NOT_EVALUATED',geometry_PASS='NOT_EVALUATED')
    (record/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    with (record/'console.log').open('w') as log:
        try:
            completed=subprocess.run(command,cwd=HERE,stdout=log,stderr=subprocess.STDOUT)
            exit_code=completed.returncode
        except OSError as e:
            log.write(str(e)+'\n')
            exit_code=127
    (record/'exit_code.txt').write_text(str(exit_code)+'\n')
    manifest['finished_utc']=datetime.now(timezone.utc).isoformat()
    manifest['independent_exit_code']=exit_code
    manifest['source_hashes_unchanged']=all(Path(p).is_file() and sha(Path(p))==h for p,h in hashes.items())
    (record/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(dict(run_id=rid,independent_exit_code=exit_code,
                         source_hashes_unchanged=manifest['source_hashes_unchanged'],
                         formal_validation=False,analysis_started=False)))
    return exit_code if exit_code else (0 if manifest['source_hashes_unchanged'] else 5)

if __name__=='__main__':
    try:
        sys.exit(main())
    except (ValueError,KeyError,OSError) as e:
        print('Preflight rejected: '+str(e),file=sys.stderr)
        sys.exit(2)

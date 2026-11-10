#!/usr/bin/env python3
"""Run exactly ONE initialization or <=200-step diagnostic, never chain cases."""
import argparse
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
OLB = Path('/home/dell/openlb')

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--case', required=True, choices=['laplace','contact','flat_liquid','flat_gas'])
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--steps', type=int, default=0)
    a = parser.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]*', a.run_id) or not 0 <= a.steps <= 200:
        parser.error('unique safe run-id and 0..200 steps required')
    exe = HERE/'src/target_prevalidation'
    if not exe.is_file():
        parser.error('build executable first')
    build_record = HERE/'evidence/build_binding.json'
    if build_record.exists():
        binding = json.loads(build_record.read_text())
        if not all(Path(p).is_file() and sha(Path(p)) == h for p,h in binding['sha256'].items()):
            parser.error('built source/backend/binary changed; rebuild and re-audit before launch')
    elif a.steps:
        parser.error('build binding missing; diagnostic advancement not released')
    if (HERE/'output'/a.run_id).exists():
        parser.error('output already exists; never overwrite')
    record = HERE/'evidence'/a.run_id
    record.mkdir(exist_ok=False)
    cmd = [str(exe),'--case',a.case,'--run-id',a.run_id,'--steps',str(a.steps)]
    tracked = [HERE/'src/target_prevalidation.cpp',HERE/'src/target_parameters.h',
               HERE/'mapping.json',HERE/'protocol.json',HERE/'PROTOCOL.md',exe,Path(__file__).resolve(),
               OLB/'config.mk',OLB/'build/lib/libolbcore.a']
    # Record the complete backend source tree fingerprint, not just a hard-coded version.
    tracked += sorted(p for p in (OLB/'src').rglob('*') if p.is_file())
    hashes = {str(p): sha(p) for p in tracked}
    manifest = dict(run_id=a.run_id, case=a.case, requested_steps=a.steps, command=cmd,
                    cwd=str(HERE), started_utc=datetime.now(timezone.utc).isoformat(),
                    source_hashes=hashes,
                    openlb_head=subprocess.check_output(['git','-C',str(OLB),'rev-parse','HEAD'],text=True).strip(),
                    openlb_status=subprocess.check_output(['git','-C',str(OLB),'status','--short'],text=True),
                    model_not_GHY=True, formal_validation=False,
                    NUMERICAL_GATE='NOT_EVALUATED', RESULT_PASS='NOT_EVALUATED', geometry_PASS='NOT_EVALUATED')
    (record/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    with (record/'console.log').open('w') as log:
        completed = subprocess.run(cmd,cwd=HERE,stdout=log,stderr=subprocess.STDOUT)
    (record/'exit_code.txt').write_text(str(completed.returncode)+'\n')
    manifest['finished_utc'] = datetime.now(timezone.utc).isoformat()
    manifest['independent_exit_code'] = completed.returncode
    manifest['source_hashes_unchanged'] = all(sha(Path(p)) == h for p,h in hashes.items())
    (record/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(dict(run_id=a.run_id, exit_code=completed.returncode,
                         unchanged=manifest['source_hashes_unchanged'], record=str(record))))
    return completed.returncode

if __name__ == '__main__':
    sys.exit(main())

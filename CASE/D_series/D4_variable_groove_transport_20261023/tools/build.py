#!/usr/bin/env python3
"""Compile this case and record the local environment; never start a solver."""
from pathlib import Path
import hashlib
import json
import os
import subprocess

ROOT=Path(__file__).resolve().parents[1]
LIB=Path(os.environ.get('SIM240_OLB_ROOT','/home/dell/openlb')).resolve()


def main():
    evidence=ROOT/'evidence';evidence.mkdir(exist_ok=True)
    flags=['make','-C',str(ROOT/'src'),'OLB_ROOT='+str(LIB)]
    commands=[flags+['--dry-run'],['mpic++','--version'],
              ['git','-C',str(LIB),'rev-parse','HEAD'],['git','-C',str(LIB),'status','--porcelain']]
    results=[]
    for command in commands:
        result=subprocess.run(command,capture_output=True,text=True)
        results.append({'command':command,'exit_code':result.returncode,'stdout':result.stdout,'stderr':result.stderr})
    files=[LIB/'build/lib/libolbcore.a',LIB/'external/lib/libz.a',LIB/'external/lib/libtinyxml2.a']
    hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    (evidence/'build_environment.json').write_text(json.dumps({'commands':results,'library_hashes':hashes},indent=2))
    with (evidence/'build.log').open('w') as stream:
        result=subprocess.run(flags+['-j2'],stdout=stream,stderr=subprocess.STDOUT)
    (evidence/'build_exit_code.txt').write_text(str(result.returncode)+'\n')
    print(json.dumps({'compiler_exit_code':result.returncode,'simulation_started':False}))
    raise SystemExit(result.returncode)


if __name__=='__main__':main()

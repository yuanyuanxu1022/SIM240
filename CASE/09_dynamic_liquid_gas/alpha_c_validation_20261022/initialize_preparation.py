#!/usr/bin/env python3
"""Preparation only: fixed configurations with --initialize-only, zero collide/stream.
Never call after execution binding is frozen. Existing evidence is not overwritten.
"""
from pathlib import Path
import datetime as dt
import json
import subprocess
import sys

BASE=Path(__file__).resolve().parent

def main():
    if (BASE/'evidence/build_binding.json').exists():raise RuntimeError('already frozen')
    protocol=json.loads((BASE/'protocol.json').read_text());records=[]
    if (BASE/'evidence/initializations_v1.json').exists():raise RuntimeError('initialization evidence exists')
    for stage in ('alpha','c'):
      for c in protocol['stages'][stage]:
        name=f'init_{c["id"]}_v1';directory=BASE/'evidence'/name;directory.mkdir(exist_ok=False)
        output=directory/'data';binary='alpha_diffusion' if stage=='alpha' else 'coupled_check'
        command=[str(BASE/'build'/binary),c['id'],str(output),'--initialize-only']
        start=dt.datetime.now(dt.timezone.utc).isoformat()
        with (directory/'console.log').open('w') as f:
            p=subprocess.run(command,cwd=BASE,stdout=f,stderr=subprocess.STDOUT)
        (directory/'exit_code.txt').write_text(str(p.returncode)+'\n')
        records.append(dict(stage=stage,case_id=c['id'],run_id=name,command=command,
            started_utc=start,finished_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
            independent_exit_code=p.returncode,output=str(output)))
        (directory/'manifest.json').write_text(json.dumps(records[-1],indent=2)+'\n')
        print(name,'exit',p.returncode,flush=True)
        if p.returncode:
            (BASE/'evidence/initializations_v1_incomplete.json').write_text(json.dumps(records,indent=2)+'\n')
            return p.returncode
    (BASE/'evidence/initializations_v1.json').write_text(json.dumps(records,indent=2)+'\n')
    return 0

if __name__=='__main__':
    try:sys.exit(main())
    except Exception as exc:print('PREPARATION_ERROR:',repr(exc),file=sys.stderr);sys.exit(2)

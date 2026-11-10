#!/usr/bin/env python3
"""Seal local files and ldd dependencies; never launch a flow solver."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
PKG=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    path=PKG/'common/release_manifest.json'
    if path.exists():raise FileExistsError('Release already sealed')
    assert os.environ.get('WM_PROJECT_VERSION')=='13'
    libraries={}
    for name,relative in [('host','build/bin/grooveDarcyStaticFoam'),('subclass','build/lib/libgroovePorosity.so')]:
        r=subprocess.run(['ldd',str(PKG/relative)],capture_output=True,text=True,check=True)
        (PKG/'reports'/('ldd_'+name+'.log')).write_text(r.stdout)
        assert 'not found' not in r.stdout
        for line in r.stdout.splitlines():
            match=re.search(r'(?:=>\s+|^\s*)(/[^\s]+)',line)
            if match:
                f=Path(match[1]);libraries[str(f)]=sha(f)
    files=[]
    for sub in ['common','application','analysis','scripts','tests','provenance','references','reports','cases/GDI01']:
        for f in sorted((PKG/sub).rglob('*')):
            if not f.is_file() or f.is_symlink() or 'linux64GccDPInt32Opt' in f.parts or '__pycache__' in f.parts:continue
            files.append(dict(path=str(f.relative_to(PKG)),sha256=sha(f)))
    for rel in ['README.md','Allwmake','.gitignore','build/bin/grooveDarcyStaticFoam','build/lib/libgroovePorosity.so']:
        files.append(dict(path=rel,sha256=sha(PKG/rel)))
    env={k:os.environ[k] for k in ['WM_PROJECT_DIR','WM_PROJECT_VERSION','WM_OPTIONS','FOAM_ETC','FOAM_LIBBIN'] if k in os.environ}
    record=dict(case_id='GDI01',protocol_id='GDI-v1',release_version='1.0.0',files=files,
        libraries=[dict(path=p,sha256=h) for p,h in sorted(libraries.items())],openfoam_environment=env,
        execution_prepared=True,simulation_authorized=False,new_run_id=None)
    path.write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps(dict(release_files=len(files),runtime_libraries=len(libraries),flow_solver_executed=False)))
if __name__=='__main__':main()

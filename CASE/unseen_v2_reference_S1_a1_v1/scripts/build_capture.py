#!/usr/bin/env python3
"""Actual isolated make + provenance capture. Never invokes the native binary."""
from pathlib import Path
import hashlib,json,shlex,shutil,subprocess,sys

CASE=Path(__file__).resolve().parents[1]
def digest(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def command(args): return subprocess.check_output(args,text=True).strip()

def main():
    log=CASE/'evidence/build.log'
    if log.exists() or (CASE/'build/urv_reference').exists():
        raise ValueError('refuse overwrite of recorded build; use separate attempt')
    with log.open('x') as output:
        result=subprocess.run(['make'],cwd=CASE/'src',stdout=output,stderr=subprocess.STDOUT)
    if result.returncode: return result.returncode
    lines=log.read_text().splitlines()
    compile_command=next(s for s in lines if s.startswith('mpic++ ') and ' -c ' in s)
    link_command=next(s for s in lines if s.startswith('mpic++ ') and ' -c ' not in s)
    dependency=CASE/'build/urv_reference.d'
    rule=dependency.read_text().replace('\\\n',' ').splitlines()[0].split(':',1)[1]
    dependencies={str((CASE/'src'/p).resolve()) for p in shlex.split(rule)}
    sources=list(sorted((CASE/'src').glob('*.h')))+[CASE/'src/urv_reference.cpp']
    libraries=[Path('/home/dell/openlb/build/lib/libolbcore.a'),
               Path('/home/dell/openlb/external/lib/libz.a'),
               Path('/home/dell/openlb/external/lib/libtinyxml2.a')]
    binary=CASE/'build/urv_reference';ldd=CASE/'evidence/ldd.txt'
    ldd.write_text(command(['ldd',str(binary)])+'\n')
    runtime={}
    for line in ldd.read_text().splitlines():
        if 'not found' in line: raise ValueError('unresolved runtime library')
        for field in line.split():
            if field.startswith('/'):
                p=Path(field).resolve();runtime[str(p)]=digest(p)
    compiler=Path(shutil.which(shlex.split(command(['mpic++','--showme:command']))[0])).resolve()
    document=dict(compile_exit_code=result.returncode,preparation_only_build=False,
        solver_invoked_by_build_script=False,compile_command=compile_command,link_command=link_command,
        compile_working_directory=str(CASE/'src'),binary_path=str(binary),binary_sha256=digest(binary),
        build_recipe_path=str(CASE/'src/Makefile'),build_recipe_sha256=digest(CASE/'src/Makefile'),
        native_sources_sha256={str(p):digest(p) for p in sources},
        dependency_file_path=str(dependency),dependency_sha256={p:digest(p) for p in sorted(dependencies)},
        link_library_sha256={str(p):digest(p) for p in libraries},dynamic_library_sha256=runtime,
        compiler_executable=str(compiler),compiler_sha256=digest(compiler),
        compiler_version=command([str(compiler),'--version']),
        openlb_version=command(['git','-C','/home/dell/openlb','rev-parse','HEAD']))
    (CASE/'evidence/build_environment.json').write_text(json.dumps(document,indent=2)+'\n')
    print(json.dumps({k:document[k] for k in ['compile_exit_code','binary_sha256','solver_invoked_by_build_script']}))
    return 0
if __name__=='__main__':sys.exit(main())

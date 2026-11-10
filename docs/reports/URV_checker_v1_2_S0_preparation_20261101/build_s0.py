"""Capture a real isolated S0 build; does not invoke the compiled solver."""
from pathlib import Path
import hashlib
import json
import re
import shlex
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
CASE = ROOT / 'CASE/unseen_v2_reference_S0_v1_2'
CHECKER = ROOT / 'CASE/unseen_v2_reference_checker_v1_2'
sys.path.insert(0, str(CHECKER / 'analysis'))
from contracts import dependency_paths, time_stepping_defines


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    capture = CASE / 'evidence/build_environment.json'
    assert not capture.exists(), 'Do not replace a captured build'
    proc = subprocess.run(['make', '-j1'], cwd=CASE / 'src',
                          capture_output=True, text=True, timeout=300)
    log = proc.stdout + proc.stderr
    (CASE / 'evidence/build.log').write_text(log)
    assert proc.returncode == 0, 'Build failed; retain log and stop'
    commands = [v for v in proc.stdout.splitlines() if v.startswith('mpic++ ')]
    compile_command = next(v for v in commands if ' -c ' in v)
    link_command = next(v for v in commands if ' -c ' not in v)
    assert time_stepping_defines(compile_command) == [('-D', 'URV_PREPARATION_ONLY=0')]
    binary = CASE / 'build/urv_reference'
    dep = CASE / 'build/urv_reference.d'
    compiler = Path(shutil.which('g++')).resolve()
    wrapper = Path(shutil.which('mpic++')).resolve()
    ldd = subprocess.run(['ldd', str(binary)], capture_output=True, text=True, check=True)
    lddpath = CASE / 'evidence/ldd.txt'; lddpath.write_text(ldd.stdout)
    dynamic = {}
    for line in ldd.stdout.splitlines():
        assert 'not found' not in line
        hit = re.search(r'(/[^\s]+)', line)
        if hit:
            p = Path(hit.group(1)).resolve(); dynamic[str(p)] = sha(p)
    dependencies = dependency_paths(dep, CASE / 'src')
    sources = [CASE / 'src/urv_reference.cpp', CASE / 'src/mass_stats.h']
    old = ROOT / 'CASE/unseen_v2_reference_v1/src'
    assert all(p.read_bytes() == (old / p.name).read_bytes() for p in sources)
    libraries = [Path('/home/dell/openlb/build/lib/libolbcore.a'),
                 Path('/home/dell/openlb/external/lib/libz.a'),
                 Path('/home/dell/openlb/external/lib/libtinyxml2.a')]
    data = dict(compile_exit_code=proc.returncode, preparation_only_build=False,
        solver_invoked_by_build_script=False, compile_command=compile_command,
        link_command=link_command, compile_working_directory=str(CASE / 'src'),
        binary_path=str(binary), binary_sha256=sha(binary),
        build_recipe_path=str(CASE / 'src/Makefile'), build_recipe_sha256=sha(CASE / 'src/Makefile'),
        native_sources_sha256={str(p): sha(p) for p in sources},
        dependency_file_path=str(dep), dependency_sha256={p: sha(p) for p in sorted(dependencies)},
        link_library_sha256={str(p): sha(p) for p in libraries},
        dynamic_library_sha256=dynamic, compiler_executable=str(compiler), compiler_sha256=sha(compiler),
        mpi_wrapper_executable=str(wrapper), mpi_wrapper_sha256=sha(wrapper),
        compiler_version=subprocess.check_output([str(compiler), '--version'], text=True),
        mpi_wrapper_command=subprocess.check_output(['mpic++', '--showme'], text=True).strip(),
        openlb_commit=subprocess.check_output(['git', '-C', '/home/dell/openlb', 'rev-parse', 'HEAD'], text=True).strip(),
        openlb_git_status=subprocess.check_output(['git', '-C', '/home/dell/openlb', 'status', '--short'], text=True),
        runtime_capable_build_is_not_launch_authorization=True)
    capture.write_text(json.dumps(data, indent=2) + '\n')
    print(json.dumps(dict(compile_exit_code=0, binary_sha256=sha(binary),
                         dependency_count=len(dependencies), solver_invocations=0)))


if __name__ == '__main__':
    main()

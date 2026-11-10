#!/usr/bin/env python3
"""Bind existing evidence/current environment and reference tests; no build/run."""
import difflib
import json
import shutil
import subprocess
import sys
from pathlib import Path

from check_static import CASE, ROOT, BASE, BASE_SHA, check, sha


def capture(argv):
    completed=subprocess.run(argv,check=True,text=True,capture_output=True)
    return completed.stdout.strip()


def main():
    target=CASE/'reports/preparation_manifest.json'
    if target.exists():
        raise FileExistsError('Refusing to overwrite preparation evidence')
    previous=json.loads((ROOT/'CASE/reports/fine_T_mass_audit_20261013_v2/offline_checks.json').read_text())
    protected=dict(previous['protected_inputs'])
    prior_drift=[]
    # This README had a user-owned XY/Z route addition before this task.
    # Permit only the exact inspected document change; frozen data/source stay strict.
    refreshed_readme=ROOT/'CASE/reports/research_review_transport_v1/README.md'
    inspected_readme_sha='869350622f6dbf2438e97afb88dde150fdd58bc74edd9b75eae35f17e08902df'
    for path,digest in list(protected.items()):
        assert Path(path).is_file(),path
        current=sha(Path(path))
        if current!=digest:
            assert Path(path)==refreshed_readme and current==inspected_readme_sha,path
            prior_drift.append({'path':path,'previous_audit_sha256':digest,'current_sha256':current,
                                'reason':'Preexisting XY/Z route link added; preserve and bind current document'})
            protected[path]=current
    lib=Path('/home/dell/openlb')
    # Hash actual include tree and candidate static link libraries, not only HEAD.
    directories=(lib/'src',lib/'external/zlib',lib/'external/tinyxml2',lib/'build/lib',lib/'external/lib')
    tree_sets={str(directory):sorted(str(p) for p in directory.rglob('*') if p.is_file())
               for directory in directories}
    for directory in directories:
        for path in directory.rglob('*'):
            if path.is_file(): protected[str(path)]=sha(path)
    for name in ('config.mk','Makefile'):
        path=lib/name
        if path.is_file(): protected[str(path)]=sha(path)
    compiler_files={name:str(Path(shutil.which(name)).resolve()) for name in ('mpic++','c++','g++')}
    for path in compiler_files.values(): protected[path]=sha(Path(path))
    for name in ('libmpi.so','libmpi_cxx.so'):
        path=(Path('/usr/lib/x86_64-linux-gnu/openmpi/lib')/name).resolve()
        assert path.is_file()
        protected[str(path)]=sha(path)
    report=check()
    arithmetic=json.loads(capture([sys.executable,'-B',str(CASE/'scripts/test_arithmetic.py')]))
    prepared={str(path.relative_to(CASE)):sha(path) for folder in ('src','scripts')
              for path in sorted((CASE/folder).glob('*')) if path.is_file()}
    prepared.update({path.name:sha(path) for path in sorted(CASE.glob('*')) if path.is_file()})
    statuses={'status':'STATIC_PREPARATION_PASS_NOT_COMPILED',
              'solver_started':False,'compilation_performed':False,
              'runtime_equivalence_verified':False,'legacy_FAIL_preserved':True,
              'execution_authorized':False,'binary_sha256':None,
              'binary_status':'not_built','build_log':'not_created',
              'basis_environment':'CONTROLLED_CURRENT_ENVIRONMENT_NOT_HISTORICAL_REBUILD'}
    environment={'OpenLB_HEAD':capture(['git','-C',str(lib),'rev-parse','HEAD']),
                 'OpenLB_tracked_diff':capture(['git','-C',str(lib),'diff','--binary','HEAD']),
                 'OpenLB_status':capture(['git','-C',str(lib),'status','--short']),
                 'compiler_version':capture(['mpic++','--version']).splitlines()[0],
                 'MPI_compile_flags':capture(['mpic++','--showme:compile']),
                 'MPI_link_flags':capture(['mpic++','--showme:link']),
                 'host_arch':capture(['uname','-m']),
                 'memory_snapshot':capture(['free','-b']),
                 'numeric_reference_python':sys.version}
    environment['compiler_files']=compiler_files
    assert environment['OpenLB_HEAD']=='882924a9cfc8dcdf82909e39530789cb6f5ebcc4'
    source=(CASE/'src/fine_T_diagnostic.cpp').read_text()
    diff=''.join(difflib.unified_diff(BASE.read_text().splitlines(True),source.splitlines(True),
                                  fromfile=str(BASE),tofile=str(CASE/'src/fine_T_diagnostic.cpp')))
    for name,contents in (('source_additions.patch',diff),):
        with (CASE/'reports'/name).open('x') as fh: fh.write(contents)
    data={**statuses,'review_date':'2026-10-13','baseline':{'path':str(BASE),'sha256':BASE_SHA},
          'prepared_source_files':prepared,'protected_inputs':protected,'include_library_tree_file_sets':tree_sets,
          'previous_audit_preexisting_document_drift':prior_drift,
          'static_review':report,'arithmetic_reference':arithmetic,'environment':environment,
          'resource_budget':{'ranks':1,'compute_threads':1,'steps':4000,'rows':4001,
                             'fluid_nodes':3686400,'core_nodes':192*192*145,
                             'observer_vector_payload_bytes':3*3686400*8,
                             'snapshot_and_mask_payload_bytes':11*3686400*8+10*28+36,
                             'recommended_RAM_GiB':8,'recommended_disk_GiB':2,
                             'walltime':'unknown; diagnostic overhead unmeasured'}}
    assert all(sha(Path(p))==h for p,h in protected.items())
    with target.open('x') as fh:
        json.dump(data,fh,ensure_ascii=False,indent=2,allow_nan=False); fh.write('\n')
    print(json.dumps({'output':str(target),'protected_files':len(protected),**statuses},ensure_ascii=False))


if __name__=='__main__':
    main()

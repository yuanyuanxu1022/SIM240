"""Bind preparation sources and installed core libraries. Never authorize a run."""
from pathlib import Path
from common import HERE,ROOT,VERSION,sha,template,write_json


def main():
    files=set(HERE.glob('*.py'))|{HERE/'DIAGNOSTIC_CONTRACT.md',HERE/'README.md'}
    for part in ('src','protocol','environment','mesh_periodic_pressure_20261025',
                 'solve_entry_review_20261025','result_adapter_review_20261026',
                 'raw_capture_review_20261025','execution_record_review_20261026'):
        files|={p for p in (ROOT/part).rglob('*') if p.is_file() and '__pycache__' not in p.parts}
    # Preserve all source inputs behind the old stdlib-only contract too.
    import json
    repo=ROOT.parents[3]
    files|={repo/p for p in json.loads((ROOT/'protocol/review_input_hashes.json').read_text())}
    files|={ROOT/'.backend/bin/python'}
    for pattern in ('libpetsc.so*','libdolfinx.so*','libbasix.so*','libmpi.so*','libmpich.so*'):
        files|=set((ROOT/'.backend/lib').glob(pattern))
    for pattern in ('numpy/_core/*.so','petsc4py/PETSc*.so','dolfinx/cpp*.so','dolfinx_mpc/cpp*.so'):
        files|=set((ROOT/'.backend/lib/python3.12/site-packages').glob(pattern))
    for package in ('dolfinx','dolfinx_mpc','ffcx','ufl','basix','petsc4py','mpi4py'):
        files|=set((ROOT/'.backend/lib/python3.12/site-packages'/package).rglob('*.py'))
    lock=dict(version=VERSION,required_python=str(ROOT/'.backend/bin/python'),
              files={str(p.resolve()):sha(p) for p in sorted(files)})
    write_json(HERE/'source_lock.json',lock)
    c=template('/tmp/SIM240_PILOT_CAPPED_VOLUME_REQUIRED','/tmp/SIM240_PILOT_RECORD_PARENT_REQUIRED',
               '/sys/fs/cgroup/user.slice/user-1000.slice/user@1000.service/app.slice')
    write_json(HERE/'contract_template.json',c)
    print('PREPARATION_SOURCE_BINDING',len(lock['files']),'EXECUTION_FALSE')


if __name__=='__main__':main()

"""Single dormant mixed-N8 worker, entered only through the bound parent."""
import argparse
import importlib.util
import os
from pathlib import Path
import sys
import traceback
from common import HERE,ROOT,Rejected,digest,expected_system,read_json,sha,validate,write_json


def handshake(record):
    c=read_json(record/'contract.json')
    validate(c,execution=True)
    started=read_json(record/'STARTED.json')
    if (str(record)!=c['record_dir'] or str(Path.cwd())!=c['work_dir']
            or started['contract_sha256']!=digest(c) or started['parent_pid']!=os.getppid()
            or started['work_dir']!=c['work_dir'] or started['record_dir']!=c['record_dir']
            or started['kind']!='REAL_DIAGNOSTIC_UNVERIFIED'):
        raise Rejected('PARENT_CHILD_RUN_BINDING_MISMATCH')
    if any(os.environ.get(k)!=v for k,v in c['environment'].items()):
        raise Rejected('WORKER_ENVIRONMENT_CHANGED')
    if Path(sys.prefix).resolve()!=(ROOT/'.backend').resolve():
        raise Rejected('ISOLATED_PYTHON_REQUIRED')
    lock=read_json(record/'source_lock.json')
    if digest(lock)!=digest(read_json(HERE/'source_lock.json')) or started['inputs_sha256_before']!=lock['files']:
        raise Rejected('PARENT_SOURCE_LOCK_MISMATCH')
    current=Path('/proc/self/cgroup').read_text().strip().split('::',1)[1]
    if (Path('/sys/fs/cgroup')/current.lstrip('/')).resolve()!=Path(c['cgroup_parent'])/('sim240-'+c['run_id']):
        raise Rejected('WORKER_NOT_IN_BOUND_MEMORY_GROUP')
    return c


def stage(work,name):
    with (work/'stages.jsonl').open('a') as f:
        import json
        f.write(json.dumps({'stage':name})+'\n');f.flush()


def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def archive_failure(archive,record,work,c,name,error,vector,diagnostics,binding):
    try:
        archive.save_failure(work/'failures',c['run_id'],name,error,vector,diagnostics,
            {**binding,'contract_sha256':digest(c),'source_lock_sha256':c['source_lock_sha256']})
    except Exception as archive_error:
        # An exhausted work volume must not hide the original exception or
        # trigger a second archive attempt into the same partial directory.
        write_json(record/'failure_archive_error.json',dict(stage=name,
            original_exception=repr(error),archive_exception=repr(archive_error),
            vector_saved='NOT_GUARANTEED',NUMERICAL_GATE='NOT_EVALUATED',RESULT_PASS=False))
        raise RuntimeError('FAILURE_ARCHIVE_FAILED; original='+repr(error)) from archive_error


def run_one(record):
    c=handshake(record)  # Before any backend import/assembly.
    import numpy as np
    from records import arrays
    from assembly import prepare_bound_mixed_system
    from solver import DiagnosticGMRES,solve_prepared_mixed_system
    work=Path(c['work_dir']); system=None; result=None; archived=False
    archive=load(ROOT/'execution_record_review_20261026/failure_archive.py','d4_v2_failure_archive')
    def fail(name,error,vector,diagnostics,binding):
        nonlocal archived
        # Mark the attempt before writing so outer failure handling never
        # overwrites the first error with FAILURE_ALREADY_ARCHIVED.
        archived=True
        archive_failure(archive,record,work,c,name,error,vector,diagnostics,binding)
    try:
        stage(work,'ASSEMBLY')
        system=prepare_bound_mixed_system(c)
        reference=expected_system()
        for key in ('matrix_csr_sha256','rhs_sha256_before_projection'):
            if system[key]!=reference[key]: raise Rejected('ASSEMBLY_HASH_DIFFERS_FROM_PREFLIGHT')
        item=system['item'];A=system['matrix'];row,col,value=A.getValuesCSR()
        W=item['mpc'].function_space;V,vm=W.sub(0).collapse();Q,pm=W.sub(1).collapse()
        count=item['domain'].topology.index_map(2).size_local
        vd=np.stack([np.asarray(vm[0])[(2*np.asarray(V.dofmap.cell_dofs(i))[:,None]+np.arange(2)).reshape(-1)] for i in range(count)])
        pd=np.stack([np.asarray(pm[0])[Q.dofmap.cell_dofs(i)] for i in range(count)])
        environment=dict(python=sys.version,executable=sys.executable,
            executable_sha256=sha(sys.executable),environment=dict(os.environ))
        from importlib.metadata import version
        environment['versions']={name:version(name) for name in ('fenics-dolfinx','fenics-basix','fenics-ffcx','petsc4py','dolfinx_mpc','numpy','mpi4py')}
        write_json(work/'runtime_environment.json',environment)
        arrays(work/'system',dict(csr_indptr=row.copy(),csr_indices=col.copy(),csr_values=value.copy(),
               rhs_before=np.asarray(system['rhs_before_projection'].array).copy(),
               rhs_after=np.asarray(system['rhs'].array).copy(),pressure_null_vector=system['candidate'].copy(),
               cell_velocity_mixed_dofs=vd,cell_pressure_mixed_dofs=pd),
               dict(record_kind='REAL_DIAGNOSTIC_UNVERIFIED',matrix_shape=list(A.getSize()),
                    contract_sha256=digest(c),gauge={k:v for k,v in system['gauge'].items() if k not in {'vector','nullspace'}},
                    pressure_support=system['support'],physical_plan=item['plan'],mesh_stats=item['stats'],
                    cell_dof_layout='P2 vector: 6 nodes x 2 components; P1 pressure: 3 nodes; mixed global indices',
                    matrix_csr_sha256=system['matrix_csr_sha256'],rhs_sha256_before_projection=system['rhs_sha256_before_projection']))
        stage(work,'SOLVER')
        result=solve_prepared_mixed_system(system,DiagnosticGMRES(**c['solver_settings']),c,fail)
        stage(work,'RESULT_RECORD')
        bridge=load(ROOT/'result_adapter_review_20261026/bridge.py','d4_v2_result_bridge')
        bundle=bridge.build_raw_bundle(item,result)
        bundle['periodic_coefficients']=np.asarray([pair['coefficient'] for pair in item['stats']['periodic_link_audit']['pairs']],dtype=np.float64)
        arrays(work/'solution',bundle,dict(record_kind='REAL_DIAGNOSTIC_UNVERIFIED',contract_sha256=digest(c)))
        write_json(work/'solver_diagnostics.json',result['diagnostics'])
        write_json(work/'worker_completion.json',dict(status='SOLVER_EXITED_UNVERIFIED',run_id=c['run_id'],
                   contract_sha256=digest(c),NUMERICAL_GATE='NOT_EVALUATED',RESULT_PASS=False,geometry_PASS=None))
    except Exception as exc:
        if not archived:
            vector=None
            if result is not None:
                try: vector=np.asarray(result['algebraic_solution_before_backsubstitution'].array).copy()
                except Exception: pass
            fail('WORKER_FAILURE',exc,vector,{'original_exception':repr(exc)},
                 {} if system is None else {'matrix_csr_sha256':system['matrix_csr_sha256']})
        raise


def main():
    p=argparse.ArgumentParser();p.add_argument('--record-dir',required=True,type=Path);a=p.parse_args()
    try: run_one(a.record_dir)
    except Exception:
        traceback.print_exc();return 2
    return 0


if __name__=='__main__': raise SystemExit(main())

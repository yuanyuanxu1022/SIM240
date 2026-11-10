"""Independent CSR/field checks. No PETSc, DOLFINx, project solver or assembly."""
import argparse
import json
from pathlib import Path
import numpy as np
import hashlib


def load_json(path):
    def pairs(items):
        out={}
        for k,v in items:
            if k in out:raise ValueError('DUPLICATE_JSON_KEY')
            out[k]=v
        return out
    return json.loads(Path(path).read_text(),object_pairs_hook=pairs,
        parse_constant=lambda x:(_ for _ in ()).throw(ValueError('NONFINITE_JSON')))


def file_sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda:f.read(1048576),b''):h.update(chunk)
    return h.hexdigest()


def object_sha(obj):
    return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def read_group(path):
    # Independent reader intentionally does not reuse records.read_arrays.
    import hashlib
    path = Path(path)
    if (path/"INCOMPLETE").exists():
        raise ValueError("INCOMPLETE_ARRAY_RECORD")
    spec = load_json(path/"manifest.json")
    data = {}
    for name, item in spec["files"].items():
        p = path/name
        if Path(name).name != name or p.is_symlink():
            raise ValueError("INVALID_ARRAY_PATH")
        if hashlib.sha256(p.read_bytes()).hexdigest() != item["sha256"]:
            raise ValueError("RAW_HASH_MISMATCH:"+name)
        a = np.load(p, allow_pickle=False)
        if a.dtype.str != item["dtype"] or list(a.shape) != item["shape"] or not np.all(np.isfinite(a)):
            raise ValueError("RAW_LAYOUT_OR_FINITE_CHECK_FAILED:"+name)
        data[name[:-4]] = a
    return data, spec["metadata"]


def check(work):
    system, meta = read_group(Path(work)/"system")
    raw, _ = read_group(Path(work)/"solution")
    row, col, val = (system[k] for k in ("csr_indptr", "csr_indices", "csr_values"))
    shape = tuple(meta["matrix_shape"])
    if (len(shape) != 2 or shape[0] != shape[1] or row.dtype.kind != "i" or col.dtype.kind != "i"
            or row.ndim != 1 or col.ndim != 1 or val.ndim != 1 or len(row) != shape[0]+1
            or row[0] != 0 or row[-1] != len(val) or len(col) != len(val)
            or np.any(np.diff(row) < 0) or np.any(col < 0) or np.any(col >= shape[1])):
        raise ValueError("CSR_INVALID")
    x = raw["algebraic_solution_before_backsub"]
    b0, b1, n = (system[k] for k in ("rhs_before", "rhs_after", "pressure_null_vector"))
    if any(a.shape != (shape[0],) for a in (x, b0, b1, n)) or min(np.linalg.norm(b0),np.linalg.norm(b1)) <= 0:
        raise ValueError("VECTOR_DIMENSIONS_OR_ZERO_RHS")
    def multiply(a):
        return np.array([np.dot(val[row[i]:row[i+1]], a[col[row[i]:row[i+1]]]) for i in range(shape[0])])
    Ax = multiply(x)
    normA = np.linalg.norm(val)
    if normA <= 0 or abs(np.linalg.norm(n)-1) > 1e-12:
        raise ValueError("MATRIX_OR_GAUGE_INVALID")
    ATn = np.zeros(shape[1])
    for i in range(shape[0]):
        np.add.at(ATn, col[row[i]:row[i+1]], val[row[i]:row[i+1]]*n[i])
    r = raw["reconstructed_solution"]
    vm, pm = raw["velocity_reconstructed_dof_indices"], raw["pressure_reconstructed_dof_indices"]
    wall, slave, master = (raw[k] for k in ("wall_velocity_dof_indices", "periodic_slave_dofs", "periodic_master_dofs"))
    for ids in (vm,pm,wall,slave,master):
        if ids.dtype.kind != "i" or ids.ndim != 1 or np.any(ids<0) or np.any(ids>=len(r)):
            raise ValueError("FIELD_INDEX_INVALID")
    if (r.shape != x.shape or slave.shape != master.shape or len(vm)+len(pm)!=len(r)
            or len(np.unique(np.r_[vm,pm])) != len(r) or len(np.unique(slave))!=len(slave)
            or np.intersect1d(slave,master).size or not set(wall)<=set(vm)):
        raise ValueError("FIELD_MAP_COVERAGE_INVALID")
    coefficients=raw['periodic_coefficients']
    if coefficients.shape!=slave.shape or np.any(np.abs(coefficients-1)>1e-11):
        raise ValueError('ONE_TO_ONE_UNIT_PERIODIC_CONTRACT_REQUIRED')
    expected=x.copy();expected[slave]=coefficients*x[master]
    reconstruction=float(np.max(np.abs(r-expected)/np.maximum(1.,np.abs(expected))))
    p, pz, w = (raw[k] for k in ("pressure_raw_P1", "pressure_zero_mean_P1", "pressure_area_weights_hat2"))
    if p.shape != w.shape or p.shape!=(len(pm),) or pz.shape != p.shape or np.any(w<=0):
        raise ValueError("PRESSURE_WEIGHTS_INVALID")
    if not np.array_equal(r[pm],p) or not np.array_equal(r[vm],raw["velocity_reconstructed_values"]):
        raise ValueError("FIELD_VALUES_DIFFER_FROM_VECTOR")
    mean = np.dot(w,p)/w.sum()
    scale = max(1.0,float(np.max(np.abs(p))))
    trace = np.max(np.abs(r[slave]-r[master])/np.maximum(1.,np.maximum(np.abs(r[slave]),np.abs(r[master])))) if len(slave) else 0.0
    metrics = dict(true_residual_before_projection=float(np.linalg.norm(Ax-b0)/np.linalg.norm(b0)),
        true_residual_after_projection=float(np.linalg.norm(Ax-b1)/np.linalg.norm(b1)),
        right_null_relative=float(np.linalg.norm(multiply(n))/normA),
        left_null_relative=float(np.linalg.norm(ATn)/normA),
        rhs_compatibility_before=float(abs(n@b0)/np.linalg.norm(b0)),
        rhs_projection_relative=float(np.linalg.norm(b1-b0)/np.linalg.norm(b0)),
        pressure_removed_mean=float(mean), pressure_shift_error=float(np.max(np.abs(pz-(p-mean)))/scale),
        pressure_mean_relative=float(abs(w@pz)/w.sum()/scale),
        reconstruction_relative=reconstruction,
        periodic_trace_relative=float(trace), wall_trace_relative=float(np.max(np.abs(r[wall])/np.maximum(1.,np.abs(r[wall])))) if len(wall) else 0.0)
    passed = (max(metrics[k] for k in ("true_residual_before_projection", "true_residual_after_projection",
        "right_null_relative", "left_null_relative", "rhs_compatibility_before", "rhs_projection_relative",
        "periodic_trace_relative", "wall_trace_relative", "reconstruction_relative")) <= 1e-10
        and max(metrics["pressure_mean_relative"],metrics["pressure_shift_error"]) <= 1e-12)
    return dict(status="DIAGNOSTIC_READBACK_PASS" if passed else "DIAGNOSTIC_READBACK_FAIL",
                record_kind=meta["record_kind"], metrics=metrics,
                field_accuracy_energy_flux="NOT_EVALUATED", NUMERICAL_GATE="NOT_EVALUATED",
                RESULT_PASS=False, geometry_PASS=None, prediction_permission="HOLD")


def main():
    parser=argparse.ArgumentParser(description="Read saved arrays only; never solves")
    parser.add_argument("work_dir",type=Path)
    parser.add_argument("--record-dir",type=Path)
    parser.add_argument('--archive-only',action='store_true',help='Integrity of stopped-run archive, including failed/partial runs; no numerical PASS')
    a=parser.parse_args()
    if a.archive_only:
        if not a.record_dir:raise ValueError('ARCHIVE_ONLY_REQUIRES_RECORD_DIR')
        result=check_archive(a.record_dir)
        if str(a.work_dir.resolve())!=str((a.record_dir/'archive').resolve()):raise ValueError('ARCHIVE_PATH_NOT_BOUND')
        print(json.dumps(result,indent=2,allow_nan=False));return 0
    result=check(a.work_dir)
    if a.record_dir:
        result['capture_checks']=check_capture(a.record_dir,a.work_dir)
    elif result['record_kind']=='REAL_DIAGNOSTIC_UNVERIFIED':
        raise ValueError('REAL_RECORD_REQUIRES_INDEPENDENT_PARENT_CAPTURE')
    print(json.dumps(result,indent=2,allow_nan=False))
    return 0 if result["status"]=="DIAGNOSTIC_READBACK_PASS" else 1


def check_capture(record,work):
    import hashlib
    record,work=Path(record),Path(work)
    load=lambda name:load_json(record/name)
    c,s,m=(load(name) for name in ('contract.json','STARTED.json','capture_manifest.json'))
    digest=hashlib.sha256(json.dumps(c,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
    if (str(record.resolve())!=c['record_dir']
            or any(x['contract_sha256']!=digest or x['run_id']!=c['run_id'] for x in (s,m))
            or s['record_dir']!=c['record_dir'] or s['work_dir']!=c['work_dir']
            or s['argv']!=c['argv'] or m['independent_exit_code']!=0 or m.get('stop_reason')
            or any(m.get(k) for k in ('supervisor_error','inventory_error','archive_error','stop_cleanup_error'))
            or m.get('children_stopped') is not True or m.get('archive_status')!='ARCHIVE_COMPLETE'
            or not m['inputs_unchanged']
            or m['inputs_sha256_after']!=s['inputs_sha256_before']
            or (record/'independent_exit_code.txt').read_text().strip()!='0'):
        raise ValueError('PROCESS_OR_INPUT_BINDING_FAILED')
    a=load('archive_manifest.json')
    if ((record/'archive.incomplete').exists() or (record/'archive_failure.json').exists()
            or a['status']!='ARCHIVE_COMPLETE' or a['source_work_dir']!=c['work_dir']
            or a['archive_dir']!=str(record/'archive') or a['contract_sha256']!=digest
            or a['run_id']!=c['run_id'] or a['independent_exit_code']!=m['independent_exit_code']
            or a['work_files']!=m['work_files'] or a['source_deleted'] is not False
            or str(work.resolve()) not in (c['work_dir'],a['archive_dir'])):
        raise ValueError('ARCHIVE_BINDING_INCOMPLETE')
    # Always inspect the durable copy, even when caller also supplies original work.
    validate_inventory(Path(a['archive_dir']),m['work_files'])
    validate_inventory(work,m['work_files'])
    actual={str(p.relative_to(work)) for p in work.rglob('*') if p.is_file()}
    if actual!=set(m['work_files']):raise ValueError('WORK_INVENTORY_INCOMPLETE')
    for name,spec in m['work_files'].items():
        path=work/name
        if path.is_symlink() or not path.resolve().is_relative_to(work.resolve()) or hashlib.sha256(path.read_bytes()).hexdigest()!=spec['sha256']:
            raise ValueError('CAPTURED_FILE_CHANGED:'+name)
    system,meta=read_group(work/'system')
    raw,rawmeta=read_group(work/'solution')
    if m['kind']=='REAL_DIAGNOSTIC_UNVERIFIED':
        lock=load_json(record/'source_lock.json')
        protocol=[h for p,h in lock['files'].items() if p.endswith('/pilot_record_v3_20261026/DIAGNOSTIC_CONTRACT.md')]
        if (c.get('version')!='D4_PILOT_RECORD_V3_20261026_PREPARATION'
                or c.get('planned_id')!='B0MIN_MMS_mixed_N8' or c.get('status')!='APPROVED_DIAGNOSTIC_ONLY'
                or c.get('authorized_to_execute') is not True or not isinstance(c.get('approval'),dict)
                or not c['approval'].get('authorization_text','').strip() or len(protocol)!=1
                or c['approval'].get('protocol_sha256')!=protocol[0]
                or meta['record_kind']!=m['kind'] or rawmeta['record_kind']!=m['kind']):
            raise ValueError('REAL_CAPTURE_RELEASE_INVALID')
        required={'mesh_coordinates_hat','mesh_triangles','algebraic_solution_before_backsub',
            'reconstructed_solution','velocity_dof_coordinates_hat','velocity_dof_components',
            'velocity_reconstructed_dof_indices','velocity_reconstructed_values',
            'pressure_coordinates_hat','pressure_reconstructed_dof_indices','wall_velocity_dof_indices',
            'pressure_area_weights_hat2','pressure_raw_P1','pressure_zero_mean_P1',
            'periodic_slave_dofs','periodic_master_dofs','periodic_coefficients'}
        if set(raw)!=required:raise ValueError('REAL_RAW_ARRAY_SET_INCOMPLETE')
        complete=json.loads((work/'worker_completion.json').read_text())
        if any(obj.get('contract_sha256')!=digest for obj in (complete,meta,rawmeta)) or complete['run_id']!=c['run_id']:
            raise ValueError('WORKER_RESULT_CONTRACT_MISMATCH')
        matrixhash=hashlib.sha256(b''.join(np.ascontiguousarray(system[k]).tobytes() for k in ('csr_indptr','csr_indices','csr_values'))).hexdigest()
        rhshash=hashlib.sha256(np.ascontiguousarray(system['rhs_before']).tobytes()).hexdigest()
        if matrixhash!=meta['matrix_csr_sha256'] or rhshash!=meta['rhs_sha256_before_projection']:
            raise ValueError('ASSEMBLY_BYTE_BINDING_MISMATCH')
        for key,width in (('cell_velocity_mixed_dofs',12),('cell_pressure_mixed_dofs',3)):
            dofs=system[key]
            if dofs.ndim!=2 or dofs.shape[1]!=width or dofs.dtype.kind!='i' or np.any(dofs<0) or np.any(dofs>=len(raw['reconstructed_solution'])):
                raise ValueError('CELL_DOF_MAP_INVALID')
        check_cell_maps(system,raw)
        check_required_records(record,work,c,s,m,check(work))
    return dict(status='CAPTURE_BINDING_PASS',kind=m['kind'],all_work_files_hashed=len(actual))


def validate_inventory(root,spec):
    if root.is_symlink():raise ValueError('ARCHIVE_ROOT_SYMLINK')
    actual={}
    for p in root.rglob('*'):
        if p.is_symlink():raise ValueError('INVENTORY_SYMLINK')
        if p.is_dir():continue
        if not p.is_file():raise ValueError('INVENTORY_SPECIAL_FILE')
        actual[str(p.relative_to(root))]={'sha256':file_sha(p),'bytes':p.stat().st_size}
    if actual!=spec:raise ValueError('WORK_INVENTORY_INCOMPLETE_OR_CHANGED')


def check_archive(record):
    """Failed-run partial files may be intact; integrity never implies solve acceptance."""
    record=Path(record)
    c=load_json(record/'contract.json');s=load_json(record/'STARTED.json')
    m=load_json(record/'capture_manifest.json');a=load_json(record/'archive_manifest.json')
    if (str(record.resolve())!=c['record_dir'] or m.get('archive_status')!='ARCHIVE_COMPLETE'
            or m.get('archive_error') or m.get('inventory_error') or m.get('children_stopped') is not True
            or any(v.get('contract_sha256')!=object_sha(c) or v.get('run_id')!=c['run_id'] for v in (s,m,a))
            or a['status']!='ARCHIVE_COMPLETE' or a['source_work_dir']!=c['work_dir']
            or a['archive_dir']!=str(record/'archive') or a['source_deleted'] is not False
            or a['work_files']!=m['work_files'] or a['independent_exit_code']!=m['independent_exit_code']
            or (record/'archive.incomplete').exists() or (record/'archive_failure.json').exists()):
        raise ValueError('ARCHIVE_BINDING_INCOMPLETE')
    code=(record/'independent_exit_code.txt').read_text().strip()
    if code!=('START_FAILED' if m['independent_exit_code'] is None else str(m['independent_exit_code'])):
        raise ValueError('ARCHIVE_EXIT_CODE_DISAGREES')
    validate_inventory(record/'archive',a['work_files'])
    return dict(status='ARCHIVE_INTEGRITY_PASS',kind=m['kind'],independent_exit_code=m['independent_exit_code'],
                stopped_reason=m.get('stop_reason'),all_work_files_hashed=len(a['work_files']),
                numerical_acceptance='NOT_EVALUATED',NUMERICAL_GATE='NOT_EVALUATED',RESULT_PASS=False,geometry_PASS=None)


def check_required_records(record,work,c,started,capture,result):
    """Pure saved-record schema check, also testable with explicitly synthetic records."""
    record,work=Path(record),Path(work)
    required={'stdout.log','stderr.log','runtime_environment.json','stages.jsonl',
              'solver_diagnostics.json','worker_completion.json','system/manifest.json','solution/manifest.json'}
    if not required<=set(capture['work_files']):raise ValueError('REQUIRED_RECORD_MISSING')
    if not all((work/name).is_file() for name in required):raise ValueError('REQUIRED_RECORD_MISSING')
    d=load_json(work/'solver_diagnostics.json')
    cfg=c['solver_settings']
    if (d.get('ksp_type')!='gmres' or d.get('pc_type')!='none'
            or type(d.get('ksp_reason')) is not int or d['ksp_reason']<=0
            or type(d.get('ksp_iterations')) is not int or not 0<=d['ksp_iterations']<=cfg['max_iterations']
            or any(d.get(k)!=v for k,v in cfg.items())):
        raise ValueError('SOLVER_CONFIGURATION_OR_REASON_INVALID')
    history=np.asarray(d['ksp_reported_residual_history'])
    residual=d['true_unpreconditioned_relative_residual']
    if (history.ndim!=1 or not 1<=len(history)<=cfg['max_iterations']+1 or not np.all(np.isfinite(history))
            or not isinstance(residual,(int,float)) or not np.isfinite(residual) or residual<0
            or residual>cfg['true_residual_target']
            or abs(residual-result['metrics']['true_residual_after_projection'])>1e-12):
        raise ValueError('SOLVER_RESIDUAL_RECORD_DISAGREES')
    complete=load_json(work/'worker_completion.json')
    if (complete.get('status')!='SOLVER_EXITED_UNVERIFIED' or complete.get('run_id')!=c['run_id']
            or complete.get('contract_sha256')!=object_sha(c)
            or complete.get('NUMERICAL_GATE')!='NOT_EVALUATED' or complete.get('RESULT_PASS') is not False
            or complete.get('geometry_PASS') is not None):raise ValueError('COMPLETION_RECORD_INVALID')
    stages=[load_line for load_line in (json.loads(line) for line in (work/'stages.jsonl').read_text().splitlines())]
    if stages!=[{'stage':name} for name in ('ASSEMBLY','SOLVER','RESULT_RECORD')]:raise ValueError('STAGE_SEQUENCE_INVALID')
    lock=load_json(record/'source_lock.json')
    if file_sha(record/'source_lock.json')!=c['source_lock_sha256'] or lock['files']!=started['inputs_sha256_before']:
        raise ValueError('CAPTURE_SOURCE_LOCK_INVALID')
    env=load_json(work/'runtime_environment.json')
    if (env['executable']!=c['argv'][0] or any(env['environment'].get(k)!=v for k,v in c['environment'].items())
            or env['executable_sha256']!=lock['files'].get(str(Path(env['executable']).resolve()))):
        raise ValueError('RUNTIME_ENVIRONMENT_INVALID')
    expected_versions={'fenics-dolfinx':'0.11.0','fenics-basix':'0.11.0','fenics-ffcx':'0.11.0',
                       'petsc4py':'3.25.6','dolfinx_mpc':'0.11.0','numpy':'2.5.4','mpi4py':'4.1.2'}
    if env['versions']!=expected_versions:raise ValueError('RUNTIME_VERSIONS_CHANGED')
    system,meta=read_group(work/'system');raw,_=read_group(work/'solution')
    if meta['physical_plan']!=c['physical_plan']:raise ValueError('RECORDED_PHYSICAL_PLAN_CHANGED')
    links=meta['mesh_stats']['periodic_link_audit']['pairs']
    saved=sorted(zip(raw['periodic_slave_dofs'].tolist(),raw['periodic_master_dofs'].tolist(),raw['periodic_coefficients'].tolist()))
    if saved!=sorted((p['slave_dof'],p['master_dof'],p['coefficient']) for p in links):raise ValueError('PERIODIC_MAP_RECORD_DISAGREES')
    pf=record/'assembly_preflight.json'
    names=[p for p in lock['files'] if p.endswith('/solve_entry_review_20261025/evidence/preflight_all9.json')]
    if len(names)!=1 or file_sha(pf)!=lock['files'][names[0]]:raise ValueError('PREFLIGHT_COPY_INVALID')
    refs=[r['preflight'] for r in load_json(pf)['records'] if r['planned_id']==c['planned_id'] and r['exit_code']==0]
    if len(refs)!=1 or any(meta[k]!=refs[0][k] for k in ('matrix_csr_sha256','rhs_sha256_before_projection')):
        raise ValueError('ASSEMBLY_DIFFERS_FROM_PREFLIGHT')
    if (capture.get('memory_enforcement')!='cgroup_v2_memory.max'
            or capture.get('wall_seconds',float('inf'))>c['resource_limits']['wall_seconds']
            or capture.get('sampled_output_peak_bytes',float('inf'))>c['resource_limits']['output_bytes']):
        raise ValueError('RESOURCE_RECORD_INVALID')
    stats=capture['cgroup_stats'];events=dict(line.split() for line in stats['memory.events'].splitlines())
    if (int(stats['memory.max'])!=c['resource_limits']['memory_bytes'] or int(events.get('oom_kill','0'))
            or 'populated 1' in stats['cgroup.events']):raise ValueError('CGROUP_RECORD_INVALID')
    resources=started['resource_before']
    if (resources['work_volume']['mechanism']!='preexisting_dedicated_tmpfs'
            or resources['work_volume']['capacity_bytes']>c['resource_limits']['output_bytes']
            or resources['record_volume']['identity']['filesystem'] not in {'ext4','xfs','btrfs','zfs'}
            or resources['record_volume']['available_bytes']<c['resource_limits']['minimum_record_disk_bytes']
            or resources['MemAvailable_bytes']<c['resource_limits']['minimum_available_memory_bytes']):
        raise ValueError('START_RESOURCE_PREREQUISITE_INVALID')
    if c['solver_settings']!={'ksp_rtol':1e-10,'true_residual_target':1e-10,'max_iterations':2000,'restart':50}:
        raise ValueError('FROZEN_DIAGNOSTIC_SETTINGS_CHANGED')
    return {'status':'REQUIRED_RECORD_SCHEMA_PASS','scientific_acceptance':'NOT_EVALUATED'}


def check_cell_maps(system,raw):
    points,tri=raw['mesh_coordinates_hat'],raw['mesh_triangles']
    if points.ndim!=2 or points.shape[1]!=2 or tri.ndim!=2 or tri.shape[1]!=3 or tri.dtype.kind!='i' or np.any(tri<0) or np.any(tri>=len(points)):
        raise ValueError('TRIANGULAR_MESH_INVALID')
    vd,pd=system['cell_velocity_mixed_dofs'],system['cell_pressure_mixed_dofs']
    if vd.shape!=(len(tri),12) or pd.shape!=(len(tri),3):raise ValueError('CELL_COUNT_MISMATCH')
    vc,comp,vm=(raw[k] for k in ('velocity_dof_coordinates_hat','velocity_dof_components','velocity_reconstructed_dof_indices'))
    pc,pm=raw['pressure_coordinates_hat'],raw['pressure_reconstructed_dof_indices']
    if vc.shape!=(len(vm),2) or pc.shape!=(len(pm),2) or comp.shape!=(len(vm),):raise ValueError('COORDINATE_MAP_LAYOUT')
    vk={int(i):tuple(np.rint(x/1e-11).astype(np.int64))+(int(c),) for i,x,c in zip(vm,vc,comp)}
    pk={int(i):tuple(np.rint(x/1e-11).astype(np.int64)) for i,x in zip(pm,pc)}
    for t,v,p in zip(tri,vd,pd):
        a,b,c=points[t];nodes=[a,b,c,(a+b)/2,(a+c)/2,(b+c)/2]
        vertices={tuple(np.rint(x/1e-11).astype(np.int64)) for x in (a,b,c)}
        expected={tuple(np.rint(x/1e-11).astype(np.int64))+(component,) for x in nodes for component in (0,1)}
        if {pk.get(int(i)) for i in p}!=vertices or {vk.get(int(i)) for i in v}!=expected:
            raise ValueError('CELL_ELEMENT_COORDINATES_MISMATCH')


if __name__=="__main__":
    raise SystemExit(main())

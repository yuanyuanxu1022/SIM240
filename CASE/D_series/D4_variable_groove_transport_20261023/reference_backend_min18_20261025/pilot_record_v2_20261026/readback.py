"""Independent CSR/field checks. No PETSc, DOLFINx, project solver or assembly."""
import argparse
import json
from pathlib import Path
import numpy as np


def read_group(path):
    # Independent reader intentionally does not reuse records.read_arrays.
    import hashlib
    path = Path(path)
    if (path/"INCOMPLETE").exists():
        raise ValueError("INCOMPLETE_ARRAY_RECORD")
    spec = json.loads((path/"manifest.json").read_text())
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
    if r.shape != x.shape or slave.shape != master.shape or len(np.unique(np.r_[vm,pm])) != len(r):
        raise ValueError("FIELD_MAP_COVERAGE_INVALID")
    p, pz, w = (raw[k] for k in ("pressure_raw_P1", "pressure_zero_mean_P1", "pressure_area_weights_hat2"))
    if p.shape != w.shape or pz.shape != p.shape or np.any(w<=0):
        raise ValueError("PRESSURE_WEIGHTS_INVALID")
    if not np.array_equal(r[pm],p) or not np.array_equal(r[vm],raw["velocity_reconstructed_values"]):
        raise ValueError("FIELD_VALUES_DIFFER_FROM_VECTOR")
    mean = np.dot(w,p)/w.sum()
    scale = max(1.0,float(np.max(np.abs(p))))
    trace = np.max(np.abs(r[slave]-r[master]))/max(1.0,float(np.max(np.abs(r)))) if len(slave) else 0.0
    metrics = dict(true_residual_before_projection=float(np.linalg.norm(Ax-b0)/np.linalg.norm(b0)),
        true_residual_after_projection=float(np.linalg.norm(Ax-b1)/np.linalg.norm(b1)),
        right_null_relative=float(np.linalg.norm(multiply(n))/normA),
        left_null_relative=float(np.linalg.norm(ATn)/normA),
        rhs_compatibility_before=float(abs(n@b0)/np.linalg.norm(b0)),
        rhs_projection_relative=float(np.linalg.norm(b1-b0)/np.linalg.norm(b0)),
        pressure_removed_mean=float(mean), pressure_shift_error=float(np.max(np.abs(pz-(p-mean)))/scale),
        pressure_mean_relative=float(abs(w@pz)/w.sum()/scale),
        periodic_trace_relative=float(trace), wall_trace_relative=float(np.max(np.abs(r[wall]))/max(1.0,np.max(np.abs(r)))) if len(wall) else 0.0)
    passed = (max(metrics[k] for k in ("true_residual_before_projection", "true_residual_after_projection",
        "right_null_relative", "left_null_relative", "rhs_compatibility_before", "rhs_projection_relative",
        "periodic_trace_relative", "wall_trace_relative")) <= 1e-10
        and max(metrics["pressure_mean_relative"],metrics["pressure_shift_error"]) <= 1e-12)
    return dict(status="DIAGNOSTIC_READBACK_PASS" if passed else "DIAGNOSTIC_READBACK_FAIL",
                record_kind=meta["record_kind"], metrics=metrics,
                field_accuracy_energy_flux="NOT_EVALUATED", NUMERICAL_GATE="NOT_EVALUATED",
                RESULT_PASS=False, geometry_PASS=None, prediction_permission="HOLD")


def main():
    parser=argparse.ArgumentParser(description="Read saved arrays only; never solves")
    parser.add_argument("work_dir",type=Path)
    parser.add_argument("--record-dir",type=Path)
    a=parser.parse_args()
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
    load=lambda name:json.loads((record/name).read_text())
    c,s,m=(load(name) for name in ('contract.json','STARTED.json','capture_manifest.json'))
    digest=hashlib.sha256(json.dumps(c,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
    if (str(work.resolve())!=c['work_dir'] or str(record.resolve())!=c['record_dir']
            or any(x['contract_sha256']!=digest or x['run_id']!=c['run_id'] for x in (s,m))
            or s['record_dir']!=c['record_dir'] or s['work_dir']!=c['work_dir']
            or s['argv']!=c['argv'] or m['independent_exit_code']!=0 or m.get('stop_reason')
            or m.get('supervisor_error') or not m['inputs_unchanged']
            or m['inputs_sha256_after']!=s['inputs_sha256_before']
            or (record/'independent_exit_code.txt').read_text().strip()!='0'):
        raise ValueError('PROCESS_OR_INPUT_BINDING_FAILED')
    actual={str(p.relative_to(work)) for p in work.rglob('*') if p.is_file()}
    if actual!=set(m['work_files']):raise ValueError('WORK_INVENTORY_INCOMPLETE')
    for name,spec in m['work_files'].items():
        path=work/name
        if path.is_symlink() or not path.resolve().is_relative_to(work.resolve()) or hashlib.sha256(path.read_bytes()).hexdigest()!=spec['sha256']:
            raise ValueError('CAPTURED_FILE_CHANGED:'+name)
    system,meta=read_group(work/'system')
    raw,rawmeta=read_group(work/'solution')
    if m['kind']=='REAL_DIAGNOSTIC_UNVERIFIED':
        required={'mesh_coordinates_hat','mesh_triangles','algebraic_solution_before_backsub',
            'reconstructed_solution','velocity_dof_coordinates_hat','velocity_dof_components',
            'velocity_reconstructed_dof_indices','velocity_reconstructed_values',
            'pressure_coordinates_hat','pressure_reconstructed_dof_indices','wall_velocity_dof_indices',
            'pressure_area_weights_hat2','pressure_raw_P1','pressure_zero_mean_P1',
            'periodic_slave_dofs','periodic_master_dofs'}
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
    return dict(status='CAPTURE_BINDING_PASS',kind=m['kind'],all_work_files_hashed=len(actual))


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

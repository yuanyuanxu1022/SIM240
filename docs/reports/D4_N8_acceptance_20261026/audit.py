"""Read-only saved-data acceptance; no PDE imports, assembly, or solve."""
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
import hashlib
import json
import sys
import numpy as np

OUT=Path(__file__).resolve().parent
REPO=OUT.parents[2]
P=REPO/'CASE/D_series/D4_variable_groove_transport_20261023/reference_backend_min18_20261025/pilot_record_v3_1_20261026'
APP=REPO/'docs/reports/D4_N8_single_approval_20261026'
sys.path.insert(0,str(P))
import readback

def read(p):return readback.load_json(p)
def sha(p):return readback.file_sha(p)
def write(name,value):
    with (OUT/name).open('x') as f:json.dump(value,f,indent=2,sort_keys=True,allow_nan=False,ensure_ascii=False);f.write('\n')
def inventory(root):return {str(p.resolve()):sha(p) for p in root.rglob('*') if p.is_file()}

def main():
    c=read(APP/'APPROVED_DIAGNOSTIC_ONLY.json');r=Path(c['record_dir']);w=Path(c['work_dir']);a=r/'archive'
    before={**inventory(r),**inventory(w),**inventory(APP),**inventory(P)}
    historical=read(REPO/'docs/reports/G4_derivation_source_audit_20261025/protected_inputs.json')
    for name,h in historical.items():assert sha(REPO/name)==h,name
    lock=read(r/'source_lock.json')
    for name,h in lock['files'].items():assert sha(name)==h,name
    assert read(r/'contract.json')==c
    assert sha(r/'source_lock.json')==c['source_lock_sha256']
    started=read(r/'STARTED.json');capture=read(r/'capture_manifest.json')
    assert lock['files']==started['inputs_sha256_before']==capture['inputs_sha256_after']
    assert c['approval']['protocol_sha256']==sha(P/'DIAGNOSTIC_CONTRACT.md')
    old=read(REPO/'docs/reports/D4_N8_permission_review_20261026/candidate_contract_NOT_AUTHORIZED.json')
    assert {k for k in c if c[k]!=old[k]}=={'approval','authorized_to_execute','status'}
    archive_check=readback.check_archive(r)
    archived=readback.check(a,record=r)
    original=readback.check(w,record=r)
    assert archived==original
    assert archived['status']=='DIAGNOSTIC_READBACK_PASS'
    write('frozen_readback.json',archived)
    write('archive_check.json',archive_check)
    # Second arithmetic path: dense reconstruction from saved CSR; never solve.
    s,meta=readback.read_group(a/'system');f,_=readback.read_group(a/'solution')
    A=np.zeros(meta['matrix_shape'])
    rows=np.repeat(np.arange(A.shape[0]),np.diff(s['csr_indptr']))
    np.add.at(A,(rows,s['csr_indices']),s['csr_values'])
    x=f['algebraic_solution_before_backsub'];b=s['rhs_after'];b0=s['rhs_before'];n=s['pressure_null_vector']
    dense_res=float(np.linalg.norm(A@x-b)/np.linalg.norm(b))
    d=read(a/'solver_diagnostics.json');history=np.array(d['ksp_reported_residual_history'])
    assert len(history)==d['ksp_iterations']+1
    assert history[-1]/history[0]<=c['solver_settings']['ksp_rtol']
    assert history[-2]/history[0]>c['solver_settings']['ksp_rtol']
    assert dense_res<=1e-10 and abs(dense_res-archived['metrics']['true_residual_after_projection'])<=1e-12
    assert abs(dense_res-d['true_unpreconditioned_relative_residual'])<=1e-12
    assert np.linalg.norm(A@n)/np.linalg.norm(A)<=1e-10
    assert np.linalg.norm(A.T@n)/np.linalg.norm(A)<=1e-10
    assert abs(n@b0)/np.linalg.norm(b0)<=1e-10
    # Rebuild pressure area weights from saved cell maps, independent of writer.
    points=f['mesh_coordinates_hat'];tri=f['mesh_triangles'];v=points[tri]
    cross=(v[:,1,0]-v[:,0,0])*(v[:,2,1]-v[:,0,1])-(v[:,2,0]-v[:,0,0])*(v[:,1,1]-v[:,0,1])
    area=np.abs(cross)/2
    assert points.shape==(153,2) and tri.shape==(256,3)
    assert np.min(area)>0 and abs(area.sum()-2)<1e-12
    assert np.allclose(points.min(axis=0),[0,0],rtol=0,atol=1e-12)
    assert np.allclose(points.max(axis=0),[2,1],rtol=0,atol=1e-12)
    pm=f['pressure_reconstructed_dof_indices'];weights=np.zeros(len(x))
    np.add.at(weights,s['cell_pressure_mixed_dofs'].reshape(-1),np.repeat(area/3,3))
    assert np.max(np.abs(weights[pm]-f['pressure_area_weights_hat2']))<=1e-12
    rp=f['reconstructed_solution'];sl=f['periodic_slave_dofs'];ma=f['periodic_master_dofs']
    reconstructed=x.copy();reconstructed[sl]=x[ma]*f['periodic_coefficients']
    assert np.max(np.abs(rp-reconstructed))<=1e-10
    coords={int(i):xy for i,xy in zip(f['velocity_reconstructed_dof_indices'],f['velocity_dof_coordinates_hat'])}
    coords.update({int(i):xy for i,xy in zip(pm,f['pressure_coordinates_hat'])})
    assert len(sl)==len(ma)==39
    for slave,master in zip(sl,ma):
        assert np.allclose(coords[int(slave)]-coords[int(master)],[2,0],atol=1e-11,rtol=0)
    wall=f['wall_velocity_dof_indices']
    assert len(wall)>0
    for dof in wall:assert min(abs(coords[int(dof)][1]),abs(coords[int(dof)][1]-1))<=1e-11
    # All velocity DOFs on z=0/1 must be recorded as wall DOFs.
    expected_wall={int(i) for i,xy in zip(f['velocity_reconstructed_dof_indices'],f['velocity_dof_coordinates_hat']) if min(abs(xy[1]),abs(xy[1]-1))<=1e-11}
    assert set(wall)==expected_wall
    stats=capture['cgroup_stats'];events=dict(line.split() for line in stats['memory.events'].splitlines())
    assert int(stats['memory.peak'])<=c['resource_limits']['memory_bytes']
    assert all(int(events.get(k,0))==0 for k in ['oom','oom_kill','oom_group_kill','max'])
    assert dict(line.split() for line in stats['pids.events'].splitlines())['max']=='0'
    final_bytes=sum(info['bytes'] for info in capture['work_files'].values())
    assert final_bytes<=c['resource_limits']['output_bytes']
    assert not (Path(c['cgroup_parent'])/('sim240-'+c['run_id'])).exists()
    assert (APP/'launcher.exit_code.txt').read_text().strip()=='0'
    assert not (a/'stderr.log').read_text().strip()
    dense=dict(true_relative_residual=dense_res,
        residual_difference_from_record=abs(dense_res-d['true_unpreconditioned_relative_residual']),
        right_null_relative=float(np.linalg.norm(A@n)/np.linalg.norm(A)),
        left_null_relative=float(np.linalg.norm(A.T@n)/np.linalg.norm(A)),
        pressure_weight_max_abs_difference=float(np.max(np.abs(weights[pm]-f['pressure_area_weights_hat2']))),
        mesh_vertices=len(points),mesh_triangles=len(tri),mesh_total_area=float(area.sum()),
        periodic_pairs=len(sl),wall_dofs=len(wall),
        ksp_iterations=d['ksp_iterations'],ksp_reason=d['ksp_reason'],history_length=len(history),
        last_history_relative=float(history[-1]/history[0]),previous_history_relative=float(history[-2]/history[0]))
    write('independent_arithmetic.json',dense)
    after={p:sha(p) for p in before};assert before==after
    for name,h in historical.items():assert sha(REPO/name)==h,name
    assert not any(k.split('.')[0] in {'petsc4py','dolfinx','dolfinx_mpc','ufl','solver','assembly','worker'} for k in sys.modules)
    write('input_sha256.json',before)
    verdict=dict(status='ONE_N8_DIAGNOSTIC_ACCEPTED',checked_at_Asia_Shanghai=datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),
        run_id=c['run_id'],scope='single mixed MMS N8 algebraic/recording diagnostic only',
        frozen_readback=archived,archive_integrity=archive_check,independent_arithmetic=dense,
        source_lock_files=len(lock['files']),historical_protected_files=len(historical),
        audited_read_files=len(before),all_read_files_unchanged=True,historical_protection_unchanged=True,
        wall_seconds=capture['wall_seconds'],cgroup_memory_peak_bytes=int(stats['memory.peak']),
        direct_child_peak_RSS_KiB=capture['direct_child_peak_RSS_KiB'],
        sampled_tree_peak_RSS_bytes=capture['sampled_tree_peak_RSS_bytes'],
        final_archived_bytes=final_bytes,sampled_output_peak_bytes=capture['sampled_output_peak_bytes'],
        original_and_archive_checks_identical=True,PDE_backend_imported=False,solver_rerun=False,second_item_started=False,
        NUMERICAL_GATE='NOT_EVALUATED',RESULT_PASS=False,geometry_PASS=None,prediction_permission='HOLD',
        unassessed=['analytic L2 accuracy','flux and energy','grid convergence','remaining 17 items','groove reference','correlation predictions'])
    write('verdict.json',verdict)
    print(json.dumps(verdict,ensure_ascii=False,indent=2))

if __name__=='__main__':main()

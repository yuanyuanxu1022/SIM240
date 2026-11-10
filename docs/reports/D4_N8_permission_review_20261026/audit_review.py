"""Read-only technical permission review; never approve, assemble or solve."""
import ast
import copy
from datetime import datetime
from zoneinfo import ZoneInfo
import hashlib
from importlib import metadata
import json
import os
from pathlib import Path
import sys

OUT=Path(__file__).resolve().parent
REPO=OUT.parents[2]
ROOT=REPO/'CASE/D_series/D4_variable_groove_transport_20261023/reference_backend_min18_20261025'
P=ROOT/'pilot_record_v3_1_20261026'
V=REPO/'docs/reports/D4_volume_probe_20261026'
def read(p):return json.loads(p.read_text())
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
def write(p,d):
    with p.open('x') as f:json.dump(d,f,indent=2,sort_keys=True,ensure_ascii=False,allow_nan=False);f.write('\n')
def verify(items,base):
    bad=[str(base/p) for p,h in items.items() if not (base/p).is_file() or sha(base/p)!=h]
    assert not bad,bad
    return {'count':len(items),'mismatches':bad}

def main():
    evidence={'checked_at_Asia_Shanghai':datetime.now(ZoneInfo('Asia/Shanghai')).isoformat()}
    sys.path.insert(0,str(P))
    import common
    from resources import hard_output_volume,durable_record_volume,cgroup_parent_check
    lock=read(P/'source_lock.json')
    evidence['source_lock']=verify(lock['files'],REPO)
    evidence['protected_history']=verify(read(REPO/'docs/reports/G4_derivation_source_audit_20261025/protected_inputs.json'),REPO)
    evidence['prior_v3']=verify(read(REPO/'docs/reports/D4_pilot_v3_review_20261026/review_inputs_sha256.json'),REPO)
    evidence['volume_evidence']=verify(read(V/'evidence/mounted_final_integrity.json')['artifact_sha256'],V)
    evidence['package_evidence']=verify(read(P/'evidence/final_integrity.json')['artifact_sha256'],P)
    tests=read(P/'evidence/test_summary.json');old_tests=read(ROOT/'pilot_record_v3_20261026/evidence/test_summary.json')
    assert tests['tests']==12 and tests['failures']==tests['errors']==tests['skips']==0
    assert old_tests['tests']==32 and old_tests['failures']==old_tests['errors']==0 and not old_tests['skips']
    assert (P/'evidence/test_kind_no_solve.exit_code').read_text().strip()=='0'
    assert (ROOT/'pilot_record_v3_20261026/evidence/test_no_solve.exit_code').read_text().strip()=='0'
    evidence['existing_tests']={'targeted':12,'earlier_suite':32,'rerun':False}
    c=copy.deepcopy(read(P/'path_contract_draft.json'))
    c['run_id']='D4_N8_diag_v3_1_20261026_v1'
    c['work_dir']=str(Path(c['work_dir']).parent/c['run_id'])
    c['record_dir']=str(Path(c['record_dir']).parent/c['run_id'])
    c['argv']=common.expected_argv(c);c['environment']=common.expected_environment(c)
    common.validate(c,execution=False)
    assert c['status']=='DRAFT_NOT_AUTHORIZED' and c['approval'] is None and c['authorized_to_execute'] is False
    try:common.validate(c,execution=True)
    except common.Rejected as exc:evidence['execution_gate_rejection']=str(exc)
    else:raise AssertionError('Unapproved review packet unexpectedly executable')
    assert not Path(c['work_dir']).exists() and not Path(c['record_dir']).exists()
    assert not (Path(c['cgroup_parent'])/('sim240-'+c['run_id'])).exists()
    write(OUT/'candidate_contract_NOT_AUTHORIZED.json',c)
    evidence['candidate']={'proposed_run_id':c['run_id'],'actual_run_id':None,
        'work_dir':c['work_dir'],'record_dir':c['record_dir'],'output_paths_unused':True,
        'contract_sha256':common.digest(c),'contract_file_sha256':sha(OUT/'candidate_contract_NOT_AUTHORIZED.json')}
    volume=hard_output_volume(Path(c['work_dir']).parent,c['resource_limits']['output_bytes'])
    disk=durable_record_volume(Path(c['record_dir']).parent,Path(c['work_dir']).parent,c['resource_limits']['minimum_record_disk_bytes'])
    cgroup_parent_check(c['cgroup_parent'])
    mem=int(next(s.split()[1] for s in Path('/proc/meminfo').read_text().splitlines() if s.startswith('MemAvailable:')))*1024
    assert mem>=c['resource_limits']['minimum_available_memory_bytes']
    import importlib.util
    spec=importlib.util.spec_from_file_location('review_layout',P/'precheck_layout.py')
    layout=importlib.util.module_from_spec(spec);spec.loader.exec_module(layout)
    w,r=layout.inspect(Path(c['work_dir']).parent),layout.inspect(Path(c['record_dir']).parent)
    assert w['mode']=='0o700' and w['uid']==w['gid']==1000 and w['empty'] and 'noexec' not in w['mount']['options']
    assert r['mode']=='0o700' and r['uid']==r['gid']==1000
    evidence['live_resource_checks']={'work':w,'record':r,'hard_output_volume':volume,
        'durable_record_volume':disk,'MemAvailable_bytes':mem,'cgroup_parent':c['cgroup_parent'],
        'controllers':(Path(c['cgroup_parent'])/'cgroup.subtree_control').read_text().strip(),
        'child_group_created':False,'status':'READ_ONLY_TECHNICAL_PREREQUISITES_PASS'}
    versions={d.metadata['Name'].lower().replace('_','-'):d.version for d in metadata.distributions(path=[str(ROOT/'.backend/lib/python3.12/site-packages')])}
    expected={'fenics-dolfinx':'0.11.0','fenics-basix':'0.11.0','fenics-ffcx':'0.11.0','petsc4py':'3.25.6','dolfinx-mpc':'0.11.0','numpy':'2.5.4','mpi4py':'4.1.2'}
    actual={name:versions.get(name) for name in expected}
    assert actual==expected,actual
    evidence['backend_metadata_read_without_import']=actual
    ref=common.expected_system()
    assert ref['planned_id']==c['planned_id'] and ref['matrix_shape']==[1275,1275]
    assert ref['solver_called'] is False and ref['gauge_check']['right_and_transpose_nullspaces_attached'] is True
    assert ref['actual_mesh']['actual_triangles']==256 and ref['actual_mesh']['actual_vertices']==153
    assert c['physical_plan']==common.load_old_plan()
    evidence['bound_prior_preflight']={k:ref[k] for k in ('planned_id','matrix_shape','matrix_csr_sha256','rhs_sha256_before_projection','mesh_sha256','periodic_mapping_sha256','gauge_check')}
    modules={p.name:ast.parse(p.read_text()) for p in P.glob('*.py')}
    solves=[n.lineno for n in ast.walk(modules['solver.py']) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='solve']
    assert len(solves)==1
    evidence['static_solver_call_site']={'module':'solver.py','line':solves[0],'public_release_check_precedes_backend_import':True,'actually_called':False}
    evidence['syntax_modules']=len(modules)
    evidence['forbidden_backend_modules_loaded']=[k for k in sys.modules if k.split('.')[0] in {'petsc4py','dolfinx','dolfinx_mpc','ufl'}]
    assert not evidence['forbidden_backend_modules_loaded']
    evidence.update(technical_readiness='READY_FOR_USER_REVIEW_OF_ONE_BOUNDED_DIAGNOSTIC',
        authorized_to_execute=False,actual_run_id=None,real_solver_called=False,new_mesh_or_assembly=False,
        NUMERICAL_GATE='NOT_EVALUATED',RESULT_PASS=False,geometry_PASS=None,prediction_permission='HOLD')
    write(OUT/'audit_evidence.json',evidence)
    inputs=dict(lock['files'])
    for root in (P,V):
        for p in root.rglob('*'):
            if p.is_file() and '__pycache__' not in p.parts:inputs[str(p.resolve())]=sha(p)
    volume_records=read(V/'evidence/mounted_independent_verification.json')
    records=[Path(volume_records['controller_record'])]+[Path(a['record_dir']) for a in volume_records['archives']]
    for root in records:
        for p in root.rglob('*'):
            if p.is_file():inputs[str(p.resolve())]=sha(p)
    write(OUT/'review_inputs_sha256.json',inputs)
    write(OUT/'review_binding.json',{'kind':'REVIEW_BINDING_NOT_EXECUTION_RELEASE',
        'proposed_run_id':c['run_id'],'actual_run_id':None,'authorized_to_execute':False,
        'candidate_file_sha256':sha(OUT/'candidate_contract_NOT_AUTHORIZED.json'),
        'source_lock_sha256':sha(P/'source_lock.json'),'diagnostic_contract_sha256':sha(P/'DIAGNOSTIC_CONTRACT.md'),
        'review_inputs_sha256':sha(OUT/'review_inputs_sha256.json'),'review_input_count':len(inputs),
        'reference_matrix_sha256':ref['matrix_csr_sha256'],'reference_rhs_sha256':ref['rhs_sha256_before_projection']})
    print(json.dumps({k:evidence[k] for k in ('source_lock','protected_history','prior_v3','candidate','backend_metadata_read_without_import','technical_readiness','execution_gate_rejection')},indent=2))

if __name__=='__main__':main()

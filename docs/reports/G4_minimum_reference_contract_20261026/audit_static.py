"""Read existing documents/manifests only; no field loading or PDE calls."""
import ast
import csv
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import sys
from zoneinfo import ZoneInfo

OUT=Path(__file__).resolve().parent
REPO=OUT.parents[2]
B=REPO/'CASE/D_series/D4_variable_groove_transport_20261023/reference_backend_min18_20261025'
P=B/'pilot_record_v3_1_20261026'

def read(p):return json.loads(Path(p).read_text())
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for block in iter(lambda:f.read(1048576),b''):h.update(block)
    return h.hexdigest()
def write(name,obj):
    with (OUT/name).open('x') as f:json.dump(obj,f,indent=2,sort_keys=True,ensure_ascii=False,allow_nan=False);f.write('\n')
def rows(p):
    with Path(p).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

def main():
    source_names=[
        'AGENTS.md',
        'docs/reports/G4_paper_claims_minimum_validation_20261026/REPORT.md',
        'docs/reports/G4_paper_claims_minimum_validation_20261026/claims.json',
        'docs/reports/D4_reference_protocol_draft_20261025/REFERENCE_METHOD_DRAFT.md',
        'docs/reports/D4_reference_protocol_draft_20261025/geometry_coverage10.csv',
        'docs/reports/D4_reference_protocol_review_20261025/REPORT.md',
        'docs/reports/D4_reference_protocol_review_20261025/MINIMUM_SCOPE.md',
        'docs/reports/D4_reference_protocol_review_20261025/minimal_benchmark18.csv',
        'docs/reports/D4_reference_revision_review_20261025/REPORT.md',
        'docs/reports/D4_reference_terminal_review_20261026/REPORT.md',
        'docs/reports/D4_grid_narrow_fine4_acceptance_20261025/verdict.json',
        'docs/reports/D4_N8_acceptance_20261026/REPORT.md',
        'docs/reports/D4_N8_acceptance_20261026/verdict.json',
        'docs/reports/D4_N8_single_approval_20261026/APPROVED_DIAGNOSTIC_ONLY.json',
        'docs/reports/Correlation_selection_freeze_20261024/candidate_lock.json',
        'docs/reports/Correlation_selection_freeze_20261024/FREEZE_RULES.md',
    ]
    source_paths=[REPO/n for n in source_names]+[B/n for n in (
        'protocol/method_contract.json','protocol/benchmarks18.csv','src/contract.py','src/physics.py',
        'src/symbolic_forms.py','mesh_periodic_pressure_20261025/interface.py',
        'result_adapter_review_20261026/bridge.py',
        'pilot_record_v3_1_20261026/common.py','pilot_record_v3_1_20261026/assembly.py',
        'pilot_record_v3_1_20261026/worker.py','pilot_record_v3_1_20261026/readback.py',
        'pilot_record_v3_1_20261026/DIAGNOSTIC_CONTRACT.md','pilot_record_v3_1_20261026/source_lock.json')]
    hashes={str(p.resolve()):sha(p) for p in source_paths}
    lock=read(P/'source_lock.json')
    history=read(REPO/'docs/reports/G4_derivation_source_audit_20261025/protected_inputs.json')
    for name,h in lock['files'].items():assert sha(name)==h,name
    for name,h in history.items():assert sha(REPO/name)==h,name
    g4=read(REPO/source_names[14])
    freeze=REPO/'docs/reports/Correlation_selection_freeze_20261024'
    for name,h in g4['bound_files'].items():assert sha(freeze/name)==h,name;hashes[str((freeze/name).resolve())]=h
    c=read(REPO/source_names[13]);record=Path(c['record_dir']);archive=record/'archive'
    raw_hashes={str(p.resolve()):sha(p) for p in record.rglob('*') if p.is_file()}
    groups={name:read(archive/name/'manifest.json') for name in ('system','solution')}
    s=groups['system']['files'];f=groups['solution']['files']
    assert len(s)==8 and len(f)==17
    assert s['csr_indptr.npy']['shape']==[1276] and s['csr_values.npy']['shape']==[37277]
    assert s['cell_velocity_mixed_dofs.npy']['shape']==[256,12] and s['cell_pressure_mixed_dofs.npy']['shape']==[256,3]
    assert f['mesh_coordinates_hat.npy']['shape']==[153,2] and f['mesh_triangles.npy']['shape']==[256,3]
    accepted=read(REPO/source_names[12])
    assert accepted['status']=='ONE_N8_DIAGNOSTIC_ACCEPTED'
    assert accepted['frozen_readback']['field_accuracy_energy_flux']=='NOT_EVALUATED'
    capture=read(record/'capture_manifest.json')
    assert capture['archive_status']=='ARCHIVE_COMPLETE' and capture['independent_exit_code']==0
    assert len(capture['work_files'])==41
    # Bind exact observed source locations; absence claim is limited to these modules.
    code_evidence={}
    probes={
        P/'readback.py':['field_accuracy_energy_flux=','field_accuracy_energy_flux="NOT_EVALUATED"','def check_cell_maps','def check_required_records'],
        P/'common.py':['FIRST =','DIAGNOSTIC_RUN_NOT_AUTHORIZED'],
        P/'assembly.py':['def prepare_bound_mixed_system','MIXED_PRESSURE_CASE_REQUIRED'],
        P/'worker.py':['stage(work,\'ASSEMBLY\')','from solver import','arrays(work/\'solution\''],
        B/'mesh_periodic_pressure_20261025/interface.py':['def build_interface','mesh.create_rectangle'],
    }
    for path,needles in probes.items():
        lines=path.read_text().splitlines()
        code_evidence[str(path.relative_to(REPO))]=[{'line':i,'text':line.strip()} for i,line in enumerate(lines,1) if any(n in line for n in needles)]
        ast.parse(path.read_text())
    assert 'field_accuracy_energy_flux="NOT_EVALUATED"' in (P/'readback.py').read_text()
    method=read(B/'protocol/method_contract.json')
    assert 'MMS f is not ex' in method['energy_work']
    benchmarks=rows(B/'protocol/benchmarks18.csv')
    assert len(benchmarks)==18 and all(r['authorized_to_execute']=='False' and not r['actual_run_id'] for r in benchmarks)
    assert sha(B/'protocol/benchmarks18.csv')==sha(REPO/source_names[7])
    benchmark_state=[]
    for r in benchmarks:
        existing=r['planned_id']=='B0MIN_MMS_mixed_N8'
        benchmark_state.append(dict(planned_id=r['planned_id'],problem=r['problem'],field=r['direction_or_field'],role=r['role'],
            existing_diagnostic_run_id=c['run_id'] if existing else None,
            current_evidence='ALGEBRAIC_RECORD_CHAIN_ACCEPTED_FIELD_METRICS_PENDING' if existing else 'NO_ACCEPTED_REAL_SOLVE_IN_REVIEWED_RECORDS',
            future_execution_authorized=False))
    geometry=rows(REPO/source_names[4]);anchors=[r for r in geometry if r['geometry_id'] in ('G01','G02')]
    assert [(r['h_nm'],r['d_nm'],r['w_nm']) for r in anchors]==[('75','25','60'),('75','120','60')]
    write('static_inventory.json',dict(source_code_locations=code_evidence,N8_manifest_arrays={k:{n:v['shape'] for n,v in m['files'].items()} for k,m in groups.items()},
        reviewed_implementation_limit='Current rectangle interface and N8-only v3.1 worker/readback; other unreviewed code is not assumed absent',
        independent_field_extractor_qualified=False,field_arrays_loaded=False))
    write('benchmark_evidence18.json',dict(status='CANDIDATE_METHOD_QUALIFICATION_NOT_EXECUTION_RELEASE',items=benchmark_state,
        existing_diagnostic_count=1,pending_other_real_solve_evidence_count=17,all_full_method_acceptance_pending=True))
    gap_actions=[('R01','EXISTING_N8_DIAGNOSTIC_ACCEPTED','reuse existing evidence',False),
        ('R02','MISSING_L2_METRICS','independent saved-field extraction',False),
        ('R03','MISSING_FLUX_METRICS','independent saved-field extraction',False),
        ('R04','MISSING_ENERGY_DIVERGENCE_METRICS','independent saved-field extraction and criterion review',False),
        ('R05','EXTRACTOR_NOT_QUALIFIED','no-solve interpolation/integration fixtures',False),
        ('R06','OTHER_METHOD_BENCHMARKS_NOT_ACCEPTED','future separately authorized method solves',True),
        ('R07','ALG_QUAD_CONTROLS_NOT_ACCEPTED','future same-problem controls; offline quadrature is distinct',True),
        ('R08','GROOVE_CHAIN_NOT_QUALIFIED','new versioned implementation then separate solve authorization',True),
        ('R09','GROOVE_REFERENCE_DISCRETIZATION_UNRESOLVED','case-specific mesh/topology/control evidence',True),
        ('R10','ACCURACY_BUDGET_NOT_FROZEN','resolve estimate-vs-bound and quantity-specific criteria',False),
        ('R11','MODEL_STOP_COMPARISON_NOT_EVALUATED','additional studies only if corresponding comparison claim retained',None),
        ('R12','COVERAGE_RESOURCES_PERMISSION_NOT_APPROVED','new case-specific coverage and bounded resource contracts',False)]
    write('gaps.json',dict(status='GAP_REVIEW_ONLY',items=[dict(id=i,status=s,next_action=a,new_solve_needed_for_missing_evidence=n) for i,s,a,n in gap_actions]))
    draft=dict(contract_id='G4_REFERENCE_MINIMUM_EVIDENCE_20261026_DRAFT_v1',
        kind='SCIENTIFIC_VALIDATION_DRAFT_NOT_RUNNER_CONTRACT',status='DRAFT_NOT_APPROVED_NOT_EXECUTABLE',approval=None,
        solver_execution_authorized=False,offline_extraction_execution_authorized=False,
        current_task='Read-only gap review and draft only; no new numerical field extraction',
        reference_target='Case-specific finite-precision Stokes numerical reference with explicit uncertainty limitations',
        reference_qualified=False,strict_error_bound_established=False,NS_equivalence_validated=False,
        reuse_existing_run_id=c['run_id'],new_actual_run_id=None,
        first_next_stage=dict(id='S0_SAVED_N8_EXTRACTION_PREPARATION',new_solves=0,status='NOT_IMPLEMENTED_NOT_EXECUTED'),
        rectangle_scope=dict(total_slots=18,existing_real_diagnostic=1,other_future_solve_slots=17,
            per_item_execution_authorization_required=True,partial_N8_diagnostic_not_method_pass=True),
        first_groove_scope=dict(geometry_ids=['G01','G02'],geometry_h_d_w_nm=[[75,25,60],[75,120,60]],
            slots_per_geometry=dict(base_three_mesh_two_directions=6,finest_topology=2,finest_ALG=2,finest_QUAD=2),
            total_slots=24,actual_implementation_qualified=False,execution_authorized=False),
        conditional_planning_count=dict(rectangles_plus_first_grooves=42,existing_real_diagnostic=1,remaining_potential_slots=41,
            not_an_execution_plan=True,not_a_complete_project_minimum=True),
        pending_before_freeze=['F01_CONSERVATION_ENERGY_DIVERGENCE_APPLICABILITY','F02_EXTRACTOR_FIXTURE_QUADRATURE_TOLERANCES',
            'F03_QUANTITY_SPECIFIC_REFERENCE_BUDGET_RELIABILITY','F04_SCALAR_OTHER_MIXED_AND_GROOVE_IMPLEMENTATION',
            'F05_PER_ITEM_RESOURCES_AND_EXPLICIT_PERMISSION','F06_MODEL_STOP_AND_DOMAIN_SCOPE'],
        future_resource_limits=None,
        inherited_method_candidate_thresholds=method['candidate_thresholds_not_activated'],
        candidate_thresholds_activated=False,old_LBM_thresholds_changed=False,old_grid_FAIL_preserved=True,
        G4_model_lock_changed=False,NUMERICAL_GATE='NOT_EVALUATED',RESULT_PASS=False,geometry_PASS=None,prediction_permission='HOLD')
    write('contract_draft.json',draft)
    for name in ('GAP_REVIEW.md','REFERENCE_CONTRACT_DRAFT.md'):
        text=(OUT/name).read_text()
        for link in re.findall(r'\]\(([^)]+)\)',text):
            if not link.startswith('http'):assert (OUT/link).is_file(),link
        # Every table row must have the same number of unescaped pipes as its header.
        table_width=None
        for line in text.splitlines():
            if line.startswith('|'):
                width=len(re.findall(r'(?<!\\)\|',line))
                if table_width is None:table_width=width
                assert width==table_width,(name,line)
            else:table_width=None
    assert all(sha(p)==h for p,h in hashes.items()) and all(sha(p)==h for p,h in raw_hashes.items())
    for name,h in lock['files'].items():assert sha(name)==h,name
    for name,h in history.items():assert sha(REPO/name)==h,name
    assert not any(n.split('.')[0] in {'numpy','scipy','petsc4py','dolfinx','ufl','worker','solver','assembly'} for n in sys.modules)
    write('source_manifest.json',dict(files=hashes,N8_record_files=raw_hashes,
        human_scientific_approval='PENDING',AI_verification='Static code locations, manifest presence, file integrity and old record comparison only'))
    write('verification.json',dict(status='STATIC_DRAFT_AUDIT_PASS',checked_at_Asia_Shanghai=datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),
        source_files=len(hashes),N8_record_files=len(raw_hashes),production_source_lock_files=len(lock['files']),historical_protected_files=len(history),
        all_hashed_inputs_unchanged=True,old_G4_lock_bound_files=14,N8_system_array_files=8,N8_solution_array_files=17,
        gap_items=12,pre_freeze_blockers=6,benchmarks=18,existing_real_diagnostic=1,
        raw_arrays_loaded=False,new_field_metrics_computed=False,backend_imported=False,new_solver_run=False,new_fit=False,
        new_argv_created=False,new_resource_budget_approved=False,new_actual_run_id=None,
        frozen_thresholds_changed=False,reference_qualified=False,submission_ready=False))
    print('STATIC_DRAFT_AUDIT_PASS: 12 gaps, 6 freeze blockers, 18 candidate method slots, 24 explicitly counted first-groove slots; no arrays loaded or solver called.')

if __name__=='__main__':main()

"""Bind the working claim plan to existing records; never import a solver."""
import csv
import hashlib
import json
from pathlib import Path
import re
from datetime import datetime
from zoneinfo import ZoneInfo

OUT=Path(__file__).resolve().parent
REPO=OUT.parents[2]
FREEZE=REPO/'docs/reports/Correlation_selection_freeze_20261024'

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def rows(p):
    with Path(p).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def write(p,x):
    with Path(p).open('x') as f:json.dump(x,f,indent=2,ensure_ascii=False,sort_keys=True,allow_nan=False);f.write('\n')

def main():
    names=[
        'docs/reports/Correlation_selection_freeze_20261024/REPORT.md',
        'docs/reports/Correlation_selection_freeze_20261024/tradeoffs.csv',
        'docs/reports/Correlation_selection_freeze_20261024/FREEZE_RULES.md',
        'docs/reports/Correlation_selection_freeze_20261024/candidate_lock.json',
        'docs/reports/G4_derivation_source_audit_20261025/REPORT.md',
        'docs/reports/Constrained_correlation_20261023/data_roles.csv',
        'docs/reports/D4_grid_narrow_fine4_acceptance_20261025/REPORT.md',
        'docs/reports/D4_grid_narrow_fine4_acceptance_20261025/verdict.json',
        'docs/reports/D4_reference_revision_review_20261025/REPORT.md',
        'docs/reports/D4_reference_terminal_review_20261026/REPORT.md',
        'docs/reports/D4_N8_acceptance_20261026/REPORT.md',
        'docs/reports/D4_N8_acceptance_20261026/verdict.json',
        'docs/reports/SIM240_中文稿_导师审阅版_20261022.md',
        'CASE/D_series/D4_variable_groove_transport_20261023/reference_backend_min18_20261025/protocol/benchmarks18.csv',
    ]
    lock=read(FREEZE/'candidate_lock.json')
    sources={str((REPO/n).resolve()):sha(REPO/n) for n in names}
    for name,h in lock['bound_files'].items():
        p=FREEZE/name;assert sha(p)==h,name;sources[str(p.resolve())]=h
    assert len(lock['bound_files'])==14 and lock['status']=='CANDIDATE_FROZEN_NOT_VALIDATED'
    assert lock['target_domain']['accuracy_validated'] is False
    assert lock['evaluation']['MAE_percent_limit']==3.0 and lock['evaluation']['max_abs_percent_limit']==5.0
    development=[r for r in rows(REPO/names[5]) if r['role']=='development']
    assert len(development)==30
    geoms={tuple(float(r[k]) for k in ('h','d','w')) for r in development}
    assert len(geoms)==15
    assert {x[0] for x in geoms}=={50,75,125} and {x[1] for x in geoms}=={25,50,75,100,120}
    assert all(abs(x[2]-120)<1e-9 for x in geoms)
    predictions=[r for r in rows(FREEZE/'reserved_anisotropy.csv') if r['model']=='G4']
    pg={tuple(int(r[k]) for k in ('h_nm','d_nm','w_nm')) for r in predictions}
    assert len(pg)==len(predictions)==8
    assert {x[0] for x in pg}=={60,100} and {x[1] for x in pg}=={40,80} and {x[2] for x in pg}=={90,180}
    metrics=[r for r in rows(FREEZE/'tradeoffs.csv') if r['model']=='G4']
    assert len(metrics)==6 and all(int(r['n'])==15 for r in metrics)
    assert all(float(r['MAE_percent'])<=3 for r in metrics)
    assert all(float(r['max_abs_percent'])>5 for r in metrics if r['quantity']=='A')
    assert all(float(r['max_abs_percent'])<5 for r in metrics if r['quantity']!='A')
    grid=read(REPO/'docs/reports/D4_grid_narrow_fine4_acceptance_20261025/verdict.json')
    n8=read(REPO/'docs/reports/D4_N8_acceptance_20261026/verdict.json')
    assert grid['narrow_three_grid_sensitivity_gate']=='FAIL' and grid['prediction_execution_released'] is False
    assert n8['status']=='ONE_N8_DIAGNOSTIC_ACCEPTED' and n8['NUMERICAL_GATE']=='NOT_EVALUATED'
    text=(OUT/'REPORT.md').read_text()
    local_links=[]
    for target in re.findall(r'\]\(([^)]+)\)',text):
        if target.startswith('http'):continue
        p=(OUT/target).resolve();assert p.is_file(),target;local_links.append(target)
    assert '0.8≤s≤3.2' in text and '1/3≤t≤1.6' in text
    assert all(key in text for key in ('C01','C02','C03','C04','C05','C06','V0','V1','V2','V3'))
    assert all(sha(p)==h for p,h in sources.items())
    claims=[
        dict(id='C01',status='CONSTRUCTION_RETAINED_FINAL_PROOF_REVIEW_PENDING',evidence=['E1','E2'],wording='有物理约束的四参数经验关系式',minimum_action='Review assumptions and algebra against frozen implementation; no new flow run'),
        dict(id='C02',status='EXISTING_DISCRETE_REFERENCE_CV_ONLY',evidence=['E1','E2'],wording='相对于旧5nm参考的留组偏差',minimum_action='Read-only reconcile folds, source IDs, denominators, P/T/A and worst cases'),
        dict(id='C03',status='PROSPECTIVE_NOT_VALIDATED',evidence=['E3','E4'],wording='仅在冻结8几何测试通过后声称这些测试点达到目标',minimum_action='After valid reference/prerequisites and separate permission: frozen 16 main directions plus 4 refinement references; score 8 A values'),
        dict(id='C04',status='CONTINUOUS_ACCURACY_UNSUPPORTED',evidence=['E4','E5','E6'],wording='不承诺连续解3%/5%精度',minimum_action='Versioned reference qualification and quantity-specific error evidence; no fixed run count certified'),
        dict(id='C05',status='ALGEBRAIC_CONVERSION_ONLY',evidence=['E2','E5'],wording='阻力/修正/各向异性按一致定义单列',minimum_action='Check units and reciprocal/ratio error transformations; no new flow run'),
        dict(id='C06',status='EXCLUDED_FROM_PAPER_ACCURACY_CLAIM',evidence=['E1','E2','E3'],wording='不承诺全域、任意占比或真实工艺统一精度',minimum_action='Delete or bound unsupported generalizations, preserve limits'),
    ]
    write(OUT/'claims.json',dict(status='AUTHOR_WORKING_CLAIM_PLAN_NOT_FINAL_FREEZE',claims=claims,
        requested_model_version='G4_candidate_prediction_v1_20261024',solver_execution_authorized=False,
        original_thresholds=dict(P_T_A_each_MAE_percent=3,P_T_A_each_max_abs_percent=5),
        test_geometry_count=8,main_direction_count=16,refinement_direction_count=4,
        analytic_or_continuous_accuracy_bound_claimed=False,uniform_domain_accuracy_claimed=False))
    write(OUT/'source_manifest.json',dict(kind='LOCAL_SOURCE_BINDING_NOT_NEW_PHYSICAL_VERIFICATION',
        files=sources,human_verification='PENDING',ai_check='File identities and existing-record consistency only'))
    write(OUT/'verification.json',dict(status='STATIC_PLAN_CONSISTENCY_PASS',
        checked_at_Asia_Shanghai=datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),
        frozen_bound_files=14,source_files=len(sources),source_files_unchanged=True,
        local_links_checked=len(local_links),training_geometry_count=15,training_direction_count=30,
        existing_CV_rows_checked=6,existing_CV_P_T_max_below_5=True,existing_CV_A_max_above_5=True,
        planned_test_geometries=8,frozen_model_unchanged=True,thresholds_unchanged=True,
        old_grid_FAIL_preserved=True,new_solver_run=False,new_fit=False,new_prediction_evaluation=False,
        formal_Gate_changed=False,submission_ready=False,actual_new_run_id=None,
        limits=['No fresh proof review','No new raw-field acceptance','No reserved flow results read','No numerical reference selected or approved']))
    print('STATIC_PLAN_CONSISTENCY_PASS: source bindings, 14 locked artifacts, 6 existing CV rows, roles, test set and report links checked; no solver or fit.')

if __name__=='__main__':main()

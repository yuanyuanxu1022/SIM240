"""Scalar audit of the proposed bound closure; no solver, fit, or held-out result reads."""
from pathlib import Path
import csv
import hashlib
import json
import math
from collections import Counter

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
protected = {}


def bind(p):
    p = p.resolve()
    key = str(p.relative_to(ROOT))
    h = hashlib.sha256(p.read_bytes()).hexdigest()
    if key in protected:
        assert protected[key] == h
    protected[key] = h
    return p


def kv(p):
    return dict(line.split('=', 1) for line in bind(p).read_text().splitlines() if '=' in line)


def rows(p):
    with bind(p).open(encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))


def write_csv(name, data):
    with (OUT/name).open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(data[0]))
        writer.writeheader(); writer.writerows(data)


def close(a, b):
    return abs(a-b) <= 2e-12*max(abs(a),abs(b),1e-100)


def geometry(h,d,w):
    return tuple(round(x,7) for x in (h,d,w))


source = ROOT/'docs/reports/PAPER1_闭环方案_20261105'
bind(source/'REPORT.md')
table = rows(source/'bound_check_44_points.csv')
assert len(table) == 44
verified = []
for r in table:
    p = ROOT/r['raw_path']
    raw = kv(p)
    manifest = kv(p.parent/'run_manifest.txt')
    code = int(bind(p.parent/'exit_code.txt').read_text())
    h,d,w,dx = (float(raw[k])*1e9 for k in ['mesa_gap_m','groove_depth_m','groove_width_m','dx_m'])
    direction = raw['direction']
    assert direction == r['direction'] and close(dx,float(r['dx_nm']))
    assert all(close(a,float(r[k])) for a,k in [(h,'h_nm'),(d,'d_nm'),(w,'w_nm')])
    hm,dm = h*1e-9,d*1e-9
    bound = ((hm+dm)**3+hm**3)/24 if direction == 'parallel' else hm**3*(hm+dm)**3/(6*(hm**3+(hm+dm)**3))
    k = float(raw['Keff_m3'])
    # Some old schemas omit physical nu; reconstruct it from stored converter fields.
    nu = (float(raw['tau'])-.5)*float(raw['dx_m'])**2/(3*float(raw['dt_s']))
    if 'nu_phys_m2_s' in raw:
        assert close(nu,float(raw['nu_phys_m2_s']))
    assert close(nu,1e-6)
    kfromj = nu*float(raw['J_main_m2_s'])/float(raw['acceleration_m_s2'])
    assert close(k,kfromj) and close(k,float(r['K_reference_m3'])) and close(bound,float(r['K_bound_m3']))
    e = 100*(bound/k-1)
    assert abs(e-float(r['bias_percent'])) < 1e-10
    assert code == 0 and raw['PASS'] == 'true' and raw['converged'] == 'true'
    verified.append({'run_id':r['run_id'],'h_nm':h,'d_nm':d,'w_nm':w,'dx_nm':dx,
        'component':'Kyy' if direction=='parallel' else 'Kxx', 'K_LC_m3':bound,'K_discrete_m3':k,
        'bias_percent_LC_over_discrete':e,'discrete_below_LC':k<bound,
        'raw_exit':code,'saved_PASS':raw['PASS'],'binary_sha256':manifest['binary_sha256'],
        'source':str(p.relative_to(ROOT))})
write_csv('bound_records44_recomputed.csv',verified)

paired = []
for h,d,w in sorted({geometry(r['h_nm'],r['d_nm'],r['w_nm']) for r in verified if close(r['dx_nm'],2.5)}):
    for component in ['Kxx','Kyy']:
        pair = [r for r in verified if geometry(r['h_nm'],r['d_nm'],r['w_nm']) == (h,d,w) and r['component']==component]
        assert len(pair)==2
        coarse = next(r for r in pair if close(r['dx_nm'],5))
        fine = next(r for r in pair if close(r['dx_nm'],2.5))
        paired.append({'h_nm':h,'d_nm':d,'w_nm':w,'component':component,
            'K5_m3':coarse['K_discrete_m3'],'K2p5_m3':fine['K_discrete_m3'],
            'change_percent_over_coarse':100*(fine['K_discrete_m3']/coarse['K_discrete_m3']-1),
            'coarse_minus_fine_percent_over_fine':100*(coarse['K_discrete_m3']/fine['K_discrete_m3']-1),
            'both_discrete_below_bound':coarse['discrete_below_LC'] and fine['discrete_below_LC']})
write_csv('existing_refinement_pairs8.csv',paired)

# The smooth case is a controlled example of positive discrete error above an exact bound.
smooth = []
for direction in ['P','T']:
    run = f'URV_S1_{direction}_A1_v1_20261102_01'
    p = ROOT/f'CASE/unseen_v2_reference_S1_a1_v1/runs/{run}/steady/result.txt'
    raw = kv(p)
    acceptance = json.loads(bind(ROOT/f'CASE/unseen_v2_reference_S1_a1_v1/analysis_results/{run}/acceptance.json').read_text())
    assert acceptance['RESULT_PASS'] and acceptance['geometry_PASS']
    flat = float(raw['mesa_gap_m'])**3/12
    k = float(raw['Keff_m3'])
    assert close(k,acceptance['scalar']['K_m3'])
    smooth.append({'run_id':run,'K_flat_exact_m3':flat,'K_discrete_m3':k,
        'discrete_above_exact_bound':k>flat,'positive_discrete_error_percent':100*(k/flat-1),
        'saved_RESULT_PASS':True})
write_csv('smooth_equality_control2.csv',smooth)

# Read completed S4 scalars only; original acceptance is retained from its existing review.
s4 = []
for direction in ['P','T']:
    values = {}
    for dx,tag in [(5.,'5'),(2.5,'2p5'),(1.25,'1p25')]:
        run = f'URV_S4_{direction}_dx{tag}_reuse_v1_20261103_01'
        raw = kv(ROOT/f'CASE/unseen_v2_reference_S4_reuse_v1/runs/{run}/steady/result.txt')
        assert close(float(raw['mesa_gap_m'])*1e9,30)
        assert close(float(raw['groove_depth_m'])*1e9,80)
        values[dx] = float(raw['Keff_m3'])
    delta = abs(values[2.5]/values[1.25]-1)
    order = math.log(abs((values[5]-values[2.5])/(values[2.5]-values[1.25])),2)
    gci = 1.25*delta/(2**order-1)
    s4.append({'component':'Kyy' if direction=='P' else 'Kxx','h_nm':30,'d_nm':80,
        'K5_m3':values[5.],'K2p5_m3':values[2.5],'K1p25_m3':values[1.25],
        'medium_fine_change_percent':100*delta,'fine_GCI_percent':100*gci,'observed_order':order,
        'both_original_grid_conditions_pass':delta<=.01 and gci<=.01})
write_csv('S4_grid_recomputed.csv',s4)

# These are the user's proposed geometries, not new simulations or newly adopted predictions.
proposals = []
for label,h,d in [('A',100.,100.),('B',100.,50.),('C',37.5,100.),('D',150.,100.)]:
    w,P,dx = 120.,240.,5.
    hm,dm = h*1e-9,d*1e-9
    kx = hm**3*(hm+dm)**3/(6*(hm**3+(hm+dm)**3)) / (1+.4900*(d/w)**.6990)
    ky = ((hm+dm)**3+hm**3)/24/(1+1.7685*(d/w)**1.6331)
    volume_nodes = (P/dx)**2*((h+d/2)/dx)
    proposals.append({'label':label,'h_nm':h,'d_nm':d,'w_nm':w,'P_nm':P,'dx_nm':dx,
        'Kxx_V2_m3':kx,'Kyy_V2_m3':ky,'A_V2':ky/kx,'volume_over_dx_cubed':volume_nodes,
        'fluid_nodes_interpretation':'analytic expected count only if geometry discretization matches',
        'actual_native_geometry_checked':False,'elapsed_runtime_established':False,
        'execution_authorized':False,'formal_prediction_lock_created_this_audit':False})
write_csv('proposed_geometry_scalar_checks.csv',proposals)

sources = [
 'docs/reports/Appendix_E_final_review_20261028/REPORT.md',
 'docs/reports/Appendix_E_final_review_20261028/ASTRA_REVIEW.md',
 'docs/reports/Appendix_E_final_review_20261028/review_receipt.json',
 'docs/reports/Paper_bounded_candidate_20261027/THEORY_APPENDIX_CANDIDATE.md',
 'docs/reports/SIM240_EJMB_中文重写稿_v2_20261019.md',
 'docs/reports/SIM240_中文稿_导师审阅版_20261022.md',
 'docs/reports/PAPER1_formula_comparison_20261105/REPORT.md',
 'docs/reports/PAPER1_gap_candidate_review_20261105/REPORT.md',
 'docs/reports/PAPER1_h25_reference_candidate_audit_20261104_225645/known_candidate_point_review.json',
 'docs/reports/Correlation_selection_freeze_20261024/candidate_lock.json',
 'docs/reports/Correlation_selection_freeze_20261024/FREEZE_RULES.md',
 'docs/reports/URV_S1_results_review_20261102/REPORT.md',
 'docs/reports/URV_S4_completed_review_20261104_143205/REPORT.md',
 'CASE/D_series/D2_groove_error_map/scripts/run_d75_validation.sh',
 'CASE/D_series/D2_groove_error_map/analysis_fit_v2.py',
 'CASE/D_series/D2_groove_error_map/results/analysis/V2_FIT_REPORT.md',
 'docs/reports/SIM240_Supplementary_Methods_20261024/Table_S2_refinement.csv']
for name in sources:
    bind(ROOT/name)
min_point = min(verified,key=lambda r:r['bias_percent_LC_over_discrete'])
summary = {'audit_scope':'bounded_paper_claim_review_not_new_theory_freeze',
    'record_count':len(verified),'unique_geometries':len({geometry(r['h_nm'],r['d_nm'],r['w_nm']) for r in verified}),
    'unique_geometry_direction_conditions':len({(*geometry(r['h_nm'],r['d_nm'],r['w_nm']),r['component']) for r in verified}),
    'direction_counts':dict(Counter(r['component'] for r in verified)),
    'records_below_bound':sum(r['discrete_below_LC'] for r in verified),
    'bias_min_percent':min(r['bias_percent_LC_over_discrete'] for r in verified),
    'bias_max_percent':max(r['bias_percent_LC_over_discrete'] for r in verified),
    'minimum_bias_record':min_point,
    'refined_geometry_count':len(paired)//2,
    'maximum_observed_paired_change_percent_over_coarse':max(abs(r['change_percent_over_coarse']) for r in paired),
    'S4_T_medium_fine_percent':s4[1]['medium_fine_change_percent'],
    'minimum_margin_divided_by_S4_change_arithmetic_only':min_point['bias_percent_LC_over_discrete']/s4[1]['medium_fine_change_percent'],
    'ratio_is_sign_robustness_certificate':False,
    'strict_error_bound_established':False,'new_simulation_run_id':None,'solver_calls':0,'fit_calls':0,
    'reserved_flow_results_read':False,'new_prediction_lock_created':False,
    'formal_model_comparison_changed':False,'scientific_gate_advanced':False}
(OUT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
(OUT/'source_manifest.json').write_text(json.dumps(protected,ensure_ascii=False,indent=2)+'\n')
changed = [p for p,h in protected.items() if hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=h]
assert not changed
(OUT/'verification.json').write_text(json.dumps({'protected_inputs':len(protected),'changed_inputs':changed,
    'raw_bounds_recomputed':44,'raw_J_K_identity_checked':44,'smooth_raw_records_checked':2,
    'S4_raw_records_checked':6,'new_solver_runs':0,'new_fits':0,'reserved_flow_results_read':False,
    'initial_attempt':'KeyError on legacy missing nu_phys_m2_s; corrected by reconstructing nu from stored tau/dx/dt without changing inputs'},ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in summary.items() if k!='minimum_bias_record'},ensure_ascii=False))

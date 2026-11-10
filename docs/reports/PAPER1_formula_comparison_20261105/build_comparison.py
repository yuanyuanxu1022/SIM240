"""Read-only scalar recomputation; no solver, fitter, VTK, or reserved predictions."""
from pathlib import Path
import csv
import hashlib
import json
import math
import statistics

ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
protected={}


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def bind(p):
    protected[str(p.relative_to(ROOT))]=sha(p)
    return p


def rows(p):
    with bind(p).open() as f:
        return list(csv.DictReader(f))


def kv(p):
    return dict(line.split('=',1) for line in bind(p).read_text().splitlines() if '=' in line)


def write_csv(name,data):
    with (OUT/name).open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader();w.writerows(data)


def same(a,b,rtol=1e-12):
    return abs(a-b)<=rtol*max(abs(a),abs(b))


screen=rows(ROOT/'docs/reports/PAPER1_formula_scope_discussion_20261105/screened_36_points.csv')
index={r['run_id']:r for r in rows(ROOT/'docs/reports/SIM240_Supplementary_Methods_20261024/Table_S1_run_inventory.csv')}
comparison=[]
for row in screen:
    name=row['run_id'];entry=index[name]
    result_path=ROOT/entry['result_path'] if 'result_path' in entry else ROOT/entry['result_file']
    result=kv(result_path)
    manifest=kv(result_path.parent/'run_manifest.txt')
    precheck=kv(result_path.parent.parent/'precheck/boundary_audit.txt')
    exit_path=result_path.parent/'exit_code.txt'
    assert int(bind(exit_path).read_text())==0
    h=float(row['h_nm']);d=float(row['d_nm']);dr=row['direction']
    assert same(float(result['mesa_gap_m'])*1e9,h) and same(float(result['groove_depth_m'])*1e9,d)
    assert same(float(result['dx_m']),5e-9) and result['direction']==dr
    assert same(float(result['groove_width_m']),120e-9)
    assert same(float(result['Lx_m']),240e-9) and same(float(result['Ly_m']),240e-9)
    assert result['periodicity']=='x_y' and float(result['acceleration_m_s2'])==1e5
    assert float(result['tau'])==1 and result['collision']=='ForcedBGK'
    assert result['PASS']=='true' and result['converged']=='true'
    assert precheck['geometry_PASS']=='true' and precheck['q_audit_PASS']=='true'
    kh=h*1e-9;kd=d*1e-9
    if dr=='parallel':
        component='Kyy';old=((kh+kd)**3+kh**3)/24
        factor=1/(1+1.7685*(d/120)**1.6331)
    else:
        component='Kxx';old=(kh+kd)**3*kh**3/(6*((kh+kd)**3+kh**3))
        factor=1/(1+.4900*(d/120)**.6990)
    lb=float(result['Keff_m3']);corrected=old*factor
    assert same(lb,float(row['K_ref_m3'])) and same(lb,float(entry['K_m3']))
    assert same(old,float(row['K_model_m3'])) and same(factor,float(row['F_V2_published']))
    assert manifest['binary_sha256']==row['binary_sha256']==entry['binary_sha256']
    e0=100*(old/lb-1);e2=100*(corrected/lb-1)
    assert abs(e0-float(row['E_percent']))<1e-10
    assert abs(e2-float(row['V2_residual_percent']))<1e-10
    comparison.append({'run_id':name,'h_nm':h,'d_nm':d,'w_nm':120,'P_nm':240,
        'h_over_w':h/120,'d_over_w':d/120,'direction':dr,'component':component,
        'OpenLB_dx5_K_m3':lb,'original_K_m3':old,'V2_factor_published':factor,
        'V2_K_m3':corrected,'original_bias_percent':e0,'V2_bias_percent':e2,
        'abs_bias_reduction_percentage_points':abs(e0)-abs(e2),
        'absolute_bias_improved':abs(e2)<abs(e0),
        'binary_sha256':manifest['binary_sha256'],'saved_PASS':result['PASS'],
        'saved_geometry_PASS':precheck['geometry_PASS'],'raw_result_path':str(result_path.relative_to(ROOT)),
        'evidence_scope':'retrospective_vs_dx5_discrete_results'})
assert len(comparison)==36
comparison.sort(key=lambda r:(r['h_nm'],r['d_nm'],r['component']))
write_csv('comparison_36_points.csv',comparison)
pairs=[]
for h,d in sorted({(r['h_nm'],r['d_nm']) for r in comparison}):
    pair={r['component']:r for r in comparison if r['h_nm']==h and r['d_nm']==d}
    assert set(pair)=={'Kxx','Kyy'}
    flat={'h_nm':h,'d_nm':d}
    for key in ('Kxx','Kyy'):
        for col in ('OpenLB_dx5_K_m3','original_K_m3','V2_K_m3','original_bias_percent','V2_bias_percent'):
            flat[key+'_'+col]=pair[key][col]
    flat['A_OpenLB_dx5']=pair['Kyy']['OpenLB_dx5_K_m3']/pair['Kxx']['OpenLB_dx5_K_m3']
    flat['A_original']=pair['Kyy']['original_K_m3']/pair['Kxx']['original_K_m3']
    flat['A_V2']=pair['Kyy']['V2_K_m3']/pair['Kxx']['V2_K_m3']
    pairs.append(flat)
write_csv('paired_18_geometries.csv',pairs)
stats=[]
for label,subset in [('all18',comparison),('h_ge_50',[r for r in comparison if r['h_nm']>=50])]:
    for key in ('Kxx','Kyy'):
        group=[r for r in subset if r['component']==key]
        a=[r['original_bias_percent'] for r in group];b=[r['V2_bias_percent'] for r in group]
        stats.append({'scope':label,'component':key,'direction_point_count':len(group),
          'original_bias_min_percent':min(a),'original_bias_max_percent':max(a),
          'V2_bias_min_percent':min(b),'V2_bias_max_percent':max(b),
          'original_max_abs_percent':max(map(abs,a)),'V2_max_abs_percent':max(map(abs,b)),
          'original_mean_abs_percent':statistics.mean(map(abs,a)),
          'V2_mean_abs_percent':statistics.mean(map(abs,b)),
          'improved_count':sum(r['absolute_bias_improved'] for r in group),
          'worse_count':sum(not r['absolute_bias_improved'] for r in group)})
write_csv('direction_summary.csv',stats)
byh=[]
for h in sorted({r['h_nm'] for r in comparison}):
    for key in ('Kxx','Kyy'):
        g=[r for r in comparison if r['h_nm']==h and r['component']==key]
        byh.append({'h_nm':h,'component':key,'count':len(g),
                    'V2_bias_min_percent':min(r['V2_bias_percent'] for r in g),
                    'V2_bias_max_percent':max(r['V2_bias_percent'] for r in g),
                    'V2_max_abs_percent':max(abs(r['V2_bias_percent']) for r in g)})
write_csv('by_gap_summary.csv',byh)

# Existing static OpenFOAM cases: inspect original acceptance identity and hashes,
# recompute saved outlet Q only. Never call the old checker or a CFD executable.
specs=[('C01','interface_static_darcy_v1','SDI_C01_v1_20261030_01','V2','Kxx'),
       ('C02','interface_static_darcy_v1_1','SDI_C02_v1_1_20261030_01','V2','Kyy'),
       ('C03','interface_static_darcy_v1_2','SDI_C03_v1_2_20261030_01','original','Kxx'),
       ('C04','interface_static_darcy_v1_3','SDI_C04_v1_3_20261030_01','original','Kyy'),
       ('GDI01','groove_darcy_static_v1','GDI01_v1_20261030_01','V2','Kxx')]
of_cases=[];of_q=[];raw_count=0
old_q=rows(ROOT/'docs/reports/OpenFOAM_comparison_clarification_20261104/case_results.csv')
for cid,package,name,model,key in specs:
    base=ROOT/'CASE'/package/'runs'/name
    report=ROOT/'docs/reports'/((cid if cid=='GDI01' else 'SDI_'+cid)+'_results_20261030')
    ap=report/('interface_analysis_geometry_v1_1.json' if cid=='C01' else 'interface_analysis.json')
    accepted=json.loads(bind(ap).read_text())
    execution=json.loads(bind(base/'execution.json').read_text())
    assert accepted['run_id']==execution['run_id']==name
    assert execution['status']=='completed'
    assert all(s['exit_code']==0 and not s['timed_out'] for s in execution['steps'])
    assert accepted['NUMERICAL_GATE']=='PASS' and accepted['RESULT_PASS'] and accepted['geometry_PASS']
    for entry in accepted['raw_files']:
        actual=sha(bind(base/entry['path']))
        assert actual==entry['sha256']
        raw_count+=1
    assert sha(bind(base/'run_manifest.json'))==accepted['run_manifest_sha256']
    case={'case_id':cid,'run_id':name,'model':model,'physical_component_in_groove_coordinates':key,
           'saved_NUMERICAL_GATE':accepted['NUMERICAL_GATE'],'saved_RESULT_PASS':accepted['RESULT_PASS'],
           'saved_geometry_PASS':accepted['geometry_PASS'],'geometry_scope':accepted['geometry_scope'],
           'physical_validation':accepted['physical_validation'],'accepted_source':str(ap.relative_to(ROOT))}
    of_cases.append(case)
    for endpoint in (['openfoam'] if cid=='GDI01' else ['two_dimensional','openfoam']):
        sub='openfoam/GDI_output' if cid=='GDI01' else ('openfoam/SDI_output' if endpoint=='openfoam' else 'two_dimensional')
        faces=rows(base/sub/'faces.csv')
        q=math.fsum(float(r['phi_m3_s']) for r in faces if r['patch']=='xHigh')
        old=next(r for r in old_q if r['case_id']==cid and r['endpoint']==endpoint)
        assert same(q,float(old['Q_m3_s']))
        of_q.append({**case,'endpoint':endpoint,'Q_m3_s':q})
write_csv('OpenFOAM_saved_cases.csv',of_cases)
write_csv('OpenFOAM_outlet_Q.csv',of_q)
of_stats={}
for key,a,b in [('Kxx','C01','C03'),('Kyy','C02','C04')]:
    qa=next(r['Q_m3_s'] for r in of_q if r['case_id']==a and r['endpoint']=='openfoam')
    qb=next(r['Q_m3_s'] for r in of_q if r['case_id']==b and r['endpoint']=='openfoam')
    of_stats[key]={'V2_to_original_Q_ratio':qa/qb,'Q_change_percent':100*(qa/qb-1)}
reports=[
 'URV_A1_S0_results_review_20261102/REPORT.md',
 'URV_S1_results_review_20261102/REPORT.md',
 'URV_S2_completed_review_20261103_095422/REPORT.md',
 'URV_S3_completed_review_20261103_172033/REPORT.md',
 'URV_S4_completed_review_20261104_143205/REPORT.md',
 'OpenFOAM_comparison_clarification_20261104/REPORT.md',
 'Historical_build_adjudication_20261028/REPORT.md',
 'PAPER1_h25_reference_candidate_audit_20261104_225645/REPORT.md']
for name in reports:
    bind(ROOT/'docs/reports'/name)
bind(ROOT/'docs/reports/SIM240_中文稿_导师审阅版_20261022.md')
bind(ROOT/'CASE/interface_static_darcy_v1/common/PROTOCOL.md')
summary={'date':'2026-11-05','direction_stats':stats,'gap_stats':byh,
         'worse_points':[r for r in comparison if not r['absolute_bias_improved']],
         'OpenFOAM_input_effect':of_stats,'OpenFOAM_raw_entries_hash_checked':raw_count,
         'scope':'retrospective_vs_original_dx5_OpenLB_results_with_saved_application_checks',
         'formal_MODEL_COMPARISON_status_changed':False,'solver_runs':0,'fit_calls':0,
         'field_array_reads':0,'reserved_predictions_read':False}
(OUT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
(OUT/'source_manifest.json').write_text(json.dumps(protected,ensure_ascii=False,indent=2)+'\n')
changed=[p for p,h in protected.items() if sha(ROOT/p)!=h]
verification={'raw_comparison_rows':36,'paired_geometries':18,
              'direction_counts':{key:sum(r['component']==key for r in comparison) for key in ('Kxx','Kyy')},
              'formulas_match_preexisting_table':True,'raw_results_and_saved_exits_match':True,
              'OpenFOAM_cases':len(of_cases),'OpenFOAM_raw_entries_verified':raw_count,
              'OpenFOAM_outlet_rows':len(of_q),'protected_inputs':len(protected),
              'changed_inputs':changed,'new_simulation_run_id':None,
              'formal_reacceptance':False,'new_fit':False,'independent_prediction_validation':False}
(OUT/'verification.json').write_text(json.dumps(verification,ensure_ascii=False,indent=2)+'\n')
assert not changed
print(json.dumps({'stats':stats,'worse_points':[(r['run_id'],r['original_bias_percent'],r['V2_bias_percent']) for r in summary['worse_points']],
                  'OpenFOAM':of_stats,'verification':verification},ensure_ascii=False))

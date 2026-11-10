#!/usr/bin/env python3
"""Independent algebra, raw-data and physical-limit checks; no optimization or flow solve."""
from pathlib import Path
import csv,hashlib,importlib.util,json,math
import numpy as np
HERE=Path(__file__).resolve().parent;PROJECT=HERE.parents[2]
OLD=PROJECT/'docs/reports/bivariate_piecewise_comparison_20261022'
spec=importlib.util.spec_from_file_location('correlation',HERE/'dimensionless_correlation.py');model=importlib.util.module_from_spec(spec);spec.loader.exec_module(model)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rows=lambda p:list(csv.DictReader(p.open(encoding='utf-8-sig')))
kv=lambda p:dict(l.split('=',1) for l in p.read_text().splitlines() if '=' in l)
def save(name,obj):(HERE/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False))
def main():
    protected=json.loads((OLD/'input_hashes.json').read_text())
    for p,h in protected.items():assert sha(Path(p))==h,p
    existing=rows(OLD/'training_data.csv');preds=rows(OLD/'full_fit_predictions.csv');computed=[];agreement=[]
    for r in existing:
        raw=kv(Path(r['source']));h,d,w=[float(raw[k])*1e9 for k in ['mesa_gap_m','groove_depth_m','groove_width_m']]
        assert math.isclose(w,120,rel_tol=1e-14) and float(raw['Keff_m3'])==float(r['K'])
        assert model.inside_sample_envelope(w,h,d)
        result=model.predict(w,h,d,r['direction']);expected=next(s for s in preds if s['key']==r['key'] and s['model']=='C4')
        agreement.append(abs(result['K_m3']/float(expected['K_pred'])-1))
        assert agreement[-1]<5e-14
        alpha,beta=h/w,d/w;a,b,c,q=model.PARAMS['coefficients'][r['direction']]
        original_delta=math.exp(a+b*math.log(beta)+c*math.log(alpha)+q*math.log(alpha)**2)
        assert math.isclose(result['Delta_excess'],original_delta,rel_tol=2e-14)
        Kflat=(h*1e-9)**3/12
        assert Kflat<=result['K_m3']<=result['K_LC_m3']
        computed.append({'key':r['key'],'direction':r['direction'],'w_nm':w,'h_nm':h,'d_nm':d,'K_raw_m3':float(r['K']),
            **result,'error_percent':100*(result['K_m3']/float(r['K'])-1)})
    summaries=[]
    for dr in ['P','T']:
        e=np.array([r['error_percent'] for r in computed if r['direction']==dr]);expected=next(r for r in rows(OLD/'full_fit_summary.csv') if r['direction']==dr and r['model']=='C4')
        stat={'direction':dr,'n':len(e),'MAE_percent':float(np.abs(e).mean()),'max_abs_percent':float(np.abs(e).max())}
        assert math.isclose(stat['MAE_percent'],float(expected['MAE_percent']),abs_tol=1e-11)
        summaries.append(stat)
    # Algebraic homogeneity across multiple scales. Not a fresh fluid-field validation.
    scales=[.25,.5,2.,10.];scaling=0.
    for r in existing:
        dr=r['direction'];h=float(r['h']);d=float(r['d']);reference=model.predict(120,h,d,dr)
        for lam in scales:
            p=model.predict(120*lam,h*lam,d*lam,dr)
            scaling=max(scaling,abs(p['K_m3']/(reference['K_m3']*lam**3)-1))
            assert math.isclose(p['F_mobility'],reference['F_mobility'],rel_tol=2e-14)
        si=model.predict(120e-9,h*1e-9,d*1e-9,dr,'m')
        assert math.isclose(si['K_m3'],reference['K_m3'],rel_tol=2e-14)
    assert scaling<2e-14
    # Screen a dense interior-ratio lattice against rigorous continuum bounds.
    count=0;minimum_ratio=math.inf
    for alpha in np.geomspace(25/120,125/120,81):
        for beta in np.geomspace(25/120,1,81):
            if not model.inside_sample_envelope(1,float(alpha),float(beta)):continue
            for dr in ['P','T']:
                result=model.predict(1,float(alpha),float(beta),dr,'m');ratio=result['K_m3']/(alpha**3/12)
                assert 1<=ratio and result['K_m3']<=result['K_LC_m3'];minimum_ratio=min(minimum_ratio,ratio);count+=1
    # Far-outside counterexamples demonstrate that the old candidate is not global.
    counter=[]
    for depth in [1e-6,10000.]:
        out=model.predict(120,75,depth,'T',allow_extrapolation=True);flat=(75e-9)**3/12
        assert out['K_m3']<flat
        counter.append({'h_nm':75,'d_nm':depth,'w_nm':120,'direction':'T','K_candidate_over_flat':out['K_m3']/flat,
            'outside_sample_domain':True,'physical_lower_bound_violated':True})
    for dr in ['P','T']:
        out=model.predict(120,75,0,dr);assert out['F_mobility']==1 and math.isclose(out['K_m3'],(75e-9)**3/12,rel_tol=1e-14)
    domain=[];seen=set()
    for r in rows(PROJECT/'CASE/D_series/D4_variable_groove_transport_20261023/protocol/candidate_cases.csv'):
        if r['role']!='new_dev':continue
        geometry=tuple(float(r[k]) for k in ['w_nm','h_nm','d_nm'])
        if geometry in seen:continue
        seen.add(geometry);w,h,d=geometry
        domain.append({'w_nm':w,'h_nm':h,'d_nm':d,'h_over_w':h/w,'d_over_w':d/w,
            'inside_old_sample_log_envelope':model.inside_sample_envelope(w,h,d),
            'equivalent_reference_h_nm':120*h/w,'equivalent_reference_d_nm':120*d/w})
    summary={'ok':True,'original_input_hashes_unchanged':len(protected),'raw_points_rechecked':36,
        'no_refit':True,'maximum_relative_difference_from_stored_C4':max(agreement),
        'existing_full_fit_metrics':summaries,'algebraic_scaling_relative_error':scaling,
        'in_domain_physical_bound_checks':count,'minimum_in_domain_K_over_flat':minimum_ratio,
        'outside_domain_counterexamples':counter,'new_dev_geometries_inside_old_envelope':sum(r['inside_old_sample_log_envelope'] for r in domain),
        'new_dev_geometries_total':len(domain),'new_OpenLB_runs':0,'new_flow_field_solves':0,'prediction_results_read':False,
        'old_V2_changed':False,'old_C4_changed':False,'final_model_lock_created':False,
        'external_new_width_validation_completed':False,'interpretation':'variables/scaling are derived; specific four-coefficient ansatz is retrospective empirical closure'}
    save('checks.json',summary);save('domain_screen_new_dev.json',domain);save('input_hashes.json',protected)
    for name,rr in [('recomputed36.csv',computed),('domain_screen_new_dev.csv',domain)]:
        with (HERE/name).open('w',encoding='utf-8-sig',newline='') as f:
            wr=csv.DictWriter(f,fieldnames=list(rr[0]),lineterminator='\n');wr.writeheader();wr.writerows(rr)
    save('artifact_hashes.json',{p.name:sha(p) for p in HERE.iterdir() if p.is_file() and p.name!='artifact_hashes.json'})
    assert all(sha(Path(p))==h for p,h in protected.items())
    print(json.dumps(summary,ensure_ascii=False))
if __name__=='__main__':main()

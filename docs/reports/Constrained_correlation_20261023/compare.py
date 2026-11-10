"""Frozen-scope retrospective fitting. Never launches CFD or reads reserved outputs."""
from pathlib import Path
import csv,hashlib,json,platform,time
import numpy as np
import scipy
from scipy.optimize import least_squares
from models import normalized,gains,blend

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
OLD=ROOT/'docs/reports/bivariate_piecewise_comparison_20261022'
PHYS=ROOT/'docs/reports/Correction_formula_physical_review_20261023'
MODELS=('G4','G6','C3_logK','C4_logK')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def readcsv(p):return list(csv.DictReader(Path(p).open(encoding='utf-8-sig')))
def writej(name,x):(HERE/name).write_text(json.dumps(x,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
def writecsv(name,rows):
    with (HERE/name).open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def load():
    protected=json.loads((PHYS/'input_hashes.json').read_text())
    assert all(sha(p)==h for p,h in protected.items())
    for p in [HERE/'PROTOCOL.md',HERE/'models.py',HERE/'compare.py',OLD/'training_data.csv',
              ROOT/'docs/reports/Correction_formula_derivation_20261023/coefficients_and_domain.json']:
        protected[str(p)]=sha(p)
    plan=readcsv(ROOT/'CASE/D_series/D4_variable_groove_transport_20261023/protocol/candidate_cases.csv')
    allowed={(float(p['h_nm']),float(p['d_nm']),p['direction']) for p in plan if p['role']=='legacy_dev'}
    rows=[]
    for r in readcsv(OLD/'training_data.csv'):
        raw=dict(line.split('=',1) for line in Path(r['source']).read_text().splitlines() if '=' in line)
        h,d,w,dx=[float(raw[k])*1e9 for k in ('mesa_gap_m','groove_depth_m','groove_width_m','dx_m')]
        assert abs(w-120)<1e-9 and abs(dx-5)<1e-9
        assert float(raw['Keff_m3'])==float(r['K'])
        role='development' if (round(h,8),round(d,8),r['direction']) in allowed else 'known_h25_sensitivity'
        assert role=='development' or abs(h-25)<1e-9
        rows.append(dict(key=r['key'],direction=r['direction'],h=round(h,8),d=round(d,8),w=w,
                         K=float(raw['Keff_m3']),s=w/h,t=d/h,role=role,source=r['source']))
    assert sum(r['role']=='development' for r in rows)==30 and len(rows)==36
    writej('input_hashes.json',protected);writecsv('data_roles.csv',rows)
    return rows,protected

records=[]
def fitmodel(model,train,label):
    fit={'model':model};group_keys=[r['key'] for r in train]
    for dr in ('T','P'):
        data=[r for r in train if r['direction']==dr]
        s=np.array([r['s'] for r in data]);t=np.array([r['t'] for r in data])
        y=np.array([r['K']/(r['h']*1e-9)**3*12 for r in data]);cp,ct=gains(s,t)
        rng=np.random.default_rng(20261023)
        if model.startswith('G'):
            free=model=='G6';lo=np.array([-12,.05]+([.25] if free else []))
            hi=np.array([12,6 if dr=='T' else 2.95]+([8.] if free else []))
            starts=[np.array([-1.,1.5 if dr=='T' else 1.]+([2.] if free else []))]
            for _ in range(7):
                starts.append(np.array([rng.uniform(-4,1),rng.uniform(.1,2.8)]+([rng.uniform(.5,5)] if free else [])))
            def prediction(p):
                if dr=='T':return 1+blend(ct,np.exp(p[0])*s**p[1],p[2] if free else 1.)
                return normalized(s,t,{**fit,'P':p},'P')
        else:
            x=-np.log(s);z=np.log(t/s)
            X=np.column_stack([np.ones(len(s)),z,x]+([x*x] if model=='C4_logK' else []))
            rank=int(np.linalg.matrix_rank(X))
            if rank<X.shape[1]:
                records.append(dict(label=label,model=model,direction=dr,status='INVALID_RANK',rank=rank,parameters=X.shape[1],train_keys=group_keys))
                return None
            start=np.linalg.lstsq(X,np.log((1+(cp if dr=='P' else ct))/y-1),rcond=None)[0]
            lo=np.array([-50,1e-8,-50]+([-50] if model=='C4_logK' else []));hi=np.array([50,10,50]+([50] if model=='C4_logK' else []))
            starts=[np.clip(start,lo+1e-6,hi-1e-6)]+[np.clip(start+rng.normal(0,.5,len(start)),lo+1e-6,hi-1e-6) for _ in range(3)]
            def prediction(p):return normalized(s,t,{**fit,dr:p},dr)
        attempts=[];solutions=[]
        for start in starts:
            res=least_squares(lambda p:np.log(prediction(p)/y),start,bounds=(lo,hi),jac='3-point',
                              ftol=1e-11,xtol=1e-11,gtol=1e-11,max_nfev=3000)
            objective=float(np.dot(res.fun,res.fun))
            jac_sv=np.linalg.svd(res.jac,compute_uv=False)
            attempts.append(dict(start=start.tolist(),x=res.x.tolist(),success=bool(res.success),status=int(res.status),
                                 message=res.message,objective=objective,nfev=int(res.nfev),optimality=float(res.optimality),
                                 near_boundary=bool(np.any(np.minimum(res.x-lo,hi-res.x)<1e-5)),jac_singular_values=jac_sv.tolist()))
            solutions.append(res)
        best=min(range(len(attempts)),key=lambda j:attempts[j]['objective'])
        assert attempts[best]['success'],(label,model,dr,attempts[best])
        fit[dr]=solutions[best].x.tolist()
        records.append(dict(label=label,model=model,direction=dr,status='FIT',train_keys=group_keys,
                            selected=best,bounds=[lo.tolist(),hi.tolist()],attempts=attempts))
    return fit

def predictions(fit,data,scheme,group,train):
    out=[]
    for r in data:
        kn=float(normalized(r['s'],r['t'],fit,r['direction']))
        pred=kn*(r['h']*1e-9)**3/12
        out.append(dict(scheme=scheme,group=str(group),model=fit['model'],key=r['key'],direction=r['direction'],
                        h_nm=r['h'],d_nm=r['d'],w_nm=r['w'],K_raw_m3=r['K'],K_pred_m3=pred,error_percent=100*(pred/r['K']-1),
                        train_count=len(train),test_in_train=r['key'] in {x['key'] for x in train}))
    return out

def main():
    begin=time.time();rows,protected=load();dev=[r for r in rows if r['role']=='development'];extra=[r for r in rows if r['role']!='development']
    result=[];fits={}
    for model in MODELS:
        fit=fitmodel(model,dev,'full_development');fits[model]=fit
        result+=predictions(fit,dev,'training','all',dev)
        result+=predictions(fit,extra,'known_h25_sensitivity','h25',dev)
        for axis in ('h','d'):
            for value in sorted({r[axis] for r in dev}):
                train=[r for r in dev if r[axis]!=value];test=[r for r in dev if r[axis]==value]
                assert not ({r['key'] for r in train}&{r['key'] for r in test})
                label=f'leave_{axis}_{value:g}';f=fitmodel(model,train,label)
                if f is not None:
                    fits[model+'__'+label]=f;result+=predictions(f,test,'leave_'+axis,value,train)
        print(model,'complete',flush=True)
    archived=json.loads((ROOT/'docs/reports/Correction_formula_derivation_20261023/coefficients_and_domain.json').read_text())
    af={'model':'C4_archived_all36',**archived['coefficients']}
    result+=predictions(af,dev,'descriptive_old_fit','all18geometries',rows)
    result+=predictions(af,extra,'descriptive_old_fit','all18geometries',rows)
    summary=[]
    for scheme,model,dr in sorted({(p['scheme'],p['model'],p['direction']) for p in result}):
        ps=[p for p in result if (p['scheme'],p['model'],p['direction'])==(scheme,model,dr)]
        e=np.array([p['error_percent'] for p in ps]);worst=ps[int(np.argmax(abs(e)))]
        summary.append(dict(scheme=scheme,model=model,direction=dr,n=len(e),MAE_percent=float(np.mean(abs(e))),
                            RMSE_percent=float(np.sqrt(np.mean(e*e))),max_abs_percent=float(np.max(abs(e))),
                            bias_percent=float(np.mean(e)),worst_key=worst['key']))
    assert all(not p['test_in_train'] for p in result if p['scheme'].startswith('leave_'))
    assert all(sha(p)==h for p,h in protected.items())
    writej('fits.json',fits);writej('optimization_records.json',records);writecsv('predictions.csv',result);writecsv('summary.csv',summary)
    writej('execution.json',dict(python=platform.python_version(),numpy=np.__version__,scipy=scipy.__version__,
        elapsed_seconds=time.time()-begin,protected_inputs=len(protected),input_mismatches=[],
        fitted_blocks=sum(r['status']=='FIT' for r in records),invalid_rank_blocks=sum(r['status']=='INVALID_RANK' for r in records),
        optimizer_attempts=sum(len(r.get('attempts',[])) for r in records),
        optimizer_failed_attempts=sum(not a['success'] for r in records for a in r.get('attempts',[])),
        selected_boundary_hits=[{'model':r['model'],'label':r['label'],'direction':r['direction']} for r in records if r['status']=='FIT' and r['attempts'][r['selected']]['near_boundary']],
        retained_prediction_rows=len(result),prediction_results_read=False,new_solver_runs=0,model_lock_created=False))
    for row in summary:
        if row['scheme'] in ('training','leave_h','leave_d'):print(row,flush=True)

if __name__=='__main__':main()

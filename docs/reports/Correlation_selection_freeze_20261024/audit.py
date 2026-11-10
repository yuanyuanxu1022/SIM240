"""Read-only input audit; no optimizer, solver or reserved result access."""
from pathlib import Path
import csv, json, math, hashlib
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OLD = HERE.parent/'Constrained_correlation_20261023'
PLAN = ROOT/'CASE/D_series/D4_variable_groove_transport_20261023/protocol/candidate_cases.csv'
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def readcsv(p): return list(csv.DictReader(Path(p).open(encoding='utf-8-sig')))
def writej(n,v): (HERE/n).write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def writecsv(n,rs):
    with (HERE/n).open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(rs[0]));w.writeheader();w.writerows(rs)
def gain(s,t,fit,dr):
    r=t*(3+t*(3+t));lp=r/2;lt=r/(r+2)
    def H(x,y,m):
        lo=np.minimum(x,y);hi=np.maximum(x,y)
        return lo/(1+(lo/hi)**m)**(1/m)
    pt,pp=fit['T'],fit['P'];mt=pt[2] if len(pt)==3 else 1.;mp=pp[2] if len(pp)==3 else 1.
    et=H(lt,np.exp(pt[0])*s**pt[1],mt)
    ep=et+H(lp-et,np.exp(pp[0])*s**pp[1]+s*s*t/2,mp)
    return 1+(ep if dr=='P' else et)
def stats(a):
    a=np.asarray(a);return dict(n=len(a),MAE_percent=float(np.mean(abs(a))),RMSE_percent=float(np.sqrt(np.mean(a*a))),max_abs_percent=float(max(abs(a))),bias_percent=float(np.mean(a)))

def main():
    inputs=json.loads((OLD/'input_hashes.json').read_text())
    inputs.update({str(ROOT/p):v for p,v in json.loads((OLD/'artifact_hashes.json').read_text()).items()})
    for p in [PLAN,OLD/'DECISION_TRADEOFF_20261023.md',OLD/'tradeoff_calcs.py',Path(__file__)]: inputs[str(p)]=sha(p)
    assert all(Path(p).is_file() and sha(p)==v for p,v in inputs.items())
    writej('input_hashes.json',inputs)
    fits=json.loads((OLD/'fits.json').read_text());pred=readcsv(OLD/'predictions.csv')
    # Bind existing prediction references back to raw development result.txt files.
    raw={}
    for r in readcsv(HERE.parent/'bivariate_piecewise_comparison_20261022/training_data.csv'):
        kv=dict(x.split('=',1) for x in Path(r['source']).read_text().splitlines() if '=' in x)
        assert float(kv['Keff_m3'])==float(r['K'])
        raw[(round(float(kv['mesa_gap_m'])*1e9),round(float(kv['groove_depth_m'])*1e9),r['direction'])]=float(r['K'])
    paired={};maximum=0.
    for r in pred:
        if r['model'] not in ('G4','G6') or r['scheme'] not in ('leave_h','leave_d'):continue
        assert r['test_in_train']=='False'
        h,d,w=map(float,(r['h_nm'],r['d_nm'],r['w_nm']))
        assert float(r['K_raw_m3'])==raw[(round(h),round(d),r['direction'])]
        fit=fits[r['model']+'__'+r['scheme']+'_'+format(float(r['group']), 'g')]
        k=float(gain(w/h,d/h,fit,r['direction']))*(h*1e-9)**3/12
        maximum=max(maximum,abs(k/float(r['K_pred_m3'])-1))
        paired[(r['scheme'],r['model'],r['key'].rsplit('_',1)[0],r['direction'])]=(k,float(r['K_raw_m3']))
    assert maximum<1e-12
    out=[]
    for sc in ('leave_h','leave_d'):
        geos=sorted({k[2] for k in paired if k[0]==sc})
        for model in ('G4','G6','MIX7'):
            vals={k:[] for k in ('P','T','A')}
            for geo in geos:
                p=paired[(sc,'G4' if model=='MIX7' else model,geo,'P')]
                t=paired[(sc,'G6' if model=='MIX7' else model,geo,'T')]
                vals['P'].append(100*(p[0]/p[1]-1));vals['T'].append(100*(t[0]/t[1]-1))
                vals['A'].append(100*((p[0]/t[0])/(p[1]/t[1])-1))
            for dr,a in vals.items():out.append(dict(scheme=sc,model=model,quantity=dr,**stats(a)))
    writecsv('tradeoffs.csv',out)
    stability=[];opt=[];records=json.loads((OLD/'optimization_records.json').read_text())
    for model in ('G4','G6'):
        folds=[v for k,v in fits.items() if k.startswith(model+'__')];assert len(folds)==8
        for dr in ('P','T'):
            for j,name in enumerate(['log_a','p']+(['m'] if model=='G6' else [])):
                v=np.array([f[dr][j] for f in folds]);base=fits[model][dr][j]
                stability.append(dict(model=model,direction=dr,parameter=name,full_fit=base,fold_min=float(min(v)),fold_max=float(max(v)),fold_n=8))
        for rec in records:
            if rec['model']!=model or rec['status']!='FIT':continue
            attempts=rec['attempts'];best=attempts[rec['selected']];s=best['jac_singular_values']
            lo,hi=map(np.array,rec['bounds']);x=np.array(best['x'])
            assert best['near_boundary']==bool(np.any(np.minimum(x-lo,hi-x)<1e-5))
            opt.append(dict(model=model,label=rec['label'],direction=rec['direction'],n_starts=len(attempts),all_success=all(a['success'] for a in attempts),selected_near_boundary=best['near_boundary'],jac_cond=s[0]/s[-1],max_parameter_start_spread=float(np.max(np.ptp([a['x'] for a in attempts],axis=0))),objective_spread=max(a['objective'] for a in attempts)-min(a['objective'] for a in attempts)))
    writecsv('parameter_stability.csv',stability);writecsv('optimizer_stability.csv',opt)
    plan=readcsv(PLAN);reserved=[r for r in plan if r['blind_geometry']=='True'];assert len(reserved)==20
    assert sum(r['role']=='prediction_test' for r in reserved)==16
    forecasts=[]
    for r in reserved:
        s=float(r['w_nm'])/float(r['h_nm']);t=float(r['d_nm'])/float(r['h_nm']);h=float(r['h_nm'])*1e-9;dr=r['direction']
        for m in ('G4','G6','MIX7'):
            model=('G4' if dr=='P' else 'G6') if m=='MIX7' else m
            n=float(gain(s,t,fits[model],dr));r3=t*(3+t*(3+t));local=1+(r3/2 if dr=='P' else r3/(r3+2))
            folds=[float(gain(s,t,v,dr)) for k,v in fits.items() if k.startswith(model+'__')]
            forecasts.append(dict(planned_case_id=r['planned_case_id'],role=r['role'],model=m,direction=dr,h_nm=r['h_nm'],d_nm=r['d_nm'],w_nm=r['w_nm'],P_nm=r['P_nm'],dx_nm=r['dx_nm'],K_pred_m3=n*h**3/12,F_pred=n/local,resistance_correction=local/n,fold_min_K_m3=min(folds)*h**3/12,fold_max_K_m3=max(folds)*h**3/12,max_fold_deviation_percent=max(abs(v/n-1) for v in folds)*100))
    writecsv('reserved_predictions.csv',forecasts)
    grids=[]
    for label,ss,tt in [('target',np.geomspace(.8,3.2,101),np.geomspace(1/3,1.6,101))]:
        s,t=np.meshgrid(ss,tt);s=s.ravel();t=t.ravel()
        for m in ('G4','G6'):
            for dr in ('P','T'):
                full=gain(s,t,fits[m],dr);fold=np.array([gain(s,t,v,dr) for k,v in fits.items() if k.startswith(m+'__')]);dev=100*np.max(abs(fold/full-1),axis=0);idx=int(np.argmax(dev))
                grids.append(dict(grid=label,n=len(s),model=m,direction=dr,max_fold_deviation_percent=float(dev[idx]),s_at_max=float(s[idx]),t_at_max=float(t[idx])))
    writej('target_sensitivity.json',grids)
    ptmeans={m:{dr:sum(r['MAE_percent'] for r in out if r['model']==m and r['quantity']==dr)/2 for dr in ('P','T')} for m in ('G4','G6')}
    dp=ptmeans['G6']['P']-ptmeans['G4']['P'];dt=ptmeans['G4']['T']-ptmeans['G6']['T']
    writej('audit_summary.json',dict(input_count=len(inputs),inputs_unchanged=all(sha(p)==v for p,v in inputs.items()),cv_recomputed_count=len(paired),cv_max_relative_difference=maximum,mean_MAE_by_direction=ptmeans,P_weight_break_even=dt/(dp+dt),parameter_bound_hit_tolerance=1e-5,bound_hits=[r for r in opt if r['selected_near_boundary']],reserved_geometry_count=8,reserved_primary_direction_count=16,reserved_grid_direction_count=4,solver_runs=0,prediction_results_read=False,new_fits=0))
    print(json.dumps(json.loads((HERE/'audit_summary.json').read_text()),indent=2))
if __name__=='__main__':main()

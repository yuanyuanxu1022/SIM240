"""Scalar reimplementation and raw-source checks. No import of fit/model code."""
from pathlib import Path
import csv,json,math,hashlib

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
def load(name):return json.loads((HERE/name).read_text())
def rows(name):return list(csv.DictReader((HERE/name).open(encoding='utf-8-sig')))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
fits=load('fits.json');preds=rows('predictions.csv');data={r['key']:r for r in rows('data_roles.csv')}
params=json.loads((ROOT/'docs/reports/Correction_formula_derivation_20261023/coefficients_and_domain.json').read_text())
protected=load('input_hashes.json');assert all(sha(p)==v for p,v in protected.items())
def hm(x,y,m):
    if x==0:return 0.
    u=-m*math.log(x);v=-m*math.log(y);a=max(u,v)
    return math.exp(-(a+math.log(math.exp(u-a)+math.exp(v-a)))/m)
def evaluate(s,t,f):
    r=t*(3+t*(3+t));cp=r/2;ct=r/(r+2)
    if f['model'].startswith('G'):
        a,p,*m=f['T'];mt=m[0] if m else 1.;et=hm(ct,math.exp(a)*s**p,mt)
        a,p,*m=f['P'];mp=m[0] if m else 1.;dp=math.exp(a)*s**p+s*s*t/2
        add=hm(cp-et,dp,mp);ep=et+add
        if t:
            dt=6*(1+t)**2/(r+2)**2;dt*= (et/ct)**(mt+1)
            hp=(add/(cp-et))**(mp+1)
            dpred=(1-hp)*dt+hp*1.5*(1+t)**2+(add/dp)**(mp+1)*s*s/2
        else:dt=dpred=1.5
        return {'P':1+ep,'T':1+et,'dP_dt':dpred,'dT_dt':dt,'CP':cp,'CT':ct}
    out={'CP':cp,'CT':ct}
    for dr,cgain in [('P',cp),('T',ct)]:
        a,b,c,*q=f[dr];x=-math.log(s);z=math.log(t/s)
        delta=math.exp(a+b*z+c*x+(q[0]*x*x if q else 0))
        out[dr]=(1+cgain)/(1+delta)
        lcprime=1.5*(1+t)**2 if dr=='P' else 6*(1+t)**2/(r+2)**2
        out['d'+dr+'_dt']=out[dr]*(lcprime/(1+cgain)-b*delta/(1+delta)/t)
    return out

maxreldiff=0.;maxerrdiff=0.
for r in preds:
    d=data[r['key']];raw=dict(x.split('=',1) for x in Path(d['source']).read_text().splitlines() if '=' in x)
    assert float(raw['Keff_m3'])==float(r['K_raw_m3'])
    scheme=r['scheme'];name=r['model']
    if name=='C4_archived_all36':f={'model':name,**params['coefficients']}
    elif scheme.startswith('leave_'):
        label=scheme+'_'+format(float(r['group']),'g');f=fits[name+'__'+label]
        axis='h_nm' if scheme=='leave_h' else 'd_nm'
        assert float(r[axis])==float(r['group']) and r['test_in_train']=='False'
        relevant=[x for x in load('optimization_records.json') if x['model']==name and x['label']==label and x['status']=='FIT']
        assert len(relevant)==2
        assert all(r['key'] not in x['train_keys'] for x in relevant)
    else:f=fits[name]
    s=float(r['w_nm'])/float(r['h_nm']);t=float(r['d_nm'])/float(r['h_nm'])
    k=evaluate(s,t,f)[r['direction']]*(float(r['h_nm'])*1e-9)**3/12
    maxreldiff=max(maxreldiff,abs(k/float(r['K_pred_m3'])-1))
    e=100*(k/float(r['K_raw_m3'])-1);maxerrdiff=max(maxerrdiff,abs(e-float(r['error_percent'])))
assert maxreldiff<1e-12
summarydiff=0.
for r in rows('summary.csv'):
    es=[float(x['error_percent']) for x in preds if all(x[k]==r[k] for k in ('scheme','model','direction'))]
    assert len(es)==int(r['n'])
    for key,val in [('MAE_percent',sum(map(abs,es))/len(es)),('RMSE_percent',math.sqrt(sum(e*e for e in es)/len(es))),('max_abs_percent',max(map(abs,es)))]:
        summarydiff=max(summarydiff,abs(val-float(r[key])))
assert summarydiff<1e-10

physics=[];derivative_error=0.;scaling_error=0.
for model in ('G4','G6','C3_logK','C4_logK'):
    f=fits[model]
    for domain in ('target_rectangle','old_log_hull','extended_diagnostic'):
        violations={'flat_lower':0,'LC_upper':0,'direction_order':0,'depth_P':0,'depth_T':0};count=0
        for j in range(101):
            for k in range(101):
                if domain=='target_rectangle':s=.8*4**(j/100);t=(1/3)*4.8**(k/100)
                elif domain=='old_log_hull':
                    al=(5/24)*5**(j/100);be=(5/24)*(24/5)**(k/100)
                    if not all(a*math.log(al)+b*math.log(be)+c<=1e-12 for a,b,c in params['log_domain_halfspaces']):continue
                    s=1/al;t=be/al
                else:s=10**(-3+6*j/100);t=10**(-7+11*k/100)
                z=evaluate(s,t,f);count+=1
                violations['flat_lower']+=int(min(z['P'],z['T'])<1-1e-10)
                violations['LC_upper']+=int(z['P']>1+z['CP']+1e-10*(1+z['CP']) or z['T']>1+z['CT']+1e-10)
                violations['direction_order']+=int(z['T']>z['P']+1e-10*z['P'])
                for dr in ('P','T'):violations['depth_'+dr]+=int(z['d'+dr+'_dt']*t/z[dr]<-1e-10)
                if model.startswith('G') and domain=='target_rectangle' and j%10==0 and k%10==0:
                    eps=1e-5;zp=evaluate(s,t*math.exp(eps),f);zm=evaluate(s,t*math.exp(-eps),f)
                    for dr in ('P','T'):
                        finite=(math.log(zp[dr])-math.log(zm[dr]))/(2*eps)
                        derivative_error=max(derivative_error,abs(finite-t*z['d'+dr+'_dt']/z[dr]))
        physics.append(dict(model=model,domain=domain,geometry_points=count,violations=violations))
        if model.startswith('G'):assert not any(violations.values()),physics[-1]
    if model.startswith('G'):
        for s in (.01,.8,1.6,3.2,100):assert evaluate(s,0,f)['P']==evaluate(s,0,f)['T']==1.
        for lam in (.01,.5,2,100):
            for dr in ('P','T'):
                h=75e-9;w=120e-9;d=100e-9
                k1=evaluate(w/h,d/h,f)[dr]*h**3/12
                k2=evaluate(lam*w/(lam*h),lam*d/(lam*h),f)[dr]*(lam*h)**3/12
                scaling_error=max(scaling_error,abs(k2/(lam**3*k1)-1))
assert derivative_error<1e-8 and scaling_error<1e-12

pairchecks=[]
for name in ('G4','G6','C3_logK','C4_logK'):
    for dr in ('P','T'):
        bad=total=0
        for h in (50.,75.,125.):
            xs=sorted([x for x in preds if x['model']==name and x['scheme']=='training' and x['direction']==dr and float(x['h_nm'])==h],key=lambda x:float(x['d_nm']))
            for a,b in zip(xs,xs[1:]):total+=1;bad+=int(float(b['K_pred_m3'])/float(a['K_pred_m3'])-1 < -1e-10)
        pairchecks.append(dict(model=name,direction=dr,pairs=total,decreasing=bad))
report=dict(ok=True,predictions_recomputed=len(preds),max_prediction_relative_difference=maxreldiff,
    max_error_percentage_point_difference=maxerrdiff,max_summary_difference=summarydiff,
    derivative_finite_difference_max_error=derivative_error,scaling_relative_error=scaling_error,
    protected_inputs=len(protected),input_mismatches=[],physics_scans=physics,adjacent_depth_pairs=pairchecks,
    theoretical_limit_warning='G along-groove h->0 fixed d/w is a rectangular-duct approximation, not its exact series solution',
    NUMERICAL_GATE='NOT_EVALUATED',RESULT_PASS='NOT_EVALUATED',geometry_PASS='NOT_EVALUATED',model_lock_created=False)
assert all(sha(p)==v for p,v in protected.items())
(HERE/'independent_verification.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))

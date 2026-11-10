#!/usr/bin/env python3
"""Protocol-bound retrospective comparison; no OpenLB or original-model edits."""
from pathlib import Path
import argparse,csv,hashlib,json,math,platform,sys,datetime
from zoneinfo import ZoneInfo
import numpy as np
from scipy.optimize import lsq_linear
import scipy

MODELS=('C3','C4','H4')
MIN_B=1e-8
TIE=1e-10

def digest(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for chunk in iter(lambda:f.read(1048576),b''):h.update(chunk)
 return h.hexdigest()
def kv(p):
 return dict(line.split('=',1) for line in Path(p).read_text().splitlines() if '=' in line)
def write_json(p,value):p.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
def write_csv(p,rows):
 with p.open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def local(h,d,dr):
 return ((h**3+(h+d)**3)/24 if dr=='P' else 1/(6*(h**-3+(h+d)**-3)))*1e-27

def matrix(records,model,tau=None):
 x=np.log([r['h']/120. for r in records]);z=np.log([r['d']/120. for r in records])
 cols=[np.ones(len(records)),z,x]
 if model=='C4':cols.append(x*x)
 if model=='H4':cols.append(np.maximum(x-tau,0.))
 return np.column_stack(cols)
def fit(records,model,tau=None):
 A=matrix(records,model,tau);y=np.log([r['K0']/r['K']-1 for r in records])
 rank=int(np.linalg.matrix_rank(A))
 if rank!=A.shape[1]:raise ValueError(f'rank deficient {model}: {rank}/{A.shape[1]}')
 coef=np.linalg.lstsq(A,y,rcond=None)[0];method='unconstrained SVD';status='global linear least-squares';active=False
 if coef[1]<MIN_B:
  lower=np.full(A.shape[1],-np.inf);lower[1]=MIN_B
  result=lsq_linear(A,y,bounds=(lower,np.full(A.shape[1],np.inf)),tol=1e-12,max_iter=1000,lsq_solver='exact')
  if not result.success:raise ValueError('constrained fit failed '+result.message)
  coef=result.x;method='convex bounded linear least-squares';status=str(result.message);active=True
 return {'model':model,'tau':tau,'h_c_nm':None if tau is None else float(120*np.exp(tau)),'coefficients':coef.tolist(),'rank':rank,'condition_number':float(np.linalg.cond(A)),'training_sse_logE':float(np.sum((A@coef-y)**2)),'n_train':len(records),'train_keys':[r['key'] for r in records],'method':method,'optimizer_status':status,'b_bound_active':active}
def predict(fit_result,records):
 g=matrix(records,fit_result['model'],fit_result['tau'])@np.asarray(fit_result['coefficients'])
 values=np.asarray([r['K0'] for r in records])*np.exp(-np.logaddexp(0.,g))
 if not np.all(np.isfinite(values)) or not np.all(values>0):raise ValueError('nonfinite/nonpositive prediction')
 return values

def select_hinge(train,tag):
 levels=sorted(set(r['h'] for r in train))
 if len(levels)<3:raise ValueError('H4 requires >=3 training h layers')
 candidates=[]
 for h0,h1 in zip(levels[:-1],levels[1:]):
  tau=float((math.log(h0/120.)+math.log(h1/120.))/2)
  candidate={'tau':tau,'h_c_nm':float(120*math.exp(tau)),'bracket_h_nm':[h0,h1],'inner_folds':[],'valid':True}
  losses=[]
  for depth in sorted(set(r['d'] for r in train)):
   tr=[r for r in train if r['d']!=depth];va=[r for r in train if r['d']==depth]
   assert not ({r['key'] for r in tr}&{r['key'] for r in va})
   try:
    f=fit(tr,'H4',tau);pr=predict(f,va);error=pr/np.asarray([r['K'] for r in va])-1
    mse=float(np.mean(error**2));losses.append(mse)
    candidate['inner_folds'].append({'held_depth':depth,'fit':f,'validation_keys':[r['key'] for r in va],'predictions':pr.tolist(),'mse_relative_K':mse})
   except ValueError as exc:
    candidate['valid']=False;candidate['reason']=str(exc);break
  if candidate['valid']:candidate['score']=float(np.mean(losses))
  candidates.append(candidate)
 valid=[c for c in candidates if c['valid']]
 if not valid:raise ValueError('no valid H4 knot')
 best=min(c['score'] for c in valid);ties=[c for c in valid if c['score']<=best+TIE]
 center=(math.log(min(levels)/120.)+math.log(max(levels)/120.))/2
 chosen=min(ties,key=lambda c:(abs(c['tau']-center),c['tau']))
 selection={'tag':tag,'training_h_levels':levels,'candidate_count':len(candidates),'tied_h_c_nm':[c['h_c_nm'] for c in ties],'chosen_h_c_nm':chosen['h_c_nm'],'chosen_bracket_h_nm':chosen['bracket_h_nm'],'candidates':candidates}
 return fit(train,'H4',chosen['tau']),selection

def metrics(err):
 a=np.asarray(err,dtype=float)
 return {'n':len(a),'MAE_percent':float(np.mean(np.abs(a))),'RMSE_percent':float(np.sqrt(np.mean(a*a))),'max_abs_percent':float(np.max(np.abs(a))),'mean_signed_percent':float(np.mean(a))}
def raw_record(project,indexrow):
 f=project/indexrow['rel_path']/'steady/result.txt';r=kv(f)
 h=round(float(r['mesa_gap_m'])*1e9,8);d=round(float(r['groove_depth_m'])*1e9,8)
 dr='P' if r['direction']=='parallel' else 'T'
 return {'key':f'h{h:g}_d{d:g}_{dr}','run_id':indexrow['run_id'],'h':h,'d':d,'direction':dr,'K':float(r['Keff_m3']),'K0':local(h,d,dr),'source':str(f),'dx_nm':round(float(r['dx_m'])*1e9,8)}

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--project',type=Path,required=True);ap.add_argument('--workspace',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);args=ap.parse_args();out=args.out
 if (out/'RESULTS.json').exists():raise SystemExit('Refusing to overwrite a completed comparison')
 protocol=out/'PROTOCOL.md';code=Path(__file__);assert protocol.is_file()
 indexfile=args.project/'docs/reports/第一篇_run_id索引_20261022.csv'
 index=list(csv.DictReader(indexfile.open(encoding='utf-8-sig')))
 data=[raw_record(args.project,r) for r in index if 'D2_groove_error_map' in r['rel_path'] and float(r['dx_nm'])==5 and not r['run_id'].startswith('mu15')]
 fine=[raw_record(args.project,r) for r in index if 'D2_groove_error_map' in r['rel_path'] and float(r['dx_nm'])==2.5]
 data.sort(key=lambda r:(r['direction'],r['h'],r['d']));fine.sort(key=lambda r:(r['direction'],r['h'],r['d']))
 assert len(data)==36 and len(fine)==8 and len({(r['h'],r['d']) for r in data})==18
 assert all(r['K0']>r['K']>0 for r in data)
 derivedfile=args.workspace/'03_数据/00_数据索引/36项主方向数据_模型对照.csv';derived=list(csv.DictReader(derivedfile.open(encoding='utf-8-sig')))
 for r in data:
  found=[a for a in derived if float(a['h_nm'])==r['h'] and float(a['d_nm'])==r['d'] and a['direction']==r['direction']];assert len(found)==1 and float(found[0]['K_m3'])==r['K']
 protect=[protocol,code,indexfile,derivedfile]+[args.project/r['rel_path']/'steady/result.txt' for r in index]
 for rel in ['CASE/D_series/D2_groove_error_map/analysis_fit_v2.py','CASE/D_series/D2_groove_error_map/src/d2_groove_error_map.cpp','CASE/D_series/D2_groove_error_map/results/analysis/v2_fit_params.csv','CASE/D_series/D2_groove_error_map/results/analysis/v2_residuals.csv','CASE/D_series/D2_groove_error_map/results/summary.csv','CASE/D_series/D2_groove_error_map/results/d75_summary.csv','CASE/D_series/D2_groove_error_map/results/h25_summary.csv','CASE/D_series/D2_groove_error_map/results/d120_summary.csv']:protect.append(args.project/rel)
 hashes={str(p):digest(p) for p in protect}
 write_json(out/'input_hashes.json',hashes)
 write_json(out/'configuration.json',{'analysis_id':'bivariate_cmp_20261022_v1','date_beijing':datetime.datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),'protocol_sha256':digest(protocol),'code_sha256':digest(code),'models':MODELS,'minimum_beta_exponent':MIN_B,'inner_score_tie_tolerance':TIE,'python':sys.version,'numpy':np.__version__,'scipy':scipy.__version__,'platform':platform.platform(),'solver_run':False,'original_V2_modified':False})
 write_csv(out/'training_data.csv',data)
 predictions=[];fits=[];selections=[];full_predictions=[];fullfits={};sensitivity=[]
 for dr in ['P','T']:
  drdata=[r for r in data if r['direction']==dr]
  for model in MODELS:
   if model=='H4':f,sel=select_hinge(drdata,f'full_{dr}');selections.append(sel)
   else:f=fit(drdata,model)
   f['direction']=dr;f['scheme']='full';fits.append(f);fullfits[(dr,model)]=f
   for r,pred in zip(drdata,predict(f,drdata)):
    full_predictions.append({'direction':dr,'model':model,'key':r['key'],'h':r['h'],'d':r['d'],'K_ref':r['K'],'K_pred':float(pred),'error_percent':float(100*(pred/r['K']-1))})
  for scheme,axis in [('leave_h','h'),('leave_d','d')]:
   for level in sorted(set(r[axis] for r in drdata)):
    tr=[r for r in drdata if r[axis]!=level];te=[r for r in drdata if r[axis]==level]
    train_keys={r['key'] for r in tr};test_keys={r['key'] for r in te};assert not train_keys&test_keys
    lo,hi=min(r[axis] for r in tr),max(r[axis] for r in tr)
    mode='axis_extrapolation' if level<lo or level>hi else 'axis_interpolation'
    for model in MODELS:
     if model=='H4':f,sel=select_hinge(tr,f'{scheme}_{dr}_{level:g}');selections.append(sel)
     else:f=fit(tr,model)
     f.update(direction=dr,scheme=scheme,held_level=level,test_keys=sorted(test_keys));fits.append(f)
     for r,pred in zip(te,predict(f,te)):
      predictions.append({'scheme':scheme,'direction':dr,'model':model,'held_axis':axis,'held_level':level,'axis_mode':mode,'key':r['key'],'h':r['h'],'d':r['d'],'K_ref':r['K'],'K_pred':float(pred),'error_percent':float(100*(pred/r['K']-1)),'h_c_nm':f['h_c_nm'],'K_pred_over_smooth':float(pred/(r['h']**3*1e-27/12))})
 summary=[];groups=[];subsets=[]
 for dr in ['P','T']:
  for scheme in ['leave_h','leave_d']:
   for model in MODELS:
    rr=[r for r in predictions if r['direction']==dr and r['scheme']==scheme and r['model']==model]
    summary.append(dict(direction=dr,scheme=scheme,model=model,**metrics([r['error_percent'] for r in rr])))
    for level in sorted(set(r['held_level'] for r in rr)):
     a=[r for r in rr if r['held_level']==level];groups.append(dict(direction=dr,scheme=scheme,model=model,held_level=level,axis_mode=a[0]['axis_mode'],**metrics([r['error_percent'] for r in a])))
    for mode in ['axis_interpolation','axis_extrapolation']:
     a=[r for r in rr if r['axis_mode']==mode];subsets.append(dict(direction=dr,scheme=scheme,model=model,axis_mode=mode,**metrics([r['error_percent'] for r in a])))
 full_summary=[]
 for dr in ['P','T']:
  for model in MODELS:
   rr=[r for r in full_predictions if r['direction']==dr and r['model']==model];full_summary.append(dict(direction=dr,model=model,**metrics([r['error_percent'] for r in rr])))
  fixed=[]
  for r in [r for r in data if r['direction']==dr]:
   beta=r['d']/120;factor=1/(1+1.7685*beta**1.6331) if dr=='P' else 1/(1+.4900*beta**.6990)
   fixed.append(100*(factor*r['K0']/r['K']-1))
  full_summary.append(dict(direction=dr,model='fixed_V2_retrospective',**metrics(fixed)))
 for r in fine:
  main_ref=next(a for a in data if a['key']==r['key'])['K']
  for model in MODELS:
   pred=float(predict(fullfits[(r['direction'],model)],[r])[0]);sensitivity.append({'direction':r['direction'],'model':model,'h':r['h'],'d':r['d'],'K_pred':pred,'K_5nm':main_ref,'K_2p5nm':r['K'],'error_5nm_percent':100*(pred/main_ref-1),'error_2p5nm_percent':100*(pred/r['K']-1),'interpretation':'same-geometry reference sensitivity, not independent prediction'})
 comparisons=[];decisions={}
 for dr in ['P','T']:
  changes=[]
  for scheme in ['leave_h','leave_d']:
   h=next(r for r in summary if r['direction']==dr and r['scheme']==scheme and r['model']=='H4')
   for base in ['C4','C3']:
    c=next(r for r in summary if r['direction']==dr and r['scheme']==scheme and r['model']==base)
    comp={'direction':dr,'scheme':scheme,'reference_model':base}
    for metric in ['MAE_percent','RMSE_percent','max_abs_percent']:
     comp[metric+'_delta_H4_minus_reference']=h[metric]-c[metric]
     comp[metric+'_relative_improvement_percent']=100*(1-h[metric]/c[metric])
    comparisons.append(comp)
    if base=='C4':changes.append(comp)
  improved=all(c['MAE_percent_delta_H4_minus_reference']<-TIE and c['RMSE_percent_delta_H4_minus_reference']<-TIE and c['max_abs_percent_delta_H4_minus_reference']<=TIE for c in changes)
  notimproved=all(c['MAE_percent_delta_H4_minus_reference']>=-TIE and c['RMSE_percent_delta_H4_minus_reference']>=-TIE for c in changes)
  decisions[dr]='consistent retrospective improvement under this protocol' if improved else 'no predictive improvement evidence under this protocol' if notimproved else 'mixed results; stable superiority not established'
 # Independent QR check of all unconstrained fits and direct scalar formula predictions.
 qrmax=0.;scalarmax=0.;bykey={r['key']:r for r in data}
 for f in fits:
  rr=[bykey[k] for k in f['train_keys']];A=matrix(rr,f['model'],f['tau']);y=np.log([r['K0']/r['K']-1 for r in rr])
  if not f['b_bound_active']:
   Q,R=np.linalg.qr(A,mode='reduced');beta=np.linalg.solve(R,Q.T@y);qrmax=max(qrmax,float(np.max(np.abs(A@(beta-np.asarray(f['coefficients']))))))
  recs=[bykey[k] for k in f.get('test_keys',f['train_keys'])]
  pr=predict(f,recs)
  for r,vec in zip(recs,pr):
   x,z=math.log(r['h']/120),math.log(r['d']/120);a,b,c=f['coefficients'][:3];g=a+b*z+c*x
   if f['model']=='C4':g+=f['coefficients'][3]*x*x
   if f['model']=='H4':g+=f['coefficients'][3]*max(x-f['tau'],0)
   scalar=r['K0']/(1+math.exp(g));scalarmax=max(scalarmax,abs(scalar/vec-1))
 # Rounding and exact branch continuity checks for final models.
 checks=[]
 for (dr,model),f in fullfits.items():
  recs=[r for r in data if r['direction']==dr];rounded=dict(f);rounded['coefficients']=[float(f'{c:.8g}') for c in f['coefficients']]
  if f['tau'] is not None:rounded['tau']=float(f"{f['tau']:.8g}")
  diff=float(np.max(np.abs(predict(rounded,recs)/predict(f,recs)-1)))
  checks.append({'direction':dr,'model':model,'8_significant_digit_prediction_change_percent':100*diff,'continuous_at_hinge':True if model=='H4' else 'not_applicable','positive_sample_predictions':bool(np.all(predict(f,recs)>0))})
 unchanged=all(digest(Path(p))==h for p,h in hashes.items())
 assert unchanged and qrmax<1e-9 and scalarmax<1e-10
 assert len(predictions)==216 and len(fits)==60 and len(selections)==20
 write_csv(out/'outer_predictions.csv',predictions);write_csv(out/'cv_summary.csv',summary);write_csv(out/'cv_groups.csv',groups);write_csv(out/'cv_subsets.csv',subsets);write_csv(out/'full_fit_predictions.csv',full_predictions);write_csv(out/'full_fit_summary.csv',full_summary);write_csv(out/'grid_reference_sensitivity.csv',sensitivity);write_csv(out/'model_comparisons.csv',comparisons)
 write_json(out/'fits.json',fits);write_json(out/'hinge_selection.json',selections);write_json(out/'formula_checks.json',checks)
 results={'analysis_id':'bivariate_cmp_20261022_v1','decisions':decisions,'input_hashes_unchanged':unchanged,'protected_file_count':len(hashes),'outer_predictions':len(predictions),'fit_count':len(fits),'hinge_selection_count':len(selections),'bounded_fit_count':sum(f['b_bound_active'] for f in fits),'QR_max_training_logE_difference':qrmax,'scalar_formula_max_relative_difference':scalarmax,'cv_summary':summary,'full_fit_summary':full_summary,'comparisons':comparisons,'full_coefficients':[f for f in fits if f['scheme']=='full'],'breakpoint_physical_status':'not established','new_simulations':False,'physical_gate_evaluated':False,'independent_final_test':False}
 write_json(out/'RESULTS.json',results)
 print(json.dumps({'decisions':decisions,'outer_predictions':len(predictions),'hashes_unchanged':unchanged,'QR_check':qrmax,'scalar_check':scalarmax},ensure_ascii=False))
if __name__=='__main__':main()

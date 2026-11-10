#!/usr/bin/env python3
"""Independent arithmetic and grouping check; does not import fitting code."""
from pathlib import Path
import csv,json,math,hashlib
import numpy as np
ROOT=Path(__file__).resolve().parent

def rows(name):return list(csv.DictReader((ROOT/name).open(encoding='utf-8-sig')))
def readkv(p):return dict(s.split('=',1) for s in Path(p).read_text().splitlines() if '=' in s)
data=rows('training_data.csv');bykey={r['key']:r for r in data}
for r in data:
 q=readkv(r['source']);assert float(q['Keff_m3'])==float(r['K']);assert abs(float(q['mesa_gap_m'])*1e9-float(r['h']))<1e-6
fits=json.loads((ROOT/'fits.json').read_text());sels=json.loads((ROOT/'hinge_selection.json').read_text());allfits=list(fits)
for sel in sels:
 for candidate in sel['candidates']:
  if not candidate['valid']:continue
  scores=[]
  for fold in candidate['inner_folds']:
   f=fold['fit'];allfits.append(f);tr=set(f['train_keys']);va=set(fold['validation_keys']);assert not tr&va
   assert all(float(bykey[k]['d'])!=fold['held_depth'] for k in tr)
   assert all(float(bykey[k]['d'])==fold['held_depth'] for k in va)
   sq=[]
   for key,val in zip(fold['validation_keys'],fold['predictions']):sq.append((float(val)/float(bykey[key]['K'])-1)**2)
   score=sum(sq)/len(sq);assert abs(score-fold['mse_relative_K'])<1e-12;scores.append(score)
  assert abs(sum(scores)/len(scores)-candidate['score'])<1e-12
qr_error=0.;pred_error=0.
for f in allfits:
 if f['b_bound_active']:raise AssertionError('independent verification requires explicit bounded solution check')
 X=[];Y=[]
 for key in f['train_keys']:
  r=bykey[key];u=math.log(float(r['h'])/120);v=math.log(float(r['d'])/120);a=[1.,v,u]
  if f['model']=='C4':a.append(u*u)
  if f['model']=='H4':a.append(max(0.,u-f['tau']))
  X.append(a);Y.append(math.log(float(r['K0'])/float(r['K'])-1))
 A=np.array(X);y=np.array(Y);Q,R=np.linalg.qr(A,mode='reduced');coef=np.linalg.solve(R,Q.T@y)
 qr_error=max(qr_error,float(np.max(np.abs(A@(coef-np.array(f['coefficients']))))))
 assert qr_error<1e-9
predictions=rows('outer_predictions.csv')
for r in predictions:
 f=next(f for f in fits if f['direction']==r['direction'] and f['model']==r['model'] and f['scheme']==r['scheme'] and f['held_level']==float(r['held_level']))
 assert r['key'] not in set(f['train_keys']) and r['key'] in set(f['test_keys'])
 axis='h' if r['scheme']=='leave_h' else 'd'
 assert all(float(bykey[k][axis])!=float(r['held_level']) for k in f['train_keys'])
 g=math.log(float(r['h'])/120);z=math.log(float(r['d'])/120);c=f['coefficients'];lin=c[0]+c[1]*z+c[2]*g
 if r['model']=='C4':lin+=c[3]*g*g
 if r['model']=='H4':lin+=c[3]*max(0.,g-f['tau'])
 h=float(r['h']);d=float(r['d']);k0=((h**3+(h+d)**3)/24 if r['direction']=='P' else h**3*(h+d)**3/(6*(h**3+(h+d)**3)))*1e-27
 khat=k0/(1+math.exp(lin));pred_error=max(pred_error,abs(khat/float(r['K_pred'])-1));assert pred_error<1e-12
 assert abs(100*(khat/float(bykey[r['key']]['K'])-1)-float(r['error_percent']))<1e-10
for s in rows('cv_summary.csv'):
 rs=[r for r in predictions if all(r[k]==s[k] for k in ['scheme','direction','model'])]
 assert len(rs)==18 and len({r['key'] for r in rs})==18
 e=[float(r['error_percent']) for r in rs]
 checks={'MAE_percent':sum(abs(x) for x in e)/18,'RMSE_percent':math.sqrt(sum(x*x for x in e)/18),'max_abs_percent':max(abs(x) for x in e),'mean_signed_percent':sum(e)/18}
 assert all(abs(checks[k]-float(s[k]))<1e-10 for k in checks)
hashes=json.loads((ROOT/'input_hashes.json').read_text())
for path,expected in hashes.items():assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==expected
result={'ok':True,'original_K_records_checked':len(data),'outer_predictions_checked':len(predictions),'fits_including_inner_checked_by_QR':len(allfits),'QR_max_logE_difference':qr_error,'scalar_max_prediction_relative_difference':pred_error,'training_validation_groups_disjoint':True,'all_input_hashes_unchanged':True,'models_imported':False,'solver_or_optimizer_run':False}
(ROOT/'independent_verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps(result,ensure_ascii=False))

#!/usr/bin/env python3
"""Descriptive tied-knot sensitivity; never used to select a model with test data."""
from pathlib import Path
import csv,json,math
import numpy as np
P=Path(__file__).resolve().parent
bykey={r['key']:r for r in csv.DictReader((P/'training_data.csv').open(encoding='utf-8-sig'))}
fits=json.loads((P/'fits.json').read_text());sels=json.loads((P/'hinge_selection.json').read_text());result=[]
for sel in sels:
 if len(sel['tied_h_c_nm'])<=1 or not sel['tag'].startswith('leave_h'):continue
 _,_,direction,level=sel['tag'].split('_');level=float(level)
 f=next(f for f in fits if f['model']=='H4' and f['scheme']=='leave_h' and f['direction']==direction and f['held_level']==level)
 train=[bykey[k] for k in f['train_keys']];test=[bykey[k] for k in f['test_keys']]
 for hc in sel['tied_h_c_nm']:
  tau=math.log(hc/120);A=[];y=[]
  for r in train:
   x=math.log(float(r['h'])/120);z=math.log(float(r['d'])/120);A.append([1,z,x,max(0,x-tau)]);y.append(math.log(float(r['K0'])/float(r['K'])-1))
  Q,R=np.linalg.qr(np.array(A));coef=np.linalg.solve(R,Q.T@np.array(y));errors=[]
  assert coef[1]>0
  for r in test:
   x=math.log(float(r['h'])/120);z=math.log(float(r['d'])/120);g=float(np.array([1,z,x,max(0,x-tau)])@coef);pred=float(r['K0'])/(1+math.exp(g));errors.append(100*(pred/float(r['K'])-1))
  result.append({'direction':direction,'held_h_nm':level,'candidate_h_c_nm':hc,'chosen_by_protocol':hc==sel['chosen_h_c_nm'],'MAE_percent':sum(abs(e) for e in errors)/len(errors),'max_abs_percent':max(abs(e) for e in errors),'usage':'diagnostic only; outer errors not used for knot selection'})
with (P/'tied_knot_sensitivity.csv').open('w',encoding='utf-8-sig',newline='') as out:
 w=csv.DictWriter(out,fieldnames=list(result[0]));w.writeheader();w.writerows(result)
print(json.dumps(result,ensure_ascii=False))

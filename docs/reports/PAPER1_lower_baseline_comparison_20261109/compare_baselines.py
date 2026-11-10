"""Compare three fixed formulas on the same 36 known main records, without fitting."""
from pathlib import Path
import csv, hashlib, json, statistics

OUT=Path(__file__).resolve().parent
REP=OUT.parent
with (REP/'PAPER1_scale_failure_audit_20261108/scalar_records.csv').open() as f:
    raw=[r for r in csv.DictReader(f) if r['role']=='D2_main']
assert len(raw)==36 and len({(r['h_nm'],r['d_nm']) for r in raw})==18
records=[]
for r in raw:
    h=float(r['h_nm'])*1e-9;d=float(r['d_nm'])*1e-9;w=float(r['w_nm'])*1e-9
    ref=float(r['K_m3']);dr=r['direction'];lower=h**3/12
    lc=(h**3+(h+d)**3)/24 if dr=='P' else h**3*(h+d)**3/(6*(h**3+(h+d)**3))
    beta=d/w
    factor=1/(1+1.7685*beta**1.6331) if dr=='P' else 1/(1+.4900*beta**.6990)
    values={'lower':lower,'LC':lc,'V2':lc*factor}
    rr={k:r[k] for k in ['run_id','direction','h_nm','d_nm','w_nm','P_nm','dx_nm','source']}
    rr['K_ref_m3']=ref
    for model,value in values.items():
        rr['K_'+model+'_m3']=value;rr[model+'_bias_percent']=100*(value/ref-1)
    assert abs(rr['LC_bias_percent']-float(r['LC_bias_percent']))<1e-9
    assert abs(rr['V2_bias_percent']-float(r['V2_bias_percent']))<1e-9
    assert rr['lower_bias_percent']<0
    rr['lower_closer_than_LC']=abs(rr['lower_bias_percent'])<abs(rr['LC_bias_percent'])
    rr['lower_closer_than_V2']=abs(rr['lower_bias_percent'])<abs(rr['V2_bias_percent'])
    records.append(rr)
summary={}
for dr in ['P','T']:
    rr=[r for r in records if r['direction']==dr];assert len(rr)==18
    summary[dr]={'count':len(rr),
       'mean_absolute_relative_bias_percent':{m:statistics.mean(abs(r[m+'_bias_percent']) for r in rr) for m in values},
       'maximum_absolute_relative_bias_percent':{m:max(abs(r[m+'_bias_percent']) for r in rr) for m in values},
       'lower_closer_than_LC_count':sum(r['lower_closer_than_LC'] for r in rr),
       'lower_closer_than_V2_count':sum(r['lower_closer_than_V2'] for r in rr)}
with (OUT/'comparison_36.csv').open('w',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=list(records[0]));writer.writeheader();writer.writerows(records)
(OUT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
protected=json.loads((OUT/'protected_inputs.json').read_text())
drift=[p for p,h in protected.items() if hashlib.sha256(Path(p).read_bytes()).hexdigest()!=h]
assert not drift
(OUT/'verification.json').write_text(json.dumps({'count':36,'geometries':18,'reference_dx_nm':5,
    'metric':'100*(K_formula/K_ref-1), compared by absolute value',
    'reproduced_saved_LC_and_V2_bias_count':72,'protected_input_count':len(protected),'changed_inputs':drift,
    'solver_calls':0,'fit_calls':0,'reserved_prediction_results_read':False,'raw_fields_read':False,
    'new_run_id':None,'formal_manuscripts_modified':False,'submission_ready':False,
    'scope':'retrospective arithmetic on known discrete references; not independent prediction or reference qualification'},indent=2)+'\n')
print(json.dumps(summary,ensure_ascii=False))

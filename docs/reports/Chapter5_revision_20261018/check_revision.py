#!/usr/bin/env python3
"""Check chapter text/number consistency and unchanged protected inputs only."""
from pathlib import Path
import csv
import hashlib
import json
import re
import statistics

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
record=json.loads((HERE/'revision_record.json').read_text())
target=Path(record['target']);text=target.read_text()
checks=[]
def check(name,condition):
    checks.append({'check':name,'passed':bool(condition)})
    if not condition:raise AssertionError(name)

check('Applied main chapter matches reviewed candidate',hashlib.sha256(target.read_bytes()).hexdigest()==record['after_sha256'])
for name,digest in record['protected_sources'].items():
    check('Protected input: '+name,hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest)
check('Latest merge base is preserved',hashlib.sha256((HERE/record['merge_base']).read_bytes()).hexdigest()==record['merge_base_sha256'])
check('Earlier concurrent snapshot is preserved',(HERE/'Chapter5_before.md').exists())
check('English and Chinese bodies present','## EN' in text and '## 中文' in text)
check('A/B/C retained in both languages',all(text.count('### '+c+'.')==2 for c in ['A','B','C']))
check('Display-math delimiters paired',sum(line.strip()=='$$' for line in text.splitlines())%2==0)
check('No accidental doubled LaTex escapes','\\\\' not in text)
check('Bold delimiters paired on every line',all(line.count('**')%2==0 for line in text.splitlines()))
check('Closing-speed sign corrected in both languages',text.count('=-\\mu V')>=2 and text.count('V=-\\dot h>0')>=2)
check('Project component mapping explicit in both languages',text.count('K_\\parallel=K_{yy}')>=2 and text.count('K_\\perp=K_{xx}')>=2)
check('Square-field weight assignment is explicit','along-groove weight is approximately 0.78' in text and '沿槽权重约0.78' in text)
check('No two-primary-time conventions mixed','primary time calculation interpolates each reference conductance' in text and 'supplementary table instead interpolates the already evaluated' in text)

audit=json.loads((ROOT/'docs/reports/Chapter5_mechanism_audit_20261018/evidence.json').read_text())
cases=audit['cases'];times=audit['times']
load_min=min(c['load_ratio'] for c in cases);load_max=max(c['load_ratio'] for c in cases)
corr_min=min(c['corrected_load_ratio'] for c in cases);corr_max=max(c['corrected_load_ratio'] for c in cases)
signed_median=(statistics.median(c['corrected_load_ratio'] for c in cases)-1)*100
numbers={'load_min':load_min,'load_max':load_max,'corrected_load_min':corr_min,'corrected_load_max':corr_max,'corrected_load_signed_median_pct':signed_median,
         'time_min':min(c['time_ratio'] for c in times),'time_max':max(c['time_ratio'] for c in times),
         'corrected_time_min':min(c['corrected_time_ratio'] for c in times),'corrected_time_max':max(c['corrected_time_ratio'] for c in times)}
for key in ['time_min','time_max','corrected_time_min','corrected_time_max','corrected_load_min','corrected_load_max']:
    token=f'{numbers[key]:.6f}'
    check('Same EN/CN audited number '+token,text.count(token)>=2)
check('Signed corrected median, not old minus-one percent',round(signed_median,2)==-2.12 and text.count('−2.12%')>=2)
for token in ['0.371464–0.477857','3.03%','17.99%']:
    check('Correct model-B resistance/frozen number '+token,text.count(token)>=2)

with (ROOT/'CASE/D_series/D3_squeeze_error_propagation/results/table2b_time_common_stroke.csv').open(encoding='utf-8-sig') as f:
    supplement=[r for r in csv.DictReader(f) if r['convention']=='pchip']
by_d={r['d_nm']:r for r in times}
max_diff=max(abs(by_d[int(r['d'])]['corrected_time_ratio']-float(r['t_cor'])) for r in supplement)
numbers['supplement_corrected_time_min']=min(float(r['t_cor']) for r in supplement)
numbers['supplement_corrected_time_max']=max(float(r['t_cor']) for r in supplement)
numbers['max_primary_vs_supplement_corrected_ratio_difference']=max_diff
check('Alternative S interpolation documented without replacing main chain',all(text.count(f'{numbers[k]:.6f}')>=2 for k in ['supplement_corrected_time_min','supplement_corrected_time_max']))
check('Supplement contrast arithmetic matches stated 0.162 percentage points',round(max_diff*100,3)==.162)
check('Exploratory V2 and uncertainty limitations retained','retrospective' in text and 'independent final' in text and 'discretization' in text and '事后' in text)
check('Unverified heat-pipe quantitative validation excluded','excluded from quantitative model validation' in text and '现有fRe图不作为定量模型验证证据' in text)
check('Human approval not claimed','作者审阅稿' in text and '不代表投稿放行' in text)
result={'checks':checks,'check_count':len(checks),'all_passed':all(x['passed'] for x in checks),'numbers_from_existing_evidence':numbers,
        'source_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'no_OpenLB_or_optimizer_execution':True,
        'scope':'Text/numeric consistency and protected-input hashes; no new scientific or numerical-gate validation.','submission_ready':False}
(HERE/'validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'all_passed':result['all_passed'],'check_count':len(checks),'corrected_time_ratio':[numbers['corrected_time_min'],numbers['corrected_time_max']],
                  'protected_inputs_unchanged':True,'submission_ready':False},ensure_ascii=False))

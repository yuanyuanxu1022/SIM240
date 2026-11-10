"""Summarise already-produced diagnostic CSVs; does not read raw fields."""
from pathlib import Path
import csv,json
p=Path(__file__).resolve().parent
def rows(n):return list(csv.DictReader((p/n).open()))
a=rows('positive_excess_diagnostic.csv');c=rows('strain_components.csv');e=rows('power_checks.csv')
key=[]
for r in e:
    if r['scheme']!='wall_quadratic' or float(r['d_nm'])<100:continue
    ident=[x for x in a if x['run_id']==r['run_id'] and x['scheme']==r['scheme']]
    comps=[x for x in c if x['run_id']==r['run_id'] and x['scheme']==r['scheme']]
    row={k:r[k] for k in ['run_id','direction','w_nm','dx_nm','strain_input_residual_percent','R_drive_over_R_LC','R_strain_over_R_LC']}
    for x in ident:row[x['term']+'_share_percent']=float(x['term_fraction_of_positive_sum'])*100
    row['positive_sum_vs_drive_excess_relative_percent']=100*(float(ident[0]['sum_terms_over_R_LC'])/float(ident[0]['drive_excess_over_R_LC'])-1)
    row['normal_strain_share_percent']=100*sum(float(x['fraction_of_strain']) for x in comps if x['component'].startswith('normal'))
    key.append(row)
columns=list(dict.fromkeys(k for r in key for k in r))
with (p/'key_results.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=columns);w.writeheader();w.writerows(key)
maxscheme=0
for x in a:
    if x['scheme']!='wall_quadratic' or float(x['d_nm'])<100:continue
    alt=next(y for y in a if y['run_id']==x['run_id'] and y['term']==x['term'] and y['scheme']=='odd_extension')
    maxscheme=max(maxscheme,100*abs(float(x['term_fraction_of_positive_sum'])-float(alt['term_fraction_of_positive_sum'])))
f=rows('field_checks.csv')
obj={'date':'2026-11-09','target_frames':10,'smooth_control_frames':2,
     'all_3D_field_y_variation_zero_at_stored_precision':all(float(x['y_variation_relative_to_umax'])==0 for x in f),
     'power_main_target_residual_range_percent':[min(float(r['strain_input_residual_percent']) for r in e if r['scheme']=='wall_quadratic' and float(r['d_nm'])>100),max(float(r['strain_input_residual_percent']) for r in e if r['scheme']=='wall_quadratic' and float(r['d_nm'])>100)],
     'positive_term_fraction_max_scheme_difference_pp':maxscheme,'key_results':key,
     'scope':'operator and spatial diagnostics, no independent causal attribution or formal Gate acceptance'}
(p/'summary.json').write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in obj.items() if k!='key_results'},ensure_ascii=False,indent=2))

from pathlib import Path
import csv,json,hashlib,math
ROOT=Path('/home/dell/yuanyuanxu/SIM240')
OUT=ROOT/'docs/reports/PAPER1_direction_review_20261113'
p=ROOT/'docs/reports/PAPER1_V2_coefficient_choice_audit_20261110/fixed_V2_primary36_checked.csv'
rows=list(csv.DictReader(p.open()));assert len(rows)==36
out={'role':'descriptive recomputation of saved data; no solver or reference requalification','DOE':{}}
for direction in ['P','T']:
 matrix=[[float(next(r for r in rows if float(r['h_nm'])==h and float(r['d_nm'])==d and r['direction']==direction)['V2_residual_percent']) for d in [25,50,75,100,120]] for h in [50,75,125]]
 avg=lambda xs:sum(xs)/len(xs)
 grand=avg([v for row in matrix for v in row]);hm=[avg(row) for row in matrix];dm=[avg([matrix[i][j] for i in range(3)]) for j in range(5)]
 total=sum((x-grand)**2 for row in matrix for x in row)
 sh=5*sum((x-grand)**2 for x in hm);sd=3*sum((x-grand)**2 for x in dm);si=sum((matrix[i][j]-hm[i]-dm[j]+grand)**2 for i in range(3) for j in range(5))
 assert abs((sh+sd+si)/total-1)<1e-12
 out['DOE'][direction]={'response':'signed V2 relative discrepancy versus 5nm OpenLB, percent','h_nm':[50,75,125],'d_nm':[25,50,75,100,120],'matrix':matrix,'h_means':hm,'d_means':dm,'equal_weight_sample_SS_shares_percent':{'h':100*sh/total,'d':100*sd/total,'interaction_remainder':100*si/total},'residual_df_with_full_interaction':15-1-2-4-8,'p_values_certified':False}
f=ROOT/'docs/reports/PAPER1_teacher_workorder_audit_20261112/current_fvm_v21_assessment.json';j=json.loads(f.read_text());out['saved_FVM_assessment']={'comparisons':j['comparisons'],'baseline':j['baseline'],'raw_fields_reintegrated_this_turn':False}
b=j['baseline'];comps={x['point']:x for x in j['comparisons'] if x.get('reference_accepted')}
a=comps['h75_d100_P']['Kref_m3']/comps['h75_d100_T']['Kref_m3'];assert abs(a-b['Aref'])<1e-12
assert abs((b['ALC']/a-1)*100-b['ALC_vs_reference_percent'])<1e-10
rs=[2.7847e-9,2.6893e-9,2.5976e-9,2.4243e-9,2.287e-9]
out['h125_reported_Ux_segment']={'source':'synthesis report, not newly retrieved server log','values':rs,'per_1000_ratios':[rs[1]/rs[0],rs[2]/rs[1],(rs[3]/rs[2])**.5],'interpretation':'positive decline is compatible with slow geometric convergence; no nonzero residual floor established; no runtime promise'}
paths=[p,f,ROOT/'docs/reports/PAPER1_action_list_20261113.md',ROOT/'docs/reports/PAPER1_synthesis_DOE_workorder_FVM_20261113/REPORT.md',ROOT/'docs/reports/PAPER1_teacher_workorder_audit_20261112/R1_R2_confirmation/R2_DECISION.json',ROOT/'CASE/paper1_fvm_stokes_reference_v2/PROTOCOL.md',ROOT/'docs/reports/PAPER1_literature_sync_20261113/DELIVERY_STATUS.json']
inputs=[dict(path=str(x.relative_to(ROOT)),sha256=hashlib.sha256(x.read_bytes()).hexdigest(),bytes=x.stat().st_size) for x in paths]
(OUT/'RECALC.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');(OUT/'INPUTS.json').write_text(json.dumps(inputs,ensure_ascii=False,indent=2)+'\n')
print('36 source records; 15-geometry descriptive decomposition per direction; saved baseline A checked; no numerical acceptance changes')

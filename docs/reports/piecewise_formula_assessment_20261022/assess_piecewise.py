#!/usr/bin/env python3
"""Assess geometry ratios and form bounded log-log interpolation from existing K.
No solver, optimizer, new simulation, or original file edits.
"""
from pathlib import Path
import argparse,csv,json,hashlib,math

def writecsv(path,items):
 with path.open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(items[0]));w.writeheader();w.writerows(items)
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--workspace',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
 src=args.workspace/'03_数据/00_数据索引/36项主方向数据_模型对照.csv';args.output.mkdir(parents=True,exist_ok=True)
 original=src.read_bytes();source_rows=list(csv.DictReader(src.open(encoding='utf-8-sig')));points=[]
 for r in source_rows:
  h,d,k,km=map(float,[r['h_nm'],r['d_nm'],r['K_m3'],r['local_model_K_m3']]);delta=d/120
  f=1/(1+1.7685*delta**1.6331) if r['direction']=='P' else 1/(1+.4900*delta**.6990)
  points.append({'h_nm':h,'d_nm':d,'direction':r['direction'],'h_over_w':h/120,'d_over_w':delta,'d_over_h':d/h,'total_height_over_w':(h+d)/120,'K_m3':k,'K_LC_m3':km,'F_required':k/km,'E_percent':100*(km/k-1),'V2_residual_percent':100*(f*km/k-1),'raw_result':r['result_path']})
 segments=[];loo=[]
 for dr in ['P','T']:
  for d in sorted({r['d_nm'] for r in points}):
   ps=sorted([r for r in points if r['direction']==dr and r['d_nm']==d],key=lambda r:r['h_nm'])
   for l,r in zip(ps[:-1],ps[1:]):
    s=math.log(r['K_m3']/l['K_m3'])/math.log(r['h_nm']/l['h_nm'])
    segments.append({'direction':dr,'d_nm':d,'h_left_nm':l['h_nm'],'h_right_nm':r['h_nm'],'K_left_m3':l['K_m3'],'K_right_m3':r['K_m3'],'exponent':s,'formula':'K=K_left*(h_nm/h_left_nm)^exponent; interval only; fixed d','left_raw_result':l['raw_result'],'right_raw_result':r['raw_result']})
   for j in range(1,len(ps)-1):
    l,m,r=ps[j-1:j+2];s=math.log(r['K_m3']/l['K_m3'])/math.log(r['h_nm']/l['h_nm']);pred=l['K_m3']*(m['h_nm']/l['h_nm'])**s
    loo.append({'direction':dr,'d_nm':d,'omitted_h_nm':m['h_nm'],'left_h_nm':l['h_nm'],'right_h_nm':r['h_nm'],'K_pred_m3':pred,'K_original_m3':m['K_m3'],'relative_error_percent':100*(pred/m['K_m3']-1),'interpretation':'within-depth retrospective interior leave-one-out; not independent final validation'})
 ranges={v:{'min':min(r[v] for r in points),'max':max(r[v] for r in points)} for v in ['h_over_w','d_over_w','d_over_h','total_height_over_w']}
 bounds=[]
 for dr in ['P','T']:
  for d in sorted({r['d_nm'] for r in points}):
   ps=[r for r in points if r['direction']==dr and r['d_nm']==d];q=[r['K_LC_m3']/r['K_m3'] for r in ps];lo,hi=min(q),max(q)
   bounds.append({'direction':dr,'d_nm':d,'n':len(ps),'best_single_F':2/(hi+lo),'minimax_sample_bound_percent':100*(hi-lo)/(hi+lo)})
 report={'input_sha256':hashlib.sha256(original).hexdigest(),'input_unchanged':src.read_bytes()==original,'n_direction_points':len(points),'n_geometries':len({(r['h_nm'],r['d_nm']) for r in points}),'ranges':ranges,'same_d_over_h_equal_1':[r for r in points if r['h_nm']==r['d_nm']],'h_independent_F_sample_bounds':bounds,'interpolation_segment_count':len(segments),'interior_loo':{dr:{'n':len([r for r in loo if r['direction']==dr]),'max_abs_error_percent':max(abs(r['relative_error_percent']) for r in loo if r['direction']==dr)} for dr in ['P','T']},'optimizer_run':False,'solver_run':False,'physical_breakpoint_determined':False,'new_theory_formula_validated':False}
 writecsv(args.output/'dimensionless_points.csv',points);writecsv(args.output/'interpolation_segments.csv',segments);writecsv(args.output/'interior_leave_one_out.csv',loo);(args.output/'assessment.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
 print(json.dumps({'interpolation_segments':len(segments),'interior_loo':report['interior_loo'],'input_unchanged':report['input_unchanged']},ensure_ascii=False))
if __name__=='__main__':main()

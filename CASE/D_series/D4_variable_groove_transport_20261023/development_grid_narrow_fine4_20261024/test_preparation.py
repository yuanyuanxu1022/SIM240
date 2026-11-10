#!/usr/bin/env python3
"""Meaningful read-only regression and refusal tests; never executes steady."""
from pathlib import Path
import argparse,copy,csv,importlib.util,json,math,os,resource,sys,tempfile
sys.dont_write_bytecode=True
import numpy as np
from numpy.lib.stride_tricks import sliding_window_view
HERE=Path(__file__).resolve().parent;CASE=HERE.parent;PROJECT=CASE.parents[2]
from window_metrics import metrics
import compare_grid as compare
import export_references as export
import run_narrow4 as runner

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();checks=[]
 def reject(label,fn):
  try:fn()
  except (RuntimeError,ValueError,FileNotFoundError,KeyError):checks.append(label);return
  raise AssertionError('not rejected: '+label)
 # Canonical whitelist and mutations, all other source rows excluded.
 selected=runner.validate_table();mock={'released':True,'allowed_case_ids':[r['planned_case_id'] for r in selected]}
 for r in selected:runner.validate_row(r,mock)
 other=[r for r in runner.csvrows(CASE/'protocol/candidate_cases.csv') if r['planned_case_id'] not in mock['allowed_case_ids']]
 for r in other:reject('role_rejected_'+r['planned_case_id'],lambda r=r:runner.validate_row(r,mock))
 for field,val in [('P_nm','999'),('direction','Q'),('h_nm','100'),('nu_m2_s','0.1'),('blind_geometry','True')]:
  bad=dict(selected[0],**{field:val});reject('mutated_row_'+field,lambda bad=bad:runner.validate_row(bad,mock))
 reject('RAM_insufficient',lambda:runner.resource_check(runner.policy(),available=4*1024**3-1,free=100*1024**3))
 reject('disk_insufficient',lambda:runner.resource_check(runner.policy(),available=20*1024**3,free=11*1024**3-1))
 for k in ['OMPI_COMM_WORLD_SIZE','PMI_SIZE','MV2_COMM_WORLD_SIZE']:reject('MPI_'+k,lambda k=k:runner.runtime_environment({},environ={k:'2'}))
 reject('OpenLB_root',lambda:runner.runtime_environment({},environ={'SIM240_OLB_ROOT':'/other'}))
 reject('wrong_batch',lambda:runner.ensure_new_batch('development_remaining14_20261024_v1'))
 reject('completed_case',lambda:runner.ensure_case_not_completed(runner.csvrows(CASE/'development_remaining14_20261024/stage_cases.csv')[0]))
 with tempfile.TemporaryDirectory() as tmp:
  path=Path(tmp)/'x';path.write_text('a');r={'bound_inputs_sha256':{str(path):runner.sha(path)}};runner.validate_binding(r);path.write_text('b');reject('bound_input_changed',lambda:runner.validate_binding(r))
  path.unlink();reject('bound_input_missing',lambda:runner.validate_binding(r))
  # Test relative binding from an unrelated cwd without changing project files.
  cwd=Path.cwd();os.chdir(tmp)
  try:runner.validate_binding({'bound_inputs_sha256':{str((HERE/'policy.json').relative_to(PROJECT)):runner.sha(HERE/'policy.json')}})
  finally:os.chdir(cwd)
 checks.append('relative_binding_independent_of_cwd')
 # Every original 5nm complete window, including threshold decisions and stopping point.
 window_count=0;maxdiff=0.;real_cases=0
 for directory in [PROJECT/'docs/reports/D4_remaining14_acceptance_20261024/scalar_acceptance',PROJECT/'docs/reports/D4_prediction_readiness_20261024/screen_acceptance']:
  for c in json.loads((directory/'field_cases.json').read_text()):
   out=Path(c['output']);data=np.loadtxt(out/'diagnostics.csv',delimiter=',',skiprows=1);header=next(csv.reader((out/'diagnostics.csv').open()));cols={k:data[:,i] for i,k in enumerate(header)}
   main=cols['J'];cross=-cols['Jx'] if c['row']['direction']=='P' else cols['Jy'];n=int(c['effective']['window_steps']);got=metrics(main,cross,n)
   windows=sliding_window_view(main,n);reference=[windows.std(axis=1,ddof=1)/np.abs(windows.mean(axis=1)),np.ptp(windows,axis=1)/np.abs(windows.mean(axis=1)),np.max(np.abs(sliding_window_view(cross,n)),axis=1)]
   for x,y in zip(got[:3],reference):assert np.array_equal(x,y);maxdiff=max(maxdiff,float(np.max(np.abs(x-y))))
   gate=(got[0]<=1e-6)&(got[1]<=5e-6)&(got[2]<=1e-12);assert gate[-1] and not gate[:-1].any()
   assert got[3]['max_dense_deviation_bytes']<=got[3]['work_budget_bytes']//2
   real_cases+=1;window_count+=len(got[0])
 # Long fine-grid window lengths and tiny physical flux; compare selected windows to long-double two-pass arithmetic.
 rng=np.random.default_rng(20261024)
 for n in [4050,16200]:
  data=1e-11*(1+2e-7*rng.standard_normal(n+150));cross=np.zeros_like(data);got=metrics(data,cross,n,work_bytes=1024**2)
  full=sliding_window_view(data,n)
  assert np.array_equal(got[0],full.std(axis=1,ddof=1)/np.abs(full.mean(axis=1)))
  for i in [0,47,150]:
   x=data[i:i+n].astype(np.longdouble);mu=x.mean();ref=np.sqrt(((x-mu)**2).sum()/(n-1))/abs(mu)
   assert math.isclose(got[0][i],float(ref),rel_tol=1e-10,abs_tol=1e-18)
  assert got[3]['max_dense_deviation_bytes']<=512*1024
  checks.append('long_window_'+str(n))
 reject('zero_window_mean',lambda:metrics(np.zeros(10),np.zeros(10),3))
 reject('workspace_too_small',lambda:metrics(np.ones(10),np.zeros(10),3,work_bytes=1))
 # Decimal threshold equality, outside points, observed order and partial/global scopes.
 policy=json.loads((HERE/'grid_policy.json').read_text())
 for q,want in [(['1.01','1.002','1'],'PASS_SENSITIVITY_MONOTONE'),(['1.010000000000001','1.002','1'],'FAIL_RESOLUTION_TARGET'),(['1.01','1.005','1'],'INCONCLUSIVE_TREND'),(['1.009','1.005000000000001','1'],'FAIL_RESOLUTION_TARGET'),(['1','1','1'],'PASS_SENSITIVITY_NEAR_FLAT'),(['1.004','.998','1'],'INCONCLUSIVE_TREND')]:assert compare.quantity(q,policy)['status']==want
 checks.append('Decimal_limit_equal_inside_outside')
 r=compare.quantity(['1.032','1.008','1.002'],policy);assert math.isclose(r['p'],2,abs_tol=1e-12) and math.isclose(r['Q_extrapolated'],1,abs_tol=1e-12)
 synth=[]
 for h,d,w in policy['geometries_h_d_w_nm']:
  for dx in policy['dx_nm_coarse_to_fine']:
   for dr in ['P','T']:synth.append(dict(h_nm=h,d_nm=d,w_nm=w,dx_nm=dx,direction=dr,K_m3=str((2 if dr=='P' else 1)*(1+.0005*(dx/1.25)**2)*1e-23),numerical_gate_pass=True,geometry_pass=True,independent_reference_accepted=True,run_id='synthetic'+str(len(synth)),acceptance_evidence='synthetic',evidence_bundle_sha256='synthetic'))
 assert compare.evaluate(synth,policy)['GRID_SENSITIVITY_TARGET']=='PASS'
 partial=compare.evaluate([r for r in synth if not(r['w_nm']==240 and r['dx_nm']==1.25)],policy)
 assert partial['narrow_two_geometry_gate']=='PASS' and partial['GRID_SENSITIVITY_TARGET']=='INCOMPLETE_OR_REFERENCE_INVALID'
 checks.append('partial_narrow_gate_does_not_release_global')
 bad=[dict(r,K_m3=str(float(r['K_m3'])*1.03)) if r['w_nm']==60 and r['dx_nm']==5 and r['direction']=='T' else r for r in synth if not(r['w_nm']==240 and r['dx_nm']==1.25)]
 judged=compare.evaluate(bad,policy)
 assert judged['narrow_two_geometry_gate']=='NOT_PASS' and any(x['status']=='FAIL' for x in judged['geometry_results'][:2])
 checks.append('narrow_failure_retained_even_when_wide_family_missing')
 checks.append('comparison_policy_and_numeric_helpers_identical_to_frozen_MID6')
 for name in ['compare_grid.py','grid_policy.json','window_metrics.py']:
  assert (HERE/name).read_bytes()==(CASE/'development_grid_mid6_20261024'/name).read_bytes()

 assert compare.evaluate(synth+[synth[0]],policy)['GRID_SENSITIVITY_TARGET']!='PASS'
 bundle=HERE/'evidence/upstream12_bundle.json';assert len(export.verify_bundle(bundle))==12
 with tempfile.TemporaryDirectory() as tmp:
  obj=json.loads(bundle.read_text());obj['rows'][0]['P_nm']='999';obj.pop('bundle_sha256');obj['bundle_sha256']=export.canonical_digest(obj);p=Path(tmp)/'forged.json';p.write_text(json.dumps(obj))
  reject('forged_period_even_with_recomputed_container_hash',lambda:export.verify_bundle(p))
  obj=json.loads(bundle.read_text());obj['rows'][0]['K_m3']='1';p.write_text(json.dumps(obj));reject('tampered_bundle_K',lambda:export.verify_bundle(p))
  obj=json.loads(bundle.read_text());obj['rows'][1]['run_id']=obj['rows'][0]['run_id'];obj.pop('bundle_sha256');obj['bundle_sha256']=export.canonical_digest(obj);p.write_text(json.dumps(obj));reject('duplicate_runid',lambda:export.verify_bundle(p))
 for file in HERE.glob('*.py'):__import__('ast').parse(file.read_text())
 result={'ok':True,'canonical_allowed':len(selected),'other_canonical_rows_rejected':len(other),'negative_and_semantic_checks':checks,'historical_cases_all_windows_compared':real_cases,'historical_windows_compared':window_count,'maximum_absolute_metric_difference':maxdiff,'future_window_lengths_tested':[4050,16200],'reference_Decimal_boundary_and_scope_checks_pass':True,'exported_upstream_references_source_checked':12,'max_RSS_KiB':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'formal_solver_runs':0}
 with a.output.open('x') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
 print(json.dumps({k:v for k,v in result.items() if k!='negative_and_semantic_checks'}))
if __name__=='__main__':main()

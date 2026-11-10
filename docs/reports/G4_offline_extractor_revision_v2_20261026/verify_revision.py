"""Static delivery/provenance audit only; no field loading or test execution."""
import ast
import hashlib
import json
from pathlib import Path
import re
import sys

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[2]
CODE=ROOT/'CASE/D_series/D4_variable_groove_transport_20261023/reference_backend_min18_20261025/offline_extractor_revision_v2_20261026'
OLD=CODE.parent/'offline_extractor_preparation_20261026'

def read(p):return json.loads(p.read_text())
def canonical(x):return json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def digest(x):return hashlib.sha256(canonical(x)).hexdigest()

def main():
 m=read(OUT/'source_manifest.json')
 for group,files in m.items():
  for p,h in files.items():assert sha(ROOT/p)==h,p
 for name in ('numerics.py','test_fixtures.py'):assert sha(CODE/name)==sha(OLD/name),name
 results=read(OUT/'fixture_results.json')
 assert results['unit_tests_run']==30 and results['regression_tests']==17 and results['new_revision_tests']==13
 assert results['failures']==results['errors']==results['skipped']==0
 log=(OUT/'fixtures_run1.log').read_text();assert sum(x.endswith(' ... ok') for x in log.splitlines())==30
 for p,h in results['code_sha256'].items():assert sha(ROOT/p)==h,p
 for p in CODE.glob('*.py'):ast.parse(p.read_text())
 t=ast.parse((CODE/'extractor.py').read_text())
 f=next(n for n in t.body if isinstance(n,ast.FunctionDef) and n.name=='extract_real_record')
 assert len(f.body)==1 and isinstance(f.body[0],ast.Raise)
 binding=read(OUT/'real_N8_binding_DRAFT.json');trust=read(OUT/'real_N8_trust_anchor_DRAFT.json')
 assert digest(binding)==trust['binding_sha256']
 assert binding['real_extraction_authorized'] is binding['solver_authorized'] is False and binding['approval'] is None
 assert sha(Path(binding['acceptance_path']))==trust['acceptance_sha256']
 assert sha(Path(binding['acceptance_inputs_path']))==trust['acceptance_inputs_sha256']
 accepted=read(Path(binding['acceptance_inputs_path']));record=Path(binding['record_root'])
 assert len(binding['inventory'])==48 and digest(binding['inventory'])==trust['inventory_sha256']
 for rel,h in binding['inventory'].items():assert accepted[str(record/rel)]==h and sha(record/rel)==h,rel
 for p,h in binding['code_sha256'].items():assert sha(Path(p))==h,p
 assert sha(Path(binding['spec_path']))==binding['spec_sha256']
 assert not Path(binding['analysis_output']).exists()
 for name,rc in [('independent_success',0),('independent_failure',2)]:
  base=OUT/name;out=base/'synthetic_analysis_output'
  assert int((base/'process.exit_code').read_text())==int((out/'analysis.exit_code').read_text())==rc
  status=read(out/'status.json');assert status['actual_N8_processed'] is status['RESULT_PASS'] is status['reference_qualified'] is False
  assert status['exit_code']==rc
  manifest=read(out/'output_manifest.json')
  for p,h in manifest['files'].items():assert sha(out/p)==h,(name,p)
  assert (out/'events.jsonl').is_file()
  if rc:
   assert status['status']=='SYNTHETIC_ANALYSIS_FAILED' and status['failure']['message']=='RECORD_BYTES_CHANGED'
   assert (out/'failure.json').is_file() and not (out/'metrics.json').exists()
  else:
   assert status['status']=='SYNTHETIC_METRICS_RECORDED'
   assert read(out/'checks.json')['status']=='SOFTWARE_CONSISTENCY_PASS'
 freeze=ROOT/'docs/reports/Correlation_selection_freeze_20261024'
 g4=read(freeze/'candidate_lock.json')
 for p,h in g4['bound_files'].items():assert sha(freeze/p)==h,p
 text=(OUT/'REPORT.md').read_text();width=None
 for link in re.findall(r'\]\(([^)]+)\)',text):
  if not link.startswith('http') and link!='verification.json':assert (OUT/link).is_file(),link
 for line in text.splitlines():
  if line.startswith('|'):
   n=len(re.findall(r'(?<!\\)\|',line))
   if width is None:width=n
   assert n==width,line
  else:width=None
 assert not any(n.split('.')[0] in {'numpy','scipy','ufl','petsc4py','dolfinx','extractor','numerics','binding','solver','worker','assembly'} for n in sys.modules)
 data=dict(status='STATIC_V2_DELIVERY_CHECK_PASS',source_counts={k:len(v) for k,v in m.items()},
   all_original_sources_and_actual_records_unchanged=True,G4_bound_files_unchanged=len(g4['bound_files']),
   unchanged_v1_numerical_core=True,unchanged_v1_regression_suite=True,python_sources=len(results['code_sha256']),
   unit_tests=30,regression_tests=17,new_revision_tests=13,unit_test_failures=0,unit_test_errors=0,
   independent_synthetic_processes={'success_exit':0,'expected_failure_exit':2},
   four_findings='IMPLEMENTED_AND_SYNTHETICALLY_VERIFIED',real_entry_unconditionally_closed=True,
   actual_N8_arrays_loaded=False,actual_N8_metrics_computed=False,actual_output_directory_created=False,
   original_acceptance_covers_all_48_record_files=True,solver_started=False,
   theory_criteria_changed=False,physical_thresholds_activated=False,strict_error_bound_established=False,
   NUMERICAL_GATE='NOT_EVALUATED',RESULT_PASS=False,geometry_PASS=None,reference_qualified=False,
   submission_ready=False,prediction_permission='HOLD')
 (OUT/'verification.json').write_text(json.dumps(data,indent=2)+'\n')
 print(data['status'],data['source_counts'],'30 unit tests + 2 synthetic process outcomes bound; actual processing closed.')

if __name__=='__main__':main()

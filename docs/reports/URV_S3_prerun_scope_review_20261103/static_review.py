"""Read-only S3 scope audit; writes only this report directory."""
from pathlib import Path
import json,csv,hashlib,sys,datetime
from zoneinfo import ZoneInfo
ROOT=Path('/home/dell/yuanyuanxu/SIM240');OUT=Path(__file__).resolve().parent
CASE=ROOT/'CASE/unseen_v2_reference_S2_reuse_v1';CHECK=ROOT/'CASE/unseen_v2_reference_checker_S2_reuse_v1'
load=lambda p:json.loads(Path(p).read_text())
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(n,d):(OUT/n).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def main():
 for n in ['SIM240_AI_CONTEXT.md','AI_HANDOFF_20261015.md']:(OUT/('before_'+n)).write_bytes((ROOT/'docs/reports'/n).read_bytes())
 release=CASE/'evidence/S2_formal_launch_release_LRP_v1_20261102_02.json';expected='d08297ebda69d9698d40762f778eb43299fa3c01c35e5591b6d31b4e06ef26cd';assert sha(release)==expected
 bound=load(release);assert all(sha(p)==h for p,h in bound['inputs_sha256'].items())
 protected={p:sha(p) for p in bound['inputs_sha256']}
 review=ROOT/'docs/reports/URV_S2_completed_review_20261103_095422'
 for tree in [review,CHECK,CASE/'runs',CASE/'analysis_results',CASE/'launch_attempts',CASE/'evidence']:
  for p in tree.rglob('*'):
   if p.is_file() and '__pycache__' not in p.parts:protected[str(p)]=sha(p)
 save('protected_inputs_before.json',protected)
 sys.path.insert(0,str(CHECK/'analysis'));import evidence,stage_s2
 stage_s2.verify_seal(release,expected);stage_s2.validate_formal_authority(bound)
 previous=load(review/'independent_review.json');assert previous['S2_SIX_RUN_ACCEPTANCE'] and previous['six_full_checker_replays_exact']
 matrix=list(csv.DictReader((CHECK/'common/case_matrix.csv').open()));s3=[r for r in matrix if r['stage']=='S3_REG_LINEARITY'];assert len(s3)==4
 rows=[];baseline=[]
 for direction in ['P','T']:
  rec=next(r for r in bound['prepared_runs'] if r['planned_case_id']==f'URV1_U_REG_{direction}_dx2p5_a100000');run=Path(rec['output_directory']);c=load(run/'completion.json');a=load(CASE/'analysis_results'/rec['run_id']/'acceptance.json')
  assert c['release_sha256']==expected and c['inputs_before_sha256']==c['inputs_after_sha256']==bound['inputs_sha256']
  assert a['completion_sha256']==sha(run/'completion.json') and a['RESULT_PASS'] and a['geometry_PASS'] and a['NUMERICAL_GATE']=='PASS'
  assert all(sha(run/p)==h for p,h in c['output_sha256'].items())
  baseline.append(dict(direction=direction,planned_case_id=rec['planned_case_id'],run_id=rec['run_id'],release_path=str(release),release_sha256=expected,config_path=rec['run_config_path'],config_sha256=rec['run_config_sha256'],completion_path=str(run/'completion.json'),completion_sha256=sha(run/'completion.json'),acceptance_path=str(CASE/'analysis_results'/rec['run_id']/'acceptance.json'),acceptance_sha256=sha(CASE/'analysis_results'/rec['run_id']/'acceptance.json'),K_m3=a['scalar']['K_m3'],baseline_reusable=True,rerun_required=False))
 for row in s3:
  t=ROOT/'docs/reports/Unseen_V2_reference_protocol_20261101/describe_only_templates'/(row['planned_case_id']+'.txt');cfg=evidence.kv(t);params=evidence.exact_parameters(cfg);g=evidence.geometry(cfg)
  b=next(r for r in baseline if r['direction']==cfg['direction']);basecfg=evidence.kv(b['config_path']);physics=[k for k in cfg if k not in ['mode','run_id','output_directory','acceleration_m_s2']];assert all(cfg[k]==basecfg[k] for k in physics)
  assert params['nodes']==368640 and params['window']==2592 and params['cap']==150528
  assert float(row['wall_cap_seconds'])==14400 and float(row['acceleration_m_s2'])==params['a']
  rows.append(dict(planned_case_id=row['planned_case_id'],actual_run_id=None,template=str(t),template_sha256=sha(t),direction=cfg['direction'],acceleration_m_s2=params['a'],pressure_gradient_equivalent_Pa_per_m=1000*params['a'],lattice_acceleration=params['a']*params['dt']**2/params['dx'],initial_J_half_force_expected_m2_s=params['H']*params['a']*params['dt']/2,parameters=params,static_geometry=g,wall_cap_seconds=14400,baseline_case_id=b['planned_case_id'],same_geometry_and_statistics_as_baseline=True))
  protected[str(t)]=sha(t)
 # Static-only compatibility findings: no invalid execution calls or contract mutation.
 findings=[dict(id='C01',status='REUSABLE_CONDITIONALLY',component='S1 native ELF',evidence='C++ accepts positive acceleration config, geometry and force direction from config; exact existing ELF/source/build closure verified. S3 native zero-step not yet run.'),dict(id='C02',status='INCOMPATIBLE_AS_IS',component='S2 stage_s2/run_S2',evidence='Exact S2 stage, six cases, a100000 identities, original B and RUN_IDS; current S2 outputs already used. S3 cannot use old command.'),dict(id='C03',status='INCOMPATIBLE_AS_IS',component='contracts/revision_s2_reuse',evidence='Source revision dispatch selects verify_s2_reuse requiring stage S2_REG_GRID, exact six and formal S2 authority. New stage-specific provenance adapter required in isolation.'),dict(id='C04',status='REUSABLE_WITH_STAGE_ADAPTER',component='original per-run scientific checker',evidence='Matrix already contains S3 cases and generic per-run arithmetic/VTK checks. Preserve scientific functions and common spec; adapt source provenance branch, not science.'),dict(id='C05',status='CROSS_RELEASE_STAGE_JOIN_REQUIRED',component='three-force control',evidence='Use each S2 baseline under its original release plus two S3 records per direction. Do not approve S2 baselines under S3 or edit old completion.'),dict(id='C06',status='OUT_OF_SCOPE',component='global aggregate/F04',evidence='Original aggregate requires 24 records and one same-stage release workflow cannot supply them; do not relax count or score V2. Stage-local linearity report may compute metric only.'),dict(id='C07',status='SEPARATE_AUTHORITY_REQUIRED',component='execution',evidence='S2 real authorization lists six S2 IDs, S3_authorized=false. This task permits read-only scope/protocol writing only.'),dict(id='C08',status='PROPOSED_NOT_EXECUTED',component='native zero-step and initial readback',evidence='Plan four configs x describe/precheck/initialize (12 zero calls) plus four actual initial-field reads. Requires later explicit native audit authorization; no new performance run proposed.')]
 save('four_configuration_review.json',rows);save('S2_baseline_references.json',baseline);save('compatibility_findings.json',findings)
 save('scope_decision.json',dict(protocol_id='S3-PR-v1',reviewed_at=datetime.datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),status='READ_ONLY_REVIEW_COMPLETE_NOT_IMPLEMENTATION',new_formal_cases=4,reused_S2_baselines=2,linearity_metric='(max(K_50000,K_100000,K_200000)-min(...))/mean(...)',linearity_limit=.001,proposed_order=[r['planned_case_id'] for r in rows],proposed_zero_calls=12,proposed_initial_field_reads=4,proposed_solver_hours_budget=16,checker_budget_hours_additional=4,actual_run_ids=[],simulation_authorized=False,native_zero_step_authorized=False,performance_time_stepping_authorized=False,formal_simulation_authorized=False,builds=0,native_calls=0,VTK_reads=0,software_tests_run=0,S3_started=False,MODEL_COMPARISON='NOT_EVALUATED',REFERENCE_QUALIFIED_FOR_CASE=False,physical_validation='NOT_EVALUATED',submission_ready=False))
 # Include exact static source locations in the evidence inventory.
 for p in [CASE/'scripts/run_S2.py',CASE/'scripts/prepare_S2.py',CHECK/'analysis/stage_s2.py',CHECK/'analysis/contracts.py',CHECK/'analysis/revision_s2_reuse.py',CHECK/'analysis/check_results.py',CHECK/'analysis/evidence.py',Path(bound['provenance']['native_sources'][0])]:protected[str(p)]=sha(p)
 save('reviewed_inputs_sha256.json',protected)
 assert all(sha(p)==h for p,h in protected.items())
 save('verification.json',dict(S3_SCOPE_REVIEW_COMPLETE=True,S3_RUN_READINESS='NOT_READY_STAGE_ADAPTATION_REQUIRED',S2_release_inputs_verified=2160,S2_baselines_reusable=2,four_templates_static_only=True,protected_files_unchanged=len(protected),native_calls=0,VTK_reader_calls=0,builds=0,CASE_writes=0,threshold_changes=0))
 print(json.dumps(dict(templates=len(rows),baseline_K=[r['K_m3'] for r in baseline],geometry=rows[0]['static_geometry'],protected=len(protected)),indent=2))
if __name__=='__main__':main()

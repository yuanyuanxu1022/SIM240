"""Synthetic read-only review probes; never native calls or genuine audit receipts.

R1 supplies synthetic metadata to audit_outputs. R2 isolates zero receipt content
checks from authority parsing using mocks, while preserving real file/hash checks.
All synthetic audit files exist only in a TemporaryDirectory and are labelled.
"""
from pathlib import Path
import sys,json,tempfile,copy
from unittest.mock import patch
ROOT=Path('/home/dell/yuanyuanxu/SIM240');OUT=Path(__file__).resolve().parent
CASE=ROOT/'CASE/unseen_v2_reference_S3_reuse_v1';CHECKER=ROOT/'CASE/unseen_v2_reference_checker_S3_reuse_v1'
sys.path.insert(0,str(CHECKER/'analysis'));sys.path.insert(0,str(CASE/'scripts'))
import stage_s3 as stage
import audit_S3_zero as audit
from evidence import sha,kv,exact_parameters
LABEL='SYNTHETIC_SOFTWARE_PROBE_NOT_NATIVE_OR_FIELD_EVIDENCE'

def main():
 d=json.loads((CASE/'evidence/preparation_A.json').read_text());record=next(r for r in d['zero_prepared_runs'] if r['mode']=='initialize');run=Path(record['output_directory']);cfg=kv(record['run_config_path']);p=exact_parameters(cfg)
 old=ROOT/'CASE/unseen_v2_reference_S2_reuse_v1/audits/URV_S2_ZERO_20261102_01/URV1_U_REG_P_dx2p5_a100000/initialize'
 effective=kv(old/'effective_config.txt');effective.update(run_id=record['run_id'],mode='initialize',acceleration_m_s2=cfg['acceleration_m_s2'],direction='parallel')
 result=kv(old/'result.txt');result.update(run_id=record['run_id'],J_vector_m2_s='0,'+str(p['H']*p['a']*p['dt']/2)+',0')
 boundary=kv(old/'boundary_audit.txt');probes=[]
 for name,wrong in [('valid_synthetic_metadata',{}),('wrong_effective_acceleration',dict(acceleration_m_s2='200000')),('wrong_effective_direction',dict(direction='perpendicular')),('wrong_effective_dx',dict(dx_m='5e-9')),('wrong_effective_nu',dict(nu_m2_s='2e-6')),('wrong_effective_formal_flag',dict(formal_simulation='true'))]:
  eff={**effective,**wrong}
  def supplied(path):
   path=Path(path)
   if path==run/'effective_config.txt':return eff
   if path==run/'result.txt':return result
   if path==run/'boundary_audit.txt':return boundary
   return kv(path)
  with patch.object(audit,'kv',side_effect=supplied):
   try:audit.audit_outputs(record);accepted=True;error=None
   except Exception as e:accepted=False;error=str(e)
  probes.append(dict(probe=name,accepted=accepted,error=error,fixture=LABEL))
 assert all(p['accepted'] for p in probes)
 # Isolate the field receipt association logic. Real authority/ELF not simulated as genuine evidence.
 with tempfile.TemporaryDirectory(prefix='SYNTHETIC_S3_RECEIPT_REVIEW_') as t:
  root=Path(t);folder=root/'audits'/stage.AUDIT_ID;folder.mkdir(parents=True)
  release=root/'SYNTHETIC_AUTHORITY_PLACEHOLDER.json';release.write_text(json.dumps(dict(fixture=LABEL)))
  fields={}
  for ident in stage.CASES:
   f=folder/('field_readback_'+ident+'.json');f.write_text(json.dumps(dict(fixture=LABEL,PASS=True,actual_reader=True,frames=[dict(J_m2_s=[0,0,0],note='inert synthetic field values, not an actual reader output')])))
   fields[ident]=f
  records=[]
  for ident in stage.CASES:
   for mode in stage.MODES:
    r=dict(planned_case_id=ident,mode=mode,run_id='SYNTHETIC_'+ident+'_'+mode,output='SYNTHETIC_ONLY',native_exit_code=0,collide_and_stream_calls=0,fixture=LABEL)
    if mode=='initialize':r.update(field_readback=str(fields[ident]),field_readback_sha256=sha(fields[ident]))
    records.append(r)
  manifest=folder/'audit_files_sha256.json';manifest.write_text(json.dumps({str(p):sha(p) for p in folder.iterdir() if p.is_file()}))
  receipt=folder/'verification.json'
  obj=dict(fixture=LABEL,audit_id=stage.AUDIT_ID,ZERO_STEP_AUDIT_PASS=True,binary_sha256=stage.ELF_SHA,actual_time_steps=0,steady_mode_invocations=0,native_describe=4,native_precheck=4,native_initialize=4,initialized_frames_read=4,audit_release_path=str(release),audit_release_sha256=sha(release),raw_manifest_path=str(manifest),raw_manifest_sha256=sha(manifest),records=records)
  results=[]
  for reuse in [False,True]:
   value=copy.deepcopy(obj)
   if reuse:
    one=fields[stage.CASES[0]]
    for r in value['records']:
     if r['mode']=='initialize':r.update(field_readback=str(one),field_readback_sha256=sha(one))
   receipt.write_text(json.dumps(value));inputs={str(p):sha(p) for p in [release,*folder.iterdir()] if p.is_file()}
   bound=dict(inputs_sha256=inputs,zero_audit_path=str(receipt),zero_audit_sha256=sha(receipt))
   with patch.object(stage,'CASE',root),patch.object(stage,'verify_seal',return_value={'fixture':LABEL}),patch.object(stage,'validate_zero_authority'):
    try:stage.verify_zero_receipt(bound);accepted=True;error=None
    except Exception as e:accepted=False;error=str(e)
   results.append(dict(probe='four_records_reuse_one_readback' if reuse else 'four_synthetic_readbacks_with_wrong_flux',accepted=accepted,error=error,fixture=LABEL,authority_checks_mocked=True,file_hash_checks_real=True))
  assert all(r['accepted'] for r in results)
 output=dict(label=LABEL,native_calls=0,VTK_calls=0,CASE_writes=0,R1=probes,R2=results,interpretation='Two content-check gaps reproduced; no claim that a genuine authorized native run produced these errors.')
 (OUT/'synthetic_gap_probes.json').write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n');print(json.dumps(output,ensure_ascii=False,indent=2))
if __name__=='__main__':main()

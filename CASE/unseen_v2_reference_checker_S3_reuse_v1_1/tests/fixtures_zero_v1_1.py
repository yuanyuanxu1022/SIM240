"""Inert synthetic zero files; never a native/audit/reader result or real authority."""
from pathlib import Path
import json,copy,sys
import numpy as np
CHECK=Path(__file__).resolve().parents[1];CASE=CHECK.parent/'unseen_v2_reference_S3_reuse_v1_1'
sys.path.insert(0,str(CHECK/'analysis'))
from evidence import sha,kv,exact_parameters,geometry
from stage_s3 import CASES,MODES,AUDIT_ID,ELF_SHA
from zero_evidence import expected_initial,payload_closure
LABEL='SYNTHETIC_SOFTWARE_ZERO_FIXTURE_NO_NATIVE_NO_READER_NO_AUTHORITY'
def writekv(path,d):Path(path).write_text(''.join(str(k)+'='+str(v)+'\n' for k,v in d.items()))
def writejson(path,d):Path(path).write_text(json.dumps(d)+'\n')
class ZeroFixture:
 def __init__(self,root):
  self.root=Path(root).resolve();self.folder=self.root/'audits'/AUDIT_ID;self.folder.mkdir(parents=True)
  self.release=self.root/'SYNTHETIC_AUTHORITY_PLACEHOLDER.json';writejson(self.release,dict(fixture=LABEL))
  self.plan=[];self.records=[];self.fields=[]
  for ident in CASES:
   a=50000 if ident.endswith('a50000') else 200000;direction='P' if '_P_' in ident else 'T'
   for mode in MODES:
    run=self.folder/ident/mode;run.mkdir(parents=True);rid=f'ZERO_{AUDIT_ID}_{ident}_{mode}'
    cfg=dict(mode=mode,run_id=rid,output_directory=str(run),direction=direction,dx_nm='2.5',h_nm='60.0',d_nm='80.0',w_nm='120',period_nm='240',Ly_nm='240',nu_m2_s='1e-06',acceleration_m_s2=str(a),window_tstar='0.75',max_time_H_diffusion='8',frame_tstar='0,0.01,0.02,0.05,0.1,0.2,0.5,1,2,4,8')
    writekv(run/'run_config.txt',cfg);writekv(run/'run_manifest.txt',dict(run_id=rid,mode=mode));p=exact_parameters(cfg);g=geometry(cfg)
    writekv(run/'effective_config.txt',dict(run_id=rid,mode=mode,direction='parallel' if direction=='P' else 'perpendicular',formal_simulation='false',h_m=p['h'],d_m=p['d'],w_m=p['w'],Lx_m=p['P'],Ly_m=p['Ly'],phi=.5,dx_m=p['dx'],dt_s=p['dt'],nominal_volume_m3=p['P']*p['Ly']*p['H'],plan_area_m2=p['P']*p['Ly'],window_steps=p['window'],maximum_steps=p['cap'],acceleration_m_s2=a,nu_m2_s=p['nu'],nx=p['nx'],ny=p['ny']))
    writejson(run/'process_receipt.json',dict(fixture=LABEL,independent_process_exit_code=0,timed_out=False,resource_stop_reason=None,elapsed_seconds=1.,solver_wall_cap_seconds=300));(run/'exit_code.txt').write_text('0\n');(run/'run.log').write_text(LABEL+'\n');writekv(run/'execution_audit.txt',dict(protocol='URV-v1',preparation_only_build=0,collide_and_stream_calls=0))
    if mode!='describe':
     b={k:g[k] for k in ['material_0','material_1','material_2','material_3','candidate_links']};b.update(valid_distance_links=g['candidate_links'],installed_links=g['candidate_links'],q_min=.5,q_max=.5,installed_q_min=.5,installed_q_max=.5,geometric_fallback_count=0,missing_fluid_neighbour_fallback_count=0,unresolved_link_count=0,geometry_PASS='true',q_audit_PASS='true');writekv(run/'boundary_audit.txt',b)
    rec=dict(planned_case_id=ident,run_id=rid,mode=mode,run_config_path=str(run/'run_config.txt'),run_config_sha256=sha(run/'run_config.txt'),output_directory=str(run));self.plan.append(rec)
    saved=dict(planned_case_id=ident,run_id=rid,mode=mode,output=str(run),native_exit_code=0,collide_and_stream_calls=0,fixture=LABEL)
    if mode=='initialize':
     J=expected_initial(cfg)
     writekv(run/'result.txt',dict(run_id=rid,formal_simulation='false',steps_completed=0,collide_and_stream_calls=0,NUMERICAL_GATE='NOT_EVALUATED',RESULT_PASS='false',finite='true',geometry_PASS='true',q_audit_PASS='true',exit_code=0,fluid_nodes=p['nodes'],frames_written=1,fluid_volume_m3=p['P']*p['Ly']*p['H'],nominal_volume_m3=p['P']*p['Ly']*p['H'],corrected_mass=1000*p['nodes']*p['dx']**3,density_delta=0,max_density_deviation=0,J_vector_m2_s=','.join(str(v) for v in J)))
     (run/'frame_index.csv').write_text('step,time_s,tstar,reason\n0,0,0,initial\n')
     vtk=run/'vtkData';(vtk/'data').mkdir(parents=True)
     (vtk/'test.pvd').write_text('<VTKFile><Collection><DataSet timestep="0" file="data/test.vtm"/></Collection></VTKFile>')
     (vtk/'data/test.vtm').write_text('<VTKFile><vtkMultiBlockDataSet><DataSet file="test.vti"/></vtkMultiBlockDataSet></VTKFile>')
     (vtk/'data/test.vti').write_text(LABEL+'\n')
     report=self.folder/('field_readback_'+ident+'.json');self.fields.append(report)
     writejson(report,dict(fixture=LABEL,PASS=True,actual_reader=True,solver_executed=False,velocity_units='m/s',pressure_units='Pa_periodic_perturbation',dissipation_units='m2/s3',frames=[dict(step=0,unique_fluid_nodes=p['nodes'],J_m2_s=J.tolist(),diagnostic_J_m2_s=J.tolist(),roundoff_bound_m2_s=(abs(J)*1e-7+1e-50).tolist(),pressure_range_Pa=[0.,0.],arrays=['material','velocity_m_s','pressure_Pa','dissipation_m2_s3'])],payload_sha256=payload_closure(vtk/'test.pvd',run)))
     writejson(report.with_suffix('.process.json'),dict(fixture=LABEL,independent_exit_code=0,timed_out=False,elapsed_seconds=.1));(self.folder/('field_reader_'+ident+'.log')).write_text(LABEL+'\n')
     saved.update(field_readback=str(report),field_readback_sha256=sha(report))
    self.records.append(saved)
  self.audit=dict(fixture=LABEL,audit_id=AUDIT_ID,ZERO_STEP_AUDIT_PASS=True,binary_sha256=ELF_SHA,native_describe=4,native_precheck=4,native_initialize=4,initialized_frames_read=4,actual_time_steps=0,steady_mode_invocations=0,records=self.records,preparation_A_sha256='a'*64,audit_release_path=str(self.release),audit_release_sha256=sha(self.release),formal_simulation_started=False,next_stage_started=False,NUMERICAL_GATE='NOT_EVALUATED',RESULT_PASS=False)
  self.refresh()
 def refresh(self):
  for r in self.records:
   if r['mode']=='initialize' and Path(r['field_readback']).exists():r['field_readback_sha256']=sha(r['field_readback'])
  self.manifest=self.folder/'audit_files_sha256.json';self.receipt=self.folder/'verification.json'
  hashes={str(p):sha(p) for p in self.folder.rglob('*') if p.is_file() and p not in (self.manifest,self.receipt)};writejson(self.manifest,hashes)
  self.audit.update(raw_manifest_path=str(self.manifest),raw_manifest_sha256=sha(self.manifest));writejson(self.receipt,self.audit)
  self.bound=dict(preparation_A_sha256='a'*64,inputs_sha256={str(p):sha(p) for p in [self.release,*self.folder.rglob('*')] if p.is_file()},zero_audit_path=str(self.receipt),zero_audit_sha256=sha(self.receipt))
  self.released=dict(fixture=LABEL,preparation_A_sha256='a'*64,zero_prepared_runs=self.plan)
 def change_kv(self,path,key,value):d=kv(path);d[key]=str(value);writekv(path,d)
 def change_json(self,path,change):d=json.loads(Path(path).read_text());change(d);writejson(path,d)

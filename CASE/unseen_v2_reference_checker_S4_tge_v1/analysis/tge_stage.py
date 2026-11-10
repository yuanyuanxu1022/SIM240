"""Isolated TGE preparation and zero-only authority. Never executes a program."""
from pathlib import Path
import json, re, sys

CHECKER=Path(__file__).resolve().parents[1]
ROOT=CHECKER.parents[1]
CASE=CHECKER.parent/'unseen_v2_reference_S4_tge_v1'
PARENT=CHECKER.parent/'unseen_v2_reference_S4_reuse_v1'
PARENT_CHECKER=CHECKER.parent/'unseen_v2_reference_checker_S4_reuse_v1'
sys.path.insert(0,str(PARENT_CHECKER/'analysis'))
from evidence import need, sha, kv, exact_parameters, geometry

STAGE='S4_T_TRANSVERSE_GRID_SUPPLEMENT'
REVISION='S4-TGE-PREP-v1'
ELF_SHA='5c3836e97c99feab88cd8e41773237f6ff642a10558f151b11e112563382b07b'
PARENT_SHA='e5f7de1e584b776f8cc9bf1dbb31f198422ce10984ba8ad7d729220afdcdd19b'
PARENT_RELEASE=PARENT/'evidence/S4_formal_launch_release_v1_20261104_01.json'
OLD_REVIEW=ROOT/'docs/reports/URV_S4_completed_review_20261104_143205'
RUN_ID='URV_S4_T_dx0p625_TGE_v1_20261104_01'
CASE_ID='URV1_U_THIN_T_dx0p625_a100000_SUPPLEMENT'
AUDIT_ID='URV_S4_TGE_ZERO_v1_20261104_01'
MODES=('describe','precheck','initialize')
ZERO_RESOURCES=dict(processes=1,threads=1,cuboids=1,overlap=3,
    per_process_address_space_GiB=8,required_available_RAM_GiB=12,
    required_initial_free_disk_GiB=100,required_before_each_call_free_disk_GiB=8,
    output_budget_GiB_per_call=4,native_call_cap_seconds=300,field_reader_cap_seconds=300)
FLAGS=('simulation_authorized','formal_simulation_authorized','native_zero_step_authorized',
       'initial_field_readback_authorized','performance_time_stepping_authorized',
       'automatic_retry_authorized','automatic_extension_authorized','S5_authorized')

def load(p):return json.loads(Path(p).read_text())

def canonical(p):
    p=Path(p)
    need(p.is_absolute() and p.is_file() and str(p)==str(p.resolve()),'missing/noncanonical input')
    need(not any(q.is_symlink() for q in (p,*p.parents)),'input symlink refused')
    return p

def covered(bound,p):
    p=canonical(p);need(bound['inputs_sha256'].get(str(p))==sha(p),'unbound/changed input: '+str(p));return p

def unchanged(bound):
    need(isinstance(bound.get('inputs_sha256'),dict) and bound['inputs_sha256'],'empty input closure')
    for p,h in bound['inputs_sha256'].items():
        need(re.fullmatch('[0-9a-f]{64}',h) is not None,'invalid input digest')
        need(sha(canonical(p))==h,'bound input drift: '+p)

def physics(cfg):
    expected={'direction':'T','dx_nm':'0.625','h_nm':'30.0','d_nm':'80.0','w_nm':'120',
        'period_nm':'240','Ly_nm':'240','nu_m2_s':'1e-06','acceleration_m_s2':'100000',
        'window_tstar':'0.75','max_time_H_diffusion':'8',
        'frame_tstar':'0,0.01,0.02,0.05,0.1,0.2,0.5,1,2,4,8'}
    need(set(cfg)==set(expected)|{'mode','run_id','output_directory'},'candidate schema changed')
    need(all(cfg[k]==v for k,v in expected.items()),'candidate physics/observation changed')
    return exact_parameters(cfg)

def validate_plan(bound):
    need(bound.get('stage')==STAGE and bound.get('revision')==REVISION,'wrong supplement stage')
    formal=bound.get('prepared_runs',[]);zeros=bound.get('zero_prepared_runs',[])
    need(len(formal)==1 and len(zeros)==3,'exact one formal plan and three zero plans required')
    expected=[(formal[0],RUN_ID,'steady',CASE/'runs'/RUN_ID/'steady')]
    expected += [(r,'ZERO_'+AUDIT_ID+'_'+m,m,CASE/'audits'/AUDIT_ID/CASE_ID/m) for r,m in zip(zeros,MODES)]
    for rec,rid,mode,out in expected:
        need(rec==dict(run_id=rid,planned_case_id=CASE_ID,mode=mode,output_directory=str(out),
             run_config_path=str(out/'run_config.txt'),run_config_sha256=bound['inputs_sha256'].get(str(out/'run_config.txt'))),
             'identity/order/output isolation changed')
        cfg=kv(covered(bound,rec['run_config_path']));physics(cfg)
        need(cfg['run_id']==rid and cfg['mode']==mode and cfg['output_directory']==str(out),'config identity changed')
        need(kv(covered(bound,out/'run_manifest.txt'))==dict(run_id=rid,mode=mode),'manifest changed')
    need(bound.get('zero_resource_proposal')==ZERO_RESOURCES,'zero resource proposal changed')
    need(bound.get('reader_path')==str(PARENT_CHECKER/'analysis/read_fields.py'),'exact frozen field reader required')
    need(bound.get('formal_solver_wall_cap_seconds') is None and bound.get('formal_checker_cap_seconds') is None,
         'formal budgets must remain undecided in this package')
    need(bound.get('original_S4_stage_accepted') is False and bound.get('reference_qualified') is False and
         bound.get('MODEL_COMPARISON')=='NOT_EVALUATED' and bound.get('physical_validation')=='NOT_EVALUATED' and
         bound.get('submission_ready') is False and bound.get('next_stage_started') is False,'scientific status promoted')
    need(bound.get('NUMERICAL_GATE')=='NOT_EVALUATED' and bound.get('RESULT_PASS') is False and
         bound.get('geometry_PASS') is None,'unexecuted preparation promoted per-run acceptance')
    need(bound.get('AI_may_start_solver') is False and bound.get('user_manually_starts') is True,
         'manual execution boundary changed')
    need(bound.get('proposed_grid_nm')==[2.5,1.25,.625] and bound.get('original_grid_nm')==[5,2.5,1.25],
         'supplement overwrote original grid family')
    need(all(bound.get(k) is False for k in FLAGS if k not in ('native_zero_step_authorized','initial_field_readback_authorized')),
         'this preparation interface forbids time stepping/retry/extension/S5')
    return zeros

def verify_history(bound):
    parent=load(covered(bound,PARENT_RELEASE));need(sha(PARENT_RELEASE)==PARENT_SHA,'wrong original release')
    need(all(bound['inputs_sha256'].get(p)==h for p,h in parent['inputs_sha256'].items()),'historical input closure omitted')
    from contracts import verify_provenance
    verify_provenance(parent)
    need(bound.get('provenance')==parent['provenance'],'same genuine build required')
    need(sha(covered(bound,parent['provenance']['native_binary']))==ELF_SHA,'same ELF required')
    review=load(covered(bound,OLD_REVIEW/'independent_review.json'))
    need(review['release_sha256']==PARENT_SHA and review['SIX_RUN_ACCEPTANCE'] is True and
         review['S4_GRID_CHECKS_PASS'] is False and review['S4_STAGE_ACCEPTED'] is False,'original failure record changed')
    original_grid=load(covered(bound,PARENT/'launch_attempts'/PARENT_SHA/'S4_grid_report.json'))
    need(original_grid['GRID_CHECKS_PASS'] is False and original_grid['directions'][1]['GRID_CHECKS_PASS'] is False,
         'original transverse FAIL erased')
    refs=bound.get('baseline_references',[])
    need([r.get('run_id') for r in refs]==['URV_S4_T_dx2p5_reuse_v1_20261103_01','URV_S4_T_dx1p25_reuse_v1_20261103_01'],
         'exact two transverse baselines required')
    for ref in refs:
        rec=next(r for r in parent['prepared_runs'] if r['run_id']==ref['run_id']);run=Path(rec['output_directory'])
        cp=covered(bound,run/'completion.json');ap=covered(bound,PARENT/'analysis_results'/ref['run_id']/'acceptance.json')
        need(ref==dict(run_id=rec['run_id'],release_path=str(PARENT_RELEASE),release_sha256=PARENT_SHA,
             completion_path=str(cp),completion_sha256=sha(cp),acceptance_path=str(ap),acceptance_sha256=sha(ap)),
             'baseline reference role/hash changed')
        c=load(cp);a=load(ap)
        need(a['RESULT_PASS'] is True and a['NUMERICAL_GATE']=='PASS' and a['geometry_PASS'] is True and
             a['independent_exit_code']==c['independent_process_exit_code']==0 and a['completion_sha256']==sha(cp),
             'baseline not independently accepted')
        need(c['release_sha256']==a['release_sha256']==PARENT_SHA and c['inputs_before_sha256']==c['inputs_after_sha256']==parent['inputs_sha256'],
             'baseline execution binding mismatch')
        actual={str(p.relative_to(run)) for p in run.rglob('*') if p.is_file() and p.name!='completion.json'}
        need(actual==set(c['output_sha256']),'baseline raw file set drift')
        for name,h in c['output_sha256'].items():need(sha(covered(bound,run/name))==h,'baseline raw drift')
    adoption=load(covered(bound,CASE/'evidence/preparation_adoption.json'))
    need(adoption['preparation_scope_adopted'] is True and adoption['user_instruction_verbatim']==
        '采用最小草案后，限定范围准备单条横槽补证的隔离接入与资源审查材料，原生审计、性能标定和正式计算仍分别授权。',
        'preparation adoption missing')
    need(all(adoption.get(k) is False for k in FLAGS),'preparation adoption grants execution')

def verify_seal(path,digest):
    path=canonical(path)
    need(path.parent==CASE/'evidence' and re.fullmatch('[0-9a-f]{64}',digest) is not None and sha(path)==digest,
         'external seal trust anchor/path mismatch')
    bound=load(path);need(bound.get('protocol_id')=='URV-v1' and bound.get('schema_version')=='S4-TGE-PREP-1',
                            'wrong preparation schema')
    unchanged(bound);validate_plan(bound);verify_history(bound)
    for tree in [CASE/'scripts',CASE/'common',CHECKER/'analysis',CHECKER/'tests']:
        for p in tree.rglob('*'):
            if p.is_file():covered(bound,p.resolve())
    if bound.get('kind')=='S4_TGE_PREPARATION_A_NOT_AUTHORIZATION':
        need(path==CASE/'evidence/preparation_A.json','wrong preparation A location')
        need(all(bound.get(k) is False for k in FLAGS),'preparation contains execution authority')
        need(bound.get('approved_run_ids')==bound.get('approved_runs')==bound.get('approved_audit_run_ids')==[] and
             bound.get('actual_audit_run_ids')==bound.get('actual_formal_run_ids')==[], 'preparation contains fictitious approved/executed identities')
    else:
        need(bound.get('kind')=='AUTHORIZED_S4_TGE_ZERO_RELEASE','unsupported executable release')
    return bound

def require_pristine(bound):
    for rec in bound['prepared_runs']+bound['zero_prepared_runs']:
        out=Path(rec['output_directory'])
        need(not out.is_symlink() and {p.name for p in out.iterdir()}=={'run_config.txt','run_manifest.txt'},
             'output used; no retry/overwrite')

def validate_zero_authority(bound,path):
    # This check precedes every write/process in the zero entry.
    need(bound.get('kind')=='AUTHORIZED_S4_TGE_ZERO_RELEASE' and bound.get('native_zero_step_authorized') is True and
         bound.get('initial_field_readback_authorized') is True,'separate explicit 3+1 authorization required')
    need(Path(path)==CASE/'evidence/S4_TGE_zero_launch_release_v1_20261104_01.json','wrong zero release identity')
    original=covered(bound,CASE/'evidence/preparation_A.json');prepared=load(original)
    need(bound.get('preparation_A_sha256')==sha(original),'original A not bound')
    covered(bound,original.with_suffix('.sha256'))
    need(all(bound['inputs_sha256'].get(p)==h for p,h in prepared['inputs_sha256'].items()),'zero release drops A inputs')
    need(bound['prepared_runs']==prepared['prepared_runs'] and bound['zero_prepared_runs']==prepared['zero_prepared_runs'],
         'zero changes prepared identities')
    need(bound.get('zero_resource_proposal')==prepared['zero_resource_proposal'] and
         bound.get('reader_path')==prepared['reader_path'],'zero changes resources or reader')
    need(bound.get('approved_runs')==bound.get('approved_run_ids')==[] and bound.get('actual_audit_run_ids')==bound.get('actual_formal_run_ids')==[],
         'zero release must not grant/claim formal work')
    need(bound.get('approved_audit_run_ids')==[r['run_id'] for r in prepared['zero_prepared_runs']], 'exact 3-call authorization required')
    for role,filename in [('zero_authorization','S4_TGE_zero_authorization_v1_20261104_01.json'),
                          ('zero_resource_decision','S4_TGE_zero_resource_decision_v1_20261104_01.json')]:
        ref=bound.get(role,{})
        p=covered(bound,ref.get('path',''));need(p==CASE/'evidence'/filename and sha(p)==ref.get('sha256'),'wrong authorization/resource evidence')
        value=load(p)
        need(value.get('stage')==STAGE and value.get('user_explicitly_authorized') is True and
             isinstance(value.get('user_instruction_verbatim'),str) and value['user_instruction_verbatim'].strip(),
             'actual scoped user declaration missing')
        if role=='zero_authorization':
            need(value.get('native_call_count')==3 and value.get('initial_field_read_count')==1 and
                 value.get('actual_time_steps')==0 and value.get('fail_stop_no_retry') is True and
                 value.get('approved_audit_run_ids')==bound['approved_audit_run_ids'],'authorization does not cover exact 3+1')
            need(value.get('formal_simulation_authorized') is False and value.get('performance_time_stepping_authorized') is False,
                 'zero authorization includes time stepping')
        else:
            need(value.get('resource_decision_accepted') is True and value.get('resources')==ZERO_RESOURCES,
                 'zero resource decision not adopted')

def static_summary(bound):
    cfg=kv(bound['prepared_runs'][0]['run_config_path']);p=physics(cfg)
    return dict(stage=STAGE,binding_check=True,solver_executed=False,prepared_formal_runs=1,
        planned_native_zero_calls=3,planned_initial_field_reads=1,parameters=p,
        original_S4_stage_accepted=False,reference_qualified=False,
        native_zero_step_authorized=bound['native_zero_step_authorized'],
        formal_simulation_authorized=False,performance_time_stepping_authorized=False)

"""Single-use creation of closed TGE identities/materials; never calls native tools."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import hashlib,json,shutil,sys
ROOT=Path('/home/dell/yuanyuanxu/SIM240');OUT=Path(__file__).resolve().parent
CASE=ROOT/'CASE/unseen_v2_reference_S4_tge_v1';CHECKER=ROOT/'CASE/unseen_v2_reference_checker_S4_tge_v1'
sys.path.insert(0,str(CHECKER/'analysis'))
import tge_stage as s
load=lambda p:json.loads(Path(p).read_text())
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(path,v):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def textfile(path,t):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x') as f:f.write(t)

old=load(s.OLD_REVIEW/'protected_inputs_and_outputs.json')
for tree in [s.OLD_REVIEW,ROOT/'docs/reports/URV_S4_transverse_disposition_review_20261104_145410',
             ROOT/'docs/reports/URV_S4_grid_failure_disposition_20261104']:
    for p in tree.rglob('*'):
        if p.is_file():old[str(p)]=sha(p)
assert all(sha(p)==h for p,h in old.items())
save(OUT/'protected_old_files.json',old)
parent=load(s.PARENT_RELEASE)
adopt=dict(protocol_id='S4-TDR-v1',adopted_preparation_id='S4-TGE-PREP-v1',preparation_scope_adopted=True,
    instruction_source='USER_TYPED_CURRENT_TURN',verbatim_recorded_from_typed_sentence=True,
    user_instruction_verbatim='采用最小草案后，限定范围准备单条横槽补证的隔离接入与资源审查材料，原生审计、性能标定和正式计算仍分别授权。',
    preparation_implementation_authorized=True,software_checks_authorized=True,
    software_checks_basis='Necessary reversible verification of the adopted isolated preparation; no native/reader calls.',
    **{k:False for k in s.FLAGS})
save(CASE/'evidence/preparation_adoption.json',adopt)

template=s.kv(s.PARENT/'runs/URV_S4_T_dx1p25_reuse_v1_20261103_01/steady/run_config.txt')
def identity(rid,mode,out):
    out.mkdir(parents=True,exist_ok=False)
    cfg=dict(template,mode=mode,run_id=rid,output_directory=str(out),dx_nm='0.625')
    p=out/'run_config.txt';textfile(p,''.join(k+'='+v+'\n' for k,v in cfg.items()))
    textfile(out/'run_manifest.txt',f'run_id={rid}\nmode={mode}\n')
    return dict(run_id=rid,planned_case_id=s.CASE_ID,mode=mode,output_directory=str(out),
        run_config_path=str(p),run_config_sha256=sha(p))
formal=identity(s.RUN_ID,'steady',CASE/'runs'/s.RUN_ID/'steady')
zeros=[identity('ZERO_'+s.AUDIT_ID+'_'+m,m,CASE/'audits'/s.AUDIT_ID/s.CASE_ID/m) for m in s.MODES]
save(CASE/'evidence/identity_plan.json',dict(prepared_runs=[formal],zero_prepared_runs=zeros))
refs=[]
for rid in ['URV_S4_T_dx2p5_reuse_v1_20261103_01','URV_S4_T_dx1p25_reuse_v1_20261103_01']:
    cp=s.PARENT/'runs'/rid/'steady/completion.json';ap=s.PARENT/'analysis_results'/rid/'acceptance.json'
    refs.append(dict(run_id=rid,release_path=str(s.PARENT_RELEASE),release_sha256=s.PARENT_SHA,
        completion_path=str(cp),completion_sha256=sha(cp),acceptance_path=str(ap),acceptance_sha256=sha(ap)))
save(CASE/'evidence/baseline_references.json',refs)
prior=ROOT/'docs/reports/URV_S4_transverse_disposition_review_20261104_145410'
audit=load(prior/'existing_evidence_audit_v1_1.json');params=s.physics(s.kv(formal['run_config_path']))
static_geo=s.geometry(s.kv(formal['run_config_path']))
save(CASE/'evidence/static_parameters.json',dict(parameters=params,geometry_prediction=static_geo,
    volume_arithmetic= audit['volume_static_path'][-1],evidence_kind='SOFTWARE_ARITHMETIC_NOT_NATIVE_AUDIT',
    geometry_PASS=None,NUMERICAL_GATE='NOT_EVALUATED',RESULT_PASS=False))
env=load(parent['provenance']['build_environment'])
reuse=dict(native_binary=parent['provenance']['native_binary'],native_binary_sha256=sha(Path(parent['provenance']['native_binary'])),
    native_sources_sha256={p:sha(Path(p)) for p in parent['provenance']['native_sources']},
    genuine_build_environment=parent['provenance']['build_environment'],build_environment_sha256=sha(Path(parent['provenance']['build_environment'])),
    original_compile_exit_code=env['compile_exit_code'],new_builds=0,new_native_calls=0,
    dependency_count=len(env['dependency_sha256']),link_library_count=len(env['link_library_sha256']),
    dynamic_library_count=len(env['dynamic_library_sha256']),openlb_version=env['openlb_version'],
    zero_evidence_implementation=str(s.PARENT_CHECKER/'analysis/zero_evidence_s4.py'),
    field_reader=str(s.PARENT_CHECKER/'analysis/read_fields.py'),
    unchanged_scientific_rules=str(s.PARENT_CHECKER/'common/acceptance_spec.json'),
    runtime_native_compatibility='NOT_AUDITED_FOR_NEW_GRID')
assert reuse['native_binary_sha256']==s.ELF_SHA
save(CASE/'evidence/source_reuse.json',reuse)
save(CASE/'common/zero_resource_proposal.json',dict(kind='PROPOSAL_NOT_ADOPTED_RESOURCE_AUTHORITY',resources=s.ZERO_RESOURCES,
    resource_decision_accepted=False,user_explicitly_authorized=False))
save(CASE/'common/supplement_grid_plan.json',dict(original_grid_nm=[5,2.5,1.25],original_GRID_CHECKS_PASS=False,
    prospective_supplement_grid_nm=[2.5,1.25,.625],direction='T',r=2,Fs=1.25,
    relative_difference_floor=1e-14,positive_finite_p_required=True,monotonic_required=True,
    medium_fine_relative_change_max=.01,GCI_fine_estimate_max=.01,
    strict_error_bound_established=False,reference_qualification_rule='SEPARATE_SCOPE_PENDING',
    formal_result_controller_implemented=False,model_comparison='NOT_EVALUATED',S5_authorized=False))
mem=int(next(l.split()[1] for l in Path('/proc/meminfo').read_text().splitlines() if l.startswith('MemAvailable:')))*1024
resource_review=dict(snapshot_at=datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),MemAvailable_bytes=mem,
    disk_free_bytes=shutil.disk_usage(CASE).free,candidate_fluid_nodes=params['nodes'],
    one_population_set_fluid_only_bytes=params['nodes']*19*8,
    conditional_cost=audit['conditional_cost'],candidate_peak_RSS='NOT_MEASURED',candidate_throughput='NOT_MEASURED',
    zero_resource_proposal=s.ZERO_RESOURCES,zero_resource_proposal_adopted=False,
    formal_solver_wall_cap_seconds=None,formal_checker_cap_seconds=None,
    formal_resource_readiness='NOT_READY_NATIVE_ZERO_AND_CANDIDATE_RESOURCE_EVIDENCE_PENDING',
    performance_interface='NOT_IMPLEMENTED_NOT_AUTHORIZED',resources_reserved=False,
    required_before_future_authority=['review_seal_and_current_resources','explicit_3_plus_1_authority_with_300s_and_8GiB_proposal',
        'accept_actual_zero_and_initial_readback','separately_prepare_and_authorize_single_finite_PERF',
        'decide_formal_budget_from_evidence_and_obtain_distinct_formal_authority'])
save(CASE/'evidence/resource_review.json',resource_review)
textfile(CASE/'README.md','''# S4 单条横槽网格补证准备 A

采用S4-TDR-v1最小准备范围，计划T/0.625nm，引用原T/2.5与1.25nm。
复用S1原ELF，未改C++、未构建；新阶段身份与3＋1零步接口在本目录隔离。
准备A全部执行权限关闭。预留正式/零步身份只表示输入准备，不表示启动。
inspect_preparation.py默认只读；audit_zero_tge.py默认只读，--execute必须另有真实3＋1授权、独立资源采用和SHA绑定。
原生审计、读场、有限PERF和正式计算分别授权。当前无PERF/正式求解控制器或启动命令。
原S4横槽网格FAIL永久保留；新三档仅是追加验证计划，不能覆盖原24条或自动进S5。
请先读PROTOCOL.md及evidence/preparation_A.json；原1%门槛、原始数据与旧合同不改。
''')
textfile(CASE/'PROTOCOL.md','''# S4-TGE-PREP-v1：已采用的最小隔离准备范围

本轮用户授权准备及其必要软件/静态验证，不授权任何原生、读场、PERF或正式求解。此文件不是启动合同。

## 物理与身份

仅T横槽+x，h30/d80/w120/P=Ly240nm，dx0.625nm，平均H70nm，a100000m/s²、nu1e-6m²/s、rho1000kg/m³、mu.001Pa·s、tau1、D3Q19_FORCE/ForcedBGK、x/y周期及Bouzidi静止无滑移。
J按平面面积归一（m²/s），K=nuJ/a（m³），U=J/H，R=mu/K；半步体力、MRP/A1质量与体积路径保持。S0专用h75密度捕获不适用。
同一S1 ELF及真实构建来源只读复用；原native_sources/Makefile不改、不重编译。
计划正式run_id=URV_S4_T_dx0p625_TGE_v1_20261104_01，planned_case_id含SUPPLEMENT，不属于原24条。正式只预留config/manifest，不提供执行入口。

## 准备A与软件边界

新stage/配置/只读检查/零步控制器/零步结果检查在新CASE隔离，原科学evidence、zero_evidence和read_fields以原绝对路径与指纹引用，不拷贝改写门槛。
准备A输入清单包含原完整构建/输入、原S4六条和失败报告、旧两基准的完成/接受、准备采用证据、全部新脚本/配置与已结束的软件检查记录；不绑定未来活动日志。
必要软件检查使用参数/权限/路径的拒绝用例与mock，禁止启动原生或pvpython。准备检查不得拿--execute做连通性测试。

## 后续3＋1（当前未授权）

仅describe/precheck/initialize各1次，全部推进0步，initialize后读回1份真实初态场。顺序固定、失败即停、不重试、不进入性能或正式。
建议每次原生和读取各300s、进程地址空间8GiB，12GiB可用RAM、首批100GiB/每次8GiB空闲盘、单次4GiB输出，1进程/1线程/1cuboid/overlap3。此为未采用资源提案；执行合同须独立绑定真实用户3＋1授权和该资源方案采用，不从旧S4许可继承。
执行前核A与当时资源、3个输出目录仍净。独立receipt/退出码、collideAndStream=0、几何/材料/链/q/体积、半步力初态、VTK闭包/单位/积分关联按原R1/R2检查。候选几何与峰值内存不能由静态预测替代。

## 新旧网格与科学停点

原5/2.5/1.25nm三档FAIL保持。新2.5/1.25/0.625nm追加分支只在独立采用/授权/正式完成接受后评价；r2/Fs1.25、差同号非近零、p正有限、中细差和GCI各≤1%全部保持。
本准备不实现正式预算、正式结果控制器、跨阶段聚合或新参考资格放行；均在候选接入/资源证据之后另定范围。没有以原12h自动改为38.5h或48h。
3＋1通过后仍须独立准备/授权有限PERF及正式计算。未授权时入口拒绝原生；reference_qualified=false、MODEL_COMPARISON/physical_validation未评价、submission_ready=false、S5未启动。
''')
textfile(CHECKER/'README.md','''# S4 TGE 隔离接入检查

analysis/tge_stage.py核对封存、精确单配置与3个零步身份、原两条横槽接受、原S4 FAIL及同一ELF来源。
analysis/check_zero_tge.py只读复核已经结束的3＋1原始证据，不执行原生或场读取。
科学算术/R1-R2/读场器均引用原S4冻结文件；本目录不改原科学阈值。
正式结果与补充网格控制器尚未实现，必须在资源决策后另立接口；当前不接受原24条聚合或参考资格升级。
''')

inputs=dict(old)
for tree in [CASE/'scripts',CASE/'common',CASE/'evidence',CHECKER]:
    for p in tree.rglob('*'):
        if p.is_file() and '__pycache__' not in p.parts:inputs[str(p.resolve())]=sha(p)
for p in [CASE/'README.md',CASE/'PROTOCOL.md',s.PARENT_RELEASE,s.PARENT_RELEASE.with_suffix('.sha256')]:inputs[str(p)]=sha(p)
for rec in [formal,*zeros]:
    for p in Path(rec['output_directory']).iterdir():inputs[str(p)]=sha(p)
candidate=dict(protocol_id='URV-v1',schema_version='S4-TGE-PREP-1',stage=s.STAGE,revision=s.REVISION,
    kind='S4_TGE_PREPARATION_A_NOT_AUTHORIZATION',**{k:False for k in s.FLAGS},
    prepared_runs=[formal],zero_prepared_runs=zeros,approved_run_ids=[],approved_runs=[],approved_audit_run_ids=[],
    actual_audit_run_ids=[],actual_formal_run_ids=[],original_S4_stage_accepted=False,
    proposed_grid_nm=[2.5,1.25,.625],original_grid_nm=[5,2.5,1.25],baseline_references=refs,
    provenance=parent['provenance'],reader_path=str(s.PARENT_CHECKER/'analysis/read_fields.py'),
    zero_resource_proposal=s.ZERO_RESOURCES,formal_solver_wall_cap_seconds=None,formal_checker_cap_seconds=None,
    NUMERICAL_GATE='NOT_EVALUATED',RESULT_PASS=False,geometry_PASS=None,reference_qualified=False,
    MODEL_COMPARISON='NOT_EVALUATED',physical_validation='NOT_EVALUATED',submission_ready=False,
    next_stage_started=False,zero_audit_status='NOT_EXECUTED',performance_status='NOT_IMPLEMENTED_NOT_AUTHORIZED',
    formal_interface_status='NOT_IMPLEMENTED_BUDGET_PENDING',AI_may_start_solver=False,user_manually_starts=True,
    external_history_independently_verified=False,author_confirmation_scope=parent['author_confirmation_scope'],
    inputs_sha256=inputs)
s.validate_plan(candidate);s.verify_history(candidate);s.require_pristine(candidate)
for p in [*list((CASE/'scripts').glob('*.py')),*list((CHECKER/'analysis').glob('*.py')),*list((CHECKER/'tests').glob('*.py'))]:
    compile(p.read_text(),str(p),'exec')
save(OUT/'candidate_preparation.json',candidate)
save(OUT/'materialization_audit.json',dict(new_native_calls=0,new_builds=0,VTK_calls=0,formal_runs=0,
    source_reuse_pass=True,syntax_checks_pass=True,planned_parameters=params,protected_old_files=len(old)))
print(json.dumps(dict(candidate=str(OUT/'candidate_preparation.json'),inputs=len(inputs),
    native_calls=0,builds=0,zero_prepared=3,formal_prepared=1),indent=2))

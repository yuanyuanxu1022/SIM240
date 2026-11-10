"""Finalize issuance documents and handoff; no execution or status polling."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from unittest.mock import patch
import json
import sys

ROOT=Path('/home/dell/yuanyuanxu/SIM240')
OUT=Path(__file__).resolve().parent
CASE=ROOT/'CASE/unseen_v2_reference_S4_reuse_v1'
CHECK=ROOT/'CASE/unseen_v2_reference_checker_S4_reuse_v1'
sys.path.insert(0,str(CHECK/'analysis'))
from evidence import sha,need
import stage_s4 as stage


def load(p):return json.loads(Path(p).read_text())
def save(p,d):
    with Path(p).open('x') as f:json.dump(d,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')


def main():
    v=load(OUT/'verification.json');pre=load(OUT/'prebinding_verification.json')
    release=Path(v['release_path']);digest=v['release_sha256']
    with patch('subprocess.Popen',side_effect=AssertionError('No process during issuance reporting')):
        bound=stage.verify_seal(release,digest);stage.validate_formal_authority(bound)
    need(release.with_suffix('.sha256').read_text().strip()==digest,'release sidecar drift')
    protected=load(OUT/'protected_files_before.json')
    need(all(sha(p)==h for p,h in protected.items()),'old evidence drift')
    stage.require_pristine(bound['prepared_runs'])
    need(not (CASE/'launch_attempts').exists() and not (CASE/'analysis_results').exists(),'formal execution has begun')
    need(not Path(v['controller_log_path']).exists(),'controller log appeared before delivery')
    auth=load(v['authorization_path']);decision=load(v['adopted_resource_decision_path'])
    need(auth['user_instruction_verbatim']=='现在采用并授权完整六条；生成合同和命令，由我手动启动','authorization mismatch')
    need(decision['resource_decision_accepted'] is True and decision['user_instruction_verbatim']==auth['user_instruction_verbatim'],'adoption mismatch')
    new_paths={str(release),str(release.with_suffix('.sha256')),v['authorization_path'],v['adopted_resource_decision_path']}
    now_files={str(p) for folder in (CASE,CHECK) for p in folder.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
    old_files={p for p in protected if Path(p).is_relative_to(CASE) or Path(p).is_relative_to(CHECK)}
    need(now_files-old_files==new_paths,'unexpected CASE additions')
    stamp=datetime.now(ZoneInfo('Asia/Shanghai')).isoformat()
    memory_GiB=pre['resources']['MemAvailable_bytes']/1024**3
    disk_GiB=pre['resources']['disk_free_bytes']/1024**3
    rows='\n'.join(f"|{i}|`{r['run_id']}`|{[1,1,4,4,12,12][i-1]}h|1h|" for i,r in enumerate(bound['prepared_runs'],1))
    report=f'''# 正式S4六条：真实授权、资源采用与独立执行绑定

签发后核对时间：{stamp}。结论：用户已明确采用S4-FRD-v1并授权完整六条，独立正式执行release已准备并通过只读验收，唯一命令见START_COMMAND.txt；**AI未执行该命令，正式计算未启动**。

## 1. 真实授权及采用来源

question_item_id：`["request_user_input_async","call_a2f8d135b2a942e78a70d8438206254e",0]`。用户实际选择：“{auth['user_instruction_verbatim']}”。完整问题与实际答复原样记录在{v['authorization_path']}，SHA `{v['authorization_sha256']}`。

授权明确覆盖：采用S4-FRD-v1；5/2.5/1.25nm每档P→T六条；原1/4/12h逐条求解上限；每条外层标准独立检查（含保存场读回）1h；前条完整接受才继续，第四条后自动进细格；暂不另做PERF，接受细格12h可能超时而批次不完整；失败停、不重试/加时/进S5；AI只准备合同和命令、用户手动启动。求解34h、检查另最多6h，文件/清理另计，不保证40h完成。

授权来自实际选项答复，verbatim_recorded_from_typed_sentence=false；不伪造一段用户手写的扩展原话。此前“获得授权后”的条件指令与本次实际授权分别保留。原资源候选文件仍accepted=false不修改；本次另存真实采用记录{v['adopted_resource_decision_path']}，SHA `{v['adopted_resource_decision_sha256']}`。采用记录本身不是可执行release，正式权限由下述独立release承载。

## 2. 正式release及身份

路径：`{release}`；SHA256 `{digest}`，输入3284项；kind=AUTHORIZED_EXECUTION_LAUNCH_RELEASE，stage=S4_THIN_GRID。release有独立.sha256侧文件，完整继承原B3248输入，并绑定B/侧文件、真实授权/采用、S4-FRD审查与新运行前核对等不可变证据。

|顺序|精确正式run_id|求解上限|独立检查外层等待|
|---:|---|---|---|
{rows}

上述身份沿用原B，日期20261103不改，实际正式身份仍空。approved_runs/approved_run_ids精确同序六条；approved_audit_run_ids为空。原18个actual_audit及6初态读取是既有完成证据，不授权重做。

simulation_authorized/formal_simulation_authorized=true；native_zero/initial_field_readback/PERF/retry/extension/S5均false、AI_may_start_solver=false、user_manually_starts=true。零步专用initial_field_readback=false不排除本次真实正式授权内的标准检查器保存场读取。

## 3. 已完成运行前核对

- 原B SHA `7ca2ce3c27076a80d7d692bb13f3030854cf44b683dfe6bcec54ed15c288b06c`及3248输入不变，原18＋6收据、逐条原始文件/R1R2及完整独立接受文件核对通过。
- 真实B/来源/当前3284输入、formal_resource_decision门、formal授权、原科学checker binding均通过。默认run_S4只读CLI退出0、solver_executed=false、zero_audit_status=PASSED、精确六ID；受控检查子进程调用0。没有用已授权release的--execute做验证。
- formal release当zero、关闭B当formal、错误外部SHA均被拒绝；原3288项保护文件不变。包内只新增授权、资源采用、正式release及其侧文件4项，无源码、配置、门槛、旧合同改动。
- 同S1 ELF SHA `5c3836e97c99feab88cd8e41773237f6ff642a10558f151b11e112563382b07b`；OpenLB版本 `{pre['openlb_version']}`。历史构建/1392依赖/3链接及15动态库来源保持，清除LD_LIBRARY_PATH/LD_PRELOAD后实际ldd解析15库路径/指纹与构建一致；未重新编译或调用原生程序。
- 最新签发前快照{pre['checked_at']}：主机{pre['host']}，可用RAM{memory_GiB:.3f}GiB、盘{disk_GiB:.3f}GiB，满足12/100GiB。无相关原生、URV控制器或场读取器进程，tmux无会话/目标会话；解释器、numpy及pvpython文件可用，未执行pvpython。此快照非资源预留，用户实际启动时控制器仍重查。
- 六正式目录均只含config/manifest；launch_attempts/analysis_results/新控制日志均不存在，无诊断/正式completion。不是“已启动”证据。
- 命令bash -n退出0，tmux参数和内层命令往返核对一致；活动控制日志未纳入不可变输入。START_COMMAND.txt是静态交付，没有运行tmux new-session。

## 4. 运行语义和限制

用户手动启动后：每条求解→completion/全过程原始证据→标准独立接受；任一门失败停，无自动重试/延时/续算。全部六条接受后才按原三网格规则评价P/T并写阶段汇总，网格不通过仍HOLD，不进入S5或V2比较。

1/4/12h为原生进程上限，初始化及输出在该进程内。独立检查外层1h，内部读取器1h含在其中；文件/指纹/网格汇总/清理另计，40h不是硬批次总时限。外层检查超时没有整棵读取器后代树统一清理保证；超时后保持HOLD，后续另做单次残留核查，不自动再起批次。S4持续性能/峰值RSS/收敛步数未知，S2条件估算不是完成保证，已在真实采用问题中明确接受细格超时风险。

控制日志`{v['controller_log_path']}`，会话`{v['session_name']}`。唯一命令固定miniconda Python -B，子进程清除LD_LIBRARY_PATH/LD_PRELOAD，不改变全局环境。用户无输出返回提示符也不等同启动成功，不重复执行；下一任务按请求单次查会话、attempt、日志/已有回执，不持续轮询。

## 5. 当前科学状态与交接

正式NUMERICAL_GATE=NOT_EVALUATED、geometry_PASS=null、RESULT_PASS=false（尚未计算），reference_qualified=false，MODEL_COMPARISON/physical_validation=NOT_EVALUATED，strict_error_bound_established/submission_ready=false，F04 OPEN。S0–S3已接受、S4零步独立接受、旧FAIL/380项差异、MRP静态FAIL、旧v1 HOLD与历史唯一归因限制保持。原S2-LRP日志例外及上轮首份B错误候选原样保留，不重判或覆盖。

本轮实际新增原生调用0、VTK0、编译0、时间推进0，未启动性能或正式计算，没有源码/配置/门槛变更。新正式授权和合同不等于已执行；actual_formal_run_ids在签发时为空，不事后覆写签发合同。

证据：prebinding_verification.json、verification.json、clean_environment_ldd.txt、START_COMMAND.txt、protected_files_before.json、final_integrity.json和document_manifest.json。此前授权待确认的只读快照在URV_S4_formal_authorization_pending_20261104_092559（若路径不同以authorization_resolved.json实际引用为准），仅是确认前历史，不替代本次真实答复。

下一动作：用户在dell本地Linux终端手动执行START_COMMAND.txt唯一命令一次，贴回输出或报错；没有输出也说明。用户实际执行后，单次核查正式S4启动状态，不重跑、不持续轮询。命令交付后本任务停止。
'''
    # Refer to the actual pre-authorization snapshot directory without assuming its creation second.
    pointer=Path('/tmp/sim240_s4_authorization_pending_directory.txt')
    if pointer.is_file():
        pending=Path(pointer.read_text().strip())
        resolution=dict(resolved_at=stamp,status='ACTUAL_AUTHORIZATION_RECEIVED_AFTER_CONDITIONAL_PRECHECK',
            question_item_id=auth['question_item_id'],actual_answer=auth['user_instruction_verbatim'],
            authorization_path=v['authorization_path'],authorization_sha256=v['authorization_sha256'],
            formal_release_path=str(release),formal_release_sha256=digest,issuance_report=str(OUT/'REPORT.md'),
            prior_pending_snapshot_preserved=True)
        save(pending/'authorization_resolved.json',resolution)
        with (pending/'REPORT.md').open('x') as f:f.write('授权确认前只读快照已完成；随后收到真实采用/完整六条授权，已在独立新目录生成正式绑定。原readonly_precheck.json的pending字段描述确认前时点，不改写为事后状态。接续见authorization_resolved.json。未启动计算。\n')
        report=report.replace('URV_S4_formal_authorization_pending_20261104_092559（若路径不同以authorization_resolved.json实际引用为准）',str(pending.relative_to(ROOT)))
    with (OUT/'REPORT.md').open('x') as f:f.write(report)
    section=f'''## 正式S4六条已真实授权并签发独立合同，命令已准备，等待用户手动启动（{stamp}）

用户实际选择“现在采用并授权完整六条；生成合同和命令，由我手动启动”，question_item_id ["request_user_input_async","call_a2f8d135b2a942e78a70d8438206254e",0]。完整问题覆盖采用S4-FRD-v1、六条原顺序/1-4-12h/每条标准检查1h、验收后继续含第四条后细格、接受12h超时批次不完整、无PERF/重试/加时/S5、AI只生成合同/命令。本次是真实选项答复，非用户手写扩展句；实际答复与完整问题分别记录。此前条件指令不假装授权。

入口docs/reports/{OUT.name}/REPORT.md、verification.json、prebinding_verification.json、START_COMMAND.txt、final_integrity.json。正式release {release.relative_to(ROOT)}，SHA {digest}，3284输入，原B3248输入完整保留。真实授权 {Path(v['authorization_path']).relative_to(ROOT)} SHA {v['authorization_sha256']}；独立已采用资源记录 {Path(v['adopted_resource_decision_path']).relative_to(ROOT)} SHA {v['adopted_resource_decision_sha256']}。旧资源candidate仍false不改，原B/A/零步release均不覆盖。

合同simulation/formal=true，approved精确六条dx5P→T、dx2.5P→T、dx1.25P→T，native_zero/initial_readback/PERF/retry/extension/S5=false，AI_may_start_solver=false，user_manually_starts=true。六run_id沿用URV_S4_P/T_dx5/2p5/1p25_reuse_v1_20261103_01，不因release日期改身份。签发时actual_formal为空，保留已完成18audit/6初态证据。34h求解＋检查另最多6h，文件/哈希/汇总/清理另计；40h不是硬批次总时限，检查超时后代清理限制按S4-FRD保留。当前未启动。

正式权限、资源采用门、科学checker binding、全3284输入均通过；默认只读控制器退出0/solver_executed=false/零步PASSED，受控子进程0，未以已授权release的execute测试。错误外部SHA/关闭B当formal/formal当zero均拒绝。3288旧保护文件保持，包内仅新增授权/资源采用/release/sidecar4项；无源码/配置/科学门修改，编译0、原生0、VTK0、步进0。命令bash语法及参数往返验证通过，没有执行tmux new-session。

签发前一次快照{pre['checked_at']}：{pre['host']}，RAM{memory_GiB:.3f}GiB、盘{disk_GiB:.3f}GiB满足12/100GiB，相关原生/控制器/场读取器进程空，tmux无会话；不是资源预留。原S1 ELF 5c3836e97c99feab88cd8e41773237f6ff642a10558f151b11e112563382b07b保持，OpenLB {pre['openlb_version']}；清洁环境实际解析15动态库路径/指纹一致，解释器/numpy及pvpython文件核对，未调用pvpython。用户启动时控制器再核查现场资源/输入。

六正式目录仍只有config/manifest，无launch_attempts/analysis_results/正式completion/diagnostics，新控制日志{v['controller_log_path']}尚不存在；会话{v['session_name']}尚未创建。命令固定miniconda Python -B并清除子进程LD_LIBRARY_PATH/LD_PRELOAD，日志不作不可变输入。已准备/交付命令不等于用户实际启动或结果通过。

正式NUMERICAL_GATE=NOT_EVALUATED、geometry_PASS=null、RESULT_PASS=false、S4网格/稳态K未评价；reference资格false、MODEL_COMPARISON/physical_validation未评价、strict_error_bound/submission_ready=false、F04 OPEN。S0–S3和S4零步接受、原S2-LRP日志例外、旧FAIL/380差异/MRP静态FAIL/旧v1 HOLD/历史唯一归因未建立、作者声明范围及独立核实false保持。上轮被拒B候选仍不可用/保留。

下一具体动作：用户在dell本地Linux终端手动执行START_COMMAND.txt唯一命令一次，贴回输出/报错，无输出返回提示符也说明，先不重复启动。用户实际执行后按请求单次查正式S4启动状态，不重跑、不持续轮询；批次结束后另任务按原协议独立分析，不自动S5。AI本轮不代启动。下一步模型GPT-6.1 Sol｜Low（用户执行后的单次启动状态核查）。
'''
    for name in ('SIM240_AI_CONTEXT.md','AI_HANDOFF_20261015.md'):
        p=ROOT/'docs/reports'/name;old=p.read_text();before=(OUT/('before_'+name)).read_text()
        start=old.index('\n## ')+1;bstart=before.index('\n## ')+1
        need(old[start:]==before[bstart:],'concurrent S4 status body changed; do not overwrite')
        end=old.find('\n## ',start+1)
        p.write_text(old[:start]+section+'\n'+(old[end+1:] if end>=0 else ''))
        with (OUT/('after_'+name)).open('xb') as f:f.write(p.read_bytes())
    need(all(sha(p)==h for p,h in bound['inputs_sha256'].items()),'issued binding drift after reporting')
    need(all(sha(p)==h for p,h in protected.items()),'old evidence drift after reporting')
    save(OUT/'final_integrity.json',dict(checked_at=stamp,PASS=True,release_sha256=sha(release),release_inputs_verified=3284,
        B_sha256=sha(CASE/'evidence/preparation_B.json'),old_protected_files_unchanged=3288,
        new_CASE_files=sorted(new_paths),formal_directories_pristine=6,formal_attempts_absent=True,
        controller_log_absent=True,actual_formal_run_ids=[],AI_started_solver=False,tmux_started=False,
        native_calls=0,VTK_calls=0,builds=0,time_steps=0,scientific_status_upgraded=False,shared_state_updated=True))
    manifest={str(p.relative_to(ROOT)):sha(p) for p in sorted(OUT.iterdir()) if p.is_file() and p.name!='document_manifest.json'}
    save(OUT/'document_manifest.json',manifest)
    print(json.dumps(dict(PASS=True,release_sha256=digest,release_inputs=3284,
        command_file=str(OUT/'START_COMMAND.txt'),formal_started=False,shared_state_updated=True),ensure_ascii=False))


if __name__=='__main__':
    with patch('subprocess.Popen',side_effect=AssertionError('No process during report/handoff finalization')):main()

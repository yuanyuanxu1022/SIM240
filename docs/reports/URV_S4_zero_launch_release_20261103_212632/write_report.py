"""Document issued zero-only authority and handoff before delivering the command."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import hashlib,json
ROOT=Path('/home/dell/yuanyuanxu/SIM240');OUT=Path(__file__).resolve().parent
CASE=ROOT/'CASE/unseen_v2_reference_S4_reuse_v1'
load=lambda p:json.loads(Path(p).read_text())
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(name,value):
    with (OUT/name).open('x') as f:json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n')
x=load(OUT/'verification.json');pre=load(OUT/'prebinding_verification.json');release=Path(x['release_path']);bound=load(release)
now=datetime.now(ZoneInfo('Asia/Shanghai')).isoformat()
assert sha(release)==x['release_sha256'] and all(sha(p)==h for p,h in bound['inputs_sha256'].items())
protected=load(OUT/'protected_files_before.json');assert all(sha(p)==h for p,h in protected.items())
report=f'''# S4原生18＋6：独立零步执行绑定与用户手动命令

签发完成时间：{now}。本轮仅复核封存与届时资源、保存真实授权、生成新零步合同并准备一条命令；不执行原生、VTK读回、构建、性能或正式计算。科学状态未升级。用户明确答复：“现在授权18＋6；生成合同和命令，由我手动启动”。

## 1. 交付与实际状态

新合同`CASE/unseen_v2_reference_S4_reuse_v1/evidence/S4_zero_launch_release_v1_20261103_01.json`，SHA256 `{x['release_sha256']}`，kind=AUTHORIZED_ZERO_STEP_AUDIT_RELEASE；2998项绑定输入逐项一致。仅原生零步与初态读回权限true，simulation/formal/PERF/S5/重试/加时保持false。

批准范围：六配置各describe/precheck/initialize，18次原生，推进0步，6次实际初态场读取。每次原生调用和每次初态读回等待预算各300s，失败即停不重试；预算不是整批完成时长或清理开销保证。approved_audit_run_ids精确18，approved_initial_field_reads精确6；approved_runs/approved_run_ids仍空。actual_audit_run_ids/actual_formal_run_ids仍空，未提前填成执行或完成。

命令已准备在START_COMMAND.txt，但本轮没有执行tmux new-session、没有运行--execute、没有新尝试/日志/原生输出/读取器输出/正式结果或准备B。会话`{x['session_name']}`尚未由本轮创建；用户手动执行后才可能开始。后续结果验收与B封存另做任务，不由零步控制器自动进入PERF或正式计算。

## 2. 授权证据的真实来源

证据`CASE/unseen_v2_reference_S4_reuse_v1/evidence/S4_zero_launch_authorization_v1_20261103_01.json`，SHA `{x['authorization_sha256']}`。来源为user_reply_to_request_user_input_async，questionItemId `["request_user_input_async","call_00fda303fc644ba0899a14837bda04fd",0]`。完整问题与实际所选答复分别逐字保存，不把选项答复写成用户手工输入的扩展长句；范围由两者共同确定。

完整问题：“S4 准备 A 的只读复核已通过。是否现在授权18次原生零步调用（六配置各 describe／precheck／initialize，推进0步）及6次初态场读取：每次原生调用、每次读取各最多300秒，失败即停、不重试？本次仅让我在复核封存和届时资源后生成独立执行合同和一条命令，由你本人手动启动；不包含性能推进或正式计算。”

合同与证据分别标明AI_may_start_solver=false、user_manually_starts=true。这份明确18+6答复接续此前条件指令，未挪用准备实施、旧S2/S3或正式运行授权。

## 3. 封存、环境、资源与冲突核对

原准备A仍为关闭状态：SHA `{x['original_A_sha256']}`，2976原输入保持。当前3245项只读复核保护证据及本轮纳入的旧报告合计3260份保护文件未变；旧源码、ELF、库、原数据/合同、13科学文件、120软件测试证据均保持。原生S4几何尚无真实审计，不把预期节点/链写为实际PASS。

新合同在原A输入之外另绑定原A与SHA侧文件、真实授权、14份只读复核文件及其清单、本次不可变资源/来源快照、绑定生成器及Python/读取器二进制指纹等；实际新增22项，总计2998，不按预估数签发。新合同有外部独立SHA，原A没有被修改或重封。

一次启动前快照时间{pre['at']}，主机`{pre['host']}`，可用内存{pre['resources']['MemAvailable_bytes']/1024**3:.3f}GiB（要求≥12GiB）、磁盘{pre['resources']['disk_free_bytes']/1024**3:.3f}GiB（首次要求≥100GiB）。未发现URV求解器/阶段控制器冲突进程，无tmux会话；tmux查询返回1且明确no server running，未将其他查询错误解释为无会话。

同一S1 ELF SHA `5c3836e97c99feab88cd8e41773237f6ff642a10558f151b11e112563382b07b`。在清除LD_LIBRARY_PATH/LD_PRELOAD的环境下，ldd查询退出0，实际解析15动态库的路径集合及内容指纹与原构建记录一致。此为只读依赖查询，不是原生模型调用。Python固定/home/dell/miniconda3/bin/python3 -B，pvpython固定/usr/bin/pvpython，仅核对其可执行路径/指纹，没有运行读取器。

上述资源是快照，不是预留。用户实际启动时控制器仍会检查资源、原输入和净目录，资源不满足即停；不删除旧数据、换库或自动加时。单进程/单线程/单cuboid/overlap3、8GiB单受限进程地址空间等原限制保持，不宣称是整个进程树内存之和或全程RSS实测。

## 4. 新合同独立检查与命令审计

verify_seal及validate_zero_authority通过，18审计身份/6读回关联/原A及真实授权均对应；错误外部SHA被拒绝，零步合同被formal权限验证明确拒绝。真实默认入口audit_S4_zero.main在所有子进程调用被阻止的条件下退出0，ZERO_PLAN_BINDING_CHECK=true、solver_executed=false、planned_native_calls18、planned_initial_field_reads6、native_zero_step_authorized=true。没有运行带--execute的入口。

START_COMMAND.txt唯一命令由参数安全引用生成，bash -n仅语法检查通过，shell参数往返一致；没有执行该命令。用户手动命令清除LD_LIBRARY_PATH/LD_PRELOAD，精确绑定新release和SHA，使用新控制日志`{x['controller_log_path']}`。活动日志不在2998项不可变输入内，避免日志正常增长造成bound input drift。

六正式目录与18零步目录仍净，无audit_attempts/launch_attempts/analysis_results/B或零步verification；原生调用0、VTK调用0、构建0、推进0。旧S3控制器首行Four注释的非阻塞遗留保持，实际S4六配置未变；未因此修改封存。

## 5. 用户操作与后续界限

在dell这台Linux机器的本地终端执行START_COMMAND.txt中唯一命令一次。它在tmux后台运行，终端可能直接回到提示符；这本身不是启动或完成证据。把终端完整输出/报错原文贴回；若无输出，说明已返回提示符，先不要重复执行。按用户下一条请求再单次查启动状态，不持续轮询。结束后另行独立复核原生18+6结果，合格后才能另存关闭准备B。

本次不授权性能推进或正式S4，更不授权S5；原正式1/4/12h与细格走满步条件成本约32h风险留待后续正式资源协议审定。当前NUMERICAL_GATE=NOT_EVALUATED、geometry_PASS=null、RESULT_PASS=false（未运行）；REFERENCE_QUALIFIED_FOR_CASE/reference_qualified=false、MODEL_COMPARISON/physical_validation未评价、strict_error_bound_established/submission_ready=false，F04 OPEN。历史FAIL/380差异、MRP静态FAIL、旧v1 HOLD、历史唯一归因未建立和作者声明有限范围不改。

报告由AI辅助整理真实授权和核对证据，不是人工科学终审。共享当前状态/最新交接已在交付命令前更新；无提交/推送。证据入口：verification.json、prebinding_verification.json、clean_environment_ldd.txt、protected_files_before.json、START_COMMAND.txt、final_integrity.json及document_manifest.json。
'''
with (OUT/'REPORT.md').open('x') as f:f.write(report)
body=f'''## S4原生18+6零步合同已签发、命令已准备，等待用户手动启动（{now}）

用户明确答复“现在授权18＋6；生成合同和命令，由我手动启动”，对应request_user_input_async call_00fda303fc644ba0899a14837bda04fd。仅六配置describe/precheck/initialize各一，共18原生调用及6初态读取，推进0步、各300s、失败停不重试；AI只生成合同/命令，不代执行，PERF/正式/S5未授权。授权来源是实际选项答复＋完整提问，非扩写的手工原话。

入口`docs/reports/URV_S4_zero_launch_release_20261103_212632/REPORT.md`、START_COMMAND.txt、verification.json。新release CASE/unseen_v2_reference_S4_reuse_v1/evidence/S4_zero_launch_release_v1_20261103_01.json，SHA `{x['release_sha256']}`，2998输入当前一致。真实授权evidence/S4_zero_launch_authorization_v1_20261103_01.json，SHA {x['authorization_sha256']}。原准备A SHA e9d12e68eaa324bd8e78ad57825710936f9e00518faf39337923b930ad82a165及2976输入不变，原A仍关闭。

新合同native_zero/initial_readback=true；simulation/formal/PERF/S5/重试/加时=false，approved审计18/读回6，approved正式空、actual审计/正式空。新合同通过原seal/provenance/权限；默认只读入口退出0且18/6、solver_executed=false，错误SHA及formal权限被拒绝。新日志不作不可变输入，语法/引用核对通过，未执行命令。

一次资源快照{pre['at']}：主机{pre['host']}，RAM{pre['resources']['MemAvailable_bytes']/1024**3:.3f}GiB、盘{pre['resources']['disk_free_bytes']/1024**3:.3f}GiB，满足12/100GiB；无URV冲突进程/tmux会话，非资源预留。清洁环境解析15动态库路径/指纹与真实构建一致，同S1 ELF不变；120软件测试记录保持，3260旧保护文件不变。未重新编译/原生/VTK/时间推进或新软件测试。

审计身份URV_S4_ZERO_v1_20261103_01，会话urv_s4_zero_v1_20261103_01；六正式预留URV_S4_P/T_dx5/2p5/1p25_reuse_v1_20261103_01未授权。24目录仍只有config/manifest，无attempt/零步结果/B/正式结果。控制日志拟CASE/unseen_v2_reference_S4_reuse_v1/S4_zero_controller_v1_20261103_01.log，当前不存在。命令固定Python -B并清除LD_LIBRARY_PATH/LD_PRELOAD。本轮准备合同和命令不等于用户已启动或审计完成。

S4实现及只读复核入口分别docs/reports/URV_S4_implementation_20261103_203002/REPORT.md与URV_S4_A_readonly_review_20261103_205756/REPORT.md。科学状态仍NOT_EVALUATED/null/false（未运行）；参考资格false、模型/物理未评价、submission_ready=false、F04 OPEN。旧FAIL/380差异/MRP静态FAIL/旧v1 HOLD及声明限制保持。正式资源决策/可能PERF和正式计算另行授权，不自动进S5。

下一具体动作：用户在dell本地Linux终端手动执行START_COMMAND.txt唯一命令一次，贴回完整输出/报错；无输出返回提示符也说明，先不重复启动。用户实际执行后按请求单次查状态，不持续轮询；结束后另任务完整独立复核18+6，合格后另存关闭B。下一步模型GPT-6.1 Sol｜Low（单次状态核查）。

'''
updates=[]
for name in ('SIM240_AI_CONTEXT.md','AI_HANDOFF_20261015.md'):
    path=ROOT/'docs/reports'/name;before=(OUT/('before_'+name)).read_text();current=path.read_text()
    a=before.find('\n## ');b=before.find('\n## ',a+1);c=current.find('\n## ')
    assert a>=0 and b>=0 and current[c:]==before[a:],'concurrent shared body changed'
    updates.append((path,current[:c+1]+body+before[b+1:]))
for path,text in updates:path.write_text(text)
save('shared_state_update.json',dict(at=now,paths_sha256={str(p):sha(p) for p,_ in updates},historical_tail_preserved=True))
assert all(sha(p)==h for p,h in protected.items()) and all(sha(p)==h for p,h in bound['inputs_sha256'].items())
assert not any((CASE/p).exists() for p in ('audit_attempts','launch_attempts','analysis_results','evidence/preparation_B.json'))
save('final_integrity.json',dict(at=now,release_sha256=sha(release),release_inputs_verified=len(bound['inputs_sha256']),original_A_unchanged=True,protected_files_unchanged=len(protected),
    actual_audit_run_ids=[],actual_formal_run_ids=[],native_calls=0,VTK_calls=0,builds=0,tmux_started=False,command_prepared_not_executed=True))
manifest={str(p.relative_to(OUT)):sha(p) for p in OUT.rglob('*') if p.is_file() and p.name!='document_manifest.json'}
save('document_manifest.json',manifest)
print('RELEASE_REPORT_READY',len(manifest),'artifacts; shared handoff written before command delivery; no execution.')

"""Write review-only findings and shared handoff; keep the frozen CASE untouched."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import hashlib,json
ROOT=Path('/home/dell/yuanyuanxu/SIM240');OUT=Path(__file__).resolve().parent
CASE=ROOT/'CASE/unseen_v2_reference_S4_reuse_v1';CHECK=ROOT/'CASE/unseen_v2_reference_checker_S4_reuse_v1'
load=lambda p:json.loads(Path(p).read_text())
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(name,x):
    with (OUT/name).open('x') as f:json.dump(x,f,ensure_ascii=False,indent=2);f.write('\n')
x=load(OUT/'review_verification.json');configs=load(OUT/'six_configuration_review.json');now=datetime.now(ZoneInfo('Asia/Shanghai')).isoformat()
assert x['PREPARATION_A_READONLY_REVIEW_PASS'] and x['new_execution_authorization_received'] is False
bound=load(CASE/'evidence/preparation_A.json')
save('binding_prerequisites.json',dict(kind='NON_EXECUTABLE_REVIEW_CHECKLIST_NOT_AUTHORIZATION',stage='S4_THIN_GRID',
    preparation_A_path=str(CASE/'evidence/preparation_A.json'),preparation_A_sha256=x['preparation_A_sha256'],
    planned_audit_id='URV_S4_ZERO_v1_20261103_01',planned_native_calls=18,planned_initial_field_reads=6,
    planned_audit_ids=[r['run_id'] for r in bound['zero_prepared_runs']],approved_audit_ids=[],actual_audit_ids=[],
    native_zero_step_authorized=False,initial_field_readback_authorized=False,formal_simulation_authorized=False,
    performance_time_stepping_authorized=False,AI_may_start=False,user_manually_starts=True,
    user_authorization_evidence=None,execution_release_path=None,launch_command=None,
    native_cap_seconds=300,initial_field_reader_wait_cap_seconds=300,advance_steps=0,fail_stop=True,retry=False,
    resource_recheck='ONLY_AFTER_EXPLICIT_AUTHORIZATION_AND_AGAIN_AT_USER_START',
    prerequisite_available_RAM_GiB=12,initial_free_disk_GiB=100,before_each_run_free_disk_GiB=8,per_process_AS_GiB=8,
    resource_snapshot_currently_taken=False,minimum_bound_files_to_add=['unchanged original A','A SHA sidecar','real18+6authorization record','new release inputs and immutable review evidence as applicable'],
    exact_added_input_count='COMPUTE_FROM_REAL_BINDING_NOT_PREDICTED',
    environment='Python -B with captured dependencies; no ambiguous inherited LD_LIBRARY_PATH/LD_PRELOAD; no new builds or library replacements',
    logs='fresh path outside immutable inputs; no reuse of active control log as input',
    boundary='No PERF or formal stepping; no S5; no automatic retry, extension or continuous polling'))
rows='\n'.join(f"|{c['direction']}|{c['dx_nm']:g}|{c['expected_nodes']:,}|{c['expected_wall_links']:,}|{c['window_steps']} / {c['maximum_steps']}|一致|" for c in configs)
report=f'''# S4准备A与采用范围：只读独立复核

核对时间：{now}。用户本轮：“只读复核 S4 准备 A 与采用范围；获得明确覆盖原生 18＋6 的授权后，再复核资源、生成独立零步执行绑定并交付用户手动命令，当前不启动。”本轮没有获得新的18+6明确执行授权；条件表述不写成真实授权。peer-review技能用于作者要求的内部方法/准备材料审查，不是期刊审稿或人工科学终审。

## 1. 裁定

PREPARATION_A_READONLY_REVIEW_PASS=true。准备A与采用的S4-MIP-v1最小范围一致，当前未发现阻塞原生零步绑定准备的技术缺口。此结论只对应关闭权限的准备包；不是S4原生接入、数值结果、参考资格或执行授权通过。

A路径`CASE/unseen_v2_reference_S4_reuse_v1/evidence/preparation_A.json`，SHA `{x['preparation_A_sha256']}`。2976项输入与侧文件一致，110份候选文件集合/内容和28份原实施报告清单一致，3245份受保护文件前后未变。旧A未修改或重新封存，源码/配置/原门槛/既有证据均保持。

## 2. 采用与实施边界

当前adoption.json明确采用S4-MIP-v1并仅授权隔离实现/软件检查/关闭准备A。它精确绑定原范围PROTOCOL.md及scope_decision.json；原范围材料中的“待采用/未实现”是历史快照，由真实采用记录及新实施证据接续，不修改旧材料。未从准备授权或旧S2/S3授权推导原生权限。

新S4 CASE和检查器仅增加阶段来源/权限、A/B封存入口、默认只读运行器/独立零步入口、六配置R1/R2和阶段内网格证据。10个common与3个科学脚本共13文件字节不变，旧zero_evidence.py也保持；S4专用R1/R2副本仅精确计数12→18、4→6和对应消息变化。contracts仅新增精确S4来源分支，原资源/停止/环境/输出清单函数与S3的AST相同。未修改C++/二进制/库/物理/平均/质量及体积舍入路径、V2系数或提前预测，未扩大F04或实现PERF。

继续只读引用原S1 ELF SHA `5c3836e97c99feab88cd8e41773237f6ff642a10558f151b11e112563382b07b`及真实构建来源。原seal/provenance验证重新通过，包含真实编译器、1392依赖、3链接库、15动态库、源码diff及限定机器审计；这是当前来源复核，没有重新编译或反汇编。S3原合同/完成接受/原始输出/控制和完整独立复核仍在各自原合同下，来源前置未被移作S4数据或执行许可。

## 3. 六配置与18零步计划

U_THIN h30/d80/w120/P240/Ly240nm、H70nm、a1e5m/s²、rho1000kg/m³、nu1e-6m²/s、mu.001Pa·s；P+y/T+x。每配置的formal与describe/precheck/initialize仅mode、run_id和输出目录不同，其物理/时间参数逐项一致。原矩阵、派生exact_parameters、精确有理数与源码double取整、保存帧目标及独立静态几何均复算一致。

|方向|dx/nm|核心节点预期|壁面链预期|窗 / 最大步|三模式与正式配置|
|---|---:|---:|---:|---:|---|
{rows}

六正式和18零步目录均净，只有config/manifest；六份未来初态读回的路径按planned_case唯一绑定。没有审计尝试、原生输出、VTK文件、正式输出、准备B或启动合同。静态几何预测不写为geometry_PASS；初态半步体力响应也不能当稳态K或已推进的证据。

## 4. 权限与检查代码

simulation/formal/native_zero/initial_field_readback/PERF/S5/重试/加时权限全部false，approved和actual列表全空。直接调用两个权限验证函数均拒绝将关闭A当零步或正式执行合同；本次只调用纯文件验证函数，未调用任何执行入口。代码中真实授权校验早于创建审计尝试和进程。

零步分支强制18条有序身份、原生推进0、6份唯一初态读取；R1逐条核实际参数和时步/初态，R2核本配置独立读取进程、物理单位/通量/节点、PVD/VTM/VTI完整载荷关联。不是只改摘要计数。原生和初态读回各300s预算、8GiB地址空间、失败即停的控制路径保留；预算不是耗时保证。

原120测试通过记录、日志、代码与28份实施报告清单保持一致；本轮没有重跑这些测试，也没有再次运行默认CLI或保存场读回。原生/VTK/构建/求解/PERF调用均0。进程审计钩子阻止所有子进程和shell执行，并限制写入仅在本新报告目录；CASE写0。

## 5. 非阻塞说明与辅助脚本纠正

N1：run_S4.py首行继承注释仍写“Four formal S4 runs”。原冻结矩阵、stage_s4严格六身份、控制器循环和solver_runs=6以及软件测试均为六；该注释不参与执行。裁定为非阻塞文字遗留，本轮不为修注释改变封存，后续若另建修订候选可一并校正。没有用四条替代六条的许可或执行行为。

本轮新复核辅助脚本首次误用q精确等于.5，触发自身断言；真实静态枚举q_max依三网格为0.5000000000000018/0.5000000000000036/0.5000000000000071，最大差约7.1e-15。原URV容差本来为1e-10。仅将新报告辅助脚本改回原容差后通过，初版和纠正说明已保存。未修改准备A、原检查器、数据或原门槛；不是新算例FAIL或科学证据冲突。

## 6. 尚未获得授权的下一步

准备包技术核对完成。需要明确的18+6授权后，才重新核查届时可用内存/磁盘、冲突任务、原生和读取器环境、封存及净目录。当前未做可供启动使用的资源快照，不把旧实施快照当资源预留；正式细格约32h的条件成本风险只属于后续正式资源决策，不因零步复核消失。

后续零步绑定必须另存真实授权原话/来源、原A及SHA侧文件、精确18 approved_audit身份、6初态读取权限和新独立release外部SHA。除显式零步/初态权限外，正式/PERF/S5/重试/加时保持关闭；实际记录不提前填写。新增输入数按真实绑定计算，不预写。启动环境应避免继承LD_PRELOAD/LD_LIBRARY_PATH造成依赖解析歧义；日志使用新路径且不纳入活动不可变输入。binding_prerequisites.json只有不可执行核对清单，无授权、合同路径或命令。

按已采用范围PROTOCOL第6节：“原生和初始化场读取的后续明确授权须覆盖18+6、推进0步、失败即停不重试、由用户手动启动。”本轮用户原话为“获得…授权后”的条件指令，因此当前只读任务不能代写成已授权。准备实施授权和过去S2/S3的授权都不挪用。

当前保持NUMERICAL_GATE=NOT_EVALUATED、geometry_PASS=null、RESULT_PASS=false（未运行），reference_qualified=false、MODEL_COMPARISON/physical_validation未评价、submission_ready=false；F04 OPEN。S0–S3接受、旧FAIL/380差异/MRP静态FAIL/旧v1 HOLD/历史唯一归因未建立及作者声明有限范围不变。本轮无新增流场、原生几何或物理验证。

下一具体动作：取得明确18+6授权后，复核封存与届时资源，生成独立零步执行绑定和一条用户手动命令；AI不启动，PERF及正式计算另行授权。若用户仅保留本轮复核，则停在权限关闭状态。

证据：review_verification.json、six_configuration_review.json、binding_prerequisites.json、helper_correction.json、review_initial.py.txt、protected_files_before.json和document_manifest.json；进度与最新共享交接已同步。
'''
with (OUT/'REPORT.md').open('x') as f:f.write(report)
body=f'''## S4准备A只读复核通过；18+6尚未明确授权，执行权限保持关闭（{now}）

用户本轮只授权只读复核准备A与采用范围；“获得明确18+6授权后再…”是条件指令，不是新的原生执行授权。报告入口`docs/reports/URV_S4_A_readonly_review_20261103_205756/REPORT.md`、review_verification.json、binding_prerequisites.json（不可执行清单）。本轮没有生成启动release/命令或启动任务。

A路径CASE/unseen_v2_reference_S4_reuse_v1/evidence/preparation_A.json，SHA e9d12e68eaa324bd8e78ad57825710936f9e00518faf39337923b930ad82a165。2976输入、110候选文件、28实施报告清单及3245保护文件当前全一致。原seal/provenance、真实采用范围、六正式/18零步配置与三网格精确时步/静态几何通过；24目录净。两个权限函数拒绝关闭A执行角色；原120软件测试记录已按指纹核实，本轮未重跑测试/CLI/原生/VTK/构建或资源启动快照。

原S1 ELF/构建/源码/依赖/库和13科学文件保持。R1/R2六配置适配实际覆盖18记录与6唯一读回；原生/读回各300s，失败即停、推进0、默认只读，真实授权早于新尝试或进程。非阻塞N1：正式控制器首行Four旧注释，实际白名单/循环/完成计数均六，封存不改。本轮辅助脚本q精确相等误用已只在新报告脚本按原1e-10容差修正，原包/科学门未动，详情报告。

S4-MIP-v1实现已完成：CASE/unseen_v2_reference_S4_reuse_v1及checker_S4_reuse_v1；实现报告docs/reports/URV_S4_implementation_20261103_203002/REPORT.md。正式身份为URV_S4_P/T_dx5/2p5/1p25_reuse_v1_20261103_01，零步URV_S4_ZERO_v1_20261103_01仅预留。全部simulation/formal/native_zero/initial_readback/PERF/S5/重试/加时权限false，approved/actual全空，无B/审计或启动尝试/结果。S4 NUMERICAL_GATE未评价、geometry_PASS=null、RESULT_PASS=false（未运行），参考资格false、模型/物理未评价、submission_ready=false、F04 OPEN。

后续真实授权须覆盖18原生零步+6实际初态读取、300s单调用/单读取预算、失败停/不重试、用户手动启动；仅让AI复核资源并生成新绑定/一条命令，AI不代执行。授权后再查届时资源/冲突任务/环境和封存，绑定真实证据及A+侧文件，不提前写actual或挪用旧许可，活动日志不作不可变输入。PERF和正式资源决策/计算仍另行授权，不进S5。本轮无新流场或数值/物理验收，历史FAIL/限制保持。

下一具体动作：收到明确18+6授权后再办独立零步绑定和用户手动命令；当前停在权限关闭，若未授权不自动继续。下一步模型GPT-6.1 Sol｜High。

'''
updates=[]
for name in ('SIM240_AI_CONTEXT.md','AI_HANDOFF_20261015.md'):
    path=ROOT/'docs/reports'/name;before=(OUT/('before_'+name)).read_text();current=path.read_text()
    start=before.find('\n## ');end=before.find('\n## ',start+1);cs=current.find('\n## ')
    assert start>=0 and end>=0 and current[cs:]==before[start:],'concurrent shared body changed'
    updates.append((path,current[:cs+1]+body+before[end+1:]))
assert all(sha(p)==h for p,h in load(OUT/'protected_files_before.json').items())
for path,text in updates:path.write_text(text)
save('shared_state_update.json',dict(at=now,paths_sha256={str(p):sha(p) for p,_ in updates},historical_tail_preserved=True))
save('final_integrity.json',dict(at=now,protected_files_unchanged=3245,CASE_writes=0,native_calls=0,VTK_calls=0,builds=0,
    tests_rerun=0,resource_snapshot_taken=False,execution_authorization_received=False,execution_release_created=False,launch_command_created=False))
manifest={str(p.relative_to(OUT)):sha(p) for p in OUT.rglob('*') if p.is_file() and p.name!='document_manifest.json'}
save('document_manifest.json',manifest)
print('READONLY_REVIEW_REPORT_COMPLETE',len(manifest),'report files; original A/CASE unchanged; permissions closed.')

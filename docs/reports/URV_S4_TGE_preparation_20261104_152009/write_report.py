"""Close the authorized preparation task; no execution authority is generated."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import hashlib,json
ROOT=Path('/home/dell/yuanyuanxu/SIM240');OUT=Path(__file__).resolve().parent
CASE=ROOT/'CASE/unseen_v2_reference_S4_tge_v1';CHECKER=ROOT/'CASE/unseen_v2_reference_checker_S4_tge_v1'
load=lambda p:json.loads(Path(p).read_text())
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(name,value):
    with (OUT/name).open('x') as f:json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n')
seal=CASE/'evidence/preparation_A.json';bound=load(seal);verified=load(OUT/'seal_verification.json')
protected=load(OUT/'protected_old_files.json');resources=load(CASE/'evidence/resource_review.json')
checks=load(OUT/'readonly_entry_checks.json');tests=load(OUT/'software_tests.json')
assert all(sha(p)==h for p,h in protected.items()) and all(sha(p)==h for p,h in bound['inputs_sha256'].items())
assert sha(seal)==verified['preparation_A_sha256'] and tests['exit_code']==0 and tests['test_methods']==15
now=datetime.now(ZoneInfo('Asia/Shanghai')).isoformat()
newfiles=sorted(str(p.relative_to(ROOT)) for tree in [CASE,CHECKER] for p in tree.rglob('*') if p.is_file())
save('changed_paths.json',dict(new_files=newfiles,old_CASE_files_modified=[],shared_state_files=['docs/reports/SIM240_AI_CONTEXT.md','docs/reports/AI_HANDOFF_20261015.md']))
report=f'''# 单条横槽补证隔离准备 A：S4-TGE-PREP-v1

**本轮采用的最小准备已完成：T/0.625nm单配置输入、原两条横槽基准引用、同一ELF来源绑定、默认只读检查、3＋1零步审计控制器与独立零步结果检查接口，以及资源审查材料均已隔离准备。软件与静态检查通过；原生/读场/PERF/正式全部未执行且未获执行授权。** 原S4横槽FAIL、参考资格与S5停点保持。

这是一份AI辅助的内部准备与软件验证报告，不是新网格的数值/几何验收，也不是人工科学终审。用户本轮原话：“采用最小草案后，限定范围准备单条横槽补证的隔离接入与资源审查材料，原生审计、性能标定和正式计算仍分别授权。” 已按原话另存preparation_adoption.json，准备与必要软件检查许可不扩展为原生或求解许可。

## 1. 本轮改动与同一ELF复用

新目录 `{CASE.relative_to(ROOT)}` 与 `{CHECKER.relative_to(ROOT)}`，新增文件{len(newfiles)}份。原S4/S1源码、C++头/Makefile、科学阈值、旧配置/结果/合同/验收记录均未修改。

原生二进制直接引用 `CASE/unseen_v2_reference_S1_a1_v1/build/urv_reference`，SHA `5c3836e97c99feab88cd8e41773237f6ff642a10558f151b11e112563382b07b`。OpenLB `882924a9cfc8dcdf82909e39530789cb6f5ebcc4`；真实构建捕获、1392依赖、3链接库、15动态库及编译器来源经原冻结provenance核对。没有重新构建，也没有新ELF；旧compile_exit_code=0只说明历史构建，不冒充本轮编译。

科学算术/质量/几何、R1/R2零步原始证据检查和read_fields.py均按原绝对路径+输入指纹引用。新tge_stage只处理候选身份、封存、旧基准关联、原FAIL和权限；未修改旧24点矩阵或把0.625nm冒充原点。

## 2. 输入、预留身份与接口

候选仅T横槽+x，h30/d80/w120/P=Ly240nm，dx0.625nm，平均H70nm；a100000m/s²、nu1e-6m²/s、rho1000kg/m³、mu.001Pa·s、tau1，固定全充液、x/y周期、Bouzidi静止无滑移，半步体力/旧质量舍入/Neumaier双账本/A1体积路径保持。J按平面面积归一，K=nuJ/a（m³），U=J/H，R=mu/K。

计划正式身份 `{bound['prepared_runs'][0]['run_id']}`，planned_case_id=`{bound['prepared_runs'][0]['planned_case_id']}`，目前steady目录仅config/manifest。原生零步预留audit_id=URV_S4_TGE_ZERO_v1_20261104_01，describe/precheck/initialize各一目录，亦仅config/manifest。**身份已预留不表示获准或实际启动**；actual_audit_run_ids/actual_formal_run_ids和approved列表均空。

旧T2.5nm/T1.25nm以原release SHA `e5f7de1e584b776f8cc9bf1dbb31f198422ce10984ba8ad7d729220afdcdd19b`及原completion/acceptance、完整原始输出引用，未复制改号为新算例。原T5/2.5/1.25中细差1.328387035%>1%的失败保持。

- scripts/inspect_preparation.py：只读封存/身份/来源检查，不导入进程执行模块。
- scripts/audit_zero_tge.py：默认只读；执行分支在任何输出/进程前要求独立3＋1真实授权、资源方案采用、原A与SHA、净目录和当时资源，不能使用准备A或旧S4 release执行。仅允许三零步模式；每次核输入，失败即停，无重试/转PERF/正式。
- analysis/check_zero_tge.py：只读复核未来已有3＋1原始记录和真实初态场回执；重查R1/R2、身份/关联/退出/步数/闭包，不执行场读取或求解器。
- common/supplement_grid_plan.json：新2.5/1.25/0.625nm追加分支的规则材料；r2/Fs1.25、正有限p/同向非近零差、中细差与GCI各≤1%保持。原三档失败不可覆盖。

当前**未实现有限PERF控制器、正式求解/结果控制器、24点聚合或新参考资格规则**：这些依赖后续资源决策与独立范围，不在准备阶段预先开通。3＋1零步审计代码可审查，但本轮没有原生调用或实际初态读回，B尚不存在。

## 3. 软件与静态验证

15项软件测试全通过，涵盖错方向/间隙/网格/驱动/观测时间/帧计划，额外身份/模式/输出路径，旧网格或FAIL被覆盖，执行/加时/S5标志、未经采用的预算/内存变化、读取器被替换、未执行却标PASS以及自动代启动等拒绝情形；已验证准备文档进入执行函数会在写入/子进程之前拒绝，测试中Popen被mock禁止。

初轮13项通过后，补充读取器替换及未执行状态/手动启动边界的检查与2项测试，最终15项通过，记录software_tests.json/log。原生C++编译0、原生调用0、pvpython/VTK调用0、性能推进0、正式运行0；不是用原生执行做软件检查。

封存后默认inspect与默认零步入口只读退出均0，错误SHA只读检查退出2；三个入口检查均不含execute参数，4个预留目录前后保持config/manifest两文件。全部新Python语法检查通过但没有生成pyc或新原生二进制。

纯参数/几何预测：流体节点16515072、候选壁面链1964544、dt6.510416666666667e-14s、统计窗10368步、最大1486848步。A1体积路径之前在原三档精确重现，候选相对差静态估计约1.584e-11在1e-10内；这些是软件算术，不填geometry_PASS=true或新网格初态PASS。

## 4. 准备A封存

准备A：`{seal.relative_to(ROOT)}`。

SHA：`{sha(seal)}`。

输入闭包**{len(bound['inputs_sha256'])}项**，逐项指纹一致；其中包括旧来源/原始结果/失败材料、两份基准、当前准备采用、全部新脚本/配置与已结束的软件检查记录。A不绑定自身或未来活动日志。外部sidecar独立记录A的SHA。

原有{len(protected)}份受保护文件内容前后不变；新包4目录均未求解。封存kind=S4_TGE_PREPARATION_A_NOT_AUTHORIZATION，所有执行/重试/加时/S5权限false，AI_may_start_solver=false，user_manually_starts=true，NUMERICAL_GATE=NOT_EVALUATED、RESULT_PASS=false、geometry_PASS=null。

## 5. 资源审查材料与剩余决策

资源快照 {resources['snapshot_at']}：MemAvailable={resources['MemAvailable_bytes']/1024**3:.3f}GiB、磁盘空闲={resources['disk_free_bytes']/1024**3:.3f}GiB；仅本次快照，不是资源预留或未来启动前通过。

仅流体节点一组19个double分布量2.337890625GiB，未计入固体/重叠、其他数组和边界等。候选峰值RSS、进程地址空间是否足够、持续速度均未实测。

旧T1.25nm为4326.036s/12537步；假设节点×8、停止物理时刻相同则步数×4，才得138433.155s≈38.4537h。条件计算不是测速、完成预报或正式预算，不能从旧S4 12h自动改成38.5h/48h。

3＋1资源**未采用提案**：每次原生/读取各300s，单进程地址空间8GiB，可用RAM≥12GiB，初始磁盘≥100GiB、每次≥8GiB，每次输出≤4GiB，1进程/线程/cuboid、overlap3。后续零步release必须绑定用户覆盖这些限制的真实3＋1授权和独立资源采用。若超限则停，不自动提高内存或时限。

有限PERF仍需另立实现与授权；之前1800s或完整step≥2048仅草案，本准备无其执行入口。正式求解上限和正式检查时间当前均null，等待原生接入/资源证据后再审定。没有启动命令。

## 6. 科学状态与下一停点

原S4六条per-run三门PASS，沿槽网格PASS；横槽原网格FAIL/S4_STAGE_ACCEPTED=false不改。即使未来新分支通过，也不得回写原矩阵失败或自动进S5。reference_qualified=false，MODEL_COMPARISON/physical_validation未评价，strict_error_bound/submission_ready=false，F04 OPEN。S0–S3接受、旧FAIL/380差异/MRP静态FAIL/旧v1 HOLD/历史唯一归因限制/S2-LRP/原被拒B及作者声明范围均保持。

当前停点：**准备A已封存，软件/静态检查通过；原生3＋1、有限PERF、正式计算均未启动，权限关闭。** 下一步先只读复核A与采用范围、3＋1资源提案；获得明确3＋1授权后再核当时资源、另存零步执行绑定和用户手动命令。不要直接执行准备脚本来“看看能否运行”。

报告证据：seal_verification.json、software_tests.log/json、readonly_entry_checks.json、changed_paths.json、protected_old_files.json及新包evidence目录。运行包/源码存在、历史二进制构建、新软件验证、原生几何接入、正式运行和独立接受分别记录；本轮未制造后四者的完成证据。

使用[peer-review](/home/dell/.codex/skills/peer-review/SKILL.md)。工具出处已记录：Kassis等(2026)，[Scientific Agent Skills](https://arxiv.org/abs/2609.00065)，同日先前公开元数据核对为v2，仅工作流来源，不作为CFD论据。作者仍须亲自理解与科学复核。
'''
(OUT/'REPORT.md').write_text(report)
save('disposition.json',dict(preparation_complete=True,software_tests_pass=15,preparation_A_sha256=sha(seal),
    source_reused_exact_ELF=True,new_builds=0,native_calls=0,VTK_calls=0,PERF_advances=0,formal_runs=0,
    original_S4_stage_accepted=False,reference_qualified=False,S5_started=False,
    native_audit_status='NOT_EXECUTED',formal_interface='NOT_IMPLEMENTED_BUDGET_PENDING',
    all_execution_permissions_closed=True,next_action='Read-only review of A and 3+1 resource proposal; distinct explicit zero authority before binding/manual command.'))

section=f'''## S4单条横槽T0.625隔离准备A完成：同ELF复用、软件通过，3＋1/PERF/正式未启动（{now}）

用户本轮采用此前最小草案并要求准备隔离接入与资源材料，原生/性能/正式分别授权。该指令只授权本轮准备及必要软件验证，已按真实原话保存新包evidence/preparation_adoption.json；覆盖此前“0.625仅未采用候选”的当前准备状态，不改变旧审查报告原时点。入口{OUT.relative_to(ROOT)}/REPORT.md、disposition.json、seal_verification.json、software_tests.log/json、readonly_entry_checks.json。

新增CASE/unseen_v2_reference_S4_tge_v1与CASE/unseen_v2_reference_checker_S4_tge_v1；无旧CASE/源码/合同/原始结果修改。原S1 ELF SHA5c3836e97c99feab88cd8e41773237f6ff642a10558f151b11e112563382b07b同一文件复用，无新C++构建/ELF；OpenLB882924a9cfc8dcdf82909e39530789cb6f5ebcc4和真实1392依赖/3链接/15动态库来源核对。科学算术、R1/R2和read_fields按原冻结文件引用，未改科学门槛。

准备A CASE/unseen_v2_reference_S4_tge_v1/evidence/preparation_A.json SHA{sha(seal)}，{len(bound['inputs_sha256'])}输入一致，{len(protected)}旧保护文件内容不变。15项软件测试通过，默认只读inspection/zero入口exit0、错误SHA只读exit2；4个预留目录仅config/manifest，无原生/VTK/性能/正式/重跑/加时/S5。准备A所有执行flag=false、approved/actual列表空、原生零步NOT_EXECUTED；A不是启动合同。新formal/性能控制器未实施，正式预算null。

计划仅URV_S4_T_dx0p625_TGE_v1_20261104_01，planned_case_id=URV1_U_THIN_T_dx0p625_a100000_SUPPLEMENT；3个零步身份属URV_S4_TGE_ZERO_v1_20261104_01，未实际调用。旧T2.5/T1.25通过原S4 release SHAe5f7de1e584b776f8cc9bf1dbb31f198422ce10984ba8ad7d729220afdcdd19b和completion/acceptance/原始闭包引用，不重命名旧算例。静态节点16515072/链1964544/dt6.510416666666667e-14s/window10368/cap1486848；不是原生geometry/q PASS。新3＋1控制器和只读独立零步证据检查器就绪，执行前另需真实3＋1授权及独立资源采用/外部SHA/净目录/现时资源；默认只读，失败即停，不能进入性能或正式。

资源只快照，候选峰值/RSS/持续速率未测；一组流体19double分布2.33789GiB不是8GiB上限可行性保证，旧细T节点×8/同物理停止步×4的38.4537h仅条件算术。3＋1每次300s/地址空间8GiB、RAM12/盘100首批-8每次/输出4GiB为未采用提案，原12h不可自动提高。有限PERF和正式实现/预算/授权仍另定。

原S4六条各自独立接受/P网格PASS/T中细1.328387035%>1% FAIL及S4阶段未通过保持。原5/2.5/1.25nm失败不被新2.5/1.25/0.625nm分支覆盖，24点聚合/新参考资格/S5不自动接入。reference_qualified=false、MODEL_COMPARISON/physical_validation未评价、strict_error_bound/submission_ready=false、F04 OPEN；S0–S3接受及全部历史FAIL/MRP/A1/S2-LRP/原被拒B/作者声明范围不变。当前无新增流场计算或数值/物理接受，AI辅助准备不代人工终审。

下一具体动作：只读复核准备A/采用范围和3＋1资源提案；获得明确3次零步＋1次初态读取及300s/8GiB资源授权后，再复核封存/届时资源，另存执行绑定并交付用户手动命令。当前不交命令、不启动。下一步GPT-6.1 Sol｜High；新疑难归因/证据矛盾按用户偏好GPT-6 Astra｜High，未声称模型切换。

'''
for name in ['SIM240_AI_CONTEXT.md','AI_HANDOFF_20261015.md']:
    p=ROOT/'docs/reports'/name;before=p.read_text();(OUT/(name+'.before.txt')).write_text(before)
    # Preserve other sessions' whole sections/prefix; prepend a dated authoritative stop.
    first_line,rest=before.split('\n',1);after=first_line+'\n\n'+section+rest.lstrip('\n')
    assert p.read_text()==before,'concurrent shared-state write; stop'
    p.write_text(after);(OUT/(name+'.after.txt')).write_text(after)
assert all(sha(p)==h for p,h in protected.items()) and all(sha(p)==h for p,h in bound['inputs_sha256'].items())
save('final_integrity.json',dict(inputs_verified=len(bound['inputs_sha256']),old_files_unchanged=len(protected),
    preparation_A_sha256=sha(seal),all_execution_permissions_closed=True,
    pristine_planned_directories=4,new_builds=0,native_calls=0,VTK_calls=0,PERF_advances=0,formal_runs=0,
    original_S4_FAIL_preserved=True,S5_started=False))
save('document_manifest.json',{str(p.relative_to(OUT)):sha(p) for p in OUT.rglob('*') if p.is_file() and p.name!='document_manifest.json'})
print(json.dumps(dict(report=str(OUT/'REPORT.md'),preparation_A_sha256=sha(seal),inputs=len(bound['inputs_sha256']),
    protected_old_unchanged=len(protected),software_tests=15,all_execution_permissions_closed=True),ensure_ascii=False,indent=2))

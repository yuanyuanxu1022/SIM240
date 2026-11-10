from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from unittest.mock import patch
import json,hashlib,sys
ROOT=Path('/home/dell/yuanyuanxu/SIM240')
OUT=Path(__file__).resolve().parent
CASE=ROOT/'CASE/unseen_v2_reference_S4_reuse_v1'
CHECK=ROOT/'CASE/unseen_v2_reference_checker_S4_reuse_v1'
sys.path.insert(0,str(CHECK/'analysis'))
from evidence import sha,need
import stage_s4 as stage

def save(p,d):
    with p.open('x') as f: json.dump(d,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')

def main():
    verify=json.loads((OUT/'B_seal_verification_corrected.json').read_text())
    digest=verify['B_sha256'];b=CASE/'evidence/preparation_B.json'
    with patch('subprocess.Popen',side_effect=AssertionError('No children in final evidence check')):
        bound=stage.verify_seal(b,digest);stage.verify_zero_receipt(bound)
    need(b.with_suffix('.sha256').read_text().strip()==digest,'B sidecar drift')
    protected=json.loads((OUT/'protected_inputs_and_outputs_before.json').read_text())
    need(all(sha(p)==h for p,h in protected.items()),'protected input changed')
    before_files={p for p in protected if Path(p).is_relative_to(CASE) or Path(p).is_relative_to(CHECK)}
    now_files={str(p) for folder in (CASE,CHECK) for p in folder.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
    need(now_files-before_files=={str(b),str(b.with_suffix('.sha256'))},'unexpected new package files')
    stage.require_pristine(bound['prepared_runs'])
    need(not (CASE/'launch_attempts').exists() and not (CASE/'analysis_results').exists(),'formal work started')
    need(not list(CASE.rglob('diagnostics.csv')) and not list(CASE.rglob('completion.json')),'unexpected time-stepping artifacts')
    native=json.loads((OUT/'native_review.json').read_text());supp=json.loads((OUT/'supplementary_verification.json').read_text())
    stamp=datetime.now(ZoneInfo('Asia/Shanghai')).isoformat()
    text=f"""# S4 原生18＋6零步证据独立复核与准备B

核对时间：{stamp}。这是用户明确委托的自有项目 AI 辅助内部证据核对，不是独立人工科学终审或期刊审稿。用户范围：按原 URV-v1／MRP／A1／S4-MIP-v1 完整复核已有18＋6，合格后另存执行权限关闭的准备B；不重跑，不启动性能推进或正式计算。

**结论：既有18次原生零步和6次初态读取通过本轮完整独立证据复核；有效准备B已另存，全部执行权限关闭。** 首次报告工具的计数错误、首份B候选的活动日志错误均保留，下文分别说明；不得使用被拒的首份候选。

## 1. 有效封存和运行身份

- 有效B：`CASE/unseen_v2_reference_S4_reuse_v1/evidence/preparation_B.json`，kind=`S4_PREPARATION_B_NOT_AUTHORIZATION`，SHA256 `{digest}`，3248项输入；sidecar为同目录preparation_B.sha256。
- 原准备A SHA `e9d12e68eaa324bd8e78ad57825710936f9e00518faf39337923b930ad82a165`（2976项）和原零步执行release SHA `a62e6f3c96292bec5ab73796789718f28ba2b88232af9f55104697dc30b81d09`（2998项）保持。B保留两者全部输入，并绑定实际审计、独立复核和处置记录。
- 审计身份 `URV_S4_ZERO_v1_20261103_01`；六配置为 `URV1_U_THIN_{{P,T}}_dx{{5,2p5,1p25}}_a100000`，每配置describe/precheck/initialize三种mode。
- 六个正式预留身份 `URV_S4_{{P,T}}_dx{{5,2p5,1p25}}_reuse_v1_20261103_01`保持prepared；actual_formal_run_ids和所有approved列表为空。actual_audit_run_ids为真实18个原生ID，actual_initialized_frames_read=6。独立复核额外6次只读保存场，不冒充新的原生调用或原审计授权。

## 2. 来源与完整性

逐项重哈希2998项release输入、2976项A输入，验证授权原话/提问、各stage精确来源、编译依赖和先行S3/S2已完成证据。原始审计清单234项，连同清单自身与verification共236文件，文件集合及内容一致；18条progress与final records逐条一致，控制日志18条顺序/身份/退出/0步一致。3218项既有受保护文件在复核前后不变，包内只新增有效B及sidecar。

复用同一S1 ELF，SHA `5c3836e97c99feab88cd8e41773237f6ff642a10558f151b11e112563382b07b`。真实历史build_environment SHA `8caca1cf39d043b57ab9675a3de146afea185790ac6110126601da551432d0eb`，1392编译依赖、3链接库、15动态库、编译器及源码指纹闭包通过；13个科学文件（10 common＋check_results/evidence/read_fields）与S3原字节相同。没有新编译、反汇编或物理内核修改；仅复用历史限定机器审计，不声称完整机器路径等价。

## 3. R1：实际参数和原生输出

逐条重解析run_config、manifest、effective_config、execution_audit、process_receipt、exit_code、boundary/result，而非只看PASS摘要。h30/d80/w120/P=Ly240nm、H70nm、a100000m/s²，P+y/T+x；dt、网格、统计窗和最大步分别按独立有理数算术重算。

|dx/nm|核心流体节点|壁面链|原统计窗/最大步|对应初态J预期（m²/s）|
|---:|---:|---:|---:|---:|
|5|32,256|30,528|162/23,232|1.4583333333333335e-14|
|2.5|258,048|122,496|648/92,928|3.645833333333334e-15|
|1.25|2,064,384|490,752|2592/371,712|9.114583333333335e-16|

P/T各档均匹配；12份原生边界材料计数吻合独立XZ枚举并沿Y延拓。candidate=valid_distance=installed，q及installed_q全部为0.5，fallback/missing_neighbor/unresolved均0。18次原生独立退出0、无超时/资源终止，单次elapsed均在原300秒内；保存的原资源/输出预算证据满足门槛。全部collide_and_stream_calls=0，无steady diagnostics或mass_capture。

初态J=H·a·dt/2是已定义的半步体力速度响应，最大相对偏差3.567812711935403e-11，符合原R1约束；它不是稳态流量，不能据此提取或比较稳态导度K。统计窗/最大步此处只验证换算与输入接入，未执行这些步数。

## 4. MRP／A1初态路径

对实际effective dx和每档核心节点数，以binary64三个先行乘法、最终math.fma的逐单元顺序复算legacy质量；另逐项加已舍入dx³复算A1体积，用独立准确求和检验补偿质量。六条均与原result浮点值精确相同。

修正初始质量均为4.0320000000000006e-18kg；解析体积4.032e-21m³。体积最大相对偏差1.8851142868925308e-11，小于原1e-10，不改容差。逐档legacy尾数不同符合不同节点累加路径，不当作时间质量漂移。初态density_delta/max_density_deviation均0，双精度切片rho均1；初态Mach最大3.0070326520293012e-10。这些只建立初态证据，不替代正式全过程质量/密度/Mach门。

h75逐点密度捕获、190差异点重放及20列旧轨迹回归为 `NOT_APPLICABLE_S0_ONLY`。本轮没有新h75重放，不用初态均匀密度的精确算术宣称历史唯一归因已建立；旧S0/A1结论及历史限制保持。

## 5. R2：六配置初态场闭包和独立实际读取

逐配置核对原读取进程退出0、无超时，唯一且属于本配置的读回路径，PVD→VTM→VTI完整三文件闭包及指纹，step=0/frame=1。独立在原始输出之外，用冻结read_fields.py只读打开6个已存场，各一次、退出0；六份新报告与各自原报告完全相同，过程记录、命令、耗时和报告SHA均保存。

校验核心流体节点唯一/无遗漏/无周期overlap重复，速度m/s、周期压力扰动Pa、耗散m²/s³，几何与坐标、有限值/非负耗散，初态压力为0，方向与半步力响应正确，场积分J与自身原始result在float32导出舍入界内一致。双精度切片672/2688/10752行和速度/压力/耗散剖面另逐档核对。没有重新生成初始化场，没有调用求解器。

## 6. B权限和入口检查

有效B的simulation/formal/native_zero/initial_readback/PERF/retry/extension/S5权限全部false；approved_runs、approved_run_ids、approved_audit_run_ids为空；AI_may_start_solver=false。

B封存后通过verify_seal、全部3248输入及verify_zero_receipt；默认正式控制器只读检查退出0、solver_executed=false、zero_audit_status=PASSED。formal/zero权限验证器均拒绝B；对正式入口的--execute尝试在无子进程保护下退出2（current package authorizes zero-step preparation only），子进程调用0，未生成launch_attempt或analysis_results。此为关闭权限的安全拒绝核验，不是正式运行尝试；未调用原生或推进时间。

## 7. 本轮辅助工具错误与处置（保留，不能删除）

1. `review_existing.py`首次由S3迁移时漏改一处最终计数4→6。六份只读场均已成功并写出回执，随后汇总断言失败。原脚本/错误/控制台保存为review_existing_initial.py.txt、review_failure.json、review_console.log，处置见helper_correction.json。仅修正本轮报告helper计数，随后finalize_existing_review.py从既有回执完成文件复核；无原生或场读取重试，未改冻结规则。
2. 第一份B候选错误地绑定其正在写入的seal_console.log。首次封存内检查后，最终打印改变了该日志；事后完整重哈希发现且仅发现这一项漂移。第一候选裁定不可用，其JSON/sidecar/当时检查记录保存在rejected_B_candidate/，失败指纹及原因在first_B_post_emission_drift.json、B_candidate_recovery_record.json。修正封存helper排除活动日志，绑定已完成的日志快照，并从未变的原A/原始证据/独立验收另存本报告第1节有效B。未覆盖任何任务前原包或原始结果，未修改数值规则，没有再调用原生或读取场。
3. peer-review intake首次将宿主AI的处理范围填入仅支持本地工具的handling字段，工具拒绝；原声明保留。工具范围按本地确定性执行单列后READY_FOR_LOCAL_REVIEW。宿主AI另在review_scope.json如实记录，并未声称宿主为本地。该格式处置不是科研PASS/FAIL。

这些为本轮可直接核验的工具错误，不把它们包装为原生计算、物理结论或历史争议的裁决。不能把第一次候选的旧B_seal_verification当作最终有效封存；最终以B_seal_verification_corrected.json和本节有效SHA为准。

## 8. 状态边界和下一步

- ZERO_STEP_INDEPENDENT_REVIEW_PASS=true；ZERO_STEP_GEOMETRY_PASS=true；R1/R2与初态MRP/A1分项通过，B权限关闭。
- 正式NUMERICAL_GATE=NOT_EVALUATED、geometry_PASS=null、RESULT_PASS=false（尚未正式评价）；S4_GRID_CHECKS_PASS/稳态K/驱动力控制均未评价。
- REFERENCE_QUALIFIED_FOR_CASE/reference_qualified=false；MODEL_COMPARISON/physical_validation=NOT_EVALUATED；strict_error_bound_established/submission_ready=false；F04 OPEN_OUT_OF_SCOPE。
- 作者对h60/d80、h30/d80未用于系数/条件选择的声明仍仅为作者声明；external_history_independently_verified=false，不扩张为独立盲法核查。
- S0–S3已接受证据保持；旧横槽FAIL/380项差异、MRP静态FAIL、旧v1 HOLD、HISTORICAL_EXCLUSIVE_ATTRIBUTION=NOT_ESTABLISHED不回写。

本轮新增原生调用0、求解时间步0、构建0，保存场只读读取6次；未重跑原审计、未性能推进、未正式计算、未自动进S5，未提交/推送/外发项目资料。下一最小任务为另行审定正式S4六条范围、资源决策及授权绑定前条件，届时再决定是否另立有限PERF，不自动实施或启动。细格性能、收敛步数、能否在原12小时上限内完成仍未实测；既有S2缩放估计不得充当S4测量。

## 9. 审查材料与技能说明

主要证据：independent_review_acceptance.json、native_review.json、native_calls.csv、initial_statistics.csv、supplementary_verification.json、六个reader过程/field_reread报告、B_seal_verification_corrected.json及final_integrity.json。B直接绑定独立验收及其过程证据；本报告与最终共享交接在外层document_manifest.json记录，避免循环封存。

使用[peer-review](/home/dell/.codex/skills/peer-review/SKILL.md)组织证据边界和内部审查；仅用户自有项目授权，无期刊/编辑决定，AI辅助不能替代人工科学责任。技能来源：Kassis, T., Agarwal, V., He, Y., Patel, D., & Brueckner, A. M. (2026), *Scientific Agent Skills: A Library of Procedural Knowledge for Research Agents*, [doi:10.48550/arXiv.2609.00065](https://doi.org/10.48550/arXiv.2609.00065)。2026-11-03公开arXiv核对最新记录为v2（2026-09-02修订）；此引文只说明工作工具，不是CFD结果依据。没有向公共查询提交项目内容。
"""
    with (OUT/'REPORT.md').open('x') as f:f.write(text)
    section=f"""## S4原生18＋6独立复核通过，有效准备B已封存，执行权限关闭（{stamp}）

用户授权本轮完整独立复核已有18＋6并在合格后另存关闭B；不重跑、不启动PERF或正式计算。入口docs/reports/{OUT.name}/REPORT.md、independent_review_acceptance.json、B_seal_verification_corrected.json、final_integrity.json。AI辅助内部证据审查，不冒充独立人工终审。

审计URV_S4_ZERO_v1_20261103_01，18原生describe/precheck/initialize各6；2998项release输入和2976项原A、234项raw清单/共236审计文件及18progress/控制日志一致，3218旧保护文件不变。R1有效配置/有理数时步/初态力响应、R2六唯一初态场PVD/VTM/VTI闭包、进程退出/资源/零步约束通过。仅只读打开6个已保存场，每个一次；新读回均与原报告完全相同，未再调用原生。新增native0、steps0、build0、PERF0、正式0，未进S5。

几何h30/d80/w120/P=Ly240nm，P+y/T+x，dx5/2.5/1.25nm各P/T；核心节点32256/258048/2064384，壁面链30528/122496/490752，原生q/installed_q均.5，fallback/unresolved0。MRP初态旧质量FMA、A1逐项体积和补偿质量独立复算均精确相同；最大体积相对差1.8851142868925308e-11<1e-10，初态J半步响应最大相对差3.567812711935403e-11，density偏差0。h75密度捕获/旧轨迹回归为NOT_APPLICABLE_S0_ONLY，未新重放。13科学文件同S3原字节；同S1 ELF 5c3836e97c99feab88cd8e41773237f6ff642a10558f151b11e112563382b07b，历史1392依赖/3链接/15动态库来源闭包通过，无新指令审计。

有效B CASE/unseen_v2_reference_S4_reuse_v1/evidence/preparation_B.json，SHA {digest}，3248输入，kind S4_PREPARATION_B_NOT_AUTHORIZATION；sidecar同目录preparation_B.sha256。实际18audit ID/6原初态读取已记，actual正式及所有approved列表空。simulation/formal/native_zero/initial_readback/PERF/retry/extension/S5均false、AI_may_start_solver=false；默认只读控制器退出0、无子进程；formal/zero权限拒绝，正式--execute受控检查退出2、无子进程/attempt。原A SHA e9d12e68eaa324bd8e78ad57825710936f9e00518faf39337923b930ad82a165及零步release SHA a62e6f3c96292bec5ab73796789718f28ba2b88232af9f55104697dc30b81d09保持，不覆写原签发许可。

本轮工具错误已保留并处置：首次报告helper末断言遗留4份而非6份，在六读取成功后失败；保存原脚本/失败，以已存回执文件续核，未重读。首份B候选误绑定自身活动seal_console.log，打印后仅该项漂移；首候选不可用，移存报告目录rejected_B_candidate/保留，原因/指纹在first_B_post_emission_drift.json及B_candidate_recovery_record.json；修正helper排除活动日志并绑定已完成快照，另存上述有效B，不引用首候选作为接受依据。最终只认B_seal_verification_corrected.json和上述SHA。未改科学门槛/原始结果，不隐去本轮错误。

ZERO_STEP_INDEPENDENT_REVIEW_PASS/ZERO_STEP_GEOMETRY_PASS=true；正式NUMERICAL_GATE=NOT_EVALUATED、geometry_PASS=null、RESULT_PASS=false，S4网格/稳态K/线性控制未评价，reference资格false、MODEL_COMPARISON/physical_validation未评价、strict_error_bound/submission_ready=false、F04 OPEN。S0–S3接受、旧FAIL/380差异/MRP静态FAIL/旧v1 HOLD和历史唯一归因NOT_ESTABLISHED保持。作者未用数据声明范围不变、独立核实false。

下一具体动作：另行审定正式S4六条范围、资源决策及授权绑定前条件，届时决定是否需单独有限PERF；当前不自动实现/启动。S4性能/收敛步数未实测，不能把S2缩放当S4实测；原12小时细格上限是否足够未证。没有新启动命令或正式授权。下一步模型GPT-6.1 Sol｜High（正式S4范围/资源审查）。
"""
    for name in ['SIM240_AI_CONTEXT.md','AI_HANDOFF_20261015.md']:
        path=ROOT/'docs/reports'/name;old=path.read_text();before=(OUT/('before_'+name)).read_text()
        need(old==before,'concurrent shared-state change: '+name)
        start=old.index('\n## ')+1;end=old.find('\n## ',start+1)
        path.write_text(old[:start]+section+'\n'+(old[end+1:] if end>=0 else ''))
    need(all(sha(p)==h for p,h in bound['inputs_sha256'].items()),'B drift after report')
    need(all(sha(p)==h for p,h in protected.items()),'old evidence drift after report')
    save(OUT/'final_integrity.json',dict(checked_at=stamp,PASS=True,B_sha256=sha(b),B_sidecar_matches=True,B_inputs_verified=len(bound['inputs_sha256']),protected_existing_files_verified=len(protected),package_new_files_only=['evidence/preparation_B.json','evidence/preparation_B.sha256'],review_PASS=True,original_A_and_release_unchanged=True,raw_audit_file_set_unchanged=True,native_calls=0,saved_field_reader_calls=6,solver_steps=0,builds=0,formal_started=False,performance_started=False,S5_started=False,first_B_candidate_usable=False,first_candidate_preserved=True,active_console_excluded=True,shared_state_updated=['docs/reports/SIM240_AI_CONTEXT.md','docs/reports/AI_HANDOFF_20261015.md']))
    manifests={str(p.relative_to(ROOT)):sha(p) for p in sorted(OUT.rglob('*')) if p.is_file() and p.name!='document_manifest.json'}
    # Shared state is mutable; freeze only copied after-state snapshots in this report manifest.
    save(OUT/'document_manifest.json',manifests)
    print(json.dumps(dict(PASS=True,B_sha256=digest,B_inputs=3248,report=str(OUT/'REPORT.md'),native_calls=0,saved_field_reads=6,formal_started=False,performance_started=False,report_manifest_files=len(manifests)),ensure_ascii=False))

if __name__=='__main__':main()

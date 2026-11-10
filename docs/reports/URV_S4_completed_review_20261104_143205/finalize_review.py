"""Publish an evidence-bounded internal audit and update shared handoff only."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import hashlib, json

ROOT=Path('/home/dell/yuanyuanxu/SIM240')
OUT=Path(__file__).resolve().parent
CASE=ROOT/'CASE/unseen_v2_reference_S4_reuse_v1'
load=lambda p:json.loads(Path(p).read_text())
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
save=lambda p,v:Path(p).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
now=datetime.now(ZoneInfo('Asia/Shanghai')).isoformat()
x=load(OUT/'independent_review.json');s=load(OUT/'status_snapshot.json')
release=CASE/'evidence/S4_formal_launch_release_v1_20261104_01.json'
b=load(release);attempt=CASE/'launch_attempts'/x['release_sha256']
protected=load(OUT/'protected_inputs_and_outputs.json')
assert all(sha(p)==h for p,h in protected.items())
records=[]
for record in b['prepared_runs']:
    run=Path(record['output_directory']);c=load(run/'completion.json')
    ap=CASE/'analysis_results'/record['run_id']/'acceptance.json'
    times={k:p.stat().st_mtime for k,p in [('run_log_last_write',run/'run.log'),('completion',run/'completion.json'),('acceptance',ap)]}
    assert times['run_log_last_write']<=times['completion']<=times['acceptance']
    records.append(dict(run_id=record['run_id'],resources_before=c['resources_before'],
        mtime_unix=times,mtime_local={k:datetime.fromtimestamp(v,ZoneInfo('Asia/Shanghai')).isoformat() for k,v in times.items()}))
for previous,following in zip(records,records[1:]):
    assert previous['mtime_unix']['acceptance']<following['mtime_unix']['completion']
grid_time=datetime.fromtimestamp((attempt/'S4_grid_report.json').stat().st_mtime,ZoneInfo('Asia/Shanghai')).isoformat()
assert records[-1]['mtime_unix']['acceptance']<=(attempt/'S4_grid_report.json').stat().st_mtime
assert records[0]['resources_before']['disk_free_bytes']>=100*1024**3
aux=dict(recorded_at=now,records=records,grid_report_last_modified=grid_time,
    order_consistent_with_filesystem_times=True,filesystem_time_is_auxiliary_not_independent_process_exit=True,
    independent_parent_controller_exit_code='NOT_RECORDED',
    controller_stop_message=s['controller_log_tail'],protected_files_unchanged=len(protected),
    raw_files=sum(r['raw_files'] for r in x['runs']),raw_bytes=sum(r['raw_bytes'] for r in x['runs']),
    intake_helper_correction='Extra policy_context field rejected by intake schema, moved to intake_context.txt before valid intake; no CFD check or solver executed in this correction.')
save(OUT/'supplementary_verification.json',aux)

table='\n'.join(f"|{r['direction']}|{r['dx_nm']:g}|{r['steps']}|{r['solver_seconds']:.3f}|{r['K_m3']:.12e}|PASS／true／true|" for r in x['runs'])
diagnostics='\n'.join(f"|{r['direction']}／{r['dx_nm']:g}|{r['window_std']:.8e}|{r['window_span']:.8e}|{r['corrected_mass_max']:.4e}|{r['legacy_mass_max']:.4e}|{r['density_deviation_max']:.4e}|{r['Mach_max']:.4e}|{r['section_final']:.4e}|" for r in x['runs'])
grids='\n'.join(f"|{g['direction']}|{g['observed_order']:.9f}|{g['medium_fine_change_percent']:.9f}%|{g['GCI_fine_percent']:.9f}%|{'PASS' if g['GRID_CHECKS_PASS'] else 'FAIL'}|" for g in x['grid'])
maxval=lambda k:max(abs(r[k]) for r in x['runs'])
report=f'''# S4 已结束结果的完整独立复核（AI 辅助内部工作报告）

**结论：六条原生计算及逐条独立验收通过；S4 在横槽网格门停止，整个阶段未通过。** 沿槽三网格通过；横槽中—细变化1.328387035%超过原1%上限，虽细网格GCI估计0.912232592%通过另一项，仍不能补偿前项失败。不改门槛、不重跑、不加时、不进入S5。

## 1. 范围、结束证据与来源

用户此前已要求“批次实际结束后，按原URV-v1／MRP／A1／S4-MIP-v1／S4-FRD-v1完整独立分析已有结果”。本轮询问是否结束，14:29:14北京时间只做一次进程/完成记录快照，确认无目标控制器或原生进程，原会话已消失；六份completion和自动acceptance齐全。最后网格报告文件修改时间为{grid_time}（文件系统辅助时间，不伪称独立退出时刻）。控制日志保存原文 `EvidenceError: S4 grid evidence failed; no retry/extension/next stage`。S4_grid_report.json存在且总GRID_CHECKS_PASS=false，S4_completed.json不存在，符合冻结控制器先写网格报告、失败即停的代码路径。父控制器独立退出码未记录，不能从报错自行补造为2；六条原生独立退出码和本轮六条检查器退出码均确证为0，无原生超时/资源停止。

正式release：`{release.relative_to(ROOT)}`；SHA `{x['release_sha256']}`。全部{x['inputs_verified']}项输入重哈希一致；核对准备B、原18＋6零步及来源/前序S3控制、真实正式授权和资源决策。精确复用S1 ELF `5c3836e97c99feab88cd8e41773237f6ff642a10558f151b11e112563382b07b`，OpenLB `882924a9cfc8dcdf82909e39530789cb6f5ebcc4`；本轮未构建或重新执行限定指令审计，依靠封存来源与同一ELF身份核对。

六个run_id按原序保留：

'''+'\n'.join(f"- `{r['run_id']}`" for r in x['runs'])+f'''

原协议入口 `docs/reports/URV_S4_formal_scope_resource_review_20261104_090724/PROTOCOL.md`；原科学门槛 `CASE/unseen_v2_reference_checker_S4_reuse_v1/common/acceptance_spec.json`；执行源 `CASE/unseen_v2_reference_S4_reuse_v1/scripts/run_S4.py`。源码、配置、合同、旧原始结果与自动接受记录未修改。

## 2. 实际完成的复核

在本报告新目录执行六次冻结check_results.py，每次仅读取已有结果并将新记录写到replay_<run_id>；六次保存场读取共读回{x['total_field_frames_read']}帧。每份新acceptance.json与fields.json分别与原自动文件完全一致。逐个核对completion绑定、计算前后输入映射、原始输出集合及内容；合计{aux['raw_files']}个原始输出、{aux['raw_bytes']}bytes（completion另计）。{x['protected_files_unchanged']}份受保护文件前后内容不变。

重新计算{x['diagnostic_rows']}行诊断、{x['full_windows']}个完整统计窗；各条最后一窗均为首次全部满足稳态条件，前一窗至少一项不满足。除冻结检查器复算外，报告脚本另外直接复算末窗样本标准差/跨度、质量账本、密度/Mach/Re、截面流量差、K与三网格算术。复核边界与实际场的单位、方向、材料/节点/链数、q、保存时间和场积分闭合。这个独立性指从原始证据重做验收，并不新增另一种物理解法或实验验证。

## 3. 参数与六条结果

固定间隙全充液单相、无滑移矩形沟槽：h=30nm，d=80nm，w=120nm，周期及Ly=240nm，平均厚度H=h+d/2=70nm；rho=1000kg/m³，nu=1e-6m²/s，mu=0.001Pa·s，a=100000m/s²，tau=1。沿槽P为+y，横槽T为+x；x/y周期，Bouzidi静止壁，D3Q19_FORCE/ForcedBGK。不是移动挤压/两相流计算，不输入V2系数。

J为单位平面面积的体积流量（m²/s）；K=nu·J/a，单位m³；平均速度U=J/H；阻力系数R=mu/K。单条求解墙钟包含该原生进程初始化和输出，不是纯步进时间。

|方向|dx (nm)|实际步数|原生求解秒|K (m³)|NUMERICAL_GATE／RESULT_PASS／geometry_PASS|
|---|---:|---:|---:|---:|---|
{table}

六条原生耗时合计{x['formal_solver_seconds']:.3f}s（{x['formal_solver_seconds']/3600:.6f}h），不含检查/哈希等其他耗时；细格P/T分别{x['runs'][4]['solver_seconds']/3600:.6f}/{x['runs'][5]['solver_seconds']/3600:.6f}h，均在12h原上限内。各条前可用内存≥12GiB、盘≥8GiB，首条记录盘≥100GiB，输出均≤4GiB；不把这些快照当成全程RSS峰值或资源硬界。

## 4. 数值与几何门槛

|方向／dx nm|末窗相对std|末窗相对span|补偿质量最大相对变化|旧质量最大相对变化|最大密度偏差|最大Mach|末态截面相对差|
|---|---:|---:|---:|---:|---:|---:|---:|
{diagnostics}

六条均满足原规则：补偿质量严格<1e-10（本次最大{maxval('corrected_mass_max'):.8e}），质量双账本差≤1e-13（最大{maxval('ledger_max'):.8e}），密度偏差≤1e-6，Mach严格<0.05，Re_H≤0.01（最大{maxval('Re_H_max'):.8e}），完整末窗样本std≤1e-6/span≤5e-6，横向通量≤1e-12m²/s（最大{maxval('cross_flux_window_max'):.8e}），末态截面差≤1e-5。

三网格流体节点32256/258048/2064384，壁面链30528/122496/490752；材料计数/几何掩膜通过；q_min=q_max=0.5，候选链与安装链相等，fallback/unresolved均0。体积相对误差最大{maxval('volume_relative_error'):.8e}<1e-10；各条全序列有限，保存场与双精度切片/全域积分闭合通过。原生RESULT_PASS=false表示留给外部独立检查；外部RESULT_PASS=true，两者不混淆。

末窗靠近门槛符合首次达标即停的控制规则；它只说明时间稳态合格，不能替代空间网格检查。旧质量列原样保留并复算，无历史差异删除。h75精确回归和密度捕获重放仅适用S0，本次标记NOT_APPLICABLE_S0_ONLY，不虚填S4密度重放PASS。已有MRP/A1指令审核的范围限制及历史唯一归因NOT_ESTABLISHED保持。

## 5. 三网格：明确保留横槽失败

原规则r=2、Fs=1.25；K随加密同向变化、差分不近零且观测阶p正且有限。中细差 `abs(K_medium/K_fine-1)` 与细网格GCI估计均须≤1%。从新验收记录重做s4_grid，再独立直接计算阶数/两门，与原控制器网格报告完全一致。

|方向|观测阶p|中—细变化（上限1%）|细网格GCI估计（上限1%）|方向网格判定|
|---|---:|---:|---:|---|
{grids}

沿槽通过。横槽中—细变化超出门槛0.328387035个百分点，故横槽及S4整体GRID_CHECKS_PASS=false。不能只挑GCI通过项、把1%改成2%、把单条稳态通过当网格通过，或因六条已算完补写成功S4_completed.json。GCI与u仍为数值敏感性估计，不是严格误差界/置信区间。本轮未证明超差的具体物理或离散误差机制，也不由此认定V2失败或成功。

## 6. 科学结论与下一停点

已验证：六条固定离散网格结果各自通过原数值/几何/流场核对；沿槽三网格符合原阶段门。未通过：横槽三网格中—细变化门，S4阶段接受=false。未评价：S5三驱动力控制、跨阶段参考资格/F04、原公式/V2正式比较、物理验证和投稿资格。

`REFERENCE_QUALIFIED_FOR_CASE=false`，`reference_qualified=false`，`MODEL_COMPARISON=NOT_EVALUATED`，`physical_validation=NOT_EVALUATED`，`strict_error_bound_established=false`，`submission_ready=false`，F04 OPEN。S0–S3已接受证据不因本次失败自动撤销；旧FAIL、380项旧差异、MRP静态FAIL、旧v1 HOLD、S2-LRP、第一候选B拒绝记录与作者外部非使用声明范围继续保留。作者声明不等于外部历史独立取证。

下一具体动作只可另定横槽网格未过的处置审查范围，先核证据是否足以判断空间离散问题及需要何种最小补证；不在本报告自动设计/实施第四网格、续算、改公式或门槛，也不进入S5。长计算若以后需要仍另行授权；此次分析无需再索同范围结果分析授权。

## 7. 审核限度与文件

本报告为AI辅助的内部计算验收工作报告，非人工科学终审或期刊审稿决定。作者仍需亲自理解/复核并负责。未宣称实验或完全独立软件参考实现，不把同一检查器的重复执行误写为独立物理验证。

证据入口：status_snapshot.json、controller_log_tail.txt、protected_inputs_and_outputs.json、independent_review.json、independent_grid_report.json、run_summary.csv、supplementary_verification.json以及六个replay目录。review_completed.py可读但单次输出拒绝覆盖，不应为查看报告再次运行。此前intake多余policy_context字段被验证器拒绝，初稿保留；移到单独context说明后声明验证通过。这只是报告工具接口修正，无科学门槛/结果改动，也未引起CFD检查重跑。

使用[peer-review](/home/dell/.codex/skills/peer-review/SKILL.md)与[scientific-writing](/home/dell/.codex/skills/scientific-writing/SKILL.md)。技能工具出处：Kassis, T., Agarwal, V., He, Y., Patel, D., & Brueckner, A. M. (2026), *Scientific Agent Skills: A Library of Procedural Knowledge for Research Agents*, [arXiv:2609.00065](https://arxiv.org/abs/2609.00065)。2026-11-04公开元数据核对为v2，无期刊版本记录；该来源仅解释工作流程，不支持本项目CFD数值结论。公开查询未包含项目内容。
'''
(OUT/'REPORT.md').write_text(report)
save(OUT/'disposition.json',dict(review_status='COMPLETE_EXISTING_RESULTS_ONLY',
    batch_status='ENDED_STOPPED_AT_TRANSVERSE_GRID_GATE',SIX_RUN_ACCEPTANCE=True,
    S4_GRID_CHECKS_PASS=False,S4_STAGE_ACCEPTED=False,reference_qualified=False,
    MODEL_COMPARISON='NOT_EVALUATED',physical_validation='NOT_EVALUATED',submission_ready=False,
    solver_calls=0,checker_replays=6,saved_field_reader_calls=6,frames_read=68,
    retries=0,extensions=0,S5_started=False,next_action='Separately scope read-only disposition of transverse grid failure; no new execution authorized.'))

section=f'''## S4实际结束：六条独立接受，横槽网格FAIL，阶段未通过（{now}）

用户先前授权结束后按原URV-v1／MRP／A1／S4-MIP-v1／S4-FRD-v1完整独立分析，本轮询问是否结束。单次实查{s['snapshot_started']}无目标控制器/原生进程、原会话消失，六completion/acceptance齐全；网格报告存在且横槽FAIL，S4_completed.json未生成。原控制日志EvidenceError: S4 grid evidence failed; no retry/extension/next stage，与冻结失败即停路径一致；父控制器独立退出码NOT_RECORDED，未伪补。此前第一节11:46运行快照已被本节实际证据覆盖；并行上方教学/汇报仍是各自历史快照。

已完成独立完整复核：入口{OUT.relative_to(ROOT)}/REPORT.md、independent_review.json、independent_grid_report.json、run_summary.csv、supplementary_verification.json。正式release CASE/unseen_v2_reference_S4_reuse_v1/evidence/S4_formal_launch_release_v1_20261104_01.json SHA{x['release_sha256']}；3284绑定输入一致，3563受保护文件前后不变。六次冻结检查器＋六次真实保存场读取68帧，新acceptance/fields均与原自动记录完全相同；61650诊断行、54852完整窗复算，首次达标窗/质量双账本/密度/Mach/Re/截面/几何q与材料/时序及积分通过，6条原生及新检查器均exit0、无超时/资源停止。MRP/A1/S0专用密度重放本阶段NOT_APPLICABLE_S0_ONLY；未新做原生/指令审计。

原六run_id依序URV_S4_P_dx5_reuse_v1_20261103_01、URV_S4_T_dx5_reuse_v1_20261103_01、URV_S4_P_dx2p5_reuse_v1_20261103_01、URV_S4_T_dx2p5_reuse_v1_20261103_01、URV_S4_P_dx1p25_reuse_v1_20261103_01、URV_S4_T_dx1p25_reuse_v1_20261103_01。各条NUMERICAL_GATE=PASS/RESULT_PASS=true/geometry_PASS=true。P三格K=2.7691299257287254e-23/2.754644779506946e-23/2.750102454184732e-23m³；T=3.64797692375804e-24/3.517910669377557e-24/3.471791836744987e-24m³。P中细变化0.165169313%、GCI0.094320912%通过；T中细变化1.328387035%>1%（FAIL）、GCI0.912232592%≤1%。因此SIX_RUN_ACCEPTANCE=true而S4_GRID_CHECKS_PASS=false/S4_STAGE_ACCEPTED=false；原失败不改。六条求解共16612.905s，不含其他处理；细格P/T约3.2322/1.2017h，均在12h原上限内。

reference_qualified=false、REFERENCE_QUALIFIED_FOR_CASE=false、MODEL_COMPARISON/physical_validation未评价、strict_error_bound/submission_ready=false、F04 OPEN、S5未启动。S0–S3接受、旧FAIL/380差异/MRP静态FAIL/旧v1 HOLD/历史唯一归因限制、S2-LRP和原被拒B/作者声明范围保持。本轮仅新增本报告目录/状态快照目录并同步共享状态，无源码/配置/原结果/合同/阈值更改，无编译/原生/重跑/加时/下一阶段/提交推送，报告不等于人工科学终审。intake未知字段接口错误已保留并修正后通过，不影响CFD证据。

当前卡点：横槽空间网格门不通过；不作具体误差机理或V2性能归因。下一具体动作：另定横槽网格失败的只读处置审查范围，保留原门槛，必要补算/修复须另行协议与授权，不自动重跑、加时或S5。下一步GPT-6.1 Sol｜High；新的多证据矛盾/疑难归因按用户要求GPT-6 Astra｜High，未声称真实切换。

'''
changed=[]
for name in ['SIM240_AI_CONTEXT.md','AI_HANDOFF_20261015.md']:
    path=ROOT/'docs/reports'/name;original=path.read_text()
    (OUT/(name+'.before.txt')).write_text(original)
    start=original.index('\n## ')+1
    end=original.find('\n## ',start+1)
    if end<0:end=len(original)
    updated=original[:start]+section+original[end:].lstrip('\n')
    assert path.read_text()==original, 'concurrent shared-state change; stop rather than overwrite'
    path.write_text(updated)
    (OUT/(name+'.after.txt')).write_text(updated)
    changed.append(str(path.relative_to(ROOT)))
assert all(sha(p)==h for p,h in protected.items())
save(OUT/'final_integrity.json',dict(protected_files_unchanged=len(protected),changed_shared_files=changed,
    solver_calls=0,builds=0,retries=0,extensions=0,S5_started=False,
    analysis_complete=True,S4_STAGE_ACCEPTED=False))
manifest={str(p.relative_to(OUT)):sha(p) for p in OUT.rglob('*') if p.is_file() and p.name!='document_manifest.json'}
save(OUT/'document_manifest.json',manifest)
print(json.dumps(dict(report=str(OUT/'REPORT.md'),grid_time=grid_time,shared_updated=changed,
    protected_unchanged=len(protected),local_document_files=len(manifest)),ensure_ascii=False,indent=2))

"""Document existing evidence and update only current shared-state section."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import hashlib,json
ROOT=Path('/home/dell/yuanyuanxu/SIM240');OUT=Path(__file__).resolve().parent
load=lambda p:json.loads(Path(p).read_text())
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
x=load(OUT/'independent_review.json');s=load(OUT/'supplementary_verification.json')
now=datetime.now(ZoneInfo('Asia/Shanghai')).isoformat()
runs=sorted(x['runs'],key=lambda v:(v['direction'],v['acceleration_m_s2']))
runrows='\n'.join(f"|{v['direction']}|{v['acceleration_m_s2']:g}|{'S2原合同中档' if v['role']=='S2_midpoint' else 'S3新增'}|{v['K_m3']:.15e}|{v['J_m2_s']:.15e}|{v['steps']}|{v['solver_seconds']:.3f}|PASS / true / true|" for v in runs)
controls='\n'.join(f"|{v['direction']}|{v['K_span_over_mean']:.12e}|{v['L_percent']:.12e}%|{v['L_ppm']:.9f}|0.1% = 1000 ppm|通过|" for v in x['controls'])
metrics=[('修正质量全程最大相对变化','corrected_mass_max','<1e-10'),('两修正账本最大差','ledger_max','≤1e-13'),('最大密度偏离','density_deviation_max','≤1e-6'),('最大Mach','Mach_max','<0.05'),('最大Re（h+d尺度）','Re_H_max','≤0.01'),('末态截面相对差','section_final','≤1e-5'),('末窗相对样本std','window_std','≤1e-6'),('末窗相对跨度','window_span','≤5e-6'),('末窗主轴横向通量 / m² s⁻¹','cross_flux_window_max','≤1e-12')]
safety='\n'.join(f"|{label}|{max(v[key] for v in runs):.12e}|{limit}|通过|" for label,key,limit in metrics)
safety+=f"\n|核心体积相对误差绝对值|{max(abs(v['volume_relative_error']) for v in runs):.12e}|≤1e-10|通过|"
windowrows='\n'.join(f"|{v['direction']}|{v['acceleration_m_s2']:g}|{v['full_windows']}|{v['window_std']:.12e}|{v['previous_window_std']:.12e}|{v['window_span']:.12e}|" for v in runs)
identities='\n'.join(f"- `{v['run_id']}`：{v['role']}；completion SHA `{v['completion_sha256']}`。" for v in x['runs'])
report=f'''# S3 四条与 S2 两中档：完整独立结果复核

完成时间：{now}。用户任务：收到批次结束信息后，完整独立分析四条已有结果、两个S2中档基准及两方向三档控制。按原URV-v1／MRP／A1／S3 v1.1／S3-FRD-v1，不重跑、加时或进入S4/S5。本报告为AI辅助的项目内部数值证据审查，供作者核对，不代表人工科学终审或期刊审稿裁决。

## 1. 裁定

S3正式批次已结束，S3_completed.json文件时间为{s['batch_mtime']}。四条新增结果均有独立原生退出0、完整completion、自动接受和本次重新执行的独立接受；两条S2中档继续在各自原S2合同下完整重验，未改绑或重算流场。六条均NUMERICAL_GATE=PASS、geometry_PASS=true、RESULT_PASS=true。

两方向三点控制独立复算与原控制器记录精确一致：P的L={x['controls'][0]['K_span_over_mean']:.16e}，T的L={x['controls'][1]['K_span_over_mean']:.16e}，均≤0.001。S3_FOUR_RUN_ACCEPTANCE、S2_TWO_MIDPOINT_REUSE_ACCEPTANCE和S3_CONTROL_PASS均true。本阶段没有需补跑或加时的失败项。

该结论关闭常规间隙U_REG在同一中档网格上的三档驱动力控制问题。S2网格证据和S3控制证据已齐全，但本轮没有执行跨阶段参考资格裁定或24条聚合；REFERENCE_QUALIFIED_FOR_CASE/reference_qualified仍false，MODEL_COMPARISON/physical_validation仍NOT_EVALUATED，strict_error_bound_established/submission_ready仍false。不能据此宣布V2准确、应用效果通过或论文闭环。

## 2. 已查证的来源和完成证据

S3原正式合同：`CASE/unseen_v2_reference_S3_reuse_v1_1/evidence/S3_formal_launch_release_v1_1_20261103_01.json`，SHA `{x['S3_release_sha256']}`。2632项输入当前逐项匹配；四条completion各自的inputs_before/after完整等于原合同。真实授权、采用的S3-FRD-v1、准备B、零步证据、来源/批准身份/输出目录均通过原只读校验。合同actual_formal_run_ids=[]是签发时快照，未据运行事实修改旧合同。

S2原正式合同：`CASE/unseen_v2_reference_S2_reuse_v1/evidence/S2_formal_launch_release_LRP_v1_20261102_02.json`，SHA `{x['S2_release_sha256']}`。2160项输入当前一致；两中档原始completion、接受、完整输出与S3冻结引用一致，其原合同身份保持。两个方向的三档配置除run_id、输出目录和驱动力外逐项相同，避免将不同边界/网格/平均定义混作线性控制。

继续复用S1原ELF，SHA `5c3836e97c99feab88cd8e41773237f6ff642a10558f151b11e112563382b07b`；绑定构建记录中的OpenLB版本宏为`882924a9cfc8`，源码/头文件/构建/动态依赖的完整来源闭包均保持。没有重编译或运行任何原生模式。

原始输出每条37文件，六条222文件，其中S3新增148文件；实际集合与各自completion清单及哈希精确一致。completion封装在原清单生成后写入，单独由原acceptance的completion_sha256及本次保护清单固定，不要求其自包含哈希。六次检查器全退出0，所得acceptance.json和fields.json与原记录分别完全相同。六次实际pvpython保存场读取共60帧，完整PVD/VTM/VTI引用载荷、唯一核心流体节点、重叠剔除、物理单位、有限值及通量与诊断在导出舍入界内的一致性全部通过。

重新核查全程{ x['diagnostic_rows']}行诊断、{x['full_windows']}个完整统计窗，每条最终窗确为首个通过窗。独立补算K、修正质量、账本差、截面差与最终窗，均与冻结检查一致。本次3019份保护文件结束时哈希未变，包括原输入、CASE结果/合同/接受和既有报告；共享状态及本次新分析文件不混入保护集合。

一次完成快照未发现S3相关运行进程或会话。快照原始文本中的一个命中是执行核查的bash自身命令；supplementary_verification.json明确排除该行，没有另做持续状态查询。空控制器日志为0字节，与该控制器无进度打印相符，不当作未启动或失败。独立父控制器退出码未另存，不虚报为0；四条原生退出码及本次六个检查器退出码均有证据。

## 3. 物理条件、方向与平均定义

U_REG：h=60nm、d=80nm、槽宽120nm、周期和Ly均240nm，槽占比1/2；平均流体厚度H=h+d/2=100nm。dx=2.5nm，dt=1.0416666666666667e-12s；每条368640核心流体节点、122496壁面链。固定全充液单相、D3Q19_FORCE/ForcedBGK、Bouzidi静止无滑移壁面、x/y周期；P沿槽+y，T横槽+x。rho=1000kg/m³、nu=1e-6m²/s、mu=0.001Pa·s、tau=1，体力半步速度修正保持。

J=Σ核心(u_phys·dx³)/平面面积，单位m²/s；K=nu·J/a，单位m³，是本项目薄膜导度。U=J/H，R_eff=mu/K，单位Pa·s/m³。h与H未混用。本显式沟槽内核不使用原公式或V2经验系数；本次不读取/评分模型预测。

## 4. 六条已有结果

|方向|a / m s⁻²|来源|K / m³|J / m² s⁻¹|步数|求解秒数|数值 / 几何 / 结果|
|---|---:|---|---:|---:|---:|---:|---|
{runrows}

S3四条求解合计{x['formal_S3_solver_seconds']:.6f}s，即{x['formal_S3_solver_seconds']/60:.6f}min，均在原单条4h内；此合计不含检查/来源/文件处理，也不把历史S2耗时算入S3新求解。每条completion无timeout/resource_stop，启动前内存均≥12GiB、盘≥8GiB，首条记录盘亦≥100GiB；单条输出远低4GiB。仅有启动前资源和程序预算监测证据，不声称获得全程RSS或内存曲线。

原生result.txt中的RESULT_PASS=false原样保留，表示独立接受交由外部检查器；上述true均来自实际重验acceptance，不能直接用原生PASS替代。

## 5. 数值、几何和窗口验收

|六条最不利量|独立复算值|原门槛|裁定|
|---|---:|---|---|
{safety}

q_min=q_max=0.5；candidate=installed=122496，fallback/unresolved均0。体积/材料/边界与保存场几何一致，主通量正、全程有限，全部原守卫通过。逐帧float32导出舍入界与诊断double积分分开核查。

|方向|a / m s⁻²|完整窗数|最终std|前一窗std|最终span|
|---|---:|---:|---:|---:|---:|
{windowrows}

2592步统计窗下，六条前一窗std均仍>1e-6，最终std均≤1e-6，且全部更早完整窗均未通过。这解释了末值贴近门槛；本轮没有修改窗口或放宽门槛。旧质量最大相对变化为{max(v['legacy_mass_max'] for v in runs):.12e}，仍完整保存，并非替代正式Neumaier修正质量门。S0专用h75精确回归/逐节点密度捕获重放在本批为NOT_APPLICABLE_S0_ONLY；核对密度诊断不等于本轮做了S0密度重放。

## 6. 两方向三档驱动力控制

按原定义L=(max(K)-min(K))/mean(K)，三点a=50000/100000/200000m/s²。每个中点都来自原S2中档独立结果；原S2完整性与两新增点原S3完整性分别核验后才组合。L并非标准差，也不是统计置信区间。

|方向|L（无量纲）|L的百分数|L / ppm|冻结上限|裁定|
|---|---:|---:|---:|---|---|
{controls}

独立controls与原linearity_P/T.json完全一致。控制器源码在P高通过后先写/检查P控制，才可进入T高；现有接受、P控制、第四条completion和T控制/完成文件时间顺序与此相容。文件mtime仅作旁证，不冒充单调时钟执行计时或完整审计轨迹。

驱动力从低档增大4倍，P末态J比为{x['controls'][0]['endpoint_J_ratio']:.12f}，T为{x['controls'][1]['endpoint_J_ratio']:.12f}；K几乎不变，符合该组低Re条件下的近线性黏性响应。在本几何/网格/三个驱动力范围内，未检出超过原0.1%门的驱动力依赖。

0.083/0.038ppm是三组末态K的观测跨度，不是绝对准确度、残差界、非线性机制大小或浮点误差的唯一归因。最终窗std约1ppm、span约3.68–4.20ppm，既有中细格差P约0.203234%、T约0.744252%远大于本次L。因此不能将极小L解释为沟槽导度已准确到小数点后七八位，也不据此改变网格门或宣称惯性严格为零。

中档方向比K_P/K_T={next(v['K_m3'] for v in runs if v['direction']=='P' and v['role']=='S2_midpoint')/next(v['K_m3'] for v in runs if v['direction']=='T' and v['role']=='S2_midpoint'):.9f}；原S2细格方向比约2.51492794。两方向不相等符合几何各向异性；这与每个方向内部K对驱动力稳定是两个独立问题，不将两方向强制相等。

## 7. 保留项与下一步边界

S2常规间隙网格检查和本次S3线性控制已通过；本轮没有调用要求24条的跨合同聚合器，没有伪造未运行项，没有评估V2预测误差。F04仍OPEN_OUT_OF_SCOPE，S4/S5预声明薄间隙风险检查未由本轮启动或放弃。所有参考/模型/物理/投稿标志维持第1节状态。

旧v1准备HOLD、旧横槽FAIL/380项差异、早期MRP静态FAIL、HISTORICAL_EXCLUSIVE_ATTRIBUTION=NOT_ESTABLISHED及作者外部数据非使用声明的有限范围均保留；本次成功不追溯改判旧证据。当前只限作者声明h60/d80和h30/d80未用于选择系数/检验条件，不写成外部独立历史调查。

本轮构建0、原生调用0、求解0、重跑0、加时0、S4/S5启动0；6次检查器和6次保存场读回属于已有结果分析，不是新的流场计算。CASE源码/配置/ELF/合同/原始结果/接受均未修改。本次辅助脚本在任何重验启动前误用了S2摘要侧文件命名（.sha256而实际为.json.sha256），已只改报告辅助脚本；初版留存review_completed_initial.py.txt。此为分析脚本路径错误，不是原算例FAIL或科学证据矛盾；未降低冻结门槛。

下一具体动作仅建议另定S4运行前材料与合同兼容性审查范围，维持预声明薄间隙验证路线；不自动实现、构建、审计或启动。后续参考资格与跨合同汇总的实现/裁定范围另审，不自动解除F04。没有待用户执行的新命令。

## 8. 精确身份与复核入口

{identities}

本目录：independent_review.json、supplementary_verification.json、run_summary.csv、六个replay_*目录的acceptance/fields/reader日志、六个独立退出记录、completion_snapshot.json、protected_inputs_and_outputs.json及report_manifest.json。共享进度与交接均已同步至docs/reports/SIM240_AI_CONTEXT.md及AI_HANDOFF_20261015.md第一节，历史段落保留。
'''
with (OUT/'REPORT.md').open('x') as f:f.write(report)
body=f'''## S3四条与S2两中档完整独立验收通过，两方向三档控制通过（{now}）

用户范围：批次结束后按原URV-v1/MRP/A1/S3 v1.1/S3-FRD-v1完整独立分析四条、S2两中档及两方向三点，不重跑/加时/进入S4S5。批次完成记录时间2026-11-03 16:44:02 +08；本轮一次快照无相关进程/会话。入口`docs/reports/URV_S3_completed_review_20261103_172033/REPORT.md`、independent_review.json、run_summary.csv、supplementary_verification.json。

S3正式release SHA {x['S3_release_sha256']}，2632输入和四条运行前后闭包全一致；S2原release SHA {x['S2_release_sha256']}、2160输入及两中档来源一致，未改绑。六次原完整检查器重验退出0，acceptance与原记录完全相同；六次实际VTK读回60帧，fields与原记录完全相同。222原始文件、62850行诊断、47304完整窗均复核，最终窗为首个通过；3019保护文件前后不变。四新增及两中档均NUMERICAL_GATE=PASS、geometry_PASS=true、RESULT_PASS=true；原生RESULT_PASS=false分工含义保留。

沿槽P三档K/m³（a50000/100000/200000）=5.919336794569472e-23/5.919337058277595e-23/5.919337286143088e-23；横槽T=2.3663885894734337e-23/2.3663885892433063e-23/2.3663886793899977e-23。独立L_P=8.304538367142662e-08（0.083045ppm）、L_T=3.809462680994329e-08（0.038095ppm），均≤0.001（0.1%），与控制器两方向记录精确一致。S3_FOUR_RUN_ACCEPTANCE/S2_TWO_MIDPOINT_REUSE_ACCEPTANCE/S3_CONTROL_PASS=true。

S3新四条步数P低13275/T低7659/P高13292/T高7666，求解合计2603.827977s，均未超4h、无资源停止；S0密度捕获/精确轨迹回归本批NOT_APPLICABLE。六条最大修正质量6.419766481e-15、账本差1.806755400e-16、密度偏离9.786378818e-09、Mach1.932133981e-07、Re3.748140729e-05；几何q0.5、368640核心节点/122496壁链，fallback/unresolved0，原门均过。极小L仅是观测稳定性，非绝对准确度；不以其替代网格误差。

已完成U_REG的S2网格和S3控制证据；本轮未作参考资格/模型评价/24条汇总。REFERENCE_QUALIFIED_FOR_CASE/reference_qualified=false、MODEL_COMPARISON/physical_validation=NOT_EVALUATED、strict_error_bound_established/submission_ready=false，F04 OPEN_OUT_OF_SCOPE。旧FAIL/380差异、MRP静态FAIL、旧v1 HOLD、历史唯一归因未建立及作者声明范围保留。

改动仅新报告目录和本共享进度/交接第一节；源码/ELF/CASE合同/原始接受和结果未变。构建/原生/求解/重跑/加时/S4S5启动全0；分析辅助脚本的S2侧文件路径小错已留初版并修正，未影响原证据。六正式run_id与completion指纹详见报告/CSV，没有新run_id或新启动命令。AI辅助数值复核不是人工科学终审。

下一具体动作：另定S4运行前材料与合同兼容性审查范围；不自动实现/构建/零步/正式计算，不自动进入S5或解除F04，正式执行仍另行授权。下一步模型GPT-6.1 Sol｜High。

'''
updates=[]
for name in ['SIM240_AI_CONTEXT.md','AI_HANDOFF_20261015.md']:
    path=ROOT/'docs/reports'/name;before=(OUT/('before_'+name)).read_text();current=path.read_text()
    start=before.find('\n## ');end=before.find('\n## ',start+1)
    cstart=current.find('\n## ')
    assert start>=0 and cstart>=0 and current[cstart:]==before[start:],'concurrent state body changed'
    updates.append((path,current[:cstart+1]+body+(before[end+1:] if end>=0 else '')))
protected=load(OUT/'protected_inputs_and_outputs.json');assert all(sha(p)==h for p,h in protected.items())
for path,text in updates:path.write_text(text)
state_hashes={str(p):sha(p) for p,_ in updates}
with (OUT/'shared_state_update.json').open('x') as f:json.dump(dict(at=now,paths_sha256=state_hashes,historical_tail_preserved=True),f,indent=2);f.write('\n')
manifest={str(p.relative_to(OUT)):sha(p) for p in OUT.rglob('*') if p.is_file() and p.name!='report_manifest.json'}
with (OUT/'report_manifest.json').open('x') as f:json.dump(manifest,f,ensure_ascii=False,indent=2);f.write('\n')
print('Report and shared state written;',len(manifest),'artifacts;',len(protected),'protected files unchanged.')

from pathlib import Path
import json,hashlib,datetime
from zoneinfo import ZoneInfo
ROOT=Path('/home/dell/yuanyuanxu/SIM240');OUT=Path(__file__).resolve().parent
x=json.loads((OUT/'independent_review.json').read_text());s=json.loads((OUT/'supplementary_verification.json').read_text())
runrows='\n'.join(f"|{v['dx_nm']:g}|{'沿槽P' if v['direction']=='P' else '横槽T'}|{v['K_m3']:.12e}|{v['steps']}|{v['solver_seconds']:.3f}|PASS|true|true|" for v in x['runs'])
gridrows='\n'.join(f"|{'沿槽P' if v['direction']=='P' else '横槽T'}|{v['observed_order']:.6f}|{100*v['medium_fine_relative_change']:.6f}%|{100*v['GCI_fine_estimate']:.6f}%|{100*v['estimated_u']:.6f}%|通过|" for v in x['grid_analysis'])
safetyrows='\n'.join(f"|{label}|{max(v[key] for v in x['runs']):.9e}|{limit}|" for label,key,limit in [('修正质量相对误差绝对值','corrected_mass_max','<1e-10'),('质量账本差','ledger_max','≤1e-13'),('密度偏离','density_deviation_max','≤1e-6'),('Mach','Mach_max','<0.05'),('Re（h+d尺度）','Re_H_max','≤0.01'),('最终截面流量相对差','section_final','≤1e-5'),('流体体积相对误差绝对值','volume_relative_error','≤1e-10')])
# Volume errors are signed: show the largest absolute magnitude.
safetyrows=safetyrows.rsplit('\n',1)[0]+f"\n|流体体积相对误差绝对值|{max(abs(v['volume_relative_error']) for v in x['runs']):.9e}|≤1e-10|"
report=f'''# S2 六条正式结果完整独立复核

复核日期：2026-11-03（北京时间）。用户授权：确认结束后按原协议分析已有结果，不自动重跑、加时或进入S3。AI辅助数值证据审查，不构成人工科学终审或投稿放行。

## 1. 结论与状态

六条均完成，原生退出和本次独立检查器退出均为0，无超时或资源停止。本轮完整重放原检查器，逐项所得acceptance与原运行时acceptance完全相同；六条NUMERICAL_GATE=PASS、geometry_PASS=true、RESULT_PASS=true。S2_SIX_RUN_ACCEPTANCE=true。

沿槽和横槽三网格指标均满足原正有限阶、单调、中细差≤1%、细格GCI估计≤1%条件。但是驱动力线性控制S3尚未完成，REFERENCE_QUALIFIED_FOR_CASE仍false，MODEL_COMPARISON/physical_validation仍NOT_EVALUATED，strict_error_bound_established/submission_ready仍false。不能据本批评价V2预测准确性，也不能把网格估计称为严格误差界。

## 2. 来源、执行和完整性

新正式合同为CASE/unseen_v2_reference_S2_reuse_v1/evidence/S2_formal_launch_release_LRP_v1_20261102_02.json，SHA256 `{x['release_sha256']}`。本次2160项输入逐项一致，每条completion的inputs_before/after均与合同完全相同；每条run_id/planned_case/output和原授权对应。

B、零步收据、原15动态库来源和ELF通过原绑定/来源检查。ELF复用S1，SHA 5c3836e97c99feab88cd8e41773237f6ff642a10558f151b11e112563382b07b。旧PERF日志变化按S2-LRP-v1保留，原空指纹和原始清单没有被改成新值；新合同绑定独立快照，本次不重解释旧合同为完整性通过。

六条原始输出清单各37文件，合计222文件，与completion精确对应；completion.json是清单生成后写入的封装文件，不可能自包含其哈希，由原acceptance的completion_sha256及本轮保护清单另行固定。原始输出无缺失、额外载荷或内容变化。六条每条10帧，共60帧，由6次实际pvpython读回，检查了完整VTK引用闭包哈希、唯一核心流体节点、周期重叠剔除、真实几何、单位、有限值，以及与诊断通量在float32导出舍入界内的一致性；fields.json与原独立读回完全相同。

全程诊断共{sum(v['diagnostic_rows'] for v in x['runs'])}行，原检查器重新计算82226个完整统计窗，并验证最终窗是第一个达标窗。独立补算K=nu·J/a、修正质量、账本、最终窗、截面差等与原数据一致。2415份受保护输入/原结果/既有接受/旧报告文件结束时哈希保持。

整批S2_completed.json已生成，solver_runs=6、next_stage_started=false。文件mtime为{s['batch_record_mtime']}，仅作时间辅助证据；独立控制器父进程退出码没有另存，不虚报该退出码。六个求解退出码和本次六个检查器退出码有独立记录。新控制日志为空与成功批次不矛盾。

## 3. 物理条件与平均定义

U_REG：h=60nm、d=80nm、w=120nm、周期和Ly均240nm；槽占比1/2，平均流体厚度H=h+d/2=100nm。固定无滑移Bouzidi壁面、水平周期、单相全充液，P沿槽+y，T横槽+x。rho=1000kg/m³、nu=1e-6m²/s、mu=0.001Pa·s、加速度a=1e5m/s²、tau=1。

J=Σ(u_phys·dx³)/平面面积，单位m²/s；K=nu·J/a，单位m³（本项目薄膜导度，不是单位m²的通常渗透率）；平均速度U=J/H。原R_eff=mu/K，单位Pa·s/m³。独立显式几何参考内核不使用原公式或V2系数。

## 4. 六条逐项结果

|dx/nm|方向|K/m³|完成步数|求解秒数|NUMERICAL_GATE|geometry_PASS|RESULT_PASS|
|---:|---|---:|---:|---:|---|---|---|
{runrows}

原生result.txt中的RESULT_PASS=false按原设计保留，表示独立接受由外部检查器写出；上述RESULT_PASS来自实际重放后的acceptance，不改原文件。

六条求解时间合计{x['formal_solver_total_seconds']/3600:.6f}小时，检查/文件处理另计；两细格P约6小时32分18秒、T约3小时45分16秒，均小于原12小时上限。没有扩时。性能外推73–76小时是走满602112步的条件成本；实际收敛P52735步、T30475步，故本次更早完成，不否定原外推的条件意义，也不提供未来条件的完成保证。

## 5. 数值与几何门槛

|全六条最不利量|本次值|原门槛|
|---|---:|---|
{safetyrows}

各网格核心流体节点为46080、368640、2949120，每方向一致；壁面链30528、122496、490752，q距0.5在1e-10容差内；fallback和unresolved均0。材料计数、体积、边界审计与60帧实际场几何一致。

六条最终窗相对样本标准差最大{max(v['window_std'] for v in x['runs']):.9e}（≤1e-6），相对跨度最大{max(v['window_span'] for v in x['runs']):.9e}（≤5e-6）；横向通量及所有原有限值守卫均通过。每条前一窗至少一项仍不达标，原全窗重算验证第一次通过即停止，贴近门槛符合控制逻辑，不据此改门槛。

旧质量轨迹仍完整保存，最大约9.66856e-11，是既有旧观察量，不替换修正质量门。修正质量最大约1.25720e-14。h75专项精确回归/密度重放属于S0；本批U_REG的density_capture=NOT_APPLICABLE_S0_ONLY，不伪造重放PASS。

正式运行只保留原前置内存/磁盘与时间/输出监测。每条开始时可用内存≥12GiB、磁盘≥8GiB，输出均远小于4GiB；不声称已获得全程RSS或可用内存曲线，正式程序没有PERF式连续观察。

## 6. 原三网格规则的独立计算

三网格dx=5/2.5/1.25nm，r=2。令a=K粗−K中、b=K中−K细；两方向a·b>0，差值未触发1e-14相对地板。p=ln(|a/b|)/ln2；GCI细=1.25·|K中/K细−1|/(2^p−1)。按原规则u=max(GCI细、中细相对差、细格最终窗跨度)。

|方向|观测阶p|中细相对变化|细格GCI估计|估计u|本阶段网格指标|
|---|---:|---:|---:|---:|---|
{gridrows}

这里的“网格指标通过”只对应原网格分支，不把helper内部的局部grid资格布尔值写成完整参考资格。仍缺S3三档驱动力线性检查；原24条聚合入口未调用，不伪造其他18条或放松完整性计数。p约1.55和1.29为该三网格的观测阶，不宣称已独立证明渐近区，也不要求把它们改为2；原冻结条件为正有限阶，不是固定二阶。

## 7. 方向性及证据限度

细格K沿槽={x['grid_analysis'][0]['K_by_grid_m3'][-1]:.12e}m³，K横槽={x['grid_analysis'][1]['K_by_grid_m3'][-1]:.12e}m³，沿槽/横槽={x['anisotropy'][-1]['K_parallel_over_K_perpendicular']:.9f}。相同驱动力和H下沿槽平均速度约59.0733µm/s、横槽约23.4891µm/s；按mu/K定义横槽等效阻力约为沿槽的2.51493倍。这是显式几何计算中的方向性输运结果，不是对V2的误差评分，也未作机理耗散占比归因。

三网格各向异性比分别2.471481、2.501422、2.514928。随加密两方向K单调下降，横槽中细变化大于沿槽；两者均满足此次原网格指标，但横槽的数值敏感性更大。u只是估计敏感性尺度，不是置信区间或严格误差界。

## 8. 本轮边界、软件说明与交接

本轮求解调用0、构建0、重跑0、加时0、S3启动0。新增仅本报告目录和共享状态/交接文件；原始CASE、旧绑定、既有接受与科学门槛未修改。旧横槽FAIL/380项差异、早期MRP静态FAIL、HISTORICAL_EXCLUSIVE_ATTRIBUTION=NOT_ESTABLISHED、F04 OPEN及作者外部数据声明原范围保持。

分析辅助脚本首次把completion封装也纳入其自身原始输出清单比较，触发断言；只读核对确认六条唯一额外文件均为completion.json，属于清单生成后才写入的元数据。随后仅修正本报告辅助脚本，将completion独立验证；已完成的第一条重放证据复用，没有重复启动检查器或求解器。初版代码留存review_completed_initial.py.txt。这不是原算例或原科学检查器FAIL，不改原接受条件。

下一步只建议另定范围审查S3运行前材料与合同兼容性，当前不实现、不启动、不追加授权。完整V2预测能力评价须待符合原协议的参考资格及其他必要阶段完成；本批不能宣布论文闭环。

入口：independent_review.json、supplementary_verification.json、run_summary.csv、六个replay_*目录（acceptance/fields/reader日志）、protected_inputs_and_outputs.json和report_manifest.json。
'''
(OUT/'REPORT.md').write_text(report)
body=f'''## S2 六条完整独立验收通过；常规间隙网格指标通过，参考资格待线性控制（2026-11-03）

用户范围：确认结束后按原协议完整分析已有结果，不重跑、不加时、不进S3。已确认无相关进程/会话，S2_completed.json存在（文件时间09:24:13 +08:00）。报告入口 `docs/reports/URV_S2_completed_review_20261103_095422/REPORT.md`、independent_review.json、run_summary.csv。

新合同SHA `{x['release_sha256']}`，2160项输入当前和六条运行前后记录全部一致；2415保护文件前后未变。六次完整原检查器重放退出0，与原acceptance逐字结构相同；6次实际VTK读回共60帧与原fields完全相同，核对222个原始输出文件、82226完整窗。六条NUMERICAL_GATE=PASS、geometry_PASS=true、RESULT_PASS=true，S2_SIX_RUN_ACCEPTANCE=true；原生result的RESULT_PASS=false保留其独立接受分工含义。

K/m³按dx5/2.5/1.25：P=5.954431833580618e-23/5.919337058277595e-23/5.907331356027004e-23，T=2.409256324244804e-23/2.3663885892433063e-23/2.3489068066462535e-23。完成步P3328/13288/52735、T1940/7664/30475；细格耗时P23537.767s、T13515.756s，均在12h内，六条求解合计10.672552h。没有扩时，PERF走满最大步条件成本不是收敛时长。

网格指标：P观测阶1.547536、中细差0.203234%、GCI估计0.132095%；T阶1.294040、中细差0.744252%、GCI估计0.640652%；均单调、正有限阶且两项<1%。细格方向比2.51492794。只记录本阶段网格指标通过；S3线性控制尚未完成，REFERENCE_QUALIFIED_FOR_CASE=false，MODEL_COMPARISON/physical_validation=NOT_EVALUATED，strict_error_bound_established/submission_ready=false。未调用要求24条的聚合器、未评价V2。

原PERF日志例外、旧正式拒绝和S2-LRP-v1路径替换保留；原源码/ELF/检查器/原接受/原始结果和门槛未改。h75精确回归及密度重放S0专属，本批NOT_APPLICABLE。旧横槽FAIL、MRP静态FAIL、F04 OPEN及作者声明范围不变。本轮分析脚本一处completion自清单比较错误仅修正报告辅助代码，原始证据无变化；详情REPORT第8节。

下一步：另定S3运行前材料与合同兼容性审查范围，当前S3未实现/启动于本轮，不自动推进、不重跑或加时。共享交接已同步，原六run_id和合同路径见报告；本阶段没有待用户启动的新计算。

'''
for name in ['SIM240_AI_CONTEXT.md','AI_HANDOFF_20261015.md']:
 p=ROOT/'docs/reports'/name;old=(OUT/('before_'+name)).read_text();assert p.read_text()==old,'concurrent shared state change';start=old.find('\n## ');end=old.find('\n## ',start+1);assert start>=0
 p.write_text(old[:start+1]+body+(old[end+1:] if end>=0 else ''))
protected=json.loads((OUT/'protected_inputs_and_outputs.json').read_text());assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in protected.items())
manifest={str(p.relative_to(OUT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in OUT.rglob('*') if p.is_file() and p.name!='report_manifest.json'}
(OUT/'report_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
print('REPORT and shared handoffs written; all 2415 protected files unchanged; '+str(len(manifest))+' report artifacts hashed.')

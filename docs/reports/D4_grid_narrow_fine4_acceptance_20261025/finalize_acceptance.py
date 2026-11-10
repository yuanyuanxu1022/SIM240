#!/usr/bin/env python3
"""Freeze audit findings and phase-stop state; never starts or refits a solver/model."""
from pathlib import Path
import datetime,difflib,hashlib,json
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[2];CASE=ROOT/'CASE/D_series/D4_variable_groove_transport_20261023'
def load(n):return json.loads((OUT/n).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(n,v):(OUT/n).write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def main():
 assert (OUT/'acceptance_exit_code.txt').read_text().strip()=='0' and (OUT/'grid_review_exit_code.txt').read_text().strip()=='0'
 cert=load('independent/certificate.json');scalar=load('independent/analysis/scalar_results.json');flow=load('independent/analysis/flow_frames.json');batch=load('batch_review.json');window=load('independent/analysis/rolling_window_checks.json');grid=load('grid_review/summary.json');verify=load('independent_grid_verification.json')
 assert cert['independent_acceptance']=='PASS' and len(scalar)==4 and flow['ok'] and flow['frames_read']==40 and batch['ok']
 assert grid['narrow_six_quantity_gate']==verify['narrow_six_quantity_gate']=='FAIL' and verify['ok']
 assert verify['FAIL_count']==5 and verify['PASS_count']==1
 protected=load('protection_before.json');assert all(sha(k)==h for k,h in protected.items())
 for obj in [cert,load('grid_review/accepted_references16.json')]:assert all(sha(k)==h for k,h in obj['bound_inputs_sha256'].items())
 limits=json.loads((CASE/'protocol/execution.json').read_text())['numerical_limits']
 keys={'max_mass_drift':'mass_relative_strict','max_density_deviation':'density_deviation','max_Mach':'Mach_strict','final_window_rel_std':'relative_std','final_window_rel_span':'relative_span','final_section_relative_difference':'section_relative_difference','final_window_cross_abs_max':'cross_flux_m2_s'}
 worst={k:{'value':max(scalar,key=lambda x:x[k])[k],'run_id':max(scalar,key=lambda x:x[k])['run_id'],'limit':limits[v]} for k,v in keys.items()};write('numerical_worst_values.json',worst)
 tz=datetime.timezone(datetime.timedelta(hours=8));start=datetime.datetime.fromisoformat(batch['start_utc']).astimezone(tz);end=datetime.datetime.fromisoformat(batch['end_utc']).astimezone(tz)
 verdict={'batch_id':batch['batch_id'],'independent_FINE4_case_acceptance':'PASS','NUMERICAL_GATE_independently_recomputed':'PASS','geometry_PASS_independently_checked':True,'saved_flow_time_series_integrity':'PASS','source_RESULT_PASS':'false preserved in all raw results','diagnostic_rows':sum(x['diagnostic_rows'] for x in scalar),'complete_windows_recomputed':sum(x['windows_recomputed'] for x in window),'raw_files':160,'flow_frames':40,'flow_referenced_files':84,'release_bound_paths_unchanged':3803,'protected_paths_unchanged':len(protected),'start_beijing':start.isoformat(),'end_beijing':end.isoformat(),'narrow_three_grid_sensitivity_gate':'FAIL','narrow_quantity_PASS_count':1,'narrow_quantity_FAIL_count':5,'narrow_geometry_FAIL_count':2,'all_six_sequences_monotone_contracting':True,'independent_Decimal80_grid_verification':'PASS_AGREEMENT_WITH_FROZEN_VERDICT','development_grid_direction_cases_independently_accepted':10,'development_grid_direction_cases_planned':12,'wide_finest_missing':2,'whole_three_geometry_grid_target':'INCOMPLETE_OR_REFERENCE_INVALID; narrow failures explicitly retained','phase_stop':'HOLD_NEXT_WIDE_AND_PREDICTION; review reference resolution/error budget before any new run','wide_fine_execution_released':False,'prediction_execution_released':False,'G4_lock_unchanged':True,'new_solver_run':False,'new_fit':False,'thresholds_changed':False}
 write('verdict.json',verdict)
 labels={'max_mass_drift':'全程质量绝对相对漂移','max_density_deviation':'最大密度偏离','max_Mach':'最大Mach','final_window_rel_std':'末窗相对样本标准差','final_window_rel_span':'末窗相对极差','final_section_relative_difference':'末态双截面相对差','final_window_cross_abs_max':'末窗横向通量绝对值(m²/s)'}
 report=f'''# 窄槽四项最细网格独立验收与三格比较

**本批4项的数值、几何、来源及保存流场验收PASS；两个窄槽的预设三格敏感性目标均FAIL。** 六个网格指标5项失败、1项通过。按冻结协议在此停下，宽槽最细2项和预测阶段均不放行。不修改原始RESULT_PASS=false、协议、容差或G4候选锁。

## 完成记录及来源

batch_id=`development_grid_narrow_fine4_20261024_v1`。北京时间{start.strftime('%Y-%m-%d %H:%M:%S')}→{end.strftime('%Y-%m-%d %H:%M:%S')}，墙钟{batch['wall_seconds']:.6f}秒，约5小时52分15秒。总批次与4项独立exit均0，completion记录attempted4/next_stage_started=false。实际run_id/参数/命令与canonical表和4份预存正式配置逐字节一致；物性、周期、方法保持。原manifest/completion中pending是运行结束快照，不回写，独立接受证书另存。

三种层次分别记录：NUMERICAL_GATE独立PASS、geometry_PASS独立true、本批独立结果/保存场PASS；GRID_SENSITIVITY_TARGET不通过，不能合并成整个研究或参考精度PASS。

160份本批原始文件先存SHA256；3803 release绑定路径、3808去重manifest/库输入核对一致；统一保护3964路径读取前后一致（集合重叠不相加）。OpenLB HEAD882924a9cfc8dcdf82909e39530789cb6f5ebcc4及构建/源/binary/库绑定保持，G4候选锁及14绑定文件保持。原始source/result/FAIL不改，无新编译、仿真、拟合或Git推送。

## 四项独立数值验收

冻结accept_batch.py显式调用数值/VTK分析；scalar、flow与总验收进程均exit0。重算184084行诊断、119288个完整16200步窗口，样本std分母n−1，核首个合格窗即停，各项44656–47713步，未触307200/1168128上限。重算质量漂移、截面、J/K/R、剖面积分；有限/正主通量/材料保持等原条件均通过。

|指标|4项最坏值|原门槛|
|---|---:|---:|
'''
 for k in keys:report+=f"|{labels[k]}|{worst[k]['value']:.10g}|{'<' if k in ('max_mass_drift','max_Mach') else '≤'}{worst[k]['limit']:.10g}|\n"
 report+='''
逐项与最坏run_id见independent/analysis/scalar_results.csv及numerical_worst_values.json。全程密度/Mach由保存诊断核对；未保存时刻不能声称离线重建完整场。

独立枚举两种几何、四方向累计3280896核心流体节点/589824边界连接，q=.5，无fallback/unresolved（累计方向计数，不是去重网格总数）。q=.5不等于零边界误差。分块标准差最大偏差工作区8294400字节，在16MiB工作预算内；数值进程峰值93608KiB/6.77s，流场660716KiB/34.88s。原仿真最大RSS730824KiB，分析资源与求解资源分开。

## 全部保存流场

实际reader读取40完整帧、递归核84份VTK引用文件，达到的计划时刻、初态及收敛末态齐全，未来未达到帧按原规则标记。有效液体点完整唯一、坐标与材料集合保持，速度/压力扰动/运动学耗散数组有限、耗散非负。各分量积分J与CSV差异在Float32逐值舍入和求和误差界内，最大主通量相对差2.96373688134e−9；末态速度与双精度field_slice舍入成Float32后逐值相同。

压力是周期扰动，不能拿p_max−p_min作为周期整体宏观压降；耗散单位m²/s³不直接当W/m³。本轮不额外声称能量闭合、局部机制分解或成品图验收。逐帧数据/引用哈希在flow_frames.json、flow_files_sha256.json。

## 三格比较：按原目标保留FAIL

来源导出与冻结比较程序均执行成功（exit0只是程序正常完成，网格结果另看字段）。粗6+中6+本批窄细4共16行绑定参考：每个窄几何分别同物性/周期/方向比较dx5、2.5、1.25；宽槽仅有前两档，最细两项仍缺。完整三几何目标显示INCOMPLETE_OR_REFERENCE_INVALID，两个已完整窄槽的FAIL另行显式保留。

定义E02=100×|Q5/Q1.25−1|，目标≤1%；E12=100×|Q2.5/Q1.25−1|，目标≤0.5%。A=KP/KT，必须由同几何同dx的合格两方向生成。以下分母均为本次1.25nm数值参考，不当连续真值：

|h/d/w（nm）|量|5对1.25差异/%|2.5对1.25差异/%|门槛判定|
|---|---|---:|---:|---|
'''
 for row in verify['records']:
  report+=f"|75/{row['d_nm']}/60|{row['quantity']}|{float(row['E_5_to_1p25_percent']):.6f}|{float(row['E_2p5_to_1p25_percent']):.6f}|{'PASS' if row['status'].startswith('PASS') else 'FAIL'}|\n"
 report+='''
- d25：KP粗格超过1%；KT粗格与中格分别超过1%和0.5%；A粗格1.014221%也超过1%，即使靠近阈值也按原规则FAIL，不四舍五入改判。
- d120：KP粗格超过1%；KT粗格与中格超过相应门槛；A两档差异及趋势满足，单项PASS。
- 六条数列均变化同向且差值收缩，但收缩本身不能代替大小容差，两个几何整体均FAIL。2.5nm的横槽差仍约0.66–0.67%，本轮证据也不支持直接认定“改用2.5nm就满足原0.5%目标”。

独立verify_grid_arithmetic.py不导入冻结比较器，直接回查16行参考的raw result.txt K及run/config/binding，在Decimal80下重建A、E02/E12、门槛和趋势，六项判定全同；条件p的最大绝对差2.22045e−16、GCI最大差8.67362e−19。冻结版本用Decimal60，边界差远小于实际超限量，不能以显示舍入掩盖失败。原comparison/grid_policy源码字节保持。

条件观察阶约0.921–1.537，按原单调收缩/差分尺度条件输出的p/GCI只作诊断，见three_grid_quantities6.csv及冻结JSON；不强制理论二阶，不把GCI当严格误差上界，也不用其值覆盖FAIL。这里只检两窄几何及规定dx/dt联动路径，不能外推全参数域精度。

## 阶段停点和后续边界

本批证明四项原始数值与输出合同满足，同时揭示预设分辨率差异目标未达到；这两个判断分别成立。保持全部已接受数据为相应固定分辨率记录，不能继续作未经限定的1%粗格参考精度声明。

开发网格方向计算已完成且数值/场独立验收10/12，宽槽最细2项未运行；完整敏感性目标没有通过。按原“窄槽FAIL或INCONCLUSIVE先停”要求，不准备/启动宽槽、不放行预测16+4。下一具体工作是审查分辨率差异对数值参考/误差预算/公式验证的影响，提出版本化修订方案；本轮不选定新参考、不放宽门槛、不追加网格、不切换训练或模型。尤其不能用细格换掉原5nm主评价差点来使公式变准。

G4 v1锁保持，如以后用新开发数据重拟合或更换主数值参考/验证合同，另立版本并在取得保留预测结果前重新冻结；本轮未读保留预测流动结果。宽细22GiB与多日预算问题仍存在，但当前第一停因已是窄槽网格目标FAIL。

证据入口：verdict.json；independent/certificate.json；batch_review.json；numerical_worst_values.json；independent scalar/flow日志与各exit/resource；grid_review/summary.json、three_grid_comparison.json、accepted_references16.json及export/compare exit；three_grid_quantities6.csv、reference_sources16.csv、independent_grid_verification.json；protection_before.json、raw_hashes_before.json和final_integrity.json。所有原始run_id/output路径在独立field_cases与reference_sources表可定位。本轮以实际流场reader/有效液体/数组语义/来源核对执行paraview-publication原则，未以图片外观代替数值或网格结论。
'''
 (OUT/'REPORT.md').write_text(report)
 block='''## 第一篇：窄槽4项数值与流场独立PASS，两个窄槽三格目标FAIL，后续阶段停止（2026-10-25，当前入口）

- 用户授权整批结束后独立验收及三格判定。批次development_grid_narrow_fine4_20261024_v1北京时间10月24日21:16:28→10月25日03:08:42完成，21134.556679秒；总/4项独立exit均0。当前入口docs/reports/D4_grid_narrow_fine4_acceptance_20261025/REPORT.md、verdict.json；independent/certificate为原始数值/几何/场PASS，grid_review/summary明确narrow_six_quantity_gate=FAIL，二者不可混用。旧运行中/2项快照保留。
- 原冻结验收scalar/flow/总分析均exit0：184084行诊断、119288个16200步完整窗，首个停止点/守恒/J/K/R/切片/几何通过；最坏质量1.63799153e−11<1e−10、密度1.19966459e−9≤1e−6、Mach3.31247540e−8<.05、std9.99990929e−7≤1e−6/span4.49916776e−6≤5e−6、末截面3.75889609e−9≤1e−5、cross4.58593426e−20≤1e−12。原RESULT_PASS=false和运行结束pending快照不改，独立判定另存。
- 两几何四方向累计3280896节点/589824壁面连接、q=.5、无fallback/unresolved；40完整流场帧/84引用实际读取通过，最大主通量相对差2.96373688e−9且在Float32界内，末态与CSV舍入后逐值同。分块工作区8294400字节≤16MiB；数值/流场分析峰值93608/660716KiB，原仿真峰值730824KiB，分别记录。
- 160本批原始文件、3803 release绑定、3808去重manifest/库绑定保持；统一保护3964路径哈希前后同（集合重叠不相加）。OpenLB HEAD882924a9cfc8dcdf82909e39530789cb6f5ebcc4及G4锁/14绑定保持。无源码/协议/容差/旧FAIL修改、无编译/仿真重跑、拟合或Git推送。
- 真实16行粗6+中6+窄细4来源绑定，冻结Decimal60三格比较：d25/w60的KP/KT/A，E(5→1.25)=1.250306%/2.287730%/1.014221%，E(2.5→1.25)=0.327389%/0.670684%/0.341008%，三项FAIL；d120/w60分别1.287126%/2.258982%/0.950388%与0.329893%/0.660534%/0.328471%，KP/KT FAIL、A PASS。共5FAIL/1PASS、两几何整体FAIL；六数列均单调收缩，不能代替1%/.5%大小门槛。
- 独立Decimal80直接重算raw K与A/两误差/判定，六项一致，条件p/GCI差≤2.22e−16/8.67e−19。p约.921–1.537仅条件诊断，不是严格误差界；不能以GCI或显示舍入覆盖FAIL。2.5nm横槽仍未满足原对1.25nm .5%差异目标，不能直接认定换中格即解决。
- 开发网格10/12方向计算已完成并数值/场验收；宽细2项缺失使完整三几何目标INCOMPLETE，但窄槽FAIL明确保留。按原协议停在这里，不准备/运行宽槽或预测16+4，不换参考/删点/改阈值。下一具体动作审查网格未达标对参考数据与公式验证的影响、提出版本化修订方案（不启动计算、不自动选定新参考/拟合）。G4 v1锁保持，后续重拟合/参考或合同变更另立版本，在保留结果前重新冻结。其他第一篇与第二篇状态保留。

'''
 sync=[]
 for name in ['SIM240_AI_CONTEXT.md','AI_HANDOFF_20261015.md']:
  p=ROOT/'docs/reports'/name;before=p.read_text();(OUT/(name+'.before')).write_text(before)
  start=before.index('## 第一篇：窄槽4项');end=before.index('## 第一篇：首批中网格6项',start);after=before[:start]+block+before[end:]
  old='窄槽4项入口/资源/三格接续准备已完成，以上方新入口为准，待用户启动；本轮中格验收不等于窄细已计算。'
  new='窄槽4项已完成并数值/场独立PASS，但两窄槽三格目标FAIL，以上方入口为准；后续宽细/预测停止。'
  after=after.replace(old,new);p.write_text(after)
  assert before[end:].replace(old,new)==after[after.index('## 第一篇：首批中网格6项'):]
  (OUT/(name+'.diff')).write_text(''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile=name+' before',tofile=name+' after')))
  sync.append({'path':str(p),'before_sha256':hashlib.sha256(before.encode()).hexdigest(),'after_sha256':sha(p),'other_sections_preserved_except_stale_operational_phrase':True})
 write('state_sync.json',sync)
 changed=[p for p,h in protected.items() if sha(p)!=h];assert not changed
 write('final_integrity.json',{'checked_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'protected_paths':len(protected),'changed':changed,'ok':not changed,'original_raw_protocol_release_G4_modified':False,'new_simulation':False,'new_compilation':False,'wide_fine_or_prediction_released':False})
 write('artifact_hashes.json',{str(p.relative_to(OUT)):sha(p) for p in OUT.rglob('*') if p.is_file() and p.name!='artifact_hashes.json'})
 print(json.dumps(verdict,ensure_ascii=False,indent=2))
if __name__=='__main__':main()

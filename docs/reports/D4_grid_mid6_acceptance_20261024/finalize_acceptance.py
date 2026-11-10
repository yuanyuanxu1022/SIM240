#!/usr/bin/env python3
"""Summarize completed frozen independent review; no solver imports or launch."""
from pathlib import Path
import csv,datetime,difflib,hashlib,json
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[2];CASE=ROOT/'CASE/D_series/D4_variable_groove_transport_20261023'
def load(n):return json.loads((OUT/n).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(n,v):(OUT/n).write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def main():
 assert (OUT/'acceptance_exit_code.txt').read_text().strip()=='0'
 cert=load('independent/certificate.json');scalar=load('independent/analysis/scalar_results.json');flow=load('independent/analysis/flow_frames.json');batch=load('batch_review.json');window=load('independent/analysis/rolling_window_checks.json');partial=load('partial_grid_comparison.json');two=load('two_level_sensitivity.json')
 assert cert['independent_acceptance']=='PASS' and len(scalar)==6 and flow['ok'] and flow['frames_read']==61 and batch['ok']
 assert partial['GRID_SENSITIVITY_TARGET']=='INCOMPLETE_OR_REFERENCE_INVALID' and not partial['prediction_released']
 for name in ['scalar','flow']:assert (OUT/'independent'/(name+'_exit_code.txt')).read_text().strip()=='0'
 protected=load('protection_before.json');changed=[p for p,h in protected.items() if sha(Path(p))!=h];assert not changed
 assert all(sha(Path(p))==h for p,h in cert['bound_inputs_sha256'].items())
 assert all(sha(Path(p))==h for p,h in load('accepted_references12.json')['bound_inputs_sha256'].items())
 limits=json.loads((CASE/'protocol/execution.json').read_text())['numerical_limits']
 keys={'max_mass_drift':'mass_relative_strict','max_density_deviation':'density_deviation','max_Mach':'Mach_strict','final_window_rel_std':'relative_std','final_window_rel_span':'relative_span','final_section_relative_difference':'section_relative_difference','final_window_cross_abs_max':'cross_flux_m2_s'}
 worst={k:{'value':max(scalar,key=lambda x:x[k])[k],'run_id':max(scalar,key=lambda x:x[k])['run_id'],'limit':limits[v]} for k,v in keys.items()};write('numerical_worst_values.json',worst)
 start=datetime.datetime.fromisoformat(batch['start_utc']).astimezone(datetime.timezone(datetime.timedelta(hours=8)));end=datetime.datetime.fromisoformat(batch['end_utc']).astimezone(datetime.timezone(datetime.timedelta(hours=8)))
 verdict={'batch_id':batch['batch_id'],'independent_MID6_acceptance':'PASS','scope':'six 2.5nm development reference numerical/geometry/provenance/saved-field protocol','NUMERICAL_GATE_independent':'PASS','geometry_PASS_independent':True,'saved_flow_time_series_integrity':'PASS','source_RESULT_PASS':'false preserved, independent certificate separate','diagnostic_rows':sum(r['diagnostic_rows'] for r in scalar),'complete_windows_recomputed':sum(r['windows_recomputed'] for r in window),'raw_files':240,'flow_frames':61,'flow_referenced_files':128,'release_bound_paths_unchanged':3397,'protected_paths_unchanged':len(protected),'start_beijing':start.isoformat(),'end_beijing':end.isoformat(),'development_fine_grid_completed':6,'development_fine_grid_planned':12,'three_level_grid_target':'INCOMPLETE_OR_REFERENCE_INVALID','two_level_comparison':'DESCRIPTIVE_ONLY','remaining_narrow_fine4_execution_released':False,'remaining_wide_fine2_execution_released':False,'prediction_execution_released':False,'G4_lock_unchanged':True,'solver_started_by_analysis':False,'protocol_changed':False,'new_fit':False}
 write('verdict.json',verdict)
 report=f'''# 首批6项2.5nm中网格原始结果及流场独立验收

本批 `development_grid_mid6_20261024_v1` 独立阶段验收 **PASS**。判定范围为冻结数值、几何、输入来源、原始输出和保存流场；**三格网格敏感性目标未完成，预测阶段未放行**。原RESULT_PASS=false保留，独立结果在certificate.json与本目录另存。

## 批次完成与来源

北京时间{start.strftime('%Y-%m-%d %H:%M:%S')}→{end.strftime('%H:%M:%S')}，墙钟{batch['wall_seconds']:.6f}秒，约3小时55分08秒。整批及6项独立退出码均0、顺序与冻结stage_cases一致，实际配置与6份预存配置逐字节匹配，唯一run_id/命令/物性/方法及来源绑定通过。没有stage_error，没有自动启动下一阶段。原总manifest和completion中的independent_acceptance=pending是运行结束时快照，按协议保留，不能为更新状态改动原始记录。

本批三种(h,d,w)nm=(75,25,60)/(75,120,60)/(75,120,240)，各P沿槽/T横槽，dx2.5nm、P=Ly=2w、a1e5、ν1e−6、ρ1000、μ.001、τ1。不存在新两相、动态边界或改变周期的扩展。

240份原始文件先存SHA256；release原3397绑定路径核对一致，14个G4锁定文件及锁本身保持。六份manifest/库绑定按绝对路径去重3404份；统一保护集合3638路径读取前后保持（集合重叠，不相加）。OpenLB HEAD882924a9cfc8dcdf82909e39530789cb6f5ebcc4与历史构建/运行记录一致；本轮不编译、不启动或重跑求解器。

## 数值和几何独立核验

冻结accept_batch.py显式调用数值/VTK独立程序，原程序、门槛与release不改。标量、流场、总验收分析exit均0，原始仿真exit与分析exit分开保存。重算91200行逐步诊断、66906个完整4050步滑窗，ddof1；逐项核首个达到门槛即停止。各项完成11228–31867步，未触最大步数；重算J/K=νJ/a/R=ρa/J、全程质量漂移、末态截面一致性和切片积分。

|指标|六项最坏值|冻结门槛|
|---|---:|---:|
'''
 labels={'max_mass_drift':'全程质量绝对相对漂移','max_density_deviation':'最大密度偏离','max_Mach':'最大Mach','final_window_rel_std':'末窗相对样本标准差','final_window_rel_span':'末窗相对极差','final_section_relative_difference':'末态双截面相对差','final_window_cross_abs_max':'末窗横向通量绝对值(m²/s)'}
 for k in keys:report+=f"|{labels[k]}|{worst[k]['value']:.10g}|{'<' if k in ('max_mass_drift','max_Mach') else '≤'}{worst[k]['limit']:.10g}|\n"
 report+='''
最坏run_id见numerical_worst_values.json；逐项值及原始输出定位见independent/analysis/scalar_results.csv、field_cases.json。全程密度/Mach以保存诊断核对，不声称对每个未保存时刻重建完整三维场。

独立枚举三种网格、六方向累计4,391,424个核心流体节点/1,067,136条壁面连接（不是去重几何节点总数），q_min=q_max=.5、无fallback/unresolved，材料集合保持；q=.5不等于零边界误差。

分块窗口最大密集偏差工作区8,359,200字节，在16MiB约定预算内。标量进程峰值79,096KiB、2.00秒；完整流场进程峰值1,037,968KiB、49.09秒。它们是独立后处理实测，不是求解器资源。原仿真六项峰值1,414,288KiB，见各raw resource_usage.json。

## 全部保存流场

实际reader读取61帧、递归核128份VTK引用文件，无缺失引用；已达到的计划t*帧、初态和收敛末态齐全，未来未到达计划点按协议标记，不补造或延算。有效液体节点集合完整唯一、坐标不变，速度/周期压力扰动/运动学耗散数组有限，耗散非负。所有分量体积积分J与CSV差异在Float32逐值半ULP及求和误差界内，主通量最大相对差3.26135294699e−9；末态速度与双精度切片CSV舍入成Float32后逐值一致。

压力字段是周期扰动，不当整个周期的宏观压降；耗散m²/s³不直接当W/m³。本轮不额外作能量闭合、局部机制分解或论文成品图验收。具体逐帧记录与哈希见independent/analysis/flow_frames.json和flow_files_sha256.json。

## 两档网格差异：描述性结果与风险

通过绑定导出器把6个已验收粗格与本批6个中格组成12行来源表，已重新核实raw/证书/协议哈希。缺少1.25nm的六项，冻结三格比较程序明确返回INCOMPLETE_OR_REFERENCE_INVALID，不能从程序exit0或本批PASS推出网格目标PASS。

下表为100×|Q(5)/Q(2.5)−1|，分母为中格数值参考；不是1.25nm参考差或连续解误差界：

|h/d/w（nm）|KP差异/%|KT差异/%|A差异/%|
|---|---:|---:|---:|
'''
 for d,w in [('25','60'),('120','60'),('120','240')]:
  r={x['quantity']:float(x['absolute_difference_percent']) for x in two if x['d_nm']==d and x['w_nm']==w}
  report+=f"|75/{d}/{w}|{r['P']:.6f}|{r['T']:.6f}|{r['A']:.6f}|\n"
 report+='''
横槽KT两格差异约1.086%–1.606%，必须保留为5nm参考空间敏感性风险，不因本批数值验收通过就淡化；它不等于预先规定的5对1.25nm≤1%三格目标已经FAIL或PASS。仍需真实最细格及趋势判定；不能事后放宽1%/0.5%、删除不利方向或以细格替换5nm主模型比较来使公式变准。两格不能确定可靠观察阶或GCI，本轮不报告其值。

## 接续与边界

开发细格6/12已完成并独立验收：全部中格6项齐全，窄槽1.25nm四项和宽槽1.25nm两项仍缺。已满足原分批方案中“中格6项独立数值/场验收”这一上游条件；是否执行下一批仍需单独准备和审查窄槽4项入口、资源及后续比较，**本轮没有放行、启动下一批**。最大宽细22GiB可用RAM/长期预算约束未解决。预测16+4继续关闭。

G4 v1锁和既有公式保持，无新拟合。若用新增开发数据重拟合须另立模型v2，在保留预测结果产生前重新冻结。无Git提交或推送。当前判断来自已完成原始文件；没有凭目录、exit0或旧报告单独判PASS。

证据入口：verdict.json；independent/certificate.json；独立scalar/flow日志及exit/resource；batch_review.json；numerical_worst_values.json；accepted_references12.json；partial_grid_comparison.json；two_level_sensitivity.csv；protection_before.json/raw_hashes_before.json/final_integrity.json。原始目录CASE/D_series/D4_variable_groove_transport_20261023/results/development_grid_mid6_20261024_v1/，完整逐项run_id见field_cases。方法沿用本批冻结协议与独立程序；流场核对采用paraview-publication的实际reader/有效液体/单位和来源原则，不以图像外观替代数值判断。
'''
 (OUT/'REPORT.md').write_text(report)
 block='''## 第一篇：首批中网格6项已完成并独立验收PASS，三格目标尚缺最细6项（2026-10-24，当前入口）

- 用户授权整批结束后独立验收。本批development_grid_mid6_20261024_v1北京时间12:35:37→16:30:44完成，14107.606463秒；批次与6项独立exit均0。当前入口docs/reports/D4_grid_mid6_acceptance_20261024/REPORT.md、verdict.json和independent/certificate.json。旧运行中/4项快照保留，现以本段为准。
- 冻结验收程序scalar/flow/总分析exit均0：重算91200行诊断与66906个4050步完整窗，核首个停止点、J/K/R/切片/守恒；6项数值/几何/来源/输出阶段PASS。最坏质量1.36360595e−11<1e−10、密度8.75048167e−9≤1e−6、Mach2.49781115e−7<.05、std9.99843736e−7≤1e−6/span4.97540473e−6≤5e−6、末截面1.61014454e−7≤1e−5、cross1.39589343e−20≤1e−12。原RESULT_PASS=false和原manifest/completion中pending快照不改，独立结论另存。
- 独立三网格六方向累计4391424节点/1067136壁面连接、q=.5、无fallback/unresolved；61完整帧/128引用文件实际读取通过，节点集合不变、字段有限、通量匹配在Float32界内，最大主相对差3.26135295e−9，末态与CSV舍入后逐值一致。标量分析峰值79096KiB/2.00s、流场1037968KiB/49.09s；分块std工作区8359200字节≤16MiB预算。
- 240本批原始文件、3397 release绑定、3404去重manifest/库绑定保持；统一保护3638路径前后哈希相同（集合重叠不相加），OpenLB HEAD与G4锁/14绑定保持。本轮未编译、启动或重跑求解器，未改协议/门槛/旧FAIL、未拟合或推送GitHub。
- 粗6+中6已来源绑定导出，三格比较因缺1.25nm六项返回INCOMPLETE_OR_REFERENCE_INVALID。描述性5对2.5nm差：h75/d25/w60的KP/KT/A=0.919906%/1.606273%/0.675517%；d120/w60=0.954085%/1.587959%/0.623966%；d120/w240=0.228374%/1.085936%/0.848350%。横槽1.09–1.61%差异是5nm参考敏感性风险，不能称网格独立，亦不提前当5对1.25的最终目标FAIL/PASS。
- 开发细格6/12已完成并独立验收，尚缺窄槽1.25nm四项与宽槽两项；原基础8/主开发16/额外线性4验收保持。中6通过满足下一批的上游条件，下一具体动作单独准备/审查窄槽4项入口、资源及三格比较；本轮未放行或启动。宽细22GiB/多日预算未解决，预测16+4仍关闭；G4 v1锁保留，重拟合另立模型v2并在保留结果前冻结。

'''
 sync=[]
 for name in ['SIM240_AI_CONTEXT.md','AI_HANDOFF_20261015.md']:
  p=ROOT/'docs/reports'/name;before=p.read_text();(OUT/(name+'.before')).write_text(before)
  start=before.index('## 第一篇：首批中网格6项');end=before.index('## 第一篇：D4余14项',start)
  after=before[:start]+block+before[end:]
  old='- 中格6项入口与有界内存验收链准备已完成，以上方本轮入口为准；待用户手动启动，完成后独立验收，不自动下一批。'
  new='- 中格6项已完成并独立验收PASS，以上方本轮入口为准；当前开发细格6/12，尚缺最细6项，不自动下一批。'
  after=after.replace(old,new)
  # Correct only stale operational counters outside the retained historical evidence narrative.
  phrase='开发细格0/12，空间精度尚未验收；预测16+4仍未进入。'
  replacement='开发细格当前6/12（中格本轮验收见上方），三格空间精度尚未验收；预测16+4仍未进入。'
  after=after.replace(phrase,replacement)
  p.write_text(after)
  assert before[end:].replace(old,new).replace(phrase,replacement)==after[after.index('## 第一篇：D4余14项'):]
  (OUT/(name+'.diff')).write_text(''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile=name+' before',tofile=name+' after')))
  sync.append({'path':str(p),'before_sha256':hashlib.sha256(before.encode()).hexdigest(),'after_sha256':sha(p),'other_sections_preserved_except_stale_operational_status':True})
 write('state_sync.json',sync)
 changed=[p for p,h in protected.items() if sha(Path(p))!=h];assert not changed
 write('final_integrity.json',{'checked_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'protected_paths':len(protected),'changed':changed,'ok':not changed,'original_raw_and_frozen_inputs_modified':False,'solver_started':False,'new_compilation':False,'prediction_released':False})
 write('artifact_hashes.json',{str(p.relative_to(OUT)):sha(p) for p in OUT.rglob('*') if p.is_file() and p.name!='artifact_hashes.json'})
 print(json.dumps(verdict,ensure_ascii=False,indent=2))
if __name__=='__main__':main()

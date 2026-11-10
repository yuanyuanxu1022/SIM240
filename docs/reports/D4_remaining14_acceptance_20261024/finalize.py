#!/usr/bin/env python3
"""Summarize independently recomputed completed results; no solver execution."""
from pathlib import Path
import json,csv,hashlib,datetime,difflib
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[2];CASE=ROOT/'CASE/D_series/D4_variable_groove_transport_20261023'
def load(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def main():
 scalar=load(OUT/'scalar_acceptance/scalar_results.json');flow=load(OUT/'scalar_acceptance/flow_frames.json');batch=load(OUT/'batch_review.json');windows=load(OUT/'scalar_acceptance/rolling_window_checks.json')
 assert batch['ok'] and flow['ok'] and flow['cases']==len(scalar)==14
 assert all(r['independent_numerical_gate'] and r['geometry_PASS'] and r['source_self_RESULT_PASS']=='false' for r in scalar)
 assert flow['frames_read']==sum(r['frames'] for r in scalar)
 original=load(OUT/'protection_before.json');assert all(sha(Path(k))==h for k,h in original.items())
 limits=json.loads((CASE/'protocol/execution.json').read_text())['numerical_limits']
 keys={'max_mass_drift':'mass_relative_strict','max_density_deviation':'density_deviation','max_Mach':'Mach_strict','final_window_rel_std':'relative_std','final_window_rel_span':'relative_span','final_section_relative_difference':'section_relative_difference','final_window_cross_abs_max':'cross_flux_m2_s'}
 worst={k:{'value':max(scalar,key=lambda r:r[k])[k],'run_id':max(scalar,key=lambda r:r[k])['run_id'],'limit':limits[v]} for k,v in keys.items()}
 write(OUT/'numerical_worst_values.json',worst)
 verdict={'batch_id':batch['batch_id'],'independent_remaining14_acceptance':'PASS','scope':'frozen 5nm development numerical/geometry/output protocol only','cases':14,'NUMERICAL_GATE_independently_recomputed':'PASS','geometry_PASS_independently_checked':True,'flow_time_series_integrity':'PASS','input_and_exit_integrity':'PASS','source_RESULT_PASS':'false, preserved in all original files','development_grid_accuracy':'NOT_EVALUATED','final_formula_validation':'NOT_EVALUATED','prediction_execution_released':False,'G4_candidate_lock_unchanged':True,'new_solver_run':False,'new_fit':False,'diagnostic_rows':48849,'complete_windows_recomputed':sum(v['windows_recomputed'] for v in windows),'raw_batch_files':552,'flow_frames':flow['frames_read'],'flow_referenced_files':flow['unique_referenced_files'],'development_main_cases_completed':16,'development_linearity_cases_completed':4,'development_fine_grid_cases_completed':0,'development_fine_grid_cases_planned':12}
 write(OUT/'verdict.json',verdict)
 pairs={}
 for row in scalar:pairs.setdefault((round(row['w_nm']),round(row['d_nm'])),{})[row['direction']]=row
 with (OUT/'direction_pairs.csv').open('w',newline='') as f:
  writer=csv.writer(f);writer.writerow(['h_nm','w_nm','d_nm','P_nm','K_parallel_m3','K_perpendicular_m3','A','parallel_run_id','perpendicular_run_id'])
  for (w,d),p in pairs.items():writer.writerow([75,w,d,2*w,p['P']['K_m3'],p['T']['K_m3'],p['P']['K_m3']/p['T']['K_m3'],p['P']['run_id'],p['T']['run_id']])
 write(OUT/'REVIEW_SCOPE.json',{'authorization':'user-owned SIM240 numerical results; explicit independent acceptance request','review_type':'internal deterministic CFD protocol acceptance, not confidential journal peer review','scope':'14 completed development cases only','skills_used':['peer-review evidence boundary','paraview-publication field semantics and payload checks'],'venue_review_policy':'not applicable: no journal review or submission','accountability':'user retains research and stage-release decisions','retention':'retain authorized local reproducibility evidence','new_solver_execution':False,'external_upload':False,'protected_raw_data_modified':False,'method_reuse':'scalar checker adapted from prior six-case independent audit, VTK reader copied byte-for-byte; not claimed as wholly new algorithms'})
 lines=['# D4余14项开发计算独立验收报告','',f'本批 `'+batch['batch_id']+'` 按冻结的5 nm开发执行协议独立验收：**PASS**。结论限本批数值、几何及输出完整性，不包含新槽宽网格精度或最终公式验证。','',
 '## 完成与判定范围','',f"北京时间2026-10-24 11:39:59.256233开始、11:55:52.888927结束，总墙钟{batch['wall_seconds']:.6f}秒（约15分54秒）。批次及14项独立exit均0，逐项run_id、配置与预存launch_configs逐字节匹配，顺序与冻结stage_cases一致；未自动进入下一阶段。原始result.txt的RESULT_PASS=false完整保留，本报告另立独立阶段判定。",'',
 '|证据层|本轮结果|边界|','|---|---|---|','|运行/输入完整性|PASS|14项与整批退出记录、输入与配置绑定|','|NUMERICAL_GATE|独立重算PASS|收敛/守恒/密度/Mach/截面/正通量等冻结门槛|','|geometry_PASS|独立检查PASS|7几何、14方向，核心节点与18方向壁面连接|','|流场时间序列|PASS|全部141实际帧，含初态、中间过程、收敛末态|','|源RESULT_PASS|false保留|独立验收写在本目录，不改历史数据|','|开发网格精度|NOT_EVALUATED|12项新细网格计算仍缺|','|最终公式/预测阶段|未放行|G4 v1锁保持，不自动拟合或预测|','',
 '## 数值重算','',f"重算48,849行逐步diagnostics、{verdict['complete_windows_recomputed']:,}个完整1013步滑窗，样本标准差分母n−1；核实停止步为首个满足窗口门槛的时刻。各项2822–7116步，均未触最大步数。独立重算质量漂移、截面相对差、J、K=νJ/a、R=ρa/J，并核最终切片积分。",'',
 '|指标|14项中最坏值|冻结门槛|','|---|---:|---:|']
 labels={'max_mass_drift':'全程质量绝对相对漂移','max_density_deviation':'全程最大密度偏离','max_Mach':'全程最大Mach','final_window_rel_std':'末窗相对样本标准差','final_window_rel_span':'末窗相对极差','final_section_relative_difference':'末态双截面相对差','final_window_cross_abs_max':'末窗横向通量绝对值(m²/s)'}
 for k in keys:lines.append(f"|{labels[k]}|{worst[k]['value']:.9g}|{'<' if k in ['max_mass_drift','max_Mach'] else '≤'}{worst[k]['limit']:.9g}|")
 lines+=['','完整最坏算例标识见numerical_worst_values.json，逐项值见scalar_acceptance/scalar_results.csv。末窗标准差有点接近预定门槛，这是按首个合格窗停止的结果，没有提高或改写门槛。密度/Mach的全程极值由原诊断记录核对；未保存逐步完整密度场，不能声称对每个未保存时刻独立重建全场。','',
 '## 几何与流场','',f"独立按矩形槽定义枚举节点及D3Q19非静止18方向连接，共核对{batch['sum_fluid_nodes_over_14_directions']:,}个方向累计核心流体节点和{batch['sum_boundary_links_over_14_directions']:,}条方向累计边界连接（不是7种几何去重总数）。q_min=q_max=0.5，无fallback或unresolved；q=.5不等于零边界误差或网格独立。",'',
 f"实际VTK reader读取141帧，递归核对296份引用文件，流体点唯一、完整且坐标不变，velocity/pressure/dissipation在有效流体域有限，耗散非负。所有分量体积积分J与CSV的差均在逐值Float32半ULP加求和误差界内；主通量最大相对差{flow['max_main_relative_flux_difference']:.10g}。各末态VTK速度与双精度field_slice舍入为Float32后逐值一致。所有已达到的t*计划点与末态齐备，未达到的未来点按原计划标为未达到，不补造、不延算。",'',
 '压力数组为周期压力扰动，不能用作整个周期的宏观压降；耗散原单位m²/s³，不能直接称W/m³。本轮验收数据完整性与一致性，不额外声称能量闭合、流动机制分解或论文成品图审查。','',
 '## 来源与保护','',f"552份本批原始文件先存SHA256。原release的2611条键记录逐项保持；14份manifest与库哈希按绝对路径去重为{batch['unique_manifest_bound_paths_verified']}份，统一保护集合为3155个路径（包含本批文件、既有输入与候选锁，集合重叠，不相加）。末次重新计算全部保护哈希一致。OpenLB HEAD {batch['OpenLB_commit']}与运行记录一致；源码/二进制和库绑定保持，编译记录沿用已有准备证据，本轮未重新编译。",'',
 'G4候选锁SHA256仍08ae91994910e98afd701143928a5186a9b22d003c96f73d9643c2eb11d810dc，14个锁定文件核对一致。未读保留预测的DNS流场或结果；已有冻结预测文件仅做哈希核对。未加入新数据重拟合，未动原协议、阈值、历史FAIL或求解器。','',
 '审查过程保留两项技术记录：前轮流场分析随会话中断未留下完整产物和退出码，恢复后仅重新执行只读流场分析，exit0；额外审查器初稿误以为命令含--config，按原run_case.py第62行及manifest纠正为binary config_path，初稿与失败日志保留。这两项不属于原仿真失败，不掩盖原始记录。','',
 '## 当前阶段与接续','',
 '结合此前已验收筛选6项（其中2项主开发、4项驱动力对照），主开发16/16与额外线性4/4齐全。本轮对既有筛选与基础证据核哈希保持，不宣称重新完成其所有数值分析。基础8项既有验收保持。12项开发细网格仍0/12，不能以粗网格数值收敛代替空间精度；预测16项及4项参考未进入。','',
 '下一具体动作是单独审查开发细网格执行入口、逐算例比较规则和分批资源条件；大网格预计资源不足问题仍需解决。本轮不启动细网格、不放行预测。若拟使用新开发数据重拟合，必须另立模型v2，并在取得保留结果前重新冻结。','',
 '## 可复核入口','',
 '- verdict.json：本批独立结论与边界。','- scalar_acceptance/scalar_results.csv、rolling_window_checks.json：逐项数值与窗口重算。','- scalar_acceptance/flow_frames.json、flow_files_sha256.json：全部帧读取、积分误差界与引用哈希。','- batch_review.json、manifest_bindings_verified.json：完成、配置、来源与额外CSV核对。','- direction_pairs.csv：本批7组几何的P/T迁移率与A，仅作已验收5nm开发数值汇总。','- protection_before.json、final_integrity.json：原始输入/数据保护；集合口径见上文。','- analysis_code_provenance.json、checker_correction.md、flow_attempt_interrupted.json：审查程序复用与过程缺陷。','',
 '原始数据根目录：CASE/D_series/D4_variable_groove_transport_20261023/results/development_remaining14_20261024_v1/；各run_id完整目录见field_cases.json。冻结依据：development_remaining14_20261024/PROTOCOL.md与protocol/execution.json。','']
 (OUT/'REPORT.md').write_text('\n'.join(lines))
 block='''## 第一篇：D4余14项已完成并独立验收PASS，开发细格与预测仍未进入（2026-10-24，当前入口）

- 用户授权独立验收14项原始结果及流场。批次development_remaining14_20261024_v1北京时间11:39:59→11:55:52结束，953.632694秒；批次及14项独立exit均0。独立报告docs/reports/D4_remaining14_acceptance_20261024/REPORT.md与verdict.json。旧“运行中/9项”是历史接收快照，当前以本段为准。
- 独立重算48,849行诊断与34,681完整1013步滑窗，14项数值/几何门槛通过；原RESULT_PASS=false完整保留，本目录另记阶段独立PASS。最坏质量2.8563681e−12<1e−10、密度3.0756491e−8≤1e−6、Mach4.3561726e−7<.05、末窗std9.99970999e−7≤1e−6/span4.97528672e−6≤5e−6、末截面2.57115771e−7≤1e−5、末窗cross3.19670987e−21≤1e−12。
- 7几何14方向独立核累计1,255,104节点/691,488边界连接，q=.5且无fallback/unresolved。读取全部141帧及296引用文件，节点集合不变、字段有限、通量积分均在Float32舍入/求和界内（最大主相对差8.55705776e−9），末态与CSV舍入后逐值一致。未到达未来计划帧明确未达到，不补造；不声称全时刻完整场或能量/机制验收。
- 552本批原始文件、2611条release键记录、2617份去重manifest/库绑定保持，统一保护集合3155路径哈希前后相符（集合重叠不相加）。OpenLB HEAD882924a9cfc8dcdf82909e39530789cb6f5ebcc4；G4候选锁及14绑定文件保持。分析中断后仅重做只读VTK分析；额外审查器命令格式假设订正已保留失败日志，不是原仿真FAIL。本轮无求解器启动/重跑/编译、门槛修改、拟合或GitHub推送。
- 结合原已验收筛选6项，主开发16/16、额外驱动力4/4齐全；基础8项验收保持，本轮对既有证据仅核哈希。开发细格0/12，空间精度尚未验收；预测16+4仍未进入。当前阶段通过不等于完整D4、最终公式或预测运行放行。
- 下一具体动作：单独审查12项开发细格的执行入口、比较规则与资源分批（最大细格资源约束尚待解决），不自动启动。G4 v1锁保留；若新开发数据重拟合须另立v2并在取得保留预测结果前重新冻结。原启动缺陷与历史快照保留，其他第一篇/第二篇内容不改。

'''
 sync=[]
 for name in ['SIM240_AI_CONTEXT.md','AI_HANDOFF_20261015.md']:
  p=ROOT/'docs/reports'/name;before=p.read_text();(OUT/(name+'.before')).write_text(before)
  start=before.index('## 第一篇：D4余14项');end=before.index('## 第一篇：G4主候选',start)
  after=before[:start]+block+before[end:]
  old='当前以顶部D4运行快照为准：筛选6项PASS，余14已由用户启动、待全部结束后独立验收'
  new='当前以顶部D4独立验收为准：筛选6项PASS，余14已独立验收PASS；主开发16/16和额外线性4/4齐全，开发细格尚缺12项'
  after=after.replace(old,new);p.write_text(after)
  assert before[end:].replace(old,new)==after[after.index('## 第一篇：G4主候选'):]
  (OUT/(name+'.diff')).write_text(''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile=name+' before',tofile=name+' after')))
  sync.append({'path':str(p),'before_sha256':hashlib.sha256(before.encode()).hexdigest(),'after_sha256':sha(p),'other_sections_preserved_except_stale_operational_phrase':True})
 write(OUT/'state_sync.json',sync)
 changed=[p for p,h in original.items() if sha(Path(p))!=h]
 write(OUT/'final_integrity.json',{'checked_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'protected_paths':len(original),'changed':changed,'ok':not changed,'simulation_executed':False,'original_solver_outputs_modified':False})
 assert not changed
 artifacts={str(p.relative_to(OUT)):sha(p) for p in OUT.rglob('*') if p.is_file() and p.name!='artifact_hashes.json'}
 write(OUT/'artifact_hashes.json',artifacts)
 print(json.dumps(verdict,ensure_ascii=False,indent=2))
if __name__=='__main__':main()

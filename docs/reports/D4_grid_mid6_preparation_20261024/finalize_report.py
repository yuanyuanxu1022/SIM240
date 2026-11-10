#!/usr/bin/env python3
"""Finalize local technical readiness and handoff; never starts a solver."""
from pathlib import Path
import csv,datetime,difflib,hashlib,json
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[2];CASE=ROOT/'CASE/D_series/D4_variable_groove_transport_20261023';STAGE=CASE/'development_grid_mid6_20261024'
def load(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(n,v):(OUT/n).write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def main():
 pre=load(OUT/'final_preflight.json');prep=load(STAGE/'evidence/preparation.json');tests=load(STAGE/'evidence/system_python_tests.json');release=load(STAGE/'release.json');flow=load(STAGE/'evidence/final_flow_reader_regression/flow_frames.json');scalar=load(STAGE/'evidence/system_scalar_regression/scalar_summary.json')
 assert pre['ok'] and prep['ok'] and tests['ok'] and flow['ok'] and scalar['all_scalar_and_geometry_checks_passed']
 assert not (CASE/'results/development_grid_mid6_20261024_v1').exists()
 rows=list(csv.DictReader((STAGE/'stage_cases.csv').open()));assert len(rows)==6
 for k,h in release['bound_inputs_sha256'].items():assert sha(k)==h,k
 mem=pre['checks'][-2]['check']['resources']['MemAvailable_bytes']/1024**3;disk=pre['checks'][-2]['check']['resources']['disk_free_bytes']/1024**3
 checked=datetime.datetime.fromisoformat(pre['checked_at_utc']).astimezone(datetime.timezone(datetime.timedelta(hours=8))).isoformat()
 summary={'technical_readiness':'PASS_LOCAL_USER_START_ONLY','allowed_cases':6,'batch_id':'development_grid_mid6_20261024_v1','source_changed':False,'new_compilation':False,'compiled_binary_reuse':'make --question exit0 and historical source/binary hashes match','describe_zero_step_checks':6,'geometry_zero_step_checks':6,'distinct_geometries':3,'collide_and_stream_calls':0,'formal_steady_runs':0,'formal_batch_exists':False,'historical_cases_window_regression':20,'historical_complete_windows':64675,'metric_difference':0,'long_window_tests':[4050,16200],'full_scalar_adapter_regression_cases':14,'full_scalar_adapter_diagnostic_rows':48849,'flow_reader_regression_frames':141,'release_bound_paths':pre['bound_inputs'],'release_sha256':pre['release_sha256'],'protected_old_paths_unchanged':pre['old_protected_paths_unchanged'],'grid_comparison_version':'executable_v2; scientific tolerances unchanged','future_remaining_grid_execution_released':False,'prediction_execution_released':False,'command_prepared':True,'user_start_confirmed':False,'checked_at_beijing':checked}
 write('preparation_verdict.json',summary)
 report=f'''# 首批6项中网格执行入口与验收链准备报告

2026-10-24。用户授权实现入口、来源绑定、分块验收、逐几何比较和运行前核查。本轮状态：**本机技术准备PASS，可交付用户手动启动中格6项；正式计算尚未启动。** 不等于数值/物理/网格验收通过或老师已批准。

## 范围与入口

新目录：`CASE/D_series/D4_variable_groove_transport_20261023/development_grid_mid6_20261024/`。

|h/d/w（nm）|P=Ly（nm）|dx（nm）|方向|数量|
|---|---:|---:|---|---:|
|75/25/60|120|2.5|P沿槽、T横槽|2|
|75/120/60|120|2.5|P、T|2|
|75/120/240|480|2.5|P、T|2|

固定batch_id=development_grid_mid6_20261024_v1。全部a1e5、ρ1000、ν1e−6、μ.001、τ1，保持充分充液、固定间隙、单相矩形槽。原C++/binary/数值协议与G4候选锁保持。make --question退出0且源码/binary与既有已验收准备哈希一致，复用原已编译程序，无新编译。

run_mid6.py只允许stage_cases.csv所列6项，测试拒绝其余84条canonical行；默认只检查，明确--execute才运行。唯一run_id/输出路径、已有批次拒绝覆盖续跑、已有正式case拒绝重跑，单进程单MPI rank。start_from_project.sh自动定位项目根，绑定也按项目根解析；从项目根、D4和/tmp调用只检查均exit0，隔离tmux的实际直接传参形式--check也exit0。所有检查后正式batch仍不存在。

## 数值与输出合同

原质量<1e−10、密度≤1e−6、Mach<.05、窗口std≤1e−6/span≤5e−6/cross≤1e−12、末截面≤1e−5及有限值/正通量/材料/几何/q/.5/无fallback/unresolved全部保持。统计窗4050步；d25/d120最大76800/292032步；dt=1.041666666666667e−12秒。原帧计划和收敛末态、未达未来帧标记保持。实际配置预存6份，未来运行生成时逐字节匹配。

每项独立exit、完整日志/原始CSV/场、输入前后哈希与时间/RSS记录；异常立即停。源RESULT_PASS=false保留。计算结束只记independent_acceptance=pending，不自动验收/拟合或运行后续。

## 审查缺口的实现与验证

1. **来源绑定导出器** export_references.py：6个粗格参考已从真实独立验收产物导出，核原始CSV/VTK哈希、配置/物性/周期/方法、run_id、K、独立exit、源码/库；共3224绑定路径。未来中格必须先完整独立验收生成certificate，再并入bundle。比较生产CLI只接bundle，verify_bundle会核绑定并按原始记录重建行；改P、改K、重复run_id等均拒绝。容器哈希不是数字签名，防完整性变化不等于对抗恶意重写所有证据。

2. **有界内存统计** window_metrics.py：16MiB工作预算，分块逐窗口计算样本标准差ddof1、极差和横向最大值，完整保留首个合格窗与旧门槛。20项已验收结果共64675个完整窗口，与原完整展开法逐值一致，最大差0，停止判定一致；4050/16200长窗与长双精度两遍计算对照通过，含小物理通量、等号与两侧检查。系统Python回归峰值{tests['max_RSS_KiB']/1024:.2f}MiB；无需分配原139GiB临时数组。

3. **完整数值验收适配** analyze_results.py：用数值矩阵读取diagnostics，避免百万行字典常驻，调用分块统计；在旧14项上完整复核48849行及全部原检查，exit0。本批未来6项仍待实际运行后验收，旧数据测试不能代替它们。

4. **流场验收适配** check_flow_frames.py：只保留规定帧诊断行、逐帧处理，限制不超过中格最大1990656核心节点。使用旧14项141帧实际reader回归通过，最大主通量相对差仍8.55705776e−9并在原Float32界内；峰值约{load(STAGE/'evidence/final_flow_reader_resource.json')['max_rss_kb']/1024:.2f}MiB。未来中格实际峰值未测，按2KiB/核心节点+1GiB留约4.80GiB预算，验收入口另要求可用RAM≥6GiB，不声称测试已覆盖2M节点动态帧。

5. **独立验收证书** accept_batch.py：仅接受已完成本批6项，总/逐项exit及输入检查后调用数值/VTK程序，分别保存独立分析exit和资源；成功才出绑定原始/分析/协议/代码的certificate。运行器不会自动调用。缺失/失败不生成PASS证书。

6. **逐几何比较与数字边界** compare_grid.py/grid_policy.json：新可执行v2，保留原1%/0.5%/η=.0001及趋势/条件GCI。Decimal精度60、输入十进制值的乘法阈值比较，修正1.01/1恰1%被二进制舍入误判的问题，等号/内外侧均验证。局部窄槽六量可PASS而缺宽槽时全局仍INCOMPLETE；最终必须三几何九量全过。仅有粗6的真实bundle通过来源核验后比较返回缺项，不是假网格PASS。CLI exit0是算术完成，不等于网格PASS。

实际Python运行环境也验证：启动器使用/usr/bin/python3（纯标准库）；系统Python NumPy1.26.4完成全部统计回归。准备环境NumPy2.5.3也通过相同20项窗口回归。VTK读取使用/usr/bin/pvpython；其版本/资源见实际记录。新比较v2不是模型v2，不修改现有G4公式/系数锁。

## 来源冻结与资源

release SHA256：`{pre['release_sha256']}`。绑定{pre['bound_inputs']}个本机绝对路径，涵盖源/binary/库/头文件/旧接受来源/新入口与协议/配置/验收比较程序/零步和回归证据。旧保护集合3156路径保持。启动日志和运行锁为可变运行记录，不纳入固定文件哈希；所有科学输入与启动脚本已绑定。release一旦存在拒绝原地重绑，任何变化须重新审查另立版本。

最后只检查快照北京时间{checked}：可用RAM约{mem:.2f}GiB、空闲磁盘约{disk:.2f}GiB，满足中格6GiB/10GiB门槛；未来启动及每项前重查。最大实际零步RSS为{max(r['resources']['max_rss_kb'] for r in prep['records'])/1024**2:.3f}GiB，不能当正式峰值保证。按原同几何粗格工作量缩放场景约5小时，最大步数工作量外推约63.5小时，都不是完成时间保证。

## 过程缺陷与边界

初次来源导出遇candidate表UTF8 BOM，已按utf-8-sig读取修正，失败日志保留。第一次隔离tmux检查脚本未在15秒内取到预期窗格状态；改用完整目标check:0.0后明确pane dead/exit0，诊断和旧记录保留。二者均发生在准备/只检查，不是仿真FAIL，不修改旧冻结证据或数值门槛。

本轮6 describe+6 precheck全部零步；无新初始化流场或steady，不运行粗格回归，只读取其已完成数据。新增Python、协议和准备文件均在新目录及本报告目录；原CASE、历史FAIL和G4锁不改。无Git提交/推送。

## 交付与下一步

唯一首批命令保存在新阶段NEXT_COMMAND.txt，交付前项目当前状态和交接已同步。用户手动启动后计算与AI分析分开；完成后另发任务独立验收6项及场，不能凭tmux消失或exit0判最终正确。中6仅有两档网格，不能完成三格判定。

后续窄细4项、宽细P/T和预测16+4仍关闭；最大两项22GiB可用RAM及长期预算没有由本许可解决。不自动下一阶段。若新开发数据重拟合G4，另立模型v2且在取得保留结果前重新冻结。

关键证据：本目录final_preflight.json/preparation_verdict.json/implementation_provenance.json；新阶段PROTOCOL、release、evidence/preparation、system_python_tests、system_scalar_regression、final_flow_reader_regression、coarse6_bundle、coarse_only_comparison及各独立exit。原12项审查保留于D4_grid_execution_review_20261024，改动逐条按本报告闭合；未运行的细格精度问题保持待验。
'''
 (OUT/'REPORT.md').write_text(report)
 block=f'''## 第一篇：首批中网格6项入口与验收链已准备，命令可交用户，尚未启动（2026-10-24，当前入口）

- 用户授权实现首批6中格入口、来源绑定、分块验收和逐几何比较。新CASE目录development_grid_mid6_20261024；报告docs/reports/D4_grid_mid6_preparation_20261024/REPORT.md与preparation_verdict.json。只允许三几何(75,25,60)/(75,120,60)/(75,120,240)nm的dx2.5、P/T共6项；其余84canonical行拒绝。batch_id=development_grid_mid6_20261024_v1。
- 6份正式配置预存、6 describe+6 precheck零步均通过（3不同几何），独立节点/18方向连接/q=.5/无fallback或unresolved通过；make --question exit0与原source/binary哈希保持，复用已编译程序，无新编译或steady。数值/几何流动验收待未来计算，不将零步当物理PASS。
- 新来源导出器核真实6粗格来源与原始/分析绑定；分块窗口用16MiB工作预算，20旧算例64675窗与原算法逐值差0且停止点一致，4050/16200长窗对照通过；系统Python测试峰值约{tests['max_RSS_KiB']/1024:.1f}MiB。完整数值适配回归14旧项48849行exit0，流场reader回归141帧exit0，未来中格动态帧仍待验收。accept_batch为完成后显式入口，不自动分析。
- 新比较可执行v2保持1%/0.5%/η与原趋势/条件GCI，Decimal等号边界及局部窄槽/全局九量作用域测试通过；粗6真实bundle现比较为缺细格，不能报网格PASS。原草案、release、源码、历史FAIL和G4锁保持；比较版本v2不是模型重拟合v2。
- 本机release SHA256 {pre['release_sha256']}，绑定{pre['bound_inputs']}路径，旧3156保护路径保持。项目根/D4/tmp和隔离tmux直接形式只检查均exit0、will_run=false；正式results批次不存在。初次BOM读取/隔离tmux检查脚本问题和修正证据保留，不是原仿真FAIL。启动脚本自动项目根定位，禁止覆盖/续跑/已有case重跑，逐项输入/资源复核，单进程单rank，异常即停。
- 末核北京时间{checked}，RAM约{mem:.2f}GiB/磁盘{disk:.2f}GiB满足中格6/10GiB；下一动作用户手动执行新NEXT_COMMAND.txt的唯一tmux命令（d4-mid6-20261024）。命令准备/交付不等于用户启动；本轮未启动或轮询正式计算。结束后独立核6项exit/哈希/诊断/全部场，再决定后续。
- 窄细4、宽细P/T和预测16+4继续关闭；中6仅两档不能做完整三格结论，最大细格22GiB与多日预算未解决。G4 v1锁保留，若新数据拟合另立模型v2并在保留结果前冻结。无Git提交推送，第一篇其他/第二篇状态保持。

'''
 sync=[]
 for name in ['SIM240_AI_CONTEXT.md','AI_HANDOFF_20261015.md']:
  p=ROOT/'docs/reports'/name;before=p.read_text();(OUT/(name+'.before')).write_text(before)
  start=before.index('## 第一篇：12项开发细网格准备审查完成');end=before.index('## 第一篇：D4余14项',start)
  after=before[:start]+block+before[end:]
  old='- 12项细格执行/比较/资源审查已完成，以上方本轮入口为准；下一动作仅准备中格6项及有界内存验收链，不自动启动。'
  new='- 中格6项入口与有界内存验收链准备已完成，以上方本轮入口为准；待用户手动启动，完成后独立验收，不自动下一批。'
  after=after.replace(old,new);p.write_text(after)
  assert before[end:].replace(old,new)==after[after.index('## 第一篇：D4余14项'):]
  (OUT/(name+'.diff')).write_text(''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile=name+' before',tofile=name+' after')))
  sync.append({'path':str(p),'before_sha256':hashlib.sha256(before.encode()).hexdigest(),'after_sha256':sha(p),'other_sections_preserved_except_stale_next_action':True})
 write('state_sync.json',sync)
 for k,h in release['bound_inputs_sha256'].items():assert sha(k)==h,k
 write('final_integrity.json',{'ok':True,'release_sha256':sha(STAGE/'release.json'),'bound_paths_unchanged':len(release['bound_inputs_sha256']),'formal_batch_exists':False,'steady_started':False,'source_or_original_protocol_changed':False,'new_compilation':False,'state_files_synchronized':True})
 write('artifact_hashes.json',{str(p.relative_to(OUT)):sha(p) for p in OUT.rglob('*') if p.is_file() and p.name!='artifact_hashes.json'})
 print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__':main()

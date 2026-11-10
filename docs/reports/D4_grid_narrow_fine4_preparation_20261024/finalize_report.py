#!/usr/bin/env python3
"""Write preparation and handoff evidence. No simulation launch."""
from pathlib import Path
import datetime,difflib,hashlib,json
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[2];CASE=ROOT/'CASE/D_series/D4_variable_groove_transport_20261023';STAGE=CASE/'development_grid_narrow_fine4_20261024'
def load(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(n,v):(OUT/n).write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def main():
 pre=load(OUT/'final_preflight.json');budget=load(OUT/'resource_budget.json');prep=load(STAGE/'evidence/preparation.json');tests=load(STAGE/'evidence/prebinding_review.json');flow=load(STAGE/'evidence/flow_reader_regression/flow_frames.json');scalar=load(STAGE/'evidence/scalar_adapter_regression/scalar_summary.json');release=load(STAGE/'release.json')
 assert pre['ok'] and prep['ok'] and tests['ok'] and flow['ok'] and scalar['all_scalar_and_geometry_checks_passed']
 assert not (CASE/'results/development_grid_narrow_fine4_20261024_v1').exists()
 protected=load(OUT/'protected_inputs_before.json');assert all(sha(k)==v for k,v in protected.items())
 assert all(sha(k)==v for k,v in release['bound_inputs_sha256'].items())
 maxrss=max(x['resources']['max_rss_kb'] for x in prep['records']);last=pre['checks'][-2]['check']['resources'];ram=last['MemAvailable_bytes']/1024**3;disk=last['disk_free_bytes']/1024**3
 summary={'technical_readiness':'PASS_LOCAL_EXPLICIT_USER_START_ONLY','batch_id':'development_grid_narrow_fine4_20261024_v1','allowed_cases':4,'other_canonical_rows_rejected':86,'describe_zero_step_checks':4,'geometry_zero_step_checks':4,'distinct_geometries':2,'collide_and_stream_calls':0,'formal_steady_runs':0,'formal_batch_exists':False,'source_binary_original_protocol_unchanged':True,'new_compilation':False,'existing_compiled_binary_reused':True,'upstream_MID6_acceptance_preserved':True,'bound_upstream_coarse_and_middle_rows':12,'window_helper_and_comparison_byte_identical_to_MID6':True,'historical_complete_windows_compared':64675,'historical_cases_compared':20,'maximum_metric_difference':0,'long_window_lengths_tested':[4050,16200],'scalar_adapter_regression_cases':6,'scalar_adapter_regression_diagnostic_rows':91200,'field_reader_regression_existing_cases':4,'field_reader_regression_existing_frames':40,'grid_finest_field_data_verified':False,'three_grid_real_narrow_result':'PENDING_FOUR_FINEST_RUNS_AND_ACCEPTANCE','release_bound_paths':pre['release_bound_paths'],'release_sha256':pre['release_sha256'],'protected_old_paths_unchanged':len(protected),'RAM_available_GiB':ram,'disk_free_GiB':disk,'minimum_available_RAM_GiB':4,'minimum_free_disk_GiB':11,'command_prepared':True,'user_started':False,'wide_fine_execution_released':False,'prediction_execution_released':False,'checked_at_beijing':pre['checked_at_beijing']}
 write('preparation_verdict.json',summary)
 report=f'''# 窄槽四项1.25nm最细网格准备与审查报告

2026-10-24。用户授权准备执行入口、资源和三格比较接续。本机技术准备 **PASS，可以交付用户手动启动本批4项的唯一命令**；正式批次尚未创建，未执行steady，未得到新最细格数值或流场。该结论不等于科学/网格PASS或老师外部审批。

## 逐算例范围与不变合同

新目录 `CASE/D_series/D4_variable_groove_transport_20261023/development_grid_narrow_fine4_20261024/`；batch_id=`development_grid_narrow_fine4_20261024_v1`。

|h/d/w（nm）|P=Ly（nm）|dx（nm）|方向|流体节点/方向|窗口步数|最大步数|
|---|---:|---:|---|---:|---:|---:|
|75/25/60|120|1.25|P、T|645120|16200|307200|
|75/120/60|120|1.25|P、T|995328|16200|1168128|

逐项ID、配对中格、步数和预算在case_budget4.csv。a1e5、ρ1000、ν1e−6、μ.001、τ1与原碰撞/边界/充分充液固定单相保持；dt=2.604166666666667e−13s。原质量/密度/Mach/窗口/截面/几何/有限值门槛和帧计划不改。首个原合格窗即停；未达到未来帧不补造或延算。源RESULT_PASS=false保留，完成后独立验收另存结论。

4项白名单只允许两窄槽1.25nm P/T；其余86canonical行拒绝，包含宽细2项、预测、已完成粗格/中格。run_narrow4.py默认仅检查；唯一batch和实际配置/输出路径固定，已存在batch或同case正式result拒绝覆盖、续跑或改tag重跑。单进程单rank、逐项串行，非零exit/绑定变化/资源不足立即停；不自动验收/拟合/启动下一批。

## 上游来源与新增实现

上游中格6项已独立验收PASS，原240文件、certificate与全部分析证据的哈希重新核对，原中格release/源码/程序不改。默认来源导出器合并真实粗6与已验收中6，生成12行bound upstream bundle；已有完整canonical参数/物性/周期/方法/K/run_id/独立exit/原始与分析来源均保持。新阶段改动是白名单、规模/资源、已知batch注册、上游certificate接入和新finish_grid_review入口；window_metrics.py、compare_grid.py、grid_policy.json三文件与冻结中格版逐字节一致。

未改C++、binary或原数值协议；make --question exit0、source/binary与原已验收哈希一致，复用已编译程序，无新编译。4 describe+4 precheck全部exit0、collideAndStream=0；2个不同形状/4方向均实际核几何与独立18方向壁面连接/q=.5，fallback/unresolved=0；实测最大零步RSS {maxrss}KiB，约{maxrss/1024**2:.3f}GiB。零步只证明安装和参数，不证明新流动物理精度。

## 分块验收与比较接续核查

- 新阶段拒绝/回归检查通过：4允许、86禁止；RAM/磁盘不足、错MPI/OpenLB、绑定变化/缺失、错批次/重复完成case、参数变更、伪造周期/K/重复run_id等拒绝；相对路径从其他目录定位仍正确。
- 20个已有5nm算例共64675完整窗口与未分块算法逐值差0，停止点一致；4050/16200长窗及低物理通量和长双精度两遍算术对照通过；工作预算16MiB，ddof1和原阈值不变。系统Python测试峰值{tests['max_RSS_KiB']/1024:.2f}MiB。旧阶段同一helper验证来源保持，不将测试当新最细格验收。
- 新数值适配器在已完成中格6项/91200行上完整回归exit0，实测峰值{load(STAGE/'evidence/scalar_adapter_resource.json')['max_rss_kb']}KiB。流场适配reader在已完成窄槽中格4项/40帧、84引用文件上实际读取exit0，峰值{load(STAGE/'evidence/flow_reader_resource.json')['max_rss_kb']}KiB；节点/字段/时间/通量与CSV保持，主通量最大相对差2.52670131e−9且在Float32界内。
- 未来fine4动态帧和完整证书还未产生，尚不能作真实fine4端到端验收。accept_batch.py只接受完成且正确batch的四项；当前给它中格batch或给finish_grid_review中格证书均拒绝，不创建伪验收目录。
- 真实上游12行经比较CLI输出缺最细格，未报全局或窄槽PASS。人造数据证明：窄槽六量可以局部PASS而宽细缺失时全局仍INCOMPLETE；窄槽某量失败时明确保留geometry FAIL及局部NOT_PASS，不能被全局缺项掩盖。阈值等号/内外、非单调/不收缩、近乎平坦、重复数据分支保持。

真实接续顺序冻结为：

1. 用户运行本批4项，结束后另行要求独立验收。
2. accept_batch.py按原合同完成数值/几何/输入/全部保存场核验，通过才生成四项certificate。
3. 显式调用finish_grid_review.py；它接完整四项证书，默认加已验收粗6/中6，形成16行有来源的参考并执行三格比较。
4. 每个窄几何的KP/KT/A分别判E(5→1.25)≤1%、E(2.5→1.25)≤0.5%以及原趋势分支，两个几何六量全过才给narrow_six_quantity_gate=PASS。原Decimal精度60/η=.0001/条件GCI均保持。
5. 任一FAIL或INCONCLUSIVE先停下复核；即便局部PASS，也只触发之后单独审查宽细22GiB/长期预算，不自动生成许可或运行。缺宽细2项时全局九量目标仍未完成。

中格已见窄槽横槽5→2.5nm差约1.59–1.61%，是保留的5nm参考敏感性风险。新最细格结果可能证明预设容差不满足；不得改门槛、丢点/方向、换最细参考，或用细格替换原5nm主模型评价以使公式变准。两窄几何三格只支持规定扩散缩放路径的联合离散敏感性，不等于全域网格独立/误差上界。G4 v1锁及原3%/5%预测合同不动，未新拟合。

## 资源与工作量

原分批方案要求可用RAM≥4GiB、磁盘≥11GiB，本轮不降低。末次只检查北京时间{pre['checked_at_beijing']}：可用RAM约{ram:.2f}GiB、磁盘约{disk:.2f}GiB，满足；未来启动及每项前重查。swap不作可用RAM，不关闭用户程序或删除旧结果来满足门槛。

最坏原始诊断数值矩阵约178.25MiB，另有线性窗口输出及临时工作区；reader最大995328核心节点，按2KiB/节点+1GiB预算约2.90GiB，验收前同样要求4GiB空闲。此预算与零步RSS/旧帧回归分别报告，新细格真实峰值仍待计算/验收后测定，不能将零步当正式峰值保证。

用对应已验收中格四项的实测秒数按节点8倍、同物理时间步数4倍即32倍缩放，场景合计{budget['middle_scaled_stop_scenario_hours']:.2f}小时；沿用旧慢样本的最大步数工作量外推{budget['historical_cap_work_extrapolated_hours']:.2f}小时。均不是预计完成时间或严格上界；新格缓存、输出、负载和停止步数可能变化。不能为缩短时长改统计窗、周期、物性或收敛规则。

## 冻结与最终运行前核查

release SHA256 `{pre['release_sha256']}`，绑定{pre['release_bound_paths']}本机输入路径；旧保护集合{len(protected)}路径保持（包含旧输入、旧中格原始/验收，合并重叠，不相加）。上游证据、源码/binary/依赖/头文件、四项协议/配置/入口/验收比较程序、零步/测试和资源预算均绑定。已存在release拒绝原地重绑；启动日志和运行锁属于可变记录，科学输入和wrapper绑定。

从项目根、D4和/tmp运行默认只检查均exit0、will_run=false；隔离tmux按交付的直接参数形式--check、明确窗格check:0.0读取exit0。没有启动steady或创建正式batch，没有影响用户现有tmux会话。源码、原协议/数值门槛、中格冻结文件/原始记录、历史FAIL及G4锁保持；无Git提交/推送。

当前停点为“本机技术准备完成、命令可交付，用户未启动”。唯一NEXT_COMMAND.txt只启动这4项，结束即停。项目状态与交接已同步后再交付；命令已交不等于计算完成。宽细2项、预测16+4继续关闭；重拟合另立模型v2并在保留预测结果前重新冻结。

证据：preparation_verdict.json、final_preflight.json、resource_budget.json、case_budget4.csv、implementation_provenance.json、final_integrity.json；新阶段evidence/preparation、prebinding_review、cli_prebinding、upstream12_bundle、scalar_adapter_regression与flow_reader_regression及各独立exit/resource；新阶段PROTOCOL/release/NEXT_COMMAND和原中格独立验收入口。流场数据语义沿用前轮paraview-publication实际reader/有效液体/单位/来源核查原则，不以画面代替数值门槛。
'''
 (OUT/'REPORT.md').write_text(report)
 block=f'''## 第一篇：窄槽4项1.25nm最细网格准备完成，命令可交付，尚未启动（2026-10-24，当前入口）

- 用户授权准备/审查窄细4项入口、资源和三格接续。新目录development_grid_narrow_fine4_20261024，报告docs/reports/D4_grid_narrow_fine4_preparation_20261024/REPORT.md与preparation_verdict.json；batch_id=development_grid_narrow_fine4_20261024_v1。仅(h,d,w)=(75,25,60)/(75,120,60)nm、dx1.25、P/T四项，其他86canonical行拒绝。旧中格6项独立PASS及全部原始/分析哈希保持。
- 正式4配置预存、4 describe+4 precheck零步exit0，2形状/4方向独立节点/18方向q=.5无fallback/unresolved通过。原source/binary与make --question exit0保持，复用已编译程序，无新编译/steady；窗口16200、d25/d120上限307200/1168128，dt2.604166666666667e−13s，原数值/输出门槛不改。
- 分块window/helper、比较程序与grid_policy均和中格冻结v2逐字节一致。20旧算例64675窗逐值差0、停止点一致、4050/16200长窗对照通过；适配器回归中格6项91200行exit0，reader回归旧窄中4项40帧exit0，未来fine4动态结果仍待验收。来源默认接粗6+中6证书，实际12行无伪细格；finish_grid_review待真实四项独立证书后导出16行，明确两窄槽六量PASS/FAIL/INCONCLUSIVE，不被宽细缺项掩盖；全局仍需宽细2项。
- 资源末核北京时间{pre['checked_at_beijing']}，可用RAM约{ram:.2f}GiB/磁盘{disk:.2f}GiB满足4/11GiB门槛；零步最大RSS{maxrss}KiB，验收预算约2.90GiB、最大诊断矩阵178.25MiB+线性输出/16MiB工作区。对应中格实测×32场景约{budget['middle_scaled_stop_scenario_hours']:.2f}h，旧上限工作量{budget['historical_cap_work_extrapolated_hours']:.2f}h，均非耗时保证。不会释放用户内存/改门槛。
- 本机release SHA {pre['release_sha256']}，绑定{pre['release_bound_paths']}路径，旧{len(protected)}保护路径一致。项目根/D4/tmp及隔离tmux直接形式只检查exit0、will_run=false，正式results批次不存在；默认只查/明确执行、禁止覆盖重跑、逐项资源和输入/库核对、单进程单rank、异常即停、不自动验收或下一阶段。
- 下一动作用户在本机手动执行新NEXT_COMMAND.txt唯一tmux命令，session=d4-narrow4-20261024；命令交付不等于启动。结束后独立验收4项及全部场，再按冻结1%/0.5%/η与趋势判两个窄槽三格。已知横槽5→2.5nm约1.6%风险保留，预设容差可能失败，不删点换参考或改阈值。
- 本轮无正式仿真/初始化、重跑、拟合或Git推送；G4 v1锁保留，重拟合另立模型v2并在保留结果前冻结。开发细格仍6/12（中格已验收，最细未运行）；宽细2项/预测16+4关闭，宽细22GiB与长期预算未解决。即使窄槽局部PASS也不自动给宽细许可；第一篇其他与第二篇状态保留。

'''
 sync=[]
 for name in ['SIM240_AI_CONTEXT.md','AI_HANDOFF_20261015.md']:
  p=ROOT/'docs/reports'/name;before=p.read_text();(OUT/(name+'.before')).write_text(before)
  at=before.index('## 第一篇：首批中网格6项');after=before[:at]+block+before[at:]
  old='下一具体动作单独准备/审查窄槽4项入口、资源及三格比较；本轮未放行或启动。'
  new='窄槽4项入口/资源/三格接续准备已完成，以上方新入口为准，待用户启动；本轮中格验收不等于窄细已计算。'
  after=after.replace(old,new);p.write_text(after)
  assert before[at:].replace(old,new)==after[after.index('## 第一篇：首批中网格6项'):]
  (OUT/(name+'.diff')).write_text(''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile=name+' before',tofile=name+' after')))
  sync.append({'path':str(p),'before_sha256':hashlib.sha256(before.encode()).hexdigest(),'after_sha256':sha(p),'other_sections_preserved_except_stale_next_action':True})
 write('state_sync.json',sync)
 assert all(sha(k)==v for k,v in protected.items());assert all(sha(k)==v for k,v in release['bound_inputs_sha256'].items())
 write('final_integrity.json',{'ok':True,'release_sha256':sha(STAGE/'release.json'),'release_bound_paths_unchanged':len(release['bound_inputs_sha256']),'old_protected_paths_unchanged':len(protected),'formal_batch_exists':False,'steady_started':False,'original_source_protocol_G4_unchanged':True,'new_compilation':False,'wide_fine_and_prediction_released':False,'state_files_synchronized':True})
 write('artifact_hashes.json',{str(p.relative_to(OUT)):sha(p) for p in OUT.rglob('*') if p.is_file() and p.name!='artifact_hashes.json'})
 print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__':main()

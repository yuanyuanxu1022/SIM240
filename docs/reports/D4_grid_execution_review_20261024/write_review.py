#!/usr/bin/env python3
"""Write the scoped review and synchronize current status without touching frozen inputs."""
from pathlib import Path
import datetime,difflib,hashlib,json
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[2]
def load(n):return json.loads((OUT/n).read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(n,v):(OUT/n).write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def main():
 batches=load('batch_resource_review.json');resource=load('resource_snapshot.json');entry=load('entry_review.json');static=load('static_verification.json');probes=load('comparator_probes.json')
 assert static['ok'] and entry['actual_grid12_configs_found']==0 and not entry['dedicated_grid_runtime_stage_directory_found']
 checked=datetime.datetime.fromisoformat(resource['checked_at']).astimezone(datetime.timezone(datetime.timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S')
 findings=[
 {'id':'R1','priority':'BLOCKS_EXECUTION','finding':'12项仅有参数JSON模板，无细格专用runner/正式key=value配置/阶段release；旧三份release允许细格0项','evidence':['entry_review.json','development_completion_plan_20261024/preparation.json','tools/run_case.py:31'],'action':'另建中格6项独立入口；默认只检查，白名单/批次/配置/输入绑定/资源/禁止重跑全部审查后才交付命令'},
 {'id':'R2','priority':'BLOCKS_TRUSTED_COMPARISON','finding':'现比较器只检查声明字段，未证实run_id、真实证据及P/Ly/物性/驱动一致','evidence':['comparator_probes.json','development_completion_plan_20261024/compare_grid.py:27'],'action':'增加来源绑定的独立验收导出器，匹配完整canonical case、run/config/hash/exit/流场验收，不能直接手填true'},
 {'id':'R3','priority':'BLOCKS_INTERMEDIATE_GATE','finding':'比较器固定要求18行，完成中6+窄细4后有16行，仍缺宽细P/T，无法据其全局状态裁定先行窄槽两族','evidence':['comparator_probes.json','development_completion_plan_20261024/compare_grid.py:27'],'action':'新版本另记逐几何结果；两个窄槽六个量均通过才可审宽细预算；完整九量最终要求保留，不能用子集PASS称全局PASS'},
 {'id':'R4','priority':'BLOCKS_BOUNDED_ACCEPTANCE_PIPELINE','finding':'原验收器将全部滑窗传给NumPy std，实际产生窗口数×窗长的密集临时数组，细格上限场景约139GiB','evidence':['case_review12.csv','numpy_variance_implementation.txt','numpy_temporary_probe.json','../D4_remaining14_acceptance_20261024/analyze_remaining14.py:98'],'action':'新增分块独立验收器，保留ddof=1、所有完整窗口、首个停止点和原门槛；用原5nm全窗口及细格长度人造数据核对，不用不稳定二阶矩相减替代'},
 {'id':'R5','priority':'RESOURCE_HOLD_WIDE_FINE','finding':f"本次可用RAM{resource['memory_available_GiB']:.2f}GiB，小于宽槽1.25nm预定22GiB门槛，不能把总内存或swap算作可用RAM",'evidence':['resource_snapshot.json','batch_resource_review.json'],'action':'宽细P和T分别保持HOLD，先窄槽证据，之后单独审满足RAM的机器/空闲资源及多日预算；不关闭用户进程或减门槛'},
 {'id':'R6','priority':'PRE_FREEZE_NUMERIC_BOUNDARY','finding':'十进制恰好1%的合成量[1.01,1.002,1]因二进制计算得到E02=0.010000000000000009而被判FAIL','evidence':['comparator_probes.json','development_completion_plan_20261024/compare_grid.py:14'],'action':'新版本在新细格结果出现前明确数字边界处理，如基于输入十进制值比较并测试等号内外；不改变1%/0.5%科学目标'},
 {'id':'R7','priority':'STALE_PREPARATION_CHECKER','finding':'旧verify_plan.py断言DEV14等所有结果目录不存在；已完成DEV14后不能再用其代表当前准备状态','evidence':['entry_review.json','development_completion_plan_20261024/verify_plan.py:40'],'action':'旧证据保持字节，新增当前细格专用检查；区分历史准备快照与现状态'},
 ]
 write('findings.json',findings)
 decision={'review_completed':True,'review_type':'internal method and software readiness assessment draft for researcher confirmation','existing_14_case_acceptance_unchanged':True,'coarse6_reference_pairing':'PASS','grid12_plan_geometry_and_step_checks':'PASS','existing_zero_step_evidence':'6 unique meshes verified; not 12 new direction checks and not steady results','comparison_math_selfchecks':14,'grid_runtime_ready':False,'grid_execution_released':False,'prediction_execution_released':False,'resource_snapshot_sufficient_for_solver_mid6':True,'resource_snapshot_sufficient_for_solver_narrowfine4':True,'resource_snapshot_sufficient_for_solver_widefine_P_T':False,'bounded_postprocessing_pipeline_ready':False,'comparison_policy_status':'retain original draft; reviewed targets are research tolerances pending versioned executable binding','next_concrete_preparation':'GRID_MID6 only, plus bound acceptance exporter, chunked numerical verifier and per-geometry comparison; do not launch','next_simulation_command_issued':False,'source_protocol_release_modified':False,'new_OpenLB_run':False}
 write('decision.json',decision)
 plan='CASE/D_series/D4_variable_groove_transport_20261023/development_completion_plan_20261024/'
 report=f'''# 12项开发细网格执行、比较与资源审查

2026-10-24，用户授权内部审查稿。结论：**审查完成，当前细网格执行链尚未准备齐全，不能直接发启动命令。** 已完成14项的独立验收保持；原求解器、数值协议、release、网格草案和G4候选锁不改。本轮未启动、编译、初始化或重跑OpenLB，也没有读取新细格或保留预测流动结果。

## 已证实可复用的前提

- `case_review12.csv`逐项与canonical candidate表核对12个细格planned_case_id、几何、物性、方向、步数和模板。3种(h,d,w)nm=(75,25,60)/(75,120,60)/(75,120,240)，P=Ly=2w，新增dx2.5/1.25nm各P/T。
- `accepted_coarse6.csv`已把三种几何的dx5、P/T共6项与已验收真实run_id/result/配置配对，附原始result哈希和独立验收入口。无需重复运行粗格。该表仅含粗格数值，未给缺失细格填值。
- 12项对应6种不同细网格形状；既有precheck原始记录、退出码、核心节点和q证据保持。它们代表6个独特网格的历史零步安装检查（记录方向P），不冒充本轮12方向新检查，也不证明流动精度。
- 用Decimal独立核几何和步数：2.5nm统计窗4050步、1.25nm16200步；最大步数d25为76800/307200，d120为292032/1168128；dt分别1.041666666666667e−12/2.604166666666667e−13秒。保持同一物理统计窗和最大时长，不为省时改规则。
- 原比较器14项人造数据检查通过，并增加实际K量级、来源声明、分批缺项和阈值边界的探针；这些是程序审查，不能记真实网格PASS。

## 必须补齐的问题

### R1：执行入口尚缺，已有模板不能直接运行

证据 `entry_review.json`：12个正式配置均不存在，没有细网格独立运行目录/执行release；已有基础、筛选6、开发14三份运行release对细格允许数量均0。`{plan}preparation.json`明确technical_runner_implemented=false、formal_input_binding_prepared=false，planned_configs为JSON计划、缺实际run_id/output_directory，不是求解器的key=value输入。

处理：下一步只准备GRID_MID6入口，按固定6项白名单、单进程单rank、默认仅检查、明确执行开关、唯一batch/run_id、拒绝覆盖/重跑、完整日志/独立exit/输入前后哈希、资源重查、失败即停、不自动进入后续批次。构建可先核原binary/source/库绑定与构建状态；是否需重新编译由变化决定，本轮不声称已完成新阶段构建核查。新入口必须以项目根目录解析绑定相对路径，并从项目根/D4/其他目录做相同的只检查核验；保留旧启动目录失败，不复用旧tmux命令。

### R2：算术比较器不能代替来源审查，缺绑定导出器

`compare_grid.py:27–39`键仅含h/d/w/dx/direction，acceptance flags与证据路径是声明。探针为合成表改成不存在的证据、重复run_id、错误P/Ly/ν，仍返回PASS；这符合其“纯算术输入”定位，不能将它直接当可信数据入口。

处理：新导出器必须由原始文件和独立验收产物导出，核完整planned_case_id、run_id、ρ/ν/μ/a/τ、w/P/Ly/φ、数值格式/碰撞/边界、源码/binary/库版本、配置字节/哈希、总与逐项exit、NUMERICAL_GATE与geometry及全部保存场。比较输入附证据SHA，数值必须来自该run，不能手填true。导出接口用canonical尺寸字符串，避免把SI反算的75.00000000000001等浮点尺寸当新几何。

### R3：缺逐几何中间关口

`compare_grid.py:27–48`固定三几何×三格×两方向=18行。拟议先中格6再窄细4，加粗格6共16行，仍缺宽细P/T两行；实际模拟该时点，现程序只给INCOMPLETE_OR_REFERENCE_INVALID。不能等它全局PASS才去运行宽细，因为形成闭环。

处理：在新版本增加逐几何结果，先对两个窄槽分别核KP/KT/A三量（共六量），仅这两个几何全部通过才进入宽细资源/时长审查；最终完整网格目标仍需三几何九量全通过。所有几何同一判据，阶段局部PASS不得被写成完整网格PASS。CLI退出0只代表算术执行完成，调度不得把它当网格PASS，必须读取明确的判定字段和范围。

### R4：独立验收后处理缺内存约束

现独立验收器`docs/reports/D4_remaining14_acceptance_20261024/analyze_remaining14.py:98–99`将全部滑窗交给NumPy std。安装版本NumPy2.5.3的_var在subtract后建立密集偏差数组；`numpy_variance_implementation.txt`保留来源，16×5小人造数组确认不与滑窗共享内存（没有分配大数组）。

单份临时数组估算：8×(诊断行数−窗长+1)×窗长字节。按同几何粗格停止物理时刻缩放，窄细最大约3.87GiB，宽细P约13.44GiB；允许跑满步数时，中格最大8.69GiB、细格最大139.04GiB。这还不含Python、其他诊断数组和VTK读取。因此求解器的6/4/22GiB门槛不能自动覆盖验收程序，现完整运行—验收链未就绪。

处理：新目录实现固定内存上限的分块完整窗口复核，保留ddof=1、所有窗口/首个停止点、横向通量与原阈值。不要用E[J²]−E[J]²直接替代微小相对方差而未经稳定性验证。用已验收5nm全部窗口与人造4050/16200长度窗、1e−6附近阈值和小通量核对，记录块大小/峰值与独立exit；VTK reader也需单帧释放和资源预算。此处仅给出审查要求，本轮没有重写或运行新验收算法。

### R5：最大两项仍受资源和长期预算限制

快照北京时间{checked}：总RAM{resource['memory_bytes']['MemTotal']/1024**3:.2f}GiB，可用RAM{resource['memory_available_GiB']:.2f}GiB，剩余磁盘{resource['disk_free_GiB']:.2f}GiB。不把swap计入可用RAM；这是瞬时观测，不是未来启动许可。

|批次|算例数|可用RAM门槛/GiB|磁盘门槛/GiB|本次求解器资源快照|同几何粗格缩放场景/h|原最大步数工作量外推/h|
|---|---:|---:|---:|---|---:|---:|
'''
 for b in batches:
  report+=f"|{b['group']}|{b['cases']}|{b['minimum_available_RAM_GiB']}|{b['minimum_free_disk_GiB']}|{'满足门槛，但入口/后处理未就绪' if b['snapshot_RAM_sufficient'] else 'RAM不足，HOLD'}|{b['coarse_same_geometry_scenario_hours']:.2f}|{b['historical_step_cap_work_extrapolated_hours']:.2f}|\n"
 report+='''
新场景逐项采用已验收相同几何方向的5nm实际秒数，按节点×步数的dx^−5缩放；比原用宽槽筛选套所有窄槽更具体，但缓存、诊断/写场、收敛步数与机器负载仍会变化，不是预计完成时间或上界。原预算保留不覆盖。宽细P+T新场景合计约6.35天，原跑满上限工作量约79天；两项需分别评估，不能因目录/零步检查18秒就认为正式很快。

保持6→4→1→1、逐项串行、每批独立验收后单独准备下一批。当前磁盘满足四批门槛；宽细两项RAM不足22GiB仍HOLD。不自动清理内存、关闭用户程序、开MPI/同时算多项或删除旧数据；换机器必须重建本机来源/库/预查绑定。

### R6：数值等号边界需在结果出现前明确

探针[1.01,1.002,1]理论E02恰为1%，现二进制浮点结果0.010000000000000009，按严格大于比较误入FAIL。它是限值附近的算术问题，不表示现有真实结果或物理门槛失败。新比较版本需用输入十进制一致的边界比较或明示可核的舍入处理，并测等号/内外两侧；1%/0.5%目标不变。不在未来真实结果出现后按有利方向调整。

### R7：旧准备检查是历史快照

原verify_plan.py第40行断言所有拟议批次目录不存在，现在DEV14已完成，不再适用于当前续接。保留旧脚本/verification及release字节，另立细格当前检查；不能为让旧检查通过而删除DEV14目录、改历史统计或重新生成旧绑定。

## 比较规则的审查意见

原grid_policy/GRID_PROTOCOL草案保持原样。本轮认可其作为待绑定研究容差的基本逻辑：Q=KP、KT、A分别由同几何同dx合格P/T组成；E02=|Q5/Q1.25−1|≤1%，E12=|Q2.5/Q1.25−1|≤0.5%；随后要求近乎平坦（相邻差/最细参考≤1e−4）或变化同向且收缩。九量分别判，不能用平均误差隐藏失败；缺项/原数值失败不删除、替代或纳入PASS。

这些容差不是老师原话、PDE误差界或NASA规定，需在真实细格结果出现前明确版本并绑定。观察阶/Richardson/GCI仅在差值超过诊断尺度且单调收缩时有条件报告，不强制理论二阶、不把安全因子变成保证、不以GCI小替代原数值验收。NASA NPARC的空间收敛教程支持三格与条件外推方法，不支持本项目特定1%/0.5%阈值：https://www.grc.nasa.gov/www/wind/valid/tutorial/spatconv.html （2026-10-24重新核对）。

dx减半同时dt按四分之一变化，故结果限定为该扩散缩放路径的联合离散敏感性；仅检三种几何，不能声称整个(w/h,d/h)域网格独立。若5nm目标失败，保留失败；不得用细格换掉原5nm模型主比较值来使公式变准。

## 当前决定与具体下一步

当前状态是**细格运行准备HOLD**，不是数值FAIL：细格尚未运行，不能判精度。6个合格粗格参考已经齐全；可进入“准备中格6项入口与验收链”的工作，不能据资源快照直接运行。先补R1/R2/R3/R4/R6及当前检查，完成白名单/资源/哈希/路径/配置的静态及必要零步核查，再交唯一中格6项启动命令给用户；后续4/1/1分别等待前批验收及预算条件。

G4 v1锁保持，不新拟合/读取预测流动结果，不放行预测16+4。若以后使用新增开发数据重拟合，另立v2并在取得保留结果前重新冻结。没有启动命令在本轮交付；没有git提交或推送。

## 证据入口和工具边界

- audit_grid_readiness.py：可复核的静态审查，只读旧原始/协议，生成本目录证据；不导入或调用运行器。
- case_review12.csv、accepted_coarse6.csv：12细格与6粗格来源配对、步数/资源。
- comparator_probes.json：14原人造自检与新增缺项、来源声明、限值探针。人造数据有明确标记，不可当真实算例。
- entry_review.json、batch_resource_review.json、resource_snapshot.json：入口缺口与资源快照。
- findings.json、decision.json、static_verification.json：逐条问题、当前决定与审查覆盖；static ok不是运行或精度PASS。
- protected_inputs_before.json、final_integrity.json：3156个规范化路径前后保护核对（包括旧3155保护集合及计划/验收输入的重叠合并，数量不相加）。

本材料是用户自有研究的内部协议/软件审查，没有保密期刊审稿材料、期刊决策或投稿；仅按用户授权处理本地证据，公开网页只查询方法/工具来源。用户/导师负责科学采用与长期资源决策。审查采用peer-review技能的主张—证据与可操作问题记录原则，不套用临床清单或以自动测试代替科研判断。

工具来源已按当前公开记录核对并列出：Kassis, T., Agarwal, V., He, Y., Patel, D., & Brueckner, A. M. (2026). Scientific Agent Skills: A Library of Procedural Knowledge for Research Agents. https://doi.org/10.48550/arXiv.2609.00065 （公开当前v2；不作为物理验证证据）。sim240 MCP本会话未发现可用工具，故使用针对性本地读取。
'''
 (OUT/'REPORT.md').write_text(report)
 (OUT/'NEXT_PREPARATION.md').write_text('''# 下一步具体实现边界（本文件不是运行许可）

只准备GRID_MID6，复用原求解器，另建独立版本入口。6项按已有development_grid12.csv筛选dx2.5；其他细格/预测/已完成粗格拒绝。暂不改任何旧release或源码。

同时补齐：绑定原始记录的独立验收导出器；固定内存分块完整窗口核验；保留原容差的新比较器版本（全局九量+逐几何六量关口）；阈值等号算术处理。版本/协议/哈希在取得细格结果前明确并绑定。

验证覆盖：真实6粗格来源、12候选精确配对、禁止角色与重复批次/覆写、输入篡改、错库/MPI、资源不足、任意启动目录、启动失败日志、只检查不建正式结果、分块与原5nm全部窗口结果及细格长窗人造对照。阶段配置/入口、源码binary库/构建记录、上游独立验收与比较器一起来源绑定。

技术核查完成后只交中格6项tmux命令，由用户启动；首批前可用RAM≥6GiB/磁盘≥10GiB，验收后处理另作有界内存保证。完成即停，不自动4/1/1，不打开预测。未明确的额外多日资源授权不从本文件推定。
''')
 protected=load('protected_inputs_before.json');changed=[p for p,h in protected.items() if sha(Path(p))!=h];assert not changed
 write('final_integrity.json',{'checked_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'protected_paths':len(protected),'changed':changed,'ok':not changed,'solver_source_binary_frozen_protocol_release_and_G4_unchanged':True,'new_simulations':0,'new_compilations':0,'grid_execution_released':False})
 block=f'''## 第一篇：12项开发细网格准备审查完成，入口与有界内存验收链待补（2026-10-24，当前入口）

- 用户授权审查执行入口、比较规则与分批资源；报告docs/reports/D4_grid_execution_review_20261024/REPORT.md，决定decision.json，接续NEXT_PREPARATION.md。已核12候选/6合格粗格配对、Decimal步数与6历史零步网格证据；原14项独立验收PASS保持，不重算。
- 当前grid_runtime_ready=false：只有JSON模板，无细格专用runner/正式配置/release，已有三份运行release允许细格0项。旧verify_plan断言DEV14不存在已过时，旧证据不改。未来入口须正确解析根目录绑定、拒绝旧批次/角色并保存早期报错，不能直接用旧tmux或模板启动。
- 原比较器14个人造自检通过，但缺来源绑定导出器；填true/不存在证据或错P/物性仍可算术PASS。中6+窄细4+粗6共16行时全局18行比较仍缺宽细2行，须补逐几何关口（窄槽六量先判，最终仍三几何九量）。恰1%浮点边界探针误判已记录，新版本需预先明确边界处理，不改1%/0.5%容差。
- 后处理新卡点：旧全滑窗std按安装NumPy源和小数组探针会建密集临时数组；细格最大步数场景单份约139.04GiB（中格最大8.69GiB），不能沿用粗格验收内存假设。需先补固定内存分块核验，保持全部窗口/ddof1/首个合格点与旧门槛，并与已验收5nm及细格长窗人造数据核对；本轮未实现该新算法。
- 资源快照北京时间{checked}：可用RAM{resource['memory_available_GiB']:.2f}GiB/磁盘{resource['disk_free_GiB']:.2f}GiB；中6与窄细4求解器门槛6/4GiB及磁盘10/11GiB满足，但执行/验收链未就绪；宽细P/T仍需可用RAM22GiB/磁盘19GiB，各自HOLD。顺序保留6→4→1→1，不自动连跑；同几何粗格外推约5.01/7.90/100.66/51.68h，非耗时保证，原上限工作量预算保持。
- 本轮静态/人造测试审查与3156路径保护核对通过；未启动/初始化/重跑/编译OpenLB，未改原协议/release/G4锁、未读预测流动结果、未拟合或推送GitHub。开发细格0/12、预测16+4未进入，不能以审查完成或资源满足判网格PASS。
- 下一具体动作：仅实现并核查GRID_MID6入口、来源绑定导出器、分块验收和逐几何比较，预先版本化边界处理；准备齐后另交首6项用户启动命令。本轮无命令交付。原14项验收、第一篇其他部分和第二篇状态保持。

'''
 sync=[]
 for name in ['SIM240_AI_CONTEXT.md','AI_HANDOFF_20261015.md']:
  p=ROOT/'docs/reports'/name;before=p.read_text();(OUT/(name+'.before')).write_text(before)
  at=before.index('## 第一篇：D4余14项');after=before[:at]+block+before[at:]
  stale='- 下一具体动作：单独审查12项开发细格的执行入口、比较规则与资源分批（最大细格资源约束尚待解决），不自动启动。'
  fresh='- 12项细格执行/比较/资源审查已完成，以上方本轮入口为准；下一动作仅准备中格6项及有界内存验收链，不自动启动。'
  after=after.replace(stale,fresh);p.write_text(after)
  assert before[at:].replace(stale,fresh)==after[after.index('## 第一篇：D4余14项'):]
  (OUT/(name+'.diff')).write_text(''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile=name+' before',tofile=name+' after')))
  sync.append({'path':str(p),'before_sha256':hashlib.sha256(before.encode()).hexdigest(),'after_sha256':sha(p),'other_sections_preserved_except_stale_next_action':True})
 write('state_sync.json',sync)
 write('artifact_hashes.json',{str(p.relative_to(OUT)):sha(p) for p in OUT.rglob('*') if p.is_file() and p.name!='artifact_hashes.json'})
 print(json.dumps(decision,ensure_ascii=False,indent=2))
if __name__=='__main__':main()

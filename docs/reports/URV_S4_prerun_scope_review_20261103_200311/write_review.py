"""Write a non-executable S4 scope proposal and current handoff; no CASE writes."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import hashlib,json
ROOT=Path('/home/dell/yuanyuanxu/SIM240');OUT=Path(__file__).resolve().parent
load=lambda p:json.loads(Path(p).read_text())
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(name,x):
    with (OUT/name).open('x') as f:json.dump(x,f,ensure_ascii=False,indent=2);f.write('\n')
x=load(OUT/'six_configuration_static_review.json');b=load(OUT/'binary_reuse_review.json');r=load(OUT/'resource_review.json')
scope=load(OUT/'scope_decision.json');v=load(OUT/'verification.json');p=load(OUT/'predecessor_binding_verification.json')
assert v['STATIC_REVIEW_PASS'] and p['does_not_grant_S4_authority']
now=datetime.now(ZoneInfo('Asia/Shanghai')).isoformat()
findings=[
 dict(id='C01',component='S1 native source and original ELF',status='CONDITIONALLY_REUSABLE',
      evidence='Exact binary/build/compiler/dependency/library hashes verified; parser accepts all aligned S4 parameters. No S4 native audit or time stepping performed.',
      source='CASE/unseen_v2_reference_S1_a1_v1/src/urv_reference.cpp:187'),
 dict(id='C02',component='S2/S3 stage controller, source revision and authorization',status='INCOMPATIBLE_AS_IS',
      evidence='Existing adapters require S2_REG_GRID/U_REG six cases or S3_REG_LINEARITY/U_REG four cases and exact old IDs/output paths; S3 explicitly S4_authorized=false.',
      source='CASE/unseen_v2_reference_checker_S3_reuse_v1_1/analysis/stage_s3.py:28'),
 dict(id='C03',component='Single-run scientific acceptance and field reader',status='REUSABLE_WITH_ISOLATED_PROVENANCE_DISPATCH',
      evidence='Original common already lists all S4 cases. Ten common files and three scientific scripts byte-identical across S2/S3. Keep unchanged; add isolated S4 source/authority branch.',
      source='CASE/unseen_v2_reference_checker_S3_reuse_v1_1/analysis/check_results.py:169'),
 dict(id='C04',component='R1/R2 zero-evidence checks',status='REUSE_VALIDATIONS_ADAPT_EXACT_COUNTS_AND_BINDINGS',
      evidence='Retain effective native physics/time crosschecks and own-field readback/payload association; current 12-record/4-field assertions must become exact S4 18/6 in isolated copy.',
      source='CASE/unseen_v2_reference_checker_S3_reuse_v1_1/analysis/zero_evidence.py:107'),
 dict(id='C05',component='S1/S2/S3 prior results',status='PREDECESSOR_EVIDENCE_ONLY_NOT_S4_REFERENCE_POINTS',
      evidence='Smooth d0, U_REG h60 and U_THIN h30/d80 differ. None of their K values can fill a missing S4 point or grant an S4 zero/native PASS.',
      source='CASE/unseen_v2_reference_checker_S3_reuse_v1_1/common/case_matrix.csv'),
 dict(id='C06',component='Stage-local three-grid evidence',status='MINIMUM_OFFLINE_JOIN_REQUIRED',
      evidence='After six accepted S4 results, pair each direction at 5/2.5/1.25nm under its own exact release; retain frozen grid math. Do not call/relax 24-result aggregate or upgrade reference qualification.',
      source='CASE/unseen_v2_reference_checker_S3_reuse_v1_1/analysis/evidence.py:143'),
 dict(id='C07',component='Runtime/resources/PERF',status='SEPARATE_PRE_FORMAL_DECISION',
      evidence='S2 timings are historical evidence only. Conditional full-step fine-grid costs about32h per direction against original12h cap. Decide bounded risk or separately scoped PERF after zero; no current PERF authorization.',
      source='resource_review.json'),
 dict(id='C08',component='24-case aggregate/F04/model comparison',status='OUT_OF_SCOPE',
      evidence='Original aggregate needs full24 and stage lineage. S4 grid-only preparation cannot close S5, F04, reference/model/physical/submission states.',
      source='CASE/unseen_v2_reference_checker_S3_reuse_v1_1/analysis/check_results.py:283')]
save('compatibility_findings.json',findings)
rows='\n'.join(f"|{i+1}|`{a['planned_case_id']}`|{a['dx_nm']:g}|{a['expected_core_nodes']:,}|{a['expected_wall_links']:,}|{a['window_steps']}/{a['maximum_steps']}|{a['proposed_solver_cap_seconds']/3600:g}h|" for i,a in enumerate(x))
protocol=f'''# S4-PR-v1：薄间隙三网格运行前材料与合同兼容性审查

审查时间：{now}。性质：只读范围审查、静态核对与后续最小实施提案；不是实现/构建/原生审计/PERF/正式执行许可。用户原话：“另定 S4 运行前材料与合同兼容性审查范围，不自动实现或启动计算。”下述S4-MIP-v1是供后续采用的最小准备范围，当前未采用、未实现，不因本报告自动生效为执行授权。

## 1. 科学问题和保留边界

S4_THIN_GRID在原24项URV-v1矩阵中占6项，研究U_THIN在三档网格上的导度是否稳定，是预声明薄间隙风险检查。几何h30/d80/w120/P240/Ly240nm，槽占比1/2，平均H=h+d/2=70nm。横槽h<50nm在原较窄推荐域之外；无论未来V2改善、变差或证据不足都须按预先规则报告，不换条件/系数/门槛使结果有利。

P沿槽+y、T横槽+x；a=100000m/s²、G=rho·a=1e8Pa/m；rho1000kg/m³、nu1e-6m²/s、mu.001Pa·s、tau1，D3Q19_FORCE/ForcedBGK、静止无滑移Bouzidi、x/y周期、单相全充液、固定几何。J=核心速度体积分/平面面积（m²/s），K=nu·J/a（m³），U=J/H、R=mu/K；K公式中的h仍平台间隙，不用H替换。原体力半步速度、A1体积路径、MRP双修正质量和旧质量观察量均不改。

S4不是三档驱动力检验，S5才使用S4两个中档加另四条；S2/S3的h60结果不能充当S4 h30结果，S1 h30/d0平板也不能代替沟槽。S4即使完成网格证据，也不能凭本阶段跳过S5、解除F04或评价V2。

## 2. 六配置和精确时步审查

|顺序|原矩阵planned_case_id|dx/nm|核心流体节点预期|壁面链预期|统计窗/最大步数|原单条求解上限|
|---:|---|---:|---:|---:|---:|---|
{rows}

顺序粗→中→细、每档P→T；此表保留原planned_case_id，没有新实际run_id或批准身份。dt随三网格为4.166666666666667e-12/1.0416666666666667e-12/2.604166666666667e-13s。统计窗ceil(0.75h²/(nu·dt))=162/648/2592，最长步数ceil(8(h+d)²/(nu·dt))=23232/92928/371712；有理数重算与当前源码double及减1e-9路径的结果一致。统计窗物理时长0.675ns，最大物理时长96.8ns。不能复制S2 h60的窗口步数，也不另加固定1000步。

本次独立XZ几何枚举再沿Y延拓，预测q_min=q_max=.5、上表节点和链；只是独立静态预期，geometry_PASS仍null，原生S4几何证据尚未产生。核心体积理论4.032e-21m³，质量rho乘该体积；不能据解析体积推断新原生累加精确相同。

原保存计划t*=0,.01,.02,.05,.1,.2,.5,1,2,4,8，按精确步数映射；保存已到达帧及末态、重复步去重，不为补未来帧延算。每档帧目标见six_configuration_static_review.json。每条独立退出、全过程诊断、完整日志、场引用载荷、来源/参数/输入前后指纹保留。

## 3. 同一二进制优先复用

静态裁定：在来源闭包不变时，优先直接只读引用原S1 ELF，不需要为改变输入几何重新编译。本轮没有构建或调用原生。路径`CASE/unseen_v2_reference_S1_a1_v1/build/urv_reference`，SHA `{b['binary_sha256']}`；真实历史build_environment SHA `{b['historical_build_sha256']}`。当前核对1392编译依赖、3链接库、15动态库、编译器和源码指纹一致；原S3 seal/provenance/授权结构只读复核通过，原合同S4_authorized=false保持。

源码参数读取器允许正间隙/非负槽深、对齐网格、P/T和现时间规则，S4输入均满足；原内核没有活动的S0逐节点密度捕获实例，不把其旧57600点专用限制套给S4。复用历史限定机器指令审计，不宣称本轮重新反汇编或证明全路径机器等价。

未来准备绑定必须覆盖同一真实build/source/dependency/library/compiler记录，S0/S1来源和S2/S3实际完成证据仍在各自原合同下；当前已逐项重哈希S3 2632输入、S2 2160输入及S3复核报告闭包。任何源码/ELF/编译选项/库漂移均HOLD、另审，不自动重建或改旧记录。当前同一ELF复用仍只是源/来源级结论，须另行执行S4六配置原生零步才能确认实际接入。

## 4. 合同为什么不能直接复用

原S2 source adapter明确要求S2_REG_GRID、U_REG六身份和原输出；原S3 v1.1 adapter明确要求S3_REG_LINEARITY、U_REG四身份、其原A/B/授权及两S2中档引用，并明示不授权S4/S5。原S1 adapter亦只允许两薄平板。故不能修改旧stage字段、套用旧命令、编辑旧白名单或挪用既有执行授权启动S4。

原common已列S4矩阵，原单条科学检查器按矩阵/参数读取，可在新增来源/权限分支后复用。10个common文件和check_results.py/evidence.py/read_fields.py共13文件当前S2/S3逐字节一致；拟在新隔离副本中继续保持。新contracts分派只增加精确S4分支，不放松既有分支。兼容问题属于预期工程缺口，当前无新科学证据矛盾。

## 5. S4-MIP-v1后续最小准备提案（待采用）

拟隔离新建`CASE/unseen_v2_reference_S4_reuse_v1/`及`CASE/unseen_v2_reference_checker_S4_reuse_v1/`；本次两路径均未创建。准备实施限于：

1. 独立S4阶段/source adoption anchor与验证器，精确stage=S4_THIN_GRID、六planned_case、顺序和参数；只引用原ELF与真实构建闭包。继承原S0/S1来源、S2/S3结果及本范围指纹，不给旧阶段补权。
2. 准备材料化与A/B封存入口，六正式准备身份、18零步准备身份及独立输出。run_id在实施准备时预留并记录；prepared不等于approved/actual。所有准备权限false、批准列表空。不能把report/scope JSON称为准备A或执行release。
3. 默认只读的正式控制器及独立零步入口；真正执行前校验外部SHA、真实明确授权、原始A/B、净目录、exact inputs、资源和非重复路径。失败即停，无自动重试/续算/加时/S5。活动日志在独立新路径，不能加入不可变输入；需引用旧日志时绑定不再变化的快照，保留S2-LRP历史例外。
4. 将S3 v1.1已补齐R1/R2原样保留在隔离新分支中，只按六配置改精确计数/身份。R1必须实际解析effective_config和每条native输出，核对物理换算、方向、dt、统计窗、最大步和初态半步体力响应；R2必须逐配置唯一读回本配置初态场，绑定自身路径、完整PVD/VTM/VTI闭包、单位/节点/通量与进程退出。不能只改摘要12→18、4→6，也不能漏改validate_audit_records等固定计数。
5. 有针对性的软件检查：合法关闭权限的只读路径不调用原生/VTK；错阶段/几何/方向/时步/ID/库/输出复用/许可或失配R1参数、R2串帧/重复读回/载荷漂移均拒绝；A/B不得夹带批准身份；失败后不得下一条，零步不能进入steady。仅合成/模拟进程接口，不产生真实原生或VTK调用。
6. 为已有结果准备阶段内六条网格报告入口：先分别完整接受六条，再按方向读三格并输出原规则指标；保留原每条独立SHA/原始载荷，不调用24条聚合器。辅助grid_estimate内的局部资格布尔值必须标为网格分支检查，不能冒充完整REFERENCE_QUALIFIED_FOR_CASE。S5或模型比较接口本轮不实现。

本最小准备不改C++/物理/统计路径、不新建构建系统或复制伪造build记录，不自动重跑S0–S3，不改原13个科学文件/模型预测/V2系数，不实现F04。若原ELF保持一致，未来本范围实施也无须编译或新机器指令审计；发现漂移才另审，不悄悄扩大工作。

## 6. 后续原生零步与B的独立权限

零步拟为六配置各describe/precheck/initialize，共18次原生调用，加6次实际初态场读取。当前仅有计划zero_call_plan.json，调用0。原生和初始化场读取的后续明确授权须覆盖18+6、推进0步、失败即停不重试、由用户手动启动；不能用准备实施授权或过去S2/S3的18+6/12+4授权替代。

可沿用现审计单次原生300s、单次初态读取等待300s、8GiB地址空间及输入前后指纹/资源检查作为拟定起点；实施时须写入对应过程收据。其值是预算非完成保证，不与正式求解4h/读取器1h混用。若为新几何需要调整，先另审，不自动重试或加时。正式结果检查含实际场读取的外层/内层超时仍应在正式资源协议里明确，不提前许诺整个后代进程树清理或硬批次墙钟。

原生审计完成后按原URV/MRP/A1和R1/R2独立复核18原生记录、6唯一初态读回及全部闭包；合格后另存权限关闭的准备B，保留原A/执行release/原始证据。零步只建立接入和几何证据，不给正式NUMERICAL_GATE/RESULT_PASS或稳态K。

## 7. 原科学接受门保持

每条Neumaier修正质量相对自身初态全程严格<1e-10、修正账本差≤1e-13、密度偏离≤1e-6、Mach严格<.05、Re_H（h+d尺度）≤.01、末态截面相对差≤1e-5、主通量正/有限/材料保持。最终窗样本std≤1e-6、span≤5e-6、主轴横向通量≤1e-12m²/s；必须重算全完整窗并证明首次达标停止。q=.5±1e-10、体积相对差≤1e-10、candidate=installed、fallback/unresolved0、原生/独立退出0，保存场真实读回与单位/核心几何一致。

三网格差分同号且非近零（原相对地板1e-14），p=ln(|(K粗−K中)/(K中−K细)|)/ln2为正有限，r2/Fs1.25；中细相对变化≤1%，细格GCI估计≤1%。估计u=max(GCI细、中细相对差、细格末窗跨度)，不是置信区间或严格误差界。失败如实HOLD/INCONCLUSIVE，不自动第四格、延时或调门槛。S0 h75精确回归/密度捕获重放在S4为NOT_APPLICABLE_S0_ONLY；平板2%解析误差不套到沟槽。

## 8. 资源决策前置与PERF范围

原计划单进程/单线程/1cuboid/overlap3、单受限进程地址空间8GiB，启动前可用RAM≥12GiB/盘≥100GiB、每条前盘≥8GiB、每条输出4GiB。原求解上限按网格1/4/12h、六条合计34h，检查与文件处理另计；这些只是现有矩阵预算，不是本轮正式执行授权或完成时间保证。当前资源快照RAM约{r['MemAvailable_bytes']/1024**3:.2f}GiB、盘约{r['disk_free_bytes']/1024**3:.2f}GiB，不预留给将来启动。

S4核心节点为同网格S2的70%，但完整包络格点/重叠/壁面工作和每步测量不严格按流体节点线性缩放。单份D3Q19双精度分布存储约4.90/39.22/313.79MB，不能把它当整个进程峰值内存。没有S4实测速率/峰值内存/收敛步数。

仅为暴露预算边界，以S2该方向实测elapsed/steps乘节点比0.7，再乘S4最大步数估算：若细格走满371712步，P约{x[4]['conditional_full_cap_cost_hours']:.2f}h、T约{x[5]['conditional_full_cap_cost_hours']:.2f}h，均超过原12h。不是S4预计收敛耗时，也不保证按此速度缩放；S2实际提前收敛的经历不能作为S4会及时收敛的证据。

正式绑定前必须另做资源/预算决策：零步B后审阅已有S2及届时资源，可明确接受原上限下可能超时即停的风险；若需要S4真实有限性能证据，则另定PERF最小范围/停止条件/身份/检查器并单独授权，不借本协议启动。性能推进不计作正式S4验收点。当前不强制新增性能实现，不签发PERF权限，不用缩减/跳过细格的部分结果声称三网格完整，也不自动加时。正式六条执行范围与检查预算由后续独立FRD/真实授权冻结。

## 9. 本轮状态与交付

静态范围审查通过，旧运行器直接接入不兼容；同ELF优先复用是有条件的静态裁定。S4接入未实现、未编译、未原生零步、未PERF、未正式计算，无actual_run_id/新准备A或B/执行release/启动命令。所有执行权限关闭。NUMERICAL_GATE=NOT_EVALUATED、geometry_PASS=null、RESULT_PASS=false（未运行）；REFERENCE_QUALIFIED_FOR_CASE/reference_qualified=false、MODEL_COMPARISON/physical_validation=NOT_EVALUATED、strict_error_bound_established/submission_ready=false，F04 OPEN_OUT_OF_SCOPE。

S0/S1/S2/S3既有接受保持；旧横槽FAIL/380差异、旧v1 HOLD、MRP静态FAIL、历史唯一归因未建立不追溯改判。作者声明仅限h60/d80与h30/d80未用于选系数/检验条件，外部独立核查仍false。本轮peer-review技能用于作者明确要求的内部材料审查，AI辅助工作稿不代替人工科学终审，没有期刊保密审稿或编辑裁决。

下一具体动作：采用本S4-MIP-v1最小提案后，只在新隔离候选实现阶段绑定/控制器/R1R2六配置适配/软件检查并交付权限关闭的准备A；原生18+6、性能推进和正式计算各按明确覆盖的独立授权办理。当前不自动实施。
'''
with (OUT/'PROTOCOL.md').open('x') as f:f.write(protocol)
cn_rows=[
 ('已有流动程序','有条件复用','原可执行文件、源码、构建与库指纹一致；源码支持六配置。还没有S4原生接入审计。'),
 ('旧S2/S3阶段入口和合同','不能直接使用','它们限定旧阶段、旧几何、编号和目录；原S3合同明确没有S4权限。'),
 ('单条科学检查和场读取','增加隔离来源分支后复用','原矩阵已含S4；13份科学文件保持字节相同，仅新增S4精确来源和权限分派。'),
 ('R1参数与R2初态关联检查','保留检查，适配六配置','现有12条原生记录、4份初态的固定计数须在隔离副本改为18和6，同时逐条核参数、路径和载荷。'),
 ('S1/S2/S3已有结果','仅作前置证据','平板、60nm沟槽、30nm沟槽几何不同，旧导度不能代填S4的任何网格结果。'),
 ('阶段内三网格报告','需要最小接入','六条单独完整接受后，按方向组合三格，使用原指标；不评分V2、不放行完整参考资格。'),
 ('资源与性能证据','正式绑定前另审','旧S2速度不能保证S4收敛时长；若跑满最大步粗估细格约32h，原12h上限有超时可能。当前不测速。'),
 ('24项汇总及模型比较','本轮范围外','S5、跨合同汇总、参考资格和模型准确度均不能由S4准备材料代替。')]
table='\n'.join('|'+ '|'.join(row)+'|' for row in cn_rows)
report=f'''# S4运行前材料与合同兼容性审查

日期：{now}。用户范围：另定S4运行前材料与合同兼容性审查范围，不自动实现或启动。结论：可提出最小隔离准备方案；原S1可执行文件可在指纹不变前提下优先复用，旧S2/S3合同及运行器不能直接用于S4。

本轮技术审查和静态核对通过。S4-MIP-v1仅为待采用提案，尚未实施；执行权限全false、无新CASE/实际run_id/准备A/B/启动release/命令。原生/VTK/构建/性能/正式求解调用全0，模型比较未评价。STATIC_REVIEW_PASS不等于geometry_PASS、NUMERICAL_GATE或RESULT_PASS。

## 已核清的范围

U_THIN：h30/d80/w120/P240/Ly240nm，平均H70nm，a1e5m/s²；P沿槽+y、T横槽+x，5/2.5/1.25nm两方向共六条。节点32256/258048/2064384，壁链30528/122496/490752；窗162/648/2592、最大23232/92928/371712步。精确矩阵、源码double取整、模板和独立几何静态枚举一致。现没有S4原生几何证据。

当前原S3输入2632和S2输入2160逐项一致；原S3正式seal/provenance/授权只读核验通过且S4_authorized=false。S3最近完成复核记录与其51份清单当前一致。原ELF/真实构建/1392编译依赖/3链接库/15动态库/编译器当前一致；13份科学common/检查文件在S2/S3间字节相同。总计{v['protected_files_unchanged']}份受保护文件本轮保持。没有重跑S3结果检查器或再读60帧。

## 兼容性逐项裁定

|组件|状态|依据|
|---|---|---|
{table}

## 建议的最小准备范围

只在新S4 CASE及检查器副本增加精确阶段来源/权限、关闭权限的准备A/B、默认只读控制器与独立零步入口；保留R1实际参数核查、R2逐配置真实初态载荷关联，精确扩为18原生+6初态读取。未来准备阶段只做软件检查，不自动执行这18+6。保留全部原物理、统计舍入、科学检查和common字节；增加的阶段内网格报告不评分V2/不放行参考资格。完整实施边界和拒绝条件见PROTOCOL.md第5–7节。

资源不能直接从S3中档套用：细格2,064,384节点，单份分布313.79MB不等于峰值；如果跑满最大步，S2测速按节点比例粗估约32h/方向，原12h存在超时可能。此为条件成本估算，非完成时间预测。零步B后、正式绑定前另作资源决策，决定接受原有预算风险还是另审有限PERF；本轮不测速、不延长原预算或自动建立性能程序。

S4不是参考资格/模型准确度的最后一项；S5薄间隙三档驱动力及F04跨合同资格/汇总兼容性仍另审。S2/S3数据不代填薄间隙三格，不把有利结果当省略风险检查的理由。原历史FAIL/作者声明范围/参考物理投稿边界保持。

## 当前停点与接续

S4准备未实现，NUMERICAL_GATE未评价、geometry_PASS=null、RESULT_PASS=false（未运行），REFERENCE_QUALIFIED_FOR_CASE/reference_qualified=false、MODEL_COMPARISON/physical_validation未评价、strict_error_bound_established/submission_ready=false，F04 OPEN。

下一动作：采用本最小范围后，隔离实现S4接入与软件检查，交付执行权限关闭的准备A；当前不实施。原生18+6、PERF和正式计算分别依明确授权办理，不自动推进S5。无待用户手动执行的命令。

证据入口：PROTOCOL.md、scope_decision.json、compatibility_findings.json、six_configuration_static_review.json/CSV、binary_reuse_review.json、predecessor_binding_verification.json、zero_call_plan.json、resource_review.json、verification.json、protected_inputs_before.json及document_manifest.json。AI辅助内部方法审查，不代表人工科学终审。
'''
with (OUT/'REPORT.md').open('x') as f:f.write(report)
body=f'''## S4运行前材料与兼容性审查完成：最小隔离准备提案待采用，未实现/未启动（{now}）

用户本轮只授权另定S4运行前材料与合同兼容性审查范围，不自动实现或启动。报告入口`docs/reports/URV_S4_prerun_scope_review_20261103_200311/REPORT.md`、PROTOCOL.md（S4-PR-v1）、scope_decision.json；S4-MIP-v1为待采用的后续最小实施提案，不是执行合同。新增仅此报告目录和共享状态/交接第一节，CASE写0。

U_THIN h30/d80/w120/P240/Ly240nm、H70nm、a1e5，P+y/T+x，5/2.5/1.25nm六配置原矩阵不变。静态节点32256/258048/2064384、壁链30528/122496/490752，窗162/648/2592、最大步23232/92928/371712，精确/源码double/模板及独立静态几何相符。上述是预测，不是原生S4几何PASS。

可优先原样复用S1 ELF（SHA5c3836e97c99feab88cd8e41773237f6ff642a10558f151b11e112563382b07b），当前真实build/source/compiler/1392依赖/3链接/15动态库一致；原S3 2632输入及S2 2160输入一致，原S3 seal/provenance只读验证通过且S4_authorized=false，13科学文件在S2/S3字节一致。{v['protected_files_unchanged']}份保护文件本轮未变。旧S2/S3/S1阶段适配/身份/合同均不能直接挪用，须在新S4副本新增精确阶段来源/权限；不修改旧分支/合同。

后续拟最小范围：隔离S4阶段绑定、A/B关闭封存、默认只读控制器和零步入口、R1/R2实际参数和逐帧载荷关联按六配置适配、软件拒绝检查、原规则阶段内网格报告。原C++/ELF/物理/统计路径/common/科学检查器及预测保持。拟18次原生零步+6初态真实读取，均未获本轮执行授权也未执行；同ELF不变无需新编译/机器审计，若漂移则HOLD另审。

资源边界：S4细格2064384核心点，为同格S2的70%；按旧S2实测每步成本和节点比、若跑满371712步，细格P/T条件成本约32.26/32.06h，超过原12h。非收敛耗时预测、非真实S4测速。原1/4/12h（六条求解预算34h）保持候选；零步B后正式绑定前另审资源决策，可明确接受预算风险或另定有限PERF；本轮不测速、不加时、不新增PERF实现。

已有S3四条/两S2中档和两方向控制完整独立通过，前报告`docs/reports/URV_S3_completed_review_20261103_172033/REPORT.md`保持。本轮无新增流场/数值验证、无实际run_id、新CASE/准备A/B/执行release/命令；构建/原生/VTK/PERF/正式计算0。S4 NUMERICAL_GATE=NOT_EVALUATED、geometry_PASS=null、RESULT_PASS=false（未运行）；参考资格false、MODEL_COMPARISON/physical_validation未评价、strict_error_bound_established/submission_ready=false、F04 OPEN_OUT_OF_SCOPE。旧FAIL/380差异、MRP静态FAIL、旧v1 HOLD和作者声明有限范围保持。

下一具体动作：采用S4-MIP-v1最小提案后，隔离实现S4接入与软件检查并交付权限关闭的准备A；当前不自动实施/编译/审计或启动。原生18+6、有限性能和正式六条各依明确覆盖的授权办理，不自动进入S5或解除F04。下一步模型GPT-6.1 Sol｜High。

'''
updates=[]
for name in ['SIM240_AI_CONTEXT.md','AI_HANDOFF_20261015.md']:
    path=ROOT/'docs/reports'/name;before=(OUT/('before_'+name)).read_text();current=path.read_text()
    a=before.find('\n## ');z=before.find('\n## ',a+1);ca=current.find('\n## ')
    assert a>=0 and z>=0 and ca>=0 and before[a:]==current[ca:],'concurrent state section/tail changed'
    updates.append((path,current[:ca+1]+body+before[z+1:]))
protected=load(OUT/'protected_inputs_before.json');assert all(sha(p)==h for p,h in protected.items())
for path,text in updates:path.write_text(text)
save('shared_state_update.json',dict(at=now,paths_sha256={str(path):sha(path) for path,_ in updates},historical_tail_preserved=True))
save('final_verification.json',dict(at=now,protected_files_unchanged=len(protected),CASE_writes=0,native_calls=0,VTK_calls=0,builds=0,
    performance_steps=0,formal_steps=0,execution_release_created=False,launch_command_created=False,review_only=True,
    protocol_written=True,shared_state_updated=True,static_geometry_does_not_grant_native_acceptance=True))
manifest={str(path.relative_to(OUT)):sha(path) for path in OUT.rglob('*') if path.is_file() and path.name!='document_manifest.json'}
save('document_manifest.json',manifest)
print('S4 REVIEW_COMPLETE',len(manifest),'artifacts;',len(protected),'protected files unchanged; no CASE/native/VTK/build writes or calls.')

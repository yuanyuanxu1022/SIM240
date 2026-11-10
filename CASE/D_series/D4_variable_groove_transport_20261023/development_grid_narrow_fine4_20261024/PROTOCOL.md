# 窄槽四项1.25nm最细网格执行与三格接续协议 v1

2026-10-24。用户明确授权准备并审查本批入口、资源和三格比较，不授权AI自动启动正式计算。上游development_grid_mid6_20261024_v1六项已按冻结协议独立验收PASS；该证据及原始哈希纳入本批绑定。老师外部审批不作已确认声明。

## 范围与不变物理

仅stage_cases.csv四项：(h,d,w)nm=(75,25,60)/(75,120,60)，dx1.25nm，P=Ly=120nm、φ=.5，各P沿槽+y/T横槽+x。a1e5、ρ1000、ν1e−6、μ.001、τ1、D3Q19_FORCE/ForcedBGK/Bouzidi/固定充分充液单相均保持。宽槽1.25nm两项、预测及其参考、已完成粗/中格和其余86canonical行拒绝。固定batch_id=development_grid_narrow_fine4_20261024_v1。

原C++、binary、库与原数值协议不改；make --question以及既有source/binary哈希核对后复用已编译程序，不无故重编。准备限describe/precheck零步与已有数据只读回归，不能将其当正式算例或流动精度PASS。正式run_id与key=value配置在launch_configs预存，实际prepare生成后必须逐字节一致。

## 运行与记录

run_narrow4.py默认仅检查，明确--execute才运行；start_from_project.sh自动确定项目根目录，绑定相对路径亦按项目根解析。只允许本机已审查来源；不同机器须重编/预查及新绑定。已存在batch一律拒绝覆盖、续跑或改tag；相同case已存在正式result拒绝重跑。单进程单rank，逐项串行，启动前及逐项前可用RAM≥4GiB、可用磁盘≥11GiB，不把swap当可用RAM。资源/输入/库版本不合则停止，不重试或自动续跑。

保留完整配置、run_id/manifest、源码/binary/库和OpenLB构建来源、原始CSV及完整VTK引用、日志、独立exit、时间/RSS和输入前后哈希。异常或非零exit立即停；不自动验收/比较/拟合/进入宽槽。源RESULT_PASS=false保留，完成仅写independent_acceptance=pending。

## 数值、帧和验收

原冻结门槛原样：质量全程绝对相对漂移<1e−10，密度≤1e−6，Mach<.05，末完整窗口样本std≤1e−6/span≤5e−6/cross≤1e−12m²/s，末双截面≤1e−5，正主通量、有限值、材料保持、几何/q=.5、fallback/unresolved=0。

dt=dx²/(6ν)=2.604166666666667e−13s，窗口Δt*=.75→16200步；最长时间8(h+d)²/ν，d25最大307200步，d120最大1168128步。沿用首个合格窗口即停止；t*=0/.01/.02/.05/.1/.2/.5/1/2/4/8及收敛末态，未达到未来点标记，不延算或补造。

accept_batch.py仅在用户另行要求且整批四项完成后显式调用：分块重算全部完整窗/质量/密度/Mach/J/K/R/截面/几何，逐帧核VTK与CSV、输入与分析exit；通过才出certificate。window_metrics.py与已验收中格助手字节一致，16MiB工作预算、ddof1及首个停止点不变。诊断用数值矩阵，最坏1168129行×20double约178.25MiB，窗口输出等额外线性内存另计；不建立139GiB密集临时数组。reader逐帧，仅保留对应诊断行，最大节点995328，按2KiB/核心节点+1GiB估计2.90GiB，验收前可用RAM也要求≥4GiB；这是预算而非新细格实际峰值保证。

## 来源绑定与三格接续

export_references.py默认接入六项已验收粗格与上游中格certificate，实际形成12行有原始/验收证据绑定的参考。未来必须先对四项最细格独立验收，才能显式用finish_grid_review.py接收其完整certificate；再导出粗6+中6+窄细4=16行。生产比较只接绑定bundle，重核真实原始配置/物性/方法、K/run_id、独立exit、输入/证书哈希，不用手填true代替来源。

compare_grid.py/grid_policy.json从中格阶段逐字节复制，保持预先冻结的可执行v2及1%/0.5%/η=.0001、Decimal精度60阈值、原趋势和条件GCI。每个窄几何分别判KP/KT/A，两个几何六量全过才给narrow_six_quantity_gate=PASS。即便宽槽最细格缺失，窄槽FAIL或INCONCLUSIVE必须在summary和逐量结果显式保留，不被全局INCOMPLETE掩盖。缺项不能PASS；全局仍需三几何九量齐全才能给GRID_SENSITIVITY_TARGET=PASS。本批最多完成两个窄槽三格链，不能说全D4或全参数域网格独立。

中格已观察到窄槽KT的5→2.5nm差约1.59–1.61%，属于已知精度风险。本批用于判断，不预设最细格结果或保证通过；不事后调整标准、删除失败方向、换参考或以细格替换原5nm主模型比较以使公式变准。近乎平坦、非单调/不收缩按原规则分支；p/GCI仅条件诊断，不当真值/严格误差界。dx和dt联动，只支持该扩散缩放路径下的联合离散敏感性。

finish_grid_review只输出结论，不生成宽槽运行许可、不自动运行任何算例。若窄槽六量有FAIL/INCONCLUSIVE，先停下复核；全部通过后也须另审宽槽22GiB可用RAM与多日预算。预测16+4仍关闭；G4 v1锁不改，新增开发数据拟合另立模型v2并在保留结果前重新冻结。比较v2与模型版本不是同一对象。

## 冻结与运行准备停点

release一次性绑定源/binary/库/头文件、上游中格原始及独立验收、当前四项协议/配置/入口/验收/比较程序、零步与回归证据。已存在release拒绝原地重绑，后续变更另立版本。启动日志与运行锁为可变记录排除，科学输入和wrapper均绑定。本目录只说明本机技术准备，不能把命令已交付写成用户已启动或结果完成。

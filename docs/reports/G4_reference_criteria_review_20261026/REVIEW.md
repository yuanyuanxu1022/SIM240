# 连续性、能量及参考预算的终审修订意见

2026-10-26；对象：[上一版最小参考合同](../G4_minimum_reference_contract_20261026/REFERENCE_CONTRACT_DRAFT.md)。本轮为作者明确要求的内部科学审查，不是期刊审稿或运行批准。使用 scientific-writing、peer-review；沿用已记录的作者授权与内部审查接收记录，公开检索仅涉及通用方法，不上传项目材料。

**结论：F01 的指标定义和适用对象、F03 的预算对象及传播关系可以按本修订稿消除歧义。相应指标的实现、数据验收和误差估计的可信性仍待证据；不能把“规则审清楚”写成“参考已合格”。** 推荐条款见 [CRITERIA_REVISION.md](CRITERIA_REVISION.md)，结构化裁定见 [decisions.json](decisions.json)。旧草案、方法合同、源代码、N8原始记录、G4锁及历史FAIL均保留。

|原歧义|本轮裁定|证据/理由|
|---|---|---|
|P2/P1弱连续性是否保证强散度≤1e−6|不保证。弱方程残差、截面一致性和强散度分开；强散度不设统一1e−6硬门槛|实际压力测试函数连续分片一次，速度散度通常是跨单元不连续的一次函数；二者不是同一空间|
|连续性行右端为0，残差除什么|除原无量纲完整系统非零右端范数；保留原周期约束基与行缩放，压力残差只抽取独立物理压力行|不得除0，不得把MPC从属占位行当作连续方程，也不能把每个未合并局部压力矩当成独立约束|
|能量应检查D−W还是D−Pdiv−W|两者均查，另查Pdiv；共同固定分母S=max(D,abs(W))|从实际弱式取测试速度u得到D−Pdiv=W；取测试压力p得到Pdiv=0，两个等式不能靠一次抵消代替|
|是否要求任意位置截面等流量|只对横向向量流问题有该含义；7截面是采样核验，不能称全域最大误差|沿槽标量速度随横槽坐标改变，横槽位置的深度积分不必相同；其沿流向连续性按充分发展假设恒成立|
|MMS是否能用单位体力功|不能；使用实际f·u|实际源码与旧method_contract本已如此规定，本轮澄清而非修复源码|
|∫abs(grad u)²是否等于真实黏性耗散|对精确不可压缩解在本边界条件下积分相等；离散非零散度时须区别2∫ε:ε|本轮推导给出两积分之差等于∫(div u)²；能量代数闭合不独自证明真实耗散精度|
|0.5%、0.12%、0.25%怎样共存|选定逐方向空间估计上限0.12%，GCI须换成目标分母；0.25%仅中细差筛查，旧GCI0.5%/拓扑0.25%候选不作为本修订稿资格门槛|只替代未生效候选条款；不修改任何已运行LBM阈值|
|模型差与停止影响是否属于Stokes参考误差|不属于；另列比较解释层，不计入参考自身预算|严格Stokes稳态有限元没有LBM有限时停止项；NS与Stokes比较涉及不同方程|
|P/T各小于0.5%是否保证A小于0.5%|不保证；A需比值传播，禁止假定抵消|同幅方向界0.5%可给A约1.005%的条件包络|
|小GCI、小ALG/QUAD变化是否给严格界|不给。三格可出条件估计；对照变化是敏感性证据|缺少可靠性证据则保留条件估计或INCONCLUSIVE，不颁发严格界证书|

本轮建议为**逐点Stokes参考估计目标**：P/T各≤0.15%，A≤0.31%。分项采用空间0.12%、代数0.01%、装配积分0.01%、独立提取0.0001%。这是研究设计选择，支持未来3%/5%公式偏差评价时保持较小参考干扰；不是通用标准，不是任何已测误差，也不改变G4原3%/5%评分规则。各分项的可靠性是独立必要条件。

所有分项若真的构成所声明比值的误差界，乘法传播给每方向约0.14013%、A约0.28064%的条件包络；0.15%/0.31%是预留小余量的验收设计，不是已实现精度。精确预算算术见 [budget_arithmetic.json](budget_arithmetic.json)。沿用旧空间/ALG/QUAD数字并单列提取层，避免漏记后处理；不得把软件控制阈值误当后处理已获严格误差界。

**当前参考资格仍为未取得。** 矩形MMS/平板只能核方法实现，不能取代沟槽角点自身精度。仅三格且无独立可靠性支持时，最高报告“按指定模型得到的条件空间误差估计”；若要论文宣称总误差有严格上界，还需要经证明可靠的后验估计/目标量包围等更强证据。此处没有批准这些追加工作。

本轮只新增本目录并更新项目状态/交接，静态验证只作文件哈希、JSON/公式预算算术和文档一致性检查；没有读取场数组、重新积分已有场、运行提取器、建网、组装、求解、拟合或修改执行许可。现有N8证书仍仅为ONE_N8_DIAGNOSTIC_ACCEPTED；NUMERICAL_GATE=NOT_EVALUATED、RESULT_PASS=false、geometry_PASS=null、reference_qualified=false、submission_ready=false、预测HOLD。

下一动作是依据修订稿准备独立提取器及合成夹具、确定浮点/积分误差控制实现，再在另一个明确范围的任务中处理现存N8；无需重跑N8。F02实施核验、F04其他问题支持、F05逐项资源许可仍未闭合；F06对比对象已界定为Stokes，NS/停止及域推广证据未取得。

## 来源与责任边界

- 本地实际弱式：`CASE/D_series/D4_variable_groove_transport_20261023/reference_backend_min18_20261025/src/symbolic_forms.py`第15–20行；实际调用：`pilot_record_v3_1_20261026/assembly.py`第46–61行。本轮未执行这些模块。冻结与旧候选来源的SHA见 [source_manifest.json](source_manifest.json)。
- [Lederer等：Divergence-free Reconstruction Operators for Pressure-Robust Stokes Discretizations With Continuous Pressure Finite Elements](https://arxiv.org/abs/1609.03701)：支持经典Taylor–Hood离散无散与严格无散的区分。本轮没有采用文中的重构算法。
- [DOLFINx Stokes示例](https://docs.fenicsproject.org/dolfinx/main/python/demos/demo_stokes.html)：P2/P1实现背景。网页提示压力符号与通常定义不同；本项目符号以本地强式/弱式为准，不复制演示符号。
- [NASA网格收敛说明](https://www.grc.nasa.gov/www/wind/valid/tutorial/spatconv.html)：Richardson/GCI依赖渐近收敛条件；不支持将本项目任何候选分项当作已证明界。
- 软件辅助方法：Kassis, T., Agarwal, V., He, Y., Patel, D., & Brueckner, A. M. (2026). *Scientific Agent Skills: A Library of Procedural Knowledge for Research Agents*. [arXiv:2609.00065](https://arxiv.org/abs/2609.00065)，本轮核对当前v2；不作为CFD物理证据。

本文是AI辅助的终审意见及推荐修订文本；最终科学采用由作者负责，未代签作者批准，未声称切换模型或另有人/代理独立复审。

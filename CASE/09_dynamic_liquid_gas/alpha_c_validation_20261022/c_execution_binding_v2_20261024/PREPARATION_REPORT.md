# C 独立执行与验收绑定实施核查

2026-10-24。用户授权仅实施独立绑定、保持物理输入/判据、不启动计算。本轮任务完成于准备阶段。

**已实现并核查：新运行端和验收端通过同一份来源绑定；旧物理程序、数值判据、父绑定和alpha证据保持。没有调用OpenLB、没有新编译、没有正式C批次或物理结果。**

## 1. 具体实现

新目录：`CASE/09_dynamic_liquid_gas/alpha_c_validation_20261022/c_execution_binding_v2_20261024/`。

| 文件 | 功能与范围 |
|---|---|
| binding.py | 两端共用的来源核对；严格核父输入、唯一管理规则兼容、历史alpha依赖和新执行文件集合 |
| compatibility.json | 精确记录旧/新AGENTS哈希和已审查diff；不允许其他文件变化或通配忽略 |
| physical_contract.json | 从旧protocol逐字段继承C四组/后端/物性/输出/完整阈值，核对等同 |
| execution_binding.json | 新冻结记录；保留父绑定SHA和alpha依赖，绑定3808项当前文件 |
| run_c.py | 新批次运行入口；默认只读预查，显式--run才可能调用旧二进制；锁、独立退出码、失败停止、前后哈希 |
| analyze_completed_c.py | 新批次完成验收入口；核同一绑定、完成证据和原始输入哈希，再调用旧analyze_c.py |
| PROTOCOL_ADDENDUM.md | 只改变执行来源口径的附录；不重新定义物理方程或阈值 |
| test_binding.py | 23项来源与控制流检查，负向变化在内存或临时fixture中完成 |

执行ID为 `C_BINDING_COMPAT_20261024_v2`，预留batch_id为 `alpha_c_20261024_binding_v2_c`。这只是固定的新命名，**尚无对应运行**。新批次的原始数据和证据只写本新目录，不混入旧alpha/旧C路径。当前没有交付启动命令。

## 2. 保持不变的证据

父物理协议 `ALPHA_C_DIAGNOSTICS_20261022_v1`、原protocol.json/PROTOCOL.md、C++源码、已编译二进制、共享OpenLB后端及原analyze_c.py均保持原字节。新Python层复用原二进制和分析函数，**未重编，不声称新的编译验证**。

四组仍为 equal/target × mu0/constitutive；64³/64步；alpha=1、tau_CH=1；NS tau端点[1,1.25]；原物性、初场、源项启动、每步16字段及首步分布三阶段不变。物理Q/质量预算均为1e-9，实现残差1e-12，安全条件及其余所有原阈值都按完整旧字典继承，不能由新CLI改值。

| 关键文件 | 本轮核对SHA-256 |
|---|---|
| 父build_binding.json | `a3409a57013cf537b969547075fe245c0012cac4185830406d4c616670ccba9a` |
| 原alpha canonical verdict | `018467d378507ce4b90f467d39acb3e00cd5748c2b328173e3780db6520fdfa9` |
| 原C源码coupled_check.cpp | `03e0afec24598f54534bd1595b07aec0e7d8abe86dbe87868b82aef2ec1b3354` |
| 原C二进制 | `c4501c49716f96dd88acf09e7e0f62018fdd1a0b2b52c36d8667b89854bb9fec` |
| 原数值分析analyze_c.py | `6eee03ae29a21559b50115ef22c1c13ca620739658e7ee5f4f849741070367fe` |
| 新execution_binding.json | `61b1bd4fff26a0fcd0e6e0c4601d3182b15148ea8955b69d1ceb3874f50fb4ae` |

新绑定3808项是合并去重后的执行输入集合，不与原3401或alpha391相加解释。旧3401项目前仍仅有AGENTS这一项与历史值不同；新层明确接受已审查的5700b378…→59d1cc51…，而非改写旧记录。旧AGENTS重建文本及精确diff与两个版本互核，任何未来新变化仍拒绝。

alpha canonical verdict、EXPORT_PROVENANCE、原批次manifest、全部391项验收输入、批次独立exit均在依赖中核对，另复核原392份运行文件。原JSON输出失败exit2和限定布尔适配exit0保留，旧alpha的算子合同范围不扩大。无需重复运行alpha。

## 3. 实际检查结果

检查记录见 `preparation_evidence/preparation_verification.json`、各独立exit文件和日志。

| 检查 | 实际结果 | 能说明什么 |
|---|---|---|
| 新执行绑定建立与回读 | exit0，3808项匹配 | 绑定来源结构及当前文件一致 |
| 新run_c默认预查 | exit0 | 来源及原12GiB磁盘条件满足；未创建正式目录、未调用程序 |
| 新验收--check-inputs | exit0 | 验收端使用同一绑定；不判断C完成 |
| 缺少正式完成证据时调用完成验收 | 预期exit2，没有创建分析结果目录 | 不把“入口就绪”写成结果通过 |
| test_binding.py | **23项通过，独立exit0** | 正反向来源/完成证据/控制流检查通过 |
| 合成元数据端到端验收分支 | 测试脚本exit0；其中模拟的物理预算失败使验收返回1 | 来源串接、旧阈值传递、失败不豁免、Gate不提升 |
| 原run_suite默认C预查 | 仍为预期exit2：AGENTS不匹配 | 原入口/旧绑定未被修改或放宽 |

23项检查覆盖：源码、二进制、参数、alpha原始history、alpha verdict、父绑定、当前AGENTS、新分析脚本、物理合同声明及alpha导出来源变化的拒绝；缺失绑定项拒绝；默认运行/验收入口不调用程序或创建正式目录；无完成数据拒绝；完整合成来源结构的正向检查及批次ID、子退出码、缺帧、零步、manifest绑定不符的拒绝；原数值加载器拒绝合成假数据；物理预算失败不豁免；假进程第二项退出9后停止且保留失败记录。

端到端测试文件 `preparation_evidence/end_to_end_acceptance_test.py` **显式用数值回调替身**，只检查完整来源串接到结果汇总/序列化的路径。四组顺序和传入阈值与原协议相同，其中一组物理预算设false，必须写出complete_C_contract_pass=false并返回1。所有文件在临时目录中，结束后删除。这不是实际C数值结果，不是完整耦合验证，也不是原数值分析器对真实C数据的正向验收。

## 4. 运行与验收如何衔接

未来明确启动时，运行端保存新绑定全文及其SHA、父物理协议ID、alpha历史依赖、四组参数、原程序绝对命令和原工作目录；逐项记录独立exit，非零停止；每项前及批次结束重核输入，禁止覆盖/恢复/自动分析/下一阶段。

以后完成验收首先要求同一binding、匹配的新batch_id、总及四组独立exit0、子/总manifest一致、配置步数完整、65帧和首步三阶段分布齐备；原数值分析函数继续检查全程场、化学势、源项、相量/质量、动量、能量与安全条件。原始文件在分析读取前后核对集合及SHA，输出序列化完成后才创建新的分析目录。

物理预算与实现余额分列，不能因为源项解释得通就转成守恒PASS。当前首步预测仍是两个本构组相量−2.36935e-9/+8.29233e-9、目标组质量−8.27245e-9，预计超过1e-9；本轮没有重新推进或改变这项预测。

## 5. 当前停点与限制

```text
执行与验收绑定：已实现、已冻结、只读预查通过
实际C运行：未启动
实际C完成验收：NOT_EVALUATED
NUMERICAL_GATE: NOT_EVALUATED
RESULT_PASS: NOT_EVALUATED
geometry_PASS: NOT_EVALUATED
```

无新OpenLB run_id、初始化/碰撞/迁移、编译、物理Gate升级或Git提交/推送。正式推进耗时与峰值RSS仍未知，当前磁盘预查不是资源预留。新层仅在本机当前绝对路径验证，跨机器搬迁未验证。未来实际数值完成验收只能在用户运行后进行，不用本轮fixture替代。

用户下一次若要求运行准备，再按本新版本复核输入与资源并单独交付启动入口；本轮不启动、不交付长算命令，不自动进入C细格/alpha16/D/静滴/润湿/K。

项目SIM240_AI_CONTEXT与最新AI_HANDOFF已同步，第一篇并行内容保留。最终原文件保护和来源核查见 `preparation_evidence/final_integrity.json`；准备实现文件加入新冻结输入，准备报告/测试日志/共享入口不循环加入自身绑定。

工具来源：本轮使用scientific-writing组织附录及证据报告。Kassis T, Agarwal V, He Y, Patel D, Brueckner AM (2026), *Scientific Agent Skills: A Library of Procedural Knowledge for Research Agents*, [arXiv:2609.00065](https://arxiv.org/abs/2609.00065)，2026-10-24核当前v2。仅为工具出处，非本项目物理验证依据；元数据记录在preparation_evidence/scientific_writing_reference.json。

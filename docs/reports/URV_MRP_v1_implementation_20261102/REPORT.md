# URV-MRP-v1 隔离实现、构建与指令审计

2026-11-02。**隔离候选已实现、实际构建成功，103 项软件测试最终通过；静态指令审计发现体积观察量伴随变化，按用户指定的 GPT-6 Astra｜High 裁定，`SOURCE_REVISION_AUDIT=FAIL`、候选及 S0 保持 HOLD。当前不具备运行交付资格。**

本轮没有调用 OpenLB 原生程序的 describe/precheck/initialize/steady，没有新增流场时间步、正式 run_id、启动合同或命令。新运行的数值／几何／结果状态仍为 NOT_EVALUATED；不能把本次静态 FAIL 写成尚未运行案例的数值 FAIL。

## 1. 授权范围、交付位置与原始保护

用户要求按 URV-MRP-v1 隔离实现最小修复与密度捕获，完成构建、软件检查和指令审计；正式运行另授权，遇指令／证据矛盾由 GPT-6 Astra｜High 裁定。本轮按这项准备授权实施。原生零步需要明确授权，本轮未执行；没有沿用旧两条 S0 启动合同来授权新版本。

- native 候选：`CASE/unseen_v2_reference_S0_mrp_v1/`。
- checker 候选：`CASE/unseen_v2_reference_checker_mrp_v1/`。
- 原协议：`docs/reports/URV_S0_mass_repair_protocol_20261101/PROTOCOL.md`，未修改。
- 本轮授权解释和范围：authorization_scope.json。
- 原有文件保护：protected_inputs_before.json，1751 份既有源码／程序／规则／原始数据／报告文件前后哈希一致；共享状态和交接按项目规则另作更新及 diff。

## 2. 实现了什么

native 主文件仅增加观察量头文件、局部质量 helper 调用、同次 rho 捕获参数与调用、初态／逐步／末态记录。已做可逆最小 diff 核对：去除这些明确列出的编辑后，主文件完整恢复原 v1.2 字节。原 Makefile 和 mass_stats.h 字节保持，未全局改浮点优化、物理参数、碰撞、边界、力、速度、收敛规则或门槛。

`mrp_observer.h:legacyMass` 使用三个局部 volatile double 舍入屏障，最后显式 std::fma。每次测量仍从 +0 空间累加，不能跨时间累积或重排。header 中无 OpenLB 类型或 lattice 访问。

密度采集在原 computeRho 后复制同一个 rho，并按 cuboid/x/y/z 顺序记录坐标、57600 个无损 double、phase、step/time、常量和原生账本位模式及浮点控制。每次遍历检查坐标与初次映射一致；初态分母和诊断 step0 分开；保存计划包括 T190差异步+10控制步、P10控制步及两次初态，预期共212份。保留最近测量缓冲，以便实际末步同输入落盘，不为补采样延算。

SHA 索引分两阶段：native 以受检 I/O 写 rho、坐标与 raw JSON；独立 Python finalizer 只核验与补充实际文件 SHA，生成最终 rho_capture_index.json，未来运行器必须在 completion 前绑定全部文件。finalizer 不重算密度或修补错误数据。当前未接入正式执行运行器，因为指令审计失败；不存在可直接复制启动的包。

独立重放实现不调用 native helper 或 OpenLB：分别重放融合／分开乘加，Neumaier 物理质量和 rho−1 账本，保存空间前缀差异、初态分母及新／旧／v1.2逐点对照。补证完成结果 CLI 会先调用原字节 URV 检查器重新验收原始材料，不信任外来声称 PASS 的文件；原规则不通过时不能由补证替代通过。

新源码来源接入只增加精确修订分支：原 anchor 保留，新源 SHA、最小 diff、原 seal 和原协议绑定。来源字节匹配只说明程序身份；另有 `instruction_audit_status` 守卫，当前 FAIL 会拒绝该候选用于正式来源放行。check_results.py、evidence.py、read_fields.py 及 common/ 的13份数值／规则文件原字节保持。旧R1/R2及F02先保存差异后拒绝保持，F04仍范围外。

## 3. 实际构建和软件检查

真实 native 构建命令、退出、编译器、OpenLB 版本、源码、编译器依赖文件、静态／动态库与 ELF 绑定存于 native/evidence/build_environment.json、build.log、ldd.txt。不是 make dry-run，构建脚本没有调用 native。

当前 ELF SHA256：

```text
6f83f1482473b6bd99f28b353c060282f031b2c394c2f4417196a8f40bd995ec
```

编译器 SHA 与原 v1.2 相同；三项原静态库哈希相同，原 Makefile 未改。它们是当前闭包核对，不能填补最早旧 D4 构建记录的历史缺口。

最终软件检查为原77项加新增26项，共 **103 项通过**，见 software_tests_final.log。覆盖独立精确有理数 FMA 反例、C++ helper 对 Python 重放、多单元顺序、无 OpenLB 合成密度采集、初态／step0分离、完整核心映射与错序拒绝、采样缺失／重复／dtype／SHA／时间／环境／非有限密度拒绝、原 anchor 保留、精确新源与 diff 篡改拒绝，以及静态审计 FAIL 明确阻断真实候选来源绑定。

软件测试通过 ctypes 执行了一个独立 C++ 合成夹具 shared object，只含观察量和人工 rho=1 数据，不链接 OpenLB、不创建格子、不调用流场程序。此类 C++ 软件算术执行如实记录于 software_fixture_build.json，不能说成“完全没有执行任何 C++”，也不能当作真实零步安装或正式密度采集证据。

初始软件失败完整保留：software_tests_initial.log 中测试夹具变量误用了 unittest 的 run 方法名，导致测试中断；software_tests.log 中一个旧负例被新来源分支过早报错，原应保留的错误语义未匹配。随后只改测试变量名与新分支缺少显式修订声明时的拒绝顺序，旧断言不放宽；software_tests_retry.log 的101项通过。加入两项必要守卫后，最终103项通过。没有借这些软件修复重构或重新编译 native 候选。

这些检查尚不覆盖真实流场端到端验收、实际调用环境下的密度 I/O耗时、所有捕获故障路径或所有传递依赖的机器等价；没有新运行材料可证明物理结果未变。

## 4. 指令审计结果与分支对应

完整反汇编 new_disassembly.txt，measure 主函数 new_measure.txt，helper 片段 legacy_mass_helper_disassembly.txt。instruction_audit.json 记录实际 ELF SHA、常量读取、地址、状态及限制。

质量 helper 在 0x308c4、0x308d4、0x308e4 分别作 VMULSD，并通过 double 存储／读取固定三个舍入点；0x308f4 VFMADD132SD 完成最后一次融合乘加。该局部路径符合质量目标，也由独立软件算术交叉核对。

**失败点是 volume：**v1.2 的 volume 通道是先 VMULPD 后 VADDPD；当前变成 VFMADD213SD，最后乘法不再单独舍入。固定 dx 下57600项最终体积相同，196个空间前缀不同，首次 ordinal=15、1ULP，见 volume_arithmetic_guard.json。不能因为末值恰好一致就通过“非质量运算保持”审计。

| 运行中的测量调用 | 实际主干 | 关键地址 |
|---|---|---|
| initial_reference、逐步 diagnostic；P/T 均可 | capture非空 | 42116 append；421cd volume FMA；421fa mass helper |
| 循环后 final；P/T 均可 | capture为空 | 4288f volume FMA；428bd mass helper |
| P/T方向分支 | 仅选截面索引，再进共同入口 | 41e88/41ebd→425e8→42613；capture分界实际在41f0a/41f25 |

已核对的正常有限值局部路径中，速度模长、压力、densityIntegral、三个速度积分、两截面与补偿 term 未再确认其他舍入语义改变；Neumaier 两补偿分支亦列入局部检查。归一化输入 volume 已改变，不能据原表达式推定其输出普遍相同。初态分母、质量误差减法后除法、停止条件的源码保持；全部被调用内核／冷分支及完整调用者未完成全量机器等价证明。这些限制和逐项状态均在 instruction_audit.json，不把局部匹配写成全程序 PASS。

## 5. 依用户条件实际调用 Astra 裁定

因上述矛盾，实际调用 GPT-6 Astra｜High 子任务只读审查协议、源码与反汇编；未更改当前模型配置或任何既有科学材料。其裁定与分支标签更正记录于 [ASTRA_RULING.md](ASTRA_RULING.md)。

裁定为当前 `SOURCE_REVISION_AUDIT=FAIL`，保留候选，完成其余只读审计后停止；不在本轮直接增改 volume 并重新构建。建议的技术目标是给单项 volume 固定原舍入点，但这项源码改变需由具体附属修订覆盖，不能静默扩大原协议允许集。

已交付可审阅的 [VOLUME_ADDENDUM_DRAFT.md](VOLUME_ADDENDUM_DRAFT.md) 和 [proposed_volume_rounding.patch](proposed_volume_rounding.patch)，状态 NOT_ADOPTED_NOT_APPLIED。补丁仅增加局部 roundedCellVolume 的 binary64 舍入存储，再单独相加；没有应用、编译或运行。后续即使采用也需新候选、新绑定和实际指令审计，不能靠 volatile 字样判通过。

## 6. 当前裁定和下一停点

| 项目 | 本轮真实状态 |
|---|---|
| 隔离源码／实际构建 | 已完成；构建退出0 |
| 软件测试 | 最终103项通过；早期失败保留 |
| 质量 helper 局部路径 | 符合所需运算 |
| SOURCE_REVISION_AUDIT | **FAIL**：volume伴随融合 |
| 原生describe/precheck/initialize／正式计算 | 未执行 |
| 新URV_NUMERICAL_GATE／geometry_PASS／URV_RESULT_PASS | **NOT_EVALUATED** |
| S0、候选运行交付 | **HOLD**，不可发启动命令 |
| 历史P／T | 原P接受、原T拒绝，记录不改 |
| 历史190点唯一归因 | NOT_ESTABLISHED |
| S1／模型评分／物理验证 | 未启动／NOT_EVALUATED |

下一具体动作是先审定上述体积附属修订，决定是否允许在另一新候选中增加这一项舍入屏障；当前不自动继续修改、构建、原生零步或正式计算。原24项研究计划、外部历史声明范围、V2参数和全部门槛不变；本轮没有增加参考网格或未见条件结果。

`reference_qualified=false`、`strict_error_bound_established=false`、`submission_ready=false`；旧细T FAIL、C/h75限定资格、V2/G4锁、D4预测 HOLD、GDI01及原准备/v1.1/v1.2封存保持。无提交推送或对外发送项目材料。

本轮使用 scientific-writing 组织报告和限制，沿用原协议记录的 [Scientific Agent Skills 来源](https://doi.org/10.48550/arXiv.2609.00065)；AI帮助不替代作者与导师负责的科学审查。工程代码／静态审计证据在本地，未以公开网络发送项目材料。

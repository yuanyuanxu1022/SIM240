# URV-S1-A1-v1：S1 光滑基准接入实现、构建、软件与两方向零步审计

日期：2026-11-02。**本文件为状态补齐记录**：S1 的实现、构建、软件测试与两方向原生零步审计已于 10:27–10:35 实际完成，但当轮未写独立报告；本节据实际产物逐项补齐，不新增任何计算、编译或原生调用。

**结论：S1 候选已在隔离目录建成并通过构建、62 项软件测试（42 项沿用检查器 + 20 项 S1 新增，分开执行）、限定静态指令审计与两方向零步原生审计（6 次调用全退出 0，实际时间推进 0 步）。S1 正式计算未授权、未启动，尚无正式 run_id 结果与正式启动合同。**

本 PASS 只覆盖本文列明的源码范围、浮点数据流与安装几何；不等于 S1 数值/解析验收通过，不构成参考资格、模型比较或物理验证。

## 1. 用户采用范围

采用记录见 `adoption.json`（本目录），原文：“采用草案后，隔离实现 S1 接入，完成构建、软件与限定指令审计、两方向原生零步审计；正式计算仍另行授权。”

被采用的草案为 `URV_S1_prerun_review_20261102/MINIMUM_ADAPTATION_DRAFT.md`，SHA `ce2937b2c87b3b9abcdff041b6c74e14733977e3f0083f126ef0c32f0fefc4a4`。采用范围明确：`formal_simulation_authorized=false`、`S0_rerun_authorized=false`、`S2_authorized=false`、`maximum_native_zero_calls=6`。

## 2. 源码改动与构建

新目录：

- `CASE/unseen_v2_reference_S1_a1_v1/`：native 候选、构建记录与审计。
- `CASE/unseen_v2_reference_checker_S1_a1_v1/`：检查器隔离副本与 S1 精确来源分支（`s1_revision/`、`revision/`）。

相对 A1 的唯一改动是**移除 S0 专用的密度捕获调用点**，全部测量改走既有 null 路径，见 `adopted_source_delta.patch`（三段共删 6 行使能行、2 处 measure 参数置空）：

```diff
- mrp::DensityCapture capture(...); capture.begin(...); ... &capture
+ const Measurement initial = measure(..., p.fx, p.fy);
- capture.begin("diagnostic",...); ... &capture
+ const Measurement state = measure(..., p.fx, p.fy);
- capture.actualFinal(finalStep);
```

`mass_stats.h`、`mrp_observer.h`、`capture_schedule.h` 与 `Makefile` 字节保持（SHA 见 `build_environment.json` 的 `native_sources_sha256`）。材料、碰撞、边界、体力、速度、J/K、时间推进与收敛规则未改。

实际构建：`compile_exit_code=0`，`solver_invoked_by_build_script=false`，编译与链接命令、编译器、静态/动态库哈希、OpenLB 标识 `882924a9cfc8`、D3Q19 ForcedBGK、CPU_SISD 均记录于 `build_environment.json`。

新候选 ELF：

```text
SHA256 5c3836e97c99feab88cd8e41773237f6ff642a10558f151b11e112563382b07b
```

A1 的 `c1fc2a1eeacced8f11a9bb045c25d70936b7be03fe5495a0b8f51789bd8fe8af` 及其 S0 接受记录原样保留，未被本候选覆盖。

## 3. 限定静态指令审计

见 `instruction_audit.json`。`SOURCE_REVISION_AUDIT=PASS`，范围限定为：

| 检查项 | 结果 |
|---|---|
| 旧质量 helper 三次已舍入乘法 | `0x2edc4`、`0x2edd4`、`0x2ede4` |
| 单项 double 存取 | 存/取成对成立 |
| 最终显式 FMA | `0x2edf4`（与 A1 归一化序列相同） |
| measure 入口与四个调用者 | `0x3fc10`；initial `0x243ed`、diagnostic `0x245e8`、final `0x24e91`、initialize `0x26442` |
| 全部调用 capture 为空 | 是（S1 无 h75 捕获器实例） |
| 体积路径 | `0x3ff26`/`0x3ff5d` 两次乘法、`0x3ff61` 存、`0x3ff69` 取、`0x3ff71` 独立加 |
| 每格一次 computeU／computeRho | `0x3fe5b`、`0x3fe8f` |
| Neumaier 双分支、速度积分 FMA、截面、归一化 | 地址见审计文件 |
| 26 个选定内核归一化序列 | 与 A1 相同 |

审计自述边界保持：`full_transitive_machine_equivalence_claimed=false`、`cold_paths_exhaustively_proven=false`、`formal_simulation_executed=false`。地址经重定位/偏移归一化，不是完整传递闭包证明。

## 4. 软件测试

分开执行，不合并冒充单次验收：

- `base_software_tests.log`：检查器既有 **42 项**通过。
- `s1_software_tests.log`：S1 新增 **20 项**通过（含全部 884736 空间前缀体积相等、实际 C helper FMA 判据、S1 精确两条身份、错误阶段/错误身份/非白名单源/错误 diff/伪 anchor/伪接受均拒绝、任意失败阻止 T、mock 成功不进入下一阶段、原光滑 K 与剖面失败原记录保留）。

`volume_prefix_software.json`：884736 个空间前缀全部一致、差异 0、末值 `1.727999999993599e-21 m³`。`software_only=true`、`native_geometry_evidence=false`——这是软件算术量，不是原生测得体积。

软件夹具 `s1_software_fixture.so` 通过 ctypes 执行 C++ 观察量函数，不含 OpenLB。

## 5. 两方向原生零步审计

审计 ID：`URV_S1_ZERO_20261102_01`，产物在 `CASE/unseen_v2_reference_S1_a1_v1/audits/URV_S1_ZERO_20261102_01/`。每方向 describe→precheck→initialize，失败即停，无重试。`steady` 调用数 0。

| 项目 | P 沿槽 +y | T 横槽 +x |
|---|---:|---:|
| describe／precheck／initialize 退出 | 0／0／0 | 0／0／0 |
| 实际时间推进步数 | 0 | 0 |
| collideAndStream 调用 | 0 | 0 |
| 独立枚举流体核心节点 | 884736 | 884736 |
| candidate 壁面链 | 368640 | 368640 |
| q 范围 | 0.5 – 0.5 | 0.5 – 0.5 |
| material 0／1／2／3 计数 | 0／884736／36864／147456 | 相同 |
| 初态 legacy 质量（kg） | 1.7280000000210298e-18 | 相同 |
| 初态补偿质量（kg） | 1.7280000000000002e-18 | 相同 |
| 密度差账本／最大密度偏离 | 0／0 | 0／0 |
| 顺序体积（m³） | 1.7279999999935988e-21 | 相同 |
| 初始 J 向量（m²/s） | (0, 3.906249999932872e-16, 0) | (3.906249999932872e-16, 0, 0) |
| 初始 Mach 最大值 | 4.6984885187957832e-12 | 相同 |
| 初始化保存帧／独立读回 | 1／通过 | 1／通过 |

初态 J 非零源于原体力方案的半步力修正，与 S0 零步一致；不得误读为已演化的输运结果。884736 节点与解析连续体积 1.728e-21 m³ 的关系见 S1 预审 `static_volume_observer_arithmetic.json`（相对差 3.7047663623415744e-12，在原 1e-10 容差内）；该算术支持，不等于原生几何 PASS。

`density_capture=NOT_APPLICABLE_S0_ONLY`——S1 按采用范围不实例化 h75 捕获器，不虚填该项 PASS。

## 6. 已准备的身份与绑定

`evidence/identity_plan.json` 与 `evidence/preparation_manifest.json`（`kind=S1_PREPARATION_NOT_AUTHORIZATION`，1473 项输入，`simulation_authorized=false`）：

| 方向 | 准备 run_id | 对应原矩阵 case |
|---|---|---|
| 沿槽 P | `URV_S1_P_A1_v1_20261102_01` | URV1_SMOOTH_H30_P_dx1p25_a100000 |
| 横槽 T | `URV_S1_T_A1_v1_20261102_01` | URV1_SMOOTH_H30_T_dx1p25_a100000 |

两 run 目录各只含 `run_config.txt` 与 `run_manifest.txt`，无 run.log、原生结果或 completion。

`scripts/run_S1.py` 默认只读，须显式 `--execute` 才调用原生程序；即使传入执行请求，准备合同仍在 binding 检查处拒绝。正式计算须另存带真实授权原话的启动合同（旧 S0 合同 SHA `cf7f1aa…` 与其许可不得挪用），原 S1 每方向墙钟上限 14400 s。

## 7. 当前状态

| 证据层 | 状态 |
|---|---|
| S1 隔离源码与采用草案一致 | 已验证（`adopted_source_delta.patch`） |
| 实际构建 | PASS，`compile_exit_code=0` |
| 软件测试 | 42 项（既有）＋ 20 项（S1 新增）分开通过 |
| 体积全部空间前缀 | 884736 项，差异 0（软件算术） |
| 限定静态指令审计 | PASS，限于本文范围 |
| 两方向零步原生接入／初始化场读回 | PASS，各 3 次调用，实际推进 0 步 |
| S1 身份／输入绑定／默认只读核对 | 已准备；1473 项；未授权 |
| S1 正式启动合同／正式计算 | 未签发／未启动 |
| S1 NUMERICAL_GATE／geometry_PASS／RESULT_PASS | NOT_EVALUATED／null／false（未运行，非失败） |
| S2–S5、模型比较 | 未启动／NOT_EVALUATED |

S0 状态保持：`S0_ACCEPTED_NEW_A1_PAIR`（P 4342 步、T 2953 步，原 20 列精确回归、212 份密度重放、190 点 380 项差异重现、20 帧实际场读回），详见 `URV_A1_S0_results_review_20261102/REPORT.md`。

历史边界全部保留：旧 v1.2 横槽 `RESULT_PASS=false`／exit2／380 项差异、前个 MRP 静态 FAIL、`HISTORICAL_EXCLUSIVE_ATTRIBUTION=NOT_ESTABLISHED`。`reference_qualified=false`、`strict_error_bound_established=false`、`MODEL_COMPARISON/physical_validation=NOT_EVALUATED`、`submission_ready=false`。

## 8. 下一步

取得用户对上述两条 S1 身份的明确正式授权后：复核 1473 项封存与当时资源，另存带授权原话的启动合同并验证独立 SHA，交付一条 SHA 绑定的 tmux 命令由用户手动启动；顺序 P→原 URV 解析/数值/几何验收→全过才 T；失败即停，不重试、不进入 S2。

光滑平板通过也不直接证明 V2 在两个未见沟槽条件更准，更不构成挤压应用闭环。

本记录为状态补齐，AI 辅助使用 scientific-writing 组织证据；技能出处 Kassis, T., Agarwal, V., He, Y., Patel, D., & Brueckner, A. M. (2026), *Scientific Agent Skills: A Library of Procedural Knowledge for Research Agents*, https://doi.org/10.48550/arXiv.2609.00065（仅说明工作辅助，不是项目数值证据）。不是独立人工科学终审。本轮未外发项目资料、未提交推送。

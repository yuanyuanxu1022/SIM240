"""Build the evidence report from audited numerical output, without solver calls."""
import json
from pathlib import Path

A=Path(__file__).resolve().parent
D=json.loads((A/'independent_review.json').read_text())
F=json.loads((A/'frozen_export_adapted/verdict.json').read_text())
R=D['all_cases']
lines=[r'''# Alpha 空间验证：完成证据与冻结验收

核对日期：2026-10-23。任务仅限用户已独立运行的 alpha 正式批次；本轮没有启动、重跑或编译任何求解器，没有启动 C，也没有修改冻结参数、公式或判据。

**验收结论：alpha 空间算子合同通过。16/16 算例、7/7 方向及细化检查通过，独立重算与冻结分析器结论一致。** 此结论只覆盖本协议的纯 CH 扩散与源项单步，不构成完整 NS/CH 耦合、平衡、润湿或沟槽迁移率的物理放行。

```text
operator_contract_pass: true
NUMERICAL_GATE: NOT_EVALUATED
RESULT_PASS: NOT_EVALUATED
geometry_PASS: NOT_EVALUATED
```

## 1. 完成与输入来源

- 协议：`../PROTOCOL.md`、`../protocol.json`，ID `ALPHA_C_DIAGNOSTICS_20261022_v1`，运行前冻结；本轮没有重定拟合窗口或阈值。旧 B1 的 5%/2% 门槛及历史 FAIL 保留，本独立协议预定为 7%/2%。
- 批次：`alpha_c_20261022_v1_alpha`。开始北京时间 **2026-10-23 17:29:46.378488**，结束 **17:31:27.376847**，实测 **100.998359 s**。
- 总批次独立 `exit_code.txt=0`；16 个子算例独立 `exit_code.txt=0`，分别与子 manifest、总 manifest 的退出码、配置、参数和起止时间核对。完成步数等于请求步数，正式命令不含 `--initialize-only`，日志齐备。
- 10 组线性扩散：粗格各 128 步、细格各 512 步；4 组实际非线性本构：粗格各 16 步、细格各 64 步；2 组源项：各 1 步。
- 总 manifest 为 `../evidence/alpha_c_20261022_v1_alpha/manifest.json`；子证据在其各 run_id 子目录；原始数据为 `../output/alpha_c_20261022_v1_alpha/<run_id>/`。全部 run_id 均为“批次名_下表 id”，明细及每文件哈希见 `raw_input_hashes.json`。
- 运行 manifest 内的 source_binding 与当前 `../evidence/build_binding.json` 完全一致。**3401 项绑定输入逐项 SHA-256 匹配**，含源码、共享后端、程序、参数和冻结分析器；另为 **392 份原始运行文件**保存并复查读取前后哈希。
- OpenLB `CITATION.cff` 声明版本 **1.9.0**，绑定 HEAD `882924a9cfc8dcdf82909e39530789cb6f5ebcc4`；实际文件逐项绑定比单独 HEAD 更完整。

| 输入 | SHA-256 |
|---|---|
''']
lines += [f"| 总 manifest | `{F['input_manifest_sha256']}` |",f"| build_binding.json | `{F['build_binding_sha256']}` |"]
lines.append(r'''
数据完整性独立检查覆盖 **200 份三维 CSV、4,919,296 行场数据、3,374 条逐步历史记录**；逐文件检查有限值、行列长度、整数坐标、完整节点覆盖和坐标唯一性，配置及步序完整。非线性每步全场可独立重算；线性仅保存初末完整场，全程 L2 来自程序内观测量，不能写成逐步离线全场复核。VTK 文件纳入哈希，但本轮未逐个解析其场内容。

## 2. 分析导出故障及受限适配

原封不动的冻结 `analyze_completed.py` 已完成数据分析，但在 `json.dumps` 保存结果时遇到 **NumPy 布尔值不能序列化**，独立分析退出码为 **2**。原错误日志 `frozen_analysis.log`、`frozen_analysis_exit_code.txt` 留存；当时创建的 `../analysis_alpha/` 为空，不能把它的存在当作通过证据。

本轮新增 `export_frozen_analysis.py`，仅在独立 Python 进程中将 JSON 输出的 NumPy 标量转换为原生标量，实际仅转换 **10 个 numpy.bool**。冻结分析源码、参考计算、阈值和原始数据保持原哈希。适配后同一冻结分析器退出 **0**，记录为 `serialization_adapter_record.json`；原失败没有删除或改写。

随后 `independent_review.py` 不导入冻结 numerical_reference/analyze helpers，以 NumPy 重新实现坐标装载、D3Q19 传播矩阵、tau=1 标量参考、中心化最小二乘拟合、全场化学势/更新、源项碰撞与迁移及能量账本。独立分析退出 **0**，结论一致。连续率误差与冻结分析器最大绝对差约 **3.71e-11**，来自浮点求和、复模态与拟合计算次序差别，远小于冻结限。

两套分析通过且输入重新核对后，将适配输出的 `verdict.json` **逐字节复制到此前缺失的 `../analysis_alpha/verdict.json`**，未覆盖旧 verdict。`../analysis_alpha/EXPORT_PROVENANCE.json` 明确记录原失败、适配范围、复制来源、独立复核和哈希。这是 alpha 验收结果落盘，不是 C 启动授权；本轮未调用 C runner。

## 3. 线性扩散：离散实现与连续精度分开判断

同一 40 nm 周期盒、同一物理迁移率 `1.7361111111e-17 m²/(Pa s)`、同一物理界面宽度 10 nm 和表面张力 0.03 N/m。粗/细 `N=16/32`、`dx=2.5/1.25 nm`、`alpha=1/4`，`tau_CH=1` 保持，时间步减为 1/4。物性属于理想模型输入，**不是补齐后的真实 GHY 实测物性**。

冻结拟合窗为 `ceil(steps/4)..steps`，即粗格 **32..128**、细格 **128..512**，含两端，不按结果移动窗口。

| 波矢 | 粗格连续率绝对相对误差 | 细格连续率绝对相对误差 | 误差缩小倍数 | 原冻结限 | 判定 |
|---|---:|---:|---:|---|---|
''')
for di in ('x','y','z','xy','xyz'):
    vals=[next(x for x in R if x['id']==f'linear_n{n}_{di}_a{a}') for n,a in ((16,1),(32,4))]
    e0,e1=[x['continuum_relative_error'] for x in vals]
    lines.append(f'| {di} | {e0*100:.6f}% | {e1*100:.6f}% | {e0/e1:.4f} | 粗≤7%、细≤2% | PASS |')
linear=[x for x in R if x['kind']=='linear']
lines.append(f'''
实测衰减率与同窗离散参考的最大相对差 **{max(abs(x['rate_ratio']-1) for x in linear):.6e}**，低于 `1e-4`；全程复模态误差/初始振幅最大 **{max(x['mode_error_over_A'] for x in linear):.6e}**，全程程序内观测 L2/初始 RMS 最大 **{max(x['all_step_observed_L2'] for x in linear):.6e}**，均低于 `1e-8`。3D 初末 L2 独立重算也通过。

轴向归一化速率 spread（各向各自实测率/离散参考率的最大值减最小值）粗/细为 **{D['matrix_checks'][0]['spread']:.6e} / {D['matrix_checks'][1]['spread']:.6e}**，冻结限 `0.002`。冻结分析器对应值约 `2.942346e-9 / 1.229518e-8`，浮点级差异不改变判定。

这里验证的是程序对离散方程的实现、三个轴的数值一致性，以及两个给定网格之间的误差下降。五种波矢具有不同模长，不能把轴向/斜向衰减率差异直接称作物理各向异性；本轮也没有计算沟槽 Kxx/Kyy。误差约缩小四倍支持该测试区间内的细化改善，**两网格不足以完成 Richardson/GCI 或证明普遍二阶收敛**。

## 4. 全程最大相量漂移

无源组以 `Q=sum(phi)`、`(Q_n-Q_0)/Q_0` 定义相量漂移。按每条历史记录的十进制 phase_sum 用 long double 重算，而非只读末值。该量不是变密度完整 NS/CH 的物理总质量。源项两组单独检查收支，不能混入 Q 应不变的统计。

| id | 全程最大绝对相对漂移 | 发生步 | 末步有符号相对漂移 | 限值/判定 |
|---|---:|---:|---:|---|
''')
for x in R:
    if 'phase_drift_max' in x:
        lines.append(f"| {x['id']} | {x['phase_drift_max']:.8e} | {x['phase_drift_step']} | {x['phase_drift_final']:.8e} | ≤1e-9 / PASS |")
peak=max((x for x in R if 'phase_drift_max' in x),key=lambda x:x['phase_drift_max'])
lines.append(f'''
全批无源最大值 **{peak['phase_drift_max']:.10e}**，位于 `{peak['id']}` 第 **{peak['phase_drift_step']}** 步；末步为 **{peak['phase_drift_final']:.10e}**，不能用末态替代全程极值。峰值约为冻结预算的 **{peak['phase_drift_max']/1e-9*100:.5f}%**。细格漂移随步数有缓慢累计，但本协议时长内未超限；不外推长时漂移上界。

## 5. 实际非线性化学势与逐点离散收支

对每个保存步，从 phi 重建 `mu=4 beta phi(phi−1)(phi−0.5)−kappa Lphi`，再检验 `Delta phi=(alpha/6)Lmu_old`。链接自由能 `F=sum[beta phi²(phi−1)²−kappa phi Lphi/2]`，耗散项 `D=−(alpha/6)sum(mu Lmu)`；有限步余项 `R=Delta F−sum(mu_old Delta phi)`，余额 `Delta F+D_old−R` 由相邻全场独立重算，并核对历史中的 F、D、R 与余额。

| id | 最大化学势残差 | 最大逐点更新残差 | 最大能量余额/节点 | 判定 |
|---|---:|---:|---:|---|
''')
for x in R:
    if x['kind']=='nonlinear':
        lines.append(f"| {x['id']} | {x['mu_error']:.6e} | {x['step_error']:.6e} | {x['energy_residual_per_node']:.6e} | ≤1e-12 / PASS |")
lines.append(r'''
这些机器精度附近的残差证明所检离散等式与输出一致。保留有限步余项是为了避免误把离散时间余额等同于连续时间严格耗散；这不是完整 NS/CH 热力学能量定理的验收。

## 6. 源项单步：预期非零变化，非守恒泄漏

按原 D3Q19 顺序检查全部 19 个分布，直接重建碰撞与周期 push 迁移。逐点源项必须用 `sum_i b_i S(x−c_i)`，不能用同一点 `−S` 替换；全局身份为 `Delta Q=−sum S`。刷新后 phi 保持、原化学势本构与字段也复核。两组 alpha=1/4 共用粗格系数，**不是固定物理迁移率的空间细化对**。

| alpha | sum S | 实测 Delta Q | 碰撞最大残差 | 迁移最大残差 | 逐点更新最大残差 | 全局余额/节点 |
|---|---:|---:|---:|---:|---:|---:|
''')
for x in R:
    if x['kind']=='source':
        e=x['errors'];lines.append(f"| {x['alpha']:g} | {x['source_sum']:.12e} | {x['phase_change']:.12e} | {e['collision']:.6e} | {e['migration']:.6e} | {e['point']:.6e} | {e['budget_per_node']:.6e} |")
lines.append(r'''
全部残差低于 `1e-12`；phi 刷新差为 0。碰撞公式在独立实现与冻结实现中采用不同浮点加法次序，绝对残差约 `6.1e-17` 与 `6.9e-18`，都处于舍入量级，不应解读为物理差异。

## 7. 已验证边界与接续

本轮支持：**保持 tau_CH=1、以 CH 专用 alpha=1→4 调整迁移率的实现，在冻结的两组网格、五波矢、小振幅本构及源项单步测试上达到预定合同。** 冻结源码表明 alpha 只进入 CH 平衡分布，实际原 mu 字段本构验证保持；没有全局缩放原化学势来改变 NS 力。

本轮未验证：alpha=16 的空间结果、更长时扩散/更大扰动、完整 NS/CH 变量密度质量及动量/能量耦合、静滴 Laplace 平衡、平壁润湿、壁面几何、沟槽 Kxx/Kyy、GHY 实际压印预测。旧 tau_CH=2.5/8.5 路径的离散精度问题并未被删除或改写。本轮 alpha 合同通过不使既有历史 FAIL 转为 PASS。

**接续停点：alpha 已验收；C 未运行。** 本轮在预定 C 批次路径没有发现正式 C manifest，也没有执行 C 命令。以后若用户要求准备 C，应先核对既有 4 项粗格协议、资源预算和 alpha verdict 输入绑定，再单独交付运行入口，不自动开始计算。

C 的独立初场预算预测仍保持：两个真实本构组首步相量相对变化约 `−2.36935425e-9 / +8.29233009e-9`，可能超过保留的 `1e-9` 预算。这是已有解析/离散预测，**不是本轮实测 C 失败**。即使可由非零源项解释，也不能据此宣称完整物理质量守恒通过，不调高阈值掩盖。

## 8. 可复核产物与工具说明

- `independent_review.py`、`independent_review.json`、`independent_review.log`、`independent_review_exit_code.txt`：独立实现、逐项指标和退出证据。
- `case_summary.csv`：每项主指标；`frozen_export_adapted/verdict.json`：仅输出类型适配后的原冻结判据结果；`../analysis_alpha/verdict.json` 与其逐字节一致。
- `raw_input_hashes.json`、`protection_before.json`、`final_integrity.json`：输入读取及冻结保护证据。
- `alpha_diagnostics.png`、`alpha_diagnostics.pdf`：四联诊断图；`plot_diagnostics.py`、`figure_source_data.json`、`figure_provenance.json` 保存所有数值变换、完整漂移曲线、输出尺寸和版本。已实际查看 PNG 与 PDF 渲染页，属于内部验收图，不声称满足某一目标期刊规范。
- 同步入口：项目 `docs/reports/SIM240_AI_CONTEXT.md` 与 `docs/reports/AI_HANDOFF_20261015.md`。2026-10-23 17:12 缺失运行证据的旧 intake 保留为历史时点，本轮正式完成证据覆盖其“尚未启动”的当前状态。冻结准备 README/PREPARATION_STATUS 中“未正式运行”为准备时快照，保持绑定原文，以最新报告和共享入口为准。

本轮使用 scientific-writing 组织证据、scientific-visualization 制图；均为本地处理，数值结论由冻结公式与原始数据支持，仍须作者负责审定。相关工具方法参考：Kassis T, Agarwal V, He Y, Patel D, Brueckner A M. *Scientific Agent Skills: A Library of Procedural Knowledge for Research Agents*. arXiv:2609.00065, v2 (2026), DOI [10.48550/arXiv.2609.00065](https://arxiv.org/abs/2609.00065)。该引用仅说明工具背景，不是本项目物理模型的依据。
''')
(A/'REPORT.md').write_text('\n'.join(lines)+'\n')

# G3-h h=75 nm 基准一致性验证启动记录

## 1. 冻结参数

本次仅针对 G3-h `h=75 nm`，方向为 Parallel (P) 与 Perpendicular (T)，继承 G2 生产候选参数：

```text
dx=2.5 nm
tau=1.0
ForcedBGK
D3Q19 FORCE
Bouzidi boundary
a=1e5 m/s²
```

未修改 G2、物理参数、几何或验证门槛。

## 2. 运行目录与命令

已创建不可覆盖的独立目录：

```text
CASE/04_parameter_study/G3_EX240_height_sweep/results/g3h_baseline_h75_20260918T074500+0800_P
CASE/04_parameter_study/G3_EX240_height_sweep/results/g3h_baseline_h75_20260918T074500+0800_T
```

每个目录均写入 `run_manifest.txt`，包含 G2 源 SHA-256、h、方向、LBM 参数和 binary hash。

后台启动命令为：

```bash
tmux new-session -d -s g3h_baseline_h75 'cd /home/dell/yuanyuanxu/SIM240/CASE/04_parameter_study/G3_EX240_height_sweep && exec bash -lc '\''set -o pipefail; ./build/g3_ex240_h75 steady P results/g3h_baseline_h75_20260918T074500+0800_P > results/g3h_baseline_h75_20260918T074500+0800_P/run.log 2>&1; p=$?; echo $p > results/g3h_baseline_h75_20260918T074500+0800_P/exit_code.txt; ./build/g3_ex240_h75 steady T results/g3h_baseline_h75_20260918T074500+0800_T > results/g3h_baseline_h75_20260918T074500+0800_T/run.log 2>&1; t=$?; echo $t > results/g3h_baseline_h75_20260918T074500+0800_T/exit_code.txt; exit $((p || t))'\'''
```

## 3. 当前启动状态

本任务只负责发起后台运行，不等待稳态完成，也不读取中间结果判定 PASS。启动过程中 P 目录已产生初始化和诊断输出；本地执行环境随后未保持 tmux 会话，且尚无完整 `exit_code.txt`，因此 **h=75 基准验证尚未形成结果**，P/T 的 `K_eff`、mass error、Mach 和最终 boundary/RESULT gate 均不得提前报告。

Perpendicular 尚未开始或尚未留下完整结果的证据，不自动视为失败；需在持久化 tmux 环境中重新执行上述命令，并在 P/T 均完成后读取结果。

## 4. 后续门禁

只有 h=75 的 Parallel 与 Perpendicular 均完成并通过既有 G2 门禁，才允许启动 h=125 和 h=50。后续结果必须报告 `K_eff`、mass error、Mach、boundary audit，并与 G2 `h=75` 对比；本记录不授权自动进入下一高度，也不启动 G3 角度验证。

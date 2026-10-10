# G4 EX240 多周期阻力收敛（Nx=1,2,4,8）

周期沟槽横向复制下的阻力数值不变性 / 周期接缝完整性 / 大域质量审计。**不是**物理代表性尺度收敛证据（解释边界见 PERIOD_CONVERGENCE_PROTOCOL.md §1）。

## 工作流

```bash
# 1. 生成 + 白名单审计 + 编译（24 个二进制：4 Nx × {serial,mpi} × 3 驱动力）
make -C src all

# 2. 静态 preflight + Level-1 冻结（Nx=1 仅 precheck，稳态证据复用 REUSE_AUDIT.md）
./scripts/run_period_matrix.sh --level 1

# 3. MPI scaling 验证（Nx=2 a1e5 P：serial-1rank + mpi 1/4/8/16 rank，约 3.5h）
#    在 tmux 中启动：
tmux new-session -d -s g4-scaling \
  'cd <case> && exec ./scripts/run_scaling_test.sh'

# 4. 逐级批次（人工审查后才放行下一级；脚本绝不自动跨级）
tmux new-session -d -s g4-nx2 \
  'cd <case> && exec ./scripts/run_period_matrix.sh --level 2'
# 审查（10 门禁、级内线性、T 方向质量轨迹、E 比值）后：
#   ./scripts/run_period_matrix.sh --level 4
#   ./scripts/run_period_matrix.sh --level 8
```

## 关键文件

| 文件 | 作用 |
|---|---|
| PERIOD_CONVERGENCE_PROTOCOL.md | 冻结协议（阈值 1%、rank 分配、MPI 仪器化白名单、scaling 判据、回退预案） |
| REUSE_AUDIT.md | Nx=1 基线复用冻结引用（SHA 锚定 G2 证据） |
| period_matrix.csv | 冻结矩阵 |
| scripts/generate_period_source.py | SHA 锁定 G2 冻结源 + 定点替换（R 系列 13 项 + M 系列 23 项） |
| scripts/verify_deltas.py | 幂等 + Nx=1 恒等白名单审计 |
| scripts/preflight_period.py | 静态校验（整数格点、节点/links 期望、体积恒等式） |
| scripts/run_period_matrix.sh | 单级批次 runner（precheck 全过才 steady，tmux 启动） |
| scripts/run_scaling_test.sh + check_scaling.py | MPI scaling 验证（判据：门禁全过 + \|dJ\|/J≤1e-10 + mass 轨迹差≤1e-12） |
| scripts/postprocess_period.py | 门禁复核 + 级内线性 + E 比值（阈值 1%，连续两扩展） |

## 冻结锚值

| Nx | 格点 (nx×ny) | fluid_nodes | candidate_links | maximumSteps | ranks |
|---:|---:|---:|---:|---:|---:|
| 1 | 96×96 | 460800 | 130176 | 60000 | 1（仅 precheck） |
| 2 | 192×96 | 921600 | 260352 | 240000 | 8 |
| 4 | 384×96 | 1843200 | 520704 | 960000 | 16 |
| 8 | 768×96 | 3686400 | 1041408 | 3840000 | 16 |

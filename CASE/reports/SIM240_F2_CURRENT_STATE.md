# SIM240 F2 当前阶段项目状态

审计范围：F1 单相基线、F2 steady 基线、F2_dynamic_v1、F2_dynamic_v2_motion。  
审计方式：只读检查 README、源码、archive、results、result.txt、run.log、进程和 tmux 状态；未修改代码，未启动计算。

状态标签含义：`[已验证]` 表示有结果文件或可复核日志证据；`[已实现]` 表示源码中存在对应接口；`[正在运行]` 仅在当前进程证据存在时使用；`[未完成]` 表示缺少实现或证据；`[计划]` 表示建议工作。

## 1 SIM240总体目标

SIM240 采用 OpenLB + LBM，对真实纳米沟槽几何进行显式解析，不用等效多孔介质阻力替代结构本身。总体路线为：

```text
真实纳米结构
      ↓
液体输运机制
      ↓
介尺度模型
      ↓
填充预测
```

当前研究路线：

```text
F1：单相输运与阻力验证
      ↓
F2：液膜压缩动态模型
      ↓
F3：两相润湿和填充
```

其中 F2 的“动态模型”目标不能由目录名称或已有稳态结果自动推断，必须以逐时间步几何和边界更新代码为证据。

## 2 F1阶段状态

目录：`CASE/06_filling_dynamics/F1_single_phase_compression`

### 模型与输出

- `[已验证]` 显式 EX240 周期几何，液膜高度 `h=50、75、125 nm`。
- `[已验证]` 生产网格 `dx=2.5 nm`。
- `[已验证]` D3Q19、Forced BGK、tau=1.0、周期体力驱动和 Bouzidi 零速度边界。
- `[已实现]` 输出 `Q`、等效 `DeltaP`、`R_eff=DeltaP/Q`、耗散功率和 `fillRatio`。
- `[已验证]` 六个 P/T 稳态结果均有 `result_summary.csv`、`result.txt`、`diagnostics.csv` 和 `exit_code.txt`。

### 输运证据

`results/summary/` 已提供：

- `[已验证]` `K_parallel` 和 `K_perpendicular`；
- `[已验证]` `R=1/K` 与高度效应；
- `[已验证]` `R_perpendicular/R_parallel` 在 h=50、75、125 nm 分别为 `3.979521990530565`、`2.230734081816928`、`1.437799584459523`；
- `[已验证]` 液膜高度增加时两方向阻力降低、有效迁移率增加；
- `[已验证]` 六个结果 `PASS=true`、`converged=true`，`q_min=q_max=0.5`，`fallback_count=0`；最大记录质量误差为 `1.1845844822105344e-11`，最大 Mach 为 `2.0089028958621632e-07`。

这里的 `fillRatio` 是单相固定几何的占据率，不是两相界面填充率。F1 已验证的是固定几何下的单相水力输运，不是动态压缩。

## 3 F2 steady基线

目录：`CASE/07_filling_dynamics/F2_liquid_film_compression_dynamic`

### 模型

- `[已验证]` 单相液体、固定液膜高度 h、周期体力稳态驱动。
- `[已验证]` `dx=2.5 nm`、tau=1.0、D3Q19、Forced BGK、Bouzidi 边界和 x/y 周期边界。
- `[已实现]` 几何在初始化阶段由 `materialAt(..., p.mesaGap)` 建立；随后调用 `geometry.communicate()` 和 Bouzidi 边界安装。
- `[已实现]` 时间循环只执行固定几何上的 `lattice.collideAndStream()` 和诊断测量。

### 结果与审计

- `[已验证]` h=50、75、125 nm 的 P/T 六个稳态结果存在 `result_summary.csv` 和 `result.txt`，记录为 `PASS=true`、`converged=true`、`exit_code=0`。
- `[已验证]` 结果中的 q 审计为 `q=0.5`，无非法回退；质量和 Mach 数与 F1 基线一致，最大质量误差约 `1.1845844822105344e-11`，最大 Mach 约 `2.0089028958621632e-07`。
- `[已验证]` F2 steady 的 `Keff`、`R_eff`、Q 和耗散值与 F1 固定几何结果相同。
- `[未完成]` 该目录没有证明液膜高度随时间改变，也没有证明存在压头位移或液体排出质量守恒。

因此当前 F2 steady 更准确的表述是“固定 h 的单相稳态基线”，不能称为已完成动态压缩模型。

## 4 F2_dynamic_v1

目录：`CASE/07_filling_dynamics/F2_dynamic_v1`

### 创建目的与修改范围

- `[已实现]` 目录保留了 F2 源码、备份源码和生成的固定高度源码变体，用于从 F1/F2 steady 框架向动态阶段过渡。
- `[已实现]` 当前源文件支持高度参数、P/T 方向、固定几何初始化、稳态碰撞与输运诊断。
- `[已验证]` 当前源码仍在进入时间循环前一次性建立 material field 和 Bouzidi links；循环中没有 `currentGap`、压头位置或几何重建路径。
- `[已验证]` 该版本已有的结果文件与 F2 steady 结果重合，不能作为独立动态证据。

### 判断

**F2_dynamic_v1 当前只是 steady 固定几何框架的复制/参数化版本，不是动态压缩实现。** 目录名、备份文件名和结果目录不能替代逐步几何更新证据。

## 5 F2_dynamic_v2_motion

目录：`CASE/07_filling_dynamics/F2_dynamic_v2_motion`

### 源码审计

当前源码中确实存在：

- `[已实现]` `compressionVelocity=0.1`；
- `[已实现]` `currentGap = max(0, mesaGap - compressionVelocity * step * dt)`；
- `[已实现]` diagnostics 表头包含 `height_nm`，并记录 `currentGap` 对应的高度值；
- `[已实现]` 逐步 `collideAndStream()` 时间循环。

但同时存在以下关键事实：

- `[已验证]` geometry 只在时间循环之前根据初始 `p.mesaGap` 建立一次；
- `[已验证]` `materialAt`、`geometry.communicate()` 和 `setBouzidiBoundary` 不在时间循环内调用；
- `[已验证]` `currentGap` 只被写入诊断，不反馈给 material field、几何 indicator 或边界链接；
- `[已验证]` 当前每一步使用同一固定 geometry 和同一组 Bouzidi links；
- `[未完成]` 没有 `h(t) → geometry update → material update → boundary update` 的完整实现；
- `[未完成]` 没有证明 `dV/dt` 与排出流量 Q 的质量守恒闭合。

因此，**当前版本为动态参数记录验证，不是真正移动边界压缩模型。** 这也是本阶段最重要的科学边界。

### 最新预检证据

最新目录为 `results/precheck_h125_P_20260920T094120+0800`：

- `[已验证]` `geometry_PASS=true`；
- `[已验证]` `converter_PASS=true`；
- `[已验证]` `q_audit_PASS=true`；
- `[已验证]` `candidate_links=installed_links=130176`；
- `[已验证]` `q_min=q_max=0.5`、`fallback_count=0`；
- `[已验证]` `collide_and_stream_calls=0`、`exit_code=0`。

该证据只证明 h=125/P 的零步几何和边界预检，不证明动态压缩或稳态输运结果。

## 6 当前运行任务

- `[已验证]` 当前 `ps` 未发现 F1/F2/OpenLB 相关运行进程。
- `[未完成]` `tmux ls` 在当前受限环境返回 `Operation not permitted`，因此不能用 tmux 查询结果证明不存在其他会话；只能确认当前进程列表中没有相关计算。
- `[已验证]` F1 六个正式结果已结束并有 `exit_code=0`。
- `[已验证]` F2 steady 六个正式结果已结束并有 `exit_code=0`。
- `[已验证]` F2 v2 最新 h=125/P 是零步预检，`exit_code=0`，不是正式动态计算。
- `[未完成]` 未发现 F2_dynamic_v2_motion 的正式动态结果目录、动态压力—流量—体积时间序列或独立动态 `exit_code` 证据。
- `[未完成]` 部分 F2 目录中存在重复的 h=50/P 运行目录，但没有完整 `result.txt`/`result_summary.csv`；这些目录不能作为完成证据。

## 7 当前科学问题

真正的动态压缩需要在每个时间步形成闭合链：

```text
h(t)
  ↓
wall position
  ↓
material field
  ↓
Bouzidi links
  ↓
LBM collideAndStream
```

还必须满足：

1. **Moving boundary**：压头位置改变后，流体区域和边界位置同步改变；
2. **Mass conservation**：压头体积变化率 `dV/dt` 必须与液体排出流量 Q、质量变化和边界通量一致；
3. **Numerical stability**：逐步监控 Mach、rho deviation、mass error、q、fallback 和 unresolved links；
4. **Result classification**：动态几何、数值门槛、质量闭合和结果 PASS 必须分开记录，不能用 `currentGap` 诊断列替代动态边界证据。

## 8 下一阶段建议

### F2_dynamic_v3（计划）

建议建立独立的 `F2_dynamic_v3`，不修改或覆盖 v2：

```text
for timestep:
    calculate h(t)
    update geometry
    update boundary links
    collideAndStream
    measure pressure, force, volume, flow rate, mass
```

最低实现要求：

- `[计划]` 采用可审计的压头运动规律和时间步长；
- `[计划]` 每步重建或增量更新 material field；
- `[计划]` 每步更新 Bouzidi 几何距离 q，并记录 candidate/installed/unresolved/fallback；
- `[计划]` 输出 `h(t)`、fluid volume、mass、Q、pressure/force、`dV/dt` 和质量闭合残差；
- `[计划]` 先做短步单元测试与几何更新测试，再做短时动态验证；
- `[计划]` F2 v2 保持只读归档，不修改现有结果。

## 9 导师汇报版

### 《SIM240纳米压印液膜压缩LBM模拟阶段进展》

**已完成**

- `[已验证]` F1 单相 EX240 纳米沟槽输运验证；
- `[已验证]` 沿槽/横槽方向液压阻力和高度依赖分析；
- `[已验证]` 固定液膜高度的单相稳态模型与数值审计；
- `[已验证]` F2 steady 基线的几何、Bouzidi q、质量和 Mach 记录。

**当前**

- `[已实现]` F2 v2 已加入压缩速度和 `currentGap` 的诊断记录；
- `[未完成]` 动态压缩边界尚未真正更新 geometry、material field 和 Bouzidi links；
- `[未完成]` 当前没有可用于动态填充结论的 `h(t)`—Q—质量闭合证据；
- `[已验证]` 当前没有相关正式计算正在运行。

**下一步**

- `[计划]` 开发独立 F2_dynamic_v3 移动压头—液体排出模型；
- `[计划]` 首先验证移动边界几何更新、Bouzidi 链接更新和质量守恒；
- `[计划]` 再进入动态 LBM 计算，最终为 F3 两相润湿和填充模型提供可信输入。

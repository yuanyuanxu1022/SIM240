# R2XY — 面内方向：受限液区在显式 EX240 沟槽上的铺展与流量

> 本目录属 SIM240 液滴线 **R2-XY**（面内支）。**协议见**
> `CASE/plans/SIM240_液滴R2-XY最小验证协议_20261015.md`（v1.0 已冻结；唯一保留项 §2.8 单位口径）。
> 上游：R0（守恒根因）→ E0（自洽初始化）→ R1（平壁静滴润湿基准，全 PASS）均已闭环。

## 状态

| 项 | 状态 |
|---|---|
| 协议冻结 v1.0 | ✅ 2026-10-15 |
| run 目录（本目录） | ✅ 已建（`src/Makefile`） |
| 源码 `src/r2xy_confined_patch.cpp` | 已存在（2026-10-15 15:20文件快照）；实现审查待完成 |
| 编译 / 静态检查 | 可执行文件已存在；当前源码与程序的绑定、构建日志及独立退出证据待核对，不据文件存在判为通过 |
| 几何审计（geometry_PASS 前置） | ⏳ 待做 |
| 200 步短段测速 | ⏳ 待做 |
| 正式 run（tmux 后台） | ⏳ 待短段测速后定总步数 |

当前交接：`docs/reports/AI_HANDOFF_20261015.md`。正式计算前须复核协议§2.8单位换算（现有dt数字与该节公式不符）、0.944/0.96μm足迹和初始体积口径。x端壁无通量，越过初始足迹的液量属于域内重新分布，不能记作域外排出。本轮只更新进度，不改协议、源码或原始结果。

## 冻结要点（详见协议）

- 几何：图案在**模具（顶面）**——凹槽轴 = **x**，周期方向 = **y**（P = 240 nm，凹槽 120 × 深 100 nm）；**基板（底面）平壁**。
- 间隙 **h = 75 nm**（凸台下方 75 nm、凹槽下方 175 nm）；**不使用移动边界**。
- 液区：受限薄膜形态（非自由球冠），足迹 **4 × 4 周期 = 0.944 × 0.944 μm**，V ≈ 0.1114 fL，θ = 60°。
- 域：x、y 各 **12 周期 = 2.88 μm**；**x 两端无滑移壁**（缓冲 968 nm），**y 周期**。
- 分辨率 **dx = 5 nm**（凹槽 24 格、间隙 15 格、深 20 格、界面宽 20 nm）；z ≈ 39 格；总 **≈ 13 M 格**（双 lattice）。
- 驱动：**毛细自铺展**（无外力）。
- 界面方法：相场 well-balanced Cahn–Hilliard + **tanh 自洽初值**（E0 结论，必用）。

## 复用来源（未改动任何既有案例）

- 几何与逐槽填充率诊断：`CASE/06_filling_dynamics/F1_liquid_film_compression/src/f1_liquid_film_compression.cpp`
- 物理单位换算与成对截面流量诊断：`CASE/02_geometry_transport/G2_EX240_single_period_transport/src/g2_ex240_single_period_transport.cpp`
- 两相 well-balanced CH 框架与润湿边界：`grooveDNS/stage3_ex240_local/phasefield_minimal_validation/phasefield_minimal_validation.cpp`

## 运行分工（项目约定，长期保持）

改代码 / 编译 / 静态检查 / 短段测速由助手完成；**正式计算一律 tmux 后台独立跑，助手不轮询、运行中不看日志**；算完后另启任务做结果分析。命令形式：

```bash
tmux new-session -d -s <session-name> 'cd <case-directory> && exec <run-command>'
```

## 构建

```bash
cd CASE/08_droplet_inplane/R2XY_confined_patch/src && make
```

产出：`CASE/08_droplet_inplane/R2XY_confined_patch/build/r2xy_confined_patch`

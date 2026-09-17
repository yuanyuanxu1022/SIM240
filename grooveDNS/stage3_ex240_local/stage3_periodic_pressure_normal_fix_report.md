# 阶段三 x 周期压力面法向最小修复报告

## 结论

固定压头开放边界基线已通过。独立程序使用真实 OpenLB `SuperGeometry`、`SuperLattice` 和 `LocalPressure3D`，在 `h=75 nm`、x 周期、y 两端等参考压力、z 固壁、零初速及零体力条件下完成 100 步 `collideAndStream`。本轮没有移动压头，也没有运行任何其他阶段。

本结论只证明该固定几何中的压力边界初始化和零驱动推进正常；它不能证明开放边界在实际排液时的精度，也不能证明移动边界或液体受压守恒。

## 失败机理与源码依据

此前失败并非 `LocalPressure3D` 不支持平面，而是默认 `material=0` outside indicator 把 x 周期 padding 同时判作域外：2400 个压力节点中有 60 个位于 x 周期拼接处，类型虽为 `Flat`，离散法向却为 `(0,0,0)`。

本机 OpenLB 的实际调用链为：

1. `boundary::set` 在每个边界节点调用 `computeBoundaryTypeAndNormal(fluidI, outsideI, latticeR)`，再将所得类型和法向交给边界条件；源码：`/home/dell/openlb/src/boundary/setBoundary.h`。
2. `LocalPressure3D::getDynamics` 只接受 `DiscreteNormalType::Flat`；源码：`/home/dell/openlb/src/boundary/localPressure3D.h`。
3. 平面动力学构造仅接受六个单位轴法向；零向量会抛出 `Could not set Boundary.`；源码：`/home/dell/openlb/src/boundary/setBoundary3D.h`。
4. `SuperIndicatorFfromIndicatorF3D` 会把分析型 indicator 映射为各 block indicator，并使用 cuboid 的真实物理坐标；源码：`/home/dell/openlb/src/functors/lattice/indicator/superIndicatorF3D.h/.hh`。

因此本次采用了首选的最小修复，没有改用定向接口。

## 实施内容

新增独立程序 `periodic_pressure_baseline.cpp` 和 Makefile 目标 `openlb-pressure-baseline`。压力边界专用 `PeriodicXOutside` 的语义是：

- x 坐标永不构成 outside，因为 x padding 是周期镜像；
- y 仅在 cell-centred 核心域 `[2.5,237.5] nm` 外判作 outside；
- z 仍按非周期核心域边界判作 outside，并未机械地只判断 y；
- 基底和压头继续由材料 2、3 表示，未被 outside indicator 或压力材料覆盖；
- 全局材料图未为规避异常而修改。

几何在法向审计前调用 `geo.communicate()`；OpenLB geometry overlap 为 3。压力边界仅初始化注册一次，时间循环没有重复添加边界或处理器。

## 初始化逐节点审计

| 检查项 | 结果 |
|---|---:|
| 预期/实际压力节点 | 2400 / 2400 |
| 正确法向 | 2400 |
| 零法向 | 0 |
| 错误或冲突法向 | 0 |
| 遗漏 | 0 |
| 固体节点被压力边界覆盖 | 0 |
| x 周期拼接压力节点 | 60 |
| x padding 被专用 indicator 误判为 outside | 0 |

材料 4（低 y 端）1200 个节点均为 `Flat,(0,-1,0)`；材料 5（高 y 端）1200 个节点均为 `Flat,(0,1,0)`。60 个拼接节点中，低端 30 个为 `(0,-1,0)`，高端 30 个为 `(0,1,0)`。完整逐节点记录见运行目录中的 `pressure_node_diagnostic.csv`。

这里的符号是本机 API 实际返回并被方向/朝向动力学构造器接受的离散法向，不是根据文字约定猜测所得。

## 固定开放边界基线

- run-id：`open_drain_fixed_h75_periodic_outside_20260907`
- 命令：`make openlb-pressure-baseline`，随后 `./periodic_pressure_baseline`
- OpenLB：`5953d8a-dirty`，Git commit `882924a9cfc8dcdf82909e39530789cb6f5ebcc4`
- 程序 SHA-256：`8c4a42302b0a369a5b34299be5a5a6c7a44acfbe1bbb96e2838762e57308a503`
- `dx=5 nm`，converter 实际 `dt=1.0e-11 s`、`tau=1.7`
- 完成步数：100；物理时间：`1.0e-9 s`
- 退出码：0；结束原因：完成 100 步且全部冻结阈值通过

统计范围为材料 1、4、5 的当前域内流体节点，共 57600 个；实体材料 2、3 不计入质量。两端质量通量采用压力面 cell-centred 求积，低端向外取 `-rho*u_y`，高端向外取 `+rho*u_y`，面积元为 `dx²`。累计向外质量采用相邻时间点的梯形积分。固定域质量收支定义仍为

`R_M(t) = M_domain(t) - M_domain(0) + cumulative_outward_mass(t)`。

| 指标 | 100 步结果 | 冻结阈值 | 判定 |
|---|---:|---:|---|
| 非有限值 | 0 | 必须为 0 | PASS |
| 最大物理速度 | `0 m/s` | `<=1e-14 m/s` | PASS |
| 格子密度范围 | `[1,1]` | `[1-1e-12,1+1e-12]` | PASS |
| 初始/最终域内流体质量 | `7.2e-18 / 7.2e-18 kg` | — | — |
| 域内质量相对变化 | `0` | `abs <=1e-13` | PASS |
| 低/高端最终向外质量通量 | `0 / 0 kg/s` | 零驱动下随速度阈值检查 | PASS |
| 累计向外质量 | `0 kg` | — | — |
| 质量收支残差 | `0 kg`（相对值 0） | `abs(relative)<=1e-13` | PASS |
| 材料场变化 | 无 | 节点计数必须完全一致 | PASS |

正常退出没有被当作单独通过依据；上表各项均由完整 0–100 步 CSV 和最终状态独立判定。初始与最终材料场、速度场已写入 VTI/VTM。

## 文件与保护范围

本轮新增：

- `periodic_pressure_baseline.cpp`
- Makefile 中独立目标 `openlb-pressure-baseline`
- `output/open_drain_fixed_h75_periodic_outside_20260907/`
- 本报告

运行目录保存 `baseline_statistics.csv`、2400 节点完整诊断、初始化审计、日志、命令/退出码、源码清单以及 step 0/100 的材料与速度 VTI/VTM。此前失败目录和静态基准均保留。没有修改 OpenLB 库、阶段一、阶段二、其他阶段三案例或原 `tmp/`。

## 尚未验证

- 非零压差或排液时压力边界的反射、稳定性和定量精度；
- 75→65 nm 的真实压头移动、链接交点和壁速更新；
- 节点转换、排液质量账本及移动域守恒；
- FreeSurface、液滴、接触角、困气和正式压印工况。

依照本轮范围，到固定开放边界基线通过为止，未启动移动压头测试。

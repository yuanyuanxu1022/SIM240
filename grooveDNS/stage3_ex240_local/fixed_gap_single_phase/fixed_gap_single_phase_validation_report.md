# SIM-EC1XT240 固定间隙单相流动基准报告

## 判定

**固定间隙单相基准PASS。** h=75、70、65 nm的X/Y六个真实OpenLB工况均达到预先冻结的1000步稳态窗口，正常退出且退出码为0。各工况无NaN/Inf，material场不变，流体体积与解析值一致，质量漂移、密度、Mach和截面通量一致性均通过。

该结果完成的是dx=5 nm功能网格上的固定显式结构流动响应，不是连续压头下降、FreeSurface、液滴、润湿、空气或动态压印结果。STEP 5-F/G/H保留为历史动态边界验证，没有被修改或用于本轮推进。

## 1. 独立case与复用范围

目录：`stage3_ex240_local/fixed_gap_single_phase/`。

- 求解器：`sim_ec1xt240_fixed_gap_dns.cpp`；
- 冻结协议：`frozen_protocol.md`；
- 后处理：`postprocess_fixed_gap.py`；
- OpenLB：`5953d8a-dirty`，commit `882924a9cfc8dcdf82909e39530789cb6f5ebcc4`；
- 求解器SHA-256：`99e93590c064ac962a4a483ffdb24abd390656479244c3e423a8d2558c18054c`。

实现复用已验证的`ex240_homogenization/ex240_h65_dns.cpp`：真实SuperGeometry/SuperLattice接入、cell-centred材料划分、ForcedBGK、核心节点积分、质量与两截面诊断。新增差异仅为运行时冻结间隙75/70/65 nm、物理压力场、阻力输出和正确的SIM-EC1XT240用户可见名称。原h=65结果和动态边界代码均未修改。

## 2. 几何、边界与驱动

- `Lx=Ly=240 nm`；x=0–60 nm左半凸台，60–180 nm凹槽，180–240 nm右半凸台；
- 槽深100 nm，基底z=0，凸台底面z=h，槽顶z=h+100 nm；
- x/y双周期，基底和压头为固定halfway bounce-back无滑移壁；
- 单相全充液；`rho=1000 kg/m3`，`nu=1e-6 m2/s`；
- `dx=5 nm`，`dt=1e-11 s`，`tau=1.7`；
- X工况`a=(1e5,0,0) m/s2`，Y工况`a=(0,1e5,0) m/s2`，格子体力非零分量为`2e-9`。

选择75、70、65 nm是因为三者均为5 nm整数倍，cell-centred材料与halfway壁面恰好落在名义位置。未使用72.5/67.5 nm，避免把halfway有效壁面偏移2.5 nm后仍按名义间隙报告。

名义体积及离散结果：

|h (nm)|`H_ref=h+50 nm` (nm)|名义体积 (m3)|流体节点|离散体积 (m3)|
|---:|---:|---:|---:|---:|
|75|125|`7.2000e-21`|57,600|`7.2000e-21`|
|70|120|`6.9120e-21`|55,296|`6.9120e-21`|
|65|115|`6.6240e-21`|52,992|`6.6240e-21`|

核心平面实际存储48×48个节点，不存重复周期端点；overlap和padding不计入质量、体积或通量。

## 3. 响应与阻力定义

平面面积`A_plan=Lx*Ly`，深度积分通量为

`J_i=(1/A_plan) integral_fluid u_i dV`。

以单方向加速度驱动时：

`K_ii=mu*J_i/(rho*a_i)`，`B_ii=K_ii/H_ref`。

本报告的主阻力为

`R_J,i=(rho*a_i)/J_i=mu/K_ii`，单位`Pa s/m3`。

同时保存`R_U,i=(rho*a_i)/mean(u_i)=mu/B_ii`，单位`Pa s/m2`。这些量是周期体力驱动固定单元的线性输运响应，尚未证明可直接作为宏观压印模型阻力，也不是数值残差的倒数。

## 4. 正式结果

|h (nm)|方向|step|J主项 (m2/s)|K主项 (m3)|B主项 (nm2)|`R_J` (Pa s/m3)|最大质量漂移|最大Mach|
|---:|:---:|---:|---:|---:|---:|---:|---:|---:|
|75|X|1807|`4.7194593e-12`|`4.7194593e-23`|377.557|`2.1188868e19`|`8.998e-13`|`3.213e-7`|
|75|Y|2379|`1.0162533e-11`|`1.0162533e-22`|813.003|`9.8400660e18`|0|`5.830e-7`|
|70|X|1711|`3.9242912e-12`|`3.9242912e-23`|327.024|`2.5482309e19`|`1.056e-12`|`2.844e-7`|
|70|Y|2314|`9.1339343e-12`|`9.1339343e-23`|761.161|`1.0948185e19`|0|`5.560e-7`|
|65|X|1703|`3.2231602e-12`|`3.2231602e-23`|280.275|`3.1025452e19`|`1.069e-12`|`2.519e-7`|
|65|Y|2255|`8.2042001e-12`|`8.2042001e-23`|713.409|`1.2188879e19`|0|`5.315e-7`|

间隙从75降到65 nm时，X向`R_J`增加约46.4%，Y向增加约23.9%；`R_X/R_Y`由约2.15增至2.55。新几何在凸台下方保持横向连通，所以X阻力有限，不能套用阶段二连续实体墙的`Bxx≈0`结论。

## 5. 质量、截面和稳定性

- 六组最大质量漂移不超过`1.0694e-12`，远低于`1e-10`门槛；
- 最大`|rho-1|`不超过`9.9130e-8`，低于`1e-6`门槛；
- 最大Mach不超过`5.8302e-7`，低于0.05；
- X两截面相对差为`4.72e-8–5.28e-8`，Y为输出精度内0，均低于`1e-5`；
- 实际`Re_max`为`8.36e-6–2.10e-5`；
- 所有material字段保持不变，无NaN/Inf。

这里的质量平衡是双周期、固定壁面封闭流体域的总流体质量漂移；没有入口/出口质量通量项。

## 6. pressure与velocity场

每个正式run的初始和收敛VTI/VTM均包含：

- `material`；
- `velocity_m_s`；
- `pressure_Pa`。

本地OpenLB按`p_lattice=cs2*(rho-1)`并经converter输出物理压力。X驱动的收敛局部压力范围约为±7.4–7.9 Pa；Y驱动因几何沿y平移不变，压力扰动仅约`1e-7 Pa`量级。

由于x/y均为周期边界，驱动力是`rho*a`的等效均匀压强梯度，域内没有可定义的入口—出口总压降。压力图只能解释局部周期压力扰动；阻力按已声明的体力梯度与J计算，不能从VTI压力极差替代。

## 7. 文件与图件

- 汇总：`fixed_gap_single_phase_summary.csv`；
- 完整时序：每个run目录的`diagnostics.csv`；
- 场数据：每个run目录的`vtkData/`；
- 阻力：`figures/fixed_gap_flow_resistance.png/.pdf`；
- 收敛：`figures/fixed_gap_J_convergence.png/.pdf`；
- 数值检查：`figures/fixed_gap_numerical_checks.png/.pdf`；
- 压力范围：`figures/fixed_gap_pressure_range.png/.pdf`；
- 复现信息：各run的`run_manifest.txt`及根目录`source_manifest.txt`。

## 8. 结论范围与下一步

本轮验证了SIM-EC1XT240显式直槽在三个固定间隙、dx=5 nm、单相全充液、双周期体力驱动下的稳态流动和方向阻力趋势。它不是网格无关结果，不代表真实压头下降时间史、实际残余膜厚、液滴供液、润湿、填槽或困气。

按照调整后的研究路线，下一门禁应是独立的固定几何FreeSurface与接触角基准；本轮不自动启动该工作，也不恢复STEP 5动态边界开发。

Historical internal directory names such as `stage3_ex240_local` and `ex240_homogenization` are retained for reproducibility. The correct physical/model designation is **SIM-EC1XT240**.

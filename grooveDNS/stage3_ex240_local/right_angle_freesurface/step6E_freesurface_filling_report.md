# SIM-EC1XT240 STEP 6-E 直角交汇沟槽 FreeSurface 填充基准

## 判定

**STEP 6-E：FAIL。** 独立程序已使用真实 OpenLB FreeSurface 后处理器、显式正交交汇几何、表面张力和润湿壁完成编译与短测。正式运行在 step 1623（`1.623 ns`）按冻结门禁停止：一个 interface/fluid cell 的液相体积分数降至 `-8.63535e-3`，超过 OpenLB `TRANSITION=1e-3` 所允许的负向带宽。程序没有 NaN/Inf，rho、Mach、液体质量和 material 均稳定，但沟槽总填充率没有产生可辨识净增长，因此不能把本轮称为填充验证通过。

本轮没有动态压头、扩域、角度扫描或参数优化。没有修改 STEP 5 和 STEP 6-A–6-D 的源码或结果。

## 1. 模型范围与本机 API 限制

计算域为 STEP 6-C 的一个 `240×240 nm` 周期单胞。沟槽平面为
`60<=x<180 nm OR 60<=y<180 nm`，形成两个 120 nm 宽的正交交汇槽；固定间隙为 65 nm，槽深为 100 nm。x/y 双周期，基底和带槽压头为固定无滑移壁。

本机 OpenLB `5953d8a-dirty` 的 FreeSurface 方法只求解液体及界面。`Gas` 是固定参考压力的自由表面状态，不求解气体速度、黏性或困气压力。因此这是液体—参考气压自由界面基准，不是完整的两流体气液 DNS。

本版本没有按角度给定接触角的 FreeSurface API。本机官方说明和既有自由球原型只支持通过固壁 `EPSILON` 改变润湿倾向；本轮按说明设置固壁 `EPSILON=1`，即 wetting-wall 倾向。它不是已校准的接触角，不能据此报告某个接触角数值或真实树脂—模具润湿性。该限制本身使“接触角边界物理一致性”只能做实现级核对，不能完成材料级验证。

## 2. 初始条件与数值参数

- OpenLB D3Q27 FreeSurface descriptor，BGK；
- `dx=5 nm`、`dt=1e-12 s`、`tau=0.62`；
- `rho=1000 kg/m3`、`nu=1e-6 m2/s`；
- 表面张力测试值 `sigma=0.0309 N/m`，格子值 `2.472e-4`；该值复用项目已有自由球功能测试，不声明为已确认材料参数；
- 体力为零，压头固定；
- 65 nm 间隙初始全液，槽口设置一层 `epsilon=0.5` 的 interface seed，槽内其余空间为 gas。

名义沟槽体积为 `4.3200e-21 m3`。初始槽内液体体积为 `1.0800e-22 m3`，所以初始 `Fill=0.025`。初始液体总体积为 `3.8520e-21 m3`：包括间隙中的 `3.7440e-21 m3` 和槽口半格界面种子。初始 fluid/interface/gas 节点数分别为 29,952/1,728/32,832；固体节点为 23,040。

正式门禁在运行前记录于 `frozen_protocol.md`。第一次正式 v1 在 step 1602 因错误使用 `1e-8` 检查正常的 FreeSurface transition overshoot 而停止；该记录完整保留。v2 只把审计范围改为与实际 `TRANSITION=1e-3` 一致，没有改变物理参数。v2 的 `epsilon=-8.64e-3` 仍越过实际算法带宽，因此是正式失败证据。

## 3. 短测试

300 步 v3 短测通过初始化与推进门禁：rho 保持在 `[0.998756,1.000443]`，最大 Mach 为 `1.59057e-3`，最大液体质量相对漂移为 `2.50228e-5`，material 不变且无非有限值。短测不要求在 `0.3 ns` 内观察到宏观填充。

## 4. 正式运行结果

|指标|结果|判定|
|---|---:|:---:|
|完成步数/物理时间|1623 / `1.623 ns`|提前停止|
|初始/最终总槽填充率|`0.0250000 / 0.0250049`|无净填充|
|初始/最终 junction 填充率|`0.0250000 / 0.0193235`|下降|
|初始/最终 arms 填充率|`0.0250000 / 0.0278456`|上升|
|最大液体质量相对漂移|`2.50228e-5`|PASS|
|rho 全过程范围|`[0.998756,1.000447]`|PASS|
|最大 Mach|`1.59057e-3`|PASS|
|最大物理速度|`4.59157 m/s`|低 Mach，但纳米毛细瞬态速度较高|
|最大单步 Fill 变化|`7.28590e-7`|无全局突跳|
|Fill 增量符号反转次数|217|存在小幅振荡|
|material 变化|0|PASS|
|NaN/Inf|0|PASS|
|最小 epsilon|`-8.63535e-3`|FAIL|

停止 cell 为 lattice `(45,35,15)`，物理坐标 `(227.5,177.5,72.5) nm`，material 1，位于水平侧臂槽口上方第一层。该 cell 在停止场中仍被标记为 fluid，却具有负 epsilon，说明界面转换/质量重分配局部状态已经不物理。界面最高位置刚到 `72.5 nm`，尚未形成沿 100 nm 槽深的可靠上升过程。

在停止场中，对 `epsilon>0` 液体节点读取的压力范围约为 `[-3.207,2.127] MPa`，最大速度为 `1.654 m/s`。MPa 量级与纳米曲率下的毛细压力尺度相容，但当前界面门禁已失败，不能把该压力场作为定量填充预测。

## 5. 填充路径与 STEP 6-D 的关系

总槽 Fill 几乎不变，但液体从 junction 界面向 arms 重新分配：到停止时 junction Fill 降低约 `5.68e-3`，arms Fill 增加约 `2.85e-3`。面积加权后两者基本抵消。这证明模型产生了润湿/表面张力驱动的局部界面运动，却没有证明液体净进入沟槽。

STEP 6-D 是全充液、体力驱动的稳态单相路径分析，显示 junction 主流较快、正交侧臂低速。本轮是无体力的毛细界面问题，驱动和初态不同；目前结果既未达到“进入交汇区”和“侧槽填充”的里程碑，也不足以验证 STEP 6-D 对真实填充顺序的预测。

## 6. 可视化与数据

- 正式 run-id：`step6E_freesurface_h65_dx5_sigma00309_v2_20260910`；退出码 3；
- `output/<run-id>/fill_fraction_history.csv`：1624 个逐步记录，含 Fill、junction/arm Fill、界面高度、质量、rho、Mach 和 epsilon；
- `output/<run-id>/vtkData/sim_ec1xt240_step6E_freesurface.pvd`：ParaView 时间序列；每个 VTI 含 `material`、`velocity_m_s`、`pressure_Pa`、`liquid_volume_fraction`、`free_surface_cell_type` 和 `free_surface_mass`；
- VTK 保存 step 0、500、1000、1500、1623；
- `figures/fill_mass_stability.png/.pdf`：Fill、质量、Mach 和 epsilon 时序；
- `figures/key_interface_states.png/.pdf`：初始、停止前和停止状态的俯视/中心截面；
- `output/<run-id>/interface_state_audit.csv`：关键 VTI 的最小 epsilon 位置；
- `parameters.txt`、`run_manifest.txt`、`run.log`：参数、命令和结束状态；
- `postprocess_step6E.py`：只读 VTI/CSV 后处理。

用户要求的“液体进入交汇区”和“侧槽填充”截图没有生成，因为对应物理里程碑未发生。报告以初始、step 1500 和失败停止场替代，避免用时间标签伪装未达到的填充状态。

## 7. 结论与停止点

真实 OpenLB FreeSurface 已接入显式 SIM-EC1XT240 正交交汇结构，几何、表面张力场、定性润湿壁、体积分数统计和 ParaView 输出均实际运行。短程数值推进正常，但正式基准在首次界面 cell 转换附近出现负液相体积分数，并且没有净填充。因此：

1. FreeSurface 基准尚未通过；
2. 接触角没有可校准的本地 API，不能判为定量物理一致；
3. 界面局部出现非物理状态，质量总体尚未爆炸，但不能继续解释后续填充；
4. 当前结果不能宣称符合 STEP 6-D 的填充路径预测。

本轮按要求停止，不扩大区域，不加入动态压头、参数扫描或其他物理模型。

Historical internal directory names such as `stage3_ex240_local` are retained for reproducibility. The correct physical/model designation is **SIM-EC1XT240**.

# SIM-EC1XT240 STEP 5.5 ParaView几何与材料场可视化检查

> Historical internal directory names such as `stage3_ex240_local` are retained for reproducibility. The correct physical/model designation is `SIM-EC1XT240`.

## 结论

本轮几何与材料场可视化检查**通过**：真实OpenLB核心材料场符合240 nm周期、
`60 nm + 120 nm + 60 nm`横向布局和100 nm槽深；solid与fluid区域连续，没有检测到孔洞、
多余solid层或x周期裂缝。首次转换的材料变化方向也与压头下移一致。

这只是几何人工审核候选，不改变STEP 5数值验收结论。STEP 5正式结果仍为FAIL
（转换瞬间Mach/rho异常且`R_geom>1e-3`），因此**当前仍不得进入STEP 6**。

## 独立导出与数据来源

- run-id：`step5_geometry_visualization_v1_20260908`；
- 独立导出程序：`step5_geometry_visualization_export.cpp`；
- 命令：`mpirun -np 1 ./step5_geometry_visualization_export`；
- OpenLB：`5953d8a-dirty`，单MPI rank；
- STEP 5冻结程序和既有结果未修改；
- 重放仅到首次转换step 3595，未继续运动、未执行STEP 6；
- 导出退出码0表示三套可视化成功生成以及几何/link审计通过，不表示STEP 5流动验收通过。

## ParaView输出文件

在`output/step5_geometry_visualization_v1_20260908/vtkData/`中直接打开：

- `state_initial.pvd`：step 0，`h=75 nm`；
- `state_pre_conversion.pvd`：step 3594，`h=72.5005751 nm`；
- `state_post_conversion.pvd`：step 3595，`h=72.4989847 nm`，首次转换并完成一个时间步；
- 对应`data/*.vti`：每套包含`material`、`rho_lattice`、`velocity_m_s`和`pressure_Pa`。

连续压头边界另存为：

- `state_initial_continuous_punch_nm.vtp`；
- `state_pre_conversion_continuous_punch_nm.vtp`；
- `state_post_conversion_continuous_punch_nm.vtp`。

VTI/OpenLB坐标单位为m，连续压头VTP为便于尺寸审核采用nm。手动叠加时需对VTI使用
`Transform: Scale=(1e9,1e9,1e9)`；本轮ParaView截图已按此处理。

已生成的人工检查图：

- `initial_xz_paraview.png`；
- `pre_conversion_xz_paraview.png`；
- `post_conversion_xz_paraview.png`；
- `initial_xy_z100nm_paraview.png`。

## Lattice与尺寸

|项目|实际定义|
|---|---:|
|核心lattice|`48 × 48 × 40` cells|
|dx|`5 nm`|
|核心x/y节点中心|`2.5–237.5 nm`|
|核心z节点中心|`-2.5–192.5 nm`|
|x物理周期|`240 nm`|
|y范围|`240 nm`，两端为Zou/He压力面，非周期|
|OpenLB overlap|3 cells；VTI extent含overlap，材料统计只含core|
|左半凸台|12 cells = `60 nm`|
|中央沟槽|24 cells = `120 nm`|
|右半凸台|12 cells = `60 nm`|
|槽深|20 cells = `100 nm`|

初始连续壁面为凸台底面`z=75 nm`、槽顶`z=175 nm`，基底有效半格壁面为`z=0`。
转换前连续壁面为`72.5005751/172.5005751 nm`，转换后为
`72.4989847/172.4989847 nm`。

必须区分连续Bouzidi壁面和体素材料面：首次转换后新solid节点中心位于
`z=72.5/172.5 nm`，其体素下表面在`z=70/170 nm`；实际流固交点仍由Bouzidi q描述，
位于`z≈72.498985/172.498985 nm`，不能把体素面当作实际壁面。

## 材料统计

|状态|material 1|material 2|material 3|material 4|material 5|fluid合计|
|---|---:|---:|---:|---:|---:|---:|
|初始|55,200|2,304|32,256|1,200|1,200|57,600|
|首次转换前|55,200|2,304|32,256|1,200|1,200|57,600|
|首次转换后|52,992|2,304|34,560|1,152|1,152|55,296|

首次事件增加2304个material 3节点：凸台底面`iz=15`有1152个，槽顶`iz=35`有1152个；
其中material 1转solid 2208个，两端压力材料4/5各转solid 48个。数量与刚体平移几何预测一致。

## 几何、连通性和周期检查

自动逐cell检查结果：

- 三个状态相对解析材料定义的mismatch均为0；
- fluid hole计数均为0；
- x=0与x=47周期对应面的材料不匹配计数均为0；
- 三个状态均恢复192条跨x周期固壁link；
- invalid q和false-solid link均为0；
- 固体压头通过顶部backing及两侧凸台保持连续；
- 基底上方流体在x方向连续，并与中央槽内空间连通；
- 左右半凸台跨周期拼接后形成120 nm完整凸台，没有裂缝。

ParaView的x-z截面与x-y、`z=100 nm`平面检查与上述逐cell审计一致：红色material 3形成
连续带槽压头，蓝色fluid占据凸台间隙和槽内区域，灰黑material 2形成单层固定基底。
首次转换后solid只沿压头向下的方向增加一层，没有错误孔洞或反向`solid -> fluid`。

## 人工审核结论与限制

当前可确认：OpenLB实际使用的lattice几何、材料编号、连续压头位置和首次材料转换位置与
SIM-EC1XT240局部设计几何一致。四张ParaView截图已完成内部人工目视检查；仍建议用户或老师
直接打开PVD/VTP，使用`Slice`、`Threshold(material)`和`Transform`复核后给出最终人工签字。

本检查不验证转换population闭合、质量重分配、Mach、rho或完整10 nm运动。鉴于STEP 5正式
数值报告仍为FAIL，即使几何人工确认通过，也必须先修复并重新通过STEP 5，方可进入STEP 6。

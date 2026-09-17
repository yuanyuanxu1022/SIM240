# 阶段一 dx=5 nm 质量与双截面通量接入报告

## 修改与保护范围

仅修改 `stage1_mass_flux_audit/`，新增 `dx5Integrated.cpp` 与 `Makefile.integrated`。原 `case.h`、`grooveDns.cpp`、README、`../tmp/`、阶段二和阶段三目录均未修改；旧测试和结果保留。

## 一致性核对

独立程序直接复用 `auditCase.h` 的 `createMesh/prepareGeometry/prepareLattice/setInitialValues/getResults`，因此 dx=5 nm、600 nm 横向条带、120 nm 墙/槽、65 nm 流体高度、Ly=240 nm、y 周期、x/z BounceBack、rho=1000、nu=1e-6、tau=1、dt=4.16667e-12 s、+y 体力 1e8 m/s²及原 B_yy 公式均保持一致。当前 material 1 core-cell 数为 32928；此前 30576 与 32928 属于不同几何/节点归属口径，不能仅凭总节点数判定等价，本次以实际 `auditCase` 材料场为准。

## 真实时间循环接入

每步执行 `collideAndStream()` 后，调用原 `getResults()`，随后只读遍历各 cuboid 的 core cells，统计 material 1 的液体质量、体积、密度偏差和 y=60/120 nm 两截面 Qy。统计不修改 lattice。overlap 和周期端点均排除；截面每节点面积为 dx²。

## 短测试与正式运行

- 编译：`make -f Makefile.integrated`，exit=0。
- 短测试：`short_diag_dx5b`，约10步，成功，诊断不引入异常。
- 正式 dx=5：run-id `dx5_formal_20260905`，单 MPI rank，按原 `MAX_PHYS_T=3e-7 s` 和 Qy 收敛判据运行。
- 收敛于 step 3909，物理时间 `1.62875e-08 s`，程序 exit=0。

## 结果

|指标|结果|
|---|---:|
|B_yy|112.4366373 nm²|
|流体节点数|32928|
|离散流体体积|4.1160e-21 m³|
|流体质量最大绝对相对漂移|7.16e-13|
|流体区域最大密度偏差|1.806e-11|
|Qy 截面 1（y=60 nm）|4.38502885e-16 m³/s|
|Qy 截面 2（y=120 nm）|4.38502885e-16 m³/s|
|截面相对差异|0（输出精度内）|
|原体积积分 Qy|4.38502885e-16 m³/s|
|截面与体积积分差异|约 1e-30 m³/s，输出精度内一致|

正式诊断 CSV：`output/dx5_formal_20260905/mass_flux_diagnostic.csv`；运行日志：`formal_run.log`。

## 尚未完成

本轮按要求未运行 dx=2.5 nm 和 1.25 nm，因此三网格质量漂移、通量平衡和正式 GCI 仍未完成。当前只能确认 dx=5 nm 粗网格的真实时间循环诊断已接入并复现原 B_yy。

## 结论

阶段一 dx=5 nm 的独立质量/通量诊断接入和收敛复现完成；流体质量漂移和两截面通量差异均处于数值舍入量级。该结论不外推至尚未运行的细网格，也不把最大密度偏差称为质量守恒误差。

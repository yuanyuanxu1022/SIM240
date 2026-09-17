# SIM-EC1XT240 ParaView汇报数据索引

本目录中的编号目录是指向原始`vtkData/`的符号链接。原始结果没有移动、复制或修改；请进入相应编号目录打开下列`.pvd`文件，不要单独复制`.pvd`，因为它需要同目录中的`data/`。

|编号|用途|打开的PVD|末态|主要变量|
|---:|---|---|---:|---|
|01|静态几何与material|`01_geometry_h65/openlb_static_geometry.pvd`|0|material、rho、velocity|
|02|h=65 nm单相y向输运|`02_single_phase_h65_y/sim_ec1xt240_h65_y.pvd`|2255|material、pressure_Pa、velocity_m_s|
|03|0°方向结构|`03_direction_0deg_y/sim_ec1xt240_angle0_y.pvd`|最后一帧|material、pressure_Pa、velocity_m_s|
|04|45°方向结构|`04_direction_45deg_y/sim_ec1xt240_angle45_y.pvd`|最后一帧|material、pressure_Pa、velocity_m_s|
|05|90°方向结构|`05_direction_90deg_y/sim_ec1xt240_angle90_y.pvd`|最后一帧|material、pressure_Pa、velocity_m_s|
|06|直角交汇结构|`06_right_angle_h65_y/sim_ec1xt240_right_angle_h65_y.pvd`|2406|material、pressure_Pa、velocity_m_s|
|07|100°接触角基准|`07_contact_angle_theta100/phasefield_contact_angle.pvd`|6000|phase_field_phi、pressure_lattice、velocity_lattice、chemical_potential|
|08|Laplace液滴基准|`08_laplace_R16/phasefield_laplace.pvd`|4000|phase_field_phi、pressure_lattice、velocity_lattice、chemical_potential|

## 推荐打开顺序

1. `01_geometry_h65`：导出x-z与x-y材料场；
2. `02_single_phase_h65_y`：导出速度Magnitude、Glyph或Stream Tracer；
3. `03`、`04`、`05`：分别导出相同切片、相同色标的方向性对比；
4. `07_contact_angle_theta100`：使用`phase_field_phi`和`phi=0.5` Contour；
5. `08_laplace_R16`：导出`phase_field_phi`、`pressure_lattice`及中心压力剖面；
6. 如果用直角结构代替方向性对比，则打开`06_right_angle_h65_y`。

建议每次只加载一个编号目录中的PVD，导出后删除Pipeline中的数据，再打开下一项，以避免不同算例时间轴合并。

## 注意

- 01～06属于SIM-EC1XT240显式几何结果；07～08是独立相场最小基准，不使用目标几何。
- 07～08的压力为格子单位，不能标为Pa。
- 方向性三图必须使用相同切片位置、相机、色标范围和截图尺寸。
- 符号链接依赖当前项目绝对路径；不要把本索引目录单独移动到其他机器。

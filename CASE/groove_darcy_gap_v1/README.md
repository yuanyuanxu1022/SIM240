# GDI 宿主的间隙字段与连续性接入分支

本分支从已运行的 `CASE/groove_darcy_static_v1/application/grooveDarcyStaticFoam.C` 最小接续，使用同一 `grooveDarcy` 子类及标准 `porosityForce`。原宿主、原协议及 `GDI01_v1_20261030_01` 保留。本分支名为 `grooveDarcyGapFoam`，不继承旧GDI01的PASS。

接入范围和假设见[协议说明](common/PROTOCOL.md)。本分支仍是全充液、单相、固定参考网格上的无惯性总Darcy平均模型，不是nanrPrint的液气VOF或运动网格改造。

## 已接入的量

宿主在创建多孔模型前读取并注册当前 `mesaGap`，另读 `previousMesaGap`；两者单位均为m。`gdiProperties`指定两快照间隔 `gapDeltaT`（s）、固定网格厚度 `referenceThickness`（m）和 `gapEpoch` 标识。示例见 [gapProperties.fragment](examples/gapProperties.fragment)、[mesaGap](examples/mesaGap)、[previousMesaGap](examples/previousMesaGap)。它们只是配置示例，不是正式计算发布包。

```text
H = mesaGap + (grooveWidth/period)*grooveDepth
Hdot = (mesaGap - previousMesaGap)/gapDeltaT
W = H/referenceThickness
```

`grooveDarcy`直接消费已注册的当前间隙，计算K与D=H/K；宿主不另写一套K公式或从结果表注入D。当前间隙在一次压力—速度外迭代中保持不变，H、Hdot和系数属于同一快照。

## 连续性和实际面流量

固定参考网格厚度为b0，单元体积为b0乘平面面积。需要满足：

```text
Hdot + div_xy(H U) = 0
sum_outward_Q_cell + (Vcell/b0)*Hdot_cell = 0
Qface = (Hface/b0)*(Uface · Sface)
```

压力—速度分裂继续采用原生porosityForce标量矩阵与外迭代，但预测通量及压力Laplacian都乘相同的面权重W。压力矩阵整体取负形成正对角，对应守恒通量为 `phiHat + pressure.flux()`。不能把未加权 `U·Sf` 当成间隙变化后的实际排液量，也不能只更新D而沿用div(U)=0。

耗散积分按当前液体体积而非参考网格体积加权；压力功含边界功和储液变化项。该代码路径需后续流场验证，本轮的原生矩阵/通量检查不代替求解收敛、动态能量或载荷精度验证。

## 检查与执行边界

`bash Allwmake`只编译独立宿主。`python3 -B scripts/check_assembly.py`创建新的软件测试夹具并仅运行 `-auditOnly`：检查实际字段到阻力、储量到矩阵源、面权重到压力算子/校正通量，以及H=b0、Hdot=0时与保存GDI01装配的一致性。旧测试输出不覆盖，每次使用新目录。

软件测试使用明确标注的合成间隙与快照间隔，不是用户采用的闭合速度、时长或正式工况。审计会以指定试探压力求一次矩阵面通量，随后恢复零初场；没有压力solve、物理时间推进或挤压流场。

程序的显式 `-solve`分支可处理一份已给定的快照，要求独立GAP01前缀身份；没有自动时间循环、没有从模具位移推断间隙、没有正式执行合同或新的计算启动授权。本轮不交付正式启动命令。实际时间序列、停止条件、边界和独立流场验收须按选定目标另行准备。

本轮完整记录：[接入报告](../../docs/reports/Groove_gap_host_integration_20261105/REPORT.md)。

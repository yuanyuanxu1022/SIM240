# 实际 OpenFOAM 宿主的间隙字段与连续性接入

日期：2026-11-05。作者内部AI辅助开发与检查记录；按scientific-writing技能组织证据和边界，作者/导师负责最终科学采用。用户要求“针对实际使用的OpenFOAM宿主，核对并接入间隙字段及相应连续性方程”，随后表示忘记宿主名称。

**结论：已依据实际运行记录确定宿主为grooveDarcyStaticFoam，并在独立新分支grooveDarcyGapFoam中完成间隙字段、储液变化与加权压力/通量的接入。Foundation13实际编译通过，12类原生装配/算子检查得到预期结果；固定间隙退回保存的GDI01矩阵。没有求解新的流场、推进物理时间或验证动态荷载/排液精度。**

## 1. 宿主身份与保护范围

本项目已有的真实运行是 `GDI01_v1_20261030_01`，源码入口 [grooveDarcyStaticFoam.C](../../../CASE/groove_darcy_static_v1/application/grooveDarcyStaticFoam.C)，实际结果及外部验收见[GDI01报告](../GDI01_results_20261030/REPORT.md)。它通过标准porosityForce调用grooveDarcy，而非仅在外部填入阻力数字；这使它成为本轮接续对象。不是由旧README中“未运行”的准备快照推断当前状态。

nanrPrint是另一套参考液气VOF算例，不能默认为当前全充液单相平均模型的实际宿主。本轮只读其参考入口用于辨别，不改其源码/字典，不下载或执行参考Allrun，不转换研究路线。

新实现目录：[CASE/groove_darcy_gap_v1](../../../CASE/groove_darcy_gap_v1/README.md)。原GDI宿主、子类库、协议与结果共288项指定旧文件哈希保持不变，见[preservation_verification.json](preservation_verification.json)。新分支独立编译、独立测试输出、独立GAP身份，不能继承GDI01的数值PASS。

## 2. 物理接口与实际代码

沿用全充液、牛顿、无惯性总Darcy平均模型。U为液体体积平均速度，K为深度积分导度(m³)，H=h+(w/P)d_g，J=HU，D=HK⁻¹。子类包含总未解析壁阻，宿主没有再叠加厚度剪切或第二份Darcy阻力。

新宿主在创建porosityForce之前读取并注册当前 `mesaGap`，同时读取 `previousMesaGap`、严格正且带时间单位的 `gapDeltaT` 和 `gapEpoch`。同一网格下，槽深/槽宽/周期保持不变，故

\[
H=h+(w/P)d_g,\qquad
\dot H=(h^{new}-h^{old})/\Delta t.
\]

当前h被原grooveDarcy实际读取，用于K和D；宿主不再写K公式，也不把检查器的解析K注入实际阻力。H、Hdot、D和所有通量属于同一快照；外迭代期间冻结间隙。实际快照/间隔的物理来源需要调用方提供，字段存在、单位正确不证明它们来自正确的模具运动。

最小改动见 [host_changes.diff](host_changes.diff)；完整实现见[新宿主源码](../../../CASE/groove_darcy_gap_v1/application/grooveDarcyGapFoam.C)。原/V2的公式及舍入系数均未改变。

## 3. 连续性必须与固定参考网格一起换算

采用原GDI参考网格，厚度b0=125nm、平面24×48µm、512单元。b0是网格几何量，当前储液高度H是物理模型量，二者可以不同。

\[
\dot H+\nabla_{xy}\cdot(H\mathbf U)=0,
\quad
Q_f=(H_f/b_0)\,(\mathbf U_f\cdot\mathbf S_f),
\]
\[
\sum_{f\in\partial c} Q_f + (V_c/b_0)\dot H_c=0.
\]

因此原生网格上的方程是 `div((H/b0)U)+Hdot/b0=0`。不能沿用div(U)=0，也不能直接把参考网格上的U·Sf当实际排液。

实际装配如下：W_face=interpolate(H/b0)，phiHat=W_face*flux(HbyA)，压力矩阵整体乘−1：

```cpp
fvScalarMatrix pressure
(
    -fvm::laplacian(faceWeight*fvc::interpolate(rAU), p)
 == -fvc::div(phiHat) - Hdot/b0
);
// This matrix has the negative-Laplacian sign.
phi = phiHat + pressure.flux();
```

压力算子及校正通量使用同一面权重。单元/全局守恒诊断加入储液变化，间隙减小要求净外排液。耗散从参考体积换算到当前液体体积，压力功同时包括边界功与储液变化项；这部分只完成代码接入和范围核对，没有新流场或动态能量验收。

本机头文件为编译依据；同时查阅Foundation13官方[有限体积Laplacian接口](https://cpp.openfoam.org/v13/fvmLaplacian_8H_source.html)和[fvMatrix接口](https://cpp.openfoam.org/v13/classFoam_1_1fvMatrix.html)。接口文档不是该新分支精度证明。

## 4. 实际编译与不求解检查

编译产物为 `CASE/groove_darcy_gap_v1/build/bin/grooveDarcyGapFoam`，本机Foundation13、g++13.3.0。子类复用原共享库的独立复制件。源码、二进制及复用库指纹见[source_manifest.json](source_manifest.json)。本轮原生检查只使用 `-auditOnly`，没有调用压力solve或推进时间。

|检查|已完成的直接证据|边界|
|---|---|---|
|当前间隙→实际阻力|原公式、V2、均匀/非均匀h下，从原生模型力响应恢复D，与独立公式逐单元对应|验证接入和单位，不验证原/V2准确性|
|储液变化→压力矩阵源|6个正常软件夹具共3072个单元，源逐单元等于−Hdot*Vcell/b0|是装配源项，不是已求得的净排液|
|闭合/开启符号|均匀闭合、非均匀闭合和非均匀开启分别检查|测试参数为合成输入，不是用户采用的闭合速度/时长|
|面权重→压力算子/通量|6个正常夹具共5856条内部面，按几何/原生rAU独立重算矩阵系数与指定试探压力的面通量|试探压力未求解，不作流场结果|
|固定间隙退回原实现|H=b0、Hdot=0时与保存GDI01审计的动量对角、压力对角/源、rAU逐单元对应|这是矩阵回归，不是重跑GDI01流场|
|非法输入拒绝|当前间隙负、前一间隙负、错误间隙单位、零间隔、错误参考厚度、未使用间隙场模式，6类均按具体原因拒绝|非零退出必须匹配预定错误，不把任意崩溃当通过|

共12类得到预期结果。详细命令、退出和数据指纹见[assembly_checks.json](assembly_checks.json)、[verification.json](verification.json)，原始正常/拒绝日志在logs/。本轮实际装配调用次数和标量/面核对数量不是独立物理样本数。

合成闭合例的储液体积变化率约−9.216e-18m³/s，因此其守恒方程要求净外排液目标约+9.216e-18m³/s。**本轮没有求得实际出口流量，不得把目标值当作仿真结果。**

初次编译因使用本版本不存在的fvcInterpolate.H失败，改为本机surfaceInterpolate.H后编译通过；原失败日志compile_attempt1.log保留。第一次检查在准备夹具时发现模板已有polyMesh，复制规则修正为只覆盖独立新夹具内的网格，旧数据未改；该次未调用原生程序，失败日志checks_attempt1.log保留。最终成功记录为checks_attempt2.log和compile_energy_fix.log。没有改阈值追认失败，没有正式仿真重试。

## 5. 当前实现边界及最小后续

已完成的是“给定前后间隙快照→注册字段→K/D→一致储液/压力/面流量装配”。程序有显式求解单快照的代码路径，但本轮没有执行；输出目录编号也不代表推进物理时间。没有自动生成真实h(t)、时间循环、运动网格、液气VOF或净载荷精度证明。

当前边界仍为原GDI的x两端24/0Pa、y侧无通量、z为空方向；不能称为四边环境压力的真实压印验证。非均匀H下的通量重构、空间/时间误差、求解收敛、全边界收支、动态能量和荷载均需后续流场证据。代码中的原GDI残差/求解控制作为开发分支控制保留，不替代尚未制定的新科学验收协议。

最小下一动作是为这个新分支确定一个受控的流场验收范围，绑定当前源码/字段/间隔/边界，检查求得的压力、实际边界Q及储量收支；之后才考虑真实时间序列或其他边界。该建议不构成执行许可。本轮未给正式启动命令、未启动正式求解、未进入下一Gate、未改论文或拟合模型。

新分支状态：source_implemented=true，compiled=true，assembly_checked=true，formal_run_id=null，NUMERICAL_GATE=NOT_EVALUATED，RESULT_PASS=false，geometry_PASS=null，physical_validation=NOT_EVALUATED。旧GDI01既有PASS保持；原S4横槽1.328387035%>1%FAIL、S4_STAGE_ACCEPTED=false、reference_qualified=false、F04 OPEN、strict_error_bound/submission_ready=false及其他历史FAIL不变。0.625准备仍未完成/未启动，不自动恢复。

当前状态和交接同步至 `docs/reports/SIM240_AI_CONTEXT.md`、主交接及便携交接。无提交/推送。下一模型建议GPT-6.1 Sol｜High，用于新分支受控流场验收准备；公式/结论最终冻结或实质复杂矛盾仍另按Astra建议处理，未声称切换。

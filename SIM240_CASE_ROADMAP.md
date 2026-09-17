# SIM240 Case Roadmap

更新时间：2026.09.16

## 文档边界

本文件描述Case设计、科学问题和论文映射，不是计算协议，也不授权启动任何计算。`SIM240_First_Validation_Task_v2.1.md` 保持原样；涉及参数、网格、收敛标准或Case编号含义的变更，必须在后续独立协议中冻结。

现行Frozen Protocol对Case03/Case04的定义与本Roadmap存在差异。本Roadmap采用本次指定的新论文路线；在Case03或Case04实施前，必须先形成无歧义的新协议版本。

## 总体路线

```text
Case00
  ↓
Case01
  ↓
Case01a
  ↓
Case01b
  ↓
Case01c
  ↓
Case02
  ↓
Case03
  ↓
Case04
```

## Case总表

| Case | Case目的 | 科学问题 | 主要输出数据 | 对应论文章节 | 当前状态 |
|---|---|---|---|---|---|
| Case00 | 验证周期通信、材料overlap和壁面link实现 | 数值边界是否按预期安装，几何距离和周期接缝是否完整？ | candidate/installed links、q分布、fallback、异常link | 方法：边界实现与内部一致性 | **完成**：Bouzidi link审计通过 |
| Case01 | 建立平板Poiseuille数值基准 | LBM能否在已知解析解下正确预测通量、阻力和速度剖面？ | $J_y$、$R_J$、解析误差、velocity profile、L2、质量和Mach | **LBM数值验证** | **进行中**：边界审计通过；冻结参数下Gate1精度未通过；refinement诊断完成 |
| Case01a | 建立$H=175\,\mathrm{nm}$最大包络高度光滑参考 | EX240相对最大可用高度的阻力增量是多少？ | $R_{\mathrm{smooth},175}$、$J_y$、解析误差、剖面、阻力比 | **Smooth参考** | 未开始 |
| Case01b | 建立$H=125\,\mathrm{nm}$等体积/等截面积光滑参考 | 面积变化与沟槽拓扑对阻力的贡献能否分离？ | $R_{\mathrm{smooth},125}$、$J_y$、解析误差、剖面、阻力比 | **Smooth参考** | 未开始 |
| Case01c | 建立光滑薄膜LBM与经典润滑理论基准 | 光滑薄膜LBM结果是否与经典Reynolds润滑理论一致？ | $R_{\mathrm{LBM}}$、$R_{\mathrm{lub}}$、relative error、velocity profile、L2 error | **润滑理论验证** | 未开始；仅完成Case设计 |
| Case02 | 测量EX240真实周期结构的有效流阻 | 纳米沟槽拓扑如何改变沿槽方向的输运阻力与局部流场？ | $R_{\mathrm{EX240}}$、相对Smooth阻力比、速度、压力、剪切、耗散 | **EX240结构流阻** | 未开始 |
| Case03 | 判断周期尺度对表观流阻的影响 | 多大有限周期阵列才能代表目标结构的整体输运性能？ | $R_N$、相对变化、尺度收敛、必要时GCI/外推 | **周期尺度** | 未开始；定义需与新协议统一 |
| Case04 | 建立结构参数与流阻的定量规律 | 沟槽深度、周期、占空比和液膜高度如何控制有效流阻？ | 参数矩阵、$R^*$、灵敏度、标度关系或响应面 | **结构参数规律** | 未开始；定义需与新协议统一 |

## Case01c：Smooth thin-film lubrication benchmark

### 科学问题

在满足薄膜长宽比和低Reynolds数条件时，OpenLB-LBM给出的光滑薄膜水力阻力及速度分布，是否收敛到经典Reynolds润滑理论？

### 目的

- 建立LBM与Reynolds理论之间的定量基准关系；
- 检查薄膜极限下阻力与速度剖面的一致性；
- 为Case02中结构导致的阻力偏离提供理论参照。

### 必需输出

- $R_{\mathrm{LBM}}$；
- $R_{\mathrm{lub}}$；
- relative error；
- velocity profile；
- velocity L2 error。

### 启动前必须冻结

- 薄膜几何及长宽比；
- Reynolds润滑解采用的边界条件和驱动定义；
- LBM与润滑理论之间一致的流阻、流量和面积归一化；
- 网格族、$\tau$或碰撞模型、时间步及收敛标准；
- 误差阈值和质量守恒要求。

在这些内容冻结前，Case01c状态保持“未开始”。

## 论文组织关系

| 论文内容 | 支撑Case | 作用 |
|---|---|---|
| 方法与实现可信度 | Case00 | 提供边界安装和周期通信证据 |
| LBM数值验证 | Case01 | 解析Poiseuille基准与离散误差说明 |
| Smooth参考体系 | Case01a、Case01b | 提供最大高度与等体积两种结构对照 |
| 润滑理论验证 | Case01c | 建立LBM与Reynolds理论关系 |
| EX240结构流阻 | Case02 | 给出核心结构输运结果 |
| 周期尺度 | Case03 | 确定有限阵列或代表尺度影响 |
| 结构参数规律 | Case04 | 建立可推广的几何—流阻规律 |

## 科学与执行风险

1. Case01尚未在Frozen Protocol参数下通过精度Gate，不能把refinement诊断自动视为协议变更。
2. Case01c不是Case01的重复：Case01验证局部Poiseuille数值解，Case01c验证薄膜渐近理论及其适用范围。
3. Case03若只复制完全相同的严格周期单胞，$R_N$可能按构造保持不变，不能证明代表性尺度收敛。该Case必须明确研究有限阵列/入口效应、非周期边界或结构统计变化中的至少一种。
4. Case04参数扫描必须在Case02的基准定义、网格策略和阻力归一化稳定后进行，否则响应规律会混入数值误差。

## 当前项目位置

```text
Case00  完成
Case01  进行中：误差来源已诊断，协议层结论待定
Case01a 未开始
Case01b 未开始
Case01c 未开始
Case02  未开始
Case03  未开始
Case04  未开始
```

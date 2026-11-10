# 第二篇胶水候选与证据缺口

用户已澄清GHY是一款候选，还需另外寻找几款；本轮按此要求补找3款。检索/核对2026-10-21。以厂商原文为优先，辅以原始研究；不是采购清单、产品性能排序或完整材料数据库。历史资料版本不代表当前供货或配方不变，正式取值须确认准确后缀/配方与条件。

| 候选 | 黏度证据 | 条件/来源 | 第二篇用途建议 | 当前缺口 |
|---|---|---|---|---|
| GHY（用户样品名） | 实测8.72356–12.0967mPa·s；30–50s⁻¹子集均值11.7762 | 约25°C，用户GHY(3)单次升速扫描 | 有本地实测依据的首轮候选 | 品名/配方、重复性/本构适用范围、ρ、σ、两表面θ |
| mr-UVCur26SF | 厂家15±2mPa·s | 25°C；2022年8月厂家Inkjet Flyer，PDF第3页Properties before UV-curing表 | 与GHY量级接近的低黏度UV压印候选；厂家列无溶剂 | ρ、σ、实际基底/模具θ；剪切条件/该批曲线未取得 |
| PAK-01 | 厂家页面括注约60mPa·s；同时另列运动黏度50–65cSt | 东洋合成官方PAK系列页；该页未注明这一物性对应温度/剪切率 | 中黏度对照候选 | μ与ν单位须分开，不能把cSt直接当mPa·s；ρ、σ、θ、温度/具体配方仍缺；页面标研发中产品 |
| OrmoComp | 厂家2.0±0.5Pa·s，即2000±500mPa·s | 2021年1月厂家Hybrid Polymers Flyer，PDF第2页未固化液态材料表；该表未标温度/剪切率 | 高黏度备选；与GHY差约两个数量级，初轮不必直接纳入全部算例 | ρ、σ、θ、匹配温度流变与可比工艺；不与同表OrmoStamp混用 |

## 来源与定位

1. mr-UVCur26SF：[厂家2022 Inkjet Flyer](https://www.microresist.de/wp-content/uploads/2022/08/Inkjet_Flyer_Aug22.pdf)，第3页Product overview/Available viscosities measured at25°C，15±2mPa·s、solvent-free=yes。文本提取可读，网页截图请求超时，未声称截图目视核对完成。
2. PAK-01：[东洋合成官方材料页](https://www.toyogosei.co.jp/english/rd/uv-feature/uv-resine.html)，Properties of PAK-01。页面同时使用cSt和括注mPa·s，不能凭近似值反推出精确密度。
3. OrmoComp：[厂家2021 Hybrid Polymers Flyer](https://www.microresist.de/wp-content/uploads/2021/07/flyer_hybridpolymers_2021_kl.pdf)，第2页Liquid material before patterning process，OrmoComp列与单位Pa·s已核文本。不是把固化后模量当液态黏度。
4. Hiroshi Hiroshima与Hidemasa Atobe，Viscosity Measurement of Spin-coated UV Nanoimprint Resin，Journal of Photopolymer Science and Technology23(1):19–24(2010)，[DOI及出版社摘要](https://doi.org/10.2494/photopolymer.23.19)。本轮仅核出版社元数据和摘要：该研究报告PAK-01薄膜受涂膜厚度、时间/加热等影响，不能把这种现象直接迁移成GHY已验证结论；也不能把块体流变数据无条件当纳米液膜实测。

## 使用原则与下一动作

建议优先GHY、mr-UVCur26SF、PAK-01三款的参数补全；OrmoComp为扩展备选。三款不构成已经可运行的参数矩阵。先完成一套材料的两相K提取验证，再判断材料对照是否必要，不立即扩成全部胶水×全部几何扫描。

真实胶水对照需要各自自洽的μ、ρ、σ、润湿条件和相同温度/工艺状态；仅改变μ、固定σ和θ是“黏度敏感性”实验，不能冒称完整的不同商品胶对照。每款内分别做Kxx/Kyy成对比较，保持初始液气状态和驱动约定一致。归一化K的变化不预设只由黏度决定。

未取得的ρ、σ、θ明确记为缺失，不用通用ρ或水接触角冒填。必要时按明确理想假设先做方法基准，但材料名与真实预测声明需受限。本轮无采购、对外联系、源码/冻结参数修改、编译、OpenLB计算或数值Gate放行。

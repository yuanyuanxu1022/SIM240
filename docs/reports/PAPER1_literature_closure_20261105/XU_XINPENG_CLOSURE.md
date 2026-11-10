# 徐新鹏论文的闭环方式：姓名澄清后的补充

日期：2026-11-05（北京时间）。用户已明确原姓名应为“徐新鹏”。学校主页定位到广东以色列理工学院Xinpeng Xu，ORCID 0000-0002-3265-7678；其方向/共同作者与下列流体工作吻合。尚无证据确定老师具体指下列哪篇。不能混入农业或经济学同名作者。
身份来源：https://sites.gtiit.edu.cn/research/people/xinpeng-xu/ （本轮打开）。

## 1. 最适合学习独立检验：2012连续模型→2013分子动力学

Xu,X.;Qian,T.(2012). Thermal singularity and droplet motion in one-component fluids on solid substrates with thermal gradients. Physical Review E85,061603. DOI10.1103/PhysRevE.85.061603。
原始页面：https://journals.aps.org/pre/abstract/10.1103/PhysRevE.85.061603 。本轮读取出版商摘要，未取得全文，不能逐图审定。模型研究单组分液气体系中接触线附近蒸发/凝结引起接触角随壁温改变，进而引起液滴迁移，并用液滴尺度流体模型解释及比较热梯度/润湿梯度驱动。

Wu,C.;Xu,X.;Qian,T.(2013). Molecular dynamics simulations for the motion of evaporative droplets driven by thermal gradients along nanochannels. Journal of Physics: Condensed Matter25(19),195103. DOI10.1088/0953-8984/25/19/195103。
机构来源：https://researchportal.hkust.edu.hk/en/publications/molecular-dynamics-simulations-for-the-motion-of-evaporative-drop/ 。本轮完整读取机构摘要和书目信息，另核PubMed23552493；未取得正文图表。
作者明确用MD作为数值实验，进一步检验2012年连续模型：迁移朝温度降低方向，速度与温度梯度成正比，并检查尺寸、液气共存温度对迁移率的影响；约10nm液滴的尺寸/耗散相关结果是半定量一致。不能表述为新物理实验、完全精确一致、普遍的连续模型纳米适用性证明。两方法共享一定物理设定，独立性是建模尺度/方法层面，不是所有假设均独立。
归纳闭环：提出机制→可检验趋势→另一建模尺度检验→参数/耗散解释→限定一致程度。此归纳不是作者明说的“闭环”术语。

## 2. 最直观的实验—机制—结构对照：2014饼状弹跳

Liu,Y.;Moevius,L.;Xu,X.;Qian,T.;Yeomans,J.M.;Wang,Z.(2014). Pancake bouncing on superhydrophobic surfaces. Nature Physics10,515–519. DOI10.1038/nphys2980。
来源：https://www.nature.com/articles/nphys2980 ，开放正文https://pmc.ncbi.nlm.nih.gov/articles/PMC5444522/ ，预印本https://arxiv.org/abs/1406.3203 。本轮取得PMC正文初次响应及图1/图3相关文本、作者预印本摘要、Nature书目信息和贡献；后续PMC出现验证码，Nature正文跳转失败，不绕验证，不声称完成所有正文/补充图逐页检查。
论文观察到液滴无需完整回缩便以扁平形态离开表面；提出压入柱间液体的毛细能转为向上运动，并要求竖直回弹和横向铺展时间尺度匹配；比较锥形柱/直柱、柱距及撞击条件，检查何时出现/不出现。作者报告接触时间相较常规完全反弹约缩短4倍。徐是共同作者，不能说独立完成；主体是毫米液滴、微柱配合细表面纹理，不是矩形纳米沟槽压印。
归纳闭环：异常现象→机制与时间尺度条件→改变结构/撞击条件检验→出现与不出现的范围→设计意义。

## 3. 最适合学习方法文章结构：2025 DRD

Gao,M.;Li,Z.;Xu,X.(2025). Simulation method of microscale fluid-structure interactions: Diffuse-resistance-domain approach. Physical Review Fluids10,094001. DOI10.1103/8xz3-2r3b。
来源：https://journals.aps.org/prfluids/abstract/10.1103/8xz3-2r3b 。本轮读取出版商摘要及出版日期2025-09-02；arXiv2407.14291是2024起的预印本，不能当作另篇独立工作或只称未发表。
Onsager变分原理构造动态模型，结合流体界面的弥散界面表示和流固界面阻力系数平滑插值；先做多个基准检验，再做复杂微尺度流固问题展示。由于未取得正文，不列未经核实的基准名称、误差数、具体应用细节。
归纳闭环：具体建模困难→有热力学依据的方法→基准→复杂问题展示。不是要求SIM240改用此方法。

## 4. 同作者其他线索（未纳入核心结论）

Xu与Qian2012，Droplet motion in one-component fluids on solid substrates with wettability gradients, PRE85,051601，DOI10.1103/PhysRevE.85.051601。出版商摘要已核：速度—润湿梯度、滑移长度/初始液滴半径以及驱动力/黏性阻力平衡。不要与061603温度梯度文混淆。
Xu等2019嵌段共聚物薄膜缺陷消除与2010接触线滑移/相变文已定位，仅作后续备选，不声称已细读。

## 5. 对当前Paper1的建议

最有价值的不是照搬两相问题，而是学习“机制能提出什么预测、改变条件后怎样检验”。建议拟一个不扩大原科学范围的结论—证据表：

|待检验问题|所需证据/对照|当前口径|
|沿槽和横槽阻力为什么不同|同几何同驱动、方向K/流量和受控场对照|18几何36点是历史5nm回顾性样本|
|原公式/V2的预测是否可信|与独立解析沟槽参考比较，保留失败和边界样本|不能用同一V2输入的两个平均模型互证准确性|
|观察到的局部流动能否解释总阻力|总量积分/收支及几何控制；局部峰只作线索|本轮没有完成耗散机制验证|
|能否指导压印过程|需要压力/排液/过程输出及独立对照|现有单相输运不能直接预测真实填充时间或缺陷|

上述是候选证据组织，不是最终机制裁决、公式冻结或新计算协议。下一实际工作建议：整理已存在的图/数据对应上述哪一列，再决定最小补证；不把先选5/10/20%容限作为该整理的前提。

## 检索范围与读取限制

定向查询“徐新鹏 纳米”“Xinpeng Xu nanoscale wetting”“Xinpeng Xu contact line molecular”及以上精确题名。访问2026-11-05，非穷尽综述。2025DRD和2012/2013链主要为出版商/作者机构摘要层证据；2014有部分正文。未伪称全论文精读。
尝试通过公开arXiv/KAUST链接取DRD和051601 PDF，未在本次有界尝试中取得文件，结束本轮下载辅助进程；xu_sources目录为空。无付费/验证码绕过，无需用户提供账号。
本轮使用paper-lookup继续检索，沿用scientific-writing证据限定；辅助方法参考见REPORT.md的软件方法条目，不当作物理证据。
无仿真、编译、原生审计、拟合、门槛修改、提交或推送；无新run_id。原S4 FAIL、reference资格false、模型/物理未评价及submission_ready=false保留。

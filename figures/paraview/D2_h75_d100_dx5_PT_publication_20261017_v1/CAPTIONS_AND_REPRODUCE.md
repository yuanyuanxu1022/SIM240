# 沿槽/跨槽速度图：图注与复现说明

日期：2026-10-17。使用用户已指定的两组现有稳态数据，仅后处理。

## 正式交付入口

- 俯视对照：figures_v2/Fig_PT_velocity_XY_z37p5nm.png
- 剖面对照：figures_v2/Fig_PT_velocity_XZ_y120nm.png
- 同名 PDF 与 SVG 也在 figures_v2/，保留可编辑/嵌入的文字与标注；场图为栅格图，不声称全矢量。
- ParaView 场景：rendered_v4/matched_fields.pvsm；它包含原始 reader 与派生采样切面，组图的坐标、图例和文字由 assemble_figures.py 重现。
- 出图参数、原始 VTM 及其引用 VTI 的完整哈希、既有 result/独立退出/几何记录的哈希：rendered_v4/render_manifest.json。
- 图片文件哈希、像素与物理尺寸：figures_v2/figure_manifest.json；最终审查以本目录 QA_RECORD.json 为准。前一个自动 manifest 中 QA pending 是导出时状态，最终目视与数值检查另存，未回写冒充自动通过。

本目录 rendered、rendered_v2、rendered_v3、figures 是保留的开发中间结果；最终采用 rendered_v4 和 figures_v2。原始仿真输出未改写。

## 统一口径

两图各由 (a) P 沿槽与 (b) T 跨槽构成，均显示绝对速度大小 |u|，单位 m/s。采用同一 ParaView Viridis 256 级色表、线性范围 0–1.8×10⁻⁴ m/s，关闭自动重缩放。没有逐图除以最大值。

两档原始物理域液体点的最大速度为：
P=1.6571265587117523×10⁻⁴ m/s；T=8.874550985638052×10⁻⁵ m/s。
上限覆盖两者，且两方向体力加速度幅值均为 10⁵ m/s²。该范围仅针对本组，不推广到整个参数矩阵。

几何：周期240 nm、槽宽120 nm（x=60–180 nm）、h=75 nm、d=100 nm、网格5 nm。坐标轴标为nm，速度没有随坐标单位变化被缩放。

### 物性必须如实标注

这里沿用用户此前指定的 h75_d100_dx5_P/T 基准目录，不使用独立的 mu15_h75_d100_dx5_P/T 目录，也未把旧速度按15倍缩放。

记录中的 tau=1、dx=5 nm、dt=4.166666666666667×10⁻¹² s，按既定 BGK 换算式
nu=(tau-0.5) dx²/(3 dt)
得到 nu≈1×10⁻⁶ m²/s。结合该模型 rho=1000 kg/m³，动态黏度相应为1 mPa·s，而非后来提出的15 mPa·s。
这个黏度说明是与记录一致的单位推导；历史 run_manifest 未显式保存全部物性/源码绑定，因此不补造缺失历史。正文若讨论15 mPa·s结果，应另选对应现有档并重新确定色标。

## 图注：俯视对照

中文：固定间隙下 SIM-EC1XT240 周期沟槽的稳态速度大小，比较 (a) 沿槽+y驱动与 (b) 跨槽+x驱动。两图均在z=37.5 nm处取样，保持相同视野、空间比例和速度色标。白色虚线标出上方沟槽边缘x=60、180 nm在该平面的投影；此高度处两侧与中央均为液体，虚线不代表平面内固液界面。几何h=75 nm、d=100 nm、周期240 nm、槽宽120 nm，dx=5 nm。驱动加速度幅值相同，为10⁵ m/s²。颜色表示绝对速度大小，无逐图归一化。

English draft: Steady speed magnitude in the periodic SIM-EC1XT240 groove cell under (a) along-groove (+y) and (b) across-groove (+x) forcing of equal acceleration magnitude, 10⁵ m s⁻². Both panels sample z=37.5 nm and use identical physical extents and a common absolute-speed scale. Dashed lines mark the projected edges of the overhead groove at x=60 and 180 nm; they are not solid–liquid interfaces in this plane. The mesa clearance is h=75 nm, the recess depth is d=100 nm, the period is 240 nm, the groove width is 120 nm, and the lattice spacing is 5 nm.

## 图注：剖面对照

中文：上述两方向的同位置XZ速度剖面，均在y=120 nm处取样。灰色为固体模具；两图以相同空间比例显示并共用同一绝对速度色标。P图的+y驱动垂直进入纸面，符号⊗不表示平面内流线；T图的+x驱动向右。本图只展示速度空间分布，不据此宣称存在回流或已完成耗散机制验证。

English draft: Matched x–z sections of the steady speed magnitude at y=120 nm for (a) along-groove and (b) across-groove forcing. The solid mold is gray. Identical spatial aspect ratios and a shared absolute-speed scale are used. The +y drive in panel (a) points into the page (⊗), while the +x drive in panel (b) points to the right. These scalar sections do not by themselves establish recirculation or an energy-dissipation mechanism.

## 采样与显示方法

原始数据为点数据。为避免点材料插值和全点Threshold侵蚀半格边界，先以 ParaView/VTK 探针在物理域内的5 nm格点中心取样，再将每个样本显示在对应5 nm的半格边界单元中；标量为原速度矢量的模。

XY切面z=37.5 nm经过原始z节点；XZ切面y=120 nm在相邻y节点之间采用线性探针。运行时检查所有采样点有效，材料与已知半格几何完全一致。每个XY面2304个液体样本，每个XZ面1200个液体样本。该显示是分片常值的“采样格足迹”，不是体积平均，也没有增加物理空间分辨率、补做墙面速度外推或平滑细节。派生VTI只保存在本出图目录，不覆盖原始VTI。

两幅图的空间比例一致。渲染相机精确对应物理范围，Matplotlib只放置原始ParaView渲染图、校准坐标和文字。速度图不因照明或透明度改变；场图与图例使用同一实际RGB查找表。最终检查所有原始采样格中心，渲染颜色与预期色表颜色差异为0个8-bit级；灰色固体亦一致。原始VTM、引用VTI及已有结果证据的哈希在渲染前后相同。

## 审查结果与使用边界

- 两张PNG均为2400×1200、全不透明；均实际打开查看，坐标、色标、驱动、灰色固体与图例完整。
- 对全部文字检查画布边界，未发现截断；PDF的DejaVu字体已嵌入，页面为203.2×101.6 mm（工作尺寸）。
- 实际ParaView 8-bit Viridis查找表有2个极小的亮度反向阶差，最小约−2.83×10⁻⁴。保留此检查发现，不宣称严格灰度单调或完整色觉可访问性认证。
- 这里“出图完成”只指这一组通用论文初稿。目标期刊、实际版面宽度、最终字号和文件格式要求尚未锁定，不声称已满足特定期刊全部规范。
- 不更新整个D2矩阵验收，不改任何历史PASS/FAIL；无新OpenLB计算、编译、求解器或冻结协议改动。
- 不把单个局部速度比当作方向迁移率比，不把本图当作实验验证、液滴或动态压印验证。

## 复现

在本机项目根目录执行（这是复现说明，不是本轮新增仿真命令）。使用全新输出目录；脚本拒绝覆盖已有目录：

~~~bash
pvpython --force-offscreen-rendering figures/paraview/D2_h75_d100_dx5_PT_publication_20261017_v1/render_fields.py --output-dir figures/paraview/D2_h75_d100_dx5_PT_publication_20261017_v1/rendered_repeat1
~~~

随后：

~~~bash
/home/dell/miniconda3/envs/sim240-analysis/bin/python figures/paraview/D2_h75_d100_dx5_PT_publication_20261017_v1/assemble_figures.py --render-dir figures/paraview/D2_h75_d100_dx5_PT_publication_20261017_v1/rendered_repeat1 --output-dir figures/paraview/D2_h75_d100_dx5_PT_publication_20261017_v1/figures_repeat1
~~~

输入reader和payload必须保留。.pvsm不包含原始数据；原文件路径改变时需重新定位。依赖包括本机pvpython、已安装的paraview-publication检查脚本，以及sim240-analysis中的Matplotlib/Pillow。版本与脚本哈希均有记录。

## 软件与规范来源

使用本地 paraview-publication、scientific-visualization 与 matplotlib Skills辅助出图和审核。后两者的方法来源：
Kassis, T., Agarwal, V., He, Y., Patel, D., & Brueckner, A. M. (2026). Scientific Agent Skills: A Library of Procedural Knowledge for Research Agents. https://doi.org/10.48550/arXiv.2609.00065
书目信息已于2026-10-17核对arXiv当前记录；本条记录工具规范来源，不作为流动物理结论的证据。


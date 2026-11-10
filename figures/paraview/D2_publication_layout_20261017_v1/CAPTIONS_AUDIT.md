# 图注草稿与替代文字

供作者核对后使用；不是已经批准的投稿稿。以下编号为本图包临时编号，可随正文调整。对应证据与句子哈希见CAPTIONS_AUDIT.md、claims.csv和source_manifest.json；数据与版面已由AI工具核查，人工作者复核尚未记录。

## Figure 1 - XY velocity comparison

ZH: 周期沟槽单胞在相同体力加速度幅值10⁵ m/s²下的稳态速度大小，对比(a)沿槽方向+y驱动和(b)跨槽方向+x驱动。两图均取z=37.5 nm平面，共用线性绝对速度色标0–1.8×10⁻⁴ m/s，不进行逐图归一化。白色虚线表示上方沟槽边缘x=60和180 nm的投影，并非该液体平面内的固液界面。几何间隙h=75 nm、槽深d=100 nm、周期240 nm、槽宽120 nm，网格间距5 nm。 [claim:C001] [evidence:E001,E004]

EN: Steady speed magnitude in a periodic groove cell under (a) along-groove (+y) and (b) across-groove (+x) forcing of equal acceleration magnitude, 10⁵ m s⁻². Both panels sample z=37.5 nm and share a linear absolute-speed scale of 0–1.8×10⁻⁴ m s⁻¹, without per-panel normalization. White dashed lines mark the projected edges of the overhead groove at x=60 and 180 nm, not solid-liquid interfaces in this liquid plane. The mesa clearance is h=75 nm, recess depth d=100 nm, period 240 nm, groove width 120 nm, and lattice spacing 5 nm. [claim:C002] [evidence:E001,E004]

ALT: Two matched x-y speed maps with nanometre axes. The left map uses +y forcing and the right map +x forcing; dashed vertical lines identify projected groove edges, and one colorbar gives the common absolute-speed scale. [claim:C003] [evidence:E001,E004]

## Figure 2 - XZ velocity comparison

ZH: 沿槽(a)与跨槽(b)驱动下，在相同y=120 nm位置的稳态速度大小剖面。灰色区域为固体模具，黑线表示名义阶梯边界；两图保持相同空间比例，共用0–1.8×10⁻⁴ m/s的绝对速度色标。沿槽+y驱动垂直进入纸面，以⊗标示；跨槽+x驱动向右。该标量剖面不单独构成回流或耗散机制的验证。 [claim:C004] [evidence:E001,E004]

EN: Matched x-z sections of steady speed magnitude at y=120 nm under (a) along-groove and (b) across-groove forcing. Gray regions denote the solid mold and black lines the nominal stepped boundary. Both panels use identical spatial aspect ratios and a common absolute-speed scale of 0–1.8×10⁻⁴ m s⁻¹. The +y drive points into the page in panel (a), denoted by ⊗; the +x drive points to the right in panel (b). These scalar sections alone do not establish recirculation or an energy-dissipation mechanism. [claim:C005] [evidence:E001,E004]

ALT: Two x-z speed sections with identical geometry, axes and color scale. The stepped mold is labeled Solid. Direction labels distinguish into-page along-groove forcing from rightward across-groove forcing. [claim:C006] [evidence:E001,E004]

## Figure 3 - Height profiles

ZH: 沿槽驱动下两处高度速度剖面的取样位置与曲线。(a)在y=120 nm剖面内，橙色实线位于沟槽中心x=120 nm，蓝色虚线位于凸台下方x=30 nm；灰色表示固体模具。(b)对应的沿槽速度分量u_y随高度z的变化，保留有效液体取样点，排除混合材料边界点且不向名义壁面外推。颜色与线型共同区分两条曲线。两条曲线分别保留971和933个插值样本；这些样本并非独立网格节点或统计重复。本图未叠加平板理论解，不能仅由曲线形状或峰值差认定等效模型失效。 [claim:C007] [evidence:E003,E004]

EN: Sampling locations and height-dependent velocity profiles under along-groove forcing. (a) In the y=120 nm section, the orange solid line is at the groove center, x=120 nm, and the blue dashed line is beneath a mesa, x=30 nm; gray denotes the solid mold. (b) Corresponding along-groove velocity components u_y versus height z. Valid liquid samples are retained, mixed-material boundary samples are excluded, and the profiles are not extrapolated to the nominal walls. Color and line style redundantly distinguish the curves. The profiles retain 971 and 933 interpolated samples, respectively; these are not independent mesh nodes or statistical replicates. No parallel-plate reference solution is overlaid, so profile shape or peak differences alone do not establish failure of an effective model. [claim:C008] [evidence:E003,E004]

ALT: A left-hand geometry panel locates two vertical sampling lines. The right-hand graph plots along-groove velocity against height, distinguishing groove-center data by an orange solid curve and under-mesa data by a blue dashed curve. Excluded boundary samples are not replaced by zeros. [claim:C009] [evidence:E003,E004]

## Figure 4 - Cross-groove dissipation

ZH: 跨槽+x驱动下，y=120 nm剖面上的单位质量耗散率ε分布，沿用原场单位m²/s³，以独立线性色标0–32显示。灰色为固体模具，黑线为名义阶梯边界。图像采用与速度场相同的5 nm采样格足迹显示方法，而非直接沿用点材料Threshold产生的侵蚀边界。本图描述已有离散场的空间分布，未进行角点耗散的网格独立性或全域能量收支验证；不将局部亮区直接等同于已量化的额外阻力机制。 [claim:C010] [evidence:E002,E004]

EN: Mass-specific dissipation rate ε in the y=120 nm section under across-groove (+x) forcing, shown in the original units of m² s⁻³ using an independent linear scale of 0–32. Gray denotes the solid mold and black lines the nominal stepped boundary. The field uses the same 5 nm sample-footprint display as the speed maps, rather than the eroded boundary produced by point-material thresholding. This image describes the existing discrete field; neither grid-independent corner dissipation nor a full-domain energy balance is established, and local bright regions are not equated with a quantified additional-resistance mechanism. [claim:C011] [evidence:E002,E004]

ALT: An x-z map of dissipation under rightward forcing. The mold is gray and labeled Solid. A dedicated nonnegative colorbar in m²/s³ distinguishes this field from the speed maps; sampled variations remain visibly limited by the original lattice spacing. [claim:C012] [evidence:E002,E004]

## Shared display-method note

ZH_COMMON: 场图将原始点值或切面探针值显示在对应的5 nm半格单元足迹内，属于分片常值显示，不是体积平均，不增加计算分辨率，也不声称得到墙面耗散值。XY平面取原始z=37.5 nm节点，XZ平面在y=120 nm处取线性探针值；每幅XY图有2304个液体样本，每幅XZ图有1200个液体样本。所有原始VTK场、CSV及用户导出图保持不变。 [claim:C013] [evidence:E001,E002,E003,E004]

EN_COMMON: Field panels display original point values or section-probe values over their corresponding 5 nm half-way cell footprints. This piecewise-constant display is not a volume average, does not increase computational resolution, and does not assert a resolved wall dissipation value. XY panels use the native z=37.5 nm level; XZ panels use linear probing at y=120 nm. Each XY panel contains 2304 liquid samples and each XZ panel 1200 liquid samples. Original VTK fields, CSV files and user-exported figures are unchanged. [claim:C014] [evidence:E001,E002,E003,E004]

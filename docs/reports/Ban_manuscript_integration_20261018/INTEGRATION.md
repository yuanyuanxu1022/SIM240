# Ban 文献进入首篇稿件：修改记录与可用段落

日期：2026-10-18。工作稿，待作者审阅；不是投稿放行。使用 scientific-writing、scientific-critical-thinking 和 PDF 技能。仅本地处理既有材料，无新增联网检索、OpenLB 运行或数值结果复核，run_id 不适用。

## 1 这次实际改了哪里

已对 `../第一篇论文_第1章引言草稿_20261017.md` 做两处局部修改：¶2 在立方律公式前明确 w/P=1/2；¶3 的前两段改成受证据约束的 Ban 文献衔接。未修改后面的文献论证、结果数字、修正公式或参考文献编号。原引言备份为 `Introduction_before.md`。

原文“always as an input”覆盖过宽，且从“交换两个分量”推导“此前未验证、因此构成创新”不成立。现改为：在所核的 Ban 模型中 K 被给定，用于宏观填充；其中毛细压力图不能作为 K 主值校核。这是本次原页检查支持的范围，不推广成全球无人验证。

## 2 原页支持与获取状态更新

Ban 2020 期刊PDF现已取得。p.022601-3–4，式(8)–(10)给定方向渗透率；p.022601-6，式(19)/Fig.7对照的是毛细压力表达与Surface Evolver结果。[claim:C001] [evidence:E001]

Ban 2021 期刊PDF现已取得。p.012601-3，式(1)(2)的U为深度平均速度，K_c=H₀²/12，式(8)–(10)给定线槽闭合；同页明确正交方向交换分量，Fig.2给出不同图案区域。[claim:C002] [evidence:E002]

本次目视核查期刊页支持学位论文相关公式与期刊模型的衔接，不能因此宣称所有章节逐字相同。尤其Ban 2021 p.012601-3将平板两个分量说成“相同”，并未写成学位论文p.67的“为1”；这说明版本差异需要逐项保留。[claim:C003] [evidence:E002,E003]

本目录 source_record.json 记录原件SHA256、原页、核查方式与AI核查状态；claims.csv绑定以下候选正文。人工作者尚未在本记录签署逐条复核，不能自动标记为投稿可用证据。

## 3 方法段候选文字：明确比较的是同一个量

### 英文，供作者决定插入方法章的位置

To compare the transport coefficients with those used by Ban and Bonnecaze, we distinguish their permeability from the depth-integrated conductance reported here. Denoting their dimensional permeability by κ, their normalization is k=κ/(H₀²/12). For the equal-width pattern, the mean fluid height is H_ref=h+d/2, and our conductance is K=H_ref κ. Substitution of their directional closures yields K∥=[h³+(h+d)³]/24 and K⊥={6[h⁻³+(h+d)⁻³]}⁻¹. Thus, the Ban formulation and the local-cubic-law baseline are the same comparator after conversion; they are not independent models.[claim:C004] [evidence:E002,E003]

### 中文解释

别人表里的K与我们表里的K单位不同；把它们换到同一口径，才知道比较的是阻力公式本身，而不是单位或平均方式不同。上段是原文定义加代数推导，不是原文逐字引文。

## 4 讨论段候选文字：讲清应用，不冒认填充验证

### 英文

The relevance to imprint filling is a local constitutive one. For a specified viscosity and pressure-gradient vector, the conductance tensor determines the in-plane flux. Replacing a closure by a resolved-cell estimate changes that flux prediction, but does not by itself determine the change in filling time or optimal droplet spacing. Those quantities also depend on the evolving gap, capillary boundary conditions and droplet coalescence. Application-level predictions would require coupling the coefficients to an appropriate macroscopic model and validating that coupling.[claim:C005] [evidence:E001,E002,E004]

### 中文解释

我们能说明“在同样推力下，公式把流量预测偏了多少”；不能直接说“Ban的填充时间错了多少”或“最优布滴间距一定偏大”。K改变后，压力场与前沿也会改变，不是替换一个比值就能得到完整结论。

## 5 局限段候选文字：宏观薄膜与槽尺度分开

### 英文

Scale separation between the film thickness and the macroscopic spreading length motivates a lubrication description at the field scale. It does not alone establish the accuracy of an independent-stripe cubic-law closure within a grooved unit cell. The present comparison evaluates that local approximation for a fixed, fully filled rectangular geometry. It does not address contact-line motion, partial filling, trapped gas, or a continuously moving template.[claim:C006] [evidence:E002,E003,E004]

### 中文解释

从远处看胶膜很薄，适合用薄膜模型；放大到单条槽以后，侧壁和空间内的速度变化仍可能重要。这正是首篇要隔离的问题，不能只凭几个几何比就宣布模型必然失效。

## 6 图表怎样借鉴，避免重复计数

Ban 2020 Fig.7采用数值预测与简化表达的对照图，但其变量是毛细压力。我们可借鉴其“同一物理量正面对照”的展示方式，而不能把该图移作水力验证证据。[claim:C007] [evidence:E001]

若现有结果章已有误差地图，不必再加重复图。最小安排：一张K模型值与数值参考值的对照图，区分沿槽/横槽并标单位；残差地图保留符号和采样点；数值不确定度只标实际有证据的位置。不能把两几何的网格差当全域统一误差条。

## 7 仍不能靠Ban支持的结论

- “行业普遍采用”“历来无人校核”“任意角旋转是我们首次证明”：本次来源不能支持。
- “引入修正后填充时间/布滴最优值必然改善”：尚未进行相应耦合模型检验。
- “所有误差唯一来自尖角”：当前方向K比较不能隔离唯一机制。现有第5章的该类论断不由本轮Ban核查获得支持；不能以另一种光滑几何的不同解析方法准确，就证明本模型误差只来自角点。需匹配几何/算子对照或动量、能量证据；12.3仍暂缓。本轮只记录，未修改第5章。
- “修正公式在连续域具有严格精度上界”：离散采样残差、内部留出成绩和连续域保证不同。后验选型亦须保留探索性质，本轮不复核或裁定V1/V2。

## 8 下一步与变更边界

请作者先审阅引言两处局部修改及上述方法/讨论候选段落，再按全稿结构决定是否插入，避免与已有方法定义重复。这里的人工作者审阅是工作稿状态说明，不阻止本轮已授权的局部写作。后续优先统一现有文献的结论—原页关系，不新增物理或长算。本轮保留所有历史PASS/FAIL，未改范围冻结卡、求解器、运行脚本或原始结果。

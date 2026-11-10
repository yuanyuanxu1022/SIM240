# Fig 7 / Fig 8 图注与数据记录（2026-10-18）

## 图号裁定

| 编号 | 内容 | 位置 |
|---|---|---|
| Fig 7 | `Fig7_error_vs_gap` | 第 5 章，紧随 5.A / 5.B，**误差地图的"为什么"** |
| Fig 8 | `Fig8_error_map` | 第 5 章，**误差地图的"是多少"** |

> 骨架原先给 Fig 7 预留了"误差图矩阵（d×h 轮廓）"，本次把它拆成两张：
> **B（error vs gap）用来解释机制，A（heat map）用来给全貌**。
> 顺序 B 在前：因为读者要先知道误差随哪个变量走，看热图才有意义。
> 若期刊限制图数，B 与 A 可合并为一张三面板图，但**不建议**——两者坐标不同，合并会削弱各自的说服力。

---

## 数据来源（可复算）

```
CASE/D_series/D2_groove_error_map/results/
  summary.csv            dx = 5 nm 的 18 档（9 P + 9 T）
  d75_summary.csv         6 档（3 P + 3 T）
  h25_summary.csv         6 档（3 P + 3 T）
  d120_summary.csv        6 档（3 P + 3 T）
  ────────────────────────────────────────────
  合计 36 档 = 每方向 18 档
```

⚠ **不要写 48 档**。48 是论文骨架 D2 **计划**的注册总数（含 μ 对照 2 档与斜槽 6 档），
那 8 档不在上述四个 CSV 中，**未参与本文误差统计**。

生成脚本：`figures/paper/make_fig7_fig8.py`（读上述四个 CSV，不手填任何数字）

误差定义：
$$E=\frac{K_{\rm stripe}-K_{\rm DNS}}{K_{\rm DNS}}\times100\%$$
其中条纹平均按式(1)：
$$K_\parallel=\frac{1}{12}\cdot\frac{h^3+(h+d)^3}{2},\qquad
K_\perp=\frac{1}{12}\cdot\frac{2}{h^{-3}+(h+d)^{-3}}$$
（单位 $10^{-27}\,$m$^3$，按单位宽度定义。）

---

## Fig 7 图注（英文）

> **FIG. 7.** Error of the stripe-average closure, Eqs. (1), against the resolved coefficients,
> as a function of the gap $h$, for each groove depth $d$. (a) Along the grooves, $K_\parallel$;
> (b) across the grooves, $K_\perp$. Note the logarithmic ordinate and the different vertical ranges.
> Along the grooves the error decreases with $h$ at most depths, while across the grooves it increases
> with $h$ at the deeper grooves, so the two components generally respond in opposite senses to the gap.
> **This is a prevailing trend, not a monotonic law**: the along-groove error rises from $139\%$ to
> $154\%$ between $h=25$ and $50$ nm at $d=100$ nm, and the across-groove error falls between
> $h=75$ and $125$ nm at $d=25$ and $50$ nm. All 36 sampled cases lie above zero, so the closure
> overestimates the conductance everywhere. Data: 18 geometries, 36 principal-direction cases at $dx=5$ nm.

## Fig 8 图注（英文）

> **FIG. 8.** The same 36 errors as a map over the sampled matrix of groove depth $d$ and gap $h$.
> (a) Along the grooves, $K_\parallel$; (b) across the grooves, $K_\perp$. Numbers are the error in
> per cent; each panel has its own colour scale, and the scales differ by nearly a factor of four.
> Hatched cells were not sampled: at $h = 25$ nm only $d = 25, 50, 100$ nm were computed.
> The along-groove error grows strongly with $d$ at fixed $h$; the across-groove error is far less
> sensitive to $d$ and varies more weakly with $h$. Neither dependence is monotonic across every
> sampled depth (see the counter-examples listed in the Fig. 7 caption); the map shows the overall
> pattern and the extremes, not a universal trend law.

---

## 两张图各自承担的论点（写作时不要混用）

| 图 | 说什么 | 不要用它说 |
|---|---|---|
| **Fig 7 (B)** | 沿槽与跨槽对 $h$ 的响应**大体相反**（但非处处相反，存在反例） | 不要用它给"误差多大"（纵轴是对数，视觉压缩） |
| **Fig 8 (A)** | 误差的**全貌与上限**（沿槽 205%、跨槽 54%） | 不要用它讲趋势（5×4 格看趋势不如折线） |

**Fig 7 能支持什么、不能支持什么（2026-10-19 收紧）**：

- **能支持**：两个分量对间隙 $h$ 的响应方向大体相反，且存在明确反例（见 Fig 7 图注）；因此**两个方向需要分别描述其误差及间隙依赖，不能用同一个相对误差函数完整刻画两者**。
- **不能支持**：由这些整体趋势去识别或排除某种局部物理机制的主导地位。"平均化效应"在本稿中没有可检验的数学定义，也没有独立的局部耗散或分段阻力分解证据；整体输运系数及其误差趋势是空间积分量，本身不含有误差来源的空间信息。
- **不能支持**：把这一现象**确定性归因于角部**。整体输运系数及其误差趋势是空间积分量，本身不含局部耗散、壁面牵引或分段阻力的信息；要做机制归属，需要独立的局部耗散分解或分段阻力证据，本轮未做。
- 正文 5.A 的相关表述应保持"候选解释"强度。

---

## ⚠ 本轮由这两张图查出的一个实质错误（2026-10-18）

画图时把 36 档误差按 $h$ 排列，才看出第 1 章 ¶5 有一段论证**与数据不符**。

**原表述**：
> "Because $H_{\rm ref}$ grows with $h$, the group $d/H_{\rm ref}$ shrinks **where the required correction grows**;
> the variable **runs opposite to the effect it is meant to absorb**."

**错在哪**：所需修正确实随 $h$ **变小**（$h$: 50→125 时所需修正因子从 0.653 升到 0.748，即修得越来越少），
而 $d/H_{\rm ref}$ 也随 $h$ 变小 ⇒ **两者同向**，不是"方向相反"。

**正确的说法（已改入正文）**：错在**跟随的强度**，不在方向。

| $d$ (nm) | 所需修正因子的变化倍数<br>($h$: 50→125) | V1 给出因子的变化倍数 | 放大 |
|---|---|---|---|
| 25 | 1.07 | 1.23 | 1.2× |
| 50 | 1.15 | 1.48 | 1.3× |
| 100 | 1.22 | 1.67 | 1.4× |
| 120 | 1.23 | 1.69 | 1.4× |

⇒ 指数接近 2，使 $d/H_{\rm ref}$ 的下降被放大，修正因子比实际需要**多变化约三分之一**，
于是**小间隙过度修正、大间隙修正不足**，残差在两者之间变号（$+38.6\%$ 就在大间隙端）。

**因此 V2 改用 $d/w$ 的真正理由**：$d/w$ 不含 $h$，把修正做成**与 $h$ 无关**，
主动放弃那 1.07–1.23 倍的弱依赖，换来不再放大它；代价是残余 $h$ 依赖 6–21 个百分点（已如实写入适用范围）。

**同步改动**：第 1 章 ¶5（英文正文）、PPT 第 8 页"为什么改用 d/w"一条。

---

## 版式记录

| 项 | 值 |
|---|---|
| 画布 | Fig 7: 7.0 × 2.95 in；Fig 8: 7.0 × 2.62 in |
| dpi | 400（png）；矢量 pdf/svg 同步输出 |
| 字体 | DejaVu Sans 8.5 pt（轴标签 8.2、刻度 7.4、图内注释 6.5） |
| 配色 | Fig 7 用 c-coral 单色系按 $d$ 深浅；Fig 8 (a) 暖色（沿槽）、(b) 冷色（跨槽），**两色标各自独立** |
| 边框 | 上/右边框隐藏，符合 Fig1/Fig4 既有样式 |

**注意**：Fig 8 两个面板色标不同（0–220 与 0–60），图注已明写"each panel has its own colour scale"。
**不要在正文里跨面板比较颜色深浅**，只能比较数字。

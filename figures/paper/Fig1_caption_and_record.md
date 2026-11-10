# Fig. 1 — Device and unit cell（图注与制作记录）

## 正式图注（英文，可直接放入正文）

**Figure 1.** Geometry of the imprint process and of the periodic unit cell used in the simulations.
(a) The J-FIL cycle: resist drops are dispensed on the substrate (a1), the patterned mold is pressed down and the resist fills the features while being squeezed out into the residual film (a2), and the film is cured under UV and the mold released (a3).
(b) Cross-section of one unit cell in the periodic limit. Rectangular grooves of width $w$ and depth $d$ are cut into the mold, leaving ribs that stand a distance $h$ above the substrate; the pattern period is $P$. The resist occupies the residual film under the ribs and the groove volume. The flow is solved in a fully filled domain, so no free surface is present in the calculations.
(c) Top view of the unit cell with the coordinate convention used throughout. The grooves run along $y$, so $K_\parallel$ denotes transport along the grooves and $K_\perp$ transport across them; the geometry is periodic in $x$ and in $y$. Values shown are those of the reference case, $P=240$ nm, $w=120$ nm, $h=75$ nm, $d=100$ nm.

## 中文对照（供老师审阅用）

**图 1.** 压印工艺与计算单胞的几何。
(a) J-FIL 循环三阶段：滴胶（a1）→ 模具下压、液体挤入槽内同时外排形成残膜（a2）→ UV 固化并脱模（a3）。
(b) 周期极限下单个单胞的横截面。模具上开有宽 $w$、深 $d$ 的矩形槽，槽间凸台距基板 $h$，图案周期 $P$。液体占满凸台下方的残膜与槽内体积；**计算域为全充液，无自由液面**。
(c) 单胞俯视图与全文坐标约定。槽沿 $y$ 延伸，故 $K_\parallel$ 为沿槽输运、$K_\perp$ 为跨槽输运；几何在 $x$、$y$ 两个方向均周期。图中数值为基准算例：$P=240$ nm、$w=120$ nm、$h=75$ nm、$d=100$ nm。

---

## 制作记录

| 项 | 内容 |
|---|---|
| 生成脚本 | `make_fig1.py`（matplotlib，纯矢量构造，无外部素材） |
| 输出格式 | `Fig1_device_and_unitcell.png`（2850×2220 px，400 dpi）、`.pdf`、`.svg` |
| 版面 | 双栏宽 7.16 in × 5.9 in，适合 A4 双栏或单栏缩放 |
| 字体 | DejaVu Sans（PDF 内嵌，跨平台一致） |
| 颜色 | 基板 `#CBCBCB`、模具 `#6E6E6E`/`#8A8A8A`、液体 `#9CCBE0`；灰蓝单色调，黑白打印可辨 |
| 几何依据 | `CASE/D_series/D2_groove_error_map/src/d2_groove_error_map.cpp`：`lx=ly=240 nm`、`grooveStart=60`、`grooveEnd=180` ⇒ $P=240$、$w=120$ |

## 与算例的一致性核对

| 图中标注 | 代码实际值 | 一致 |
|---|---|---|
| $P=240$ nm | `lx = ly = 240.0e-9` | ✅ |
| $w=120$ nm | `grooveEnd - grooveStart = 180 - 60 = 120` | ✅ |
| $y$ 沿槽、$x$ 跨槽 | 槽在 x 方向界定、沿 y 无限延伸（周期） | ✅ |
| 全充液无自由液面 | 单相求解，域内无气液界面 | ✅ |
| $d$、$h$ 为基准值 | 参数化：$h\in[25,125]$、$d\in[25,120]$，图示取 75/100 | ✅ |

## 审稿可能问到的点

1. **为什么 (a) 里画了液面，正文却说无自由液面？**
   → (a) 是**工艺过程**示意（有液面是事实），(b)(c) 是**计算构型**（全充液）。图注 (b) 已明写 "The flow is solved in a fully filled domain, so no free surface is present in the calculations." 这句必须保留。

2. **为什么 $h$ 标在凸台下方而不是槽底？**
   → $h$ 定义为**凸台与基板之间的残余间隙**，槽内高度是 $h+d$。这是本文与前人（Jain 的 $h$ 是间隙、$d$ 是特征高度）对齐的口径，图注已明确。

3. **能否只用单色？**
   → 可以。灰度下基板浅灰、模具中灰、液体浅蓝（灰度约 78%），三者可分。

## 后续可改项（暂不动，等定稿）

- 若投 Microelectronic Engineering（更短），可只保留 (b)(c)，(a) 移到补充材料。
- 若审稿人要求标注晶向/占空比，可在 (c) 加 $\varphi=w/P=0.5$。
- 目前 (a) 中液滴为球冠轮廓，未按真实接触角绘制（真实 θ≈15°，球冠会很扁平）。若要精确，需按 θ 重算轮廓。

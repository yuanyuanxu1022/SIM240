# FIG. 4 — 图注与制作记录

## 英文正式图注

**FIG. 4.** Resolved transport coefficients of the rectangular groove array at $P=240$ nm, $w=120$ nm. (a) Along-groove $K_\parallel$ (filled symbols, solid lines) and across-groove $K_\perp$ (open symbols, dashed lines) against groove depth $d$, at four residual gaps. (b) Anisotropy ratio $A=K_\parallel/K_\perp$ on a logarithmic ordinate; the dotted line marks $A=1$. Coefficients are given per unit width, in m³; division by the equivalent-volume height $H_{\rm ref}=h+\varphi d$ gives the three-dimensional permeability in m², consistent with the volume-averaged velocity $\bar u=J/H_{\rm ref}$ defined in Sec. II. Within the sampled depth range the $K_\perp$ curves in (a) are nearly horizontal: at fixed gap $K_\perp$ varies by at most 3.7% over the sampled depths (largest at $h=25$ nm, where the sampled depths are only $d=25$, $50$ and $100$ nm). The depth is the abscissa because it is the variable that the along-groove coefficient follows; the gap is the variable that the across-groove coefficient follows, and it enters only through the series label. The matrix is not a full rectangle: at $h=25$ nm only $d=25$, $50$ and $100$ nm were computed.

## 中文对照

**图 4.** $P=240$ nm、$w=120$ nm 矩形沟槽阵列的显式数值输运系数。(a) 沿槽 $K_\parallel$（实心符号、实线）与跨槽 $K_\perp$（空心符号、虚线）随槽深 $d$ 的变化，四个残余间隙各一组。(b) 各向异性比 $A=K_\parallel/K_\perp$，纵轴对数；点线标 $A=1$。系数按单位宽度定义，单位 m³；除以等体积高度 $H_{\rm ref}=h+\varphi d$ 即为三维渗透率（m²），与 Sec. II 定义体积平均速度 $\bar u=J/H_{\rm ref}$ 一致。在所采样深度范围内，(a) 中 $K_\perp$ 曲线接近水平：固定间隙时 $K_\perp$ 在已算深度上的变化不超过 3.7%（$h=25$ nm 处最大，该档仅算了 $d=25$、$50$、$100$ nm）。横轴取槽深，因为这是沿槽系数所跟随的变量；跨槽系数跟随的是间隙，只通过曲线的组别标签体现。矩阵并非完整矩形：$h=25$ nm 处只算了 $d=25$、$50$、$100$ nm。

---

## 一致性核对

| 项 | 值 | 来源 | 核对 |
|---|---|---|---|
| 数据点 | 18 档（每档含 P、T 各一） | `summary.csv`(dx=5) + `d75/h25/d120_summary.csv` | ✅ |
| $K$ 单位 | m³（单位宽度） | 与 Sec. II G 一致 | ✅ |
| 换算 | $K^{[\rm m^2]}=K^{[\rm m^3]}/H_{\rm ref}$，$H_{\rm ref}=h+\varphi d$ | 体积平均速度口径，见 Sec. II | ✅（2026-10-19 由 $K/P$ 订正） |
| 面板 (b) 纵轴 | 对数 | $A$ 跨 14 倍（1.09–15.45） | ✅ |
| 配色 | c-blue 单向渐变 | 颜色深浅 = 间隙大小（序数） | ✅ |
| 实/空心 | 实=K∥，空=K⊥ | 同一间隙共用颜色，靠填充区分方向 | ✅ |

## 图中支撑的正文数字

| 论断 | 数字 | 在图上的位置 |
|---|---|---|
| $K_\perp$ 对 $d$ 呈**弱依赖**（非零） | 已采样深度内最大变化 3.69%（h=25）；其余档 1.009–1.037 倍 | (a) 虚线接近水平 |
| $K_\perp$ 随 $h$ 强变化 | $2.14\times10^{-24}$ → $1.86\times10^{-22}$ m³，**87 倍** | (a) 四条虚线竖直间距 |
| $K_\parallel$ 随 $d$ 增长且依赖 $h$ | $h$=50/75/125 时 3.55/2.13/1.39 倍 | (a) 实线斜率随 $h$ 变缓 |
| $A$ 跨 14 倍 | 1.090（$h$=125,$d$=25）– 15.45（$h$=25,$d$=100） | (b) 上下包络 |
| $d\to0$ 时 $A\to1$ | $A=1.090$ | (b) 最下方曲线趋近点线 |

## 制作

- 脚本：`figures/paper/make_fig4.py`
- 输出：`figures/paper/Fig4_K_and_anisotropy.{png,pdf,svg}`，400 dpi，成品约 7.0 × 2.9 in（双栏宽）
- 迭代记录：初版 3 处标注压线（$K_\parallel$/$K_\perp$ 标签、量程说明），已移到空白区

## 一个刻意的设计选择（写论文时可解释）

图中**横轴统一取 $d$**，尽管 $K_\perp$ 对 $d$ 存在弱依赖（已采样深度内最大 3.69%）。这样做的理由：

1. 两个面板共用横轴，读者可以直接对照"同一个 $d$ 下 $K$ 与 $A$ 的关系"；
2. **$K_\perp$ 曲线接近水平，本身就是结论**——如果改成横轴取 $h$，$K_\perp$ 就会变成四条陡峭上升的线，反而看不出"对 $d$ 仅弱依赖"这件事；
3. 审稿人一眼能看到"虚线几乎不动、实线显著在动"，这是全文后续论证（两个分量的误差需分别描述）的图形基础。**注意：外观上的"不动/在动"只是图示；它不能识别误差的局部物理来源。**

**若审稿人要求**：可补一张横轴取 $h$ 的版本作为补充材料（`make_fig4.py` 改两行即可），但那会削弱主图的表达力，不建议作为主图。

## 2026-10-27 定点订正

对应当前中文导师审阅稿图2，文件名沿用旧Fig4。图内范围说明改为“over the sampled depths”，明确仅指各间隙已采样的槽深；图注列明h=25 nm仅计算d=25、50、100 nm。数据、单位、归一化与曲线不变。此次导出环境与检查见 `docs/reports/Paper_text_figure_corrections_20261027/REVISION_NOTE.md`；不表示期刊版式或科学验收通过。

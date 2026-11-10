# Fig. fRe — 图注与制作记录

> ## ⚠ 状态：历史过程材料，不作为正式定量验证图（2026-10-19 确认）
>
> 本图**不进入稿件正文**作为验证证据。理由：
> 1. 纵轴定义 $f\,Re=2\varepsilon r_h^2/K_\parallel$ 在 $K$ 取本文 m³ 口径时右端非无量纲；脚本实际使用的是 m² 量，图注未写清这一换算。
> 2. 灰带值 $f\,Re\approx14$ 与"typical tube value"标签缺少可核对的原始关联式来源。
> 3. 同一记录已承认：原开放槽关联式未取得、未逐式核对，因此不能据此宣称该关联式"失效"。
>
> 下面保留的英文/中文图注是**当时版本**，仅作历史过程记录。若将来要恢复为正式验证图，必须先解决上述定义与来源问题，另立证据，不得直接引用本图注。

## 英文正式图注

**FIG. fRe.** Failure of the open-groove resistance correlation on the present geometry. The ordinate is the product $f\,Re$ inferred from the resolved coefficients, $f\,Re = 2\varepsilon r_h^2 / K_\parallel$, where $\varepsilon=w/P=0.5$ and $r_h=2w\delta/(w+2\delta)$ are the porosity and hydraulic radius used by the open-groove correlation. For that correlation to hold, $f\,Re$ must be a function of the aspect ratio $\alpha=w/\delta$ alone, and therefore constant along each coloured series (fixed $\delta$). The inferred values instead fall by factors of $4$ to $41$ along each series as $h$ goes from 25 to 125 nm. The grey band marks the value $f\,Re\approx14$ typical of fully developed laminar flow in a rectangular duct. The dependence on $h$ is at least an order of magnitude stronger than the residual dependence on $\delta$.

## 中文对照

**图 fRe.** 开放槽阻力关联式在本几何上失效。纵轴为从解析系数反推的 $f\,Re=2\varepsilon r_h^2/K_\parallel$，其中 $\varepsilon=w/P=0.5$、$r_h=2w\delta/(w+2\delta)$ 是开放槽关联式所用的孔隙率与水力半径。若该关联式成立，$f\,Re$ 必须只是宽高比 $\alpha=w/\delta$ 的函数，因而在同一条彩色曲线上（$\delta$ 固定）应为常数。实测反推值却随 $h$ 由 25 nm 增至 125 nm 下降 4–41 倍。灰带标出矩形管内充分发展层流的典型值 $f\,Re\approx14$。$h$ 的影响比 $\delta$ 的残余影响至少大一个数量级。

---

## 一致性核对

| 项 | 值 | 来源 | 核对 |
|---|---|---|---|
| $w$ | 120 nm | `d2_groove_error_map.cpp`：`grooveEnd-grooveStart=180-60` | ✅ |
| $P$ | 240 nm | `lx=ly=240e-9` | ✅ |
| $\varepsilon=w/P$ | 0.500 | 计算 | ✅ |
| $r_h=2w\delta/(w+2\delta)$ | 35.3–80.0 nm（$d$=25→120） | 计算 | ✅ |
| **量纲换算** | $K_{[\rm m^2]}=K_{[\rm m^3]}/P$ | 本文 K 为 m³（单位宽度），热管 K 为 m² | ✅ **必须除 P，否则差 6 个数量级** |
| 数据点 | 18 档 | `summary.csv`(dx=5) + `d75/h25/d120_summary.csv` | ✅ |

## 图中数字（供正文引用）

**固定 $\delta$，$h$ 从 25→125 nm 时 $f\,Re$ 的变化倍数**：

| $\delta$ | $\alpha=w/\delta$ | $f\,Re$（$h$=25→125） | 倍数 |
|---|---|---|---|
| 25 | 4.80 | 61.19 → 1.49 | **41.2×** |
| 50 | 2.40 | 59.77 → 3.13 | **19.1×** |
| 75 | 1.60 | 24.52 → 4.29 | **5.7×** |
| 100 | 1.20 | 39.36 → 5.06 | **7.8×** |
| 120 | 1.00 | 22.31 → 5.48 | **4.1×** |

**固定 $h$，$\delta$ 从 25→120 nm 时 $f\,Re$ 的变化倍数**：

| $h$ | $f\,Re$ | 倍数 |
|---|---|---|
| 25 | 61.19 → 39.36 | 1.55× |
| 50 | 15.41 → 22.31 | 1.45×（0.69 的倒数） |
| 75 | 5.78 → 13.90 | 2.40× |
| 125 | 1.49 → 5.48 | 3.68× |

**⇒ $h$ 的影响（4–41×）比 $\delta$ 的影响（1.6–3.7×）大一个数量级。**

## 若热管关联式允许自选最优常数

| 情形 | $f\,Re$ | 18 档最大误差 |
|---|---|---|
| 自选最优（最宽容） | 31.34 | **95%** |
| 常规取值 | 14.5 | −90% ~ +322%（随 $h$ 变号） |
| 对比：条纹平均 | — | +10% ~ +205%（同号、单调） |

## 制作

- 脚本：`figures/paper/make_fig_fre.py`
- 输出：`figures/paper/Fig_fRe_collapse.{png,pdf,svg}`（400 dpi）
- 配色：单向蓝色渐变（c-blue 系），**颜色深浅对应 $\delta$**，符合"颜色编码强度/序数"而非分类
- 纵轴对数：因为 $f\,Re$ 跨 41 倍，线性轴会把小值压扁

## 引用时的边界（重要）

- 该关联式的**原始出处**（Faghri 1995 / Chi 1976）**未取得，未逐式核对**。本图只用到"$K\propto r_h^2/fRe$ 且 $f\,Re=f(\alpha)$"这一形式特征。
- **结论不依赖 $f\,Re$ 的具体数值**：即使换成另一套 $f\,Re$ 图表，也只是把所有点整体平移一个常数，**无法改变"同一 $\alpha$ 下 $f\,Re$ 变化 41 倍"**这一事实。
- 因此正文可以写"该形式在此几何上不成立"，但**不宜写"热管公式误差为 322%"**（那个数依赖一个猜来的 $f\,Re$）。

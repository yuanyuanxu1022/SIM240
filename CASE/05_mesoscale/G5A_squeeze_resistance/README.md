# G5A 准静态挤压阻抗模型

一维准静态挤压阻抗数值模型的独立实现。它把现有 G3 微尺度输运闭包（`dx = 2.5 nm` 的 OpenLB 结果）转换成压力、垂向载荷与归一化挤压阻抗，并用解析解、质量闭合和线性响应逐项验证。本目录不修改 OpenLB 核心，也不重跑任何 OpenLB 工况。

## 1. 坐标约定（先澄清，避免与 LBM 混淆）

- `z` 是壁法向 / 压头下压方向，**不是** D3Q19 的某个离散速度方向；
- `y` 是 EX240 沟槽延伸方向（parallel，使用 `K_parallel`）；
- `x` 是横跨沟槽方向（perpendicular，使用 `K_perp`）；
- 一维条带坐标统一记为 `s ∈ [-L/2, L/2]`。

两层网格要分清：

- `dx = 2.5 nm` 属于**输入闭包**（G3 微尺度 OpenLB 网格），本模型不读取/不重算 5 nm 与 1.25 nm；
- `N = 401` 属于**本模型**的 1 mm 条带介尺度离散。

## 2. 控制方程与解析解

深度积分面内通量、一维质量守恒与归一化挤压阻抗：

- `q = -(K/μ) dp/ds`
- `dq/ds = Vp`（由 `dh/dt = -Vp` 得到）
- `C_F = F_z / V_p`

空间均匀 `K` 下的解析解：

- `p(s) = p_out + μ Vp (L²/4 - s²) / (2K)`
- `F_z = μ Vp W L³ / (12K)`

## 3. 九个工况（恒速）

每个离散高度 `h ∈ {50, 75, 125} nm` 上比较三种模型：

| 高度 | Smooth | EX240 parallel | EX240 perpendicular |
|---:|:---:|:---:|:---:|
| 50 nm | ✓ | ✓ | ✓ |
| 75 nm | ✓ | ✓ | ✓ |
| 125 nm | ✓ | ✓ | ✓ |

- Smooth 的 `K = h³/12`（解析生成，`R_input = μ/K`）；
- EX240 从 `transport_database/G3_height_resistance.csv` 读取 `K_parallel/K_perp` 与 `R_parallel/R_perp`。

本模型只做**恒速**加载（`Vp` 固定）。总排液量由压头排开体积决定：`Q_out,total = W L Vp`，因此不同模型在相同高度下 `Qdisplaced_m3_s` 相同——不要把恒速输出误读成不同的总排液量。

## 4. 运行命令

从仓库根目录：

```bash
MPLCONFIGDIR=/tmp/sim240-mpl-cache \
conda run --no-capture-output -n sim240-analysis \
python CASE/05_mesoscale/G5A_squeeze_resistance/run_g5a.py \
  --config CASE/05_mesoscale/G5A_squeeze_resistance/config/g5a_baseline.json \
  --repo-root .
```

结果写到 `CASE/05_mesoscale/G5A_squeeze_resistance/results/<run_id>/`（默认不提交该目录）。

## 5. 输出文件与门槛

每次运行生成九个证据文件：

| 文件 | 内容 |
|---|---|
| `run.log` | 运行日志 |
| `exit_code.txt` | 独立退出码（`0` = 全部通过） |
| `input_manifest.json` | 输入 CSV 路径与 SHA-256、配置、运行时间 |
| `case_results.csv` | 九工况的 `K, p_max, F_z, C_F, Q` 及误差 |
| `pressure_profiles.csv` | 401 网格压力剖面 |
| `validation_report.md` | 逐门槛 PASS/FAIL |
| `Figure_G5_pressure_profiles.png` | 压力剖面图（600 dpi） |
| `Figure_G5_squeeze_impedance_vs_h.png` | 阻抗-高度图（600 dpi） |
| `Figure_G5_directional_ratio_vs_h.png` | 方向阻抗比图（600 dpi） |

六个命名门槛：

```text
INPUT_GATE
NUMERICAL_GATE
ANALYTIC_GATE
MASS_GATE
LINEARITY_GATE
RESULT_PASS
```

只有九工况全部生成、所有门槛通过、所有证据文件可读，才写 `RESULT_PASS: true`。

## 6. 证据边界（重要）

- 输入闭包是**固定网格候选**：`INPUT_CLOSURE_STATUS: CANDIDATE_FIXED_GRID`；
- 本模型不声明介尺度网格独立，也不声明微尺度网格独立：`FINAL_GRID_INDEPENDENT_CLOSURE: false`；
- 物理假设：单相、全充液、牛顿、等温、不可压缩；无气液界面、润湿、毛细、困气或固化；
- 不修改 OpenLB 核心、G2/G3 结果或现有提取脚本。

因此即使 `RESULT_PASS: true`，也不得表述为「完成了网格无关的真实纳米压印动态模拟」或「证明了普适下压阻力规律」。

## 7. 测试

```bash
cd CASE/05_mesoscale/G5A_squeeze_resistance
MPLCONFIGDIR=/tmp/sim240-mpl-cache conda run --no-capture-output -n sim240-analysis \
  python -m unittest discover -s tests -v
```

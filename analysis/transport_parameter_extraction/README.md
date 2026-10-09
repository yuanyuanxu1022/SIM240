# SIM240 介尺度输运参数提取模块

该模块只读已有 OpenLB `results` 目录，生成：

- `mobility.csv`：几何、物性、通量与 `K_eff`；
- `resistance.csv`：`R_eff` 与 `K_eff`；
- `pressure_drop.csv`：局部压力范围，以及由周期体力定义的有效压力梯度和跨周期等效压差；
- `flow_rate.csv`：`J`、由 `J*A_plan` 得到的 Q、两个截面 Q 和截面差异；
- `dissipation.csv`：已有 `energy_dissipation.csv` 的位置-Phi 数据。

同时生成数据库目录：

```text
transport_database/G2/
├── mobility.csv
├── resistance.csv
└── transport_summary.md
```

数据库按同一网格的 Parallel/Perpendicular 结果配对，包含 EX240 几何字段、`K_parallel`、`K_perpendicular`、`R=1/K`、方向比、细网格 GCI 和原始质量门禁状态。

默认读取：

```text
CASE/03_grid_convergence/G2_EX240_grid_convergence/results
```

运行：

```bash
conda run --no-capture-output -n sim240-analysis \
  python analysis/transport_parameter_extraction/extract_transport_parameters.py
```

指定其他结果根目录和输出目录：

```bash
conda run --no-capture-output -n sim240-analysis \
  python analysis/transport_parameter_extraction/extract_transport_parameters.py \
  --results-root CASE/04_parameter_study/G3_EX240_height_sweep/results \
  --output analysis/transport_parameter_extraction/g3_h_results
```

输出按路径排序、固定字段写出，可重复运行。模块不修改 OpenLB、Case 或原始结果。

执行一次真实 G2 提取：

```bash
conda run --no-capture-output -n sim240-analysis \
  python analysis/transport_parameter_extraction/extract_transport_parameters.py
```

自动发现最新已完成 OpenLB results 并更新总数据库：

```bash
conda run --no-capture-output -n sim240-analysis \
  python analysis/transport_parameter_extraction/extract_transport_parameters.py \
  --auto-latest \
  --database-root analysis/transport_parameter_extraction/transport_database
```

总数据库输出：

```text
transport_database/transport_database.csv
transport_database/G2/{mobility.csv,resistance.csv,transport_summary.md}
transport_database/reports/TRANSPORT_DATABASE_SUMMARY.md
```

MCP 工具名：`analyze_latest_transport_results`。它执行上述自动发现命令并返回数据库路径与总报告摘要；命令行脚本仍可独立运行。

## 物理定义边界

G2 使用周期体力驱动，没有入口/出口压力边界。因此 `pressure_drop.csv` 同时保留局部 `pressure_range` 和 `rho*a*L` 的有效体力压差；后者才是 `K_eff` 定义中的驱动接口，不能把局部压力范围直接当成物理入口-出口压降。`dissipation.csv` 明确标记当前数据不是全域耗散积分。

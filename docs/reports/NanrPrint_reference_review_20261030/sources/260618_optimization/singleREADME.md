# 单层 Imprint Droplet 优化脚本说明

本文档对应脚本：

```bash
260618_optimization/optimize_single_layer_droplets.py
```

这个脚本用于单层网格 case 的液滴布局优化。它复用 `optimize_droplets.py` 中已有的液滴解析、候选生成、评分、CSV/SVG 输出逻辑，但路径规则改成单层 OpenFOAM case：

- 液滴初始条件：`system/setFieldsDict`
- 分区/评分区域：`system/topoSetDict`
- 评估场文件：`<case>/<time>/alpha.liquid`
- 运行模板：不包含 `system/imprint`、`system/groove`、`constant/regionProperties` 等 multi-region 结构

## 推荐初始对比 case

当前单层优化默认用下面两个 case 做初始对比：

```bash
template_3r5cBoard_350
template_3r5cBoard_triangle350
```

其中 `template_3r5cBoard_350` 作为 baseline，`template_3r5cBoard_triangle350` 作为 triangle350 对比布局。

## 1. 提取初始液滴和评分区域

```bash
python3 260618_optimization/optimize_single_layer_droplets.py extract \
  --baseline-case template_3r5cBoard_350 \
  --triangle-case template_3r5cBoard_triangle350 \
  --out-dir 260618_optimization/single_generated
```

输出文件包括：

- `baseline_350_droplets.csv`
- `triangle350_droplets.csv`
- `zones.csv`
- `baseline_350_layout.svg`
- `triangle350_layout.svg`
- `extract_summary.json`

`zones.csv` 后续会用于候选布局生成和仿真结果评分。

## 2. 随机种子生成候选 batch

```bash
python3 260618_optimization/optimize_single_layer_droplets.py suggest \
  --zones 260618_optimization/single_generated/zones.csv \
  --out-dir 260618_optimization/single_candidates \
  --batch-size 10 \
  --pool-size 200 \
  --seed 260618 \
  --allow-channel
```

每个候选会生成一个目录，例如：

```text
260618_optimization/single_candidates/candidate_000/
```

候选目录中包含：

- `droplets.csv`：液滴坐标
- `setFieldsDict`：可写入 OpenFOAM case 的初始化字典
- `layout.svg`：液滴布局预览
- `summary.json`：候选评分和特征摘要

## 3. 准备 OpenFOAM 运行目录

批量准备：

```bash
python3 260618_optimization/optimize_single_layer_droplets.py prepare-batch \
  --template-case template_3r5cBoard_350 \
  --candidates-dir 260618_optimization/single_candidates \
  --runs-dir runs/single_iter_000 \
  --overwrite
```

只准备一个候选：

```bash
python3 260618_optimization/optimize_single_layer_droplets.py prepare-run \
  --template-case template_3r5cBoard_350 \
  --droplets 260618_optimization/single_candidates/candidate_000/droplets.csv \
  --run-dir runs/single_iter_000/candidate_000 \
  --overwrite
```

脚本会复制模板 case，忽略旧的运行输出，然后把候选液滴写入：

```text
runs/single_iter_000/candidate_000/system/setFieldsDict
```

## 4. 运行 OpenFOAM

进入准备好的运行目录：

```bash
cd runs/single_iter_000/candidate_000
./Allrun
```

如果需要并行求解，按当前 case 的 OpenFOAM 环境和求解器流程继续运行。

## 5. 一次评估一个 batch 的仿真结果

仿真结束后，不需要对每个 candidate 单独运行评估命令。直接对整个 `runs/single_iter_000` 下的 `candidate_*` 批量评分：

```bash
python3 260618_optimization/optimize_single_layer_droplets.py evaluate-batch \
  --runs-dir runs/single_iter_000 \
  --time 1 \
  --zones 260618_optimization/single_generated/zones.csv
```

每个 candidate 会在自己的运行目录下生成：

```text
runs/single_iter_000/candidate_000/optimization_metrics/metrics.csv
runs/single_iter_000/candidate_000/optimization_metrics/summary.json
```

同时会生成 batch 汇总：

```text
runs/single_iter_000/batch_metrics.csv
```

`batch_metrics.csv` 记录每个 candidate 的状态、objective 分数、summary 路径和错误信息。默认遇到某个 candidate 缺少结果文件时会继续评估其他 candidate；如果希望任意失败都让命令返回非零状态，追加 `--strict`。

脚本默认目标填充率为 `0.95`，评分越低越好。

仍然可以只评估单个 case：

```bash
python3 260618_optimization/optimize_single_layer_droplets.py evaluate-field \
  --case runs/single_iter_000/candidate_000 \
  --time 1 \
  --zones 260618_optimization/single_generated/zones.csv \
  --out-dir runs/single_iter_000/candidate_000/optimization_metrics
```

## 6. 一次添加一个 batch 的历史记录

评估完整个 batch 后，用一条命令把所有 candidate 的结果追加到历史记录：

```bash
python3 260618_optimization/optimize_single_layer_droplets.py record-batch \
  --results 260618_optimization/single_results.csv \
  --candidates-dir 260618_optimization/single_candidates \
  --runs-dir runs/single_iter_000 \
  --zones 260618_optimization/single_generated/zones.csv
```

`record-batch` 会按 candidate 名称匹配：

- 候选液滴：`260618_optimization/single_candidates/candidate_000/droplets.csv`
- 评估结果：`runs/single_iter_000/candidate_000/optimization_metrics/summary.json`

默认缺少某个 candidate 的结果时会跳过并打印 warning；如果希望缺失结果时命令返回非零状态，追加 `--strict`。

仍然可以只记录单个 candidate：

```bash
python3 260618_optimization/optimize_single_layer_droplets.py record-result \
  --results 260618_optimization/single_results.csv \
  --candidate-dir 260618_optimization/single_candidates/candidate_000 \
  --zones 260618_optimization/single_generated/zones.csv \
  --run-dir runs/single_iter_000/candidate_000 \
  --summary runs/single_iter_000/candidate_000/optimization_metrics/summary.json
```

查看当前最优结果：

```bash
python3 260618_optimization/optimize_single_layer_droplets.py best-result \
  --results 260618_optimization/single_results.csv
```

当 `single_results.csv` 中至少有 3 个已完成候选时，可以在下一轮 `suggest` 中加入历史记录：

```bash
python3 260618_optimization/optimize_single_layer_droplets.py suggest \
  --zones 260618_optimization/single_generated/zones.csv \
  --history 260618_optimization/single_results.csv \
  --out-dir 260618_optimization/single_candidates_iter_001 \
  --batch-size 10 \
  --pool-size 200 \
  --seed 260619
```

如果环境中安装了 `scikit-learn`，脚本会从几何先验排序切换到 Gaussian-process expected improvement 排序。

## 常用辅助命令

验证一个液滴 CSV：

```bash
python3 260618_optimization/optimize_single_layer_droplets.py validate \
  --droplets 260618_optimization/single_candidates/candidate_000/droplets.csv
```

单独把液滴 CSV 转成 `setFieldsDict`：

```bash
python3 260618_optimization/optimize_single_layer_droplets.py write-setfields \
  --droplets 260618_optimization/single_candidates/candidate_000/droplets.csv \
  --out /tmp/setFieldsDict
```

## 注意事项

- `prepare-run` 和 `prepare-batch` 默认不会覆盖已有运行目录；需要覆盖时加 `--overwrite`。
- 单层脚本不会读取 `system/imprint/setFieldsDict` 或 `system/imprint/topoSetDict`。
- 候选生成默认随机种子是 `260618`；固定 seed 可以复现同一批候选。
- 默认液滴半径、最小间距、count 范围沿用原优化脚本设置。
- `evaluate-field` 只读取 OpenFOAM scalar field 的 `internalField`，需要目标时间步下存在 `alpha.liquid`。

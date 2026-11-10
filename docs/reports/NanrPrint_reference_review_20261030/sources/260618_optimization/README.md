# 260618 Imprint Droplet Optimization

This directory contains the executable tooling for the 260618 plan. It does not
modify the source cases unless a generated run directory is explicitly requested.

Scoring uses 16 zones from `system/imprint/topoSetDict`: `channel` is included
as its own group, plus the K, EC, and R rows.

## Quick Start

Extract baseline droplets and zones:

```bash
python3 260618_optimization/optimize_droplets.py extract \
  --baseline-case git_template_3r5cBoard_350_multiRegionPermeationV9_zero \
  --triangle-case template_3r5cBoard_triangle350_multiRegionPermeation_zero \
  --out-dir 260618_optimization/generated
```

Generate candidate designs:

```bash
python3 260618_optimization/optimize_droplets.py suggest \
  --zones 260618_optimization/generated/zones.csv \
  --out-dir 260618_optimization/candidates \
  --batch-size 4 \
  --pool-size 200 \
  --seed 260618
```

Prepare OpenFOAM run directories for a full candidate batch:

```bash
python3 260618_optimization/optimize_droplets.py prepare-batch \
  --template-case git_template_3r5cBoard_350_multiRegionPermeationV9_zero \
  --candidates-dir 260618_optimization/candidates \
  --runs-dir runs/bo_iter_000
```

Prepare only one candidate when needed:

```bash
python3 260618_optimization/optimize_droplets.py prepare-run \
  --template-case git_template_3r5cBoard_350_multiRegionPermeationV9_zero \
  --droplets 260618_optimization/candidates/candidate_000/droplets.csv \
  --run-dir runs/bo_iter_000/candidate_000
```

After running OpenFOAM, evaluate a final imprint field:

```bash
python3 260618_optimization/optimize_droplets.py evaluate-field \
  --case runs/bo_iter_000/candidate_000 \
  --time 1 \
  --zones 260618_optimization/generated/zones.csv \
  --out-dir runs/bo_iter_000/candidate_000/optimization_metrics
```

Append the evaluated candidate to the optimization history:

```bash
python3 260618_optimization/optimize_droplets.py record-result \
  --results 260618_optimization/results.csv \
  --candidate-dir 260618_optimization/candidates/candidate_000 \
  --zones 260618_optimization/generated/zones.csv \
  --run-dir runs/bo_iter_000/candidate_000 \
  --summary runs/bo_iter_000/candidate_000/optimization_metrics/summary.json
```

Inspect the current best result:

```bash
python3 260618_optimization/optimize_droplets.py best-result \
  --results 260618_optimization/results.csv
```

Use `suggest --history 260618_optimization/results.csv` after at least three
evaluated candidates. When `scikit-learn` is available, this switches candidate
ranking from the geometry prior to Gaussian-process expected improvement.

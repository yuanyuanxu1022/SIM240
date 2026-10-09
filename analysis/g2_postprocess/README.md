# G2 自动后处理模块

该模块读取 G2 Step3 的 `g2_grid_summary.csv` 和 `g2_richardson_gci.csv`，自动生成：

- `G2_K_convergence.png`
- `G2_anisotropy.png`
- `G2_GCI.png`
- `G2_POSTPROCESS_SUMMARY.md`

运行环境为 `sim240-analysis` conda 环境：

```bash
conda run --no-capture-output -n sim240-analysis python analysis/g2_postprocess/g2_postprocess.py
```

可用 `--batch` 指定其他 G2 结果批次，`--output` 指定输出目录。模块只读结果文件，不修改 OpenLB 代码或 Case。

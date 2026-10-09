# G3-h 自动后处理模块

该独立模块读取 G3-h 高度扫描结果，支持两种 CSV 格式：

1. 宽表：`height_nm,K_parallel,K_perpendicular`；
2. 长表：`height_nm,direction,Keff`（direction 为 `parallel/perpendicular` 或 `P/T`）。

自动输出：

- `G3_K_parallel_h.png`
- `G3_K_perpendicular_h.png`
- `G3_anisotropy_h.png`
- `G3_POSTPROCESS_SUMMARY.md`

运行示例（正式 G3-h 结果产生后）：

```bash
conda run --no-capture-output -n sim240-analysis \
  python analysis/g3_postprocess/g3_postprocess.py \
  --input path/to/g3_h_summary.csv
```

模块只读输入 CSV，不启动模拟，不修改 OpenLB 或任何 Case 结果。

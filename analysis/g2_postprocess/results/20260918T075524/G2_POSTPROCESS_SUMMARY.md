# G2 自动后处理总结

输入批次：`CASE/03_grid_convergence/G2_EX240_grid_convergence/results/g2_grid_20260917T165045+0800`

## K 收敛与方向性

| dx_nm | direction | Keff | anisotropy | run_gate_PASS |
| --- | --- | --- | --- | --- |
| 5.0 | parallel | 9.834075958643652e-23 | 2.210390488544205 | True |
| 5.0 | perpendicular | 4.449022021045936e-23 | 2.210390488544205 | True |
| 2.5 | parallel | 9.782423697043172e-23 | 2.2307340819991053 | True |
| 2.5 | perpendicular | 4.3852935121144107e-23 | 2.2307340819991053 | True |
| 1.25 | parallel | 9.764325526249012e-23 | 2.2402366762089274 | True |
| 1.25 | perpendicular | 4.358613368821741e-23 | 2.2402366762089274 | False |

## GCI

| metric | apparent_order_p | GCI_fine_percent | asymptotic_ratio | mathematical_valid |
| --- | --- | --- | --- | --- |
| K_parallel | 1.5129876294506368 | 0.124965937780287 | 0.9981499297766432 | True |
| K_perpendicular | 1.2561724912115395 | 0.5510219860185761 | 0.9939159959945744 | True |
| anisotropy | 1.0981812083843374 | 0.4647625904539864 | 1.0042598507309783 | True |

## 证据边界

GCI 图和 K 收敛图由原始 CSV 自动生成。`dx=1.25 nm / EX240_perpendicular` 的质量门禁失败仍保留在输入数据中；该后处理不修改阈值，也不把数学收敛改写为完整 Gate PASS。

图文件：`G2_K_convergence.png`、`G2_anisotropy.png`、`G2_GCI.png`。

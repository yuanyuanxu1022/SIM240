# SIM240 第一篇：二维 FEM 定点试点

这是独立数值核验的最小实现，不是新论文主线，也不是对既有FVM的替换。科学范围、停止顺序和门槛见 `PROTOCOL.md`。

- `fem_pilot.py`：P2标量Poisson及P2/P1 Taylor–Hood Stokes求解器；一次只运行一个明确算例。
- `verify_results.py`：从保存的三角形与场独立重积分，不信任求解器自报的K或PASS。
- `results/<case>/`：逐档JSON、CSV及压缩场；大型矩阵不保存。原始场不进入Git。
- `../../docs/reports/PAPER1_conclusion_FVM_FEM_pilot_20261113/`：论文六条结论与现有FVM证据对照，以及最终试点报告。

隔离运行环境：`/home/dell/.workbuddy/binaries/python/envs/default/bin/python`。依赖版本写入每份结果JSON。当前实现使用scikit-fem 12的 `ElementTriP2` / `ElementTriP1`，不是FreeFEM脚本；科学离散路线不变。

完成状态必须以各算例 `VERIFICATION.json` 和最终报告为准。`PILOT_NUMERICAL_CHECKS_PASS` 不等于论文参考资格，不自动触发下一几何或19P+4T。

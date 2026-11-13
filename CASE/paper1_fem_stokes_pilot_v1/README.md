# SIM240 第一篇：二维 FEM 定点试点

这是独立数值核验的最小实现，不是新论文主线，也不是对既有FVM的替换。科学范围、停止顺序和门槛见 `PROTOCOL.md`。

- `fem_pilot.py`：P2标量Poisson及P2/P1 Taylor–Hood Stokes求解器；一次只运行一个明确算例。
- `verify_results.py`：从保存的三角形与场独立重积分，不信任求解器自报的K或PASS。
- `results/<case>/`：逐档JSON、CSV及压缩场；大型矩阵不保存。原始场不进入Git。
- `../../docs/reports/PAPER1_conclusion_FVM_FEM_pilot_20261113/`：论文六条结论与现有FVM证据对照，以及最终试点报告。

隔离运行环境：`/home/dell/.workbuddy/binaries/python/envs/default/bin/python`。依赖版本写入每份结果JSON。当前实现使用scikit-fem 12的 `ElementTriP2` / `ElementTriP1`，不是FreeFEM脚本；科学离散路线不变。

完成状态必须以各算例 `VERIFICATION.json` 和最终报告为准。`PILOT_NUMERICAL_CHECKS_PASS` 不等于论文参考资格，不自动触发下一几何或19P+4T。

## 批量队列（2026-11-13）

`run_queue.py` 按老师工单把尚未覆盖的 18 个格子排队跑完（沿槽16 + 横槽2），每例三档网格并自动调用独立复核。

```
# 先看要跑什么，不计算
python3 run_queue.py --dry-run

# 全队列，中断后再执行同一条命令即从断点继续
python3 run_queue.py

# 只跑某几个
python3 run_queue.py --cases h100_d100_T h25_d100_T

# 重算某例（会先删该例旧输出）
python3 run_queue.py --redo h25_d100_T
```

状态在每个算例结束时原子刷新到 `QUEUE_STATUS.json` / `QUEUE_STATUS.csv`，日志追加到 `queue_run.log`。单例失败只记录、不终止队列；失败不自动改门槛或加档。

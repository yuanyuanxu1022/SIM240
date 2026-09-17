# Case01-Bouzidi-steady 验证报告

完整证据目录：`results/steady_20260916T092333p0800`

## 最终判定

稳态判据、质量守恒、Mach、截面一致性以及 Bouzidi link 审计均通过；但 `Jy` 解析误差为 `+4.675555%`，速度 L2 误差为 `4.065283%`，未达到两项均小于 2% 的精度门槛。应用程序独立退出码为 `3`，因此总体验证为 **FAIL**，不能宣称 Gate1 通过。

关键数值：`Jy=3.679999984e-12 m2/s`，`RJ=2.717391316e19 Pa·s/m3`，最大 Mach 数 `2.508010e-7`，最大质量相对漂移 `0`。上下壁邻 fluid-cell 中心速度均为 `1.114999997e-5 m/s`；速度剖面相对解析解呈近似常量正偏移 `2.087499788e-6 m/s`。

本次所有 wall-link 均为 `q=0.5`。在该特例下 Bouzidi 更新退化为 halfway link bounce-back，所以结果与原 BounceBack 一致。周期 overlap 漏同步问题已经修复，但不能再把剩余 4.68% 偏差归因于漏装 wall-link。下一步应先推导/核对 ForcedBGK、离散体力和半格反弹组合的 tau 相关离散解，再决定独立网格或 tau 对照；本次未运行这些扩展算例。

详细门禁、守恒、剖面、哈希及证据边界见 `results/steady_20260916T092333p0800/validation_report.md`。

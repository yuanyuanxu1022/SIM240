# A1 两方向零步已通过，S0新编号绑定已准备，正式计算未启动

2026-11-02当前入口。原README.md、PROTOCOL.md和run_config.md是上一轮构建阶段的封存快照；其中“零步未执行／无runs目录”不覆盖本轮新证据，也不修改这些旧快照。

已对封存ELF `c1fc2a1eeacced8f11a9bb045c25d70936b7be03fe5495a0b8f51789bd8fe8af` 执行P/T各describe、precheck、initialize，共6次，全部退出0、时间推进0。审计在 `audits/URV_A1_ZERO_20261102_01/`；两份初始化VTK由原独立读取器成功读回。没有进入steady或真实密度捕获路径。

只准备、尚未执行的正式身份：

| 方向 | 新run_id | 目录 |
|---|---|---|
| P沿槽+y | URV_S0_P_A1_20261102_01 | runs/URV_S0_P_A1_20261102_01/steady |
| T横槽+x | URV_S0_T_A1_20261102_01 | runs/URV_S0_T_A1_20261102_01/steady |

两目录各仅run_config.txt与run_manifest.txt。固定h75/d100/w120/P=Ly240/dx5nm、rho1000、nu1e-6、a1e5、tau1，统计窗1013、最大58800步，原边界／平均／收敛门槛保持。

准备合同：`evidence/S0_prepared_binding_A1_20261102_01.json`，SHA `d58019c2843454ce0ec1b2548e83fb6af66f4081d20acd54b695d665c916766c`。这是PREPARED_EXECUTION_BINDING_NOT_LAUNCH_RELEASE，simulation_authorized=false、approved_run_ids=[]；默认只读核对通过，不能执行正式计算。旧v1.2合同不能转用。

`scripts/run_S0_A1.py` 未来仅在真实授权另存合同后允许启动。顺序为P原生→捕获SHA索引→绑定全部原始输出→原URV验收→独立密度重放／补偿与物理输出守卫→全部通过才T。失败／超时／输入变化立即停，不自动重试或进入S1。formal capture端到端仍待真实运行检验。

本轮没有交付启动命令。S0 HOLD，新正式NUMERICAL_GATE、RESULT_PASS与geometry_PASS尚未评价；零步几何通过不替代正式回归。完整报告：`../../docs/reports/URV_A1_zero_S0_binding_20261102/REPORT.md`。

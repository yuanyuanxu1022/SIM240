# A＋B 独立验证：碰撞/单步收支与纯CH扩散

当前入口：[PREPARATION_STATUS.md](PREPARATION_STATUS.md)。
执行协议：[PROTOCOL.md](PROTOCOL.md) / [protocol.json](protocol.json)。

本目录新增独立实现和编译准备，旧source3d/LP200/LP2000及共享OpenLB保持原样。
仅A1局部碰撞和22项零步初始化已执行；**4项A2单步和18项B扩散正式批次尚未启动**。
不将准备成功当成扩散、完整NS/CH、静滴、润湿、沟槽K或GHY验证通过。

## 代码与证据

- `src/dimension_corrected_ch.h`：与上轮已验证局部修正逐字节相同。
- `src/ch_collision_check.cpp`：实际CH碰撞、D2回归与旧D3缺陷对照，新增tau2.5。
- `src/ns_collision_check.cpp`：实际NS碰撞、独立人口公式、压力/半步力与微小速度置零。
- `src/ab_check.cpp`：实际SuperLattice周期迁移、四阶段A2快照、18项固定B配置。
- `reference.py` / `reference/`：独立19×19矩阵参考和谱预检查，无求解器执行。
- `analyze_completed.py`：仅分析已完成批次；全程复模态/漂移、三维场/一步式、方向与粗细网格比较。
- `test_contracts.py`：7项合成数据/数学参考检查，不是新的CFD证据。
- `run_suite.py`：默认只预检查；显式`--run`一次运行22项，拒绝覆盖，不自动分析/重试/进入C/D。
- `evidence/`：编译、碰撞、零步初始化、入口防错、绑定和保护证据；旧失败日志保留。

`NEXT_COMMAND.txt`是本次准备交付的唯一正式运行命令；存在该文件不代表用户已启动。
运行完成后，先检查批次与22项独立退出码、完整CSV/场和哈希，再按冻结协议验收。
单MPI进程；没有墙、NS/CH反馈、移动边界或真实物性校准。

## 物理解释边界

B1的人造正曲率自由能用于识别扩散算子；B2使用目标格子化学势短测。
它们不会单独解决扩散质量/动量相容性、体相端点漂移或物理压力口径。
下一阶段C/D保持待验收状态，本批次不自动进入。

科研技能沿用scientific-critical-thinking/scientific-writing；来源说明见上轮
`../coupled_balance_review_20261022/REVIEW.md`参考R4。流程工具不代替数值证据。

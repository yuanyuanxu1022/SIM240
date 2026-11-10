# 单周期细 T 同步质量诊断 v2

本目录是独立旁路诊断实现。先定位历史 h75/dx1.25/T 质量门禁异常，再决定是否需要统计修复或动力学定位。历史源、程序、数据、FAIL及正在由其他会话完善的 v1 均保留。

入口：[冻结诊断协议](PROTOCOL.md)、[账本 schema](ledger_schema.md)、[启动准备记录](reports/run_ready.json)。源码是已审查 v1 求解器副本，只增强独立观察器；v2 新增每步 film/recess 计数与 delta-rho、密度极值 ID、名义体积、重构残差汇总以及重复/遗漏观测拒绝。

## 当前验证

- 实际 C++ 观察器已通过合成输入测试；原初始 double 质量精确重现。
- 分区节点数为2,211,840与1,474,560，两者之和为3,686,400；合成扰动的分区和与全域一致，密度极值ID正确。
- 独立 OpenLB 可执行文件已编译；完整命令/stdout/stderr、source/library/binary及动态依赖SHA见 [构建与零推进审查](reports/build_precheck.json)。
- 零推进预检独立exit=0，geometry/converter/q均通过；3,686,400流体节点、521,472条安装链接、q约0.5、fallback/unresolved均0，collideAndStream调用0次。
- 尚未执行4000步诊断，尚未定位瞬态峰值，尚未获得新的稳态参考PASS。

## 用户运行与证据

唯一运行目录先通过 `scripts/run_diagnostic.py --prepare-only` 创建；已准备目录只能执行一次。脚本在启动前验证冻结源/库/binary/协议SHA，强制单计算线程，拒绝已有输出，并检查资源预算。实际命令在对应manifest中保存。

长计算由用户在tmux启动；脚本等待一个T诊断完成，保存run.log、独立exit_code.txt、timing.txt及所有输出SHA，不启动后续工况。诊断的原程序可能因未稳态或旧门禁而exit=3，应与diagnostic_status.txt、完整覆盖和高精度账本分别审查。运行结束后另开结果分析任务。

`run_ready`仅表示编译和零推进预检具备启动条件，**不表示质量根因、细网格参考或网格独立性已通过**。所有诊断状态保持formal_reference_accepted=false。

后续科学审查仍要核对4001行、9固定快照与峰值、同刻独立fsum、1e-13账本一致性/重构、旧与新轨迹及全部原门禁。若高精度账本显示真实变化，再做阶段/link定位。端点高度补证与排液优势评估不会自动启动。

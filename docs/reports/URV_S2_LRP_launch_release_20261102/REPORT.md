# S2-LRP-v1 恢复清单、新正式绑定与手动命令

## S2-LRP-v1 新正式绑定已交付准备；正式计算未启动（2026-11-02 22:43:02 +08:00）

用户已采用 S2-LRP-v1，授权准备独立恢复清单、新正式绑定与用户手动命令；本轮不自动启动。入口 `docs/reports/URV_S2_LRP_launch_release_20261102/REPORT.md`、START_COMMAND.txt、verification.json、recovery_manifest.json、input_set_delta.json。

新合同 `CASE/unseen_v2_reference_S2_reuse_v1/evidence/S2_formal_launch_release_LRP_v1_20261102_02.json`，SHA256 `d08297ebda69d9698d40762f778eb43299fa3c01c35e5591b6d31b4e06ef26cd`，2160项输入；原正式其余2139项逐项继承，B1816项全部保留。唯一移出的活动输入是旧PERF控制日志，改绑本报告目录当前字节快照；旧空指纹、旧原始清单、旧合同、正式拒绝快照及恢复裁定均保留。不是修复旧合同通过，旧release仍存在bound input drift。

本轮已重新验证 PERF2058项输入、原62项仅该日志差异，两方向独立复算与原检查器重放完全相同；PERF_RESOURCE_PREREQUISITE=RETAINED_WITH_DOCUMENTED_LOG_EXCEPTION。原15个动态库/ELF未变，未构建/原生/VTK调用。原 inspect、binding、validate_formal_authority 及默认只读入口通过（0），错误外部SHA拒绝；全部2160项和受保护文件结束时一致。只读审计未创建launch_attempts。六目录仅配置/manifest，无相关任务。资源快照 MemAvailable 18.68GiB、空闲磁盘318.01GiB，启动时仍由原程序重核。

沿用已有六条真实授权证据，未把本次准备指令伪写成新的求解授权。kind=AUTHORIZED_EXECUTION_LAUNCH_RELEASE、formal_simulation_authorized=true、AI_may_start_solver=false、user_manually_starts=true；automatic retry/extension/S3仍false，actual_formal_run_ids=[]。原六身份URV_S2_{P,T}_dx{5,2p5,1p25}_reuse_v1_20261102_01不变；5→2.5→1.25nm、每档P→T、逐条1/1/4/4/12/12小时、原独立验收通过才继续、失败即停。第四条通过后自动进入第五条属于已有范围；细格12h不保证完成。

新会话 `urv_s2_formal_lrp_v1_20261102_02`；新控制日志 `CASE/unseen_v2_reference_S2_reuse_v1/evidence/S2_formal_controller_LRP_v1_20261102_02.log`。用户仅在dell机器终端手动执行START_COMMAND.txt中的一条命令；不要再执行旧正式或PERF命令。命令已准备与交付不代表用户已启动。新绑定默认入口未执行 --execute，求解调用0，无任何正式结果验收升级。

下一步：用户实际执行后另发任务，单次核查新会话/新控制日志与原六身份的启动状态；不轮询、不重试。完成后再按原URV-v1/MRP/A1/S2-MIP-v1完整验收。旧日志完整性例外、历史FAIL、F04 OPEN、参考资格false及模型比较/物理验证未评价保持。


本轮新增文件仅为本报告目录及新合同/SHA侧文件；旧合同、源码、门槛和原始结果未改。完整命令见 START_COMMAND.txt。

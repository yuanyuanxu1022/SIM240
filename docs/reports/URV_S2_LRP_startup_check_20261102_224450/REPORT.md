# 新绑定正式 S2 单次启动状态核查

## 新绑定正式 S2 已启动；快照时完成前两条、正在第三条（2026-11-02 22:44:50 +08:00）

用户本轮授权仅单次启动状态核查，不重跑、不持续轮询。证据入口 `docs/reports/URV_S2_LRP_startup_check_20261102_224450/snapshot.json`、REPORT.md。

已确认新会话 urv_s2_formal_lrp_v1_20261102_02 存在；控制器PID780296绑定新release SHA d08297ebda69d9698d40762f778eb43299fa3c01c35e5591b6d31b4e06ef26cd，原生PID781184正在URV_S2_P_dx2p5_reuse_v1_20261102_01（2.5nm沿槽P）。该次快照最后已落盘完整诊断step460，不等同精确当前调用数或完成进度百分比。

5nm沿槽P与横槽T均已有completion和独立acceptance：原生独立退出0，无超时/资源停止，inputs_unchanged=true；自动独立检查器NUMERICAL_GATE=PASS、geometry_PASS=true、RESULT_PASS=true，检查器退出0。P3328步/约27.27s，T1940步/约16.47s。这里只记录已有接受文件，不替代本轮之后对整批的独立完整分析；原生result中RESULT_PASS=false是原设计待独立接受字段，不是新矛盾。

2.5nm横槽与1.25nm两方向仍只有配置/manifest，未启动。六条总体为已完成并获自动接受2、运行中1、尚未启动3。新控制日志存在且快照时为空；实际会话/原生进程/诊断和前两条接受证明已进入正式计算，不能按日志为空判未启动。正式launch_attempts新SHA目录已有两条检查器日志。

本轮不重新哈希2160项输入、不做全轨迹科学验收、不新增计算/重跑、不修改CASE/绑定/门槛、不控制或终止任务。仅新增本快照报告并更新共享状态。原PERF日志例外及旧正式拒绝均保留。

下一步：保持本批按既有六条授权和失败即停控制器运行；结束后由用户另发完整分析请求，按URV-v1/MRP/A1/S2-MIP-v1/S2-LRP-v1核对所有已有结果。不得自动重跑、加时或进入S3。参考资格false、MODEL_COMPARISON/physical_validation=NOT_EVALUATED、历史FAIL及F04 OPEN不因本次启动核查升级。当前快照不预测结束时间。


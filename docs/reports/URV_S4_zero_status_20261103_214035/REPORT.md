# S4 原生18＋6零步审计：单次启动状态核查

核查范围：按用户请求仅做一次运行状态快照；不重跑、不持续轮询、不运行独立结果检查器，不进入性能推进或正式计算。

结论：已确认实际启动，快照时已有完整结束记录。审计身份 `URV_S4_ZERO_v1_20261103_01`。快照时间为2026-11-03T21:40:35.148575+08:00至21:40:35.159839+08:00。

## 本次观察

- 已交付release SHA256为 `a62e6f3c96292bec5ab73796789718f28ba2b88232af9f55104697dc30b81d09`，本次读取的合同文件指纹一致；本轮未重新核验2998项全部输入。
- 存在绑定attempt目录、18条progress、18份原生进程回执、6份读取进程回执及6份初态读回报告。
- 18次原生调用均exit=0、timed_out=false、stop_reason=null；describe/precheck/initialize各6次。
- 6次初态读取均exit=0、timed_out=false；6份读回报告均PASS=true、actual_reader=true、frame_count=1。
- 已有自动verification显示ZERO_STEP_AUDIT_PASS=true，actual_time_steps=0、steady_mode_invocations=0、formal_simulation_started=false。
- 状态快照未见相关运行进程，tmux无活动server/目标会话。结合完整结束材料，判为已结束，不能仅根据会话消失判断失败。未单独取得父控制器退出码，不推断该退出码。
- 自动verification SHA256：`1a73d2d705af23ddcc30f64c112c28eb1e1566557a94e151d3f6faa757087330`。

## 判定边界

以上为启动/结束状态核查及已有自动回执概览，不是原URV-v1／MRP／A1／S4-MIP-v1下的完整独立验收。尚未逐项独立复核封存输入、原生原始证据、几何/q、初态场内容与审计文件清单。准备B尚不存在；本轮不生成B。

自动结果的NUMERICAL_GATE=NOT_EVALUATED、RESULT_PASS=false、reference_qualified=false保持原样，不能将零步自动PASS解释为正式流场通过或参考取得资格。正式attempt/完成记录未见，性能推进、正式S4、S5均未启动。旧FAIL、既有HOLD及投稿限制不改变。

## 本轮动作与接续

本轮启动进程0、原生调用0、场读取器调用0、重试0；仅一次状态快照，随后从保存的JSON整理报告并更新共享状态。未修改源码、原合同、准备A或原始结果。

下一任务可在单独请求后，完整独立复核已有18＋6结果，合格后另存执行权限关闭的准备B；不重跑、不自动进入性能推进或正式计算。

证据：`status_snapshot.json`、`controller_log_snapshot.txt`。旧状态备份为本目录的两个before文件。实际输出源：`CASE/unseen_v2_reference_S4_reuse_v1/audits/URV_S4_ZERO_v1_20261103_01/`。

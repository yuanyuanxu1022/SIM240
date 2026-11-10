# S2 bound input drift 只读定位

## 正式 S2 绑定差异已定位：旧 PERF 控制日志变化；正式求解未开始（2026-11-02）

本轮范围：只读定位原因，不重跑、不修改绑定。2140 项正式绑定输入逐项重哈希：2139 项一致、1 项变化、无缺失。唯一变化为 `CASE/unseen_v2_reference_S2_perf_v1/evidence/S2_perf_controller_v1_20261102_01.log`，合同期望空文件 SHA256 e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855；当前为 1173 bytes，SHA256 ca3607bfc8f2c7aaeb99997253e85485f1633f74983f85aa087c96da70d8799c。正式 release 自身 SHA 仍为 2c0ed4c3c9d05178da160c2c2772ea8cee4ea03808ce7d765a19e3e3a86d1ad0。

变化日志内容是旧 run_perf.py 经 inspect→pristine 拒绝 `output already used; no restart/overwrite` 的 traceback，发生在 execute 之前。日志与源码支持旧 PERF 入口再次被调用并在准备检查拒绝，不能证明调用者、完整命令、是否带 --execute 或确切调用时刻；不推断用户误操作。文件 mtime 为北京时间 22:18:19，正式合同 released_at 为 22:08:36，正式拒绝日志 mtime 为 22:23:13；mtime 仅为辅助证据。旧 PERF 原始证据清单同样记录该日志为空；正式 bind_release.py 第 104 行将 perf_raw 全部引入，导致旧日志变化进入正式输入闭包。

直接失败路径：run_S2.main→inspect→verify_seal→unchanged；stage_s2.py 第 21–25 行比较全部哈希并抛出 bound input drift。此次2139项一致覆盖原生二进制、源码、六份配置及已绑定PERF诊断/回执；没有发现这些文件变化。旧PERF日志的完整性问题必须保留，不能仅因其他文件一致就把整条旧证据链判为完全未变。

证据入口：`docs/reports/URV_S2_bound_input_drift_diagnosis_20261102/REPORT.md`、verification.json、changed_perf_controller.log.txt。本轮仅新增诊断报告与维护共享状态；无CASE文件修改、构建、原生调用、重跑、重新绑定或门槛修改。沿用上轮正式六条未启动判断，本轮未重新轮询进程；未新增数值或物理验收。

下一步：另定最小恢复协议，保留旧合同、旧日志及原始空日志哈希，不截空日志、不直接接受新哈希覆盖旧绑定；先审定旧PERF核心证据是否足以维持前置资格，再准备独立的新正式执行绑定及新控制日志路径。既有六条授权范围不扩大；交付新命令与用户手动执行分开，禁止自动重跑或S3。历史FAIL、原门槛与reference资格边界保持。


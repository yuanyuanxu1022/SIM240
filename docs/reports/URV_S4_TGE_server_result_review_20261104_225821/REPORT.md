# 1.25 nm结果/构建等价/实测资源复核：结束条件尚未满足

北京时间2026-11-04 22:58:22，单次只读SSH快照：求解PID1181432/Rl，运行01:31:54，CPU99.9%，当前RSS1556060KiB（约1.484GiB）；控制器PID1181366/Ss+，运行01:31:55。CPU与RSS是该时刻进程快照，不能替代最终运行速度/峰值内存。控制日志空，未找到result.txt、exit_code.txt、completion.json、acceptance.json或formal_run_record.json。尚在求解，独立检查未取得结果；无结束证据，不能进行结束后验收，也不判数值FAIL。

直接证据：snapshot_stdout.json（SSH返回原文，含进程表、回执搜索、日志尾与合同哈希），snapshot_stderr.txt为空。合同SHA758f13deecec0a26ae309e982cbcadfb1aa9bf198e58513292bd2114df49631d本轮远端重哈希一致；本轮只核合同文件指纹，没有重放整个输入闭包验证，不能据此宣称全量来源验收通过。

用户范围：计算及独立检查结束后，复核现有1.25 nm结果、构建等价及实测资源。run_id=URV_S4_T_dx1p25_TGESRV_v1_20261104_01；服务器10.103.102.55/yuanyuan；h30/d80/w120/P240 nm、横槽T、dx1.25 nm。没有新run_id或执行授权，不启动/停止原运行，不自动重跑、0.625、零步、PERF或S5。

下一动作：用户收到结束信息后再发起结果复核，取回completion/独立exit/result/acceptance/formal_run_record及日志，核来源与输入/输出哈希、完整诊断和几何/q，独立复算K与统计窗，再核相对本机3.471791836744987e-24 m³的偏差绝对值≤1e-6及time-v最终峰值RSS/耗时/吞吐。沿用既有协议和冻结门槛，失败即保留，不覆盖旧证据。此前准备及验收清单见URV_S4_TGE_server_closeout_pending_20261104_225446/REPORT.md。

状态：BUILD_EQUIVALENCE未评价，最终资源未取得；无新增计算或科学验收。本轮0远端写入、0求解启动/停止、0重试、0读场、0科学检查器重放。仅新增本报告/快照/指纹与维护状态交接，未提交或推送。

原S4六条per-run接受、P网格PASS保留；T中细1.328387035%>1%仍FAIL、S4_STAGE_ACCEPTED=false、reference_qualified=false、MODEL_COMPARISON/physical_validation未评价、strict_error_bound/submission_ready=false、F04 OPEN及全部历史FAIL不变。本文为AI辅助状态记录，未替代人工科学终审。

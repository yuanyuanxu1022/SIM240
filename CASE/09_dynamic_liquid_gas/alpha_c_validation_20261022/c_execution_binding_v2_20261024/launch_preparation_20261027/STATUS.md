# C 独立运行入口准备（2026-10-27）

状态：COMMAND_READY_NOT_STARTED。用户授权按新版本复查输入/资源并准备独立运行入口，明确不自动启动。本轮未调用tmux new-session、求解器（包括零步）、编译或完整结果分析。

- 执行版本：C_BINDING_COMPAT_20261024_v2，固定批次alpha_c_20261024_binding_v2_c；4组64³/64步，物理输入/判据按原协议，既有二进制不变，本轮未重编。
- 北京时间2026-10-27 17:59:31快照：新runner默认预查exit0，验收--check-inputs exit0，3808项绑定一致。新旧C的预定output/evidence批次目录均不存在，单次ps未见coupled_check，计划tmux会话名未占用；不据此推断其他机器。
- 可用磁盘336.52GiB（需12GiB），MemAvailable13.05GiB；这是快照，不是预留。动态依赖未缺失、二进制可执行；正式耗时和峰值RSS未实测，无运行安全保证。
- 命令见NEXT_COMMAND.txt：固定本机绝对工作目录和Python解释器，runner显式--run；bash -n语法检查exit0，只检查不执行。后台stdout/stderr追加到本目录runner.log，保留可能的预查拒绝；逐项独立日志和退出码仍由原runner记录。
- 命令交付不等于用户已启动。用户应在当前存有该项目的Ubuntu电脑、本机普通终端中执行一次；不需要先切目录，不需要在聊天框执行。无报错时tmux一般不显示文本。之后由用户反馈启动或完成证据，不自动轮询、重跑、分析或下一阶段。
- 原相量/质量1e-9预算保持。真实本构两组首步相量预测−2.36935e-9/+8.29233e-9、目标组质量预测−8.27245e-9仍预计超限，C是收支诊断，不预先宣称物理守恒通过。三类Gate保持NOT_EVALUATED；已预测不是实测C FAIL。
- 完成后另行核总/4项独立退出码、输入SHA、每组65帧及首步三阶段分布，再用本版本analyze_completed_c按原数值函数验收。不要重复alpha或使用旧run_suite/NEXT_COMMAND，C不自动进入细格/D/静滴/润湿/K。

本目录新增准备记录不修改冻结源码/协议/绑定。项目共享入口已同步；最终读取核对见final_integrity.json，命令检查见command_validation.json。

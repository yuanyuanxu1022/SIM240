# D4首14项启动退出：目录与相对绑定路径问题

2026-10-24。用户贴出实际终端：tmux new-session返回后，tmux ls仍报no server running。本轮授权范围为定位和修正启动问题，保留原科学协议，不启动/重跑正式计算。

**原因已复现：原启动命令先cd到D4子目录，而release中有47项以项目根目录为基准的相对路径。** 检查器直接Path(p)解析；从项目根目录检查能通过，从D4目录却无法找到同一文件，报bound input changed后退出，尚未进入创建正式批次或求解器的步骤。终端操作本身正确；此前准备时仅在项目根目录进行了CLI默认检查，遗漏了交付命令的实际工作目录。

## 直接证据

`tmux_dry_check.json/log`在隔离tmux套接字中复现原shell调用，只去除--execute。tmux启动返回0，子进程报：

```text
RuntimeError: bound input changed: CASE/D_series/D4_variable_groove_transport_20261023/development_completion_plan_20261024/case_budget26.csv
```

该文件并未改变：以SIM240根目录解析其路径时SHA仍与release一致。错误信息反映的是工作目录导致的未找到文件，不应据此称数据被篡改。总计47个相对绑定受相同影响，所有2611绑定在项目根目录解析后核对一致。

tmux会话消失只说明子进程已退出，不能证明计算已完成。当前正式batch不存在，也没有execution.lock创建记录。本轮未运行任何steady，G4公式、原始数据、历史FAIL和数值门槛不变。

## 最小修正

新增D4/development_remaining14_20261024/start_from_project.sh，按自身位置确定项目根目录并cd，再调用原冻结run_remaining.py。默认--check只检查，必须明确--execute才调用原执行分支。未改原runner、release、源码、binary、PROTOCOL或任何模型系数，也没有重新绑定已冻结输入。

--execute的控制台输出追加到同阶段evidence/startup_console.log，即使在batch创建前失败也留下报错。日志当前未因正式执行生成；本轮检查日志为startup_check.log和本目录tmux_corrected_dry_check.log。新wrapper及命令的SHA单列保存，不声称它们属于原2611项运行绑定。

原NEXT_COMMAND.txt与准备报告是历史快照，保留字节。**今后使用NEXT_COMMAND_CORRECTED.txt及CURRENT_STARTUP.md，不再使用原先cd到D4目录的启动命令。** 输出batch_id、14项白名单和所有参数不变，不通过改名重跑掩盖失败。

## 核查

- /bin/bash -n通过。
- 从D4目录和/tmp分别调用wrapper --check：exit0、ok=true、will_run=false。
- 在隔离tmux套接字中按更正后直接传参方式调用--check，得到同样结果；未传--execute。
- 非法参数--other被拒绝（exit2）。
- 2611原绑定重新核对一致；原release SHA仍9606906a7ea18c5ec47f1728eeb7d9af48990e17955167f79019c6ec1e3358c9；正式batch仍不存在。

验证机器记录见verification.json。直接传参调用方式以本机tmux3.4的/usr/share/man/man1/tmux.1.gz为依据；多参数shell-command可直接执行，不依赖外层cd字符串。本轮没有修改用户tmux配置或环境。

## 当前停点

启动目录问题已修正并完成不计算的复核；不是14项运行完成或物理验收通过。下一步用户手动运行更正命令，完成后独立验收。计算期间不持续轮询，不自动进入12项开发细格或20项预测/预测细格。当前状态与交接见state_sync.json；旧结果和全部科学协议/模型保持。

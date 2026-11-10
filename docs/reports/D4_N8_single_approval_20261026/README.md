# 首项N8：单项批准与启动交付

2026-10-26（北京时间）。状态：APPROVED_PREPARED_NOT_STARTED。

用户在本轮明确答复：“明确批准上述唯一首项和固定预算，由我启动”。完整确认问题与答复保存于批准合同的approval.authorization_text及approval_evidence.json。唯一批准对象为B0MIN_MMS_mixed_N8；合同编号D4_N8_diag_v3_1_20261026_v1，实际运行尚未开始，actual_run_id=null。

批准合同为APPROVED_DIAGNOSTIC_ONLY.json，仅改变原候选的status、authorized_to_execute、approval三字段。原候选、原物理plan、18项执行位和原科学协议不改。单项诊断规格SHA写入approval.protocol_sha256；来源锁SHA及全部参数继承已审对象。

范围：无量纲矩形P=2、H=1，16×8三角网格，P2/P1，1275原始混合自由度，MMS规定源项。GMRES/无预条件器/零初值，restart50、最多2000次，rtol和独立真实残差1e−10、atol0，MPI1/库线程1。工作进程600秒检测限及5秒终止宽限；cgroup内存4GiB、swap0、pids32；512MiB专用工作卷，普通盘可用≥2GiB，启动前MemAvailable≥6GiB。归档在工作进程结束后执行，不计为精确600秒内全流程。失败即停、保留已有文件和退出，不增预算、不改算法/阈值、不重试、不运行第二项。

本轮已验证：472份已审输入哈希一致；批准合同执行许可校验通过；runner.prerequisites只读检查通过；工作卷空/0700/可执行缓存加载、持久目录ext4/0700/不同设备、memory/pids委派和资源下限满足；拟用work/record/cgroup不存在。tmux已安装、指定会话不存在，最终shell脚本和命令bash语法通过。快照资源见approval_evidence.json与final_precheck.json；启动时runner再次检查。未调用runner.run/main或worker，未创建cgroup、网格、矩阵或KSP，未导入PETSc/DOLFINx/UFL。

准备脚本首次exit1：合同与证据写出后，末尾断言错误地禁止NumPy（runner的records模块正常导入NumPy）。只修正此断言，未覆盖已生成批准对象；重新执行独立只读许可/资源与文件SHA校验exit0，见final_precheck.json。该准备检查错误不是求解失败。既有12/32项历史测试未重跑，亦无新编译。

唯一交付入口为launch_command.txt，调用launch_once.sh；初版内联命令仅留历史launch_command_initial.txt，禁止重复执行。最终命令/脚本SHA与语法记录见launch_binding.json；approval_evidence.json中的launch_command_sha256对应初版，最终以launch_binding.json为准。脚本不覆盖既有launcher日志；保留launcher.stdout.log、launcher.stderr.log、launcher.exit_code.txt，便于启动前拒绝时追溯。交付命令不等于用户已经执行。

下一动作：用户在本机普通终端执行最终唯一tmux命令一次。随后停止本轮工作，不轮询。完成后另任务按原v3.1读回合同独立验收来源、独立退出、持久归档、KSP及真实残差、r=Tx、零空间/相容/周期/壁面迹和压力去均值。exit0或归档完整均不能单独判诊断通过。

当前NUMERICAL_GATE=NOT_EVALUATED、RESULT_PASS=false、geometry_PASS=null，预测HOLD。解析L2、通量/能量、完整18项、沟槽和公式验证未评估。无OpenLB编译/运行、拟合、Gate推进、Git提交或推送。

# Alpha与C粗网格验证准备状态

2026-10-22。IMPLEMENTED / COMPILED / LOCAL_CHECKS_PASS / ZERO_STEP_INITIALIZATION_CHECKED。
正式执行冻结以PROTOCOL.md、protocol.json及evidence/build_binding.json一致为准；交付前已安排统一哈希与预检查。没有正式alpha/C空间推进，不存在新空间验证PASS。

| 内容 | 证据与状态 |
|---|---|
| 独立源码 | src/alpha_ch.h、alpha_diffusion.cpp、coupled_check.cpp等；旧正确源项文件字节相同 |
| 编译 | build_local_v2_exit_code=0、build_c_v2_exit_code=0，4个二进制；不重编共享库 |
| CH局部 | 59184检查/0失败，最大2.2204460493e-15 |
| NS局部 | 3240检查/0失败，最大8.6736173799e-19，含新tau1.25 |
| 零步 | 16alpha＋4C，20项独立退出0；没有collide/stream |
| 独立复核 | evidence/preparation_verification_final.json与对应日志/独立退出码；C初场全字段和alpha初末字段核对 |
| 静态参考 | reference/，evidence/reference_static_checks.json；完整矩阵/标量传播交叉核对 |
| 合成负对照 | test_contracts.py，8项；故意破坏分布/截断数据可检出，无OpenLB调用 |
| 防误启动 | evidence/CLI_guard_checks.json；错误ID、选项和已有输出拒绝；stage预查见final_preflight.json |
| 保护 | 3045份旧A/B及实际谱审查去重输入，evidence/protected_inputs.json；本轮无不匹配 |
| 正式alpha | 16项空间计算待用户独立启动；未完成、未验收 |
| 正式C | 4项粗格64步程序和协议就绪，待alpha合同验收后用户单独启动；未完成、未验收 |
| 正式Gate | NUMERICAL_GATE / RESULT_PASS / geometry_PASS全部NOT_EVALUATED |

Alpha粗/细为同40nm域、alpha1/4、tau1、固定M、W物理10nm；独立协议连续率限粗7%/细2%，静态最差约6.215%/1.594%，没有改旧协议5%/2%。C参数与上轮选择一致，等密度对照保持运动黏度而非动力黏度。

C保存全程16字段与第1步全NS/CH分布三阶段，未压缩原始量约9.68GB，需预留12GiB；未测正式耗时。C不测K，不判断平衡/压力收敛，不自动进入细格C/D/静滴/润湿。

**首步守恒预算预警已记录**：独立初场S0积分预测两个真实本构组首步DeltaQ/Q约−2.37e-9 / +8.29e-9，超过1e-9。未实际推进，不报告实测FAIL；保留C为收支诊断，物理预算不放宽，不能以准备通过承诺物理守恒通过。见evidence/c_initial_budget_forecast.json。

当前下一动作：用户在本机SIM240终端执行NEXT_COMMAND.txt中的唯一alpha阶段tmux命令。命令已准备不等于已启动。运行结束后再启动结果分析任务，核对独立退出码、完整数据和绑定；不重复启动已存在批次。

第一篇有并行状态更新，本任务同步共享入口时保留其最新首段；此前快照及差异在before/与evidence/state_sync.json。科研技能出处已记入CODE_REVIEW.md，不作为物理验证。

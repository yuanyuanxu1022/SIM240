# 正式S2六条授权与绑定前条件核查

2026-11-02。用户本轮要求“采用 S2-FRD-v1 并明确正式执行范围后，核查授权与绑定前条件；不自动启动计算”。本轮按FRD主方案六条进行只读核查；协议采用不推导为正式执行许可。

## 已验证

22:02:29 +0800，原正式控制器inspect(B)通过：1816项绑定来源、六个净输出目录、零步身份/收据和原资源检查均通过。另核B内独立零步接受文件SHA、已接受性能复核及原始性能文件SHA，均一致；没有重做原生零步、场读取或性能测试。

可用内存20497305600 bytes=19.08960GiB、空闲磁盘341482606592 bytes=318.03046GiB，满足12/100GiB前置门。Python前单进程清理LD_LIBRARY_PATH/LD_PRELOAD后，ldd只读解析的15个动态库路径及SHA与原构建记录一致。资源是当前快照，签发真实合同和实际启动时仍须重查。

六个正式目录仍只有config/manifest，launch_attempts不存在，未发现相关原生/正式控制器进程。没有新正式执行release文件。真实B SHA2e55f3369f9445e7763ee1f9a87c57f79348d1b332c959bc038c1bcc4739081f保持。

## 核查范围与绑定方案

范围为原六条：P5/T5/P2.5/T2.5/P1.25/T1.25nm，预留身份及精确配置见precheck.json和binding_plan.json。单条1/1/4/4/12/12小时，求解预算34小时，独立检查每条最多1小时，I/O和清理额外；不是严格40小时整批上限或完成保证。完整合同获准后第四条通过会直接进入第五条；细格12小时可能不足。原资源/统计窗/最大步/帧/科学门槛均不改。

binding_plan.json是NON_EXECUTABLE_FORMAL_S2_BINDING_PLAN_NOT_AUTHORIZATION，所有许可false、approved/actual空，无实际授权release或命令。未来真实合同须绑定原B及闭包、独立性能复核与可验证原始证据、FRD协议/采用范围和真实六条授权，不能挪用两条性能授权。原B不回写。

## 当前授权缺口

原正式stage_s2.validate_formal_authority要求AUTHORIZED_EXECUTION_LAUNCH_RELEASE、simulation_authorized=true，以及真实记录formal_simulation_authorized=true和精确六条approved_run_ids。现有记录没有这项许可；当前消息要求核查，不能自行改写为“现在授权正式六条”。

已单独请求确认是否现在采用并授权完整六条、接受原预算内尝试和第四条后自动进入细格，仅生成合同/一条命令由用户手动启动；无自动重跑或S3。当前等待明确答复，不记录虚假的授权，不生成正式release/命令，不启动计算。

## 停点

本轮只新增本目录和维护共享当前状态/交接；源码、B、性能证据、六个正式配置/目录不改，无构建、求解器/VTK调用或时间推进。现NUMERICAL_GATE=NOT_EVALUATED、RESULT_PASS=false、geometry_PASS=null、REFERENCE_QUALIFIED_FOR_CASE=false、MODEL_COMPARISON/physical_validation=NOT_EVALUATED，reference_qualified/strict_error_bound_established/submission_ready=false。S0/S1接受、旧FAIL/380差异、MRP静态FAIL、D4预测HOLD、F04 OPEN等保持。

下一具体动作：收到明确六条正式授权后，重新核对资源/封存，另存真实性能之外的正式授权证据与独立执行合同、固定SHA；只读验证后交付用户手动命令。本轮核查结果不等于执行授权或科学放行。

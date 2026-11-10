# S2 后续执行绑定接口：字段与边界

本文件是操作说明，不是授权文件。当前只有关闭许可的A封存，尚无零步/性能/正式执行release；禁止把下面的字段说明复制成虚构用户授权。实际用户原话、身份及SHA必须来自届时真实证据。已有明确覆盖的授权不重复询问。

## 1. 原生零步release

从当前A封存另存新文件，保留全部原A输入哈希和六条正式/18条审计准备记录。新增并绑定A文件本身的绝对路径/SHA、实际零步授权证据JSON的绝对路径/SHA；二者加入inputs_sha256。引用当前A的外部SHA，以 `PREPARATION_A_SHA256.txt` 为核对入口；不得只算一遍修改后文件的哈希便称“已绑定旧A”。

执行release字段：kind=AUTHORIZED_ZERO_STEP_AUDIT_RELEASE、stage=S2_REG_GRID、native_zero_step_authorized=true、simulation_authorized=false、performance_time_stepping_authorized=false、approved_runs/approved_run_ids=[]。preparation_A_path/sha256必须是当前A；approved_audit_run_ids必须按原顺序覆盖18个zero_prepared_runs的run_id，不得使用正式身份。

audit_authorization含user_explicitly_authorized=true及真实user_instruction_verbatim；audit_authorization_evidence含证据文件path/sha256。实际证据JSON必须同存该原话、user_explicitly_authorized=true、stage=S2_REG_GRID、native_zero_step_authorized=true、formal_simulation_authorized=false、performance_time_stepping_authorized=false和完整approved_audit_run_ids。

准备后先只读核对新release和外部SHA、原A、真实授权及资源，随后才交付用户手动后台命令。本任务没有创建这种release或命令。

## 2. B封存

只有全部18次原生调用正常退出、0时间推进、六个初态场实际读取后才会有真实审计verification及raw哈希闭包。finalize-zero读取原A和这些记录，另存preparation_B.json，包含A、零步授权release、原始审计记录/字段payload/收据；所有执行授权仍关闭。缺项拒绝，不产生B。

## 3. 正式release

必须另获六条正式计算授权，先绑定真实B文件preparation_B_path/sha256并保留B全部输入、原零步路径/SHA、准备身份。kind=AUTHORIZED_EXECUTION_LAUNCH_RELEASE、simulation_authorized=true；approved_runs/approved_run_ids必须与六条prepared完全相同，不能把性能或零步编号挪入。

launch_authorization含真实原话与明确授权标志；launch_authorization_evidence绑定证据path/sha256。证据JSON必须同存原话、stage=S2_REG_GRID、formal_simulation_authorized=true及精确六条approved_run_ids。新证据和B本身加入输入闭包，外部固定release SHA，执行前后重哈希。仅改变A的布尔值或持有旧S1许可会被拒绝。

正式单条时限保持5nm=3600s、2.5nm=14400s、1.25nm=43200s，其他资源见A。失败即停，不自动延时、重试、评分公式或启动S3。若另定部分网格执行范围，需先另审其合同版本，不能直接删当前六条。

## 4. 性能推进

使用已采用的S2-MIP-v1-PERF协议和独立授权/身份/目录；不能传给上述零步或正式入口。当前任务没有实现性能执行器，也没有性能授权、标定结果或启动命令。性能证据永远不代替B零步证据或正式参考结果。

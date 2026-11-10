# 实际专用工作卷及限定无求解探针：完成与独立核验

2026-10-26；当前入口。此前REPORT.md/首次final_verification.json是等待管理员挂载时的历史快照，原样保留。用户已在本机挂载；本轮读取实际状态确认后执行已授权的mounted探针，没有启动求解。

**结论：PASS_BOUNDED_ENVIRONMENT_PROBES_ONLY。** 独立512MiB工作卷、持久盘小文件、微型缓存库编译加载、真实容量耗尽、卷满时独立退出记录、人工成功/失败档案持久化及副本读回均通过。该结论仅针对本轮环境/文件链，不是N8实际计算、物理验证或运行许可通过。

## 1. 实际挂载与资源

- 工作挂载点：`/run/user/1000/sim240_pilot_n8_work_20261026`；来源名sim240-pilot-n8；独立tmpfs、设备0:87、mount_id9170；容量536870912字节（512MiB）。rw/nosuid/nodev、无noexec；uid/gid1000:1000、0700。
- 持久记录父目录：`/home/dell/yuanyuanxu/SIM240_runtime_records/reference_pilot_n8_20261026`；ext4、设备259:2，与工作卷不同；权限和余量符合原要求。
- 执行前后路径检查均LAYOUT_CHECK_PASS_ONLY，全部布尔条件为true；工作卷恢复为空、可用容量536870912字节。独立复核后再次检查仍通过，证据`evidence/current_layout_verified.json`。
- 本轮没有执行mount或修改系统服务/fstab；本轮确认的是用户已完成的实际挂载，不以“命令已交付”代替证据。

## 2. 限定探针实际结果

|阶段|实测结果|原始证据|
|---|---|---|
|B 持久盘小文件|写1048576字节，文件/目录fsync后重新读SHA一致|mounted_after_user.json/persistent及持久probe_result.json|
|C 缓存兼容性|仅返回240的微型共享库编译exit0；另进程加载/调用exit0、输出CACHE_LOAD_PASS|controller目录compiler/loader的stdout、stderr、exit_code；源/库SHA|
|D 工作卷容量边界|成功实际写入536870912字节后ENOSPC（errno28）；可用字节为0且仍有4067470空闲inode，支持是容量耗尽而非inode耗尽|capacity_probe.json、fill哈希及mounted_after_user.json|
|D 卷满时独立记录|固定写入探针进程exit28；持久盘独立退出码保存成功|full_volume_child.independent_exit_code及日志|
|E 人工成功档案|子exit0；22个文件完整归档；删除已核准的人工源后，副本数值关系与记录绑定读回通过|VOLUME_PROBE_success_a741409d5373及independent_success_readback.log|
|E 人工失败档案|子exit7；3个文件及partial.bin完整保留；档案完整性读回通过，失败状态不改|VOLUME_PROBE_failure_e26dedcc7bd7及independent_failure_readback.log|
|F 最终状态|只清理本次明确探针/人工源文件，工作卷为空；持久副本与日志保留|layout_after及current_layout_verified.json|

主入口`probe_volume.py --phase mounted`独立exit0，结果BOUNDED_VOLUME_PROBES_PASS_ONLY；证据为`evidence/mounted_after_user.json`、`.stderr.log`、`.exit_code`。没有覆盖前一轮未挂载时exit2拒绝快照。

本次controller记录目录：`/home/dell/yuanyuanxu/SIM240_runtime_records/reference_pilot_n8_20261026/volume_probe_mounted_99a7e052de40/`。文件系统探针与人工档案的编号都不是实际流动计算run_id；合同保持false/null，全部标FILESYSTEM_PROBE_NOT_PDE或SYNTHETIC_PROCESS_NOT_PDE。

## 3. 独立核验与来源

`verify_mounted.py`只读原始文件/记录并另进程读回，没有编译、写满或求解。结果PASS_BOUNDED_ENVIRONMENT_PROBES_ONLY，独立exit0；见`evidence/mounted_independent_verification.json`、`verify_mounted.log`及exit_code。

独立验证包括：

- 重读1MiB已知文件的大小/SHA；按512个1MiB的已知V字节块独立重算fill哈希。
- 核编译器/加载器真实退出文件及加载输出；核卷满进程独立exit28。
- 对成功22份/失败3份归档逐文件重算大小和SHA，核合同/来源/运行标识/原work路径绑定，前后来源一致、源已移除及失败partial.bin内容。
- 另进程仅从持久副本读回，两个入口exit均0。失败档案只通过完整性检查，原子进程退出7、RESULT_PASS=false保留。
- 核358条v3.1来源、4233历史保护文件及319份旧v3文件均无SHA差异；集合重叠不相加。原v3.1的12项与历史32项测试未重跑，原科学协议、模型锁和旧FAIL未修改。

## 4. 停点与边界

本轮真实工作卷和持久文件链的环境阻碍已消除，不再把“未挂载”列为当前卡点。工作卷是本机当前临时挂载，实际求解前须再核当时的卷/空目录与可用资源；不能用本报告代替启动时检查。

尚未执行N8真实后端，未证明真实矩阵在4GiB/600秒内收敛，也没有解析误差、通量/能量、完整18项、沟槽参考或公式预测的新结果。微型库不是OpenLB编译，人工矩阵不是物理解；环境测试通过不自动批准求解。

下一步只审首项B0MIN_MMS_mixed_N8的v3.1合同、实际路径配置、来源锁及运行许可条件。仍不自动执行N8或第二项；没有批准合同、实际流动run_id、Git提交或推送。NUMERICAL_GATE=NOT_EVALUATED、RESULT_PASS=false、geometry_PASS=null，预测HOLD。

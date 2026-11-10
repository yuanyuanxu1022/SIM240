# v3合同、实现证据与工作卷方案审查

2026-10-26。用户授权仅审查并具体化路径/核查方案，继续不启动计算。结论 **HOLD_NO_RUN_PERMISSION**：v3已补齐前次主要记录链，但放行前还需一项小范围类型分流修补、实际卷核查和单项授权。无需重做完整研究设计或先跑完18项。

按scientific-critical-thinking的观察—影响—补救方式审查。对象为`reference_backend_min18_20261025/pilot_record_v3_20261026/`，下称P。未修改该目录任何文件；本轮证据在audit_evidence.json、audit.py、audit.log及review_inputs_sha256.json。

## 1. 已得到本轮支持的结论

|内容|复核证据|判断|
|---|---|---|
|来源/历史完整性|356项来源、318项v3最终包产物、359份v2文件、4233项历史保护文件、138项前次终审输入逐项SHA一致；集合重叠不相加|没有发现既有绑定漂移。|
|既有32项测试|原log/summary/独立exit0一致，0失败/错误/跳过；本轮没有重复启动短测试进程或OOM测试|保持既有无求解准备结论。|
|向量—场关联|P/readback.py:81–110明确独立按保存周期系数构造Tx并比较r；检查单位系数、从属唯一和主从不相交|前次R1缺少重建关系的问题已在实现中补齐；不据此推断真实后端精度。|
|持久归档|P/archive.py停止写入前提、源/副本大小SHA复核、文件/目录刷新、完成发布及失败保留；runner将归档失败与子退出码分开|前次R2只有tmpfs原始数据的问题已在代码中补齐。|
|既有档案读回|本轮只读12份已保存人工进程档案，档案完整性均通过，失败退出原因保留；源已移除的人工成功档案读回/数值关系核对通过|说明已保存人工档案链有效，不是12个物理算例。|
|默认拒绝|原模板纯执行许可校验拒绝DIAGNOSTIC_RUN_NOT_AUTHORIZED；新路径草案准备校验通过，仍false/null|没有批准包、实际run_id或求解结果。|

## 2. 放行前的一项代码修补：记录类型必须先严格核对

**源码位置：** P/readback.py:138–203。函数只在`capture_manifest.kind == REAL_DIAGNOSTIC_UNVERIFIED`时进入真实结果的完整检查，否则直接走较简的路径；没有先拒绝未知kind，也没有统一检查STARTED、capture和系统/场类型之间的对应关系。`check_archive`也未要求STARTED与capture的kind一致。

**本轮反例：** 读取原已存人工成功档案，在内存中仅将capture_manifest.kind改为`UNKNOWN_REVIEW_INJECTION`；其他文件、数值和哈希完全不变。调用实际v3的check_capture，得到`CAPTURE_BINDING_PASS`，kind仍为该未知值，22份工作文件校验。反例保存在audit_evidence.json/kind_counterexample，audit.py可复现。

**证据边界：** 这是对元数据解析的人工注入，没有修改原档案，没有制造真实结果或批准合同，没有声称真实数据已通过错误验收。它证明“未知类型会拒绝”的性质当前不成立；结合if分支可知类型错误可能跳过要求较完整的检查。因此本轮不能把“真实结果必需记录验收已全面闭合”作为放行依据。

**最小补救，先于选择验收分支：**

1. 父进程STARTED.kind与capture.kind必须一致，只接受已定义的`REAL_DIAGNOSTIC_UNVERIFIED`或`SYNTHETIC_PROCESS_NOT_PDE`；未知、缺失、不一致均拒绝。
2. 真实父记录必须对应真实system/solution元数据，且两者一致；人工父记录只能对应既定人工数组类型。当前人工类型为`SYNTHETIC_MANUAL_ARRAYS_NOT_PDE`，不能机械要求它与父记录字符串字面相同，应显式定义对应表。
3. 独立check/main同样拒绝未知数组类型，真实数组必须要求匹配的真实父记录；archive-only保留失败档案完整性范围，但核父记录类型一致且已知。
4. 补未知类型、STARTED/capture不一致、真实/人工串标签、缺父记录和两条合法路径的定向测试。用小补丁并重新绑定来源，保留v3快照；不需要组装或求解，也不必扩大数值验收范围。

## 3. 合同口径与非阻塞文字修订

本轮认可将这次首项限定为**受限求解/记录诊断**：N8、GMRES/PC NONE、零初值、restart50/max2000、rtol/真实残差1e−10、atol0；600秒检测加5秒终止宽限、4GiB内存、512MiB工作卷保持。是否真实收敛正是将来单项诊断要回答的问题，不能先要求它完成再批准诊断。

v3原始数组实际为17组，合同前文遗留16组、增补段明确17组。现有实现/新增段已说明，不构成新的物理问题；下次小补丁发布时将新合同前文统一为17组并重新绑定，旧v2不改。P/solver.py顶部沿用“v2”说明也应一并澄清。不要因文字清理重复实施全套科学验证。

解析场L2、通量/能量、完整18项和沟槽参考仍NOT_EVALUATED；本次诊断通过也不能解除预测HOLD。原协议、候选G4 v1及窄槽网格FAIL保留。

## 4. 实际路径方案与当前环境结论

已形成[VOLUME_PLAN.md](VOLUME_PLAN.md)和未授权的[path_contract_draft.json](path_contract_draft.json)。拟定工作卷`/run/user/1000/sim240_pilot_n8_work_20261026`，持久记录父目录`/home/dell/yuanyuanxu/SIM240_runtime_records/reference_pilot_n8_20261026`。持久目录在Git仓库之外，落在现有ext4磁盘；工作卷需额外挂载一个专用512MiB tmpfs，不能直接使用容量更大的公共/run/user/1000或/dev/shm。

本轮只读资源快照及来源见audit_evidence.json，内存约16.79GiB、持久父级磁盘约336.97GiB；拟定目标目录均不存在。只读脚本precheck_layout.py实测返回LAYOUT_NOT_READY/exit2，原因是两个目标目录未创建；memory/pids委派及内存下限检查通过。磁盘/内存余量不是已预留额度，启动前重新核对。

工作卷要能加载JIT缓存生成的扩展库；不要配置noexec。该要求来自本机DOLFINx/FFCx加载源码与[Linux mmap手册](https://man7.org/linux/man-pages/man2/mmap.2.html)的PROT_EXEC约束。详细挂载选项、权限、实际空间耗尽及失败归档探针、持久副本独立读回顺序均列于VOLUME_PLAN；本轮未挂载、编译探针、写满或新建cgroup。

## 5. 停点与最短接续

先补记录类型一致性这一处小修补并重绑，随后按已列路径执行经授权的无求解卷准备/探针，再审定首项配置和运行许可。当前没有任何求解启动命令；审批对象仍只有B0MIN_MMS_mixed_N8，不自动运行第二项/全18项。

本轮仅新增独立审查目录和同步项目状态/交接；没有修改v3代码或原证据，没有OpenLB编译、建网/组装/PDE求解、拟合、协议冻结、Git提交或推送。NUMERICAL_GATE=NOT_EVALUATED、RESULT_PASS=false、geometry_PASS=null、预测HOLD。

# v3.1 记录类型补丁、针对性无求解测试与实际卷核查

2026-10-26。用户授权补记录类型一致性、完成针对性无求解测试，接续实际工作卷核查，继续不启动计算。

**结论：记录类型补丁通过限定测试，整体仍为PASS_PREPARATION_ONLY；实际卷LAYOUT_NOT_READY，求解未授权。** 本目录为独立修订，v3代码和原证据保持不变，没有实际run_id或新物理结果。

## 1. 修改的实际行为

P/readback.py（P为本目录）增加显式对应表及公共检查：

|父记录类型（STARTED和capture必须一致）|允许的system/solution数组类型（两者必须一致）|
|---|---|
|REAL_DIAGNOSTIC_UNVERIFIED|REAL_DIAGNOSTIC_UNVERIFIED|
|SYNTHETIC_PROCESS_NOT_PDE|SYNTHETIC_MANUAL_ARRAYS_NOT_PDE|

未知、缺失、父记录不同、system/solution不同或两组交叉标签均拒绝，检查发生在选择真实/人工验收分支之前。archive-only同样要求父记录类型明确且一致；失败/部分档案不强求完整数组存在。

公共check与CLI都要求真实数组提供父记录。数值数组复算移入私有_check_arrays，真实完整验收可在内部调用它，避免公共入口与父记录检查递归；独立残差、重建r=Tx和原阈值保持。真实标签的人工拒绝输入不构成真实计算结果或批准包。

新合同统一成功原始场为17组，版本为D4_PILOT_RECORD_V3_1_20261026_PREPARATION；清理新solver说明中的旧版本字样。common和真实读回的版本/合同定位同步更新，源码重新绑定。原物理plan、18项CSV、求解设置、容差、预算、G4锁及旧FAIL不改。

## 2. 针对性验证

证据：`evidence/test_kind_no_solve.log`、`test_kind_no_solve.exit_code`、`test_summary.json`。

- **12个测试方法，0失败、0错误、0跳过，0.392秒，独立exit0。** 方法内含多种缺失/未知/不一致输入，不把子反例数量当独立算例数。
- 同一份上轮内存注入反例：原v3仍返回CAPTURE_BINDING_PASS；v3.1在类型分流前明确拒绝PARENT_RECORD_KIND_UNKNOWN_MISSING_OR_MISMATCHED。原始文件未改，未创建真实结果或批准合同。
- 合法的两组标签映射通过纯逻辑测试；既有人工成功归档完整读回通过。真实路径只检验标签对应和未授权拒绝，没有启动真实后端或生成实际获准记录。
- 未知/缺失父类型、STARTED/capture不一致、未知/缺失数组类型、system/solution不一致、真实/人工交叉标签、archive-only未知类型都拒绝。公共check及CLI对真实标签但缺父记录也拒绝。
- 既有12份v3人工成功/部分/超时/OOM档案只读检查通过，exit7及OOM原因保持。没有重新运行进程夹具、OOM或整套32项历史测试；仅CLI拒绝测试运行了短Python读回进程，没有PDE模块。
- 1→7重建反例仍返回数值FAIL，误差6，说明补丁未停用已有数值关系检查。真实runner与public solver仍在创建进程/KSP前拒绝未授权模板。
- 默认准备CLI另进程exit0，见`evidence/cli_check.json`；无--execute。没有PETSc/DOLFINx/UFL加载，没有真实KSP或求解。

独立标准库核查见`evidence/independent_preparation.json`：17模块语法、358条新来源SHA保持，旧v3的319份文件、v2的359份文件、4233历史保护文件、138项前次终审输入均无变化；集合重叠不相加。原18行继续false/无actual_run_id；新模板及实际路径草案继续false/null。

## 3. 实际工作卷核查结果

本轮已生成绑定v3.1的`path_contract_draft.json`，通过纯准备校验；实际run_id仍占位。

|实际检查目标|本轮实查|
|---|---|
|`/run/user/1000/sim240_pilot_n8_work_20261026`|不存在；父级/run/user/1000为公共tmpfs，不能替代专用512MiB挂载点。|
|`/home/dell/yuanyuanxu/SIM240_runtime_records/reference_pilot_n8_20261026`|不存在；最近现有父级/home/dell/yuanyuanxu为ext4、可写，但不是已建立的记录目录。|
|内存余量与memory/pids委派|只读检查通过；余量是时点快照，不等于预留。|
|完整静态卷预检|LAYOUT_NOT_READY、独立exit2，两个目标目录缺失。|

证据：`evidence/layout_precheck.json`、`layout_precheck.exit_code`、`layout_snapshot.json`。precheck_layout.py只读取目录、mountinfo、容量、权限、内存及委派，未创建目录、挂载或写出探针。

后续沿用`docs/reports/D4_pilot_v3_review_20261026/VOLUME_PLAN.md`：专用512MiB tmpfs（需允许缓存库加载）、独立ext4持久目录≥2GiB、属主1000:1000与0700；实际准备后做小文件刷新读回、限定共享库加载、容量耗尽与失败留档、持久副本独立读回，恢复空卷后再核。当前B—F未实施，不将软件类型补丁PASS当成卷准备或运行许可。

## 4. 停点

本轮完成类型补丁和针对性测试，并给出了实际卷缺失的当前证据。未启动求解、建网、组装、OpenLB编译或新进程夹具；未挂载/更改系统配置、公式拟合、原协议/阈值变更、Git提交或推送。

下一步是实际专用工作卷与持久目录准备及限定无求解探针，之后审首项N8许可。真实后端成功/失败端到端仍未验，完整18项/数值参考/公式预测不自动推进。NUMERICAL_GATE=NOT_EVALUATED、RESULT_PASS=false、geometry_PASS=null、预测HOLD。

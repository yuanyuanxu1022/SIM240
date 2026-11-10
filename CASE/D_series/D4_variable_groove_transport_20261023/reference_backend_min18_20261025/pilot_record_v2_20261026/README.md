# 三项缺口修订 v2：独立许可、完整记录、资源停止与读回

用户授权仅准备与无求解测试，2026-10-26。本目录所有真实入口默认拒绝；contract_template.json含false，approval为空。**本轮没有真实求解或批准运行。** 不修改原18项CSV、静态contract、旧求解候选、G4锁、旧网格FAIL。

主要入口：common.py定义新合同；assembly.py只复用旧物理接口/零空间方法，增加投影前b；solver.py使用新合同并补KSP创建/快照失败的记录；worker.py核父子来源再工作；runner.py默认只检查输入；resources.py落实有限时停止及硬资源前提；readback.py独立读取已有数组，绝不求解。

source_lock.json绑定全部必需源码/协议/依赖及解释器/核心库；模板本身也是含source lock摘要的明确待审对象。物理plan保留execution_authorized=false，真实执行权限属于新合同，不通过改旧flag或猴子补丁获得。真实入口目前无有效批准合同；测试不产生此类合同。

独立读回入口是`readback.py <已有工作目录> --record-dir <对应父进程记录目录>`。它只读文件并向标准输出JSON，不修改运行文件，不自动验收其他项目。对真实记录缺父进程记录即拒绝。合成记录的PASS仅说明保存/复算链测试，不是物理PASS。

资源实现区分：20ms抽样超时/进程树RSS/输出仅作监督；真实内存依赖cgroup v2，输出依赖已有专用小容量tmpfs。缺任何硬资源条件均在创建真实进程前拒绝，不自动挂载或修改系统。临时测试可使用小型自建cgroup，仅包含固定合成进程，结束删除。工作卷准备与实际后端端到端仍须未来审查，不因代码存在视为已具备运行条件。

无求解测试入口test_no_solve.py；报告/日志/独立退出保存在evidence。verify_preparation.py只做标准库证据、来源和状态核对，不导入后端。测试包括手写小矩阵/向量、假KSP对象和固定短进程；不导入PETSc/DOLFINx、不组装/求解PDE。

准备报告PREPARATION_REPORT.md给出本机测试覆盖、未测项和资源前提。所有正式Gate及预测保持原状态。

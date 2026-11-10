# A1 精确源码绑定与检查器候选

本目录是新隔离副本。analysis/和common/全部保持上一MRP候选字节；原数值检查与门槛继续保持。新revision_anchor.json只绑定此次A1实际源、最小diff、采用记录及静态审计文件；原source_preparation_anchor.json保持。

instruction_audit_status=PASS表示此次已采用观察量范围的静态检查通过，不是原生运行或科学结果通过。本轮没有执行合同、正式run_id或运行授权。对审计FAIL的拒绝守卫保留，并以人工失败视图的软件负例验证；实际新构建的完整来源闭包软件核对另有正例。

最终107项软件测试通过（此前103项保留，增加4项A1检查），包括57600个体积空间前缀逐位一致、旧融合路径196个前缀差异可检出、夹具与native采用相同源码表达式，以及实际新构建来源校验。C++夹具不含OpenLB，不能代替原生零步或流场验收。

报告：`../../docs/reports/URV_MRP_v1_A1_implementation_20261102/REPORT.md`。README_MRP.md等复制说明是上一失败候选历史快照，当前状态以本文件和共享状态为准。

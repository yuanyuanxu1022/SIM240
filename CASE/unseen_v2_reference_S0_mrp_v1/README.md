# URV-MRP-v1 隔离实现候选：静态审计 FAIL，HOLD

本目录实现旧质量的显式 binary64 运算、同次 rho 采集和实际构建证据。报告入口：`../../docs/reports/URV_MRP_v1_implementation_20261102/REPORT.md`。

**构建成功不表示可运行交付。** 质量 helper 的三次舍入与最终 FMA 已在实际 ELF 核对；编译器同时把 volume 最后乘加融合，违反非质量运算不变要求。GPT-6 Astra｜High 只读裁定保持 HOLD，当前候选保留，不再修改或构建。后续局部体积舍入屏障仅在报告目录中作为未采用草案。

无 `runs/`、正式 run_id、启动合同或启动命令。原生 describe/precheck/initialize/steady 均未执行。密度采集器仅在无 OpenLB 的合成软件夹具中检查；没有真实密度或流场新结果。完整原生零步安装、来源闭包运行验收、两方向回归及密度重放仍待。

`src/Makefile` 保持旧 v1.2 原字节，含可推进编译标志；没有授权就不得直接调用二进制。`scripts/build_capture.py` 仅作实际构建记录，不调用原生程序；它拒绝覆盖本次构建。

原 URV-v1、URV-MRP-v1 协议副本在 evidence/；原始封存位于旧目录，未改。补证 Python 代码在同级 `unseen_v2_reference_checker_mrp_v1/`，其精确来源分支对本候选的 instruction_audit_status=FAIL 明确拒绝，不能用于正式验收放行。

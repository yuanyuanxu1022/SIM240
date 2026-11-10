# 正式S4范围与资源决策审查

日期2026-11-04。结论：推荐采用S4-FRD-v1完整六条、原顺序、原1/4/12h求解上限；每条标准独立检查外层1h，前条完整接受才继续；失败停。当前不强制额外S4 PERF，前提为后续用户明确接受细格12h可能超时、批次不完整的风险。方案未获采用或正式执行授权，无实现或启动。

推荐依据：有效B3248输入/原18＋6及独立复核通过；同ELF完整S2六条（222原始输出）当前一致，细格P6.538h/T3.754h；较早S2 PERF带既有S2-LRP唯一日志例外保留观察RSS/短段速度用途。S4流体节点为对应S2的70%，但没有S4持续性能或收敛步数实测，不能据此保证更快。走满S4最大步数再假设0.7步成本，约32.26/32.06h；这是条件成本，不是预计收敛时间。单独短PERF也不能保证12h收敛。

预算：六条求解34h＋六条检查外层等待另最多6h；内部读取器1h含在各自外层内。文件处理/核对/网格汇总/清理另计，40h不是硬批次总上限。资源仍8GiB每受限进程地址空间、批次前RAM12/盘100GiB、每条前RAM12/盘8GiB、原生输出4GiB；不冒充全程RSS或整个进程树限制。继承检查器超时后代清理限制已明确，不修改冻结代码。

正式接口已有独立资源采用门；推荐路线可直接复用冻结B/同ELF/当前六条程序，无需代码修改或编译。仍须真实采用S4-FRD-v1并另授权完整六条，绑定真实授权＋独立资源采用记录，重查届时资源/净目录/冲突/来源后，才生成新正式release与一条用户手动命令。本轮只交非执行candidate/plan，权限全部false，无正式release/命令。

本轮初版文档辅助核对在读取历史S2 PERF清单时，先要求全部相同，触发已封存的唯一控制日志差异；之后按原S2-LRP精确校验路径/旧SHA/现SHA/大小和已绑定快照，61项仍同，恰1项已记录例外。初稿audit_scope_initial.py.txt和review_helper_note.json保留。未新增例外、未改旧清单、未重判旧完整性通过，没有重放求解/场/检查器。科学门槛和历史FAIL不变。

入口：PROTOCOL.md（完整范围、门槛、条件和限制），six_run_scope.csv/json，resource_evidence.json，resource_snapshot.json，resource_decision_candidate.json（未采用），formal_binding_plan.json（非执行），PERF_log_exception.json，scope_audit.json。最终保护核对见final_integrity.json、文档清单document_manifest.json。AI辅助内部技术审查，用户保留科学责任；技能说明及公开出处已在协议末注明。

科学状态保持：正式S4未评价/未运行，参考资格false、模型/物理未评价、submission_ready=false、F04 OPEN；S0—S3接受和原失败/限制保持，不进入S5。

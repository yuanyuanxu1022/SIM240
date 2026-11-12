# v2.1 定点修复、边界测试与指定Astra静态复核完成

2026-11-11。作者授权本轮修复、合成测试和GPT-6 Astra High新快照静态审查；没有求解启动授权。采用peer-review的证据定位与范围控制，属于作者自审工作稿，不是期刊裁定或人工数值独立验收。

## 结论

五项旧阻塞及coarse预算冲突已关闭；指定模型新快照静态审查剩余阻塞0。正式目录CASE/paper1_fvm_stokes_reference_v2/已同步为受审文件同字节版本，46项合成测试在隔离候选和正式路径均全过。无任何新PDE/编译/网格工具/mapFields运行，run_id=null。

最终release SHA：f1531d4091a6279a5db2df5cff75875d279d4ffc981f52ae5502bedd98ffc292，212本地+23外部指纹0漂移。指定模型报告见ASTRA_REVIEW.md，sync_verification.json证明正式目录与受审候选同一；verification.json为最终摘要。

## 修复实际范围

- acceptance.py为唯一机器规则源（version=v2.1_stopping_fix、declared_residuals.normal/tight、branches），prepare写清单，runner与reader使用同一函数接口，后者独立读原日志/CSV再核回执。消除混合接口/schema，不以函数命名本身判科学正确。
- 沟槽P查v；T查完整Ux/Uz/p，若输出Uy也检查。普通严格<1e-10、tight<1e-11；tight线性精度保留。仅T d=0 flat可按幅值比例≤1e-9及解析导度/剖面≤0.1%的限定例外接收，P平板不查不存在字段。
- 末尾End、独立退出码、固定源码完整末轮顺序、native报告时间及原生终场时间均核对。正常上限结束可经完整条件接收，停止原因与接收结果分开；超时/异常拒收。依据本机Time::running处理start=.5的半步上限，非简单计数=endTime。
- seed源按本release完整独立读回接收，绑定run/receipt/release/最终原场/mesh；工具mapFields加入外部指纹，并绑定argv/log/exit与目标输入副本。副本置runtime/seed_inputs，防purgeWrite清除0.5后无法核验。后处理递归核层链。
- 零值有限非负检查，无零分母。回执stopping与同日志独立重算字典严格相等。same_residual辅助边界函数另有零/零、一零一非零测试，不用于放宽正式字典一致性。
- coarse墙钟1800s、flat3600s；其他预算不改。耗时不作为保证，不自动增配。coarse/mid不增加最细0.1%收支门槛。

## 并发冲突与归档

中途发现另一会话同时改postprocess/prepare；tests_initial.log保留该混合接口造成的46项中12 error，不能作为最终候选结果。用户确认另一会话已暂停后，本会话在隔离候选从受审旧基线恢复并修复；最终tests_candidate_final.log与tests_formal_final.log均46/46通过。

唯一旧v2基线v2_unreleased_snapshot.tar.gz哈希714cf113390e97640728c40895fa5b01673df99be0f0a68d24860fe201e3517c，含原release 68453dac…全部绑定文件。另一会话partial _archive中的11份绑定文件已从该tar逐字恢复，MANIFEST注明来源；未绑定CURRENT_STATUS仅保留作辅助旧记录。修复前partial_archive_before_repair.tar.gz、混合源码concurrent_editor_observed.tar.gz和同步前mixed_worktree_before_sync.tar.gz均本地保留，不冒称受审旧版。隔离候选仅为审查工作副本，正式使用入口唯一为CASE/paper1_fvm_stokes_reference_v2/。

## 不改变的科学身份与下一步

C++源码、ELF、物理网格/边界/初值/物性/驱动/fvSchemes和comparison_inputs与旧受审记录一致；主稿、补充、结论、投稿MANIFEST及36条主统计不改。固定四几何六方向、3网格+6tight+2flat共26输入，不新增方向，不改2%/2%/0.40度比较门槛。旧v1 T及S4/D4 FAIL、reference_qualified=false、strict_error_bound_established=false、submission_ready=false保持。

release内PENDING_ASTRA_V21_RECHECK及numerical_execution_authorized=false保留为冻结控制元数据，不能用它否认本轮审查已经完成；也不能因外部报告完成擅自解锁启动。后续仅在作者授权求解后，处理同一快照审查元数据/身份记录，再先分别启动并验收本版P/T平板，合格后才到固定沟槽。若只更新发布审查元数据，须保存本受审release并证明科学绑定文件未变；不需要因目录同字节同步重新审科学规则。

本轮交接已同步SIM240_AI_CONTEXT.md与AI_HANDOFF_PORTABLE_20261104.md；无commit/push/投稿。

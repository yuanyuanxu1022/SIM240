# 窄槽四项1.25nm最细网格准备入口

先读PROTOCOL.md、policy.json和项目docs/reports/SIM240_AI_CONTEXT.md。只准备stage_cases.csv四项，继承已验收中格上游证据，旧阶段/原求解器/冻结容差/G4锁保持。

start_from_project.sh默认--check；准备核查及release通过后，唯一用户启动命令位于NEXT_COMMAND.txt。只有用户明确--execute才创建正式批次，已有batch/case拒绝重跑，不自动进入其他阶段。

prepare_stage.py仅做describe/precheck零步。test_preparation.py用已有数据与人造数据验证程序，不执行steady。bind_release.py冻结本机输入，已存在release不重写。

计算完成后，由用户另行发起独立验收：accept_batch.py生成完整证书，再显式调用finish_grid_review.py导出16行有来源的参考并比较两个窄槽的六量三格关口。宽槽最细缺项时全局仍INCOMPLETE；窄槽失败不能被全局缺项掩盖。任何状态都不自动发下一批许可。

准备记录：项目根docs/reports/D4_grid_narrow_fine4_preparation_20261024/REPORT.md。准备文件为冻结时快照；启动/完成/独立验收状态以项目当前入口和新验收报告更新，不改本目录旧绑定文件追记。

# 单项诊断记录 v3.1：独立关联与持久归档准备

2026-10-26；本目录由v3另版作类型分流小修补，不修改v2/v3及历史证据。所有真实入口仍默认拒绝，contract_template.json为DRAFT_NOT_AUTHORIZED、false、approval=null；无真实run_id或PDE结果。

common/assembly/solver/worker保留原单项门禁和物理方案；worker额外保存周期系数（原始场17数组）。readback只用NumPy/标准库重建r=Tx、核必需记录/来源/环境/阶段/资源。archive在停止写入后复制全部已落盘文件到持久副本，大小/SHA/文件目录fsync成功才发布完成；失败保留源/部分副本与独立退出码。runner区分子进程退出与记录/归档结果，缺实际硬资源卷仍执行前拒绝。

独立读回入口：readback.py <已有原始work或record/archive> --record-dir <对应record>。只读、不启动其他项；实际运行原路径仍在合同中，不为移动副本改合同。真实记录同时要求对应持久档案。

test_no_solve.py继承16项无求解控制测试并增加反例/必需记录/归档拒绝；仅人工数组、假KSP和固定短子进程。部分测试写“真实记录所需schema”模拟数据，均标SYNTHETIC_SCHEMA_NOT_PDE且合同仍false，不形成批准包或物理结果。

本轮不挂载、不启动PDE、不改原18项或G4锁/旧FAIL、不提交推送。真实≤512MiB专用卷及其真实写满路径、实际后端成功/失败链仍待审查；合成测试不替代它们。PREPARATION_REPORT.md与evidence记录实际验证边界。

本轮针对性入口test_kind_no_solve.py：只读取已有人工归档或生成手写数组，不调用求解器、不启动进程夹具；旧test_no_solve.py/legacy保留作回归入口，本轮不自动整套重跑。precheck_layout.py只核实际路径、卷、权限和资源，不创建目录/挂载或执行写出探针。当前结果见PATCH_REPORT.md及evidence。

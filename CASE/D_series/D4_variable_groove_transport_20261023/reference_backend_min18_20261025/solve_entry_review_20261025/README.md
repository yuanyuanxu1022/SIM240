# 9 项混合矩形的待审求解入口：压力零空间接入与运行前核查

2026-10-25。用户授权把前一轮核对正确的**约化常数压力向量**纳入待审求解入口，并保持不求解。本目录是一个可供未来审查的**组装—压力规范接口**，不是求解器、运行许可或新协议。入口 `entry.prepare_bound_mixed_system(planned_id)` 返回实际矩阵、右端、网格、MPC 和已登记的压力零空间，供后续单独审查；命令行只接受 `--mode preflight` 和原白名单中的混合问题 ID，`--solve`、`--execute` 和 `--mode solve` 均拒绝。没有 KSP、`solve()`、物理场、正式 run_id 或输出目录。

## 接入方式

复用上一实际网格接口和原 UFL Stokes 弱式，不改旧文件。每项先按原白名单组装 `A`、`b`，施加固壁零速度和 x 周期 MPC；从物理常压候选中删除**所有周期从属自由度位置**并归一化，严格核其压力主从对应关系和速度分量为零。对真实矩阵分别核 `A n` 和 `Aᵀn`、`nᵀb`，并要求 PETSc 零空间测试通过；其后把该向量登记为矩阵的右/左零空间，并投影右端。这里的 `1e-10` 是沿用上轮接口的**局部预检拒绝值**，不宣布原待审参考协议的容差生效。未通过检查时，接口拒绝，不能继续到求解。

另外，用 MPC 的回填操作检查：把约化向量的从属位置按周期主点补回后，压力在实际 P1 自由度上恢复常数。这个操作仅作用于测试向量，不是计算得到的压力场。实际矩阵 CSR 与右端哈希必须与[前一轮 9 项独立组装记录](../pressure_assembly_audit_20261025/evidence/assembly_all9.json)逐项一致；输入来源也按前一记录的哈希重核。当前软件版本、几何、网格、源项、积分阶数及周期设置一并写入预检记录。

## 结果与负例

- [`evidence/preflight_all9.json`](evidence/preflight_all9.json)：9/9 混合项独立进程退出码 0；均登记右和转置零空间、复现前一矩阵/右端哈希。最大右零空间相对残差 `1.7091531021232052e-19`，最大左残差 `1.964428335753306e-19`，右端相容偏差为 0；回填后的常压最大差 `6.938893903907228e-18`。
- [`evidence/negative_controls.json`](evidence/negative_controls.json)：旧的错误向量、故意在压力方程加入不相容右端、标量问题，以及三种求解选项，共 6 个负例均被拒绝。
- [`evidence/independent_review.json`](evidence/independent_review.json)：独立无后端记录复核 9/9；4233 条受保护旧路径及上一接口包 19 个文件哈希不变。脚本 AST 中无求解调用，且记录 `solver_called=false`。

`planned_mesh.constructed=false` 是原静态白名单的历史字段；同一记录中的 `actual_mesh` 和网格哈希记录本轮真实建网，不能把两者混作同一状态。预检耗时是组装开销，不代表未来求解资源或精度。入口只覆盖 9 个含压力的混合矩形，9 个标量矩形没有接入；它也没有完整求解后残差、物理流场、通量/能量、网格误差或正式结果记录接口。只检查了一个预期零模，未做谱分析证明零空间唯一。

当前 `NUMERICAL_GATE=NOT_EVALUATED`、`RESULT_PASS=false`、`geometry_PASS=null`、预测 HOLD；原 18 项 DRAFT_v2 仍未正式启用，运行许可仍为否。未来若启动参考求解，须先独立审查求解器类型、真实残差和收敛、周期迹、压力面积去均值、单位恢复、完整原始输出/输入哈希以及预算；本目录不提供启动命令，不自动放行下一阶段。

API 依据：本机固定 DOLFINx/dolfinx_mpc 0.11.0、PETSc/petsc4py 3.25.6 接口；公开参考为 [DOLFINx-MPC 作者 API](https://jsdokken.com/dolfinx_mpc/docs/api.html) 与 [PETSc 的零空间接口说明](https://petsc.org/release/petsc4py/reference/petsc4py.PETSc.Mat.html)。公开最新版接口可能变化，复现以本目录绑定版本和记录为准。

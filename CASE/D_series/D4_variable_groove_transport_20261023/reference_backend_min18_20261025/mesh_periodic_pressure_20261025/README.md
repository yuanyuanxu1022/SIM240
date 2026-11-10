# 18 项矩形基准：实际网格、周期约束和压力规范接口

2026-10-25。承接同级目录的静态准备 v1，仅在隔离 DOLFINx 0.11.0 / dolfinx_mpc 0.11.0 环境中建立**实际二维矩形三角网格与自由度约束**。本目录是接口准备及静态检查；待审草案中的容差和运行许可没有因此生效。没有物理方程矩阵、右端、流场或正式 run_id。

## 接口和几何

- `interface.build_interface(planned_id)` 仅接受原 18 项白名单及绑定来源。平板在无量纲坐标中为 `[0,3.2]×[0,1]`，制造解为 `[0,2]×[0,1]`，均使用原计划的 `(nx,nz)` 和 right 对角线三角剖分。无量纲恢复规则沿用上级 `protocol/method_contract.json`；这里没有把 240 nm 直接当有限元坐标值。
- 沿槽/标量问题建 P2 标量空间；横槽/混合制造解建 P2 二维速度与 P1 压力混合空间。上下固壁速度/标量零值；压力无点值 Dirichlet 约束。
- 对网格真实自由度逐一列出右边界自由度与左边界同高度、同分量的对应点，调用后端 `MultiPointConstraint.add_constraint()` 完成约束和 `finalize()`。速度在上下固壁交点由壁面条件优先，不列为周期从点；P2 内部边中点全列入；P1 压力两端顶点全列入。发现任一缺失、重复、跨分量、非单位系数或错位，接口即拒绝。
- 早期小网格探查中，直接调用后端自动边界配对在 `P=3.2、nx=48、nz=15` 的混合问题上漏掉部分期望从点；漏点数在独立探查中不同。因而当前明确配对接口仍使用后端 MPC 消元对象，但不依赖该自动搜索返回的集合；`test_missing_periodic_master_is_rejected` 检查缺点必拒绝。此探查没有求解，不推断自动接口在其他版本或并行下的根因。

## 压力规范：准备到哪一步

对混合问题，从**实际** P1 空间生成一个只在压力自由度非零的常数向量，并按每个三角形面积的 1/3 构造 P1 节点积分权重。`remove_pressure_area_mean(values, weights)` 提供以后按面积去均值的入口。没有指定压力某个节点等于零，也没有多加整壁约束。

`attach_checked_pressure_nullspace(matrix, rhs, candidate)` 是未来已经组装完矩阵/右端后才调用的接口：先核 `A·n` 和 `n·b`，达到调用方规定的相对容差才把唯一常数压力零空间附着到矩阵，并清除右端的剩余常数分量。它在本轮**仅用人为构造的 3×3 矩阵测试**；真实 18 项矩阵尚未组装，`matrix_kernel_checked=false`、`rhs_compatibility_checked=false`、`matrix_nullspace_attached=false`。真实系统不能从合成测试推断为通过。

## 静态证据和停点

- `evidence/actual_interface_all18.json`：18 项分别建了真实网格与约束；逐项记录三角形/节点/自由度数量、左右边界段数、所有从点—主点坐标/分量/系数、映射哈希、压力候选和面积权重检查、来源哈希。几何重复的代数/积分对照仍分别核其白名单 ID；6 组独特网格不是 6 个计算结果。
- `test_interface.py`：重点检查最细混合网格、P2 边中点与压力端点、缺失主点拒绝、去均值、合成矩阵的零空间附着/错误拒绝、无求解入口。上一级原 9 项静态测试也再执行并保留独立日志。
- 实测本机 18 项仅建网格/约束的检查为约 1.6 秒、峰值常驻内存约 171 MiB。这是软件准备阶段的观察值，**不是**未来矩阵组装、求解或 2 小时/4 GiB 预算保证。
- 输出 `NUMERICAL_GATE=NOT_EVALUATED`、`RESULT_PASS=false`、`geometry_PASS=null`、预测 HOLD；真实网格来源检查不等于方法精度或真实沟槽结果通过。

下一阶段若另有授权，可把该接口接入同一版本的方程组装，并在**实际组装矩阵**上检查常数压力零空间、右端兼容、真实残差、源项与周期迹，再讨论正式矩形参考计算。当前没有求解入口。原 18 项协议/门槛未改，G4 候选锁和历史网格 FAIL 保留。

后端用法依据本机安装的 `dolfinx/mesh.py`、`dolfinx_mpc/multipointconstraint.py` 和 `petsc4py` 实际接口；公开说明可参见 [DOLFINx 0.11 Python 文档](https://docs.fenicsproject.org/dolfinx/v0.11.0/python/) 与 [DOLFINx-MPC 作者文档](https://jsdokken.com/dolfinx_mpc/main/docs/api.html)。公开主分支文档可能与本机固定版本不同，复现以本机版本、绑定哈希和本目录实际记录为准。

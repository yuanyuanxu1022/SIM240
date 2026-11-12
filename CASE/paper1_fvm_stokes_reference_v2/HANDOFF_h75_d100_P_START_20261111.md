# 交接：本机开跑 FVM 第 2 个点 h75_d100_P

时间：2026-11-11 23:08（+08:00）。**本轮只做预检与命令准备，未启动任何算例。**
用户裁定：**在本机跑**（不搬 103.63）。理由见 `docs/reports/REMOTE_DEPLOY_103_63_20261111/FVM_103_63_FEASIBILITY_20261111.md`。

## 一、为什么选 h75_d100_P 作为第 2 个点

已完成 `h75_d100_T`（FAIL，delta=+2.5110%）。选同几何的 P 方向，可直接回答"超 2% 是单方向偶然还是同几何两方向都有"。若 P 也超，则"OpenLB 5 nm 基线存在系统偏差"这一判断在两个方向上都成立，比多跑一个陌生几何更有价值。

其余 4 点（`h25_d100_T`、`h50_d120_P`、`h125_d120_P`、`h125_d120_T`）保持 `NOT_EXECUTED`，未启动。

## 二、开跑前预检（全部通过）

| 项 | 结果 |
|---|---|
| 当前 release SHA | `97ae55ff9dbaad4c2aa58fbe3b3b5dac548f82400631ac5cd1e12c9ef96c13e5` |
| `status` | `PREPARED_NOT_RUN` |
| `numerical_execution_authorized` | `True` |
| `formal_review_status` | `ASTRA_FINAL_STATIC_RECHECK_COMPLETE` |
| 本地 212 项哈希漂移 | **0** |
| 外部 23 项哈希漂移 | **0** |
| `h75_d0_P_flat` gate | `LOCAL_CHECKS_PASS`，issues=[] |
| `h75_d0_T_flat` gate | `LOCAL_CHECKS_PASS`，issues=[] |
| 残留进程 | 无（`ps` 无 `paper1StokesReference` / `run_one.py`） |
| tmux 会话 | 不存在 |
| `prepared/h75_d100_P_*/runtime` | **均不存在**（不会被"已有证据"拒绝） |

## 三、待跑算例规格

`prepared/h75_d100_P_coarse`：

```
h_nm=75  d_nm=100  w_nm=120  P_nm=240  dx_nm=1.25
direction=P   equation=scalar_Poisson
expected_cells=19200   expected_V_m3=3e-23   Aplan_m2=2.4e-16
seed_from=null（从零起跑，不做 mapFields）
end_time_cap=60000     wall_clock_seconds=1800（上限 30 min）
exit_trigger: p/U/v 均 1e-10
flat_zero_component_exception=false
```

## 四、耗时预期（按 T 方向同层实测外推）

| 层 | T 实测 | P 预期 |
|---|---:|---|
| coarse | 3:25 | 同量级，可能更快（标量泊松未知数少于矢量斯托克斯） |
| mid | 19:04 | 同量级 |
| fine | 3:32:44 | 同量级 |
| tight | 1:07:14 | 同量级 |
| **四点合计** | **≈ 5.0 h** | **≈ 3~5 h** |

## 五、资源占用（回答"会不会卡"）

实测峰值内存（同几何 T 方向）：coarse 66 MB、mid 127 MB、fine 372 MB、tight 378 MB；CPU 恒为**单核 99%**。
代码自带硬闸 `run_one.py:59` `RLIMIT_AS = 4 GiB`，单进程不可能超 4 GB。
⇒ 占全机 1/24 核、≤2.1% 可用内存，**不会卡**；唯一体感是风扇持续转。

## 六、必须遵守的边界

1. **逐层推进，不串行批跑。** `run_one.py` 一次只跑一个 case。coarse 跑完必须独立验收，才能准备 mid；mid 未接受时 fine 拒绝启动（seed 链设计）。
2. **不开跑后一层不需要重新授权，但每层启动前要重新给命令。** 用户本人启动，代理不代跑。
3. **不得重跑 `freeze_release.py`**：会把执行锁退回 `PENDING_ASTRA_V21_RECHECK`、抹掉 `reviewed_release_sha256`、产生第三个 SHA。
4. **不得重跑已完成算例**：`run_one.py:169` 遇 `runtime/` 存在即拒绝（设计意图）。
5. **不得改任何阈值、判据、历史 FAIL、论文数字。**
6. **FAIl 不改写为 PASS。** 参考未取得的点不得说"整体正式 FAIL"。

## 七、本轮未做的事

- 未启动、未停止、未重跑任何算例。
- 未执行 `blockMesh` / `checkMesh` / `mapFields` / 求解器。
- 未改任何源码、清单、协议、阈值。
- 未触碰 103.63 上的 OpenLB 部署（保持可用的干净状态，供 OpenLB 路线用）。

## 八、下一步

用户执行 coach 层命令 → 完成后独立验收（`read_case` 传**绝对路径**，这是 2026-11-11 踩过的坑）→ 通过后准备 mid。

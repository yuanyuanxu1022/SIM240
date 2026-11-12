# 第一篇：OpenFOAM 13 显式沟槽 Stokes 独立参考（v2 准备版）

本目录落实固定 4 几何 6 方向；当前没有求解结果。先读 [PROTOCOL.md](PROTOCOL.md)，具体参数与数量见 [run_config.md](run_config.md)。

v2 是 v1 的修复版，不是新几何：v1 的 `h75_d0_T_flat` 在 6000 步迭代上限内未收敛，给出 −8.943434% 的假偏差；同算例 40000 步为 +0.013878%。v2 因此改迭代预算、层间初场延拓和收敛判据三件事，几何/阈值/离散格式/源码全部不动。

v1 目录 `../paper1_fvm_stokes_reference_v1/` 保持只读，其中两条平板运行记录（P：LOCAL_CHECKS_PASS；T：REFERENCE_CHECK_FAIL）是"协议参数不足"的第一手实证，不得覆盖或删改。

- `solver/paper1StokesReference.C`：P 为标量 Poisson，T 为去惯性稳态 Stokes；K 由解输出。与 v1 逐字节相同，无需重编译。
- `prepare.py`：只生成字典，拒覆盖，不启动 OpenFOAM；写分层上限与 `seed_from`。
- `prepared_manifest.json`、`comparison_inputs.json`：26 份准备输入及六方向历史 K5 锚点；哈希绑定，未执行。`comparison_inputs.json` 从 v1 逐字节继承。
- `postprocess.py`：只读积分/逐级接收/公式比较；v2 的稳态判据在此独立重算，缺 receipt、缺数值判据记录或参考未接收时返回不可裁决。
- `run_one.py`：单例启动控制器；带层间初场延拓（mapFields → `0.5/`）与数值收敛记录，不自动下一个网格/方向。
- `release_manifest.json`：准备快照。`formal_review_status=PENDING_ASTRA_V2_RECHECK`，因此当前拒绝启动。它不是运行结果。
- `tests/`：归一化/方向/坏输入/缺证据/判据边界的合成核对，不是数值基准。

局部 `bin/`、`solver/Make/linux*`、`prepared/*/constant/polyMesh` 和未来时间目录/场文件只留本地，不提交大型结果或可执行文件。本轮不提交推送，亦不改论文母稿。状态入口为项目 `docs/reports/SIM240_AI_CONTEXT.md`。

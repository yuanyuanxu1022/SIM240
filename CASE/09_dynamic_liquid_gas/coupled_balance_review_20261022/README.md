# NS/CH 离散收支与平衡参考审查，2026-10-22

本目录是独立审查材料，不是已编译/已运行的新 CASE。

- `REVIEW.md`：实际源码、离散收支、物理模型缺口与平衡参考。
- `NEXT_VALIDATION_DESIGN.md`：下一组独立验证的设计版本，尚非执行协议。
- `static_operator_audit.py` / `.json` / `.log`：从本机 D3Q19 描述子读取速度和权重，进行有限数组代数核算及旧绑定哈希核对；没有时间推进、OpenLB 执行或平衡求解。
- `verification.json` / `input_hashes.json`：本次审查的证据与输入保护。

结论：已通过的三维源项和平移合同保持有效，但完整 NS/CH、目标物性平衡、静滴、润湿和 K 均未放行。优先准备“真实碰撞/单步收支 + CH 扩散”验证；完整耦合短测和平衡参考为后续依赖，不自动串行启动。

旧批次 `source3d_translation_20261022_v1` 已完成，不重跑。
本轮无新 OpenLB run_id、编译或长算命令。三类正式 Gate 均为 `NOT_EVALUATED`。

# T fine 单例启动准备

## T fine单例命令已核对并交付，尚未启动（2026-11-11 17:21:09 +08:00）

当前coarse/mid已独立验收通过，中粗变化约0.194279%≤1%。用户本轮仅授权核对/准备h75_d100_T_fine：同几何/物性/边界/驱动，dx=.3125nm、307200单元，seed_from=h75_d100_T_mid、目标初场时间.5，endTime200000、求解墙钟43200s（12小时上限非预计耗时），内存地址空间上限4GiB。fine目标runtime/referenceEvidence/.5均不存在，无重跑/覆盖；tmux v21_g3检查时不存在。

源mid完整冻结读回仍LOCAL_CHECKS_PASS，且递归核coarse链通过；source_run_id=h75_d100_T_mid_20261111T165012_e5ad708d、绑定源末态22796.5，receipt/U/p/phi/5份mesh身份完整。P/T平板也复核通过，当前release97ae55ff9dbaad4c2aa58fbe3b3b5dac548f82400631ac5cd1e12c9ef96c13e5授权与审查位有效，212+23指纹0漂移。

准备命令见PAPER1_fvm_v21_review_20261111/h75_d100_T_fine_START_COMMAND.txt，核对报告h75_d100_T_fine_PREPARE_20261111.{md,json}，状态PREPARED_NOT_STARTED。此次未执行网格工具/mapFields/求解/编译；命令交付不等于用户已启动，无fine run_id。完成后按fine原冻结条件验收完整残差、来源/几何/有限性及功率/截面/面体通量各≤0.1%，再核d32≤0.5%且变化递减（或原小变化例外）；原d21约0.194279%保持。fine后还需tight，不能提前认证最终参考或OpenLB/V2准确度。不自动启动下一层或扩算，旧FAIL、三false、论文数字与门槛不改。

启动命令：

```bash
tmux new-session -d -s v21_g3 'source /opt/openfoam13/etc/bashrc && cd /home/dell/yuanyuanxu/SIM240/CASE/paper1_fvm_stokes_reference_v2 && exec python3 run_one.py --case h75_d100_T_fine --execute'
```

# 三维相场源项独立修正与验证准备

2026-10-22：固定36条平移矩阵已完整结束并完成冻结验收，批次/子运行独立exit0。
**最新入口：[analysis_20261022/REPORT.md](analysis_20261022/REPORT.md)**。
修正实现18条全部满足冻结判据；旧移动实现仍约半速，负对照复现成立。
速度最大误差N16为2.5500836%、N32为0.6412140%，约减小3.97696倍；
轴向/正反/对角分量一致，全程相量漂移远低于1e-9。
本轮仅完成规定速度相场算子验证，静滴、润湿、K和真实GHY均未放行。
`analysis_pending_20261022/`仅保留先前运行中快照，不再是当前停点。

先读 `DESIGN_REVIEW.md`（为何修正、如何检出半速），再读 `PROTOCOL.md`（预先固定的参数与判据）。

## 已有证据

- `src/dimension_corrected_ch.h`：独立类型，源项常数从-2改为-(d+2)/2；共享OpenLB不变。
- `src/collision_check.cpp` / `build/collision_check`：真实OpenLB CellD碰撞，通用/CSE路径。
  D2/D3各162组，合计21546项检查，0失败，最大绝对误差8.881784197001252e-16。
  `evidence/collision_v2.log` 与独立 `collision_v2_exit_code.txt=0`。
  对S=.0002，旧D3零阶=-.0001、二阶xx=.0000333333；新D3零阶=-.0002、二阶xx=0。
  这是局部碰撞一致性PASS，不是完整输运或物理PASS。
- `src/translation_check.cpp` / `build/translation_check`：真实SuperLattice周期迁移测试已编译。
  `evidence/build_v3_exit_code.txt=0`；碰撞补充打印后编译v4与检查v2均exit0。
- 两项零步 `source3d_init_{old,new}_n16_xyzp_20261022_v1` 各exit0；
  4096核心节点、初始phase_sum=2048（舍入误差内）、初始L2=1.8692e-15；
  初末相同，新旧初态逐字节相同。见 `initialization_commands.json` / `initialization_checks.json`。
- `test_analysis.py`：6项合成数据检查exit0，验证半速、正负与斜向、振幅损失、
  中途最大漂移、缺行/NaN、零速度；它们不是仿真结果。
- 6项入口检查通过，包括描述、非法实现/网格/方向/选项及拒绝覆盖已有目录。
- 早期构建v1/v2失败日志保留：版本宏/类型命名、本机初始化API问题；后续已修正。
- `evidence/protected_before.json` 与 `protection_check.json`：1772份旧算例/后端/库文件保护核对。
- `evidence/build_binding.json` 将当前代码、二进制、协议、后处理和后端绑定；
  `verification.json` 是本轮最终准备核查入口。

## 已完成批次的运行与证据入口

`run_translation_suite.py` 默认仅核对哈希和防覆盖；只有显式 `--run` 才启动36条轨迹。
矩阵是2实现×2网格×9速度方向（含零速度）；N16/32为500/1000步。
这是已知速度的数学输运测试，化学势人为设0，不是目标物性的自由液滴。
36条已于北京时间08:22:34完整结束，总耗时257.967681秒（约4分18秒）；完整验收见最新分析报告。

固定batch_id：`source3d_translation_20261022_v1`。
`NEXT_COMMAND.txt`是已使用的历史启动命令，勿重复启动；本批次已经完成并分析。
每个子run_id有配置、全程CSV、3D初末场、日志和独立退出码；批次有前后哈希及退出码。
不自动分析、不自动重试、不自动进入下一Gate。输出目录已存在即拒绝覆盖。

结果分析入口 `analyze_translation.py`：读取退出码/manifest/哈希、完整逐步记录、
三维初末场，重算解析场、相量、L2、各轴相位斜率、振幅、粗细网格与方向差异。
旧实现只用于复现缺陷，不能将“负对照符合预期”写成物理输运PASS。

NUMERICAL_GATE / RESULT_PASS / geometry_PASS 均为 NOT_EVALUATED。
局部修正不解决化学平衡密度偏移、机械压力定义、完整耦合、润湿或残余流的所有问题。

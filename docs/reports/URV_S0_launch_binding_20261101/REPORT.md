# S0真实授权绑定与命令交付（2026-11-01）

用户明确答复：“现在授权两条 S0；生成合同和命令，由我手动启动”。原问题、答复和两条获准编号保存于 [user_launch_authorization.json](user_launch_authorization.json)。本轮授权允许准备启动合同和命令，由用户手动启动；代理未执行正式求解、未创建tmux会话。

## 新合同与保留证据

新合同：[S0_launch_release_20261101_01.json](../../../CASE/unseen_v2_reference_S0_v1_2/evidence/S0_launch_release_20261101_01.json)。SHA256为 `eb73d1ec7989cee26aecf1a43c9b8fd818a77fdd5d9ba8fef5e805d9451a5f4a`，获准阶段仅S0_REGRESSION。

- P：URV_S0_P_v1_2_20261101_01，对应URV1_H75_P_dx5_a100000。
- T：URV_S0_T_v1_2_20261101_01，对应URV1_H75_T_dx5_a100000。

approved_runs与原prepared_runs逐项完全一致。原准备绑定SHA `a836c5f4368ed5d80d1a585abde3a353848d4555094ba2556b14fd3d883cb846`及1568项原输入不变；新合同增加原准备绑定、其SHA文件、真实授权记录和创建脚本，共1572项。原准备JSON、README和旧报告中“授权关闭”是准备时快照，保留原字节；当前授权以本新launch合同和最新项目状态为准。旧外部历史PENDING快照也保留，不覆盖真实作者未使用确认。

新合同simulation_authorized=true，仅用于用户手动启动这两条；launch_authorization.agent_solver_execution_authorized=false、next_stage_authorized=false。S0_started=false与actual_formal_run_ids=[]是交付前快照；实际启动/完成状态以后应读运行目录、外层进程和completion记录，不修改本封存冒充运行证据。

## 本轮核对

[verification.json](verification.json)及[launch_readonly_check.log](launch_readonly_check.log)：真实合同的公开binding检查通过；运行器不加--execute的只读入口退出0，未调用native。新合同1572项输入与现文件匹配，程序/源码/构建/编译器/依赖/运行库/检查器/两条配置绑定均保持。

本轮封存前核对可用RAM 23.08GiB，磁盘空闲 318.65GiB，满足RAM≥12GiB、首批磁盘≥100GiB；真正启动仍自动复核，每条前磁盘≥8GiB。tmux版本tmux 3.4，指定会话不存在。命令只进行bash -n语法解析，未执行。

P/T目录各仅run_config.txt和run_manifest.txt，没有正式日志、result、completion或启动标记。既有2518文件前后哈希保持；本轮未改求解器、运行器、检查器、参数、V2或门槛，未重编译、零步审计、运行测试或读取场数据。前轮77项检查器/6项人工运行器测试及4次零步证据保持，未冒充本轮复跑。

h75/d100/w120/P=Ly240nm，dx5nm、a1e5m/s²，P+y/T+x；窗1013、上限58800，单进程/线程/cuboid、overlap3、AS8GiB、单条求解3600s不变。K相对旧同方向差≤1e-4、完整20共同诊断列先保存差异；未解释变化HOLD。P求解并经独立检查通过才继续T；任一失败即停、不自动重试、不进入S1。S0是已知h75统计移植回归，不是新几何模型预测检验。

## 交付命令与停止边界

在SIM240所在的dell计算机普通终端执行 [launch_command.txt](launch_command.txt) 中的一条命令。它绑定本次合同SHA，外层控制台输出追加到CASE下 evidence/S0_launch_console_20261101_01.log；原生完整日志和独立退出按各run目录保存，独立检查结果在analysis_results/。命令已准备供本轮回复交付，不等于用户已执行。

```bash
tmux new-session -d -s urv_s0_v1_2_20261101_01 'cd /home/dell/yuanyuanxu/SIM240/CASE/unseen_v2_reference_S0_v1_2 && exec /home/dell/miniconda3/bin/python3 -B scripts/run_S0.py --release evidence/S0_launch_release_20261101_01.json --release-sha256 eb73d1ec7989cee26aecf1a43c9b8fd818a77fdd5d9ba8fef5e805d9451a5f4a --execute >> evidence/S0_launch_console_20261101_01.log 2>&1'
```

本轮截至封存正式运行0，无新数值或物理验证。formal_NUMERICAL_GATE=NOT_EVALUATED、RESULT_PASS=false、geometry_PASS=null、reference_qualified=false、strict_error_bound_established=false、physical_validation/MODEL_COMPARISON=NOT_EVALUATED、submission_ready=false。旧FAIL、C/h75限定资格、V2/G4锁和旧D4预测HOLD保持，F04多合同汇总仍后续单独处理。未提交推送或外发项目材料。

下一动作是用户手动启动；执行后可贴回终端输出，仅做一次启动状态核查，不持续轮询。完成后按原URV-v1分析已有结果，不自动启动下一阶段。

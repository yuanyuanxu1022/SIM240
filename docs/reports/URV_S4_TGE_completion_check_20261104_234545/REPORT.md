# 服务器1.25 nm结果、构建等价与实测资源收尾

复核时间：2026-11-04T23:48:18.733822+08:00。23:45:45单次服务器快照已确认原控制器/求解器PID均退出，completion、exit_code、result、acceptance及formal_run_record齐全。用户已授权结束后的完整复核；本次继续完成，不启动新计算。

## 结论与范围

**1.25 nm服务器重跑已完成，独立检查与本轮复核均通过本条构建等价范围；实测资源已取得。** 这只建立本次同配置服务器构建与本机构建的K复现证据，不是通用跨硬件逐位等价保证，不接受S4阶段或授予严格参考资格。

run_id：URV_S4_T_dx1p25_TGESRV_v1_20261104_01。服务器10.103.102.55、yuanyuan。几何h30/d80/w120/P=Ly240 nm，横槽T（+x）、dx1.25 nm，nu=1e-6 m²/s，加速度100000 m/s²，tau=1，D3Q19_FORCE/ForcedBGK，x/y周期，Bouzidi固定零速壁。OpenLB提交882924a9cfc8dcdf82909e39530789cb6f5ebcc4；服务器ELF SHA5780e6194f53895ffaa182dcf7ae7de17d793815c54dbfcfac622f0fa3c0bb61。

正式合同SHA758f13deecec0a26ae309e982cbcadfb1aa9bf198e58513292bd2114df49631d，仅批此条。原生独立退出码0，timed_out=false、resource_stop_reason=null；formal_run_record在独立检查成功后生成且BUILD_EQUIVALENCE_PASS=true。未单独记录检查子进程exit_code文件；检查日志与控制器最终记录共同证明正常路径已完成，不伪造独立检查退出码回执。

## 结果与数值诊断

| 项目 | 本轮复核值 | 冻结要求/解释 |
|---|---:|---|
| K | 3.471791836744987e-24 m³ | 本机参照同值 |
| 相对本机偏差 | 0.0 | 绝对值≤1e-6，通过；限记录数值精度 |
| 最终主通量Jx | 3.4717918367449866e-13 m²/s | K=nu J/a |
| 停止步数/诊断行 | 12537 / 12538 | step0至12537连续 |
| 窗口步数/完整窗数 | 2592 / 9947 | 全部重算，首次合格窗为末窗 |
| 最后窗口相对样本标准差 | 8.277215726150058e-7 | ≤1e-6 |
| 最后窗口相对极差 | 4.987652165446628e-6 | ≤5e-6 |
| 全程补偿质量最大相对偏差 | 4.394483008026431e-15 | <1e-10 |
| 质量账本最大差 | 1.7752391338696864e-16 | ≤1e-13 |
| 全程最大密度偏差 | 1.2731204979132826e-9 | ≤1e-6 |
| 全程最大Mach | 6.2651511933297235e-9 | <0.05 |
| 最终截面流量相对差 | 9.40181232094637e-7 | ≤1e-5 |
| Re_H | 1.909874592374824e-6 | ≤0.01 |

独立解析几何得到2064384流体节点、490752条壁面链；原始candidate/valid/installed均同数，q=0.5，两个fallback与unresolved均0。有限性、时间单位、流向及质量账本重算通过。最终窗口另用math.fsum/样本方差直接复算，与冻结检查函数一致。geometry_PASS=true。

## 来源与文件复核

服务器只读验证正式封存及当前1437输入哈希，completion前后输入清单与合同逐项相同；37个原始输出指纹全部核对一致。取回15份必要文件，逐文件SHA一致，包括原始diagnostics、result、边界、配置、日志、completion、acceptance及控制器终记录。本机检查函数check_formal_server.py/server_stage.py/evidence.py内容对回服务器封存一致后，调用只读run_checks/scalars并重算全轨迹/全部完整窗，返回标量与服务器acceptance逐项相同。没有执行检查器main、没有覆盖acceptance，没有求解或原生审计。

场文件保留服务器且37项输出哈希检查覆盖它们；本轮未重新读取三维场数组，不声称新增场物理验证。10帧场输出登记见frame_index.csv（11行含表头）。

## 实测资源

- 求解进程墙钟7575.365345648956秒，约**2小时6分15秒**；/usr/bin/time -v显示2:06:15。
- time-v峰值RSS1599728 KiB=1638121472 bytes=**1.5256195068 GiB**，与completion完全一致；这是本条求解进程的最大驻留内存，不是整机/控制器/独立检查器总内存峰值。
- 平均1.6549696850步/秒，0.6042406753秒/步（总墙钟含初始化和输出）。
- 本机旧12537步/4326秒约2.898步/秒；服务器本条总耗时约为1.75倍。历史“服务器更快、约一小时”估计不成立，后续必须用实测重新预算。
- 1.25 nm峰值不能直接当0.625 nm内存预算，节点增加、读场与检查共存峰值另审；本轮不做0.625放行或时长保证。

## 状态必须分开

原生result写NUMERICAL_GATE=PASS、PASS=true、RESULT_PASS=false。服务器独立构建等价acceptance写NUMERICAL_GATE=NOT_EVALUATED、RESULT_PASS=false、geometry_PASS=true、BUILD_EQUIVALENCE_PASS=true；这些字段照录，不因raw PASS改成完整阶段通过。formal_run_record的geometry_PASS=null是控制器摘要字段，具体几何接受见acceptance及本轮复核，不修改原回执。

原S4六条per-run接受、沿槽P网格PASS保持；横槽T中细1.328387035%>1%仍FAIL、S4_STAGE_ACCEPTED=false、reference_qualified=false、MODEL_COMPARISON/physical_validation未评价、strict_error_bound/submission_ready=false、F04 OPEN及历史FAIL不变。

## 本轮改动与接续

新增本目录快照、取回文件、remote_hash_verification.json、independent_review.json、本报告和source_manifest.json；同步当前状态/主交接/便携交接。未修改CASE或旧合同/参数/源码/结果，未构建、启动/停止/重试求解、读场或进入0.625/零步/PERF/S5；未提交推送。远端只读、无写入；没有新增run_id。

本条1.25 nm结果复核任务完成。下一研究候选是另审0.625 nm前置原生3＋1/初态读回、资源包装、必要PERF与正式预算/网格衔接，各自需既定准备和授权，均未启动。本轮不提供新启动命令。本报告为AI辅助复核，非人工科学终审。整理沿用scientific-writing技能的证据边界原则。

# 余14项：执行入口和运行前核查完成，待用户启动

2026-10-24。用户明确授权准备14项执行入口与运行前核查。**本轮已完成技术准备并形成只允许14项的本机release，正式计算尚未启动。** 本文件是当前状态；原PROTOCOL及release绑定的准备记录原样保留。

## 已验证

- 新增run_remaining.py、独立PROTOCOL/policy、14项精确白名单与14份完整实际key=value配置；默认调用只检查，不启动求解器。入口在正式执行时复用原run_case.prepare；未来配置须与launch_configs逐字节一致。
- 原源码、binary、编译依赖和库与已验收筛选一致；make --question退出0。本轮复用已编译binary，**没有重新编译**，未用编译状态代替物理验证。
- 14项参数由同一binary的describe模式实际读取；14项方向分别执行precheck，共7个不同几何。28个零步检查运行记录保留于evidence/zero_step_checks，全部独立exit0。每个precheck明确collide_and_stream_calls=0、formal_simulation=false，几何/converter/q通过；独立枚举流体节点及D3Q19的18方向连接、q=.5和无fallback/unresolved，与C++安装数相符。
- 允许14项、拒绝主表其余76项；另15个负面检查覆盖篡改参数、未放行、错误批次、已存在批次、内存/磁盘不足、来源绑定变化/缺失。最终又核3项MPI/root环境拦截，实际CLI默认检查退出0、will_run=false。
- release绑定2611个去重输入文件，SHA256=9606906a7ea18c5ec47f1728eeb7d9af48990e17955167f79019c6ec1e3358c9。绑定包括原始来源与首6验收、原方案、阶段源码/协议/白名单/14配置和本轮零步/审查记录。所有原2276项保护保持，G4 v1锁不变。
- 单进程单MPI rank、可用RAM≥2GiB/空闲磁盘≥7GiB，每项启动前复查；当前快照满足。tmux与/usr/bin/time可用；拟定tmux会话尚不存在。资源检查仅快照，不保证正式峰值或耗时。

## 当前未发生

正式批次results/development_remaining14_20261024_v1尚不存在，没有任何新steady启动、流动收敛记录或正式验收。本轮实际新增的是28个零步检查run_id，不能说有28项新流动数据。

```text
preparation_checks: PASS
geometry_precheck: PASS
formal_NUMERICAL_GATE: NOT_EVALUATED
formal_RESULT_PASS: false
formal_geometry_PASS: NOT_EVALUATED
```

release.released=true仅代表用户手动启动这14项的技术前提已准备，不代表老师签字或科学结果通过。原源码/门槛/历史FAIL与G4锁均未改，12开发细格和20预测/预测细格未放行；没有GitHub推送。

## 交付与后续

本机唯一待启动命令见NEXT_COMMAND.txt；用户在本机Linux普通终端手动执行。固定batch_id与tmux会话分别为development_remaining14_20261024_v1、d4-dev14-20261024。命令已准备/交付不等于已启动，不能根据本文件之后仍写“尚未启动”而重复执行。

程序完成14项即停，失败/资源不足/来源变化即停，不自动重试、续跑、分析、拟合或进入网格。各项独立exit/完整数据与来源的验收在完成后另做。保留原result的RESULT_PASS=false，独立结论单列；未来若已存在部分batch，不通过改名重跑掩盖问题。

上一轮预算的相同物理停止时刻缩放场景约0.38h、原最大步数工作量外推约2.51h；这些不是实际墙钟下/上界，实际看收敛及机器负载。本轮未等待正式计算，也不持续轮询。

核验入口：evidence/preparation.json、build_reuse.json、prebinding_review.json、final_review.json、command_dry_run.json。首6独立验收仍见项目docs/reports/D4_prediction_readiness_20261024/REPORT.md；参数/网格预算仍见上级development_completion_plan_20261024/PLAN.md。源证据、配置、协议、OpenLB版本或binary变化后旧release会拒绝，须重新核查，不无检查地再次绑定。

当前进度与AI交接已同步；本轮状态差异、保护及最终完整性见evidence/state_sync.json与evidence/final_integrity.json。其他机器需重新构建/核查/绑定，本机绝对路径许可不能直接复用。

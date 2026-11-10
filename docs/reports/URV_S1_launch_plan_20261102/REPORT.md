# S1 启动合同准备：只读复核通过，待用户明确授权后签发

日期：2026-11-02 11:24。**本轮只做只读复核与不可执行方案准备。没有签发启动合同，没有生成可执行命令，没有启动任何计算。**

用户本轮指令原文：“取得 S1 授权后另存启动合同并交付单条 tmux 命令。”

按项目冻结协议（URV-MRP-v1 §7、URV-v1 §8），该句仍是条件式表述（“取得……后”），不构成对两条 S1 身份的现在授权。`simulation_authorized=false`、`approved_run_ids=[]` 保持不变，见 `launch_release_plan.json` 的 `authorized=false`。旧 S0 合同（SHA `cf7f1aac…`）的许可不能转用于本阶段。

## 1. 本轮只读复核结果（全部通过）

| 复核项 | 结果 |
|---|---|
| 绑定输入项数 | 1473，缺失 0，内容变化 0 |
| 原生二进制实测 SHA | `5c3836e97c99feab88cd8e41773237f6ff642a10558f151b11e112563382b07b`，与准备合同一致 |
| 零步审计 | `URV_S1_ZERO_20261102_01` PASS，推进 0 步，describe/precheck/initialize 各 2 次 |
| 零步审计所绑二进制 | 与准备合同一致（同一 ELF） |
| 两个 run 目录 | 仅含 run_config.txt、run_manifest.txt，run_config SHA 符合，未启动过 |
| launch_attempts 目录 | **不存在**，证明从未启动、无历史尝试 |
| 作者非使用声明 | `AUTHOR_DECLARED_NONUSE_CONFIRMED`，SHA `f5b7c4e6…` |
| MemAvailable | 20.67 GiB（门槛 12 GiB） |
| 磁盘空闲 | 318.10 GiB（门槛 100 GiB） |
| tmux 会话 / 相关进程 | 0 / 0 |

## 2. 本轮发现的实质问题（若不处理，命令会在启动瞬间失败）

准备合同 `preparation_manifest.json` 的 1473 项输入**不包含**以下两项：

1. 零步审计 `audits/URV_S1_ZERO_20261102_01/verification.json`；
2. 准备合同自身 `evidence/preparation_manifest.json`。

而 `run_S1.py` 第 58–63 行要求：

```python
zero = Path(data['zero_audit_path'])
need(data['inputs_sha256'].get(str(zero)) == data['zero_audit_sha256'] == sha(zero),
     'zero audit not bound')
```

即启动合同必须把零步审计文件收进自己的 `inputs_sha256`，否则在 `inspect()` 阶段就被拒绝。若直接把准备合同原样改名为启动合同，会在此处报 `zero audit not bound`。

正确做法沿用 S0 先例（S0 准备 1545 项、启动合同 1548 项，多出的是授权证据、准备合同及其 .sha256 旁文件）：S1 启动合同应为 **1475 项**，即 1473 项原样 + 上述 2 项。

作者声明文件已在 1473 项之内，不需要重复添加。

## 3. 已准备好的不可执行方案

`launch_release_plan.json` 中已落实全部具体字段，待授权即可填值签发：

- 两条保留身份：`URV_S1_P_A1_v1_20261102_01`（沿槽 +y）、`URV_S1_T_A1_v1_20261102_01`（横槽 +x）；
- 拟定启动合同路径 `evidence/S1_launch_release_A1_v1_20261102_01.json`；
- 拟定授权证据路径 `evidence/S1_launch_authorization_A1_v1_20261102_01.json`；
- provenance 六个角色取自真实构建捕获（`build_environment.json` 的 `binary_path`／`native_sources_sha256`／`build_recipe_path`／`dependency_file_path`，加 `ldd.txt`）；
- 资源合同：1 进程／1 线程／1 cuboid／overlap 3／地址空间 8 GiB／RAM≥12 GiB／首批盘≥100 GiB／每条≥8 GiB／每方向墙钟 14400 s；
- 执行顺序 P→原 URV 解析、数值、几何验收全过→才 T；任一失败即停，无重试、不进 S2；
- `startup_command_generated=false`、`command_shape_if_authorized` 仅示意结构，不是可执行命令。

## 4. 授权后要做的六步

1. 写授权证据文件，逐字记录用户原话与范围（仅这两条 S1 身份）；
2. 复制全部输入闭包并补入上述 2 项，另存启动合同；准备合同原字节不动；
3. 计算启动合同独立 SHA256 作为外部信任锚；
4. 用 `run_S1.py` 默认只读模式核对实际退出 0、`solver_executed=false`；
5. 更新 `SIM240_AI_CONTEXT.md` 与 `AI_HANDOFF_20261015.md` 后才交付命令；
6. 只交付一条 SHA 绑定的 tmux 命令，由用户手动执行；AI 不代执行。

## 5. 本轮边界

未编译、未调用原生程序、未运行求解器、未签发启动合同、未生成可执行命令、未修改 CASE 源码或检查器规则、未改任何门槛、未重跑 S0、未提交或推送、未外发项目资料。

S1 状态不变：`NUMERICAL_GATE=NOT_EVALUATED`、`geometry_PASS=null`、`RESULT_PASS=false`（未运行而非失败）。`reference_qualified=false`、`strict_error_bound_established=false`、`submission_ready=false`、`MODEL_COMPARISON/physical_validation=NOT_EVALUATED`、`HISTORICAL_EXCLUSIVE_ATTRIBUTION=NOT_ESTABLISHED` 均保持。

本记录为 AI 辅助准备，不是独立人工科学终审，也不是启动许可。

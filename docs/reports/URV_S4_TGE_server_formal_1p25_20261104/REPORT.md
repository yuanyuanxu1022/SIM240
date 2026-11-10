# 1.25 nm 基准重跑：合同已修正并重签（第一次启动被自身校验拦下）

时间：2026-11-04T21:25+08:00。服务器 `10.103.102.55`（`jj-Rack-Server`），账户 `yuanyuan`。

## 0. 先说发生了什么

你执行了启动命令，会话立刻消失。**这是我自己写的一处校验逻辑打架，不是服务器问题、不是权限问题、也不是资源不够。**

日志只有一行：

```
EvidenceError: explicit approved formal identities required
```

**关键是：它在写任何东西之前就停了。** 我查过：1.25 输出目录仍然只有两个配置文件，`launch_attempts` 和 `analysis_results` 都不存在。所以**这次失败没消耗任何东西**，没有半截数据，不用清理。

## 1. 错误的根因

我原来的设计是"批准的算例必须等于计划里的全部算例"。后来改成"可以只批一部分"（所以只批了 1.25，没批 0.625），但我漏改了这一行：

```python
need(bound.get('approved_run_ids') == [r['run_id'] for r in bound['prepared_runs']], ...)
```

它仍然在跟"全部计划"比，于是认为"批准清单不完整"。

**更值得说的问题**：这个检查只在真正启动时才跑，所以之前所有只读校验都没发现它。这是我的流程设计缺陷——校验放得太靠后。

## 2. 修了什么（四处）

| # | 修改 | 原因 |
|---|---|---|
| 1 | 批准清单改为跟"实际批准的那几个"比，并抽成独立函数 | 修根因；顺便可单独测试 |
| 2 | **把正式权限校验前移到只读入口** | 以后合同有问题，你启动前就能发现 |
| 3 | 每次运行只检查**当前**目录是否干净 | 原来检查全部，将来批两个算例时第二个会误判 |
| 4 | 检查器超时改为从合同读取，不再写死 3600 | 避免与合同里的数字不一致 |

## 3. 新增两项测试（共 21 项）

- **少批一个算例必须通过**：批准 1.25 而不批 0.625，是合法的
- **批准清单必须与计划精确对应**：空清单、清单里有计划外的 id、id 与记录不匹配、重复记录、有记录但 id 为空 —— 五种错法逐一拒绝

21 项在服务器本地全部通过。

## 4. 额外做了一件我认为必要的事

不想让你再白等一小时去试错，所以**先用你电脑上那份已通过的 1.25 nm 结果把检查器跑了一遍**：

| 项目 | 结果 |
|---|---|
| 基础校验（身份/几何/进程） | 通过 |
| 重算的 K | `3.471791836744987e-24` |
| 已接受记录的 K | `3.471791836744987e-24` |
| **相对差** | **0.0** |
| 几何 | 2 064 384 流体节点、490 752 壁面链、q 全为 0.5 |
| 等价判据（≤1e-6） | **PASS** |

**这证明检查器的数学逻辑是对的**——拿正确结果去喂，它给出正确结论。这样服务器上跑出来的数字才可信。

顺便得到本机真实速度：**2.898 步/秒**，12 537 步用 4 326 秒。

## 5. 新合同

| 项目 | 值 |
|---|---|
| 正式合同 SHA | **`758f13deecec0a26ae309e982cbcadfb1aa9bf198e58513292bd2114df49631d`** |
| 准备封存 SHA | `2dff3e35e6bd38e729b4af…` |
| 批准算例 | 仅 `URV_S4_T_dx1p25_TGESRV_v1_20261104_01` |
| 软件检查 | 21 项全过 |
| 只读全量校验 | 通过（含完整正式权限校验） |
| 资源前置 | MET（可用内存 128.21 GiB） |
| 输出目录 | 仍为空 |
| 会话名 | 改用 `…_02`（避免旧名残留干扰） |

## 6. 请再执行一次

你已经登录在服务器上了，直接执行：

**第一步，看资源：**
```
awk '/MemAvailable/{printf "可用内存 %.2f GiB (门槛 80.00 GiB)\n",$2/1048576}' /proc/meminfo
```

**第二步，启动（只执行一次）：**
```
tmux new-session -d -s urv_s4_tge_1p25_20261104_02 'cd /home/yuanyuan/SIM240/CASE/unseen_v2_reference_S4_tge_server_v1 && exec /usr/bin/env -u LD_LIBRARY_PATH -u LD_PRELOAD /usr/bin/python3 -B scripts/run_formal_server.py --release /home/yuanyuan/SIM240/CASE/unseen_v2_reference_S4_tge_server_v1/evidence/S4_TGE_SERVER_formal_launch_release_v1_20261104_01.json --release-sha256 758f13deecec0a26ae309e982cbcadfb1aa9bf198e58513292bd2114df49631d --execute > /home/yuanyuan/SIM240/CASE/unseen_v2_reference_S4_tge_server_v1/S4_TGE_SERVER_formal_1p25_controller_v1_20261104_01.log 2>&1'
```

**第三步，确认它真的在跑**（等十秒后执行）：
```
tmux ls; ps -eo pid,etime,pcpu,rss,comm | grep urv_reference
```

第一条应列出 `urv_s4_tge_1p25_20261104_02`；第二条应看到 `urv_reference` 且 CPU 接近 100%。

如果 `tmux ls` 又找不到会话，先看日志再告诉我：
```
cat /home/yuanyuan/SIM240/CASE/unseen_v2_reference_S4_tge_server_v1/S4_TGE_SERVER_formal_1p25_controller_v1_20261104_01.log
```

## 7. 本次失误与改进

**失误**：改了设计没改全相关校验；校验放得太靠后，导致只读检查看不出来。

**改进已落地**：正式权限校验现在在只读入口就跑，合同有问题会在启动前暴露。另外用已知正确结果验证了检查器，而不是直接拿服务器去试。

## 8. 证据

本目录：`START_COMMAND.txt`、`CHECK_BEFORE_START.txt`、`server_evidence/`（9 件，含新合同与新封存）、`server_logs/`（6 个，含 21 项测试日志）、`document_manifest.json`。

服务器端：`~/SIM240/CASE/unseen_v2_reference_S4_tge_server_v1/`

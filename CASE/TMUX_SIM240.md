# TMUX_SIM240.md

> SIM240 长时间数值计算的 tmux 使用速查表  
> 适用场景：OpenLB 长时间计算、网格收敛矩阵、参数扫描、SSH 可能断线的任务。

---

## 1. 什么时候用 tmux？

### 建议使用

以下任务建议放到 tmux 后台运行：

- G2 / G3 多工况矩阵；
- `dx = 1.25 nm` 等细网格计算；
- OpenLB steady 长时间计算；
- 网格收敛 / GCI 批量工况；
- 参数扫描；
- 晚上持续计算；
- SSH / VS Code 远程连接可能中断的任务。

### 一般不需要

以下任务通常不需要 tmux：

- 只编译；
- precheck；
- 几十秒内的小测试；
- 查看日志；
- CSV 后处理；
- 画图；
- 结果分析。

---

# 2. SIM240 推荐工作流

```text
Codex
  ↓
修改代码
  ↓
编译
  ↓
precheck / 参数审计
  ↓
给出 tmux 命令
  ↓
手动复制运行
  ↓
tmux 后台计算
  ↓
偶尔查看状态
  ↓
计算结束
  ↓
再让 Codex 分析结果
```

原则：

> Codex 负责“准备计算”，tmux 负责“后台跑计算”，计算结束后再让 Codex 分析结果。

不要让 Codex 持续轮询长时间模拟。

---

# 3. 后台启动任务

标准格式：

```bash
tmux new-session -d -s <session-name> 'cd <case-directory> && exec <run-command>'
```

例如 G2 Step 3：

```bash
tmux new-session -d -s sim240-g2-step3 'cd /home/dell/yuanyuanxu/SIM240/CASE/G2_EX240_grid_convergence && exec ./scripts/run_grid_matrix.sh'
```

参数含义：

- `-d`：后台启动；
- `-s sim240-g2-step3`：tmux 会话名称；
- `cd ...`：进入 Case 目录；
- `exec ...`：执行正式计算。

---

# 4. 查看当前有哪些 tmux 任务

```bash
tmux ls
```

例如：

```text
sim240-g2-step3: 1 windows
```

说明该任务还在 tmux 会话中。

如果对应会话消失，通常表示脚本已经结束或异常退出。

---

# 5. 查看当前跑到哪里

推荐优先使用：

```bash
tmux capture-pane -pt sim240-g2-step3 | tail -n 40
```

如果只想看已经完成的 steady Case：

```bash
tmux capture-pane -pt sim240-g2-step3 | grep 'steady run='
```

例如：

```text
steady run=dx5_Smooth75 exit=0
steady run=dx5_EX240_parallel exit=0
```

表示：

- `dx=5 nm Smooth75` 已完成；
- `dx=5 nm parallel` 已完成；
- `exit=0` 表示正常退出。

---

# 6. 查看当前程序和运行时间

```bash
ps -eo pid,etime,cmd | grep -E 'run_grid_matrix|g2_ex240' | grep -v grep
```

其中：

- `PID`：进程号；
- `ETIME`：已运行时间；
- `CMD`：当前正在执行哪个程序。

例如：

```text
38750   00:10   ... g2_ex240_dx5 steady T ...
```

表示：

- 当前程序已运行 10 秒；
- `dx5`：5 nm 网格；
- `T`：transverse / perpendicular。

---

# 7. 进入 tmux 看实时输出

```bash
tmux attach -t sim240-g2-step3
```

进入后不要直接关闭终端。

查看完以后退出 tmux、但保持任务继续运行：

```text
Ctrl+B
然后按 D
```

这叫 detach。

---

# 8. 常用 Case 命名规则

建议统一使用：

```text
sim240-g1-validation
sim240-g2-step1
sim240-g2-step2
sim240-g2-step3
sim240-g3-gap
sim240-g3-depth
sim240-g3-duty
```

原则：

```text
sim240-阶段-任务
```

不要使用：

```text
test1
tmp
run
new
```

这类以后很难判断用途的名称。

---

# 9. 判断是否还在运行

## 方法 1：看 tmux

```bash
tmux ls
```

还能看到会话：

```text
sim240-g2-step3
```

说明 tmux 会话仍存在。

## 方法 2：看实际计算进程

```bash
ps -eo pid,etime,cmd | grep -E 'run_grid_matrix|g2_ex240' | grep -v grep
```

如果还能看到 OpenLB 可执行文件，说明正式计算仍在运行。

---

# 10. 判断已经完成

如果：

```bash
tmux ls
```

中对应会话消失，可以进一步检查结果目录。

例如：

```bash
ls -lt /home/dell/yuanyuanxu/SIM240/CASE/G2_EX240_grid_convergence/results | head
```

然后检查：

- 最终报告；
- summary CSV；
- exit code；
- run log。

不要仅凭 tmux 会话消失就判定 PASS。

最终 PASS / FAIL 必须按照冻结协议检查。

---

# 11. 手动停止任务

先确认会话名称：

```bash
tmux ls
```

然后：

```bash
tmux kill-session -t sim240-g2-step3
```

注意：

> 这会直接终止 tmux 会话和其中的计算任务。

除非确定需要停止，否则不要使用。

---

# 12. SIM240 当前 G2 Step 3 示例

当前正式计算：

```bash
tmux new-session -d -s sim240-g2-step3 'cd /home/dell/yuanyuanxu/SIM240/CASE/G2_EX240_grid_convergence && exec ./scripts/run_grid_matrix.sh'
```

快速查看进度：

```bash
tmux capture-pane -pt sim240-g2-step3 | grep 'steady run='
```

查看当前正在跑什么：

```bash
ps -eo pid,etime,cmd | grep -E 'run_grid_matrix|g2_ex240' | grep -v grep
```

查看最近输出：

```bash
tmux capture-pane -pt sim240-g2-step3 | tail -n 40
```

---

# 13. 长计算 Codex 固定要求

以后给 Codex 的长计算任务，结尾统一加：

```text
按 AGENTS.md 执行。

完成代码修改、编译、参数审计和运行前检查后，
如果正式计算需要较长时间，
只给我最终可复制的 tmux 后台运行命令。

不要等待模拟完成。
不要持续轮询。
不要自动进入下一 Step / Gate。
```

---

# 14. 计算结束后的 Codex 指令

计算结束以后：

```text
按 AGENTS.md 执行。

读取刚完成的正式计算结果。

只分析已有结果，不重新运行计算。

完成：

1. PASS / FAIL；
2. 核心物理结果；
3. 数值稳定性；
4. 网格 / GCI / 不确定度；
5. 更新 CASE_STATUS；
6. 给出下一步建议。

不要自动运行下一 Step。
```

---

# 15. 最常用命令速查

| 目的 | 命令 |
|---|---|
| 后台启动 | `tmux new-session -d -s NAME 'COMMAND'` |
| 查看全部会话 | `tmux ls` |
| 进入会话 | `tmux attach -t NAME` |
| 退出但不停 | `Ctrl+B`，再按 `D` |
| 看最近输出 | `tmux capture-pane -pt NAME \| tail -n 40` |
| 看完成 Case | `tmux capture-pane -pt NAME \| grep 'steady run='` |
| 看进程/时间 | `ps -eo pid,etime,cmd \| grep ...` |
| 强制结束 | `tmux kill-session -t NAME` |

---

# 16. 一句话记忆

> **短测试直接跑，长计算用 tmux；Codex 负责准备，tmux 负责后台计算，结束后再让 Codex 分析。**

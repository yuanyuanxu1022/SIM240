# AGENTS.md — SIM240 项目工作协议

> 用途：告诉任何进入本项目的 Codex / AI 代理（Codex、Claude Code 等）**应该怎么工作**。
> 进入项目后，**第一步先读本文件**，再读项目状态文件，然后才能动手改代码 / 跑命令 / 做判断。
> 本文不是历史日志，不是论文正文；只讲"规则"和"当前状态入口"。

---

## 0. 进入项目后必须先做的事

在任何修改、运行或判断之前，按顺序读：

1. `AGENTS.md`（本文件）
2. `SIM240_AI_CONTEXT.md` — 项目当前状态
3. `SIM240_CASE_ROADMAP.md` — Case 路线与科学问题映射
4. `PROGRESS_SUMMARY.md` — 历史进度汇总（只读参考）

若任务涉及具体 CASE，再读该 CASE 内相关的：

- `PROTOCOL.md`
- `run_config.md`
- `README.md`
- validation report
- 当前源码

**不得脱离当前项目状态，仅凭旧聊天或旧方案继续执行。**

---

## 1. 当前研究主线（务必遵守，不要跑偏）

固定几何、单相液体、真实 EX240 纳米沟槽中的**方向性输运与水力阻力**研究。

重点：

- 沿槽方向输运；
- 横槽方向输运；
- 有效迁移率 / 水力阻力；
- 各向异性；
- 数值收敛与网格独立性；
- 物理耗散机制。

**除非用户明确要求，否则不要自动切回**：动态压头、移动边界、两相填充、液滴铺展任务。

当前 Gate 路线（详见 `SIM240_AI_CONTEXT.md`）：

| Gate | 任务 | 状态（截至 2026-09-16） |
|---|---|---|
| G0 | 数值实现与边界审计 | 完成 |
| G1 | Smooth 平板迁移率验证（$K=h^3/12$） | 进行中，精度门槛未通过 |
| G2 | EX240 直沟槽 RVE（$K_\parallel,K_\perp$） | 进行中：G2-T 横槽正式计算已 PASS；G2-P 状态以最新 result.txt 为准 |
| G3 | 0°/45°/90° 张量方向验证 | 未开始 |
| G4 | 结构/间隙参数化 | 未开始 |
| G5 | 介尺度挤压模型 | 未开始 |
| G6 | 直接移动边界交叉验证 | 可选，不阻塞主线 |
| G7 | 复杂物理扩展 | 未开始 |

---

## 2. SIM240 MCP 使用规则

读取项目状态、CASE 结果或验证状态时，**优先使用 `sim240` MCP**，不要反复读完整项目上下文。

优先使用针对性工具：

- `read_sim240_context`
- `read_latest_log`
- `check_validation_gate`
- `compare_cases`
- `compare_cases_table`
- `rank_cases`
- `git_status`
- `git_diff`

原则：**只读取完成当前任务所需的信息**，减少上下文与额度消耗。

---

## 3. 长时间 OpenLB 计算的分工

**Codex 负责"改和查"，OpenLB 负责"算"。**

若预计运行超过几分钟：

1. Codex 负责检查代码；
2. Codex 负责编译；
3. Codex 给出**正确运行命令**；
4. 使用 Linux / `tmux` 独立运行；
5. Codex **不要持续轮询**计算状态；
6. 模拟完成后再读取结果并分析。

---

## 4. CASE 成功判定（关键，禁止过度声称）

不得因为"程序正常退出"或"达到稳态"就报告 CASE 成功。

必须区分三类独立证据：

- `NUMERICAL_GATE`
- `RESULT_PASS`
- `geometry_PASS`

例：

```text
NUMERICAL_GATE: PASS
RESULT_PASS: false
geometry_PASS: false
```

只能表述为：**数值门槛通过，但整个 CASE 尚未完全通过。** 不得写成"CASE 验证成功"。

---

## 5. 基础数值验证要求

Poiseuille / mobility 基准验证至少检查：

- 收敛；
- Mach < 0.05；
- 质量守恒；
- `Jy_relative_error < 2%`；
- `velocity_profile_L2_relative_error < 2%`；
- 几何边界正确；
- 无 unresolved boundary links；
- 无非法 fallback；
- 输出为有限值。

---

## 6. Git 使用规则

- 主仓库：`yuanyuanxu1022/SIM240`
- 参考仓库：`junjieli2/nanrPrint`（**不得误 push 到此仓库**）
- push 目标：`sim240/main`

提交前必须：

1. `git status`
2. 查看 `git diff`
3. 只 `git add` 本次需要的文件
4. 再 commit
5. push

**禁止无检查地执行 `git add .`。**

---

## 7. 不提交的内容（默认只留本地）

- 大型计算结果；
- `CASE/**/results/`
- `CASE/**/build/`
- `output/`
- `tmp/`
- Python cache；
- `.o`、`.d`；
- ELF 可执行文件；
- 大型诊断 CSV；
- MCP 临时备份文件（如 `mcp_server.py.bak`、`.before_*` 等）。

---

## 8. 修改代码原则

- 优先做**最小修改**；
- 不无理由重构整个工程；
- 不修改与当前任务无关的文件；
- 修改前先说明目的；
- 修改后说明具体改变；
- 能编译时先编译验证；
- **不把"编译成功"当成"物理验证成功"。**

---

## 9. Linux / 服务器带教规则

给用户终端操作时：

- 一次只给少量命令；
- 明确说明在哪台机器执行；
- 明确说明在哪个终端执行；
- 等用户贴回输出后再决定下一步；
- 未确认前不要跳步骤；
- SSH、代理、Codex、conda、tmux 尤其如此。

---

## 10. 输出风格

默认：专业、学术、简洁、证据驱动。

必须区分三类表述：

- **已验证**（有证据链）
- **推测**（尚未证实）
- **下一步**

涉及导师汇报时，优先整理成：

1. 当前背景；
2. 已完成；
3. 当前问题；
4. 判断依据；
5. 下一步。

---

## 11. 核心工作原则（最重要）

每次任务遵循：

```
先读项目状态 → 再判断 → 再修改 → 再验证 → 最后总结
```

**不要：先改代码 → 再猜项目现在在做什么。**

---

## 12. 状态文件更新规则

每完成一个 Gate 或研究路线变化时，更新 `SIM240_AI_CONTEXT.md`：

1. 更新"当前真实进度"；
2. 更新"当前已知问题"；
3. 更新"下一任务"；
4. 删除已失效的临时信息；
5. 不无限追加历史日志。

这些状态文件始终描述"现在是什么状态"，而不是"过去发生过什么"。

---

## 13. Long-running simulation execution policy

For SIM240 numerical simulations, follow this workflow:

1. Read the current state and relevant Case protocol before modifying code.
2. Only modify files necessary for the current task.
3. Complete:
   - code modification;
   - compilation;
   - static checks;
   - run configuration / parameter audit;
   - required pre-run validation.
4. Do NOT wait for a long simulation to finish inside the Codex task.
5. Do NOT continuously poll simulation status.
6. Do NOT repeatedly inspect logs while the simulation is running.
7. Do NOT automatically start the next Gate / Step.

If the formal calculation is expected to take significant time:

- prepare the executable and run directory;
- verify the exact command;
- return only one directly copyable `tmux` background command to the user.

Preferred form:

```bash
tmux new-session -d -s <session-name> 'cd <case-directory> && exec <run-command>'
```

After providing the tmux command, stop the task.

The simulation and AI analysis are separate stages:

```text
Code / protocol preparation
→ compile
→ static validation
→ provide tmux command
→ user starts background calculation
→ calculation finishes
→ user starts a new Codex task for result analysis
```

For result-analysis tasks:

- analyze existing completed results only;
- do not rerun simulations unless explicitly requested;
- report PASS/FAIL according to the frozen protocol;
- do not change thresholds after seeing results;
- do not automatically enter the next Step.

For formal SIM240 runs, always preserve:

- `run_id`;
- source hash / manifest;
- OpenLB version;
- full parameters;
- raw CSV / field files;
- complete log;
- independent exit code;
- convergence evidence;
- mass, density and Mach diagnostics.

Never use `git add .` automatically.
Do not commit temporary files, `.bak`, `tmp/`, or simulation output unless explicitly required.

# AGENTS.md — SIM240 项目工作协议

> **重要前提：本项目用户是非技术人员（2026-10-16 明确）。**
> 用户不懂编程、命令行、编译、网格、OpenLB/tmux 等技术细节。任何 AI 代理与其沟通时**必须**：
> - 用通俗白话解释，少用术语；必须用术语时要先解释意思；
> - 给终端命令时一次只给少量，并说清「在哪台机器、哪个终端执行、执行后贴回什么」；
> - 涉及技术/参数/命名等决策时，用大白话讲清利弊再让用户选，不要默认用户懂；
> - 不要假设用户能自己看懂编译报错、日志或源码。
>
> 本条优先级最高，与下述所有规则冲突时以此为准。

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
5. `docs/reports/AI_HANDOFF*.md` 中日期最新的交接摘要 — 当前停点、证据与接续动作

上述三份项目状态文件实际位于 `docs/reports/`；以当前状态和最新交接为准，不用历史汇总覆盖新证据。

若任务涉及具体 CASE，再读该 CASE 内相关的：

- `PROTOCOL.md`
- `run_config.md`
- `README.md`
- validation report
- 当前源码

**不得脱离当前项目状态，仅凭旧聊天或旧方案继续执行。**

### 0.1 执行前与下一步的模型建议（用户固定偏好）

- 每个新任务开始执行前，在首条进度说明中主动写：`本次执行建议：<模型>｜<推理强度>；任务：<简短说明>`，不要等用户提醒。纯问答在回答中简短注明即可。
- 任务进入风险或复杂度明显变化的阶段（例如从查进程转为修改求解器、从读日志转为物理放行审查）时，在该阶段执行前更新建议；同阶段的每个工具调用不必重复。
- 每次最终回复末尾注明：`下一步模型：<模型>｜<推理强度>；任务：<下一步>`。若任务已结束且没有下一步，注明无需切换，不人为增加任务。
- 下列是本项目工作建议，不是官方能力保证；具体模型及推理选项以用户界面实际可用项为准：
  - 终端命令带教、查进程、简单文件修改：GPT-6.1 Sol｜Low。
  - 常规 Python 出图、数据整理、明确范围的脚本实现：GPT-6.1 Sol｜Medium；涉及科研数值口径时升为 High。
  - OpenLB/MPI 代码修改、并行输出问题、完整结果审查、Gate 放行：GPT-6.1 Sol｜High。
  - **特别难的问题一定用 GPT-6 Astra｜High，不因省额度降档**（2026-10-23 用户定）：① 复杂物理推导中的疑难部分（如封闭极限、变分论证这类硬骨头）；② 疑难根因分析（多线索交织、顺藤摸瓜型）；③ 多证据矛盾、需判断谁对谁错的裁决；④ 公式/结论最终冻结前的终审把关。这四处不省。
  - 省额度原则只作用于"不算特别难"的任务：常规推导/根因分析（Sol 结果可由原始数据独立核验）用 GPT-6.1 Sol｜High，核验不符或反复复核仍矛盾时升 Astra；日常带教/查进程用 Low、出图/数据整理用 Medium，均不得随意升 Astra。
- 模型建议与真实模型切换是两回事：不得声称已经切换；未经明确授权不修改 Codex 模型配置、登录信息或运行中的仿真。
- 如建议模型不可用，说明替代选择；不得仅因建议未落实就中断安全、已授权的工作。模型强弱不能代替冻结协议和实际验证证据。

---

### 0.2 自动选用Skill（用户2026-10-17明确要求）

按实际任务主动读取并使用相关已安装Skill，无需用户重复输入技能名，简短说明所用技能：

- 论文/科研报告起草、章节与证据组织：scientific-writing。
- 稿件投稿前自审、科学论证和方法/证据检查、审稿回复规划：peer-review。
- 已有学术文本润色：academic-humanizer，保留数字、单位、公式、引用和必要限定。
- 文献任务按需选paper-lookup、literature-review、citation-management、scientific-critical-thinking；CSV曲线按可用环境选matplotlib/scientific-visualization；OpenLB场图优先paraview-publication；Word/PDF/PPT按相应现有技能处理。

只调用相关项；Skill的通用规则不替代本项目冻结协议、原始证据、PASS/FAIL及长算授权边界。自有材料已有明确任务授权时沿用；不自动开始长仿真或下一Gate，不把CFD数值误差机械改成临床/统计检验问题。没有环境或未发现技能时如实记录，不声称已运行或验证。

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

### 12.1 每次任务结束与跨 AI 交接（用户 2026-10-15 明确要求）

- 每次完成项目任务、到达阶段停点或需要中断交接时，结束前同步 `docs/reports/SIM240_AI_CONTEXT.md` 与日期最新的 `docs/reports/AI_HANDOFF*.md`，无需用户再次提醒；这是用户已授权的常规进度维护。
- 当前状态只保留现在的进度、问题与下一步；详细证据放在独立报告中，避免无限追加重复历史。纯解释/复述若没有新增结果，应明确“本轮无新增计算或验证”，不得制造进展。
- 交接至少写清：用户已裁定的范围、此次做了什么及改动路径、已验证/未验证/失败、协议与 run_id/证据路径、当前卡点、下一条具体动作、需要用户启动的长计算和权限边界。
- 源码存在、可执行文件存在、编译验证、几何/q 审计、短测、正式计算与独立验收分别记录；没有证据的步骤写“未核实/待做”，不能按目录或文件存在推断完成。
- 文件与交接不一致时，按本轮实际证据修正过时条目，并注明核对时间。其他 AI 正在工作的文件只记录快照，不覆盖其源码或原始结果。
- 给出长计算 tmux 命令前先写好交接；明确“命令已准备/已交付”不等于“用户已启动/运行已完成”。不为更新进度而启动、重跑或持续轮询仿真，不改历史 FAIL 和冻结门槛。
- 最终回复简短指出已更新的进度/交接入口，使接手 AI 可从文件继续，不依赖旧聊天或某个工具的私有记忆。

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

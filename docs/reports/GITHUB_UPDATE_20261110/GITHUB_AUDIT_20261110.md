# GitHub 现状审计与补齐清单（2026-11-10）

> 一句话：GitHub 上只有 **1168 个文件**，而且其中 `docs/reports` **只有 5 个**——
> 本地 1150 份正式文档、近 4000 份算例档案从来没上去过。
> 本次已把能上传的**全部暂存在本地**（8354 个 / 201 MB），只等你确认后提交。

---

## 一、GitHub 上现在到底有什么

远程分支 `sim240/main`，最新提交 `9bad48a`（2026-10-12），共 **1168 个文件**：

| 位置 | 文件数 | 说明 |
|---|---|---|
| `grooveDNS/` | 543 | 沟槽 DNS 求解器各阶段（stage1/2/3/5）、参数、少量输出 |
| `CASE/` | 494 | 早期算例（00_validation、01_baseline、03_grid_convergence、06/07_filling） |
| `analysis/` | 46 | 分析脚本 |
| `figures/` `paper_figures/` | 34 | 图件与绘图脚本 |
| `docs/` | 17 | **只有 5 个文档在 docs/reports**，其余是 ex240 几何说明 |
| `paper_database/` `transport_database/` | 17 | 文献与输运数据 |
| `tools/` `notebooks/` | 13 | MCP 工具、notebook |
| 根目录 | 3 | `AGENTS.md`、`.gitignore`、`Allrun` |

**最关键的缺口**：`docs/reports/` 里只有
`PROGRESS_SUMMARY.md`、`SIM240_AI_CONTEXT.md`、`SIM240_CASE_ROADMAP.md`、
`SIM240_CASE_STATUS.md`、`SIM240_VALIDATION_REPORT.md` 这 5 个。
也就是说——**从 9 月到现在所有评审、审计、改稿记录、论文母本与投稿件，全部不在 GitHub 上。**

## 二、缺什么（本次补齐的内容）

本地有、GitHub 上没有、且**应该**上传的：**10633 个文件 / 214 MB**。
其中已实际暂存 **8354 个 / 201 MB**，剩下 2285 个被项目自己的 `.gitignore` 拦下（见第三节）。

| 主题 | 文件数 | 内容 |
|---|---|---|
| 论文与报告 | 4531 | 五件母本、投稿派生件、MANIFEST、结论定稿、430 余个评审/审计目录、改前快照 |
| 算例档案 | 3759 | 每个 CASE 的 `PROTOCOL.md`、`src/`、`scripts/`、`run_config`、结果摘要 json/csv |
| 图件与控制文件 | 49 | ParaView 状态文件 `.pvsm`（可复现出图） |
| 源码与分析工具 | 10 | `grooveDNS` 改动、`analysis/`、`tools/` |
| 其他 | 6 | 根目录说明文档、notebook |

按类型：文档 `.md` 1521 个（84 MB）、源码 957 个（8 MB）、配置与证据 5877 个（110 MB）。

## 三、故意不上的（以及为什么）

### 3.1 被项目自己的 `.gitignore` 拦下：2285 个

这些**不是我不想传，是仓库规则禁止**，主要集中在运行证据目录：

| 位置 | 数量 | 被谁拦 |
|---|---|---|
| `CASE/D_series/D4_.../` 后端与环境记录 | 1180 | `.conda_pkgs`、`.backend` 规则 |
| `CASE/unseen_v2_reference_v1/audits/` | 623 | 该 CASE 自己的 `.gitignore` 写了 `/audits/` |
| `CASE/03_grid_convergence/G4_.../build_fields_*` | 269 | 构建产物 |
| 其余各 CASE 的 `runs/`、`audits/` | 213 | 各 CASE 的 `.gitignore` |

**要不要强制上传（`git add -f`）需要你定**：
- 强传的好处：运行审计（`audits/`）是"这个算例真的跑过"的证据链。
- 强传的坏处：一旦入库，以后每次改动都会产生大量 diff；且这些目录当初被排除是有意为之。
- 我的建议：**`audits/` 值得强传（约 700 个、多为小 json），`.backend`/`.conda_pkgs` 绝对不要**。

### 3.2 类型上就不该进 Git：4256 个

| 类型 | 为什么不传 |
|---|---|
| `.npy` `.vti` `.vtm` 场数据 | 单个几十 MB 到几 GB，Git 存二进制会永久膨胀仓库，且无法 diff |
| `.png` `.pdf` `.pptx` 图件与幻灯片 | 二进制、可重新生成；GitHub 不是文件网盘 |
| `.o` `.so` 编译产物 | 换台机器就要重编 |
| `.log` 运行日志 | 已由各 CASE 的 `results/`、`reports/` 摘要替代 |

### 3.3 体积超标：236 个

单文件 > 500 KB 的 csv/json/txt（最大 64 MB 的 `dual_boundary_history.csv`）。
这些是仿真原始输出，属于"数据"而非"代码与文档"，不适合 Git。

### 3.4 目录级排除：16298 个

`build/`、`tmp/`、`output/`、`outputs/`、`results/`、`.conda_pkgs/`、`.backend/`、
`site-packages/`、`.workbuddy/`、`.vscode/`、`.Trash-0/`。

其中 **`.backend/` 里躺着 15879 个 GCC 标准库头文件**（一套完整编译工具链的副本），
`.conda_pkgs/` 里是一整包 conda 缓存——这是本地"源码"数量高达 2.3 万的真相，
与项目代码无关，一个都不能进仓库。

## 四、一个需要你决定的遗留问题

`CASE/reports/` 下有 **35 个文件在你工作区已被删除**，但它们**已经在上 GitHub 上了**
（2026-10-12 那次提交带的）。

- 我**没有**暂存这些删除 → 它们在 GitHub 上会**继续保留**，不会丢。
- 风险提示：这 35 份（`G2_FINAL_STATUS.md`、`Gate0_report.md`、`G5A_SQUEEZE_RESISTANCE_RESULTS_*.md` 等）
  在 `docs/reports/` 里**找不到同名替代**。如果哪天提交了删除，GitHub 上就永久少一份。
- 建议：**先别删**。等确认它们确实已迁移或确属废弃，再单独处理。

## 五、提交后会变成什么样

| | 现在 | 提交后 |
|---|---|---|
| 文件数 | 1168 | 约 9523 |
| 内容 | 只有代码和 5 个文档 | 代码 + 全部论文文档 + 全部算例档案 |
| 历史可追溯性 | 只有 10-12 之前的 | 从 9 月至今每一轮改稿都能查 |

体积提示：本次约 202 MB 原始文件，Git 压缩后大致 60–90 MB。推送时间取决于网速，
几百 KB/s 的校园网可能要十几分钟，属正常。

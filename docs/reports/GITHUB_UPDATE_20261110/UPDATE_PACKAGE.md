# 操作手册：把补齐内容推到 GitHub

> 读这一页就够了。审计结论与"为什么这些不上"见同目录 `GITHUB_AUDIT_20261110.md`。
> **本机已完成筛选与暂存，没有提交、没有推送。**

---

## 一、现在的状态

| 项 | 值 |
|---|---|
| 已暂存 | **8354 个文件**（8349 新增 / 5 修改），约 **201 MB** |
| 范围 | 9 月至今全部论文文档 + 算例档案 + 源码，排除场数据/图件/编译产物 |
| 提交说明 | 已写好并润色：`COMMIT_MESSAGE_CLEAN.txt`（46 行 / 3171 字节） |
| 目标远程 | `sim240` → `git@github.com:yuanyuanxu1022/SIM240.git` |
| 目标分支 | `main`（上游 `sim240/main`，本地无领先提交，可直接推） |
| 禁推远程 | `origin` → `junjieli2/nanrPrint`，已设 `DISABLED_READONLY` |

## 二、指令（二选一）

### 指令 A：自己在本机终端执行（推荐，最省事）

打开终端，把下面这行整段复制粘贴，回车：

```bash
cd /home/dell/yuanyuanxu/SIM240 && git commit -F docs/reports/GITHUB_UPDATE_20261110/COMMIT_MESSAGE_CLEAN.txt && git push sim240 main
```

推送期间终端会显示进度百分比，几百 KB/s 的网速大约十几分钟，不要关窗口。

### 指令 B：交给另一个 AI 执行

把下面整段（从 `【任务】` 到结尾）复制给那个 AI：

```text
【任务】
把 /home/dell/yuanyuanxu/SIM240 仓库中已暂存的内容提交并推送到 GitHub。

【背景】
该仓库已完成筛选与暂存：8354 个文件（8349 新增 / 5 修改），约 201 MB，
全部为文档、源码与小体积配置证据。不要重新挑选文件，不要改变暂存范围。

【必须执行的三条命令】
cd /home/dell/yuanyuanxu/SIM240
git commit -F docs/reports/GITHUB_UPDATE_20261110/COMMIT_MESSAGE_CLEAN.txt
git push sim240 main

【硬性约束，违反会出事】
1. 推送目标只能是远程名 sim240（yuanyuanxu1022/SIM240），分支 main。
2. 绝对禁止推送到 origin（那是 junjieli2/nanrPrint，别人的仓库，已设为只读）。
3. 绝对禁止使用 git add . 或 git add -A，不要重新暂存。
4. 绝对禁止 git push --force 或 --force-with-lease。
5. 不要执行任何删除文件、git reset --hard、git clean 的命令。
6. 如果推送因远程有新提交被拒，改用 git pull --rebase sim240 main 后重推，
   并把完整输出贴回来，不要自行强制推送。

【完成后请贴回以下输出】
git log --oneline -3
git show --stat --oneline HEAD | tail -5
git status --short | grep -c '^??'
```

## 三、提交前自查（可选，只读，随时可跑）

```bash
cd /home/dell/yuanyuanxu/SIM240
git diff --cached --shortstat
git -c core.quotePath=false diff --cached --name-only | grep -iE '\.(npy|vti|vtm|png|pdf|pptx|o|so)$'
```

第二条命令应当**没有任何输出**（说明没混进二进制）。若出现输出，先停下来告诉我。

## 四、撤销（万一想反悔）

```bash
cd /home/dell/yuanyuanxu/SIM240 && git restore --staged .
```

只把"待提交"退回"未提交"，**不会删除任何工作区文件**。

## 五、推送失败怎么办

| 提示 | 含义 | 处理 |
|---|---|---|
| `Permission denied (publickey)` | 本机没配好 SSH 密钥 | 换在有密钥的机器上执行，或配好 `~/.ssh/id_*` 与 GitHub 公钥 |
| `rejected ... fetch first` | 远程有新提交 | `git pull --rebase sim240 main` 后重推 |
| `GH001: Large files detected` | 混进了大文件 | 停下，把输出贴回来 |
| `remote: error: File ... exceeds 100 MB` | 同上 | 同上 |
| 卡住不动 | 只是网络慢 | 等，别按 Ctrl+C |

## 六、推送完核对

```bash
cd /home/dell/yuanyuanxu/SIM240
git log --oneline -3
git show --stat --oneline HEAD | tail -5
```

预期：`git log` 顶部是 `docs: 补齐 9 月以来未入库的论文文档与算例档案`，
`git show --stat` 显示 `8354 files changed`。

## 七、这次没动的两件事（下次再议，别顺手做）

1. **`CASE/reports/` 下 35 个文件在工作区已删，但删除动作没有提交。**
   它们会继续留在 GitHub 上，不会丢。这 35 份在 `docs/reports/` 里找不到同名替代，
   一旦提交删除就永久少一份 —— 等确认确属废弃再单独处理。

2. **2285 个运行审计文件被项目自己的 `.gitignore` 拦下**（`audits/`、`runs/`、
   `.backend/`、`.conda_pkgs/` 等）。要不要强制上传由你定：
   - `audits/`（约 700 个，多为小 json）值得强传，是"算例真跑过"的证据；
   - `.backend/` 与 `.conda_pkgs/` 绝对不要（内含整套编译工具链与 conda 缓存）。
   - 完整清单见 `blocked_by_gitignore.txt`。

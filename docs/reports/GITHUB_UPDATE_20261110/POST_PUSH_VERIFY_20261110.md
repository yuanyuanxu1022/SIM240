# 推送后核验报告（2026-11-10 20:40）

## 一、推送结果

| 项 | 值 |
|---|---|
| 提交 | `ac4b15a docs: 补齐 9 月以来未入库的论文文档与算例档案` |
| 远程更新 | `9bad48a..ac4b15a  main -> main`，已被 GitHub 接受 |
| 本次入库 | 8354 个文件 / 181 万行新增 / 约 201 MB |
| 压缩传输 | 8224 个对象，17.58 MiB（压缩率约 11:1） |
| 仓库跟踪总数 | 1168 → **9517** |

## 二、内容核验（逐项实查）

**论文关键件全部在库**：中文稿、英文稿、结论定稿、权威清单、MANIFEST、
投稿派生件 CN/EN、中文补充方法——8/8 命中。

**文件未被改动**（哈希与 §1.1 权威表一致）：

| 文件 | SHA 前 16 位 |
|---|---|
| `SIM240_中文稿_导师审阅版_20261022.md` | `5c35a49819add94e` |
| `SIM240_First_Paper_English_20261028.md` | `fff9aff2eafc583a` |
| `PAPER1_submission_manuscript_20261110/SIM240_submission_CN.md` | `ef66ce61f8b80f7d` |

**密钥扫描**：9517 个文件全扫（私钥头、GitHub 令牌、AWS 密钥、通用 api key、
OpenAI 格式），**0 命中**。

**二进制扫描**：提交内 `.npy/.vti/.vtm/png/pdf/pptx/.o/.so` **0 个**。
`.workbuddy/`、`.vscode/`、`.Trash-0/` **0 个**。

**未上传的 2285 个**（被项目自身 `.gitignore` 拦下）经抽查全部为合理排除：
`build_fields_*/`（构建产物）、`runs/*/provenance/`（运行副本）、
`src/lnInclude/`（OpenFOAM 符号链接）、`.pytest_cache/`、
`.backend/`（GCC 工具链副本）、`.conda_pkgs/`（conda 缓存）。

## 三、发现并已处理：两个不该入库的文件

推送内容里混进了两个根目录临时文件，已在本地提交 `16a1cdd` 移除：

| 文件 | 问题 | 处置 |
|---|---|---|
| `test.txt`（35 B） | 工具调用测试残留"WorkBuddy 工具调用测试成功" | 从版本控制移除，本地保留 |
| `tmp_jain2017.txt`（35 KB） | **Jain 2017 论文全文提取**，Elsevier 版权内容 | 从版本控制移除，本地保留 |

同时在 `.gitignore` 增加规则：`/test.txt`、`/tmp_*.txt|py|csv`、
`/paper_database/**/*_fulltext.txt`，防止再次误入库。

**还要推送一次才生效**（见第六节）。

## 四、需要你决定的两件事

### 4.1 仓库目前是**公开**的

匿名访问 `api.github.com/repos/yuanyuanxu1022/SIM240` 返回 200，说明是公开仓库。
公开状态带来三类暴露，都已在本次提交里存在：

**① 已发表论文的全文（最需要注意）**

仓库里有 **56 个 `.txt`、合计 4.4 MB** 的论文全文提取，集中在：

| 位置 | 文件数 | 说明 |
|---|---|---|
| `docs/reports/PAPER1_V2_downloads_source_audit_20261110/text/` | 41 | V2 来源核查时提取的 30 篇文献全文（`*_full.txt`、`*_first2.txt`） |
| `docs/reports/Primary_text_received_20261027/evidence/` | 3 | 含 `NEW_THIRD.txt`（280 KB） |
| `docs/reports/Jain_citation_audit_20261017/raw/` | 3 | Jain 2017 等原文提取 |
| 其余分散 | 9 | 下载源、预检材料 |

这些是出版社版权内容。**公开仓库相当于对外分发**，严格说未经授权。

**② 内网信息**

`docs/reports/服务器*.md` 三份含 `10.103.102.55`（内网地址，公网不可达）、
用户名 `yuanyuan`、本机路径 `/home/dell/...`、公钥内容（公钥本身无风险）。
风险等级低（私网 IP 无法从外部访问），但暴露了内网结构。

**③ 未发表成果全文**

两篇稿子、补充材料、430 个评审目录都在公开仓库里——投稿期间可能有
"已公开"争议，部分期刊要求稿件未公开发表。

**三个选项：**

| 选项 | 做法 | 效果 | 代价 |
|---|---|---|---|
| **A（推荐）** | 把仓库改成 Private | 一次性解决①②③，无需改动内容与历史 | 只有你能看；协作者需逐个加；免费额度无限制 |
| B | 保留公开，删除 56 个全文 txt | 只解决①，且历史里仍有 | 需再清一次，且核查报告引用会断 |
| C | 保持现状 | 什么都不用做 | 风险自担 |

改 Private 的路径：GitHub 网页 → 仓库 `Settings` → 最下方 `Danger Zone` →
`Change repository visibility` → `Make private`。**一步点完，不影响任何文件。**

### 4.2 那 35 个已删除的 `CASE/reports/` 文件

仍未提交删除，所以**它们仍在 GitHub 上存在**（这是上一轮故意保留的）。
现在既然全量补齐了，可以确认一下：这 35 份是否确有替代或确属废弃？
如果确认废弃，我可以单独提交一次删除；如果想留档，就永久保留。

## 五、还差什么没上

| 类别 | 数量 | 是否该上 |
|---|---|---|
| 场数据 `.npy/.vti/.vtm` | 约 4200 个 | 否——二进制，Git 会永久膨胀 |
| 图件 `.png/.pdf`、幻灯片 `.pptx` | 含在内 | 否——可重新生成 |
| 编译产物 `.o/.so`、日志 | 含在内 | 否 |
| 单文件 > 500 KB 的 csv/json | 234 个 / 502 MB | 否——仿真原始输出 |
| `audits/`、`runs/` 运行证据 | 约 2285 个 | **由你定**——见下 |

关于 `audits/`：约 700 个小 json，是"这个算例真的跑过"的证据链。要传需用
`git add -f` 强制绕过 `.gitignore`。我倾向**不传**：结论已在各报告的
`verification.json` 与 `acceptance.json` 里体现，重复度高。

## 六、下一步指令

推送清理提交（一行）：

```bash
cd /home/dell/yuanyuanxu/SIM240 && git push sim240 main
```

推送后建议立刻把仓库改 Private（第二节 4.1 选项 A），两件事可以一起做。

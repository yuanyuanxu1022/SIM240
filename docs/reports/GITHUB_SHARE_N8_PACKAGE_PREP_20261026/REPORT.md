# SIM240_code_figures_data：N8方法资料提交草案核对

日期：2026-10-26。本文件记录**上传前准备快照**；用户随后明确要求上传，当前发布结果见[PUBLISH.md](PUBLISH.md)与[publish.json](publish.json)。准备阶段状态为`LOCAL_STAGED_REVIEWED_NOT_COMMITTED_NOT_PUSHED`；该阶段用户只授权整理和核对提交内容，没有授权实际N8提取、重跑或第二项计算。

## 目标与本地草案

- 目标：私有仓库 `yuanyuanxu1022/SIM240_code_figures_data` 的 `main`，核对时远端HEAD为`076bf7001ab9aeab7508a5a59c43a3a0f907718a`；本机账号有ADMIN权限。主项目的`origin`仍指参考仓库`junjieli2/nanrPrint`，本轮未从主项目推送。
- 独立本地副本：`/home/dell/yuanyuanxu/SIM240_code_figures_data_review_20261026`。仅在该副本暂存，尚无新commit或push。主项目已有未相关改动不带入。
- 暂存206路径：202个新增、4个修改。新增含200份主项目来源原字节副本、1份查看入口、1份提交草案核对JSON。修改为根`README.md`、`00_当前进度.md`、`清单与核验入口.md`、`文件清单.csv`。

## 200份来源的白名单

|来源|份数|共享仓库位置|
|---|---:|---|
|D4_N8_acceptance_20261026|10|`01_代码/00_技术说明/D4_N8_acceptance_20261026/`|
|G4_minimum_reference_contract_20261026|10|`01_代码/00_技术说明/G4_minimum_reference_contract_20261026/`|
|G4_reference_criteria_review_20261026|8|`01_代码/00_技术说明/G4_reference_criteria_review_20261026/`|
|G4_offline_extractor_preparation_20261026|13|`01_代码/00_技术说明/G4_offline_extractor_preparation_20261026/`|
|G4_offline_extractor_review_20261026|7|`01_代码/00_技术说明/G4_offline_extractor_review_20261026/`|
|G4_offline_extractor_revision_v2_20261026|137|`01_代码/00_技术说明/G4_offline_extractor_revision_v2_20261026/`|
|初版提取器代码|5|`01_代码/计算与分析/D4_variable_groove_transport_20261023/reference_backend_min18_20261025/offline_extractor_preparation_20261026/`|
|v2提取器代码|10|`01_代码/计算与分析/D4_variable_groove_transport_20261023/reference_backend_min18_20261025/offline_extractor_revision_v2_20261026/`|

200份共5,412,730字节。保留两个完整人工成功/故障过程包，其中50份`.npy`是明确标记的人工夹具，不是实际N8数据。各目录的`before_*.md`是含主项目完整交接和第二篇状态的历史快照，未复制到第一篇共享包。`delivery_integrity.json`仍保留原本地交付快照，不能据它声称共享包包含全部本地路径。实际N8原始矩阵、场数组和完整运行目录未收录，故该共享包不能独立重算N8物理指标。

## 核对结果

- 旧`文件清单.csv`的8,391行前缀与当前远端基准提交中的文件逐字节相同；新添200行后为8,591行，每条新增源文件和共享副本字节、大小、SHA-256一致，源路径与目标路径均无重复。旧提交的`检查记录/文件完整性.json`记录8,391份、52项索引、无SHA问题、`ok=true`；本轮没有重新读取那8,391份原件。
- 全部暂存Markdown链接在新增文件或旧Git树中均找到目标；按常见GitHub凭证和私钥模式扫描暂存文本，命中0路径。暂存路径中没有`build/`、真实`results/`、`tmp/`、缓存、`before_*.md`、`.o`或`.d`。
- 在独立共享副本运行v2人工测试：30组、0失败、exit0。该测试不导入PDE后端，不接触实际N8数组。旧报告另保留两个独立人工进程0/2退出记录。
- `git diff --cached --check`的常规默认检查会对旧格式CRLF清单的200行报行尾提示，并对故意追加空白以触发损坏拒绝的`independent_failure/synthetic_record/synthetic_aux_00.json`报提示。该文件与原失败夹具字节/SHA相同，不能为排版整洁而更改。按CRLF约定并单独排除这份故障输入后，剩余暂存内容的空白检查通过。
- 曾尝试把稀疏副本补齐以重做全包8,591项校验；远端旧文件下载过慢，已中止该额外检查。暂存草案保持完整；本轮结论只依赖旧基准提交不变、旧8,391项历史验证记录及新增200项的当前逐字节验证。

## 科学与执行边界

共享仓库首页新日期段准确标为：N8仅代数/记录诊断验收，参考判据仍是建议，v2仅人工软件测试；`NUMERICAL_GATE=NOT_EVALUATED`、`RESULT_PASS=false`、`geometry_PASS=null`、`reference_qualified=false`、`submission_ready=false`，预测`HOLD`。本轮没有新求解、实际N8提取、公式精度放行或论文投稿。

下一动作若用户明确要求上传：先复核共享仓库`main`远端HEAD是否仍等于本次基准，再只在独立副本复核暂存206路径，创建单次阶段提交并推送该仓库`main`，之后核对远端提交和入口文件。没有复用主项目`sim240`或参考仓库`origin`。目前无需用户执行终端命令。

本报告的证据约束写法参考`scientific-writing`技能。方法来源：Kassis, T., Agarwal, V., He, Y., Patel, D., & Brueckner, A. M. (2026), *Scientific Agent Skills: A Library of Procedural Knowledge for Research Agents*, [arXiv:2609.00065](https://arxiv.org/abs/2609.00065)，当前v2；不作为CFD精度证据。

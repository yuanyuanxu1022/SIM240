# A范围基础下界的双语定点合入

2026-11-09，Asia/Shanghai。用户明确采用A范围，要求按修正版衔接双语附录与讨论、核对编号引用及哈希，并明确无需重复下界理论复核。本轮已实际合入当前工作稿；不再等待相同范围的采用或合稿。

## 实际修改

| 文件 | 变动 |
|---|---|
| [中文正文](../SIM240_中文稿_导师审阅版_20261022.md#appendix-e-lower) | 附录E末增加E.1“基础下界及其适用范围”；§5.1末新增一句回指 |
| [英文正文](../SIM240_First_Paper_English_20261028.md#appendix-e-lower) | 与中文对应的E.1及§5.1回指，公式与限制一致 |
| [现有MANIFEST](../PAPER1_submission_package_20261109/MANIFEST.md) | 重绑定两份正文的SHA256前16位和字节数，增加本轮有限范围说明及完整哈希回执入口 |

两份共享状态另同步当前停点。未改摘要、五条正文结论、原编号公式、原上界推导、科学参考文献或双语补充S1—S14。新增公式仅为(E7)固定驱动的变分恒等式及(E8)合并上下界；未新增正式图号、表号或补充编号。修正版区间图仍在独立追溯目录，不作本轮新增投稿图。独立六条结论文件保留原样；其与正文五条结论的既有组织差异没有在本轮重排。

## 采用的科学范围

直接转写已完成复核的贯通h层试探场、可容许性说明及固定驱动变分方向；未重新开展理论复核。采用条件沿用原附录E：全充液、不可压缩、常黏度牛顿Stokes、静止无滑移壁面、匹配周期面及h>0。新增文字不把下界解释为真实槽内速度、不赋予槽宽依赖、不提升为主要创新或普适预测律。

为避免读者把区间当作精度保证，保留沿槽最大U/L=63、横槽约1.984及归一化左端的说明。46条不同离散记录均处于上下界内，只称相容性。下界/局部立方律的偏差比较仍限原18几何36条5 nm结果：沿槽58.2%低估/88.8%高估，横槽23.8%/30.6%，两方向各11/18下界更近。未将新增间隙、加密或两宽度诊断组混入分母，未将偏差改称纯连续模型误差。

讨论新增一句仅说明连续主导度受上下界约束，以及这种范围不能给出机制份额或通用点预测精度。原机制段落与其限制保持，不引入新机制主张。

## 来源与核对

| 证据 | 已打开并核对的定位 | 本轮用途 |
|---|---|---|
| [既有下界复核](../PAPER1_contribution_bound_audit_20261109/LOWER_BOUND_REVIEW.md) | §1—3及§5 | 转写已审试探场、变分方向及适用条件；不重复证明审查 |
| [修正版说明](../PAPER1_interval_note_review_20261109/REVISED_NOTE.md) | 公式、集合及解释段 | 限定本轮已采用的文字范围 |
| [46条归一化记录](../PAPER1_interval_note_review_20261109/normalized_records.csv)及[核查回执](../PAPER1_interval_note_review_20261109/verification.json) | raw_path、in_primary36、两方向K/L与U/L | 记录去重、区间宽度及相容性；未处理流场 |
| [原36条基线汇总](../PAPER1_lower_baseline_comparison_20261109/summary.json) | P/T的count、mean_absolute_relative_bias_percent、lower_closer_than_LC_count | 已有平均偏差及11/18读数，正文使用一位小数 |
| 实际合入前当前两稿 | 本目录*.before及baseline_hashes.json | 本轮以实际当前稿为底稿，保留前轮已有修改 |

以上为AI辅助来源与一致性核对记录，不冒称另一个人已签字终审。用户授权采用本范围，不等于已完成整篇作者科学终审。无新增外部科学引文，原[1]—[11]条目逐字保持，未重新宣称全篇书目已再次逐篇核验。

`check_merge.py`实际运行，**108项通过、0失败**，详见[verification.json](verification.json)。核对内容包括：

- 逆序撤销已记录替换可逐字还原实际底稿，确认没有未记录的正文改动。
- 摘要、第1—4章、五条结论、原附录E推导及原参考文献保持；原显示公式与标签保留，只增E7/E8；两语新增显示公式完全一致。
- 四稿全部Markdown本地文件和显式锚点可以定位；新增讨论回指E.1及E8可定位。
- 46条去重记录、38＋8构成、19种几何、原36条统计及端点偏差一位小数与已保存证据一致。
- 现有MANIFEST的8个编号文件条目，其哈希前缀及字节数均对应当前文件；三份本轮改动文件另保存完整SHA。
- 23份受保护输入SHA无漂移，包括双语补充、S1—S9表、编号映射、独立结论文件、理论报告、CSV和修正版图件等。

这些是文稿、算术、编号、引用路径与文件一致性核对，不是108项科学验证、连续误差验收或新的Gate。新文段未附加尚无证据的机制或精度结论。

执行记录：[merge.py](merge.py)、[check_merge.py](check_merge.py)、[edits.json](edits.json)、[逐项链接回执](link_checks.json)、[MANIFEST八项回执](manifest_rows_verified.json)、[完整输出SHA](output_hashes.json)。差异文件为本目录三份*.diff，改前原件为*.before；旧任务的哈希记录保留其历史快照身份，不重写成当前绑定。

## 完成状态与边界

本次A范围双语合稿及一致性任务完成。已同步 `docs/reports/SIM240_AI_CONTEXT.md` 与 `docs/reports/AI_HANDOFF_PORTABLE_20261104.md`，将前轮“若采用A则合稿”的停点改为已完成。后续若继续，按先前贡献裁决处理最近工作比较；本轮不自动启动文献扩写、改题、重排结论或新增计算。

本轮没有新run_id，无求解器源码/原数据/系数/协议/门槛变动，无编译、求解、拟合、原场处理或保留结果读取；无提交、推送、上传或投稿。S4原FAIL、D4窄槽网格目标FAIL、reference_qualified=false、strict_error_bound_established=false、submission_ready=false保持，无0.625/S5/新几何长算授权。

## 写作流程来源

本轮用scientific-writing整理来源、限制及双语一致性。流程来源记录于此，不加入论文物理参考文献：Kassis, T., Agarwal, V., He, Y., Patel, D., & Brueckner, A. M. (2026). *Scientific Agent Skills: A Library of Procedural Knowledge for Research Agents*. [doi:10.48550/arXiv.2609.00065](https://doi.org/10.48550/arXiv.2609.00065)。2026-11-09公开记录核对为v2。该来源不支持本论文流体力学结论。

## 后续：呈现修正（2026-11-09 晚）

本报告记录的两正文 SHA（`7ce3ac6b…` / `0554657c…`）及 `output_hashes.json`、`manifest_rows_verified.json` 为**本轮当时的收据，不回改**。其后独立复核发现两处新加文本自身的呈现问题（新段落百分比一位/两位小数不一致；附录标题仍写“上界性质”而内容已含 E.1 下界），已另行修正：见 `docs/reports/PAPER1_lower_bound_fix_20261109/REPORT.md`，当前有效 SHA 以该目录 `output_hashes.json` 为准。本次修正不改变本报告的实质结论与证据边界。

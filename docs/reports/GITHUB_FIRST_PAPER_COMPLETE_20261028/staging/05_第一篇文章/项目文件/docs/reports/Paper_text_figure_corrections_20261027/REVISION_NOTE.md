# 第一篇图文定点订正记录

日期：2026-10-27（Asia/Shanghai）。作者审阅工作稿；用户明确授权按上一轮只读核对清单小范围修改。本次不作公式、结论的最终理论冻结，不裁定严格误差界，不启动计算或真实N8提取。

## 1. 修改范围

当前正文为 `docs/reports/SIM240_中文稿_导师审阅版_20261022.md`，保留其V2经验关系，没有将后续G4候选写入正文。

| 组 | 位置 | 订正 |
|---|---|---|
| E01 | 当前图2，旧文件Fig4 | 图内“over the whole range of d”收紧为“over the sampled depths”；中文图注说明小于4%只描述各间隙已采样槽深，并列明h=25 nm仅有d=25、50、100 nm。独立图注记录同步。 |
| E02 | 当前图3，旧文件Fig7 | 纵轴由旧“error of Eqs. (1)”改为不依赖式号的“local cubic-law error (%)”；正文图注分别指向局部立方律式（3）和误差定义式（4），保留对数轴及不同范围说明。独立图注记录同步；当前图4图注明确独立色标和斜线缺失格。 |
| E03 | 正文附录B | 6个倍率和4个误差端点分别改指表5、表6；“本轮复算”改为“既有复算”，不将本轮文字修订冒充新的全面数值验收。 |
| E04 | 正文§2.4 | 区分数值验证、独立求解器交叉核验与物理验证。独立求解器对照不能单独证明真实物理保真度；同几何独立对照与实验比较尚未完成的边界保留。 |

正文附录D.6记录本次接续。摘要、§4结果、§5讨论、§6结论、公式及全部原表格内容保持修改前文本；没有更改系数、数值参考、采样点或阈值。

## 2. 图件与检查方法

只替换 `figures/paper/Fig4_K_and_anisotropy.{png,pdf,svg}` 和 `figures/paper/Fig7_error_vs_gap.{png,pdf,svg}` 六个文件。当前图1/图4（旧Fig1/旧Fig8）不重新导出，原字节受保护。

`render_selected.py`在本地执行既有绘图逻辑，将输出重定向到本目录`staged/`。Fig7/Fig8脚本在Fig8开始前停止，不执行Fig8段落；旧源码执行仅收集绘图对象，抑制导出。旧/新绘图对象的曲线横纵值、坐标范围、刻度、比例尺、颜色、标记及线型逐项比较，结果见`render_comparison.json`。这属于展示数据的一致性检查，不是求解器复现。

PNG及实际PDF经Poppler渲染的预览均由本轮助手目视检查，记录在`visual_QA.json`，预览保留在`pdf_previews/`。该检查不是人工作者最终审阅，也未验收嵌入正文后的版式。SVG检查XML结构与标注，没有声称完成其全部浏览器渲染测试。

导出环境：Python 3.14.7、Matplotlib 3.11.2、NumPy 2.5.3、Pillow 12.3.0；PNG使用原脚本400 dpi设置。历史图件与本次软件环境可能不同，布局与边缘像素尺寸可有小幅差别，不要求新旧文件字节一致；实际绘图值及轴设置的比较独立记录。本次没有重新核查目标期刊的最终图件规范，不据格式或dpi声称期刊合规。

## 3. 可复核文件

- `before/`：正文、两份绘图脚本、两份独立图注、六个原图件及两份状态/交接的修改前快照。
- `input_hashes.json`：13个拟改文件的原哈希与436份选定来源/原始结果/日志/历史记录/锁及未改图件的保护清单。436是本轮选定文件集合，不冒充历史全项目保护集合。
- `render_selected.py`、`render.log`、`render_comparison.json`：选择性导出及旧/新绘图对象比较。
- `visual_QA.json`、`pdf_previews/`：助手目视检查范围与实际PDF预览。
- `verify_revision.py`、`verification.json`：正文不变项、原始数据、显示标注、导出文件及来源保护检查。
- `changes.diff`：相对于本轮快照的文本差异；图件字节哈希另列。原Git工作树已有的其他改动不归入本次修订。

## 4. 保留限制与接续

当前仍是相对于指定5 nm离散数值参考的有限样点误差评价。历史细横槽FAIL、全地图空间误差界缺口与52项历史构建来源限制保持。没有把G4的新几何测试或整套18项矩形基准列为当前限定稿的自动前置，也没有裁定其参考资格。

源诊断run_id仍为`D4_N8_diag_v3_1_20261026_v1`；本轮没有新求解run_id。N8仍仅`ONE_N8_DIAGNOSTIC_ACCEPTED`，`NUMERICAL_GATE=NOT_EVALUATED`、`RESULT_PASS=false`、`geometry_PASS=null`、`reference_qualified=false`、`strict_error_bound_established=false`、`submission_ready=false`、预测HOLD。未运行OpenLB、有限元后端、真实N8提取、拟合或预测评分；未编译、提交或推送GitHub。

本次修订后的具体接续是：作者/导师审阅订正稿；后续若继续准备投稿，先核图件嵌入后的版式、未闭合引文及数据公开声明。最终理论冻结或严格误差界审定应另行按项目要求使用GPT-6 Astra｜High作终审，本次不声称已经切换或完成该审定。

## 5. 辅助流程来源

本次使用scientific-writing与scientific-visualization技能，辅助来源记在此修订记录中，不增改正文的CFD参考文献：Kassis, T., Agarwal, V., He, Y., Patel, D., & Brueckner, A. M. (2026). *Scientific Agent Skills: A Library of Procedural Knowledge for Research Agents*. [arXiv:2609.00065](https://arxiv.org/abs/2609.00065)。2026-10-27核对公开元数据，当前记录为v2，未见期刊发表字段；该来源仅说明辅助流程，不作为本研究物理证据。外部查询仅使用公开文献标识，没有发送项目稿件或数据。

# §1.2第一段审读：压印应用与平均关系的引用分工

日期：2026-11-07。用户授权按段审读；本轮形成中英文候选，不合入正式引言。无新增数值计算或数值验证。

## 原段

> 以等效输运系数描述未解析图案，在压印建模中已是常规做法：Jain 等将各向异性输运用于图案化模板下的液体流动计算，后续压印模型也沿用这一处理 [1–3]。Patir 与 Cheng 的平均流模型给出了流量因子的来源，其条纹平均关系正是本文比较的对象之一 [4]。

## 裁定及逐句修改

- “常规做法”是领域采用频率判断，所列几个例证不足以作系统性概括。改为点名模型及其用途，不否认已有应用。
- Jain [1]支持在图案化模板过程模型中，用有效各向异性渗透率表征密集线槽图案并研究液滴铺展、合并和填充；不借过程模型表现认证本文的指定几何导度、V2准确度或实际工艺精度。本轮没有据有限访问断言Jain全文从未验证系数。
- [2] Ban–Bonnecaze 2020与[3] 2021可保留，但明确各自关注布滴与多结构模板填充。指定原文方法页确有有效渗透率张量，足以支持这一有界的延续关系；不声称所有系数定义、几何或边界与本稿完全相同，也不写原封不动沿用所有关系。
- Patir–Cheng [4]是平均流框架和一维条纹极限平均关系的文献依据。印刷第15页式（23）（24）分别给出横向调和、纵向算术流量因子关系，原文还指出相应结果来自既有随机过程理论，故不写其首次发明该平均关系或“流量因子的唯一来源”。
- 原文流量因子为无量纲量；还原相应参考高度三次方及1/12后，才与本稿深度积分导度K（m³）比较。该模型内平均关系不等于矩形台阶全Stokes域精确解，也不证明侧壁耗散等候选机制。
- 当前第三段已详述系数定义差异；本段只说明引用分工及简要换算要求，具体式子继续放§2.3/补充S6，避免重复。

## 中文候选

> Jain 等以等效各向异性渗透率描述密集线槽图案的平均输运，并将其用于压印液滴铺展、合并及填充模拟[1]。Ban 与 Bonnecaze 在相关压印模型中进一步研究了布滴优化和多结构模板下的填充问题[2,3]。Patir 与 Cheng 的平均流模型则提供了局部 Reynolds 近似下的一维纵向算术平均与横向调和平均关系[4]；本文将这些关系换算为同一定义的深度积分导度，用于与固定、全充液矩形沟槽的显式计算比较。

## 英文对应候选

> Jain et al. represented the mean transport of dense line-and-space patterns through an effective anisotropic permeability and used it to simulate droplet spreading, merging and filling during imprinting [1]. Ban and Bonnecaze subsequently studied droplet-placement optimization and filling beneath templates containing multiple structures in related imprint models [2,3]. The average-flow model of Patir and Cheng provides arithmetic and harmonic averaging relations for one-dimensional longitudinal and transverse patterns, respectively, within the local Reynolds approximation [4]. Here, these relations are converted to a common depth-integrated conductance definition for comparison with groove-resolved calculations in fixed, fully filled rectangular grooves.

## 本轮来源核对范围

本轮是作者授权的AI辅助文字与引文对应检查，不冒称作者已完成独立人工作者核验或全面新颖性裁定。只向网页发送公开题名/DOI等文献元数据，未发送未发表稿文。

| 来源 | 本轮实际读取 | 用于支持 |
|---|---|---|
| Jain 2017 DOI 10.1016/j.mee.2017.04.001 | 出版社直开403；公开检索返回同一出版社的摘要、Highlights及可见节选 | 有效各向异性渗透率与压印过程应用，未重读完整方法/补充 |
| Ban 2020 DOI 10.1116/6.0000030 | 已保存发表版PDF，定向提取方法/摘要及相关段落，PDF第3–5、8、12页；其中PDF第4页为022601-3 | 有效渗透率张量、Jain框架及布滴/毛细边界研究；未逐式核全部推导 |
| Ban 2021 DOI 10.1116/6.0000648 | 已保存发表版PDF，定向提取方法/相关结果/引用，PDF第4、7、9、11、12页；PDF第4页为012601-3 | 有效渗透率张量与多结构区域填充模拟；未独立复算其过程结果 |
| Patir–Cheng 1978 DOI 10.1115/1.3453103 | 本地原文页图patir_page4.png重新目视核对，印刷第15页式（23）（24）；对照已有Methods_support审计及补充S6 | 原文流量因子及模型内平均关系，非全台阶域精确性 |

Ban两篇DOI网页本轮不可访问，公开搜索中的第三方摘要只用于定位，不作为上述技术结论的证据；技术依据为本地发表版。两篇封面分别明确2020年38卷022601、2021年39卷012601，后者在线发表于2020年12月，不修改其2021卷期引文。文献编号[1]–[4]保持当前书目，无新增文献身份。

公开Jain来源：https://www.sciencedirect.com/science/article/pii/S0167931717301296 。本地原文位于 `docs/reports/Jain_citation_audit_20261017/raw/`；Patir页图位于 `docs/reports/Methods_support_audit_20261022/`。

工作流使用scientific-writing及academic-humanizer；程序性来源记为Kassis, T., Agarwal, V., He, Y., Patel, D., & Brueckner, A. M. (2026), Scientific Agent Skills: A Library of Procedural Knowledge for Research Agents, arXiv:2609.00065，https://doi.org/10.48550/arXiv.2609.00065 。本轮核公开元数据当前v2，不在标识后加版本号；仅属写作流程来源，不作为流体科学论据或另添正文引文。

## 停点

正式中英文引言均未改，前轮已合入摘要保持；本轮仅本审读目录及两份共享状态更新。无仿真、拟合、场读回、耗散分解、新run_id、Gate放行或上传。S4原FAIL、reference_qualified=false、submission_ready=false不变。若继续逐段，下一动作审§1.2第二段Dewangan–Datta的谱方法/摄动方法、几何限制与近邻先例作用；若用户明确要求采用候选，再合入并检查相邻段重复。

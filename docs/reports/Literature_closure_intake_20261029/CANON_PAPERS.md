# 与本项目相关的佳能署名文献：身份核对与阅读顺序

> 全文接收更新（2026-10-29）：用户已提供Seki2022、Sreenivasan2017、Choi/Resnick2019三篇PDF；当前接收/阅读证据以[新报告](../Canon_received_review_20261029/REPORT.md)及intake.json为准。下方“未取得全文”是先前检索阶段记录，现已被接收证据更新；2020会议版仍未收到。

核对日期：2026-10-29。范围：针对当前Ban文献及“闭环”问题的定向检索，不是佳能全部出版物的系统目录，也没有确认老师指定的唯一文章。

## 判别依据

以文章作者署名单位为依据，区分Canon Inc.、Canon Nanotechnologies Inc.、大学与企业双重署名，以及仅引用佳能资料的文章。文章讨论佳能设备不等于作者来自佳能；同样，作者有大学署名也不排除同时有佳能署名。

## 已确认的重点文章

### 1. Seki等，2022：模拟器方向，优先阅读

- 题名：Enabling nanoimprint simulator for quality verification: process-design co-optimization toward high-volume manufacturing。
- 期刊：Journal of Micro/Nanopatterning, Materials, and Metrology 21(1),011005 (2022)。DOI：[10.1117/1.JMM.21.1.011005](https://doi.org/10.1117/1.JMM.21.1.011005)。
- 作者单位：Crossref出版元数据的10名作者均列Canon Inc.或同名带逗号写法；作者本人[清原直樹主页](https://nkiyohara.github.io/)亦列该文及DOI。
- 本轮证据：Crossref题名/作者/单位/日期/摘要，原始回执`canon_sources/Seki2022_crossref.json`。摘要介绍用积分表达降低计算维数，接入工艺参数与液滴配置，预测液滴合并与未填充区域，并称已应用到实际NIL系统。本轮没有取得并逐式审读该篇全文，不能据摘要确认其具体误差、验证独立性或对本项目适用。
- 阅读用途（研究建议）：检查局部模型怎样接入工艺模拟，以及原文怎样对照实际结果。不能预设它使用本项目同一K定义，或直接证明本项目修正有效。

### 2. Seki等，2020：相近题名的会议文章，版本须单列

- 题名：Enabling nanoimprint simulator for quality verification; Process-design co-optimization toward high volume manufacturing。
- 会议：Design-Process-Technology Co-optimization for Manufacturability XIV，Proc.SPIE11328,113280N (2020)。DOI：[10.1117/12.2551999](https://doi.org/10.1117/12.2551999)。
- 身份：SPIE官方[2020会议程序](https://spie.org/Documents/ConferencesExhibitions/AL20-Final-L.pdf)列Junichi Seki等10名作者，Canon Inc.(Japan)，报告11328-21。Crossref核题名/作者/DOI/2020-03-23出版日期，回执`canon_sources/Seki2020_crossref.json`。
- 边界：与2022文章题名及作者接近，但DOI和发表载体不同；全文差异未核，不能互换页码、公式或图号，也不当作两份独立验证证据。

### 3. Ito等，2016：佳能本体与子公司署名，工艺/材料方向

- 题名：Nanoimprint System for High Volume Semiconductor Manufacturing; Requirement for Resist Materials。
- 期刊：Journal of Photopolymer Science and Technology29(2),159-168 (2016)。DOI：[10.2494/photopolymer.29.159](https://doi.org/10.2494/photopolymer.29.159)。
- [J-STAGE官方记录](https://www.jstage.jst.go.jp/article/photopolymer/29/2/29_159/_article/-char/en)列Toshiki Ito、Keiji Emoto、Tsuneo Takashima、Keita Sakai为Canon Inc.，Weijun Liu、James DeYoung、Zhengmao Ye、Dwayne LaBrake为Canon Nanotechnologies,Inc.。
- 摘要涉及J-FIL设备、材料、铺展/填充、套刻、吞吐率与缺陷。适合建立工艺背景与评价量，不单独作为本项目K误差验证。
- 与现有Ban2021的对应：其文末参考文献[5]正是Ito等，J.Photopolym.Sci.Technol.29,2(2016)；书目由本地Ban原文最后一页核对，并用J-STAGE补全题名/页码/单位。

### 4. Sreenivasan，2017：大学与佳能子公司双重署名，产业化综述

- 题名：Nanoimprint lithography steppers for volume fabrication of leading-edge semiconductor integrated circuits。
- 期刊：Microsystems & Nanoengineering3,17075 (2017)。DOI：[10.1038/micronano.2017.75](https://doi.org/10.1038/micronano.2017.75)。
- [出版社原文](https://www.nature.com/articles/micronano201775)和[PMC全文](https://pmc.ncbi.nlm.nih.gov/articles/PMC6445000/)列S.V.Sreenivasan的两单位为UT Austin与Canon Nanotechnologies Inc.。不是纯大学署名的Ban2021，也不是纯佳能本体署名文章。
- 主题为J-FIL工艺、系统与产业化评价，包括材料供给、吞吐率、缺陷、套刻等；用于理解应用目标，不据此声称得到可直接验证本项目K的实验数据。
- 与现有Ban2021的对应：其参考文献[1]即S.V.Sreenivasan,Microsyst.Nanoeng.3,17075(2017)。

### 5. Choi与Resnick，2019：佳能子公司署名，设备进展方向

- 题名：The Status of Nanoimprint Lithography for High Volume Semiconductor Manufacturing。
- 期刊：Journal of Photopolymer Science and Technology32(5),753-757 (2019)。DOI：[10.2494/photopolymer.32.753](https://doi.org/10.2494/photopolymer.32.753)。
- [J-STAGE官方记录](https://www.jstage.jst.go.jp/article/photopolymer/32/5/32_753/_article/-char/en)列Jin Choi与Douglas J.Resnick均为Canon Nanotechnologies Inc.。
- 摘要涉及设备进展、套刻、吞吐率、液滴图案补偿及模板寿命。工艺背景价值已确认；本轮不把液滴图案补偿等同于液体水力系数的验证。

## 对当前阅读任务的建议

若目标是找老师可能指的现有引用，先核Ban2021参考文献[1]与[5]，它们已经能明确对应佳能相关署名。如果目标是研究“局部系数—应用预测—独立对照”的连接办法，先读Seki2022模拟器文章；2020会议文章按独立版本保留。其他三篇作为工艺目标与边界的辅助阅读。

这只是根据主题作出的阅读排序，不是老师指定篇目的确认，也不是已经完成闭环。下一步应取得模拟器全文并核模型输入、平均定义、边界、标定与独立验证证据；没有同条件证据时不能直接移植其结果。

## 检索与权限记录

- 检索来源：本地Ban2021参考文献；公开网页定向检索；J-STAGE官方元数据/摘要；SPIE官方会议程序；Crossref两个明确DOI；Nature/PMC原文与作者个人出版清单。
- 代表检索词：Canon nanoimprint fluid filling simulation；Ito Emoto Takashima Sakai2016；Enabling nanoimprint simulator for quality verification；The Status of Nanoimprint Lithography for High Volume Semiconductor Manufacturing。
- SPIE出版全文页面访问失败；仅元数据/摘要与官方会议程序确认，不伪报全文取得。未向外部服务提交本项目未发表正文或原始研究数据。
- 本轮新增文献身份与阅读建议，无新增数值/物理验证，无源码修改/编译/求解/拟合/新run_id/下一Gate/投稿或Git提交推送。历史FAIL、旧N8与现有科学状态保持。

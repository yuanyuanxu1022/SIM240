# “TAN木”文献查找：候选身份核对，尚未唯一确认

日期：2026-10-29。用户明确表示还有另一篇“TAN木”的文献，要求查找；不再将其自动等同于Ban。本记录是定向消歧检索，不是穷尽全部文献，也不是候选全文科学验收。

## 结论与最有用的两条线索

1. 若名字确实拼作Tan，优先核对Hua Tan参与的Liang等2007气泡形成/溶解文章。作者拼写吻合，有实验—模型比较，主题为气体与缺陷。
2. 若导师指的是整片、多尺度、液滴流动与模拟工具，Taylor2016是值得核对的上下文候选；Seki2022直接将其列为参考文献[13]。Taylor和Tan不是同一作者，不能因题材相近就认定。

目前没有足够证据确定老师指哪篇。已向用户询问名字是否为作者或机构、以及年份/主题线索；未知状态保留。

## A. 作者为Tan的候选

- 题名：Air bubble formation and dissolution in dispensing nanoimprint lithography。
- 作者：Xiaogan Liang、Hua Tan、Zengli Fu、Stephen Y.Chou。
- 期刊：Nanotechnology18(2),025303(2007)。DOI：[10.1088/0957-4484/18/2/025303](https://doi.org/10.1088/0957-4484/18/2/025303)。Crossref在线日期为2006-12-15；机构记录按2007期刊卷期引用，二者不混同。
- 身份来源：[Princeton作者机构记录](https://collaborate.princeton.edu/en/publications/air-bubble-formation-and-dissolution-in-dispensing-nanoimprint-li/)、Crossref原回执LiangTan2007_crossref.json及IOP出版社摘要。
- 已核摘要内容：实时观察气泡形成与收缩；基于分子扩散和流体力学建立模型，并与实验比较；讨论初始泡尺寸、压力、溶解性和残膜厚度等因素。
- 与闭环讨论的关系：确有实验/理论对照这一线索；不是SIM240单相K的同几何参照。未取得并审读本文全部原始数据，不能认定具体模型精度、临界值或本项目填充时间。

## B. 多尺度上下文候选，作者为Taylor

- 题名：Defectivity prediction for droplet-dispensed UV nanoimprint lithography, enabled by fast simulation of resin flow at feature, droplet, and template scales。
- 作者：Hayden K.Taylor。
- 出版：Proc.SPIE9777,97770E(2016)。DOI：[10.1117/12.2218757](https://doi.org/10.1117/12.2218757)。
- 身份来源：Crossref原回执Taylor2016_crossref.json（2016-03-22）；[SPIE2016官方会议程序](https://spie.org/Documents/ConferencesExhibitions/AL16-final-L.pdf)列报告9777-9，作者单位UC Berkeley和Simprint Nanotechnologies；[作者纳米压印研究页](https://www.ocf.berkeley.edu/~hayden/nanoimprint.php)列该题名与DOI。
- 项目内原文线索：Seki2022期刊011005-13页参考文献[13]为该文；[21]—[23]也列Taylor的液滴铺展/合并与全模板模拟报告。
- 关联：作者页面介绍全域/多尺度纳米压印模拟方向。此处仅作为识别线索，尚未完成该文全文验证方式审读，不能直接称其完成本项目所需闭环。
- 日期核对：作者旧网页有2015写法，与Crossref2016及SPIE2016程序不一致；本记录用明确DOI对应的出版元数据2016，网页日期差异保持，不据旧网页新建另一独立文章。

## C. 若导师说的是Taylor与Lam，两姓组合的辅助候选

- 题名：A computationally simple method for simulating the micro-embossing of thermoplastic layers。
- 作者：Hayden Taylor、Yee Cheong Lam、Duane Boning。
- 出版：Journal of Micromechanics and Microengineering19(7),075007(2009)。DOI：[10.1088/0960-1317/19/7/075007](https://doi.org/10.1088/0960-1317/19/7/075007)。Crossref原回执TaylorLamBoning2009_crossref.json。
- Seki2022参考文献[11]列该文。与前述2016文献不是同一篇；题目明确为热塑性层微压印，不能直接套用于当前单相固定间隙K。此候选仅在名字线索匹配时继续。

## 本地与其他拼写检查

- 本地下载目录PDF文件名未见可唯一匹配Tan/Taylor/TAMU的对象。`These_HT_compil.pdf`已核首页为Hubert Teyssèdre2013热纳米压印博士论文，不把缩写HT误判为Hayden Taylor。
- 检索了Tan、Tanaka、Tam、TAMU与纳米压印、填充、模拟关键词，出现多种不同主题结果；目前没有足够证据将TAMU机构线索或某篇Tanaka文章与老师所指绑定。未将不相关光学/脱模/器件论文强列为目标。
- 既有Ban2021与佳能三篇PDF保留原字节，未改文件名或题名来强行匹配用户叫法。

## 检索范围与可复查来源

- 时间：2026-10-29。
- 来源：项目现行状态/文献综述、已接收Seki2022参考文献、本地下载目录文件名及Teyssèdre论文首页；公开网页定向发现；Princeton机构记录；SPIE官方会议程序；作者本人出版页；Crossref三个确定DOI。
- 代表检索式：nanoimprint Tan model filling；nanoimprint Tanaka simulation；nanoimprint Taylor Lam droplet simulation；Tan resist flow；TAMU nanoimprint simulation；Tam nanoimprint lithography；Hua Tan nanoimprint；Defectivity prediction droplet-dispensed Taylor；nanoimprint Tan M。
- Crossref查询为/works/{percent-encoded DOI}，每篇的完整endpoint及响应保存在相应JSON；未虚构mailto，不进行大批量检索。
- 本轮没有把搜索摘要当作全文验收；全文取得情况按单独回执为准。即使找到可下载文件，仍需题名/DOI/版本核对。
- 本轮只查找消歧与维护交接，无新增计算或验证、无拟合/求解/真实N8提取/新run_id/下一Gate/提交推送或长算授权。既有挤压阻力目标仍是推荐，不因候选文献改变。

流程技能与来源说明沿用[前轮阅读报告末尾](../Canon_received_review_20261029/REPORT.md)。

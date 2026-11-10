# 两处证据边界措辞修改回执

日期：2026-11-10（Asia/Shanghai）。范围：按用户本轮请求，定点同步中英文诊断说明和§4.2标题，重生成投稿正文、重绑当前文件指纹。使用academic-humanizer v0.3.3保留科学数字、公式、引文和限定语；未扩展至全文润色或科学终审。

## 实际改动

1. 诊断句的实际位置为当前§3.1，中文第259行、英文第253行，并非用户所称§4.3。原文是质量、密度、Mach及边界诊断与通量收敛“分别记录”，没有把它改成“全部通过”。在原句之后新增：

   中文：这些检查的通过不构成导度相对于连续解的误差界。

   英文：Passing these checks does not establish an error bound for conductance relative to the continuous solution.

2. §4.2标题修改：

   中文：局部立方律在全部36条5 nm主方向结果上均高估。

   英文：The local cubic law overestimates all 36 principal-direction results at 5 nm。

上述为每份母稿两处、总计四处精确文字替换。edits.json保存完整before/after，两个diff文件可逐项检查；before目录保存改前Markdown快照。除标题补显已有“5 nm”身份外，所有既有结果数值、系数、单位、公式、图表及引文编号均保留；V2标定归属句未改，主比较分母仍为36条。

## 当前文件与绑定

| 文件 | SHA256前16位 | 字节 |
|---|---|---:|
| 中文母稿 | 26ec0656f7f9c6b6 | 76090 |
| 英文母稿 | fff9aff2eafc583a | 83079 |
| 中文投稿派生件 | a762e27fce51b7d6 | 68163 |
| 英文投稿派生件 | 7aecf220ed7c3093 | 81866 |
| MANIFEST | ec6d62851565ef8f | 30083 |

MANIFEST第1节/§1.4、authority母稿与派生件表、投稿README指纹表均同步SHA和字节。MANIFEST新增§1.8；authority同步MANIFEST自身的最终SHA与字节。生成脚本未改。README原先字节与版本描述滞后，已按本次产物纠正。旧终审报告新增后续处置回执，关闭标题第④项；原审查正文与历史哈希不回写。

## 校验与边界

- 两份母稿均与改前快照逐字重建比对一致，确认为各两处精确替换，其他文字未变。
- 投稿正文先重新生成，再运行build_submission.py --check：两稿一致，脚本所查禁词0、断链0。
- output_hashes.json的18项逐项核SHA和字节，0不一致。
- 当前三份清单的10行正文/派生指纹记录与authority中的MANIFEST绑定核对相符。
- 两补充、独立结论、编号映射、四份数据表及六份图件共13项保护输入SHA/字节无漂移，见verification.json。

上述检查证明文字变更范围和文件绑定一致，不是新增数值/物理验证或录用保证。无新run_id、编译/求解/拟合/原场处理、Gate放行、Git提交推送、上传或投稿。reference_qualified=false、strict_error_bound_established=false、submission_ready=false及既有S4/D4 FAIL保持。

两项已关闭。接续从当前有效文件清单和投稿派生目录继续排版准备；此前§2.3其他候选未自动采用，函数形式直接前身也未因本轮而确认。无需用户启动长算，无0.625nm/下一Gate授权。

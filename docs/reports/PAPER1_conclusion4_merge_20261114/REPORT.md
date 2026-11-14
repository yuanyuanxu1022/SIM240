# 结论第四条采纳（候选 A）落稿记录（2026-11-14）

> 本包记录一次**已执行**的改动：中文稿与英文稿 §6 第四条换成候选 A，两派生投稿件重建，三份登记文件重绑指纹。
> 结论文件（六条口径）**未改**。

## 0 一句话结果

中英母本各改 **1 行**，数字一个未丢（全篇两位小数百分比零增删）；两派生件各改 1 行并已通过 `--check`；三份登记文件 18 处哈希/字节配对与磁盘实况全部一致。**落稿过程中发现并修正了候选文本里的一处单位笔误**（见 §3）。

## 1 改了哪些文件

| 文件 | 行 | 改动 | 改前 | 改后 |
|---|---|---|---|---|
| 中文稿 `SIM240_中文稿_导师审阅版_20261022.md` | L594 | 第四条 644→608 字 | `7f85e77c7155c143`／96904 B | `cb05a1f843de3608`／96801 B |
| 英文稿 `SIM240_First_Paper_English_20261028.md` | L586 | 第四条 2226→2029 字符 | `4badbe87609fa3cb`／109026 B | `bea51ad37ebc400b`／108832 B |
| 派生 `SIM240_submission_CN.md` | L590 | 随母本重建 | `de6e0ff191aa4572`／87418 B | `6ad3fa79f2c734d4`／87315 B |
| 派生 `SIM240_submission_EN.md` | L584 | 随母本重建 | `2eb04d4a3cfbc06c`／107008 B | `97346abec41483bb`／106814 B |
| 结论文件 `PAPER1_conclusions_current_20261109.md` | — | **未改** | `98080077d3ea3a47`／21474 B | 同左 |
| 补充材料中英两件 | — | **未改** | `4c762d99…`／`81706870…` | 同左 |

`git diff` 确认：两母本共 2 个 hunk、2 行改动；两派生件共 2 个 hunk、2 行改动。没有别的文件被动过。

## 2 落稿正文

### 2.1 中文稿 §6 第四条（L594）

**四、** 使用固定V2系数回顾性比较同一主集合，沿槽平均绝对偏差由88.85%降至6.40%，横槽由30.63%降至4.42%，合计35/36条绝对偏差减小，残余最大绝对值分别为10.50%与18.71%（表8）。改善是总体性的，但不保证逐点改善，也不保证方向比改善：h=25 nm、d=100 nm横槽点的改善判断随5/2.5 nm参考改变，h≥50 nm子集的6.92%只对该子集成立（§4.4）。在与主集合并列的有限元独立对照中（§4.5，表9、表10，17个横槽成对几何），固定V2的横槽平均绝对偏差为4.21%、有符号均值+1.83%，方向比与45°重建角的平均绝对偏差由42.72%与5.02°降至7.63%与1.51°，但3个几何的这两项指标同时增大，局部立方律的方向比在2个几何上本就低估，故改善同样是总体而非逐点的。该集合与36条5 nm主统计分属不同参考与不同几何集合，不作合并；新增有限元计算待正式采用，既有有限元结果保留有限采用建议及溯源限制，既有合格有限体积法记录保留资格；本比较既非物理验证，也不构成连续参数域的精度保证。V2残差的间隙依赖、固定d100沿槽残余在h75与h100间的变号与漂移幅度，以及残余须与模型选择、参数估计和参考误差分别评价，见§4.4；等权矩阵下的间隙相关差异见§4.6。这些均指向仅以$d/w$为自变量的因子表达有限，但不单独确定唯一的缺失变量或物理原因。

### 2.2 英文稿 §6 第四条（L586）

**4.** Using the fixed V2 coefficients, a retrospective comparison on the same main set reduces the along-groove mean absolute discrepancy from 88.85% to 6.40% and the transverse value from 30.63% to 4.42%, improving 35/36 records, with maximum absolute residuals of 10.50% and 18.71% (Table 8). The improvement is overall rather than pointwise or uniform in the direction ratio: the transverse record at h=25 nm, d=100 nm changes its improvement assessment between the 5 and 2.5 nm references, and the 6.92% for the h≥50 nm subset holds only within that subset (§4.4). In the independent finite-element comparison listed alongside the main set (§4.5, Tables 9 and 10, 17 paired transverse geometries), fixed V2 gives a transverse mean absolute discrepancy of 4.21% with a signed mean of +1.83%, and reduces the mean absolute deviations of the direction ratio and the 45° reconstructed angle from 42.72% and 5.02° to 7.63% and 1.51°; yet both metrics increase at three geometries and the local-law direction ratio is already underestimated at two, so this improvement is likewise overall rather than pointwise. That set and the 36-record 5 nm main statistics use different references and different geometry sets and are not merged; the new finite-element runs await formal adoption, legacy finite-element results retain their limited-use recommendation and provenance limitations, and qualified finite-volume records retain their qualification; the comparison is neither a physical validation nor a guarantee of continuous-domain accuracy. Gap dependence of the V2 residual, the sign change and drift magnitude of the fixed-d100 along-groove residual between h=75 and h=100 nm, and the need to assess the residual separately from model selection, parameter estimation and reference error are reported in §4.4, while the gap-related variation on the equally weighted matrix is reported in §4.6; all indicate a limited expressive capacity of a factor in $d/w$ alone, but do not identify a unique missing variable or physical cause.

## 3 发现并修正的一处单位笔误（重要）

**问题。** 候选文本把「45° 重建角的平均绝对偏差……降至 7.63% 与 1.51°」写成了 **1.51%**（百分号），角度错标成百分比。中英两份候选都错。

**怎么发现的。** 改完后跑全篇数字增删核对（剔除章节号、表号、几何标签后比较数字集合），结果报"新增 `1.51%` 一个两位小数百分比"。数值本身没变，变的是百分号——候选阶段的"数字去向"核对按纯数字比对，把 `°` 和 `%` 当同一类，所以漏过了。

**怎么修的。** 把两份稿的 `1.51%` 改回 `1.51°`（§4.5 原文本来就是度数）。修后重跑：全篇两位小数百分比**零增删**。

**教训。** 单位符号必须纳入核对项。纯数字集合比对挡不住 `%`→`°`、`nm`→`m` 这类改动；以后凡涉及带单位数字，须同时比较"数字＋紧随单位"的组合。

## 4 核对结果

### 4.1 全篇数字增删（HEAD vs 工作区）

| 文件 | 数字记号总数 | 新增 | 删除 | 两位小数百分比 |
|---|---|---|---|---|
| 中文稿 | 1988→1991 | `8`、`9`、`10`（表8/表9/表10）、`4.4`×2、`4.6`（章节号） | `7.93`、`5`、`2` | 零增删 |
| 英文稿 | 1754→1758 | 同上 | `7.93`、`5` | 零增删 |

逐项确认被删的三个记号：

- **`7.93`**：原文"漂移7.93个百分点>5个百分点"整句退出结论层，原位 §4.4 L434 保留（全篇计数 2→1，中英同）。
- **`5`**：即"5个百分点"结构筛查门槛，同样保留在 §4.4（中文"5个百分点"、英文"five-percentage-point"，均仍在）。
- **`2`**（仅中文）：属 `V2` 标签的一次出现（合并句子时减少一处），非数据值；`2个几何`、`5/2.5 nm`、`35/36` 均原位保留。

### 4.2 派生件重建

`build_submission.py` 先报两件"不一致（需重跑）"，重建后报"一致"，且"无禁词、无断链、图注与附录各就位"。派生件此前与母本一致，说明本轮是唯一触发源。

### 4.3 登记文件重绑

三份文件、18 处（哈希, 字节）配对逐项与磁盘实况比对：**全部 ok，0 处不符**。

- `PAPER1_CURRENT_FILES_AUTHORITY_20261110.md`：五行表 + 派生件两行 + 清单声明一处 + 日期行与说明列。
- `PAPER1_submission_package_20261109/MANIFEST.md`：主交付件表两行、派生件表两行、表头绑定说明。
- `PAPER1_submission_manuscript_20261110/README.md`：两处表格共四行。

**踩到的连带坑（第二次）。** 改 `MANIFEST.md` 会改它自己的哈希，而权威表第 23 行声明了这个哈希，且替换串等长时**字节数不变、哈希照样变**。处置顺序必须是：先定 MANIFEST → 取其终值 → 最后写权威表；反过来会留下指向不存在值的登记。本次因此返工两轮：第一轮把 `8486c579…`→`6ef7f7f2…` 写进权威表，紧接着改了 MANIFEST 表头，哈希变成 `d9176b73…`，只好再改一次。

## 5 未做与仍待

- **未改**：§4.4／§4.5／§4.6 任何文字；表 8／9／10 任何单元格；结论文件与两件补充材料。
- **未新增**：任何仿真、编译、拟合、重冻、run_id。
- **候选包加横幅**：`PAPER1_conclusion4_compression_20261114/REPORT.md` 顶部注明"候选 A 已采纳、本包为采纳前快照"，避免其"改前指纹"被当成现值。
- **仍待（不属本轮）**：C1/C2 采用责任记录未签；C4 外部可复算与受控获取未测；C7 终检；旧采用报告 §3.2"17 个横槽点没有任何解析解或严格界"与附录 E 冲突未修；另一 AI 包内 `REPORT.md` 引用的 `CONTRIBUTION_AND_PROVENANCE.md` 全库不存在。

## 6 复现方法

```
tmp/apply_candA.py           # 按行号精确替换，断言行首前缀
tmp/check_num_invariance.py  # HEAD vs 工作区数字多集比对
tmp/rebind_hashes.py         # 三份登记文件重绑（计数断言）
tmp/strict_registry_check.py # 18 处（哈希, 字节）配对核盘
```

脚本留在 `tmp/`，未入库。规则写在正文，可按同法复现。

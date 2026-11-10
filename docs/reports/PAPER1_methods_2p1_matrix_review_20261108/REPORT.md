# §2.1采样矩阵与表1审读

日期：2026-11-08（Asia/Shanghai）。用户要求核标题、计数、未采样组合及新增结果范围。本轮形成双语候选，不改正式稿、旧统计或原始结果。

## 当前原文

采样矩阵见表 1。**参数组合未完全覆盖**：在 $h=25$ nm 时仅计算 $d=25$、$50$、$100$ nm，未计算 $d=75$ 与 $120$ nm。

> 此处"覆盖"指参数组合的取样范围，与后文 5 nm 的计算网格无关，二者不可混用。

**表 1　采样几何与样点数**

| 间隙 $h$ (nm) | 已算槽深 $d$ (nm) | 几何数 | 主方向样点 |
|---|---|---:|---:|
| 25 | 25, 50, 100 | 3 | 6 |
| 50 | 25, 50, 75, 100, 120 | 5 | 10 |
| 75 | 25, 50, 75, 100, 120 | 5 | 10 |
| 125 | 25, 50, 75, 100, 120 | 5 | 10 |
| **合计** | — | **18** | **36** |


## 裁定及修改理由

1. 表1现有数字正确：h25三种几何/六结果；h50、75、125各五种/十结果，共18种/36结果。两稿表格与保存的44条标量表中的36条5nm记录一致，且这36个run_id与补充表S1的main组一致。每几何恰有Kxx/Kyy各一，无缺方向或重复项。本轮不是重算K或验收原轨迹。
2. 原标题“采样几何与样点数”范围偏宽，全文已含h100新增结果，容易误以为表1列出全部比较几何。改为“主比较集合的采样几何与导度结果数（网格间距5nm）”。末列“主方向样点”改“主方向导度结果数”，不写成36种几何、36独立验证或全部为验证集。原式/V2主比较不因改标题取得独立性。
3. “已算槽深”改为“主比较采用的槽深”；“间隙”明确为残余间隙h。数字与行顺序不变，不把h100追加进表1并把合计改成19/38，以免改变表格与旧主统计的对应角色。
4. 缺项是四档h={25,50,75,125}与五档d={25,50,75,100,120}的离散组合内，h25/d75及h25/d120未出现在主比较清单。宜写“本主比较矩阵未采样”，不把有限清单缺项扩大为整个工程从未计算、所有版本无结果或该几何无解。原句在主矩阵语境下方向无误，修订是收紧证据范围，并非发现其必然为假。未核当初未采样原因，不虚构资源不足/计算失败等解释。
5. “覆盖”解释框可删除：用“离散几何组合未完整”和表标题“网格间距5nm”分别交代参数采样与空间离散。不能由18/20组合推导连续域覆盖率、容差范围或精度保证；也不能用h/d最小最大值代替实际采样列表。
6. 四旧几何八加密记录不增加几何数，参考敏感性另列；h100/d100两方向是1种新增几何的固定公式补充对照，不并入旧36统计。h75构建B复算不增加比较几何。总19几何46记录仍由§2.1数据角色表说明，不用在表1重复总数。旧S1清单52项及旧边界审计46的范围不改。
7. 当前补充表S6有六条（h100新两条、h75构建新两条、历史h75两条）；不能把“六条记录”全部当新增几何。当前源码/目录标签A_blind不赋予严格盲测身份。表下注仅指向S6，完整来源/身份界限继续由正文和补充承接。

## 中文候选

表1列出原公式与V2主统计所用的18种几何及36个5 nm主方向导度结果。相对于四档间隙与五档槽深构成的离散组合，本主比较矩阵未采样(h,d)=(25,75) nm与(25,120) nm，因而不是完整组合。

**表1 主比较集合的采样几何与导度结果数（网格间距5 nm）**

| 残余间隙h（nm） | 主比较采用的槽深d（nm） | 几何数 | 主方向导度结果数 |
|---|---|---:|---:|
| 25 | 25, 50, 100 | 3 | 6 |
| 50 | 25, 50, 75, 100, 120 | 5 | 10 |
| 75 | 25, 50, 75, 100, 120 | 5 | 10 |
| 125 | 25, 50, 75, 100, 120 | 5 | 10 |
| **合计** | — | **18** | **36** |

注：每种几何分别计算沿槽Kyy与横槽Kxx。其中4种几何的8条2.5 nm加密结果另用于参考敏感性检查；h=100 nm、d=100 nm新增几何的两条5 nm结果单列为固定公式补充对照，均不并入本表对应的36结果主统计。新增间隙与构建对照记录见补充表S6。

## 英文对应候选

Table 1 lists the 18 geometries and 36 principal-direction conductance results on the 5 nm grid used for the main original-formula and V2 statistics. Of the discrete combinations formed by four gap levels and five groove-depth levels, (h,d)=(25,75) nm and (25,120) nm are not sampled in this main matrix; the combinations are therefore incomplete.

**Table 1. Sampled geometries and conductance-result counts in the main comparison set (grid spacing 5 nm).**

| Residual gap h (nm) | Groove depths d used in the main comparison (nm) | Geometries | Principal-direction conductance results |
|---|---|---:|---:|
| 25 | 25, 50, 100 | 3 | 6 |
| 50 | 25, 50, 75, 100, 120 | 5 | 10 |
| 75 | 25, 50, 75, 100, 120 | 5 | 10 |
| 125 | 25, 50, 75, 100, 120 | 5 | 10 |
| **Total** | — | **18** | **36** |

Note: Each geometry has one along-groove result Kyy and one across-groove result Kxx. Eight refined results on a 2.5 nm grid for four of these geometries separately characterize reference sensitivity. Two results on a 5 nm grid for the additional geometry h=100 nm, d=100 nm provide a fixed-form supplementary comparison. Neither supplementary set is pooled into the original 36-result main statistics. Added-gap and build-comparison records are listed in Supplementary Table S6.

## 实际核查范围

读取当前中英文表1及前后采样/数据角色说明、补充S1与S6及原文表；直接从recomputed_44_records.csv按dx5重组h/d/方向并逐行核两稿表1，交叉补充Table_S1_run_inventory.csv的main组ID；从Table_S6_added_gap_build_comparison.csv识别h100与构建复现，重计总集合19/46。原尝试的S6文件名new_gap不存在，按补充正文链接读取实际added_gap文件，未据此报证据缺失。仅已知清单检查，不进行项目全盘结果扫描、不打开保留流动结果、不核缺项历史原因或重新验收求解器。

来源哈希见source_manifest.json，逐h计数与范围见matrix_recount.json，正式稿保持与状态范围见verification.json。使用已读scientific-writing和academic-humanizer流程；程序性来源沿用§1.2第一段审读报告所列Kassis等Scientific Agent Skills（2026，arXiv:2609.00065），不另加正文科学引文。本轮无新增文献检索。

## 停点

只新增本目录和更新两共享状态，正式中英文表1、主稿其他内容、补充表和原数据/系数/阈值未改；前轮摘要合入保持，引言与§2.1候选尚未合入。无新编译/求解/拟合/场处理/原轨迹接受/run_id/Gate/上传；S4原FAIL、reference_qualified=false、strict_error_bound_established=false、submission_ready=false保持，无新运行或长算授权。

下一具体动作：审§2.1求解器设置、体力项与壁面处理的文字和引用边界；若用户要求采用候选，再同步正式中英文表1及前后文，保持18/36主分母不变。

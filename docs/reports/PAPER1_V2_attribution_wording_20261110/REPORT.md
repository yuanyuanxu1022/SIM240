# V2 归属措辞由"建立"收窄为"标定"（2026-11-10 16:50）

> 性质：**文字定点修改**。依据是作者本人当日完成的来源核查（`docs/reports/PAPER1_V2_downloads_source_audit_20261110/REPORT.md`）。
> 零数字改动：V2 四参数、全部结果数值、单位、图表与式编号、参考文献编号、既有 FAIL 均未动。
> 未重新拟合、未运行仿真、未改 Gate／`submission_ready=false`。

## 1 为什么改

前一轮（16:19—16:21）已把 V2 从"既定/公布"改为"本研究建立并标定"。本轮来源核查给出的结论使其中"建立"二字超出证据：

| 事项 | 证据状态 |
|---|---|
| V2 四个系数由本项目标定 | **有记录支持**：9 种几何（h=50/75/125 × d=25/50/100 nm、w=120 nm），每方向 9 个 5 nm 导度结果，对两参数作 minimax 拟合 |
| 函数形式的直接前身 | **未确认**：下载目录 34 个 PDF（去重 30 份）内未找到 V2 关系或其四系数；Dewangan–Datta 2020 §4.3 的 Padé 分母型改写只是表达思路前例，相似不足以认定借用 |
| 被比较原模型的文献基础 | **有**：Jain et al. 2017 式(11)—(13) 给出条纹模板平均高度与两方向有效渗透率；Patir–Cheng 1978 式(23)(24) 给出横/纵向条纹的调和/算术流量因子 |

**关键逻辑**：用自己的数据重拟合，同样可以产生"取自已有函数形式的新系数"。所以"四系数来自自有数据"**推不出**"函数形式原创"。原表述在这一点上过强。

## 2 改了什么（共 11 处，全部为归属措辞 ＋ 1 处补引）

| # | 位置 | 改前 | 改后 |
|---|---|---|---|
| 1 | 中文摘要 | 本研究**建立并标定**的经验修正（V2）的回顾性评价 | 本研究**标定**的经验修正（V2）在回顾性评价中 |
| 2 | 中文 §1.3 | 本研究**建立并标定**一个以 d/w 为因子自变量的…V2 | 本研究**采用**…V2，并用 9 种标定几何**标定**其四个系数 |
| 3 | 中文 §2.3 | 只引 Patir–Cheng [4] | 增补"这一组合在纳米压印降阶模型中已有使用 **[1]**，其中条纹模板的平均高度与两方向有效渗透率以同一算术／调和组合给出" |
| 4 | 中文 §4.4 首句 | 本文所用 V2 关系**由本研究……建立并标定** | 本文所用 V2 关系的**四个系数由本研究标定**，标定集为 9 种几何 |
| 5 | 中文 §4.4 次句 | V2 **是本研究建立并标定**的经验关系 | V2 **形式与四个系数在本研究中保持固定** |
| 6 | 英文摘要 | correction **developed and calibrated** in this study | correction **calibrated here on nine geometries** |
| 7 | 英文 §1.3 | correction **developed** in this study | correction **calibrated** in this study |
| 8 | 英文 §2.3 | 只引 [4] | 增补 "already used in reduced-order nanoimprint models **[1]**" |
| 9 | 英文 §4.4 首句 | was **developed and calibrated** in this study using nine geometries | **four coefficients** … **were calibrated** in this study on nine geometries |
| 10 | 英文 §4.4 次句 | was **developed and calibrated** in this study | **form and the four coefficients** … **are held fixed** |
| 11 | 英文结论 1 | V2 **developed** in this study | V2 **calibrated** in this study |

### 为什么补引 [1] 而不是只补一句免责

中文 §2.3 推式(3) 时原本只引 [4]（Patir–Cheng 关于 Reynolds 单胞关系）。但式(3) 的算术/调和组合与 Jain 2017 式(11)—(13) 构造相同，而 [1] 已在文献表、§1.2 已引用。补上它是**零成本**的：既准确交代原模型的 NIL 文献背景，也避免"把已有构造写成自己推的"这一类质疑。文献编号不变（[1] 复用）。

## 3 保留不动（必须核对的部分）

- 9 种标定几何、每方向 9 个 5 nm 结果、两参数×两方向＝**四参数**、minimax 目标函数
- "标定集包含于 18 种几何、36 条主方向结果的主比较集中"
- "扩展数据在形式选择时已可见，因此本节评价属于**回顾性比较，不构成独立预测精度证明**"
- "这些性质不能替代系数、指数或仅选 d/w 作为因子变量的精度证据"
- V2 四参数数值 1.7685／1.6331／0.4900／0.6990；全部偏差与导度数值；单位；图 1—4、表 1—8、式 (1)—(8)／(E1)—(E8)；文献 [1]—[14]
- **两补充材料与结论定稿本次未改**：其现有措辞为"固定 V2／固定系数"，本就不含"建立"断言（核对：`SUPPLEMENTARY_METHODS.md` L117、`PAPER1_conclusions_current_20261109.md` L58）

## 4 指纹

| 文件 | 改前 | 改后 |
|---|---|---|
| `SIM240_中文稿_导师审阅版_20261022.md` | `7035a548…`／75826 | **`c065a96afb0195bc`／76008** |
| `SIM240_First_Paper_English_20261028.md` | `9d0e8585…`／82728 | **`2a5c6d8ad119e92f`／82935** |
| `SIM240_submission_CN.md` | `c281d3a8…`／67899 | **`40b78c4f0c23b5b0`／68081** |
| `SIM240_submission_EN.md` | `cf2508c2…`／81515 | **`df6dd0444d3cb885`／81722** |
| `PAPER1_submission_package_20261109/MANIFEST.md` | `2eb85145…`／24183 | **`1f8d94117cda145c`／27233**（新增 §1.7） |

`build_submission.py --check`：两份派生件"一致"，0 禁词、0 断链。`output_hashes.json` **18 条 0 不一致**。逐项见 `after_hashes.json`。

> 注：本文件不写入自身哈希——写这句话本身会改变文件。

## 5 仍开放的项

**V2 函数形式的直接前身**。现有证据只能说：项目内记录支持四系数标定；下载目录内见分母型 Padé 改写前例（Dewangan–Datta 2020 §4.3），但相似不等于借用；无可指认的直接来源。若作者日后能指认具体篇名与段落，按"直接采用／改造／一般背景"三种身份分别处理引用，届时另记一节并重绑指纹。**不为了寻找原创性而重拟合，也不把相似表达自动加成 V2 出处。**

---

## 6 补正：英文 §1.3 的动词原形（2026-11-10 17:10）

**漏在哪**：第 1—3 节的检索词是 `developed and calibrated`、`developed in this study`、`建立并标定`、`establish`——全部为过去式/完成式。英文 §1.3 贡献句用的是**动词原形**：`...and develop and calibrate a two-direction multiplicative empirical correction, V2, whose factors depend on $d/w$.`（英文稿第 45 行），因此未被命中。它属于同一类"建立"断言，且与中文 §1.3 已改后的"采用…并用 9 种标定几何标定其四个系数"口径不一致。

**改成**：`...and calibrate a two-direction multiplicative empirical correction, V2, whose factors depend on $d/w$, on nine geometries.`——尾部补 `on nine geometries`，使 §1.3 与摘要、§4.4 的标定集表述自洽。

**影响范围**：一句话；零数字、零编号、零图表、零结论、零文献变动。中文稿、两补充材料、结论定稿本次均未动。

**指纹变动（本轮补正后为当前值）**

| 文件 | 16:50 时 | 现在 |
|---|---|---|
| 英文主稿 | `2a5c6d8ad119e92f`／82935 | **`2361c9d6c4ecf326`／82943**（+8 B） |
| 英文派生件 | `df6dd0444d3cb885`／81722 | **`8dc1f533cd9f7934`／81730** |
| 中文主稿 | `c065a96afb0195bc`／76008 | 不变 |
| 中文派生件 | `40b78c4f0c23b5b0`／68081 | 不变 |
| MANIFEST | `1f8d94117cda145c`／27233 | **`8924839395d3c84c`／28497**（新增 §1.7.1） |

`build_submission.py --check`：两份派生件"一致"、0 禁词、0 断链；`output_hashes.json` 18 条 0 不一致；authority 表第 1、2 行与派生件行、`SIM240_AI_CONTEXT.md`、`AI_HANDOFF_PORTABLE_20261104.md` 已同步。

**方法修正（写进流程）**：过度归属检索必须同时覆盖——动词原形 `develop`／`developing`、名词 `development`、`propose(d)`、中文"建立／提出／构造／推导出"。只搜过去式会漏。

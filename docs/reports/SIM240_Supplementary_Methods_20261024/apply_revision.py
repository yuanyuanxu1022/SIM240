#!/usr/bin/env python3
"""Apply the authorized three claim revisions and numbered supplement links."""
import csv
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
TARGET=ROOT/'docs/reports/SIM240_中文稿_导师审阅版_20261022.md'
INDEX=ROOT/'docs/reports/Methods_support_audit_20261022/SUPPORTING_MATERIALS_INDEX.md'
assert TARGET.read_bytes()==(HERE/'manuscript_before.md').read_bytes(), '正文已变化，须重新核对'
assert INDEX.read_bytes()==(HERE/'support_index_before.md').read_bytes(), '索引已变化，须重新核对'
body=TARGET.read_text()
base='SIM240_Supplementary_Methods_20261024/SUPPLEMENTARY_METHODS.md'
def ref(label,anchor):return f'[{label}]({base}#{anchor})'
def replace(old,new):
    global body
    assert body.count(old)==1,old
    body=body.replace(old,new)

replace('（其合理性见 §2.4 的线性检查）','（该幅值的基准几何检查见 §2.4）')
replace('所用 OpenLB 版本的提交标识、编译配置与二进制哈希随每次运行的清单文件一并保存，可据以复现。',
        '现存运行清单保存了二进制哈希，参数、结果与日志可按'+ref('补充材料表 S1','table-s1')+'定位；部分历史运行的源码、编译配置及 OpenLB 依赖版本绑定尚未完整核实，作为来源限制保留（见'+ref('补充材料 S10','sm-s10')+'）。')
replace('另有两个 $\\mu=15$ mPa·s 的黏度对照工况，物性与主地图分列。含加密、黏度与斜向驱动检查在内，现有正式运行共 52 次；**运行数不等于几何数**，完整批次与来源记录见支持资料。',
        '另有两个 $\\mu=15$ mPa·s 的黏度对照工况，物性与主地图分列。用于 D2/D3 主地图与附加检查的运行清单共 52 项，包括 36 个主方向样点、8 次加密、2 次黏度对照和 6 次斜向驱动（'+ref('补充材料 S1、表 S1','sm-s1')+'）；**运行数不等于几何数**。周期复制与多力检查、历史平板与三网格基准分别列于'+ref('补充材料 S8','sm-s8')+'和'+ref('S9','sm-s9')+'，不计入这 52 项。历史构建来源的核实范围见'+ref('S10','sm-s10')+'。')
replace('这确认在所用力范围内 $K$ 与驱动强度无关，符合牛顿液体的线性响应，也说明全文采用单一驱动幅值是合理的。',
        '这支持基准几何 $(h,d)=(75,100)$ nm、2.5 nm 网格在被检力范围内的线性响应；本文未对全部 36 个 5 nm 主地图样点逐一做多力检查，不据此声称已逐点验证其驱动力独立性。逐项数据见'+ref('补充材料 S8、表 S3','table-s3')+'。')
replace('### 2.2 输运系数怎么定',
        '本章支持资料按 S1—S11 编号；'+ref('补充材料总目录','sm-index')+'及附录 B 给出正文位置与数据表的对应关系。\n\n### 2.2 输运系数怎么定')
replace('最坏情形出现在 $(h,d)=(25,100)$ 的跨槽分量：',
        '表 2 对应的未取整数值与变化定义见'+ref('补充材料 S7、表 S2','table-s2')+'。\n\n最坏情形出现在 $(h,d)=(25,100)$ 的跨槽分量：')
replace('在间隙 75 nm 的平行平板中，数值系数应恢复 $K_0=h^3/12$。三套网格的结果见表 3。',
        '在间隙 75 nm 的平行平板中，数值系数应恢复 $K_0=h^3/12$。三套网格的结果见表 3；原始结果定位及历史横槽失败记录见'+ref('补充材料 S9、表 S4','table-s4')+'。')
replace('本稿全部数值可回溯到原始 `result.txt` 与四个汇总 CSV。逐项索引见 `docs/reports/第一篇_run_id索引_20261022.csv`（52 行，含 run_id、几何、方向、网格、路径、$K$、步数、PASS、$q_{\\min}$）。',
        'D2/D3 主地图与附加检查的逐运行数据见'+ref('补充材料表 S1','table-s1')+'（52 行）；原有 `docs/reports/第一篇_run_id索引_20261022.csv` 保留。下表将本地方法支持索引 S1—S11 对应到本稿采用的补充材料编号；四张补充数据表分别为表 S1—S4。')
rows=list(csv.DictReader((HERE/'SUPPLEMENT_NUMBER_MAP.csv').open()))
mapping='\n\n| 补充材料 | 内容 | 正文位置 | 数据表 |\n|---|---|---|---|\n'
for r in rows:
    mapping+=f"| {ref(r['supplement_section'],r['anchor'])} | {r['title']} | {r['main_location']} | {r['supplementary_table'] or '—'} |\n"
replace('已验证：52 个 run 均可定位，52/52 存在 `steady/result.txt`，52/52 记录 `PASS=true`。',
        '已核对：52 项均可定位原始 `steady/result.txt`，均记录 `PASS=true`；该记录不代替独立几何、网格或来源验收。'+mapping)
replace('新增 §2.4：三档驱动力（相差四倍）给出同一系数，最大相对偏差 $3.7\\times10^{-8}$',
        '新增 §2.4：基准几何 h75/d100、2.5 nm 网格下，三档驱动力（相差四倍）的系数最大相对偏差 $3.7\\times10^{-8}$；不代表全部主地图样点均做多力检查')
replace('OpenLB 版本与构建哈希指向随运行保存的清单。',
        '现存清单保存二进制哈希；历史源码、编译配置和 OpenLB 版本绑定的缺口按补充材料 S10 保留。')
body+='\n### D.5 方法承诺与补充材料编号（2026-10-24）\n\n按 `Methods_support_audit_20261022/REPORT.md` 的三处候选句，收紧历史构建可复现承诺、52 项运行的统计范围与基准几何线性检查的外推范围；同步本附录对应表述。补充材料 S1—S11 与原支持索引一一对应，表 S1—S4 分列 52 项 D2/D3 清单、8 行双网格比较、18 行周期/多力记录、9 行历史三网格记录。编号对照及本轮核对见 `SIM240_Supplementary_Methods_20261024/REVISION_NOTE.md` 与 `verification.json`。没有新仿真或来源缺口补造；本次编号不表示远端发布、投稿就绪或数值/物理验收升级。\n'
TARGET.write_text(body)

index=INDEX.read_text()
table='\n## 与配套补充材料的编号对应（2026-10-24）\n\n以下对应只固定编号和定位；本目录原报告及 JSON 核对记录保留为原审计快照，不追溯改写为本轮结果。正文已采用三处限定句，补充材料的作者审阅版本见下表。\n\n| 原索引 | 补充材料 | 内容 | 数据表 |\n|---|---|---|---|\n'
for r in rows:
    url='../'+base+'#'+r['anchor']
    table+=f"| {r['previous_index']} | [{r['supplement_section']}]({url}) | {r['title']} | {r['supplementary_table'] or '—'} |\n"
index=index.replace('## S1 几何来源、方向与采样组合（§2.1、表1）',table+'\n## S1 几何来源、方向与采样组合（§2.1、表1）',1)
index=index.replace('因此正文“每次运行均保存提交标识、编译配置并可据以复现”超出当前核实范围，需按REPORT候选句收紧。没有据此判定已存数值无效。',
                    '原审计发现正文“每次运行均保存提交标识、编译配置并可据以复现”超出核实范围；2026-10-24已按REPORT候选句收紧，并指向补充材料S10。历史来源缺口继续保留，没有据此判定已存数值无效。')
INDEX.write_text(index)
print('正文三处限定与S1—S11编号对应已写入。')

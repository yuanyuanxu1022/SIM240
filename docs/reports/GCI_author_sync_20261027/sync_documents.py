"""Apply the author's selected, previously reviewed wording; no solver calls."""
import csv
import difflib
import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
SUP = ROOT / 'docs/reports/SIM240_Supplementary_Methods_20261024'
REVIEW = ROOT / 'docs/reports/GCI_decision_review_20261027'
MAIN = ROOT / 'docs/reports/SIM240_中文稿_导师审阅版_20261022.md'
targets = [MAIN, SUP/'SUPPLEMENTARY_METHODS.md', SUP/'README.md', SUP/'SUPPLEMENT_NUMBER_MAP.csv']
before = OUT / 'before'
before.mkdir(exist_ok=True)
assert not (OUT/'applied.json').exists(), 'Already applied; do not overwrite original snapshots'
texts = {}
for path in targets:
    shutil.copy2(path, before/path.name)
    texts[path] = path.read_text()
for name in ['SIM240_AI_CONTEXT.md', 'AI_HANDOFF_20261015.md']:
    shutil.copy2(ROOT/'docs/reports'/name, before/name)

def replace_once(text, old, new):
    assert text.count(old)==1, (old, text.count(old))
    return text.replace(old,new,1)

protected = json.loads((REVIEW/'protected_inputs.json').read_text())
protected = {p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in protected if ROOT/p not in targets}
for path in list(REVIEW.iterdir()) + list(SUP.glob('Table_S[1-4]*.csv')):
    if path.is_file():
        protected[str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
(OUT/'protected_inputs.json').write_text(json.dumps(protected,indent=2,ensure_ascii=False)+'\n')

candidate = (REVIEW/'CANDIDATE_TEXT.md').read_text()
paragraphs = [line[2:] for line in candidate.splitlines() if line.startswith('> ')]
assert len(paragraphs)==3
main_new = paragraphs[0].replace('补充表[待编定表号]', '[补充材料 S9、表 S5](SIM240_Supplementary_Methods_20261024/SUPPLEMENTARY_METHODS.md#table-s5)').replace('方法参照[10]', '方法参照 [10]')
old = '两级网格不能确定观测阶，也不能给出整个参数范围的误差上界。基准几何另有一套归档的三网格 GCI 分析 [10]，但**不将其细网格估计套用于全部生产网格样点**。'
texts[MAIN] = replace_once(texts[MAIN],old,main_new)
texts[MAIN] = replace_once(texts[MAIN], '四张补充数据表分别为表 S1—S4。', '五张补充数据表分别为表 S1—S5；表 S5 补列历史基准的条件性 Richardson/GCI 估计。')
texts[MAIN] = replace_once(texts[MAIN], '| §3.2—3.4 | 表S4 |', '| §3.2—3.4 | 表S4、S5 |')

table_start = candidate.index('| 指标 |')
table_end = candidate.index('\n\n定义：',table_start)
table = candidate[table_start:table_end]
addition = r'''<a id="table-s5"></a>

**表 S5　历史基准的条件性 Richardson/GCI 估计（6项）**

完整数值表：[Table_S5_conditional_gci.csv](Table_S5_conditional_gci.csv)。原始三格值与原记录状态另见表 S4。细、中、粗网格分别为1.25、2.5、5 nm，$r_{21}=r_{32}=2$，$F_s=1.25$。平板间隙为75 nm；沟槽基准为$h=75$ nm、$d=100$ nm、周期240 nm、槽宽120 nm。沿用原协议的$\rho=1000$ kg/m³、$\mu=1$ mPa·s、$a=10^5$ m/s²与$\tau=1$；[原协议](/home/dell/yuanyuanxu/SIM240/CASE/03_grid_convergence/G2_EX240_grid_convergence/STEP3_PROTOCOL.md)保存完整几何及参数。K单位m³；eta方向为该方向K除以同网格平板K，anisotropy为沿槽K除以横槽K，两者无量纲。方法参照配套正文[10]，原文版本核实范围见S11。

TABLE

令$\phi_1$、$\phi_2$分别为细格和中格结果，采用统一符号定义外推值$\phi_{\mathrm{ext}}=\phi_1+(\phi_1-\phi_2)/(r^p-1)$，$e_a=|(\phi_1-\phi_2)/\phi_1|$，$e_{\mathrm{ext}}=|(\phi_{\mathrm{ext}}-\phi_1)/\phi_{\mathrm{ext}}|$，$GCI_{\mathrm{fine}}=F_s e_a/(r^p-1)$。表中误差与GCI列均以百分数报告；CSV保留原始三格值与完整精度。

**失败记录随表披露：** 历史1.25 nm横槽运行相对质量指标为$1.1967043900362632\times10^{-10}$，超过冻结阈值$10^{-10}$，独立退出码3。K_perpendicular、eta_perpendicular与anisotropy均依赖该失败点。可计算的GCI不赋予该记录合格参考资格，不改变历史G2 Step 3的FAIL/INCONCLUSIVE判定。所列估计不外推其他几何，也不构成全参数域严格误差界。

ASYMPTOTIC

SMOOTH

'''.replace('TABLE',table).replace('ASYMPTOTIC',paragraphs[1]).replace('SMOOTH',paragraphs[2])
sp = SUP/'SUPPLEMENTARY_METHODS.md'
texts[sp] = replace_once(texts[sp], '表S1—S4的编号', '表S1—S5的编号')
texts[sp] = replace_once(texts[sp], '编号版本：2026-10-24。', '编号版本：2026-10-24；2026-10-27按作者采用范围增补表S5及限定文字。')
texts[sp] = replace_once(texts[sp], '| §3.2—3.4 | 表S4 |', '| §3.2—3.4 | 表S4、S5 |')
texts[sp] = replace_once(texts[sp], '<a id="sm-s10"></a>', addition+'<a id="sm-s10"></a>')
rp = SUP/'README.md'
texts[rp] = replace_once(texts[rp], '- [表S4](Table_S4_grid_archive.csv)：9行历史三网格记录，保留失败状态。', '- [表S4](Table_S4_grid_archive.csv)：9行历史三网格记录，保留失败状态。\n- [表S5](Table_S5_conditional_gci.csv)：2026-10-27按作者采用范围增补的6项条件性Richardson/GCI估计；三项依赖历史细横槽失败点，限定说明见S9。')
texts[rp] += '\n2026-10-27的表S5/正文同步记录见[本次修订报告](../GCI_author_sync_20261027/REPORT.md)；既有verification.json是2026-10-24编号工作的历史记录，本次检查另存，不覆盖旧证书。\n'
mp = SUP/'SUPPLEMENT_NUMBER_MAP.csv'
texts[mp] = replace_once(texts[mp], '§3.2—3.4,表S4', '§3.2—3.4,表S4、S5')

assert all('\r' not in text and '\t' not in text for text in texts.values())
diffs = []
for path, text in texts.items():
    diffs.extend(difflib.unified_diff((before/path.name).read_text().splitlines(True),text.splitlines(True),fromfile='before/'+path.name,tofile=str(path.relative_to(ROOT))))
    path.write_text(text)
dst = SUP/'Table_S5_conditional_gci.csv'
assert not dst.exists()
shutil.copy2(REVIEW/'candidate_gci_table.csv',dst)
(OUT/'document_changes.diff').write_text(''.join(diffs))
(OUT/'applied.json').write_text(json.dumps(dict(modified=[str(p.relative_to(ROOT)) for p in targets],added=[str(dst.relative_to(ROOT))],solver_started=False,source_review='GCI_decision_review_20261027',theory_substantively_changed=False),indent=2,ensure_ascii=False)+'\n')
print('Applied 4 document/index changes and copied 6-row Table S5; snapshots and diff saved.')

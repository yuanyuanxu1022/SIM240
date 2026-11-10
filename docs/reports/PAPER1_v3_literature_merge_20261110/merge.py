"""Merge the authorized v3 paragraphs and renumber current scientific citations."""
from pathlib import Path
import difflib
import hashlib
import json
import re

OUT = Path(__file__).resolve().parent
REP = OUT.parent
ROOT = REP.parents[1]
SUP = REP / 'SIM240_Supplementary_Methods_20261024'
V3 = REP / 'PAPER1_MF_fulltext_audit_20261110'
CN = REP / 'SIM240_中文稿_导师审阅版_20261022.md'
EN = REP / 'SIM240_First_Paper_English_20261028.md'
SC = SUP / 'SUPPLEMENTARY_METHODS.md'
SE = SUP / 'SUPPLEMENTARY_METHODS_EN_20261028.md'
MAN = REP / 'PAPER1_submission_package_20261109/MANIFEST.md'
DOCS = [CN, EN, SC, SE]
MAPPING = {n: n if n <= 6 else n + 3 for n in range(1, 12)}
MAPPING.update({8:12, 9:11})  # Guo is first cited before Bouzidi in the actual methods paragraph.
PURE_CITE = re.compile(r'\[(\d+(?:\s*[,;–—-]\s*\d+)*)\]')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(name, data):
    (OUT / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')


def renumber(text, mapping):
    def transform(match):
        return '[' + re.sub(r'\d+', lambda n: str(mapping[int(n[0])]), match[1]) + ']'
    return PURE_CITE.sub(transform, text)


assert not (OUT / 'edits.json').exists(), 'Already merged; use snapshots and checks instead of reapplying.'
changes = DOCS + [MAN]
states = [REP / 'SIM240_AI_CONTEXT.md', REP / 'AI_HANDOFF_PORTABLE_20261104.md']
for path in changes + states:
    (OUT / (path.name + '.before')).write_bytes(path.read_bytes())
dump('baseline_hashes.json', {str(p.relative_to(ROOT)): sha(p) for p in changes + states})
protected = [V3 / n for n in ['CANDIDATE_CN_v3.md', 'CANDIDATE_EN_v3.md', 'REPORT.md',
    'SOURCE_NOTES.md', 'verification.json', 'arithmetic.json']]
protected += [REP / 'PAPER1_conclusions_current_20261109.md', REP / 'PPT_论文汇报_20261109/论文汇报.pptx',
    REP / 'SIM240_manuscript_revision_20261018/map36_evidence.csv',
    REP / 'PAPER1_闭环方案_20261105/bound_check_44_points.csv', SUP / 'SUPPLEMENT_NUMBER_MAP.csv']
protected += sorted(SUP.glob('Table_S*.csv'))
old = REP / 'PAPER1_nearest_work_comparison_20261109'
protected += [old / 'sources/round2/Ng2017_accepted.pdf', old / 'sources/round2/Mohammadi2013_jfm.pdf',
    old / 'sources/round2/Mohammadi2013_jfm.txt', old / 'source_manifest.json']
protected += [old / 'sources' / n for n in ['Ng2017_crossref.json', 'Mohammadi2013_crossref.json', 'Stroock2002_crossref.json']]
dump('protected_inputs.json', {str(p.relative_to(ROOT)): sha(p) for p in protected})
previous = json.loads((V3 / 'artifact_manifest.json').read_text())
for name in ['CANDIDATE_CN_v3.md', 'CANDIDATE_EN_v3.md']:
    assert sha(V3 / name) == previous[name], 'Reviewed v3 changed: ' + name

edits = []
def replace(path, before, after, label):
    current = path.read_text()
    assert current.count(before) == 1, label
    edits.append(dict(kind='literal', path=str(path.relative_to(ROOT)), label=label, old=before, new=after))
    path.write_text(current.replace(before, after, 1))


# Transform only bracketed numerical citations. Mathematical [2\ell_i(...)] is excluded.
for path in DOCS:
    current = path.read_text()
    edits.append(dict(kind='renumber', path=str(path.relative_to(ROOT)),
        label='Old reference identity mapping', mapping=MAPPING))
    path.write_text(renumber(current, MAPPING))

candidate_cn = (V3 / 'CANDIDATE_CN_v3.md').read_text()
candidate_en = (V3 / 'CANDIDATE_EN_v3.md').read_text()
def extract(text, heading):
    return text.split(heading, 1)[1].split('\n## ', 1)[0].strip()

cn_intro = extract(candidate_cn, '## §1.2候选：现有第二段后插入')
en_intro = extract(candidate_en, '## Section 1.2: insert after the existing second paragraph')
cn_height = extract(candidate_cn, '## §2.2候选：现有H_ref与κ关系后的定义澄清')
en_height = extract(candidate_en, '## Section 2.2: clarify the existing H_ref and κ relation')
for key, number in [('Ng', 7), ('MF', 8), ('St', 9)]:
    cn_intro = cn_intro.replace('[' + key + ']', '[' + str(number) + ']')
    en_intro = en_intro.replace('[' + key + ']', '[' + str(number) + ']')
    cn_height = cn_height.replace('[' + key + ']', '[' + str(number) + ']')
    en_height = en_height.replace('[' + key + ']', '[' + str(number) + ']')

replace(CN, '已有工作在所解问题和系数定义上与本文各有区别。', cn_intro + '\n\n已有工作在所解问题和系数定义上与本文各有区别。', 'CN §1.2 reviewed v3')
replace(EN, 'The compared problems and coefficient definitions differ.', en_intro + '\n\nThe compared problems and coefficient definitions differ.', 'EN §1.2 reviewed v3')
replace(CN, '### 2.3 局部立方律与偏差定义', cn_height + '\n\n### 2.3 局部立方律与偏差定义', 'CN §2.2 geometric reference height')
replace(EN, '### 2.3 Local cubic law and discrepancy definitions', en_height + '\n\n### 2.3 Local cubic law and discrepancy definitions', 'EN §2.2 geometric reference height')
dump('adopted_blocks.json', dict(CN_intro=cn_intro, EN_intro=en_intro, CN_height=cn_height, EN_height=en_height))

new_references = {
 7: '[7] Ng C.-O. Effective slip for Stokes flow between two grooved walls with an arbitrary phase shift. *Fluid Dyn. Res.*, 2017, **49**(2): 025516. DOI: 10.1088/1873-7005/aa5b58',
 8: '[8] Mohammadi A., Floryan J.M. Pressure losses in grooved channels. *J. Fluid Mech.*, 2013, **725**: 23–54. DOI: 10.1017/jfm.2013.184',
 9: '[9] Stroock A.D., Dertinger S.K., Whitesides G.M., Ajdari A. Patterning Flows Using Grooved Surfaces. *Anal. Chem.*, 2002, **74**(20): 5306–5312. DOI: 10.1021/ac0257389',
}
for path in [CN, EN]:
    text = path.read_text()
    matches = list(re.finditer(r'^\[(\d+)\] .+$', text, re.M))
    assert len(matches) == 11
    entries = {int(m[1]): m[0] for m in matches}
    entries.update(new_references)
    old_block = text[matches[0].start():matches[-1].end()]
    new_block = '\n\n'.join(entries[n] for n in range(1, 15))
    replace(path, old_block, new_block, path.name + ' bibliography first-appearance order')
replace(CN, '编号已按本稿出现顺序重排。原 22 条完整书目与核验记录见英文稿及支持资料。',
    '编号按本文首次出现顺序排列；各来源的核读范围与限制见补充材料S11。', 'CN bibliography numbering note')
replace(EN, '## References\n', '## References\n\nReferences are numbered in order of first appearance; source-reading scopes and limits are recorded in Supplementary S11.\n', 'EN bibliography numbering note')

cn_sources = '''- **[7] Ng 2017**：题名为 *Effective slip for Stokes flow between two grooved walls with an arbitrary phase shift*，Fluid Dynamics Research 49(2)，025516，DOI 10.1088/1873-7005/aa5b58。已读取[机构接收稿](../PAPER1_nearest_work_comparison_20261109/sources/round2/Ng2017_accepted.pdf)的§2、§2.1式（18）—（21）、§2.2式（41）—（44）及相关结果：两壁均为矩形槽、壁面无滑移、压力驱动；其对称中面不是本文无滑移平板，沿槽等效滑移明确排除槽腔流量。用于§1.2的相邻问题与定义比较，不作为一平一槽的逐点数值参考；接收稿与最终发表版尚未逐页对应。
- **[8] Mohammadi–Floryan 2013**：已取得32页正式全文，印刷pp23—54，DOI 10.1017/jfm.2013.184；读取层级已由早期摘要升级为[本地发表版](../PAPER1_nearest_work_comparison_20261109/sources/round2/Mohammadi2013_jfm.pdf)的定向全文核查。式（2.1）、（4.5）及图4—5支持一般壁形框架、平壁设置与矩形槽几何降阶对照；§4.4.2的 $EC_h$ 为按摩擦因子匹配的水力开度，不是本文几何平均高度。2026-11-10复核印刷p34图6(b)，存在 $S=0.08$，不能把 $S=0.06$ 当作方法适用上限；高波数下 $EC_h$ 接近 $2-S/2$ 未获原文充分计算确认，不能借作已证极限。本文未重算其算例，未建立与本稿几何、低惯性条件和通量定义匹配的精度排名，亦不以该文证明本稿的同一个机制。原文定位与纠错边界见[本次全文审查](../PAPER1_MF_fulltext_audit_20261110/SOURCE_NOTES.md)。
- **[9] Stroock等2002**：*Patterning Flows Using Grooved Surfaces*，Analytical Chemistry 74(20)，5306—5312，DOI 10.1021/ac0257389。[作者站7页发表版](https://www.gmwgroup.harvard.edu/sites/g/files/omnuum10006/files/gmwgroup/files/822.pdf)可通过PDF阅读器读取；2026-11-10定向复读印刷p5307的一平壁、一小幅正弦壁、无滑移压力驱动设置及通量说明。普通下载失败与文献是否已读分开记录；不因下载状态把实际页级读取降为摘要。该文支持各向异性有效边界与横向流的已有认识，不作为任意深矩形台阶的同条件精度基准。
'''
en_sources = '''- **[7] Ng 2017:** *Effective slip for Stokes flow between two grooved walls with an arbitrary phase shift*, Fluid Dynamics Research 49(2), 025516, DOI 10.1088/1873-7005/aa5b58. The [institutional accepted manuscript](../PAPER1_nearest_work_comparison_20261109/sources/round2/Ng2017_accepted.pdf) was read at Section 2, Eqs. (18)–(21) in Section 2.1, Eqs. (41)–(44) in Section 2.2 and related results. Both walls have rectangular grooves with no slip under pressure forcing. Its symmetric mid-plane is not the present no-slip plate, and longitudinal effective slip explicitly excludes cavity flux. Section 1.2 uses it for neighboring-problem and definition comparisons, not a matched flat-wall/grooved-wall numerical reference. The accepted and published versions have not been matched page by page.
- **[8] Mohammadi–Floryan 2013:** the 32-page published paper, printed pages 23–54, DOI 10.1017/jfm.2013.184, is available. Reading has advanced beyond the earlier abstract to targeted assessment of the [local published full text](../PAPER1_nearest_work_comparison_20261109/sources/round2/Mohammadi2013_jfm.pdf). Eqs. (2.1) and (4.5) and Figures 4–5 support the general wall-shape framework, a planar wall and rectangular-groove geometry-reduction tests. Section 4.4.2 defines $EC_h$ by matching friction factor, rather than the present geometric mean height. On 2026-11-10, Figure 6(b), printed page 34, was checked and contains $S=0.08$; $S=0.06$ is therefore not a method-applicability ceiling. The apparent high-wavenumber approach of $EC_h$ to $2-S/2$ was not computationally confirmed in the source and is not an established limit adopted here. Its examples have not been recomputed, a matched accuracy ranking at the present geometry, low-inertia conditions and flux definition has not been established, and it does not prove identity with our mechanism interpretation. See the [full-text audit locators and limits](../PAPER1_MF_fulltext_audit_20261110/SOURCE_NOTES.md).
- **[9] Stroock et al. 2002:** *Patterning Flows Using Grooved Surfaces*, Analytical Chemistry 74(20), 5306–5312, DOI 10.1021/ac0257389. The [author-hosted seven-page published PDF](https://www.gmwgroup.harvard.edu/sites/g/files/omnuum10006/files/gmwgroup/files/822.pdf) is accessible through the PDF reader. Printed page 5307 was reread on 2026-11-10 for the flat-wall/small-amplitude sinusoidal-wall, no-slip pressure-driven configuration and flux definition. Download failures are recorded separately from actual source reading; page-level evidence is not downgraded to an abstract solely because a download failed. The paper supports prior anisotropic-boundary and transverse-flow results, not a matched accuracy reference for arbitrarily deep rectangular steps.
'''
replace(SC, '- **[10] OpenLB**', cn_sources + '- **[10] OpenLB**', 'CN S11 new primary-source scopes')
replace(SE, '- **[10] OpenLB:**', en_sources + '- **[10] OpenLB:**', 'EN S11 new primary-source scopes')
for path in [SC, SE]:
    lines = path.read_text().splitlines()
    bouzidi = next(line for line in lines if line.startswith('- **[12] Bouzidi'))
    guo = next(line for line in lines if line.startswith('- **[11] Guo'))
    replace(path, bouzidi + '\n' + guo, guo + '\n' + bouzidi,
        path.name + ' S11 source entries follow actual reference order')
replace(SC, '2026-10-28更新[6]；其余条目沿用各自核对日期，文献编号沿用配套正文。',
    '2026-11-10新增[7]—[9]的相关工作核读范围，并与配套正文统一引文编号；[6]的2026-10-28更新及其余条目的各自核对日期保留。', 'CN S11 dates and numbering')
replace(SE, 'Reference [6] was updated on 2026-10-28; other entries retain their individual check dates. Numbers follow the companion manuscript.',
    'Reading scopes for related works [7]–[9] were added on 2026-11-10, with citation numbers aligned to the companion manuscript. The 2026-10-28 update of reference [6] and the individual check dates of other entries are retained.', 'EN S11 dates and numbering')

# Rebind the four actual deliverables, leaving historical receipts and source identities intact.
for path in DOCS:
    rel = str(path.relative_to(ROOT))
    line = next(s for s in MAN.read_text().splitlines() if f'`{rel}`' in s and re.match(r'^\| [1-4] \|', s))
    cells = line.split('|'); cells[4] = ' **2026-11-10** '; cells[5] = f' `{sha(path)[:16]}` '; cells[6] = f' {path.stat().st_size} '
    replace(MAN, line, '|'.join(cells), 'MANIFEST rebind ' + path.name)
replace(MAN, '**清单生成时间：2026-11-09**', '**清单当前绑定更新：2026-11-10**', 'MANIFEST binding date')
replace(MAN, '内容已改到 2026-11-09', '内容已改到 2026-11-10', 'MANIFEST example date')
replace(MAN, '**⚠ 三处日期全部滞后于内容**：1、2、3、4 号文件的文件名日期均早于内容版本。投稿打包时一律以本表第 5 列（内容版本）为准。',
    '**四个正文/补充文件的文件名日期均早于内容版本**：打包时以“内容版本”及SHA256绑定为准。', 'MANIFEST date-column explanation')
new_note = '''## 1.2 纠错v3相关工作与引文编号合入（2026-11-10）

已按 `PAPER1_MF_fulltext_audit_20261110/CANDIDATE_*_v3.md` 同步两正文§1.2、§2.2及两补充S11。新增Ng[7]、Mohammadi–Floryan[8]、Stroock[9]；按实际首次出现顺序，原OpenLB[7]→[10]、Guo[9]→[11]、Bouzidi[8]→[12]、Celik[10]→[13]、Teyssèdre[11]→[14]。全文与补充回指按同一文献身份更新，未另增Tran。原上下界推导、公式/图表编号、摘要、五条正文结论及既有数字保持，结论中原科学引文如有仅随身份改号。没有重复理论复核或新增仿真。

第1—4行SHA及字节数已按本轮实际文件重绑定。当前完整SHA、改前快照、全局引用映射和检查回执见 `docs/reports/PAPER1_v3_literature_merge_20261110/REPORT.md`、`output_hashes.json`、`verification.json`。旧合稿/复核记录保留各自历史快照身份，不作为当前文件哈希；当前投稿资格与既有FAIL不因本轮文字工作改变。

---

'''
replace(MAN, '## 2 数据证据件', new_note + '## 2 数据证据件', 'MANIFEST v3 integration scope')
replace(MAN, '**五个主交付件的哈希在本目录生成后全部未变**，可作为"未动正文"的证据。',
    '**在该派生目录生成当轮，五个主交付件的哈希均未变**；后续正文与补充修订以本清单第1节当前绑定为准。', 'MANIFEST historical derived-file receipt scope')
replace(MAN, '输出前 16 位应与本表第 2 节逐行一致', '输出前 16 位应与本表第 1 节主交付件逐行一致', 'MANIFEST verification table pointer')

dump('edits.json', edits)
dump('citation_map.json', dict(old_to_new=MAPPING, added={'Ng2017':7,'MohammadiFloryan2013':8,'Stroock2002':9},
    applied_to=[str(p.relative_to(ROOT)) for p in DOCS], historical_reports_renumbered=False, Tran_added=False))
dump('output_hashes.json', {str(p.relative_to(ROOT)):sha(p) for p in changes})
for path in changes:
    before = (OUT / (path.name + '.before')).read_text()
    (OUT / (path.name + '.diff')).write_text(''.join(difflib.unified_diff(before.splitlines(True),path.read_text().splitlines(True),
        fromfile=path.name+'.before',tofile=str(path.relative_to(ROOT)))))
print('v3 merged into four documents; references 1-14 and MANIFEST rebound. Checks pending.')

"""Apply the author-authorized A-scope addition to current bilingual manuscripts."""
from pathlib import Path
import difflib
import hashlib
import json
import re

OUT = Path(__file__).resolve().parent
REP = OUT.parent
ROOT = REP.parents[1]
CN = REP / 'SIM240_中文稿_导师审阅版_20261022.md'
EN = REP / 'SIM240_First_Paper_English_20261028.md'
MAN = REP / 'PAPER1_submission_package_20261109/MANIFEST.md'
SUP = REP / 'SIM240_Supplementary_Methods_20261024'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


assert not (OUT / 'edits.json').exists(), 'Already applied; inspect saved edits instead of reapplying.'
changed = [CN, EN, MAN]
states = [REP / 'SIM240_AI_CONTEXT.md', REP / 'AI_HANDOFF_PORTABLE_20261104.md']
protected = [SUP / n for n in ['SUPPLEMENTARY_METHODS.md', 'SUPPLEMENTARY_METHODS_EN_20261028.md',
    'SUPPLEMENT_NUMBER_MAP.csv', 'Table_S9_mechanism_diagnostic.csv']]
protected += [REP / 'PAPER1_conclusions_current_20261109.md',
    REP / 'SIM240_manuscript_revision_20261018/map36_evidence.csv',
    REP / 'PAPER1_闭环方案_20261105/bound_check_44_points.csv',
    REP / 'PAPER1_contribution_bound_audit_20261109/LOWER_BOUND_REVIEW.md',
    REP / 'PAPER1_lower_baseline_comparison_20261109/summary.json',
    REP / 'PAPER1_interval_note_review_20261109/REVISED_NOTE.md',
    REP / 'PAPER1_interval_note_review_20261109/normalized_records.csv',
    REP / 'PAPER1_interval_note_review_20261109/verification.json',
    REP / 'PAPER1_interval_note_review_20261109/figure_manifest.json',
    REP / 'PAPER1_interval_note_review_20261109/interval_positions_corrected.png',
    REP / 'PAPER1_interval_note_review_20261109/interval_positions_corrected.pdf']
protected += sorted(SUP.glob('Table_S[1-8]_*.csv'))
for path in changed + states:
    (OUT / (path.name + '.before')).write_bytes(path.read_bytes())
dump('baseline_hashes.json', {str(p.relative_to(ROOT)): sha(p) for p in changed + states})
dump('protected_inputs.json', {str(p.relative_to(ROOT)): sha(p) for p in protected})

cn_add = r'''<a id="appendix-e-lower"></a>
### E.1 基础下界及其适用范围

在上述相同假设与归一化下，取试探场 $\boldsymbol\phi=f_h(z)\mathbf e_i$，其中 $f_h(z)=z(h-z)/2$（$0\le z\le h$），在 $z\ge h$ 取零。该场在 $z=h$ 连续为零，属于 $H^1$，满足全部固壁（包括台阶竖壁）的零迹及周期匹配；两个水平主方向均为弱无散度。内部界面的导数跳变不影响可容许性，试探场无需满足动量方程。

记 $a(\boldsymbol v,\boldsymbol w)=\int_\Omega\nabla\boldsymbol v:\nabla\boldsymbol w\,\mathrm dA$，$\ell_i(\boldsymbol v)=\int_\Omega v_i\,\mathrm dA$。由式（E1）的弱式和式（E2），

$$
P K_i-\bigl[2\ell_i(\boldsymbol\phi)-a(\boldsymbol\phi,\boldsymbol\phi)\bigr]
=a(\mathbf U-\boldsymbol\phi,\mathbf U-\boldsymbol\phi)\ge0.
\tag{E7}
$$

本试探场满足 $\ell_i(\boldsymbol\phi)=a(\boldsymbol\phi,\boldsymbol\phi)=Ph^3/12$；因此，结合式（E6），两个主方向的连续导度均满足

$$
L:=\frac{h^3}{12}\le K_i\le U_i:=K_i^{\rm mod},
\qquad i\in\{x,y\}.
\tag{E8}
$$

下界等于仅保留贯通 $h$ 层、对槽腔增加零速度约束所得的平板导度，不描述真实槽内速度。它不含槽宽，不能独立解释宽度依赖。对本文19种比较几何，上下界比 $U_i/L$ 的最大值沿槽为63、横槽约为1.984；区间较窄不等于点预测已达到某一精度。不同 $h$ 的有量纲下界不同，只有除以各自 $L$ 后左端才统一为1。

原36条5 nm主记录、新增间隙两条及8条加密记录共46条不同离散记录，均位于相应上下界内；这是与连续界限的相容性，不代替下界证明或数值精度验收。另仅对原18种几何的36条5 nm主结果，以离散导度为分母，下界平均低估沿槽58.2%、横槽23.8%，局部立方律平均高估分别为88.8%和30.6%；两方向各11/18个几何的下界更接近。这组基线比较包含参考网格影响，不认证下界的普适预测能力。

'''
en_add = r'''<a id="appendix-e-lower"></a>
### E.1 Elementary lower bound and its scope

Under the same assumptions and normalization, choose the trial field $\boldsymbol\phi=f_h(z)\mathbf e_i$, where $f_h(z)=z(h-z)/2$ for $0\le z\le h$ and is zero for $z\ge h$. The field is continuous and zero at $z=h$, belongs to $H^1$, has zero trace on all solid walls, including the vertical steps, and is periodic. It is weakly divergence free for either horizontal principal direction. The derivative jump at the internal interface does not prevent admissibility; a trial field need not satisfy the momentum equation.

Define $a(\boldsymbol v,\boldsymbol w)=\int_\Omega\nabla\boldsymbol v:\nabla\boldsymbol w\,\mathrm dA$ and $\ell_i(\boldsymbol v)=\int_\Omega v_i\,\mathrm dA$. The weak formulation of Eq. (E1), together with Eq. (E2), gives

$$
P K_i-\bigl[2\ell_i(\boldsymbol\phi)-a(\boldsymbol\phi,\boldsymbol\phi)\bigr]
=a(\mathbf U-\boldsymbol\phi,\mathbf U-\boldsymbol\phi)\ge0.
\tag{E7}
$$

For this trial field, $\ell_i(\boldsymbol\phi)=a(\boldsymbol\phi,\boldsymbol\phi)=Ph^3/12$. Combining this result with Eq. (E6), the continuous conductance in either principal direction satisfies

$$
L:=\frac{h^3}{12}\le K_i\le U_i:=K_i^{\rm mod},
\qquad i\in\{x,y\}.
\tag{E8}
$$

The lower bound equals the parallel-plate conductance obtained by retaining only the connected layer of thickness $h$ and imposing an additional zero-velocity constraint in the groove cavity; it does not describe the actual cavity velocity. It contains no groove-width dependence and cannot independently explain width effects. Among the 19 comparison geometries, the maximum upper-to-lower ratio $U_i/L$ is 63 along the grooves and approximately 1.984 across them. A narrower interval does not establish a specified point-prediction accuracy. Dimensional lower bounds differ with $h$; only normalization by each geometry's own $L$ gives a common left endpoint of 1.

The 36 main 5 nm records, two added-gap records and eight refinement records give 46 distinct discrete records, all within their respective bounds. This is compatibility with the continuous bounds, rather than a substitute for the lower-bound proof or numerical-accuracy assessment. Separately, for only the 36 main 5 nm results from 18 geometries, with discrete conductance as denominator, the lower bound underestimates by an average of 58.2% along and 23.8% across the grooves; the local cubic law overestimates by 88.8% and 30.6%, respectively. In each direction the lower bound is closer for 11/18 geometries. This baseline comparison includes reference-grid effects and does not establish general predictive ability of the lower bound.

'''
cn_disc = '在附录[E.1](#appendix-e-lower)的相同连续模型下，真实主导度满足式（E8）的上下界约束；该区间用于呈现理论范围和比较基线，不提供机制份额或通用点预测精度。\n\n'
en_disc = 'Under the same continuous model, the principal conductances lie within the bounds in Eq. (E8), as shown in [Appendix E.1](#appendix-e-lower); this interval supplies theoretical constraints and a comparison baseline, rather than mechanism fractions or general point-prediction accuracy.\n\n'

edits = []
def replace(path, old, new, label):
    current = path.read_text()
    assert current.count(old) == 1, label
    edits.append(dict(path=str(path.relative_to(ROOT)), label=label, old=old, new=new))
    path.write_text(current.replace(old, new, 1))

replace(CN, '### 5.2 对降阶挤压模型的含义\n', cn_disc + '### 5.2 对降阶挤压模型的含义\n', 'CN discussion cross-reference')
replace(EN, '### 5.2 Implications for reduced squeeze-flow models\n', en_disc + '### 5.2 Implications for reduced squeeze-flow models\n', 'EN discussion cross-reference')
cn = CN.read_text()
assert cn.endswith('\n') and '### E.1 ' not in cn
replace(CN, cn[-220:], cn[-220:].rstrip() + '\n\n' + cn_add.rstrip() + '\n', 'CN append lower-bound subsection')
replace(EN, '\n## References\n', '\n' + en_add + '## References\n', 'EN append lower-bound subsection')

# Only rebind modified deliverables in the existing publication manifest.
for path in [CN, EN]:
    rel = str(path.relative_to(ROOT))
    manifest = MAN.read_text()
    line = next(s for s in manifest.splitlines() if f'`{rel}`' in s and re.match(r'^\| [12] \|', s))
    cells = line.split('|')
    cells[5] = f' `{sha(path)[:16]}` '
    cells[6] = f' {path.stat().st_size} '
    replace(MAN, line, '|'.join(cells), 'MANIFEST rebind ' + path.name)
note = '''## 1.1 A范围基础下界定点合入（2026-11-09）

两份正文仅在附录E末尾增加E.1基础下界（新增式E7、E8），并在§5.1末加入一句回指。摘要、五条正文结论、原式E1—E6、科学参考文献及双语补充S1—S14保持；未增加正式图表号。修正版区间图作为独立追溯材料保留。第1、2行哈希与字节数已按本轮实际文件重绑定；完整SHA和合稿检查见 `docs/reports/PAPER1_lower_bound_merge_20261109/output_hashes.json`、`verification.json`。其他历史清单和旧审查哈希保留其快照身份，不据此声称当前文件未变。

本次合稿不改变数值参考资格、既有FAIL或投稿准备状态；不扩大机制或预测主张。独立六条结论文件未改，正文五条结论也未改；其既有组织差异不在本轮重排范围。

---

'''
replace(MAN, '## 2 数据证据件', note + '## 2 数据证据件', 'MANIFEST scope and full-hash receipt')
dump('edits.json', edits)
dump('output_hashes.json', {str(p.relative_to(ROOT)): sha(p) for p in changed})
for path in changed:
    before = (OUT / (path.name + '.before')).read_text()
    diff = ''.join(difflib.unified_diff(before.splitlines(True), path.read_text().splitlines(True),
        fromfile=path.name + '.before', tofile=str(path.relative_to(ROOT))))
    (OUT / (path.name + '.diff')).write_text(diff)
print('Merged A scope into two current manuscripts; manifest hashes rebound. Check pending.')

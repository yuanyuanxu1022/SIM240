#!/usr/bin/env python3
"""Apply only the recorded provenance wording changes; never fit or solve."""
from pathlib import Path
import difflib
import json

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
R = 'docs/reports/'
CN = R + 'SIM240_中文稿_导师审阅版_20261022.md'
EN = R + 'SIM240_First_Paper_English_20261028.md'
SC = R + 'SIM240_Supplementary_Methods_20261024/SUPPLEMENTARY_METHODS.md'
SE = R + 'SIM240_Supplementary_Methods_20261024/SUPPLEMENTARY_METHODS_EN_20261028.md'
CO = R + 'PAPER1_conclusions_current_20261109.md'

EDITS = {
    CN: [
        ('既定经验修正（V2）的回顾性评价', '本研究建立并标定的经验修正（V2）的回顾性评价'),
        ('及既定经验修正表现的配套评价', '及本研究所建经验修正表现的配套评价'),
        ('量化其对各向异性及张量重建流向的影响，并在同一离散参考下评价既定经验修正的改善与局限。',
         '量化其对各向异性及张量重建流向的影响。同时，本研究建立并标定一个以 $d/w$ 为因子自变量的双方向乘性经验修正V2，并在同一离散参考下回顾性评价其改善与局限。'),
        ('采用乘性因子 $F_i$ 修正式（3）。当前V2关系的公布舍入表达为',
         '本文所用V2关系由本研究以9种标定几何（$h=50,75,125$ nm与 $d=25,50,100$ nm的全部组合，$w=120$ nm）建立并标定。每个方向分别使用这9种几何的5 nm OpenLB导度结果，以最小化最大绝对相对残差为目标拟合两个参数，共四个参数。标定集包含于18种几何、36条主方向结果的主比较集中；扩展数据在形式选择时已可见，因此本节评价属于回顾性比较，不构成独立预测精度证明。采用乘性因子 $F_i$ 修正式（3），固定系数的舍入表达为'),
        ('式（6）的V2在本文中作为既定经验关系接受评价。', '式（6）的V2是本研究建立并标定的经验关系；本节保持其形式与系数不变进行评价。'),
        ('公布表达式保持正值', '该表达式保持正值'),
        ('按公布系数直接计算', '按固定系数直接计算'),
        ('为考察既定经验修正在新增间隙下的表现', '为考察本研究所建经验修正在新增间隙下的表现'),
        ('使用原先公布的 V2 系数', '使用原先固定的 V2 系数'),
        ('并评价既定经验修正V2的改善程度', '并评价本研究所建经验修正V2的改善程度'),
        ('使用公布V2系数回顾性比较', '使用固定V2系数回顾性比较'),
    ],
    EN: [
        ('Retrospective evaluation of the fixed empirical correction (V2)', 'Retrospective evaluation of the empirical correction developed and calibrated in this study (V2)'),
        ('and fixed-correction performance for this rectangular family', 'and the performance of the empirical correction developed in this study for this rectangular family'),
        ('and assess the fixed empirical correction at the same discrete references.', 'and develop and calibrate a two-direction multiplicative empirical correction, V2, whose factors depend on $d/w$. Its improvement and limitations are evaluated retrospectively against the same discrete references.'),
        ('We apply multiplicative factors $F_i$ to Eq. (3). The published rounded form of V2 is',
         'The V2 relation was developed and calibrated in this study using nine geometries: all combinations of $h=50,75,125$ nm and $d=25,50,100$ nm at $w=120$ nm. For each direction, two parameters were fitted to the 5 nm OpenLB conductances for these nine geometries by minimizing the maximum absolute relative residual, giving four parameters in total. The calibration set is contained in the main comparison set of 18 geometries and 36 principal-direction results. Extension data were already visible during model-form selection, so the evaluation in this section is retrospective and does not establish independent predictive accuracy. We apply multiplicative factors $F_i$ to Eq. (3); the rounded expression with fixed coefficients is'),
        ('The V2 relation of Eq. (6) is evaluated here as a fixed empirical relation.', 'The V2 relation of Eq. (6) was developed and calibrated in this study; its form and coefficients are held fixed for the present evaluation.'),
        ('Evaluation using the published coefficients', 'Evaluation using the fixed coefficients'),
        ('previously published V2 coefficients', 'previously fixed V2 coefficients'),
        ('the improvement achieved by the fixed empirical correction V2', 'the improvement achieved by the empirical correction V2 developed in this study'),
        ('using the published V2 coefficients', 'using the fixed V2 coefficients'),
    ],
    SC: [('固定公布系数', '固定系数')],
    SE: [('Fixed published coefficients', 'Fixed coefficients')],
    CO: [
        ('并评价既定经验修正 V2 的改善程度', '并评价本研究建立并标定的经验修正 V2 的改善程度'),
        ('使用**公布系数**回顾性比较', '使用**固定系数**回顾性比较'),
        ('使用**原先公布**的 V2 系数', '使用**原先固定**的 V2 系数'),
    ],
}

def main():
    planned = {}
    log = []
    # Check every input before writing any manuscript.
    for name, edits in EDITS.items():
        p = ROOT / name
        before = (HERE / 'before' / name).read_text()
        assert p.read_text() == before, f'Concurrent change: {name}'
        after = before
        for old, new in edits:
            assert after.count(old) == 1, (name, old, after.count(old))
            after = after.replace(old, new)
            log.append({'path': name, 'before': old, 'after': new})
        planned[name] = (before, after)
    for name, (before, after) in planned.items():
        (ROOT / name).write_text(after)
        (HERE / (Path(name).name + '.diff')).write_text(''.join(
            difflib.unified_diff(before.splitlines(True), after.splitlines(True),
                                 fromfile='before/' + name, tofile=name)))
    (HERE / 'edits.json').write_text(json.dumps(log, ensure_ascii=False, indent=2) + '\n')
    print(f'Applied {len(log)} exact replacements across {len(planned)} authoritative files.')

if __name__ == '__main__':
    main()

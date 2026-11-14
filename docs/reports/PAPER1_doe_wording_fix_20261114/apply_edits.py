#!/usr/bin/env python3
"""One-shot, exact-match manuscript prose edits. No solver or CASE writes."""
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
R = 'docs/reports/'
CN = R + 'SIM240_中文稿_导师审阅版_20261022.md'
EN = R + 'SIM240_First_Paper_English_20261028.md'
SC = R + 'SIM240_Supplementary_Methods_20261024/SUPPLEMENTARY_METHODS.md'
SE = R + 'SIM240_Supplementary_Methods_20261024/SUPPLEMENTARY_METHODS_EN_20261028.md'
CO = R + 'PAPER1_conclusions_current_20261109.md'
paths = [CN, EN, SC, SE, CO]
original = {p: (ROOT / p).read_text() for p in paths}
texts = dict(original)
edits = []


def change(path, before, after, reason):
    assert texts[path].count(before) == 1, (reason, before[:90])
    texts[path] = texts[path].replace(before, after, 1)
    edits.append({'path': path, 'reason': reason, 'before': before, 'after': after})


def line(path, prefix, after, reason):
    matches = [s for s in texts[path].splitlines() if s.startswith(prefix)]
    assert len(matches) == 1, (prefix, len(matches))
    change(path, matches[0], after, reason)


def main():
    before_manifest = json.loads((OUT / 'before_manifest.json').read_text())
    for p in paths:
        assert hashlib.sha256((ROOT / p).read_bytes()).hexdigest() == before_manifest[p]['sha256']
    for p in (CN, SC, CO):
        while '有限元体积法' in texts[p]:
            old = next(s for s in texts[p].splitlines() if '有限元体积法' in s)
            change(p, old, old.replace('有限元体积法', '有限体积法'), 'E4: correct FVM terminology')

    line(CN, '第一行与第三行的对照给出', '在所列等权矩阵中，**原公式有符号偏差的槽深主效应平方和份额在两个方向均最大**（93.40% 与 93.77%）；对于**固定 V2 的沿槽有符号偏差，间隙主效应份额最大**（88.98%）。原公式已经含有槽深和间隙，乘性修正不等于扣除了槽深依赖。该分解与仅依赖 $d/w$ 的乘性因子仍保留间隙相关残余的观察一致，但不能确定唯一的缺失变量、改进函数形式或物理原因。完整公式仍含 $h$；§4.4 对残差随间隙变化的观察，在这里得到本采样矩阵内的描述性量化。', 'W1: descriptive shares do not remove a physical dependency')
    line(EN, 'The first and third rows carry', 'Within the specified equally weighted matrix, **the depth main-effect sum-of-squares share is the largest for the signed local-cubic-law discrepancy in both directions** (93.40% and 93.77%). For **the fixed-V2 along-groove signed discrepancy, the gap main-effect share is the largest** (88.98%). The local-cubic law already contains depth and gap; a multiplicative correction does not remove depth dependence. This decomposition is consistent with gap-dependent residuals remaining under a $d/w$-only factor, but does not identify a unique missing variable, correction form or physical cause. The complete formula still contains $h$; the present matrix gives a descriptive quantification of the residual gap dependence discussed in Section 4.4.', 'W1: bilingual match')

    change(CN, '每个组合只有一个确定性结果，截距、两个主效应与完整交互已占满 15 个自由度，没有独立残差自由度。', '每个组合只有一个确定性结果，包含完整交互的两因素模型以 15 个单元均值参数表示，为饱和模型，没有独立残差自由度。', 'E3: saturated model parameters, not centered total degrees of freedom')
    change(EN, 'each combination has a single deterministic outcome, and intercept, two main effects and the full interaction already exhaust the 15 degrees of freedom, leaving no independent residual degrees of freedom.', 'each combination has a single deterministic outcome, and the complete two-factor interaction model has 15 cell-mean parameters. It is saturated, with no independent residual degrees of freedom.', 'E3: bilingual match')
    change(SC, '每个组合只有一个确定性结果，截距、两个主效应与完整交互已占满 15 个自由度，**没有独立残差自由度**。', '每个组合只有一个确定性结果，包含完整交互的两因素模型以 15 个单元均值参数表示，为饱和模型，**没有独立残差自由度**。', 'E3: supplement')
    change(SE, 'Each combination has a single deterministic outcome, and intercept, two main effects and the full interaction already exhaust the 15 degrees of freedom, so **no independent residual degrees of freedom remain**.', 'Each combination has a single deterministic outcome, and the complete two-factor interaction model has 15 cell-mean parameters. It is saturated, with **no independent residual degrees of freedom**.', 'E3: English supplement')

    line(CN, '**参考身份同 §4.5。**', '**参考身份同 §4.5。** 本节所含 12 条新增横槽有限元计算仍为**待正式采用的候选参考**；其余既有有限元结果保留经保存场复核后的有限采用建议及历史运行溯源限制。2 条合格有限体积法记录保留既有参考资格，不能因共同用于本节而一并降级或将有限元结果一并提升。各来源的身份区别见 §4.5。本节仅说明所列趋势在更换数值对照后仍保留，不据此排除全部离散影响，不构成对 V2 的独立验证或连续适用域保证；5 nm 比较基线的限定保持不变。', 'W2/W4: distinguish reference identities and bound robustness claim')
    line(EN, '**Reference status as in Section 4.5.**', '**Reference status as in Section 4.5.** The 12 new transverse finite-element runs remain **candidate references pending formal adoption**. The legacy finite-element results retain the recommendation for limited use after saved-field checks, together with their historical run-provenance limitations. The 2 qualified finite-volume records retain their existing reference qualification; their use in the same analysis neither downgrades them nor qualifies the finite-element results. These source-specific distinctions follow Section 4.5. The listed trends persist after changing the numerical comparison; this does not exclude all discretization effects, independently validate V2 or guarantee a continuous domain of accuracy. The limitations of the 5 nm comparison basis remain unchanged.', 'W2/W4: bilingual match')

    change(CN, '该非单调并非 5 nm 参考的产物：在 §4.6 的独立参考上，同一序列由 140.50% 上升至 156.30%。', '在 §4.6 所列替代数值对照下，同一序列仍由 140.50% 上升至 156.30%，说明这一非单调观察并非仅见于以 5 nm OpenLB 为基线的比较；该结果不单独确定其机制或连续解精度。', 'W4: persistence is not elimination of all numerical effects')
    change(EN, 'This non-monotonicity is not an artefact of the 5 nm reference: on the independent reference of Section 4.6 the same sequence rises from 140.50% to 156.30%.', 'Under the alternative numerical comparisons listed in Section 4.6, the same sequence still rises from 140.50% to 156.30%. This non-monotonicity is therefore not confined to comparisons using the 5 nm OpenLB basis, but does not by itself identify its mechanism or continuous-solution accuracy.', 'W4: bilingual match')

    line(SC, '单位 %，有符号。注意"总均值"', '单位 %，有符号。本节为完全平衡的等权矩阵：15 个格点的总均值，既等于各间隙档边际均值的算术平均，也等于各槽深档边际均值的算术平均。未取整时这两种平均与总均值相等；显示取整引起的末位差以未取整值为准。', 'E1: balanced means agree exactly before rounding')
    line(SE, 'Percent, signed. The grand mean is not', 'Percent, signed. On this fully balanced, equally weighted matrix, the grand mean of the 15 grid points equals both the arithmetic mean of the gap marginal means and the arithmetic mean of the depth marginal means before rounding. Where displayed rounding produces a last-digit difference, the unrounded values govern.', 'E1: bilingual match')
    change(SC, '因此上表的差异来自参考与几何集合的改变，不是算法或选点口径的改变。', '两轮总体记录集合不同，但本表份额比较使用相同的平衡矩阵、等权选点与算法。因此上表反映的是该固定子集更换数值对照后偏差响应的改变，不应归因于分析矩阵换点。', 'E2: same analysis subset, different reference')
    change(SE, 'The differences above therefore come from the change of reference and geometry set, not from a change of algorithm or sampling convention.', 'The full record sets differ, but the share comparison uses the same balanced subset, equal weighting and algorithm in both rounds. The differences above therefore reflect the changed discrepancy response when the numerical comparison is replaced, rather than a change of points in the analyzed matrix.', 'E2: bilingual match')

    change(SC, '$d=75$ 列达峰（+2.4128、+6.4755、+5.3491）；', '$d=75$ 列为 +2.4128、+6.4755、+5.3491；对间隙平均后的槽深边际均值在该采样档最大，不表示各固定间隙曲线均在此达峰；', 'E5: peak is marginal, not every individual curve')
    change(SE, 'the peak occurs at $d=75$ (+2.4128, +6.4755, +5.3491);', 'the $d=75$ column is +2.4128, +6.4755, +5.3491; the depth marginal mean, averaged over gaps, is largest at this sampled level, which does not imply that every fixed-gap curve peaks there;', 'E5: bilingual match')
    change(CN, '在 $d=75$ nm 达到峰值（+4.75%），其后回落。', '对间隙平均后的槽深边际均值在所采样的 $d=75$ nm 档最大（+4.75%），随后回落。', 'E5: specify marginal mean in main text')
    change(EN, 'with a peak at $d=75$ nm (+4.75%) followed by a decline.', 'with the depth marginal mean, averaged over gaps, largest at the sampled $d=75$ nm level (+4.75%) and lower thereafter.', 'E5: bilingual match')
    change(CN, '这与横槽无单一主控参数一致，但比"非单调"更具体：小槽深处出现反向，峰值位于采样中段。', '这些是所列偏差响应的描述性特征，不确定横槽输运的物理主控参数：小槽深处出现偏差反向，槽深边际均值的最大值位于采样中段。', 'W1/E5: residual shape is not a physical-control diagnosis')
    change(EN, 'This is consistent with the absence of a single controlling parameter across the groove, but is more specific than non-monotonicity alone: reversal occurs at small depth and the peak lies in the middle of the sampled range.', 'These are descriptive features of the listed discrepancy response and do not identify a physical controlling parameter for transverse transport: the discrepancy reverses sign at small depth, and the largest depth marginal mean lies in the middle of the sampled range.', 'W1/E5: bilingual match')

    change(SC, '定性判断"横槽没有单一主控参数"仍成立，但', '本矩阵的横槽有符号偏差包含两个主效应与交互余项，不能据此判定物理主控参数；', 'W1: distinguish descriptive response from physical control')
    change(SE, 'The qualitative statement that no single parameter controls the transverse response still holds, but', 'The transverse signed discrepancy on this matrix contains both main-effect and interaction components, which do not identify a physical controlling parameter;', 'W1: bilingual match')

    # Reference distinctions in adjoining limitations and supplement summaries.
    change(CN, '参考分别为有限元与 5 nm OpenLB', '参考分别为有限元/有限体积法组合与 5 nm OpenLB', 'W2: mixed reference set is not entirely FEM')
    change(CN, '其五，该批计算为待正式采用的候选参考，不构成正式参考资格或物理验证。', '其五，新增有限元计算仍为待正式采用的候选参考，既有有限元结果保留有限采用建议和历史溯源限制，既有合格有限体积法记录保留原参考资格；本比较不构成物理验证。', 'W2: main-text limitations distinguish statuses')
    change(EN, 'referenced to finite-element and 5 nm OpenLB values respectively', 'referenced to the finite-element/finite-volume combination and 5 nm OpenLB values respectively', 'W2: bilingual mixed-reference description')
    change(EN, 'Fifth, that batch is a candidate reference pending formal adoption and confers neither formal reference status nor physical validation.', 'Fifth, the new finite-element runs remain candidate references pending formal adoption, legacy finite-element results retain their limited-use recommendation and provenance limitations, and the qualified finite-volume records retain their existing reference status. This comparison is not physical validation.', 'W2: bilingual status distinctions')
    change(CN, '其身份为待正式采用的候选数值参考，不构成物理验证。', '其中新增有限元计算待正式采用，既有有限元结果保留有限采用建议及溯源限制，既有合格有限体积法记录保留资格；本比较不构成物理验证。', 'W2: main conclusion preserves all source identities')
    change(EN, 'its status is candidate numerical reference pending formal adoption, and it constitutes neither physical validation nor a continuous-domain guarantee.', 'the new finite-element runs await formal adoption, legacy finite-element results retain their limited-use recommendation and provenance limitations, and qualified finite-volume records retain their qualification. The comparison constitutes neither physical validation nor a continuous-domain guarantee.', 'W2: bilingual conclusion')
    change(CO, '参考为二维有限元，17 种几何成对', '参考由二维有限元与既有合格有限体积法结果组成，17 种几何成对', 'W2: conclusion authority mixed-reference description')
    change(CO, '其身份为**待正式采用的候选参考**，不构成物理验证。', '其中新增有限元计算仍为**待正式采用的候选参考**，既有有限元结果保留有限采用建议及历史溯源限制，既有合格有限体积法记录保留原资格；本比较不构成物理验证。', 'W2: conclusion authority status distinctions')
    change(SC, '2. "正式参考资格"——当前为候选参考，须另签审查。', '2. 将本节全部结果统称为"已取得正式参考资格"——新增有限元仍为候选，既有有限元保留有限采用建议及历史溯源限制；既有合格有限体积法记录的资格不变。', 'W2: avoid blanket classification in S15')
    change(SE, '2. "Formal reference status" — the status is candidate, pending separate sign-off.', '2. Describing all results here as formally qualified references: the new finite-element runs remain candidates, legacy finite-element results retain their limited-use recommendation and provenance limitations, and qualified finite-volume records retain their qualification.', 'W2: bilingual S15')
    change(SC, '8. 不因本节趋势成立就称 V2"已被独立验证"；参考身份仍是候选，须另签采用审查。', '8. 不因本节趋势成立就称 V2"已被独立验证"；新增有限元参考仍为候选，须另签采用审查；既有有限元的有限采用建议及溯源限制、既有合格有限体积法的资格分别保留。', 'W2: source-specific S16 qualification')
    change(SE, '8. No claim that V2 is independently validated on the strength of these trends; the reference remains a candidate pending a formal adoption review.', '8. No claim that V2 is independently validated on the strength of these trends. The new finite-element references remain candidates pending formal adoption; legacy finite-element limited-use recommendations and provenance limitations, and existing qualified finite-volume status, are retained separately.', 'W2: bilingual S16')

    # Preserve every DOE numeric value in the conclusion file, outside the six conclusions.
    begin = texts[CO].index('**独立参考下的趋势分解（2026-11-14 新增）。**')
    end = texts[CO].index('\n\n**证据位置**', begin)
    numeric_note = texts[CO][begin:end]
    corrected_note = numeric_note.replace('**原公式的偏差在两方向都由槽深主导', '**原公式有符号偏差的槽深主效应平方和份额在两方向均最大').replace('扣除槽深依赖后 V2 的沿槽残余偏差反过来由间隙主导', '固定 V2 沿槽有符号偏差的间隙主效应份额最大').replace('这与 V2 因子只含 $d/w$、完整式仍含 $h$ 是同一件事的两面：原式漏掉的主要是槽深，补入后剩下的主要是间隙。', '原公式已经含有槽深与间隙。该结果与仅依赖 $d/w$ 的因子仍保留间隙相关残余的观察一致，但不确定唯一的缺失变量、改进形式或物理原因；完整公式仍含 $h$。').replace('非 5 nm 参考产物', '该观察并非仅见于以 5 nm OpenLB 为基线的比较，不单独确定机制或连续解精度').replace('15 个确定性结果占满全部自由度，无独立残差自由度', '15 个确定性格点上的完整交互模型为饱和模型，无独立残差自由度')
    summary_cn = '在所列等权采样矩阵中，固定 V2 的沿槽有符号残余仍呈间隙相关差异；所列参数趋势在更换数值对照后保留。这支持按采样条件评价单变量因子的局限，不单独确定唯一的缺失变量、物理原因或连续参数域精度。'
    summary_en = 'Within the specified equally weighted matrix, the fixed-V2 along-groove signed residual retains gap-related variation, and the listed parameter trends persist after changing the numerical comparison. This supports evaluating the limitations of the single-variable factor under the sampled conditions, but does not identify a unique missing variable or physical cause, or establish continuous-domain accuracy.'
    change(CO, numeric_note, summary_cn, 'W3: detailed numeric evidence moved outside six conclusion statements')
    marker = '\n---\n\n## 2 统一偏差定义'
    change(CO, marker, '\n---\n\n## DOE证据说明（对应第四条，不属于六条结论正文）\n\n' + corrected_note + '\n\n' + marker.lstrip('\n'), 'W3: retain every original DOE numeric value in a separate evidence note')
    for p, prefix, summary in [(CN, '**四、** 使用固定V2系数', summary_cn), (EN, '**4.** Retrospective comparison', summary_en)]:
        old = next(s for s in texts[p].splitlines() if s.startswith(prefix))
        change(p, old, old + ' ' + summary, 'W3: synchronize qualitative DOE conclusion without shares')
    change(CO, '**现有不一致：无。** 三方（本文件六条 / 稿件 §6 六条 / PPT 第 11 页六条）已完全对齐。', '**本轮同步范围**：本文件六条与中英稿件 §6 六条的核心科学口径已同步；PPT 第 11 页本轮未复核，不由历史检查推断其当前已完全对齐。', 'W3: do not claim current PPT verification not performed')

    # These refinements keep the already reported numbers and bound local agreement.
    change(CN, '远小于本节讨论的百分比差异。$h=25$', '远小于本节讨论的百分比差异；这一局部一致性不证明两法在全部几何上可互换。$h=25$', 'W2: one-geometry agreement is local evidence')
    change(EN, 'far below the percentage differences discussed here. The three $h=25$', 'far below the percentage differences discussed here; this local agreement does not establish interchangeability over all geometries. The three $h=25$', 'W2: bilingual local agreement')
    change(SC, '混用两种参考是可接受的，因为', '两种参考的同条件差异在所列局部检验中较小：', 'W2: report local agreement rather than blanket acceptability')
    change(SC, '但必须披露，**不能写成"全部为有限元"**。', '这一局部一致性不证明所有几何上两法可互换，来源仍须分别披露，**不能写成"全部为有限元"**。', 'W2: source disclosure and limited inference')
    change(SE, 'Mixing two references is acceptable because both methods exist under identical conditions at $h=75$, $d=100$ nm and differ by far less than the percentage differences discussed here; it must nevertheless be disclosed, and the set **must not be described as entirely finite element**.', 'Both methods exist under identical conditions at $h=75$, $d=100$ nm and differ by far less than the percentage differences discussed here. This local agreement does not establish interchangeability across all geometries; the source composition must be disclosed, and the set **must not be described as entirely finite element**.', 'W2: bilingual local agreement in supplement')

    # Guard all scientific percentages, numerical table cells, displayed equations and references.
    checks = {}
    percent = r'(?<![\w.])[+−–-]?\d+(?:\.\d+)?\s*(?:\\%|%)'
    for p in paths:
        old, new = original[p], texts[p]
        assert Counter(re.findall(percent, old)) == Counter(re.findall(percent, new)), ('percentages', p)
        table_numbers = lambda s: [re.findall(r'[+−-]?\d+(?:\.\d+)?', line)
                                   for line in s.splitlines() if line.startswith('|')]
        assert table_numbers(old) == table_numbers(new), ('table numbers', p)
        assert re.findall(r'\$\$.*?\$\$', old, re.S) == re.findall(r'\$\$.*?\$\$', new, re.S), ('equations', p)
        assert Counter(re.findall(r'\[\d+(?:[—–,-]\d+)*\]', old)) == Counter(re.findall(r'\[\d+(?:[—–,-]\d+)*\]', new)), ('citations', p)
        assert '有限元体积法' not in new
        checks[p] = {'percentage_multiset_unchanged': True, 'table_numeric_cells_unchanged': True,
                     'displayed_equations_unchanged': True, 'numeric_citations_unchanged': True}
    assert corrected_note in texts[CO]
    assert len(re.findall(r'^### [一二三四五六]、', texts[CO], re.M)) == 6
    for p in paths:
        assert (ROOT / p).read_text() == original[p], ('concurrent edit', p)
    for p in paths:
        (ROOT / p).write_text(texts[p])
    (OUT / 'edits.json').write_text(json.dumps(edits, ensure_ascii=False, indent=2) + '\n')
    (OUT / 'edit_checks.json').write_text(json.dumps(checks, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'documents_changed': len(paths), 'exact_edits': len(edits), 'guards': checks}, ensure_ascii=False))


if __name__ == '__main__':
    main()

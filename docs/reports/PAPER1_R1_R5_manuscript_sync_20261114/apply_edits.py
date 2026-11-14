#!/usr/bin/env python3
"""One-shot, snapshot-bound prose edits. No simulation or evidence promotion."""
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
BASE = 'docs/reports/'
MOTHERS = [BASE + p for p in [
    'SIM240_中文稿_导师审阅版_20261022.md',
    'SIM240_First_Paper_English_20261028.md',
    'SIM240_Supplementary_Methods_20261024/SUPPLEMENTARY_METHODS.md',
    'SIM240_Supplementary_Methods_20261024/SUPPLEMENTARY_METHODS_EN_20261028.md',
    'PAPER1_conclusions_current_20261109.md']]
OTHER = [BASE + p for p in [
    'PAPER1_submission_manuscript_20261110/SIM240_submission_CN.md',
    'PAPER1_submission_manuscript_20261110/SIM240_submission_EN.md',
    'PAPER1_CURRENT_FILES_AUTHORITY_20261110.md',
    'PAPER1_submission_package_20261109/MANIFEST.md',
    'PAPER1_submission_manuscript_20261110/README.md']]

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    assert not (OUT / 'before_manifest.json').exists(), 'One-shot script; snapshot already exists'
    reviewed = json.loads((ROOT / BASE / 'PAPER1_core_claims_final_review_20261114/INPUT_SNAPSHOT.json').read_text())
    for path in MOTHERS + OTHER[:-1]:
        assert sha(ROOT / path) == reviewed[path]['sha256'], ('Reviewed baseline changed', path)
    snapshot = {}
    for rel in MOTHERS + OTHER:
        p = ROOT / rel
        dest = OUT / 'before' / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(p.read_bytes())
        snapshot[rel] = {'sha256': sha(p), 'bytes': p.stat().st_size,
                         'snapshot': str(dest.relative_to(OUT))}
    (OUT / 'before_manifest.json').write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + '\n')
    protected = json.loads((ROOT / BASE / 'PAPER1_doe_wording_fix_20261114/protected_inputs.json').read_text())
    protected.update({p: v['sha256'] for p, v in reviewed.items() if p not in MOTHERS + OTHER})
    for p in (ROOT / BASE / 'PAPER1_core_claims_final_review_20261114').iterdir():
        if p.is_file():
            protected[str(p.relative_to(ROOT))] = sha(p)
    for p, expected in protected.items():
        assert sha(ROOT / p) == expected, ('Protected baseline mismatch', p)
    (OUT / 'protected_inputs.json').write_text(json.dumps(protected, ensure_ascii=False, indent=2) + '\n')
    texts = {p: (ROOT / p).read_text() for p in MOTHERS}
    edits = []
    cn, en, sc, se, co = MOTHERS

    def rep(path, old, new, reason):
        assert texts[path].count(old) == 1, (reason, path, old[:80], texts[path].count(old))
        texts[path] = texts[path].replace(old, new, 1)
        edits.append({'path': path, 'before': old, 'after': new, 'reason': reason})

    def paragraph(path, prefix, new, reason):
        old = next(p for p in texts[path].split('\n\n') if p.startswith(prefix))
        rep(path, old, new, reason)

    paragraph(cn, '本文的主比较针对固定周期',
        '本文针对固定周期、等宽槽与凸台的全充液矩形沟槽，量化局部立方律相对于显式沟槽计算的两主方向导度偏差，以及这些偏差对各向异性和张量重建流向的影响。本研究采用以 $d/w$ 为因子自变量的双方向乘性经验修正V2，并用9种标定几何标定其四个系数，回顾性评价固定V2的总体改善与局部失效。另列有限元和有限体积法数值对照，检查主要观察对离散实现的依赖；这些对照承担验证职责，分别保留候选参考、有限采用建议与既有合格参考的身份，不能推广为全图参考资格。',
        'R1: organize principal bias, retrospective correction, and cross-method support')
    paragraph(cn, '在固定周期、固定槽宽的矩形沟槽中，分别施加',
        '主比较分别施加沿槽与跨槽驱动，以5 nm网格得到的两个主值为离散参考，在相同几何、通量定义与物性下评价原公式及V2经验修正。四个几何的加密结果用于报告参考敏感性，不构成全地图连续解精度证书。理想Stokes问题中的主导度上界提供连续模型约束，不给出离散偏差幅度或修正精度。参数趋势用于描述所采样残差的结构；另对两种槽宽的已知开发几何作梯度能量诊断，为所测条件的方向性偏差提供受限定量解释，见第5.1节和补充材料S14。理论、数值核对与这些补充解释各有证据范围，不能相互替代。',
        'R1: distinguish theoretical constraints and supplementary interpretation')
    paragraph(en, 'We compare both principal conductances of fully filled',
        'For fully filled rectangular grooves of fixed period and equal groove and rib widths, we quantify local-cubic-law discrepancies in both principal conductances relative to explicit-groove calculations, and their consequences for anisotropy and tensor-reconstructed flow direction. We calibrate a two-direction multiplicative empirical correction, V2, whose factors depend on $d/w$, on nine geometries and retrospectively evaluate the aggregate improvement and local failures of fixed V2. Separate finite-element and finite-volume comparisons examine the dependence of the main observations on discretization. These comparisons provide verification evidence while retaining the respective candidate-reference, limited-use-recommendation and previously qualified-reference statuses; they do not qualify references across the full map.',
        'R1: English counterpart of claim hierarchy and reference roles')
    paragraph(en, 'For rectangular grooves of fixed period and width, we apply',
        'The main comparison applies along-groove and across-groove forcing separately. Principal values on a 5 nm grid serve as discrete references for the local cubic law and V2 under common geometry, flux definitions and fluid properties. Refinements at four geometries characterize reference sensitivity, rather than certifying continuous-solution accuracy across the map. Ideal-Stokes upper bounds constrain the continuous model but do not quantify discrete discrepancies or correction accuracy. Parameter trends describe the sampled residual structure. A gradient-energy diagnostic on known development geometries at two groove widths provides a bounded quantitative interpretation of directional discrepancies under the tested conditions; see Section 5.1 and Supplementary S14. Theory, numerical comparisons and these supplementary interpretations have distinct evidential scopes and cannot replace one another.',
        'R1: English counterpart of theoretical and supplementary roles')

    rep(sc, '本节 36 条为 19 种几何、参考为有限元。',
        '本节 36 条为 19 种几何、参考为有限元/有限体积法组合对照。', 'R2: mixed reference identity')
    rep(se, 'the 36 here are 19 geometries against finite-element references.',
        'the 36 here are 19 geometries against a combination of finite-element and finite-volume comparison references.', 'R2: mixed reference identity')
    rep(cn, '三档网格 5.0、2.5、1.25 nm 逐档求解，不重试、不自动加密。数值门槛在冻结前写入并事后逐档重算，相邻两档导度变化最坏为',
        '对本轮新增横槽有限元记录，三档网格 5.0、2.5、1.25 nm 逐档求解，不重试、不自动加密。以下冻结门槛与最坏值仅对应该新增批次，事后由保存场逐档复核；以粗一级导度为分母的相邻两档导度变化最坏为', 'R2/R5: new-batch scope and frozen denominator')
    rep(en, 'Three grids of 5.0, 2.5 and 1.25 nm are solved in sequence, with no retry and no automatic refinement. Numerical gates were fixed before the runs and are recomputed level by level afterwards; the worst conductance changes between adjacent grids are',
        'For the newly added transverse finite-element records, three grids of 5.0, 2.5 and 1.25 nm are solved in sequence, with no retry and no automatic refinement. The following frozen gates and worst values apply only to this added batch and are checked level by level from saved fields; the worst conductance changes between adjacent grids, normalized by the coarser-level conductance, are', 'R2/R5: English new-batch scope and frozen denominator')
    rep(sc, '三档网格 5.0、2.5、1.25 nm 逐档求解，**不重试、不自动加密**。',
        '本轮新增横槽记录按三档网格 5.0、2.5、1.25 nm 逐档求解，**不重试、不自动加密**。', 'R2: scope of execution policy')
    # Match the English sentence without assuming its punctuation from a prior revision.
    old = next(s for s in texts[se].splitlines() if '5.0, 2.5 and 1.25' in s)
    new = old.replace('Three grids of 5.0, 2.5 and 1.25 nm', 'For the newly added transverse records, three grids of 5.0, 2.5 and 1.25 nm')
    assert new != old
    rep(se, old, new, 'R2: scope of execution policy')
    rep(sc, '各项门槛在运行前冻结，事后由保存场逐档重算：',
        '下列冻结门槛与最坏实测值仅对应本轮新增横槽有限元记录；门槛在运行前固定，事后由保存场逐档复核。既有有限元记录的有限采用建议与溯源限制、既有有限体积法参考的资格分别保留，不由本表统一授予：', 'R2: gate and provenance scope')
    rep(se, 'Gates were fixed before the runs and recomputed level by level from the saved fields:',
        'The following frozen gates and worst measured values apply only to the newly added transverse finite-element records; gates were fixed before the runs and checked level by level from saved fields. The limited-use recommendation and provenance limitations of the earlier finite-element records, and the existing qualification of the finite-volume references, remain separate and are not conferred by this table:', 'R2: gate and provenance scope')

    for path in (cn, sc, co):
        rep(path, '但h100尚无同几何加密证据，', '但h100尚无同几何的OpenLB加密证据；另列的有限元网格对照不能替代这一OpenLB加密检查，', 'R3: missing refinement refers to OpenLB')
    for path in (en, se):
        rep(path, 'However, no same-geometry refinement is available at h100, so', 'However, no same-geometry OpenLB refinement is available at h100; the separately reported finite-element grid comparison cannot replace that OpenLB refinement check, so', 'R3: missing refinement refers to OpenLB')
    rep(sc, 'h100尚无同几何加密参考，本轮未追加计算。', 'h100尚无同几何的OpenLB加密参考，已有有限元对照不替代该项检查；本轮未追加计算。', 'R3: supplementary refinement scope')
    rep(se, 'A matched refinement at h100 is unavailable; no calculation was added in this revision.', 'A matched OpenLB refinement at h100 is unavailable; the existing finite-element comparison does not replace this check. No calculation was added in this revision.', 'R3: supplementary refinement scope')

    rep(cn, '深槽之间的差异落在数值分辨力之下，故不宜宣布精确的连续饱和阈值。',
        '所列深槽增量小于报告的相邻网格变化；在缺少针对该增量的不确定性评估时，不据此认定连续饱和阈值。', 'R4: adjacent-grid changes are not resolution certificates')
    rep(en, 'differences among deep grooves fall below the numerical resolution, so no precise continuous saturation threshold should be declared.',
        'the listed deep-groove increments are smaller than the reported adjacent-grid changes; without an uncertainty assessment for those increments, no continuous saturation threshold is inferred.', 'R4: adjacent-grid changes are not resolution certificates')

    rep(sc, '| 检查 | 最坏实测 | 门槛 | 门槛÷最坏 | 最坏出现处 |',
        '| 检查 | 最坏实测（网格行按显示口径） | 冻结门槛（按协议口径验收） | 门槛÷显示值 | 最坏出现处 |', 'R5: distinguish display normalization from frozen acceptance')
    rep(se, '| Check | Worst measured | Threshold | Threshold ÷ worst | Worst at |',
        '| Check | Worst measured (display convention for grid rows) | Frozen threshold (protocol convention for acceptance) | Threshold ÷ displayed value | Worst at |', 'R5: distinguish display normalization from frozen acceptance')
    rep(sc, '**最紧两项是相邻网格变化（5.2×、5.5×）与直接残差（8.6×），不是"每项三个数量级余量"。** 相邻网格变化本身不是连续解的误差上界。',
        '**分母说明：** 表中相邻网格变化显示值以细一级导度为分母，即相邻两档导度差的绝对值除以细一级导度，再以百分比表示；冻结协议及复核回执则以粗一级导度为分母进行门槛验收。两种量均来自同一组保存导度，但不能视为同一个验收读数。门槛÷显示值一列只作近似量级展示，不替代按冻结协议读取回执的判定；其余检查的定义不变。\n\n**按表中显示口径，余量较小的项目为相邻网格变化（5.2×、5.5×）与直接残差（8.6×），不能概括为"每项三个数量级余量"。** 相邻网格变化本身不是连续解的误差上界。',
        'R5: explicit finer/coarser denominators; preserve displayed values and historical decisions')
    rep(se, '**The tightest items are the adjacent-grid changes (5.2×, 5.5×) and the direct residual (8.6×), not "three orders of magnitude on every item".** Adjacent-grid changes are not error bounds on the continuous solution.',
        '**Denominator convention.** Displayed adjacent-grid changes use the finer-level conductance as denominator: the absolute difference between adjacent conductances is divided by the finer value and expressed as a percentage. The frozen protocol and verification receipts instead use the coarser-level conductance for gate acceptance. Both quantities come from the same saved conductances but are not the same acceptance reading. The threshold-to-displayed-value column gives approximate scale comparisons and does not replace receipt-based decisions under the frozen protocol; definitions of the other checks are unchanged.\n\n**Under the displayed convention, the smaller margins are for adjacent-grid changes (5.2×, 5.5×) and the direct residual (8.6×); they cannot be summarized as "three orders of magnitude on every item".** Adjacent-grid changes are not error bounds on the continuous solution.',
        'R5: explicit finer/coarser denominators; preserve displayed values and historical decisions')

    num = r'(?<![\w.])[+−-]?\d+(?:\.\d+)?'
    for path, text in texts.items():
        old = (ROOT / path).read_text()
        a, b = Counter(re.findall(num, old)), Counter(re.findall(num, text))
        assert a == b, (path, a-b, b-a)
    (OUT / 'edits.json').write_text(json.dumps(edits, ensure_ascii=False, indent=2) + '\n')
    for path, text in texts.items():
        (ROOT / path).write_text(text)
    print(json.dumps({'edits': len(edits), 'mothers': len(texts), 'protected': len(protected)}, ensure_ascii=False))

if __name__ == '__main__':
    main()

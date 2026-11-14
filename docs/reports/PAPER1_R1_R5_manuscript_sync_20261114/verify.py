#!/usr/bin/env python3
"""Check text/data invariants for this revision; never runs a simulation."""
import csv
import hashlib
import json
import re
import subprocess
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    before = json.loads((OUT / 'before_manifest.json').read_text())
    mothers = list(before)[:5]
    documents = {}
    num = r'(?<![\w.])[+−-]?\d+(?:\.\d+)?'
    pct = r'(?<![\w.])[+−–-]?\d+(?:\.\d+)?\s*(?:\\%|%)'
    replay = {p: (OUT / before[p]['snapshot']).read_text() for p in mothers}
    for item in json.loads((OUT / 'edits.json').read_text()):
        assert replay[item['path']].count(item['before']) == 1
        replay[item['path']] = replay[item['path']].replace(item['before'], item['after'], 1)
    for rel in mothers:
        old = (OUT / before[rel]['snapshot']).read_text()
        new = (ROOT / rel).read_text()
        assert new == replay[rel], ('edit replay', rel)
        for pattern in (num, pct, r'\[\d+(?:[—–,-]\d+)*\]'):
            assert Counter(re.findall(pattern, old)) == Counter(re.findall(pattern, new)), (rel, pattern)
        table = lambda s: [re.findall(num, line) for line in s.splitlines() if line.startswith('|')]
        assert table(old) == table(new)
        assert re.findall(r'\$\$.*?\$\$', old, re.S) == re.findall(r'\$\$.*?\$\$', new, re.S)
        assert Counter(re.findall(r'(?<!\$)\$(?!\$).*?(?<!\$)\$(?!\$)', old)) == Counter(re.findall(r'(?<!\$)\$(?!\$).*?(?<!\$)\$(?!\$)', new))
        assert re.findall(r'\]\(([^)]+)\)', old) == re.findall(r'\]\(([^)]+)\)', new)
        for phrase in ('有限元体积法', '原式遗漏的主要变量是槽深', '原式漏掉的主要是槽深',
                       'after removing that depth dependence', 'This is the same fact stated twice',
                       'not an artefact of the 5 nm reference', '差异来自参考与几何集合的改变',
                       'The differences above therefore come from the change of reference and geometry set',
                       'exhaust the 15 degrees of freedom'):
            assert phrase not in new, (rel, phrase)
        documents[rel] = {'all_numeric_tokens_unchanged': True, 'percentages_unchanged': True,
                          'numeric_table_cells_unchanged': True, 'displayed_equations_unchanged': True,
                          'inline_math_multiset_unchanged': True, 'link_targets_unchanged': True,
                          'numeric_citations_unchanged': True, 'exact_edit_replay_matches': True}

    cn, en, sc, se, co = [(ROOT / p).read_text() for p in mothers]
    formal_sections = [cn.split('## 6 结论', 1)[1].split('## 参考文献', 1)[0],
                       en.split('## 6 Conclusions', 1)[1].split('## Appendix E.', 1)[0],
                       co.split('## 1 六条结论', 1)[1].split('## DOE证据说明', 1)[0]]
    for section in formal_sections:
        assert not any(value in section for value in ('93.40%', '93.77%', '88.98%'))
    assert len(re.findall(r'^### [一二三四五六]、', formal_sections[2], re.M)) == 6
    assert len(re.findall(r'^\*\*[一二三四五六]、\*\*', formal_sections[0], re.M)) == 6
    assert len(re.findall(r'^\*\*[1-6]\.\*\*', formal_sections[1], re.M)) == 6
    assert all(value in co.split('## DOE证据说明', 1)[1] for value in ('93.40%', '93.77%', '88.98%'))
    for section in (cn.split('### 4.6', 1)[1].split('## 5 ', 1)[0],
                    en.split('### 4.6', 1)[1].split('## 5 ', 1)[0]):
        assert '12' in section and '2' in section
    assert '既有参考资格' in cn and 'existing reference qualification' in en
    assert '有限采用建议' in cn and 'recommendation for limited use' in en

    # Bilingual scope checks supplement, rather than replace, editorial review.
    intro_cn = cn.split('### 1.3', 1)[1].split('## 2 ', 1)[0]
    intro_en = en.split('### 1.3', 1)[1].split('## 2 ', 1)[0]
    assert all(s in intro_cn for s in ('回顾性', '局部失效', '有限体积法', '验证职责', '有限采用建议', '连续模型约束'))
    assert all(s in intro_en for s in ('retrospectively', 'local failures', 'finite-volume', 'verification evidence', 'limited-use-recommendation', 'continuous model'))
    assert '19 种几何、参考为有限元/有限体积法组合对照' in sc
    assert '19 geometries against a combination of finite-element and finite-volume' in se
    assert '最坏实测值仅对应本轮新增横槽有限元记录' in sc
    assert 'worst measured values apply only to the newly added transverse finite-element records' in se
    for text in (cn, sc, co):
        assert 'h100尚无同几何的OpenLB加密证据' in text
        assert '但h100尚无同几何加密证据' not in text
    for text in (en, se):
        assert 'no same-geometry OpenLB refinement is available at h100' in text
        assert 'no same-geometry refinement is available at h100' not in text
    assert '差异落在数值分辨力之下' not in cn
    assert 'differences among deep grooves fall below the numerical resolution' not in en
    assert all(s in sc for s in ('以细一级导度为分母', '以粗一级导度为分母', '不能视为同一个验收读数'))
    assert all(s in se for s in ('finer-level conductance as denominator', 'coarser-level conductance for gate acceptance', 'not the same acceptance reading'))
    assert '待正式采用的候选参考' in sc and 'candidate reference pending formal adoption' in se

    source = json.loads((ROOT / 'docs/reports/PAPER1_fem_v2_doe_20261114/DOE_V2_NEW_REFERENCE.json').read_text())
    responses = ['LC_P', 'V2_P', 'LC_T', 'V2_T']
    table_cells = 0
    for text, marker in [(cn, '**表 11'), (en, '**Table 11.'),
                         (sc, '### S16.3'), (se, '### S16.3')]:
        text = text.split(marker, 1)[1]
        data = []
        started = False
        for line in text.splitlines():
            if not line.startswith('|'):
                if started:
                    break
                continue
            started = True
            cells = [s.strip() for s in line.strip('|').split('|')]
            if len(cells) == 5 and all(re.fullmatch(r'[+−-]?\d+\.\d+%', x) for x in cells[1:]):
                data.append(cells)
        assert len(data) == 4
        for row, name in zip(data, responses):
            obj = source['new_set_decomposition'][name]
            expected = [obj[k] for k in ('share_h_percent', 'share_d_percent', 'share_interaction_percent', 'grand_mean')]
            assert all(abs(float(actual.replace('−', '-').strip('%')) - value) <= 0.00501
                       for actual, value in zip(row[1:], expected))
            table_cells += 4

    supp = ROOT / 'docs/reports/SIM240_Supplementary_Methods_20261024'
    name_map = {'local_cubic_along': 'LC_P', 'fixed_V2_along': 'V2_P',
                'local_cubic_across': 'LC_T', 'fixed_V2_across': 'V2_T'}
    csv_counts = {}
    for file in ('Table_S17_doe_shares.csv', 'Table_S18_doe_marginals.csv', 'Table_S19_doe_grid.csv'):
        b = (supp / file).read_bytes()
        assert b'\r' not in b
        with (supp / file).open() as stream:
            rows = list(csv.DictReader(stream))
        csv_counts[file] = len(rows)
        for row in rows:
            if 'variable' in row:
                value = source['new_set_decomposition'][name_map[row['response']]]['marginal_' + row['variable']][str(float(row['level_nm']))]
                assert abs(float(row['signed_marginal_mean_percent']) - value) <= 0.0000501
            elif 'h_nm' in row:
                for label, name in name_map.items():
                    value = source['profiles'][name]['by_h'][str(int(row['h_nm']))][[25, 50, 75, 100, 120].index(int(row['d_nm']))]
                    assert abs(float(row[label + '_percent']) - value) <= 0.0000501

    proc = subprocess.run([sys.executable, '-B', str(ROOT / 'docs/reports/PAPER1_submission_manuscript_20261110/build_submission.py'), '--check'],
                          cwd=ROOT, capture_output=True, text=True)
    (OUT / 'derived_check.log').write_text(proc.stdout + proc.stderr)
    assert proc.returncode == 0 and '不一致' not in proc.stdout
    protected = json.loads((OUT / 'protected_inputs.json').read_text())
    assert all(sha(ROOT / p) == expected for p, expected in protected.items())
    authority = (ROOT / 'docs/reports/PAPER1_CURRENT_FILES_AUTHORITY_20261110.md').read_text()
    manifest = (ROOT / 'docs/reports/PAPER1_submission_package_20261109/MANIFEST.md').read_text()
    for rel in mothers:
        row = next(line for line in authority.splitlines() if line.startswith('| ') and '`' + rel + '`' in line)
        assert sha(ROOT / rel)[:16] in row and str((ROOT / rel).stat().st_size) in row
        row = next(line for line in manifest.splitlines() if line.startswith('| ') and '`' + rel + '`' in line)
        assert sha(ROOT / rel)[:16] in row and str((ROOT / rel).stat().st_size) in row
    assert sha(ROOT / 'docs/reports/PAPER1_submission_package_20261109/MANIFEST.md')[:16] in authority
    outputs = {}
    for rel in before:
        p = ROOT / rel
        outputs[rel] = {'sha256': sha(p), 'bytes': p.stat().st_size, 'lines': len(p.read_bytes().splitlines())}
    (OUT / 'output_hashes.json').write_text(json.dumps(outputs, ensure_ascii=False, indent=2) + '\n')
    check = {'checked_at': datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),
             'documents': documents, 'source_bound_share_table_cells_checked': table_cells,
             'csv_rows_checked': csv_counts, 'conclusion_counts': [6, 6, 6],
             'numeric_DOE_evidence_retained_outside_six_conclusions': True,
             'derived_check_exit_code': proc.returncode, 'active_bindings_match': True,
             'protected_input_count': len(protected), 'changed_protected_inputs': [],
             'R1_R5_bilingual_scope_checks': 'PASS',
             'new_simulations': 0, 'reference_status_promoted': False,
             'check_scope': 'Text/data consistency only; no PDE or reference qualification re-audit'}
    (OUT / 'verification.json').write_text(json.dumps(check, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'mothers_numeric_invariance': len(documents), 'share_table_cells': table_cells,
                      'protected_inputs_unchanged': len(protected), 'derived_check': proc.returncode,
                      'conclusion_counts': [6, 6, 6]}, ensure_ascii=False))


if __name__ == '__main__':
    main()

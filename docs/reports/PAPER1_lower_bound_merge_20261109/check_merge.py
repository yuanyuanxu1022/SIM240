"""Check A-scope text integration against saved evidence and pre-edit snapshots."""
from pathlib import Path
from urllib.parse import unquote
import csv
import hashlib
import json
import math
import re

OUT = Path(__file__).resolve().parent
REP = OUT.parent
ROOT = REP.parents[1]
CN = REP / 'SIM240_中文稿_导师审阅版_20261022.md'
EN = REP / 'SIM240_First_Paper_English_20261028.md'
MAN = REP / 'PAPER1_submission_package_20261109/MANIFEST.md'
SUP = REP / 'SIM240_Supplementary_Methods_20261024'
checks = []


def check(name, ok, detail=None):
    item = dict(check=name, passed=bool(ok))
    if detail is not None:
        item['detail'] = detail
    checks.append(item)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def section(text, start, end):
    return text.split(start, 1)[1].split(end, 1)[0]


def dump(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


edits = json.loads((OUT / 'edits.json').read_text())
for path in [CN, EN, MAN]:
    old = (OUT / (path.name + '.before')).read_text()
    new = path.read_text()
    reverted = new
    for edit in reversed([e for e in edits if e['path'] == str(path.relative_to(ROOT))]):
        check(edit['label'] + ' uniquely reversible', reverted.count(edit['new']) == 1)
        reverted = reverted.replace(edit['new'], edit['old'], 1)
    check(path.name + ' all unlogged text unchanged', reverted == old)
    if path == MAN:
        continue
    cn = path == CN
    prefix = 'CN' if cn else 'EN'
    check(prefix + ' abstract unchanged', section(old, '## 摘要' if cn else '## Abstract', '## 1 ') ==
          section(new, '## 摘要' if cn else '## Abstract', '## 1 '))
    for number in [1, 2, 3, 4]:
        check(prefix + f' chapter {number} unchanged', section(old, f'## {number} ', f'## {number + 1} ') ==
              section(new, f'## {number} ', f'## {number + 1} '))
    check(prefix + ' five conclusions unchanged', section(old, '## 6 ', '## 参考文献' if cn else '## Data,') ==
          section(new, '## 6 ', '## 参考文献' if cn else '## Data,'))
    check(prefix + ' original references unchanged', re.findall(r'^\[\d+\].*$', old, re.M) ==
          re.findall(r'^\[\d+\].*$', new, re.M))
    tags = re.findall(r'\\tag\{([^}]+)\}', new)
    check(prefix + ' equation numbering preserved plus E7 E8', tags == re.findall(r'\\tag\{([^}]+)\}', old) + ['E7', 'E8'])
    check(prefix + ' all equation tags unique', len(tags) == len(set(tags)))
    appendix_head = '## 附录 E' if cn else '## Appendix E'
    original_e = old.split(appendix_head, 1)[1].split('\n## References', 1)[0].rstrip()
    new_e_original = new.split(appendix_head, 1)[1].split('<a id="appendix-e-lower">', 1)[0].rstrip()
    check(prefix + ' original Appendix E proof unchanged', original_e == new_e_original)
    check(prefix + ' E.1 heading and anchor unique', new.count('### E.1 ') == 1 and new.count('id="appendix-e-lower"') == 1)
    check(prefix + ' discussion points to E.1 and E8', '#appendix-e-lower' in new.split('### E.1 ')[0] and
          ('式（E8）' if cn else 'Eq. (E8)') in section(new, '## 5 ', '## 6 '))
    check(prefix + ' display delimiters balanced', new.count('$$') % 2 == 0 and new.count(r'\[') == new.count(r'\]'))
    old_equations = re.findall(r'\$\$\n(.*?)\n\$\$', old, re.S)
    new_equations = re.findall(r'\$\$\n(.*?)\n\$\$', new, re.S)
    check(prefix + ' all old displayed equations unchanged', new_equations[:-2] == old_equations)
    check(prefix + ' new numerical facts localized to E.1', all(s in new.split('### E.1 ')[1] for s in
          ['1.984', '58.2%', '23.8%', '88.8%', '30.6%', '11/18']))

cn_text, en_text = CN.read_text(), EN.read_text()
displays = lambda text: [re.sub(r'\s+', '', e) for e in re.findall(r'\$\$\n(.*?)\n\$\$', text.split('### E.1 ')[1], re.S)]
check('CN and EN E7/E8 displays identical', displays(cn_text) == displays(en_text) and len(displays(cn_text)) == 2)
for token in [r'f_h(z)=z(h-z)/2', r'0\le z\le h', r'z\ge h', r'H^1',
              r'Ph^3/12', r'i\in\{x,y\}']:
    check('CN and EN shared definition ' + token, all(token in t.split('### E.1 ')[1] for t in [cn_text, en_text]))

for relative, expected in json.loads((OUT / 'protected_inputs.json').read_text()).items():
    check('protected input ' + relative, sha(ROOT / relative) == expected)

with (REP / 'PAPER1_interval_note_review_20261109/normalized_records.csv').open() as handle:
    rows = list(csv.DictReader(handle))
check('saved data 46 unique paths', len(rows) == 46 and len({r['raw_path'] for r in rows}) == 46)
check('saved data 19 geometries', len({(r['h_nm'], r['d_nm']) for r in rows}) == 19)
check('38 main-grid plus 8 refinements', sum(float(r['dx_nm']) == 5 for r in rows) == 38 and
      sum(float(r['dx_nm']) == 2.5 for r in rows) == 8)
check('46 discrete conductances compatible with both bounds', all(float(r['lower_m3']) <= float(r['K_m3']) <= float(r['upper_m3']) for r in rows))
for direction, targets in [('P', (58.2, 88.8, 63)), ('T', (23.8, 30.6, 1.984))]:
    main = [r for r in rows if r['direction'] == direction and r['in_primary36'] == 'True']
    lower = sum(100 * (1 - float(r['lower_m3']) / float(r['K_m3'])) for r in main) / len(main)
    upper = sum(100 * (float(r['upper_m3']) / float(r['K_m3']) - 1) for r in main) / len(main)
    closer = sum(abs(float(r['lower_m3']) / float(r['K_m3']) - 1) < abs(float(r['upper_m3']) / float(r['K_m3']) - 1) for r in main)
    width = max(float(r['upper_over_lower']) for r in rows if r['direction'] == direction)
    check(direction + ' primary denominator 18', len(main) == 18)
    check(direction + ' adopted lower mean rounding', round(lower, 1) == targets[0])
    check(direction + ' adopted upper mean rounding', round(upper, 1) == targets[1])
    check(direction + ' lower closer 11/18', closer == 11)
    check(direction + ' interval width rounding', math.isclose(width, targets[2], abs_tol=.0005))

# Validate all numbered file rows in the existing MANIFEST, including unchanged ones.
manifest_rows = []
for line in MAN.read_text().splitlines():
    cells = [c.strip() for c in line.split('|')]
    if len(cells) > 4 and cells[1].isdigit():
        rel = cells[2].strip('`')
        path = ROOT / rel
        digest_index, size_index = (5, 6) if int(cells[1]) <= 5 else (3, 4)
        match = sha(path)[:16] == cells[digest_index].strip('`')
        size_match = path.stat().st_size == int(cells[size_index])
        manifest_rows.append(dict(path=rel, sha256=sha(path), bytes=path.stat().st_size))
        check('MANIFEST hash ' + rel, match)
        check('MANIFEST size ' + rel, size_match)
check('all eight numbered MANIFEST rows checked', len(manifest_rows) == 8)
dump('manifest_rows_verified.json', manifest_rows)

link_receipt = []
for path in [CN, EN, SUP / 'SUPPLEMENTARY_METHODS.md', SUP / 'SUPPLEMENTARY_METHODS_EN_20261028.md']:
    text = path.read_text()
    issues = []
    for dest in re.findall(r'!?\[[^\]\n]*\]\(([^\n)]+)\)', text):
        dest = unquote(dest.strip().strip('<>'))
        if re.match(r'^[a-z]+://', dest):
            continue
        target, _, anchor = dest.partition('#')
        target = re.sub(r':\d+$', '', target)
        resolved = (path.parent / target).resolve() if target else path.resolve()
        if not resolved.exists():
            issues.append(dict(link=dest, issue='missing file'))
        elif anchor:
            target_text = text if resolved == path.resolve() else resolved.read_text()
            if not re.search(r'id=[\"\x27]' + re.escape(anchor) + r'[\"\x27]', target_text):
                issues.append(dict(link=dest, issue='missing explicit anchor'))
    check(path.name + ' all local links and anchors resolve', not issues, issues)
    link_receipt.append(dict(path=str(path.relative_to(ROOT)), issues=issues))
dump('link_checks.json', link_receipt)

output_hashes = json.loads((OUT / 'output_hashes.json').read_text())
for rel, expected in output_hashes.items():
    check('output hash current ' + rel, sha(ROOT / rel) == expected)
dump('verification.json', dict(checks_passed=sum(c['passed'] for c in checks),
    checks_failed=sum(not c['passed'] for c in checks), checks=checks,
    scope='Text, saved arithmetic, references, links and hashes; no new theory or numerical acceptance',
    human_final_scientific_approval='not asserted', submission_ready=False))
print(json.dumps(dict(passed=sum(c['passed'] for c in checks), failed=[c for c in checks if not c['passed']]), ensure_ascii=False))
assert all(c['passed'] for c in checks)

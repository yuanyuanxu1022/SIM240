"""Check source identity, bilingual candidate citations, and unchanged inputs."""
from pathlib import Path
import csv
import hashlib
import json
import re
import zipfile

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
REP = ROOT / 'docs/reports'
checks = []


def check(name, ok, detail=None):
    item = dict(check=name, passed=bool(ok))
    if detail is not None:
        item['detail'] = detail
    checks.append(item)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


protected = json.loads((OUT / 'protected_inputs.json').read_text())
for relative, expected in protected.items():
    check('protected ' + relative, sha(ROOT / relative) == expected)

ledger = json.loads((OUT / 'source_manifest.json').read_text())
check('four distinct source identities', len(ledger) == len({s['doi'] for s in ledger}) == 4)
for e in ledger[:3]:
    m = json.loads((ROOT / e['metadata_path']).read_text())['message']
    for field, actual, expected in [('doi', m['DOI'].lower(), e['doi'].lower()),
            ('title', m['title'][0], e['title']), ('authors', m['author'], e['authors']),
            ('year', m['published']['date-parts'][0][0], e['year']),
            ('volume', m.get('volume'), e['volume']), ('page/article', m.get('page'), e['page_or_article'])]:
        check(e['evidence_id'] + ' Crossref ' + field, actual == expected)
    check(e['evidence_id'] + ' metadata SHA', sha(ROOT / e['metadata_path']) == e['metadata_sha256'])
check('Mohammadi full-text status not upgraded', 'abstract only' in ledger[2]['reading_level'])
check('Ng accepted-manuscript status retained', 'Accepted manuscript' in ledger[0]['reading_level'])

with (OUT / 'four_way_comparison.csv').open() as handle:
    rows = list(csv.DictReader(handle))
check('comparison has project plus four sources', len(rows) == 5)
check('all four comparison dimensions supplied', all(all(r[k] for k in ['geometry', 'driving', 'normalization', 'known_results_and_comparability']) for r in rows))
for name in ['CANDIDATE_CN.md', 'CANDIDATE_EN.md']:
    text = (OUT / name).read_text()
    body = text.split('\n\n')[2:-1]
    citations = re.findall(r'\[(1[2-5])\]', '\n\n'.join(body))
    check(name + ' new citations in order 12-15', citations == ['12', '13', '14', '15'], citations)
    check(name + ' marked unmerged', ('未合入' if '_CN' in name else 'not merged') in text)
refs = (OUT / 'REFERENCES.md').read_text()
check('candidate bibliography contiguous 12-15', re.findall(r'^\[(\d+)\]', refs, re.M) == ['12', '13', '14', '15'])
for e in ledger:
    check(e['evidence_id'] + ' DOI in candidate bibliography', e['doi'] in refs)

status = []
for name in ['SIM240_中文稿_导师审阅版_20261022.md', 'SIM240_First_Paper_English_20261028.md']:
    text = (REP / name).read_text()
    conclusion = text.split('## 6 ', 1)[1].split('\n## ', 1)[0]
    check(name + ' E.1 present', '### E.1 ' in text)
    check(name + ' E1-E8 present', re.findall(r'\\tag\{(E\d+)\}', text) == ['E' + str(i) for i in range(1, 9)])
    check(name + ' five conclusion items', len(re.findall(r'^\*\*[一二三四五六1-6]', conclusion, re.M)) == 5)
    check(name + ' scientific bibliography still 11 items', len(re.findall(r'^\[\d+\]', text, re.M)) == 11)
    status.append(dict(path=str((REP / name).relative_to(ROOT)), sha256=sha(REP / name), E1_present=True, conclusion_items=5))
with zipfile.ZipFile(REP / 'PPT_论文汇报_20261109/论文汇报.pptx') as z:
    slides = [n for n in z.namelist() if re.fullmatch(r'ppt/slides/slide\d+\.xml', n)]
    text = ' | '.join(re.findall(r'<a:t>(.*?)</a:t>', z.read('ppt/slides/slide11.xml').decode()))
    check('current PPT has 14 slides', len(slides) == 14)
    check('current slide11 has six conclusions and previously missing topics', all(s in text for s in ['六条结论', '新增间隙与静态接入', '机制诊断', 'S14']) if 'S14' in text else all(s in text for s in ['六条结论', '新增间隙与静态接入', '机制诊断', '梯度诊断']))
status.append(dict(path='docs/reports/PPT_论文汇报_20261109/论文汇报.pptx', slides=14, conclusion_slide=11, conclusion_items=6))
old_map = (REP / 'PAPER1_conclusions_current_20261109.md').read_text()
check('old independent-file PPT map is stale as reported', '汇报 PPT 第 10 页（五条）' in old_map and '**无对应**（PPT 缺）' in old_map)

receipt = json.loads((OUT / 'retrieval_log.json').read_text())
for filename in ['Ng2017_accepted.pdf', 'Stroock2002_author.pdf']:
    record = next(r for r in receipt if r['file'] == filename)
    check(filename + ' failed download not represented as saved PDF', record['status'] == 'not_retrieved' and not (OUT / 'sources' / filename).exists())
for filename in ['CANDIDATE_CN.md', 'CANDIDATE_EN.md', 'FOUR_WAY_COMPARISON.md', 'STATUS_CORRECTIONS.md', 'REFERENCES.md']:
    text = (OUT / filename).read_text()
    for dest in re.findall(r'\]\(([^)]+)\)', text):
        if '://' not in dest:
            check(filename + ' local link ' + dest, (OUT / dest.partition('#')[0]).exists())

result = dict(checks_passed=sum(c['passed'] for c in checks), checks_failed=sum(not c['passed'] for c in checks),
    checks=checks, manuscript_and_status_observations=status,
    scope='Source identity, preserved inputs, candidate numbering and current document facts; no novelty certification or numerical validation',
    human_final_scientific_approval='not asserted', formal_manuscripts_modified=False, submission_ready=False)
(OUT / 'verification.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(dict(passed=result['checks_passed'], failed=[c for c in checks if not c['passed']]), ensure_ascii=False))
assert result['checks_failed'] == 0

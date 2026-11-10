"""Local receipt/document integrity checks; does not import or run any solver."""
from pathlib import Path
import json, hashlib, re, difflib
BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[2]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
manifest = json.loads((BASE / 'source_manifest_before.json').read_text())
changes = json.loads((BASE / 'document_changes.json').read_text())
changed_paths = {str((ROOT / x['path']).resolve()) for x in changes}
protected = []
for name, entry in manifest.items():
    if name not in changed_paths:
        actual = sha(name)
        protected.append({'path': name, 'expected_sha256': entry['sha256'], 'actual_sha256': actual, 'unchanged': actual == entry['sha256']})
assert all(x['unchanged'] for x in protected)
assert len(changes) == 5
assert sum(x['path'].endswith('SUPPLEMENTARY_METHODS.md') for x in changes) == 2
assert sum(x['path'].endswith('20261022.md') for x in changes) == 3
formula_checks = []
for name in {x['path'] for x in changes}:
    p = ROOT / name
    old = (BASE / 'before' / p.name).read_text()
    cur = p.read_text()
    expected = old
    for ch in [x for x in changes if x['path'] == name]:
        assert expected.count(ch['before']) == 1
        expected = expected.replace(ch['before'], ch['after'])
    assert expected == cur
    tokens = lambda t: re.findall(r'\$\$[\s\S]*?\$\$|(?<!\$)\$[^$\n]*\$(?!\$)', t)
    assert tokens(old) == tokens(cur)
    formula_checks.append({'path': name, 'latex_fragments': len(tokens(cur)), 'identical': True})
for name in ['SIM240_AI_CONTEXT.md', 'AI_HANDOFF_20261015.md']:
    old = (BASE / 'before' / name).read_text()
    cur = (ROOT / 'docs/reports' / name).read_text()
    a = cur[cur.index('\n## 第一篇：历史构建'):]
    b = old[old.index('\n## 第一篇：历史构建'):]
    previous = ('[6]2018原文仍不在本机（全盘仅有2020 JFM那篇），M1保持OPEN，未取得。' if name == 'SIM240_AI_CONTEXT.md' else '**[6]2018原文仍不在本机**（全盘仅2020 JFM那篇），M1保持OPEN；未取得，无法核适用条件。')
    assert a == b.replace(previous, '该轮搜索时未取得[6]2018原文；此状态现由本页顶部2026-10-28接收记录取代，构建专项其余分析本次不重判。')
    (BASE / (name + '.diff')).write_text(''.join(difflib.unified_diff(old.splitlines(keepends=True), cur.splitlines(keepends=True), fromfile='before/' + name, tofile=name)))
# The verification report legitimately links to this output file itself.
verification_path = BASE / 'verification.json'
verification_path.write_text(json.dumps({'status': 'CHECKING'}))
links = []
source_texts = [(BASE / 'REPORT.md', (BASE / 'REPORT.md').read_text())]
source_texts += [(ROOT / x['path'], x['after']) for x in changes]
for p, txt in source_texts:
    for ref in re.findall(r'\]\(([^)]+)\)', txt):
        if re.match(r'https?://|#', ref):
            continue
        exists = (p.parent / ref.split('#')[0]).resolve().exists()
        links.append({'from': str(p.relative_to(ROOT)), 'ref': ref, 'exists': exists})
        assert exists, (p, ref)
record = {'date': '2026-10-28', 'scope': 'Selected artifact integrity and bounded editorial change checks; no numerical acceptance', 'all_checks_passed': True, 'protected_selected_inputs': protected, 'editorial_replacements': len(changes), 'exact_reconstruction_from_reviewed_replacements': True, 'formula_checks': formula_checks, 'new_relative_links_checked': links, 'state_changes': 'One newest receipt and one obsolete missing-PDF sentence replaced per state file; all other existing state text unchanged', 'human_author_verification': 'NOT_RECORDED', 'simulation_or_extractor_run': False, 'new_run_id': None, 'git_publish': False, 'interpretation': 'Does not validate source derivations, historical build provenance, numerical accuracy or journal readiness'}
verification_path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
outputs = {str(p.relative_to(ROOT)): sha(p) for p in BASE.rglob('*') if p.is_file() and p.name != 'output_manifest.json'}
for name in ['SIM240_AI_CONTEXT.md', 'AI_HANDOFF_20261015.md', 'SIM240_中文稿_导师审阅版_20261022.md', 'SIM240_Supplementary_Methods_20261024/SUPPLEMENTARY_METHODS.md']:
    p = ROOT / 'docs/reports' / name
    outputs[str(p.relative_to(ROOT))] = sha(p)
(BASE / 'output_manifest.json').write_text(json.dumps(outputs, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'all_checks_passed': True, 'protected_inputs': len(protected), 'editorial_replacements': len(changes), 'latex_fragments_preserved': sum(x['latex_fragments'] for x in formula_checks), 'relative_links': len(links)}, ensure_ascii=False))

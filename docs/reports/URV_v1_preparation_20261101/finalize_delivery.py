#!/usr/bin/env python3
"""Final local hash/link checks; no compiler or solver calls."""
from pathlib import Path
import hashlib
import json
import re

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[2]
CASE=ROOT/'CASE/unseen_v2_reference_v1'

def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for data in iter(lambda:f.read(1<<20),b''):h.update(data)
    return h.hexdigest()

def main():
    inputs=json.loads((CASE/'evidence/preparation_seal.json').read_text())['inputs_sha256']
    assert all(sha(p)==s for p,s in inputs.items())
    protected=json.loads((OUT/'protected_inputs_before.json').read_text())
    assert all(sha(p)==s for p,s in protected.items())
    old=json.loads((ROOT/'docs/reports/C_h75_reference_review_20261101/protected_inputs_verified.json').read_text())['files']
    assert all(sha(p)==s for p,s in old.items())
    link_count=0
    for p in [CASE/'README.md',CASE/'PROTOCOL.md',OUT/'REPORT.md']:
        for target in re.findall(r'\]\(([^)]+)\)',p.read_text()):
            if '://' in target:continue
            path=target.split('#')[0]
            assert (p.parent/path).exists(), (str(p),target)
            link_count+=1
    for name in ['SIM240_AI_CONTEXT.md','AI_HANDOFF_20261015.md']:
        text=(ROOT/'docs/reports'/name).read_text()
        assert text.splitlines()[2].startswith('## URV-v1隔离实现')
        assert 'URV_ZERO_20261101_01' in text[:7000]
    assert not (CASE/'results').exists()
    report=dict(delivery_PASS=True,preparation_bindings_unchanged=len(inputs),
        preserved_selected_inputs=len(protected),prior_C_h75_bindings_unchanged=len(old),
        local_document_links_checked=link_count,shared_context_and_handoff_updated=True,
        formal_runs_started=0,source_or_threshold_changes_after_seal=False)
    (OUT/'final_verification.json').write_text(json.dumps(report,indent=2)+'\n')
    files=[p for p in OUT.rglob('*') if p.is_file() and p.name!='source_manifest.json']
    files.extend(p for p in CASE.rglob('*') if p.is_file() and not any(v in p.relative_to(CASE).parts for v in ['audits','build','__pycache__']))
    files.extend(ROOT/'docs/reports'/name for name in ['SIM240_AI_CONTEXT.md','AI_HANDOFF_20261015.md'])
    (OUT/'source_manifest.json').write_text(json.dumps(dict(
        files={str(p.relative_to(ROOT)):sha(p) for p in sorted(set(files))},
        zero_audit_payloads_separately_bound=str(CASE/'audits/URV_ZERO_20261101_01/audit_files_sha256.json'),
        binary_and_dependencies_separately_bound=str(CASE/'evidence/preparation_seal.json')),indent=2)+'\n')
    print(json.dumps(report))

if __name__=='__main__':main()

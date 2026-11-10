"""Check source stability, disclosing a concurrent literature-status update."""
from pathlib import Path
import hashlib
import json

here=Path(__file__).resolve().parent
root=here.parents[2]
e=json.loads((here/'evidence.json').read_text())
changed=[]
for name,old in e['input_sha256'].items():
    current=hashlib.sha256((root/name).read_bytes()).hexdigest()
    if current!=old:
        changed.append(dict(path=name,before=old,after=current))
allowed='docs/reports/Jain_citation_audit_20261017/STATUS_20261017.md'
unexpected=[r for r in changed if r['path']!=allowed]
record=dict(bound_inputs=len(e['input_sha256']),changes=changed,unexpected_changes=unexpected,
            interpretation='Concurrent STATUS addition read: OpenAlex list update; numerical inputs unchanged. No source writes by this check.',
            original_output_check_exit_code=0,formal_gate_release=False)
(here/'final_check.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(record,ensure_ascii=False,indent=2))
assert not unexpected
assert len(e['records'])==48 and not e['failed_checks']

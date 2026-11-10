#!/usr/bin/env python3
"""Create an isolated checker version, leaving the original 830-file CASE intact."""
from pathlib import Path
import hashlib
import json
import shutil

ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
OLD=ROOT/'CASE/unseen_v2_reference_v1'
NEW=ROOT/'CASE/unseen_v2_reference_checker_v1_1'

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
    if NEW.exists():raise FileExistsError(NEW)
    original={str(p):sha(p) for p in OLD.rglob('*') if p.is_file()}
    (OUT/'original_case_before.json').write_text(json.dumps(original,indent=2)+'\n')
    previous=ROOT/'docs/reports/URV_v1_readonly_review_S0_20261101'
    protected={str(p):sha(p) for p in previous.rglob('*') if p.is_file()}
    protected.update(json.loads((previous/'historical_inputs_before.json').read_text()))
    (OUT/'protected_inputs_before.json').write_text(json.dumps(protected,indent=2)+'\n')
    for name in ['SIM240_AI_CONTEXT.md','AI_HANDOFF_20261015.md']:
        (OUT/'before').mkdir(exist_ok=True)
        shutil.copy2(ROOT/'docs/reports'/name,OUT/'before'/name)
    for folder in ['analysis','common','tests']:
        (NEW/folder).mkdir(parents=True)
    for p in (OLD/'analysis').glob('*.py'):shutil.copy2(p,NEW/'analysis'/p.name)
    for p in (OLD/'common').glob('*'):
        if p.is_file():shutil.copy2(p,NEW/'common'/p.name)
    for p in (OLD/'tests').glob('test_*.py'):
        text=p.read_text().replace("CASE/'audits/URV_ZERO_20261101_01'", "CASE.parent/'unseen_v2_reference_v1/audits/URV_ZERO_20261101_01'")
        (NEW/'tests'/p.name).write_text(text)
    anchor=dict(protocol_id='URV-v1',preparation_seal=str(OLD/'evidence/preparation_seal.json'),
        preparation_seal_sha256=sha(OLD/'evidence/preparation_seal.json'),
        native_source_sha256={p.name:sha(p) for p in (OLD/'src').glob('*') if p.suffix in ['.cpp','.h']},
        physical_spec_sha256=sha(OLD/'common/acceptance_spec.json'),
        execution_authorized=False)
    (NEW/'common/source_preparation_anchor.json').write_text(json.dumps(anchor,indent=2)+'\n')
    (NEW/'.gitignore').write_text('__pycache__/\n*.pyc\n')
    print(json.dumps(dict(new_checker=str(NEW),original_files=len(original),solver_calls=0)))

if __name__=='__main__':main()

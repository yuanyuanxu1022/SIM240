"""Use the frozen VTK audit function on completed local files; no native calls."""
from pathlib import Path
import hashlib
import json
import sys

REPORT=Path(__file__).resolve().parent
REPO=REPORT.parents[2]
PACKAGE=REPO/'outputs/URV_S4_1p25_data_20261104_234955'
RAW=PACKAGE/'01_raw_server/steady'
SOURCE=PACKAGE/'03_provenance/checker_analysis'
OUT=REPORT/'full_field_audit.json'
assert REPORT.resolve()!=RAW.resolve() and not REPORT.resolve().is_relative_to(RAW.resolve())
assert not OUT.exists(),'refusing audit overwrite'
release=json.loads((PACKAGE/'03_provenance/server_evidence/S4_TGE_SERVER_formal_launch_release_v1_20261104_01.json').read_text())
for name in ['read_fields.py','evidence.py']:
    assert hashlib.sha256((SOURCE/name).read_bytes()).hexdigest()==release['inputs_sha256'][
        'CASE/unseen_v2_reference_checker_S4_tge_server_v1/analysis/'+name]
sys.path.insert(0,str(SOURCE))
import read_fields
result=read_fields.audit(RAW)
result['audit_execution_context']=dict(caller='audit_fields.py',
    actual_python=sys.executable,reader_function='unchanged read_fields.audit',
    CLI_main_called=False,solver_calls=0,protected_run=str(RAW),
    note='Direct read-only function call; report is outside raw directory. No contracts CLI adapter invoked.')
OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(PASS=result['PASS'],frames=len(result['frames']),
                     steps=[x['step'] for x in result['frames']],VTK_version=result['VTK_version'],solver_calls=0)))

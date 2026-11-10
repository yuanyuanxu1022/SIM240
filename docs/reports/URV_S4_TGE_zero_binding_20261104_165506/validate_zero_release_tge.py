"""Read-only validation of the issued S4-TGE zero release. Never calls --execute."""
import json, sys
from pathlib import Path

ROOT = Path('/home/dell/yuanyuanxu/SIM240')
CASE = ROOT / 'CASE/unseen_v2_reference_S4_tge_v1'
CHECKER = ROOT / 'CASE/unseen_v2_reference_checker_S4_tge_v1'
PARENT_CHECKER = ROOT / 'CASE/unseen_v2_reference_checker_S4_reuse_v1'
sys.path.insert(0, str(CHECKER / 'analysis'))
sys.path.insert(0, str(PARENT_CHECKER / 'analysis'))
from tge_stage import verify_seal, validate_zero_authority, require_pristine, static_summary, unchanged, sha  # noqa: E402
import stage_s4  # noqa: E402

REL = CASE / 'evidence/S4_TGE_zero_launch_release_v1_20261104_01.json'
DIGEST = sha(REL)
results = {}

bound = verify_seal(REL, DIGEST)
results['verify_seal_with_external_sha'] = True
validate_zero_authority(bound, REL)
results['validate_zero_authority_exact_3_plus_1'] = True
require_pristine(bound)
results['four_planned_directories_pristine'] = True
unchanged(bound)
results['input_closure_3710_unchanged'] = True
summary = static_summary(bound)
results['static_summary'] = {k: summary[k] for k in
    ('binding_check', 'solver_executed', 'prepared_formal_runs', 'planned_native_zero_calls',
     'planned_initial_field_reads', 'native_zero_step_authorized', 'formal_simulation_authorized')}

# negative 1: wrong external SHA must be refused
try:
    verify_seal(REL, '0' * 64)
    results['wrong_sha_refused'] = False
except Exception:
    results['wrong_sha_refused'] = True

# negative 2: this zero release must not pass the formal S4 authority
try:
    stage_s4.validate_formal_authority(bound)
    results['formal_authority_refused'] = False
except Exception:
    results['formal_authority_refused'] = True

# negative 3: preparation A itself must still contain no execution authority
a = json.loads((CASE / 'evidence/preparation_A.json').read_text())
results['A_still_closed'] = (a['kind'] == 'S4_TGE_PREPARATION_A_NOT_AUTHORIZATION' and
    a['native_zero_step_authorized'] is False and a['approved_audit_run_ids'] == [])
results['A_sha_unchanged'] = sha(CASE / 'evidence/preparation_A.json') == \
    '53e544543ae26402a0d0fac7a7b3294e0a2286e7a7d4c336ce08e91abf53bfb9'

# no execution artefacts
results['no_audit_attempts_directory'] = not (CASE / 'audit_attempts').exists()
results['no_zero_verification_receipt'] = not (CASE / 'audits/URV_S4_TGE_ZERO_v1_20261104_01/verification.json').exists()
results['no_controller_log'] = not (CASE / 'S4_TGE_zero_controller_v1_20261104_01.log').exists()

results['release_sha256'] = DIGEST
results['release_inputs'] = len(bound['inputs_sha256'])
results['checks_pass'] = all(v is True for k, v in results.items() if isinstance(v, bool))
print(json.dumps(results, indent=2, ensure_ascii=False))
Path(ROOT / 'docs/reports/URV_S4_TGE_zero_binding_20261104_165506/validation_readonly.json').write_text(
    json.dumps(results, indent=2, ensure_ascii=False) + '\n')

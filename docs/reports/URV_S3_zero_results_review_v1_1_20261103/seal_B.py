"""Seal the accepted zero evidence as B, granting no execution permission."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from unittest.mock import patch
import contextlib
import copy
import io
import json
import sys

ROOT = Path('/home/dell/yuanyuanxu/SIM240')
OUT = Path(__file__).resolve().parent
CASE = ROOT / 'CASE/unseen_v2_reference_S3_reuse_v1_1'
CHECK = ROOT / 'CASE/unseen_v2_reference_checker_S3_reuse_v1_1'
sys.path[:0] = [str(CHECK / 'analysis'), str(CASE / 'scripts')]
from evidence import sha, need, EvidenceError
import stage_s3 as stage
import run_S3


def load(p):
    return json.loads(Path(p).read_text())


def save(p, d):
    with Path(p).open('x') as f:
        json.dump(d, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write('\n')


def main():
    a = CASE / 'evidence/preparation_A.json'
    a_sha = '7f6ca19de96949a537802f92804c787cf092e8de0eb10c681ed279736a2d3695'
    release = CASE / 'evidence/S3_zero_launch_release_v1_1_20261103_01.json'
    release_sha = 'dbe8b8a4ee33806e7d7ceeeaea0ec76ad68985fbb51851bcb0d3cae7dbd28f42'
    b = CASE / 'evidence/preparation_B.json'
    need(not b.exists() and not b.with_suffix('.sha256').exists(), 'B exists; no overwrite')
    acceptance = OUT / 'independent_review_acceptance.json'
    review = load(acceptance)
    need(review['ZERO_STEP_INDEPENDENT_REVIEW_PASS'] is True and
         review['ZERO_STEP_GEOMETRY_PASS'] is True and review['B_sealing_condition_satisfied'] is True and
         review['actual_VTK_field_rereads'] == 4 and review['twelve_records_reviewed'] == 12,
         'independent acceptance not complete')
    original = stage.verify_seal(a, a_sha)
    released = stage.verify_seal(release, release_sha)
    stage.validate_zero_authority(released)
    stage.require_pristine(original['prepared_runs'])
    protected = load(OUT / 'protected_inputs_and_outputs_before.json')
    need(all(sha(p) == h for p, h in protected.items()), 'existing evidence changed')
    audit = CASE / 'audits' / stage.AUDIT_ID
    receipt = audit / 'verification.json'
    completed = load(receipt)
    bound = copy.deepcopy(original)
    bound['inputs_sha256'].update(released['inputs_sha256'])
    for p in [a, a.with_suffix('.sha256'), release, release.with_suffix('.sha256'),
              *(p for p in audit.rglob('*') if p.is_file()),
              *(p for p in OUT.iterdir() if p.is_file())]:
        need(not p.is_symlink(), 'B input symlink')
        if str(p) in bound['inputs_sha256']:
            need(bound['inputs_sha256'][str(p)] == sha(p), 'B would overwrite existing digest')
        bound['inputs_sha256'][str(p)] = sha(p)
    bound.update(kind='S3_PREPARATION_B_NOT_AUTHORIZATION',
        sealed_at=datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),
        preparation_A_path=str(a), preparation_A_sha256=a_sha,
        zero_audit_status='PASSED', zero_audit_path=str(receipt), zero_audit_sha256=sha(receipt),
        actual_audit_run_ids=[r['run_id'] for r in completed['records']],
        actual_formal_run_ids=[], actual_initialized_frames_read=4,
        independent_zero_review_path=str(acceptance), independent_zero_review_sha256=sha(acceptance),
        ZERO_STEP_INDEPENDENT_REVIEW_PASS=True, ZERO_STEP_GEOMETRY_PASS=True,
        simulation_authorized=False, formal_simulation_authorized=False,
        native_zero_step_authorized=False, initial_field_readback_authorized=False,
        performance_time_stepping_authorized=False,
        approved_runs=[], approved_run_ids=[], approved_audit_run_ids=[],
        prepared_runs=original['prepared_runs'], prepared_run_ids=original['prepared_run_ids'],
        zero_prepared_runs=original['zero_prepared_runs'])
    need(all(bound['inputs_sha256'].get(p) == h for p, h in released['inputs_sha256'].items()), 'B drops release inputs')
    with patch('subprocess.Popen', side_effect=AssertionError('no subprocess while sealing B')):
        stage.verify_zero_receipt(bound)
    save(b, bound)
    digest = sha(b)
    with b.with_suffix('.sha256').open('x') as f:
        f.write(digest + '\n')
    observed = stage.verify_seal(b, digest)
    with patch('subprocess.Popen', side_effect=AssertionError('no subprocess checking B')) as proc:
        stage.verify_zero_receipt(observed)
        refusal = {}
        for name, validator in [('formal', stage.validate_formal_authority),
                                ('zero', stage.validate_zero_authority)]:
            try:
                validator(observed)
            except EvidenceError as e:
                refusal[name] = str(e)
            else:
                raise AssertionError('B unexpectedly grants ' + name + ' authority')
        stdout, stderr = io.StringIO(), io.StringIO()
        with patch.object(sys, 'argv', ['run_S3.py', '--release', str(b), '--release-sha256', digest]), \
             contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = run_S3.main()
        need(code == 0 and not proc.called, 'B readonly entry failed/created subprocess')
    inspection = json.loads(stdout.getvalue())
    need(inspection['solver_executed'] is False and inspection['simulation_authorized'] is False and
         inspection['zero_audit_status'] == 'PASSED', 'B default inspection status')
    need(all(sha(p) == h for p, h in protected.items()), 'original file changed while sealing')
    need(sha(a) == a_sha and sha(release) == release_sha, 'old contract changed')
    need(all(sha(p) == h for p, h in observed['inputs_sha256'].items()), 'new B input drift')
    stage.require_pristine(observed['prepared_runs'])
    need(not (CASE / 'launch_attempts').exists() and not (CASE / 'analysis_results').exists(), 'formal work started')
    verification = dict(verified_at=datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),
        B_path=str(b), B_sha256=digest, B_kind=observed['kind'],
        bound_inputs=len(observed['inputs_sha256']), original_A_inputs_preserved=len(original['inputs_sha256']),
        original_zero_release_inputs_preserved=len(released['inputs_sha256']),
        protected_existing_files_unchanged=len(protected),
        actual_audit_run_ids=observed['actual_audit_run_ids'], actual_formal_run_ids=[],
        ZERO_STEP_INDEPENDENT_REVIEW_PASS=True, ZERO_STEP_GEOMETRY_PASS=True,
        independent_review_directly_bound=True,
        approved_runs=[], approved_run_ids=[], approved_audit_run_ids=[],
        simulation_authorized=False, formal_simulation_authorized=False,
        native_zero_step_authorized=False, initial_field_readback_authorized=False,
        performance_time_stepping_authorized=False,
        readonly_controller_exit_code=code, readonly_controller_output=inspection,
        readonly_controller_stderr=stderr.getvalue(), readonly_controller_subprocess_calls=0,
        closed_authority_refusals=refusal, native_solver_calls_this_task=0,
        saved_VTK_field_rereads_this_task=4, time_steps_this_task=0, builds_this_task=0,
        source_or_config_changes=0, formal_started=False, performance_started=False,
        next_stage_started=False, NUMERICAL_GATE='NOT_EVALUATED', geometry_PASS=None,
        RESULT_PASS=False, reference_qualified=False, MODEL_COMPARISON='NOT_EVALUATED',
        physical_validation='NOT_EVALUATED', submission_ready=False)
    save(OUT / 'B_seal_verification.json', verification)
    print(json.dumps(verification, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()

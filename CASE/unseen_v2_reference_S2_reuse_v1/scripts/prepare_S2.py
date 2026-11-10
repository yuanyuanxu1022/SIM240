"""Materialize identities and closed seals only. Never executes native code."""
from pathlib import Path
import argparse
import json
import sys

CASE = Path(__file__).resolve().parents[1]
ROOT = CASE.parents[1]
CHECKER = CASE.parent / 'unseen_v2_reference_checker_S2_reuse_v1'
S1 = CASE.parent / 'unseen_v2_reference_S1_a1_v1'
sys.path.insert(0, str(CHECKER / 'analysis'))
from evidence import need, sha, kv, save, exact_parameters
from stage_s2 import CASES, RUN_IDS, MODES, AUDIT_ID, REVISION, RESOURCES, ELF_SHA, verify_zero_receipt


def write_identity(run, rid, ident, mode, original):
    run.mkdir(parents=True, exist_ok=False)
    config = dict(original, mode=mode, run_id=rid, output_directory=str(run))
    path = run / 'run_config.txt'
    path.write_text(''.join(k + '=' + v + '\n' for k, v in config.items()))
    (run / 'run_manifest.txt').write_text(f'run_id={rid}\nmode={mode}\n')
    return dict(run_id=rid, planned_case_id=ident, mode=mode, run_config_path=str(path),
                run_config_sha256=sha(path), output_directory=str(run))


def materialize():
    plan = CASE / 'evidence/identity_plan.json'
    need(not plan.exists(), 'identity plan exists; refusing overwrite')
    formal, zero = [], []
    for rid, ident in zip(RUN_IDS, CASES):
        template = ROOT / 'docs/reports/Unseen_V2_reference_protocol_20261101/describe_only_templates' / (ident + '.txt')
        original = kv(template)
        formal.append(write_identity(CASE / 'runs' / rid / 'steady', rid, ident, 'steady', original))
        for mode in MODES:
            aid = f'ZERO_{AUDIT_ID}_{ident}_{mode}'
            run = CASE / 'audits' / AUDIT_ID / ident / mode
            zero.append(write_identity(run, aid, ident, mode, original))
    save(plan, dict(simulation_authorized=False, native_zero_step_authorized=False,
                    prepared_runs=formal, zero_prepared_runs=zero))


def view():
    prior = S1 / 'evidence/S1_launch_release_A1_v1_20261102_01.json'
    previous = json.loads(prior.read_text())
    need(sha(prior) == 'd15d044729fe398afcd6996346d7b260dd22a0930037da653d98e76ed5966d68', 'S1 release changed')
    envpath = S1 / 'evidence/build_environment.json'
    env = json.loads(envpath.read_text())
    need(sha(env['binary_path']) == ELF_SHA, 'original S1 ELF drift')
    planpath = CASE / 'evidence/identity_plan.json'
    plan = json.loads(planpath.read_text())
    anchor = CHECKER / 's2_revision/anchor.json'
    revision = json.loads(anchor.read_text())
    # Keep the genuine historical build closure; add only new-stage provenance.
    inputs = dict(previous['inputs_sha256'])
    for folder in (CASE/'scripts', CHECKER/'analysis', CHECKER/'common', CHECKER/'revision',
                   CHECKER/'s1_revision', CHECKER/'s2_revision', CHECKER/'tests'):
        for path in folder.rglob('*'):
            if path.is_file() and '__pycache__' not in path.parts:
                inputs[str(path)] = sha(path)
    for item in revision['frozen_inputs']:
        inputs[item['path']] = item['sha256']
    for item in revision['diffs'].values():
        inputs[item['path']] = item['sha256']
        inputs[item['baseline_path']] = item['baseline_sha256']
    for p in (prior, planpath, CASE/'evidence/adoption.json', CASE/'README.md', CHECKER/'README.md'):
        inputs[str(p)] = sha(p)
    for r in plan['prepared_runs'] + plan['zero_prepared_runs']:
        for p in (Path(r['run_config_path']), Path(r['output_directory'])/'run_manifest.txt'):
            inputs[str(p)] = sha(p)
    return dict(protocol_id='URV-v1', schema_version='URV-EXEC-1.1', stage='S2_REG_GRID',
        addendum_id=REVISION, kind='S2_PREPARATION_A_NOT_AUTHORIZATION',
        simulation_authorized=False, native_zero_step_authorized=False,
        performance_time_stepping_authorized=False, preparation_only_build=False,
        approved_run_ids=[], approved_runs=[], actual_formal_run_ids=[], actual_audit_run_ids=[],
        prepared_runs=plan['prepared_runs'], prepared_run_ids=[r['run_id'] for r in plan['prepared_runs']],
        zero_prepared_runs=plan['zero_prepared_runs'], resources=RESOURCES,
        launch_authorization=dict(user_explicitly_authorized=False, user_instruction_verbatim=None),
        author_external_data_history_confirmation=previous['author_external_data_history_confirmation'],
        author_reply_file=previous['author_reply_file'], author_reply_sha256=previous['author_reply_sha256'],
        external_history_independently_verified=False,
        author_confirmation_scope='author-declared nonuse for h60/d80 and h30/d80 only; no external independent audit',
        provenance=previous['provenance'],
        source_revision=dict(id=REVISION, anchor=str(anchor), sha256=sha(anchor)), inputs_sha256=inputs,
        h75_regression_references={}, density_capture='NOT_APPLICABLE_S0_ONLY',
        exact_parameters={r['planned_case_id']: exact_parameters(kv(r['run_config_path'])) for r in plan['prepared_runs']},
        NUMERICAL_GATE='NOT_EVALUATED', RESULT_PASS=False, geometry_PASS=None,
        REFERENCE_QUALIFIED_FOR_CASE=False, reference_qualified=False, strict_error_bound_established=False,
        MODEL_COMPARISON='NOT_EVALUATED', physical_validation='NOT_EVALUATED', submission_ready=False,
        zero_audit_status='NOT_EXECUTED', performance_status='NOT_EXECUTED', next_stage_started=False, F04='OPEN_OUT_OF_SCOPE')


def seal():
    from stage_s2 import verify_seal
    from contracts import verify_provenance
    data = view()
    need(all(sha(p) == h for p, h in data['inputs_sha256'].items()), 'cannot seal drifted input')
    verify_provenance(data)
    output = CASE / 'evidence/preparation_A.json'
    save(output, data)
    verify_seal(output, sha(output))
    print(json.dumps(dict(preparation_A_sha256=sha(output), inputs=len(data['inputs_sha256']), solver_executed=False)))


def finalize_zero():
    # This action can only seal existing real audit results; never grants launch authority.
    from stage_s2 import verify_seal
    original = CASE / 'evidence/preparation_A.json'
    data = verify_seal(original, sha(original))
    zero = CASE / 'audits' / AUDIT_ID / 'verification.json'
    need(zero.is_file(), 'real S2 zero audit absent; no B seal')
    evidence = json.loads(zero.read_text())
    need(evidence['preparation_A_sha256'] == sha(original), 'zero/preparation mismatch')
    for p in [original, *zero.parent.rglob('*')]:
        if p.is_file():
            need(not p.is_symlink(), 'audit output symlink refused')
            data['inputs_sha256'][str(p)] = sha(p)
    # Preserve the separate actual audit release and its user authorization record.
    audit_release = Path(evidence['audit_release_path'])
    need(sha(audit_release) == evidence['audit_release_sha256'], 'audit release drift')
    audit_bound = json.loads(audit_release.read_text())
    for p, h in audit_bound['inputs_sha256'].items():
        need(sha(p) == h, 'audit-authorized input drift')
        need(p not in data['inputs_sha256'] or data['inputs_sha256'][p] == h, 'conflicting audit inputs')
        data['inputs_sha256'][p] = h
    data['inputs_sha256'][str(audit_release)] = sha(audit_release)
    data.update(kind='S2_PREPARATION_B_NOT_AUTHORIZATION', zero_audit_status='PASSED',
                zero_audit_path=str(zero), zero_audit_sha256=sha(zero),
                preparation_A_path=str(original), preparation_A_sha256=sha(original))
    verify_zero_receipt(data)
    save(CASE / 'evidence/preparation_B.json', data)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('action', choices=['identities', 'seal', 'finalize-zero'])
    args = ap.parse_args()
    {'identities': materialize, 'seal': seal, 'finalize-zero': finalize_zero}[args.action]()

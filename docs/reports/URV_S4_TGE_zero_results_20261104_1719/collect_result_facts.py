"""Collect the 3+1 zero-audit result facts. Read-only on CASE."""
import json, hashlib, re
from pathlib import Path

ROOT = Path('/home/dell/yuanyuanxu/SIM240')
CASE = ROOT / 'CASE/unseen_v2_reference_S4_tge_v1'
R = ROOT / 'docs/reports/URV_S4_TGE_zero_results_20261104_1719'
AUD = CASE / 'audits/URV_S4_TGE_ZERO_v1_20261104_01'
SUB = AUD / 'URV1_U_THIN_T_dx0p625_a100000_SUPPLEMENT'


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def read(p):
    p = Path(p)
    return p.read_text(errors='replace') if p.is_file() else None


precheck_log = read(SUB / 'precheck/run.log') or ''
facts = {
    'kind': 'ZERO_3_PLUS_1_EXECUTION_RESULT',
    'recorded_at': '2026-11-04T17:19+08:00',
    'release_path': str(CASE / 'evidence/S4_TGE_zero_launch_release_v1_20261104_01.json'),
    'release_sha256': 'd654196816e36fe97638c079c26a498e6203db8a01bd492042ecb1320c314949',
    'release_seal_still_valid': True,
    'release_inputs_checked': 3710,
    'controller_log_verbatim': read(CASE / 'S4_TGE_zero_controller_v1_20261104_01.log'),
    'attempt_directory': str(CASE / 'audit_attempts/d654196816e36fe97638c079c26a498e6203db8a01bd492042ecb1320c314949'),
    'attempt_directory_files': [],
    'attempt_budget_consumed': True,

    'describe': {
        'status': 'PASS',
        'independent_exit_code': 0,
        'actual_time_steps': 0,
        'elapsed_seconds': 0.36747822095640004,
        'timed_out': False,
        'resource_stop_reason': None,
        'effective_config_written': True,
        'direction_field': 'perpendicular',
        'direction_consistent_with_old_T_run': True,
        'dx_m': 6.2500000000000001e-10,
        'nx': 384, 'ny': 384,
        'window_steps': 10368, 'maximum_steps': 1486848,
        'note': 'describe returns before lattice construction, so it exercises config only.'
    },
    'precheck': {
        'status': 'FAIL_RESOURCE_CAPACITY',
        'independent_exit_code': -6,
        'signal': 'SIGABRT',
        'timed_out': False,
        'resource_stop_reason': None,
        'elapsed_seconds': 10.417795438028406,
        'solver_wall_cap_seconds': 300,
        'raised': 'std::bad_alloc',
        'aborted_by_controller': False,
        'interpretation': ('The process aborted itself inside the adopted 8 GiB per-process address-space cap. '
                           'This is neither a wall-clock timeout nor a controller resource stop; the controller only '
                           'observed a non-zero exit and stopped the batch.'),
        'failure_phase': 'before any collide-and-stream call; during lattice/geometry setup',
        'collide_and_stream_calls': 0,
        'result_txt_written': False,
        'boundary_audit_written': False,
    },
    'initialize': {
        'status': 'NOT_ATTEMPTED',
        'reason': 'fail-stop after precheck; the controller never reached the third call',
        'directory_files': ['run_config.txt', 'run_manifest.txt'],
    },
    'initial_field_read': {
        'status': 'NOT_ATTEMPTED',
        'reason': 'depends on initialize, which never ran',
    },
    'formal_steady_run': {
        'status': 'NOT_STARTED',
        'directory_files': ['run_config.txt', 'run_manifest.txt'],
    },
    'verification_receipt_written': (AUD / 'verification.json').exists(),
    'progress_records': [p.name for p in sorted((AUD / 'progress').glob('*.json'))],
    'native_calls_completed': 1,
    'native_calls_attempted': 2,
    'VTK_calls': 0,
    'actual_time_steps': 0,
    'software_tests_rerun': 0,
    'builds': 0,
    'retry_performed': False,

    'node_scaling_evidence': {
        'dx_0p625_fluid_nodes': 16515072,
        'dx_0p625_domain_cells': 384 * 384 * 180,
        'dx_1p25_fluid_nodes_from_old_accepted_run': 2064384,
        'dx_1p25_domain_cells': 192 * 192 * 90,
        'node_ratio': 8.0,
        'old_1p25_ran_under_same_8GiB_cap_and_passed': True,
        'old_1p25_steps_completed': 12537,
        'old_1p25_elapsed_seconds': 4326.036,
        'implication': ('Memory grows roughly with node count. The accepted 1.25 nm run fitted inside the same 8 GiB '
                        'cap; the 0.625 nm case has exactly 8x the fluid nodes and exceeded that cap during setup. '
                        'Therefore the required address space is materially above 8 GiB, plausibly in the high teens '
                        'to mid twenties of GiB. The exact figure is NOT measured and must not be quoted as if it were.'),
    },
    'scientific_status': {
        'NUMERICAL_GATE': 'NOT_EVALUATED', 'RESULT_PASS': False, 'geometry_PASS': None,
        'original_S4_stage_accepted': False, 'reference_qualified': False,
        'MODEL_COMPARISON': 'NOT_EVALUATED', 'physical_validation': 'NOT_EVALUATED',
        'submission_ready': False, 'zero_step_audit_passed': False,
    },
    'what_this_does_not_prove': [
        'It does not prove the 0.625 nm case is physically wrong or numerically invalid; no physics was evaluated.',
        'It does not give a measured peak RSS; only that 8 GiB of address space is insufficient.',
        'It does not change any historical FAIL, any threshold, or any accepted S4 record.',
        'It does not authorize a larger cap, a retry, performance calibration, or a formal run.'],
}
facts['attempt_directory_files'] = sorted(p.name for p in (CASE / 'audit_attempts/d654196816e36fe97638c079c26a498e6203db8a01bd492042ecb1320c314949').iterdir())
(R / 'result_facts.json').write_text(json.dumps(facts, indent=2, ensure_ascii=False) + '\n')
files = sorted(p for p in R.iterdir() if p.is_file() and p.name != 'document_manifest.json')
(R / 'document_manifest.json').write_text(
    json.dumps({p.name: sha(p) for p in files}, indent=2, ensure_ascii=False) + '\n')
print(json.dumps(facts, indent=2, ensure_ascii=False))

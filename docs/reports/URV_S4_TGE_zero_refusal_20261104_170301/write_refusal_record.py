"""Record the 2026-11-04 17:01 precondition refusal. Read-only on CASE."""
import json, hashlib
from pathlib import Path

R = Path('/home/dell/yuanyuanxu/SIM240/docs/reports/URV_S4_TGE_zero_refusal_20261104_170301')
CASE = Path('/home/dell/yuanyuanxu/SIM240/CASE/unseen_v2_reference_S4_tge_v1')


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


dirs = {
    'formal_steady': 'runs/URV_S4_T_dx0p625_TGE_v1_20261104_01/steady',
    'zero_describe': 'audits/URV_S4_TGE_ZERO_v1_20261104_01/URV1_U_THIN_T_dx0p625_a100000_SUPPLEMENT/describe',
    'zero_precheck': 'audits/URV_S4_TGE_ZERO_v1_20261104_01/URV1_U_THIN_T_dx0p625_a100000_SUPPLEMENT/precheck',
    'zero_initialize': 'audits/URV_S4_TGE_ZERO_v1_20261104_01/URV1_U_THIN_T_dx0p625_a100000_SUPPLEMENT/initialize',
}
log = CASE / 'S4_TGE_zero_controller_v1_20261104_01.log'
rec = {
    'kind': 'ZERO_LAUNCH_PRECONDITION_REFUSAL_RECORD',
    'attempt_at': '2026-11-04T17:01:51+08:00',
    'release_path': str(CASE / 'evidence/S4_TGE_zero_launch_release_v1_20261104_01.json'),
    'release_sha256': 'd654196816e36fe97638c079c26a498e6203db8a01bd492042ecb1320c314949',
    'user_terminal_memory_readings_GiB': [11.35, 11.22],
    'adopted_floor_GiB': 12.0,
    'shortfall_GiB': round(12.0 - 11.22, 3),
    'refusal_message': log.read_text().strip(),
    'controller_log_path': str(log),
    'controller_log_sha256': sha(log),
    'refusal_stage': 'resources(initial) inside execute(), before attempt directory creation',
    'writes_before_refusal': 0,
    'attempt_directory_created': False,
    'audit_attempts_exists': (CASE / 'audit_attempts').exists(),
    'zero_verification_exists': (CASE / 'audits/URV_S4_TGE_ZERO_v1_20261104_01/verification.json').exists(),
    'directory_contents': {k: sorted(p.name for p in (CASE / v).iterdir()) for k, v in dirs.items()},
    'native_calls': 0,
    'VTK_calls': 0,
    'actual_time_steps': 0,
    'solver_executed': False,
    'input_closure': 3710,
    'input_closure_unchanged': True,
    'release_reseal_verified_after_refusal': True,
    'tmux_session_persisted': False,
    'correction_to_prior_report': [
        'The issuance-time statement "no urv/pvpython solver process, tmux has no session" came from a process view restricted to the assistant sandbox namespace: ps sees 3 processes while /proc/loadavg reports about 3700 threads, and the tmux socket is equally invisible there.',
        'The user then ran tmux successfully on the real host, which proves that statement was a false negative and must not be used as evidence of a clean host or a free session name.',
        'The /proc/meminfo readings remain valid: the user own terminal returned 11.35 and 11.22 GiB, consistent with the assistant readings in the same minutes.',
        'This record changes no threshold and no authorization; the adopted 12 GiB floor stays exactly as adopted.'],
    'interpretation': ('Configured safety refusal, not a numerical FAIL and not a completed zero audit. No attempt budget was consumed '
                       'because no attempt directory was written; repeating the same command without freeing host memory reproduces the refusal.'),
    'next_action': ('Free at least about 0.8 GiB of host memory, re-run the read-only check until MemAvailable >= 12.00 GiB, '
                    'then the user may run the same single launch command once.'),
}
(R / 'refusal_record.json').write_text(json.dumps(rec, indent=2, ensure_ascii=False) + '\n')
files = sorted(p for p in R.iterdir() if p.is_file() and p.name != 'document_manifest.json')
(R / 'document_manifest.json').write_text(
    json.dumps({p.name: sha(p) for p in files}, indent=2, ensure_ascii=False) + '\n')
print(json.dumps(rec, indent=2, ensure_ascii=False))

"""Create the explicitly approved single-item packet; never launch a worker."""
import copy
from datetime import datetime
import json
from pathlib import Path
import shlex
import subprocess
import sys
from zoneinfo import ZoneInfo

OUT = Path(__file__).resolve().parent
REPO = OUT.parents[2]
P = REPO / 'CASE/D_series/D4_variable_groove_transport_20261023/reference_backend_min18_20261025/pilot_record_v3_1_20261026'
REVIEW = REPO / 'docs/reports/D4_N8_permission_review_20261026'
QUESTION = '你的表述是“收到明确运行授权后”。为避免把准备请求误记为运行批准，请确认：是否批准仅运行首项 B0MIN_MMS_mixed_N8，采用已审查的600秒工作进程限时（另加5秒终止宽限）、4GiB内存、512MiB工作卷、最多2000次迭代，失败即停、不重试、不运行第二项，并由你亲自执行后台启动命令？'
ANSWER = '明确批准上述唯一首项和固定预算，由我启动'


def main():
    sys.path.insert(0, str(P))
    import common
    import runner
    import precheck_layout
    now = datetime.now(ZoneInfo('Asia/Shanghai')).isoformat()
    # Recheck the reviewed inputs without recreating probes, meshes or matrices.
    reviewed = common.read_json(REVIEW / 'review_inputs_sha256.json')
    for name, expected in reviewed.items():
        path = REPO / name
        assert path.is_file() and common.sha(path) == expected, name
    old = common.read_json(REVIEW / 'candidate_contract_NOT_AUTHORIZED.json')
    common.validate(old, execution=False)
    c = copy.deepcopy(old)
    c.update(status='APPROVED_DIAGNOSTIC_ONLY', authorized_to_execute=True,
             approval=dict(authorization_text=QUESTION + '\n用户明确答复：' + ANSWER,
                           protocol_sha256=common.sha(P / 'DIAGNOSTIC_CONTRACT.md')))
    assert {k for k in c if c[k] != old[k]} == {'status', 'authorized_to_execute', 'approval'}
    resources = runner.prerequisites(c)  # Read-only; never call runner.run/main.
    assert not (Path(c['cgroup_parent']) / ('sim240-' + c['run_id'])).exists()
    layout = {key: precheck_layout.inspect(Path(c[key]).parent) for key in ('work_dir', 'record_dir')}
    for key, item in layout.items():
        assert item['canonical'] and item['is_directory'] and item['writable']
        assert item['uid'] == item['gid'] == 1000 and item['mode'] == '0o700'
    assert 'noexec' not in layout['work_dir']['mount']['options']
    session = 'd4-n8-diag-20261026-v1'
    check = subprocess.run(['/usr/bin/tmux', 'has-session', '-t', '=' + session], capture_output=True, text=True)
    assert check.returncode == 1, (check.returncode, check.stdout, check.stderr)
    contract = OUT / 'APPROVED_DIAGNOSTIC_ONLY.json'
    common.write_json(contract, c)
    common.validate(common.read_json(contract), execution=True)
    # Parent logs/exit remain available even when preconditions reject before record creation.
    invocation = shlex.join(['/usr/bin/python3', '-B', str(P / 'runner.py'), '--contract', str(contract), '--execute'])
    inner = ('cd ' + shlex.quote(str(REPO)) + ' && ' + invocation
             + ' > ' + shlex.quote(str(OUT / 'launcher.stdout.log'))
             + ' 2> ' + shlex.quote(str(OUT / 'launcher.stderr.log'))
             + '; launch_exit=$?; printf \'%s\\n\' "$launch_exit" > '
             + shlex.quote(str(OUT / 'launcher.exit_code.txt')) + '; exit "$launch_exit"')
    command = shlex.join(['/usr/bin/tmux', 'new-session', '-d', '-s', session, inner])
    subprocess.run(['/bin/bash', '-n', '-c', command], check=True)
    with (OUT / 'launch_command.txt').open('x') as f:
        f.write(command + '\n')
    common.write_json(OUT / 'approval_evidence.json', dict(
        checked_at_Asia_Shanghai=now, authorization_question=QUESTION, authorization_answer=ANSWER,
        authorization_source='Current conversation explicit user reply',
        approved_contract_sha256=common.sha(contract), approved_contract_digest=common.digest(c),
        candidate_file_sha256=common.sha(REVIEW / 'candidate_contract_NOT_AUTHORIZED.json'),
        protocol_sha256=c['approval']['protocol_sha256'], source_lock_sha256=c['source_lock_sha256'],
        reviewed_input_count=len(reviewed), reviewed_inputs_unchanged=True,
        changed_contract_fields=['approval', 'authorized_to_execute', 'status'],
        live_resources=resources, layout=layout, run_paths_and_cgroup_unused=True,
        tmux_session=session, tmux_session_absent=True, command_bash_syntax_pass=True,
        launch_command_sha256=common.sha(OUT / 'launch_command.txt'),
        real_solver_called=False, backend_imported=False, child_group_created=False,
        actual_run_id=None, reserved_contract_run_id=c['run_id'], status='APPROVED_PREPARED_NOT_STARTED',
        NUMERICAL_GATE='NOT_EVALUATED', RESULT_PASS=False, geometry_PASS=None, prediction_permission='HOLD'))
    # runner imports records/NumPy for inventories; no PDE backend is imported.
    assert not any(k.split('.')[0] in {'petsc4py', 'dolfinx', 'dolfinx_mpc', 'ufl'} for k in sys.modules)
    print(json.dumps(dict(status='APPROVED_PREPARED_NOT_STARTED', reviewed_inputs=len(reviewed),
                         MemAvailable_GiB=resources['MemAvailable_bytes']/1024**3,
                         record_available_GiB=resources['record_disk_available_bytes']/1024**3,
                         contract=str(contract), actual_run_id=None), indent=2))


if __name__ == '__main__':
    main()

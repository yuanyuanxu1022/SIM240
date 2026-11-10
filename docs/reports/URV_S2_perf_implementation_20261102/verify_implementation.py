"""Final preparation-only verification. No subprocess/native/VTK calls."""
from pathlib import Path
import ast
import contextlib
import hashlib
import io
import json
import sys
from unittest.mock import patch

ROOT=Path('/home/dell/yuanyuanxu/SIM240')
CASE=ROOT/'CASE/unseen_v2_reference_S2_perf_v1'
OUT=Path(__file__).resolve().parent
EXPECTED='806c40a62620396faf6795008a81b25f7f9bf4182869b6df4422b575b2b08030'


def sha(path):
    digest=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(1<<20),b''):digest.update(block)
    return digest.hexdigest()


def main():
    sys.path[:0]=[str(CASE/'analysis'),str(CASE/'scripts')]
    import perf_contract as c
    import run_perf as runner
    seal=CASE/'evidence/preparation_perf.json'
    assert sha(seal)==EXPECTED==seal.with_suffix('.json.sha256').read_text().strip()
    data=c.verify(seal,EXPECTED)
    assert data['kind']==c.PREP
    assert len(data['inputs_sha256'])==2055
    c.pristine(data['prepared_benchmark_runs'])
    argv=['run_perf.py','--release',str(seal),'--expected-sha256',EXPECTED]
    with patch('subprocess.Popen',side_effect=AssertionError('NO REAL PROCESS ALLOWED')),\
         patch.object(sys,'argv',argv),contextlib.redirect_stdout(io.StringIO()):
        assert runner.main()==0
    with patch('subprocess.Popen',side_effect=AssertionError('NO REAL PROCESS ALLOWED')),\
         patch.object(sys,'argv',argv+['--execute']):
        try:runner.main()
        except ValueError as exc:assert 'cannot launch' in str(exc)
        else:raise AssertionError('preparation launched')
    for name in ['performance_attempt.json','performance_execution.lock','performance_batch_result.json']:
        assert not (CASE/name).exists()
    protected=json.loads((OUT/'protected_inputs_before.json').read_text())
    assert len(protected)==3086
    assert all(Path(p).is_file() and sha(p)==h for p,h in protected.items())
    for name in ['SIM240_AI_CONTEXT.md','AI_HANDOFF_20261015.md']:
        before=(OUT/('before_'+name)).read_text();current=(ROOT/'docs/reports'/name).read_text()
        assert before.split('\n## ',2)[2]==current.split('\n## ',2)[2]
        assert 'S2性能接入已隔离实现' in current.split('\n## ',2)[1]
    sources=list(CASE.rglob('*.py'))
    for path in sources:ast.parse(path.read_text())
    assert len(sources)==5 and not list(CASE.rglob('__pycache__'))
    assert not list(CASE.rglob('*.cpp')) and not (CASE/'build').exists()
    tests=json.loads((OUT/'software_checks.json').read_text())
    assert tests['SOFTWARE_CHECK_PASS'] is True and tests['tests_run']==49
    assert (OUT/'software_tests.log').read_text().rstrip().endswith('OK')
    # Parent and closed-preparation reports must agree on the actual input closure.
    closed=json.loads((OUT/'closed_seal_checks.json').read_text())
    assert closed['preparation_sha256']==EXPECTED and closed['preparation_inputs']==2055
    result=dict(checked_at=c.now(),SOFTWARE_PREPARATION_VERIFICATION_PASS=True,
        scientific_or_native_acceptance=False,preparation_sha256=EXPECTED,preparation_inputs=2055,
        old_protected_files_checked=len(protected),old_file_drift=[],B_sha256=c.B_SHA,
        original_ELF_sha256=c.ELF_SHA,tests_passed=49,syntax_AST_source_files=5,
        preparation_readonly_pass=True,preparation_execute_rejected=True,
        execution_permissions_closed=True,all_approved_and_actual_ids_empty=True,
        actual_native_calls=0,actual_VTK_reads=0,builds=0,actual_time_steps=0,
        actual_benchmark_run_ids=[],launch_contract_generated=False,start_command_delivered=False,
        no_launch_markers=True,new_CASE_files={str(p.relative_to(CASE)):sha(p)
            for p in CASE.rglob('*') if p.is_file()},historical_state_tails_unchanged=True,
        **c.SCIENCE)
    (OUT/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    manifest={str(p.relative_to(OUT)):sha(p) for p in OUT.rglob('*')
              if p.is_file() and p.name!='report_manifest.json'}
    (OUT/'report_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='new_CASE_files'},ensure_ascii=False))


if __name__=='__main__':main()

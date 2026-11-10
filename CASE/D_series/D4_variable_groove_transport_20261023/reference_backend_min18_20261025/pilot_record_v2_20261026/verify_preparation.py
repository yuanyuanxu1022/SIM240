"""Independent stdlib-only evidence and protected-source verification."""
import ast
import csv
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
REPO=ROOT.parents[3]


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()


def main():
    lock=json.loads((HERE/'source_lock.json').read_text())
    changed=[p for p,v in lock['files'].items() if not Path(p).is_file() or sha(p)!=v]
    protected=json.loads((REPO/'docs/reports/G4_derivation_source_audit_20261025/protected_inputs.json').read_text())
    old_changed=[p for p,v in protected.items() if not Path(p).is_file() or sha(p)!=v]
    terminal=json.loads((REPO/'docs/reports/D4_reference_terminal_review_20261026/review_inputs_sha256.json').read_text())
    review_changed=[p for p,v in terminal.items() if sha(REPO/p)!=v]
    rows=list(csv.DictReader((ROOT/'protocol/benchmarks18.csv').open(encoding='utf-8-sig')))
    assert len(rows)==18 and all(r['authorized_to_execute']=='False' and not r['actual_run_id'] for r in rows)
    c=json.loads((HERE/'contract_template.json').read_text())
    assert c['authorized_to_execute'] is False and c['approval'] is None
    assert c['source_lock_sha256']==sha(HERE/'source_lock.json')
    parsed={p.name:ast.parse(p.read_text()) for p in HERE.glob('*.py')}
    assert len([n for n in ast.walk(parsed['solver.py']) if isinstance(n,ast.Call)
                and isinstance(n.func,ast.Attribute) and n.func.attr=='solve'])==1
    assembly=(HERE/'assembly.py').read_text()
    assert 'rhs_before_projection = rhs.copy()' in assembly
    assert '"execution_contract": contract' in assembly
    assert 'plan["execution_authorized"] =' not in assembly
    tests=json.loads((HERE/'evidence/test_summary.json').read_text())
    assert tests['status']=='PASS_NO_PDE_TESTS' and not tests['forbidden_backend_modules_loaded']
    assert not changed and not old_changed and not review_changed
    out=dict(status='PASS_PREPARATION_ONLY',syntax_modules=len(parsed),source_binding_files=len(lock['files']),
        source_changed=changed,protected_paths=len(protected),protected_changed=old_changed,
        terminal_review_inputs=len(terminal),terminal_inputs_changed=review_changed,
        original_plan_execution_false_rows=len(rows),new_template_execution=False,
        no_PDE_tests=tests,real_backend_end_to_end='NOT_TESTED',
        actual_capped_work_volume='NOT_PROVISIONED_BY_THIS_TASK',formal_run_id=None,
        NUMERICAL_GATE='NOT_EVALUATED',RESULT_PASS=False,geometry_PASS=None,prediction_permission='HOLD')
    path=HERE/'evidence/independent_preparation.json'
    path.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out))


if __name__=='__main__':main()

"""Synthetic metadata workflow only; numeric callback is a stub, not a C result."""
import importlib.util
import io
import json
import sys
import tempfile
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import binding as b
import analyze_completed_c as analyzer
from test_binding import ContractTests

def main():
    ContractTests.setUpClass();test=ContractTests()
    bound,protocol=b.verify_binding();calls=[]
    with tempfile.TemporaryDirectory(prefix='sim240_c_acceptance_e2e_') as temp:
        root=Path(temp);manifest=test.fixture(root)
        (root/'execution_binding.json').write_bytes(b.binding_path().read_bytes())
        manifest['execution_binding_sha256']=b.sha(root/'execution_binding.json')
        (b.paths(root)[0]/'manifest.json').write_text(json.dumps(manifest))
        def numeric_stub(case,path,thresholds):
            assert thresholds==protocol['thresholds']
            assert case==protocol['stages']['c'][len(calls)]
            calls.append(case['id'])
            return dict(id=case['id'],initialization_only=False,implementation_contract_pass=True,
                        physical_amount_drift_within_budget=len(calls)!=2,safety_pass=True,
                        synthetic_callback_only=True)
        output=root/'synthetic_analysis'
        with patch.object(analyzer,'ROOT',root),patch.object(analyzer,'binding_path',lambda:root/'execution_binding.json'),\
             patch.object(analyzer,'post_mismatches',lambda bound,bs:b.post_mismatches(bound,bs,root=root)),\
             patch.dict(sys.modules,{'analyze_c':SimpleNamespace(analyze_case=numeric_stub)}),\
             patch.object(sys,'argv',['analyze_completed_c.py','--output',str(output)]),redirect_stdout(io.StringIO()):
            code=analyzer.main()
        verdict=json.loads((output/'verdict.json').read_text())
        assert code==1 and verdict['implementation_contract_pass'] is True
        assert verdict['physical_amount_drift_within_budget'] is False and verdict['complete_C_contract_pass'] is False
        assert calls==[c['id'] for c in protocol['stages']['c']]
        for k,v in b.GATES.items():assert verdict[k]==v
        assert verdict['execution_binding_sha256']==b.sha(b.binding_path())
    assert all(not p.exists() for p in b.paths())
    print(json.dumps(dict(scope='SYNTHETIC METADATA WORKFLOW ONLY; frozen numerical callback replaced by an explicit stub',
        exit_from_budget_failure=code,called_case_ids=calls,physical_budget_failure_not_waived=True,
        execution_binding_roundtrip=True,formal_Gates_unchanged=True,real_C_results_created=False,
        solver_invocations=0,temporary_data_removed=True),indent=2))

if __name__=='__main__':main()

"""Pin existing accepted N8 metadata/inventory, never load field arrays."""
import hashlib
import json
from pathlib import Path

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[2]
CODE=ROOT/'CASE/D_series/D4_variable_groove_transport_20261023/reference_backend_min18_20261025/offline_extractor_revision_v2_20261026'

def canonical(x):return json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def digest(x):return hashlib.sha256(canonical(x)).hexdigest()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    record=Path('/home/dell/yuanyuanxu/SIM240_runtime_records/reference_pilot_n8_20261026/D4_N8_diag_v3_1_20261026_v1')
    cert=ROOT/'docs/reports/D4_N8_acceptance_20261026/verdict.json'
    index=ROOT/'docs/reports/D4_N8_acceptance_20261026/input_sha256.json'
    accepted=json.loads(index.read_text());verdict=json.loads(cert.read_text())
    assert verdict['status']=='ONE_N8_DIAGNOSTIC_ACCEPTED' and verdict['run_id']==record.name
    expected=json.loads((OUT/'source_manifest.json').read_text())['N8_record_files']
    assert len(expected)==48 and all(accepted.get(p)==h for p,h in expected.items())
    assert {str(p) for p in record.rglob('*') if p.is_file()}==set(expected)
    assert all(sha(Path(p))==h for p,h in expected.items())
    inventory={str(Path(p).relative_to(record)):h for p,h in expected.items()}
    c=json.loads((record/'contract.json').read_text())
    spec=CODE/'ANALYSIS_SPEC.md'
    code_files={str(CODE/n):sha(CODE/n) for n in ('numerics.py','extractor.py','binding.py','analysis_record.py')}
    binding=dict(schema_version=2,kind='EXISTING_N8_ANALYSIS_DRAFT_REAL_DISABLED',
        status='DRAFT_NOT_APPROVED_NOT_EXECUTABLE',analysis_id='DRAFT_D4_N8_OFFLINE_v2_20261026_v1',
        source_run_id=record.name,planned_id='B0MIN_MMS_mixed_N8',source_contract_sha256=digest(c),
        record_root=str(record),acceptance_path=str(cert),acceptance_inputs_path=str(index),
        acceptance_sha256=sha(cert),acceptance_inputs_sha256=sha(index),inventory=inventory,
        inventory_sha256=digest(inventory),code_sha256=code_files,spec_path=str(spec),spec_sha256=sha(spec),
        analysis_output='/home/dell/yuanyuanxu/SIM240_runtime_records/reference_n8_analysis_v2_20261026/D4_N8_offline_v2_20261026_v1',
        approval=None,solver_authorized=False,real_extraction_authorized=False)
    trust={k:binding[k] for k in ('acceptance_sha256','acceptance_inputs_sha256','inventory_sha256','code_sha256','spec_sha256')}
    trust['binding_sha256']=digest(binding)
    for name,data in [('real_N8_binding_DRAFT.json',binding),('real_N8_trust_anchor_DRAFT.json',trust),
          ('real_binding_static_check.json',dict(status='PINNED_DRAFT_STATIC_CHECK_PASS',
           original_accepted_input_entries=len(accepted),record_inventory_entries=len(inventory),
           all_48_entries_covered_by_original_acceptance=True,source_arrays_loaded=False,
           real_extraction_executed=False,solver_started=False,trust_sha256=digest(trust),
           real_output_directory_created=False,source_run_id=record.name))]:
        with (OUT/name).open('x') as f:json.dump(data,f,indent=2);f.write('\n')
    assert not Path(binding['analysis_output']).exists()
    print('PINNED_DRAFT_STATIC_CHECK_PASS: all 48 raw files anchored to original independent acceptance; no field arrays loaded.')

if __name__=='__main__':main()

"""Pinned provenance and record-schema reader; synthetic preparation only."""
from io import BytesIO
import hashlib
import json
from pathlib import Path
import numpy as np
from numerics import Rejected, require

REAL_ROOT=Path('/home/dell/yuanyuanxu/SIM240_runtime_records/reference_pilot_n8_20261026/D4_N8_diag_v3_1_20261026_v1')
SYNTHETIC='SYNTHETIC_EXTRACTOR_REVISION_NOT_RESULT'
ARRAY_NAMES={
    'system': {'cell_pressure_mixed_dofs','cell_velocity_mixed_dofs','csr_indices','csr_indptr','csr_values','pressure_null_vector','rhs_after','rhs_before'},
    'solution': {'algebraic_solution_before_backsub','mesh_coordinates_hat','mesh_triangles','periodic_coefficients','periodic_master_dofs','periodic_slave_dofs','pressure_area_weights_hat2','pressure_coordinates_hat','pressure_raw_P1','pressure_reconstructed_dof_indices','pressure_zero_mean_P1','reconstructed_solution','velocity_dof_components','velocity_dof_coordinates_hat','velocity_reconstructed_dof_indices','velocity_reconstructed_values','wall_velocity_dof_indices'}
}


def canonical(obj):return json.dumps(obj,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def digest(obj):return hashlib.sha256(canonical(obj)).hexdigest()
def blob_sha(blob):return hashlib.sha256(blob).hexdigest()
def read_json(path):return json.loads(Path(path).read_text())


def verify_binding(binding,trust):
    """Trust is a separately pinned anchor, never regenerated from input files."""
    require(digest(binding)==trust['binding_sha256'],'BINDING_ANCHOR_MISMATCH')
    require(binding['acceptance_sha256']==trust['acceptance_sha256'] and
            binding['acceptance_inputs_sha256']==trust['acceptance_inputs_sha256'] and
            binding['inventory_sha256']==trust['inventory_sha256'],'TRUST_CHAIN_MISMATCH')
    require(binding['code_sha256']==trust['code_sha256'] and binding['spec_sha256']==trust['spec_sha256'],'IMPLEMENTATION_BINDING')
    require(binding['solver_authorized'] is False and binding['real_extraction_authorized'] is False,'EXECUTION_MUST_REMAIN_CLOSED')
    for name,h in binding['code_sha256'].items():
        require(blob_sha(Path(name).read_bytes())==h,'EXTRACTOR_CODE_CHANGED')
    require(blob_sha(Path(binding['spec_path']).read_bytes())==binding['spec_sha256'],'ANALYSIS_SPEC_CHANGED')
    return True


def snapshot(root):
    result={}
    for p in root.rglob('*'):
        require(not p.is_symlink(),'SYMLINK_IN_RECORD')
        if p.is_file():
            rel=str(p.relative_to(root));result[rel]=p.read_bytes()
    return result


def verify_snapshot(blobs,expected):
    require(set(blobs)==set(expected),'RECORD_INVENTORY_CHANGED')
    require(all(blob_sha(blob)==expected[name] for name,blob in blobs.items()),'RECORD_BYTES_CHANGED')


def read_synthetic_record(binding,trust,*,after_load_test_hook=None):
    """Exercise the actual contract/capture/manifest schema with artificial data.

    Real root and its descendants/ancestors are rejected before any file read.
    All payloads are decoded from the same hashed byte snapshot, not reopened.
    """
    require(binding.get('kind')==SYNTHETIC,'SYNTHETIC_BINDING_REQUIRED')
    root=Path(binding['record_root']).resolve()
    require(not root.is_relative_to(REAL_ROOT) and not REAL_ROOT.is_relative_to(root),'REAL_ROOT_FORBIDDEN')
    require(root.is_dir() and not Path(binding['record_root']).is_symlink(),'RECORD_ROOT_INVALID')
    verify_binding(binding,trust)
    marker=read_json(root/'synthetic_marker.json')
    require(marker=={'kind':SYNTHETIC,'not_a_PDE_solution':True},'SYNTHETIC_MARKER_REQUIRED')
    cert_blob=Path(binding['acceptance_path']).read_bytes()
    index_blob=Path(binding['acceptance_inputs_path']).read_bytes()
    require(blob_sha(cert_blob)==trust['acceptance_sha256'],'ACCEPTANCE_CERTIFICATE_CHANGED')
    require(blob_sha(index_blob)==trust['acceptance_inputs_sha256'],'ACCEPTANCE_INPUT_LIST_CHANGED')
    cert=json.loads(cert_blob);accepted_inputs=json.loads(index_blob)
    require(cert['status']=='SYNTHETIC_DIAGNOSTIC_ACCEPTED_NOT_RESULT' and cert['kind']==SYNTHETIC,'CERTIFICATE_STATUS_OR_KIND')
    require(cert['run_id']==binding['source_run_id'],'ACCEPTANCE_RUN_ID')
    expected=binding['inventory']
    require(len(expected)==48 and digest(expected)==trust['inventory_sha256'],'PINNED_INVENTORY_DIGEST')
    for rel,h in expected.items():
        p=Path(rel)
        require(not p.is_absolute() and '..' not in p.parts,'UNSAFE_RELATIVE_PATH')
        require(accepted_inputs.get(str(root/rel))==h,'INVENTORY_NOT_IN_ACCEPTED_INPUTS')
    blobs=snapshot(root);verify_snapshot(blobs,expected)
    contract=json.loads(blobs['contract.json']);capture=json.loads(blobs['capture_manifest.json'])
    completion=json.loads(blobs['archive/worker_completion.json'])
    require(contract['run_id']==capture['run_id']==completion['run_id']==binding['source_run_id'],'RUN_BINDING')
    require(contract['planned_id']==binding['planned_id']=='B0MIN_MMS_mixed_N8','CASE_BINDING')
    require(contract['record_dir']==str(root),'RECORD_PATH_BINDING')
    require(capture['archive_status']=='ARCHIVE_COMPLETE' and capture['independent_exit_code']==0
            and capture['inputs_unchanged'] is True and capture['children_stopped'] is True,'INCOMPLETE_PARENT_RECORD')
    require(completion['status']=='SOLVER_EXITED_UNVERIFIED','COMPLETION_STATUS')
    contract_sha=digest(contract)
    require(capture['contract_sha256']==completion['contract_sha256']==contract_sha,'CONTRACT_BINDING')
    require(contract_sha==binding['source_contract_sha256'],'SOURCE_CONTRACT_DIGEST')
    groups={}
    for group in ('solution','system'):
        m=json.loads(blobs['archive/'+group+'/manifest.json'])
        require(set(m['files'])=={x+'.npy' for x in ARRAY_NAMES[group]},'ARRAY_NAME_SET')
        require(m['metadata']['contract_sha256']==contract_sha and
                m['metadata']['record_kind']=='SYNTHETIC_DIAGNOSTIC_UNVERIFIED_NOT_RESULT','ARRAY_MANIFEST_BINDING')
        groups[group]={}
        for name,e in m['files'].items():
            require(Path(name).name==name,'UNSAFE_ARRAY_NAME')
            blob=blobs['archive/'+group+'/'+name]
            require(blob_sha(blob)==e['sha256'],'ARRAY_SHA_MISMATCH')
            a=np.load(BytesIO(blob),allow_pickle=False)
            require(list(a.shape)==e['shape'] and a.dtype.str==e['dtype'],'ARRAY_SCHEMA')
            require(a.dtype.kind in 'fiu' and np.all(np.isfinite(a)),'NONFINITE_OR_NONNUMERIC_ARRAY')
            groups[group][name[:-4]]=a
    if after_load_test_hook is not None:after_load_test_hook(root)
    verify_snapshot(snapshot(root),expected)
    # The acceptance anchors must remain stable throughout the read as well.
    require(blob_sha(Path(binding['acceptance_path']).read_bytes())==trust['acceptance_sha256'],'ACCEPTANCE_CHANGED_DURING_READ')
    require(blob_sha(Path(binding['acceptance_inputs_path']).read_bytes())==trust['acceptance_inputs_sha256'],'ACCEPTANCE_INPUTS_CHANGED_DURING_READ')
    return groups['solution'],groups['system']

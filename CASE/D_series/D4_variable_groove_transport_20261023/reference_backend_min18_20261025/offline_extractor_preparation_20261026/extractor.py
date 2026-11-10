"""Prepared independent extractor API. Real-record entry is deliberately closed.

The preparation task exercises extract_arrays only with synthetic arrays.
No CLI path can open an N8 record, invoke a solver or return a physical PASS.
"""
import hashlib
import json
from pathlib import Path
import numpy as np
from numerics import Field, Rejected, QUADRATURE_CHANGE_TARGET, require


REAL_RECORD_EXTRACTION_ENABLED = False


def extract_real_record(record_dir, expected_files=None):
    # Before Path resolution, reads, imports, or changes to any input.
    if not REAL_RECORD_EXTRACTION_ENABLED:
        raise Rejected('REAL_RECORD_EXTRACTION_CLOSED_PREPARATION_ONLY')
    # Dormant adapter: a future reviewed analysis version must bind the complete
    # inventory independently. The old solver approval is never an analysis permit.
    require(isinstance(expected_files,dict) and len(expected_files)==48,'EXACT_N8_INVENTORY_REQUIRED')
    root=Path(record_dir).resolve()
    expected_root='/home/dell/yuanyuanxu/SIM240_runtime_records/reference_pilot_n8_20261026/D4_N8_diag_v3_1_20261026_v1'
    require(str(root)==expected_root,'ONLY_BOUND_EXISTING_N8_SUPPORTED')
    paths={str(p.resolve()):p for p in root.rglob('*') if p.is_file()}
    require(set(paths)==set(expected_files),'RECORD_INVENTORY_CHANGED')
    def verify():
        for name,p in paths.items():
            require(not p.is_symlink() and not any(q.is_symlink() for q in p.parents if q!=root.parent),'SYMLINK_INPUT')
            require(hashlib.sha256(p.read_bytes()).hexdigest()==expected_files[name],'RECORD_HASH_CHANGED')
    verify()
    contract=json.loads((root/'contract.json').read_text())
    capture=json.loads((root/'capture_manifest.json').read_text())
    completion=json.loads((root/'archive/worker_completion.json').read_text())
    run='D4_N8_diag_v3_1_20261026_v1'
    digest=hashlib.sha256(json.dumps(contract,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
    require(contract['run_id']==capture['run_id']==completion['run_id']==run,'RUN_BINDING')
    require(contract['planned_id']=='B0MIN_MMS_mixed_N8' and contract['record_dir']==str(root),'CASE_BINDING')
    require(capture['archive_status']=='ARCHIVE_COMPLETE' and capture['independent_exit_code']==0
            and capture['inputs_unchanged'] is True and capture['children_stopped'] is True,'INCOMPLETE_PARENT_RECORD')
    require(capture['contract_sha256']==completion['contract_sha256']==digest,'CONTRACT_BINDING')
    groups={}
    for group,count in (('system',8),('solution',17)):
        m=json.loads((root/'archive'/group/'manifest.json').read_text())
        require(len(m['files'])==count and m['metadata']['contract_sha256']==digest
                and m['metadata']['record_kind']=='REAL_DIAGNOSTIC_UNVERIFIED','ARRAY_MANIFEST_BINDING')
        groups[group]={}
        for name,entry in m['files'].items():
            require(Path(name).name==name and name.endswith('.npy'),'UNSAFE_ARRAY_NAME')
            p=root/'archive'/group/name
            require(hashlib.sha256(p.read_bytes()).hexdigest()==entry['sha256'],'ARRAY_HASH_MISMATCH')
            value=np.load(p,allow_pickle=False)
            require(list(value.shape)==entry['shape'] and value.dtype.str==entry['dtype'],'ARRAY_SCHEMA')
            groups[group][name[:-4]]=value
    result=extract_arrays(groups['solution'],groups['system'])
    result.update(run_id=run,analysis_kind='REAL_N8_SAVED_FIELD_POSTPROCESS_UNACCEPTED',
                  input_inventory_sha256=hashlib.sha256(json.dumps(expected_files,sort_keys=True).encode()).hexdigest())
    verify()
    return result


def extract_arrays(solution, system, kind='mms_mixed', include_algebra=True):
    field=Field(solution,system)
    low=field.integrate(kind,8);high=field.integrate(kind,12)
    scale=max(high['D'],abs(high['W']))
    changes={}
    for key in ('D','Dsym','W','Pdiv','div_integral','div2'):
        changes[key]=abs(high[key]-low[key])/scale if scale>0 else None
    changes['J_hat']=abs(high['J_hat']-low['J_hat'])/abs(high['J_hat']) if high['J_hat']!=0 else None
    for prefix in ('u','p'):
        denom=high[prefix+'_exact2']
        changes[prefix+'_error2']=abs(high[prefix+'_error2']-low[prefix+'_error2'])/denom if denom>0 else None
        changes[prefix+'_exact2']=abs(high[prefix+'_exact2']-low[prefix+'_exact2'])/denom if denom>0 else None
        key=prefix+'_L2_relative'
        changes[key]=abs(high[key]-low[key]) if high[key] is not None else None
    for key in ('eta_energy_weak','eta_pressure_work','eta_energy_direct','eta_div'):
        changes[key]=abs(high[key]-low[key]) if high[key] is not None else None
    finite_changes=[v for v in changes.values() if v is not None]
    flux=field.flux_report(high['J_hat'])
    algebra=field.weak_residual(high['weak_pressure_moments_unconstrained']) if include_algebra else None
    return dict(status='OFFLINE_METRICS_UNACCEPTED',kind=kind,trace=field.trace_report(),
                low_rule=low,high_rule=high,flux=flux,algebra=algebra,
                quadrature=dict(rule='Duffy tensor Gauss-Legendre, 8 and 12 points per axis; not assembly degrees',
                                normalized_changes=changes,candidate_change_target=QUADRATURE_CHANGE_TARGET,
                                within_candidate_change_target=all(v<=QUADRATURE_CHANGE_TARGET for v in finite_changes),
                                rigorous_quadrature_error_bound=False),
                NUMERICAL_GATE='NOT_EVALUATED',RESULT_PASS=False,geometry_PASS=None,
                reference_qualified=False,strict_error_bound_established=False)


def read_synthetic_bundle(directory):
    """Strict synthetic fixture transport only; not a real archive adapter."""
    root=Path(directory).resolve()
    manifest=json.loads((root/'fixture_manifest.json').read_text())
    require(manifest.get('kind')=='SYNTHETIC_EXTRACTOR_FIXTURE_NOT_RESULT','SYNTHETIC_MARKER_REQUIRED')
    require(manifest.get('run_id') is None,'REAL_RUN_ID_FORBIDDEN')
    require(set(manifest)=={'kind','run_id','groups'},'FIXTURE_SCHEMA')
    groups={}
    for group,files in manifest['groups'].items():
        require(group in ('solution','system'),'FIXTURE_GROUP')
        groups[group]={}
        for name,entry in files.items():
            require(name.endswith('.npy') and Path(name).name==name,'UNSAFE_ARRAY_NAME')
            p=root/group/name
            require(not p.is_symlink() and not p.parent.is_symlink(),'SYMLINK_INPUT')
            require(p.resolve().is_relative_to(root) and p.stat().st_size==entry['size_bytes'],'ARRAY_SIZE_OR_PATH')
            require(hashlib.sha256(p.read_bytes()).hexdigest()==entry['sha256'],'ARRAY_HASH_MISMATCH')
            value=np.load(p,allow_pickle=False)
            require(list(value.shape)==entry['shape'] and value.dtype.str==entry['dtype'],'ARRAY_SCHEMA')
            require(value.dtype.kind in 'fiu' and np.all(np.isfinite(value)),'UNSAFE_ARRAY_DATA')
            groups[group][name[:-4]]=value
    require(set(groups)=={'solution','system'},'MISSING_GROUP')
    return groups['solution'],groups['system']


if __name__=='__main__':
    raise SystemExit('PREPARATION ONLY: real-record extraction disabled; use synthetic fixture tests.')

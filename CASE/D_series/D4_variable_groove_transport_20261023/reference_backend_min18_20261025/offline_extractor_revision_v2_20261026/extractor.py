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


def extract_real_record(*args, **kwargs):
    # Real data processing has no execution route in this preparation version.
    raise Rejected('REAL_RECORD_EXTRACTION_CLOSED_PREPARATION_ONLY')


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

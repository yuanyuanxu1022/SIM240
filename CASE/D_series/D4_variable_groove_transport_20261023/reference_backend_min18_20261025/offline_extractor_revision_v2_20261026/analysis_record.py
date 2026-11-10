"""Unique synthetic analysis artifacts, predeclared software checks, fail stop.

No real record route. Consistency checks are not physical Gates or error bounds.
"""
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import traceback
from binding import (SYNTHETIC,REAL_ROOT,canonical,digest,blob_sha,verify_binding,
                     read_synthetic_record,snapshot,verify_snapshot)
from extractor import extract_arrays
from numerics import require

SOFTWARE_LIMIT=2e-11
DECISION_BAND=64*2.220446049250313e-16
QUAD_LIMIT=1e-8


def compare(value,limit,band=DECISION_BAND):
    if value is None:return 'MISSING'
    if not isinstance(value,(int,float)) or not (float('-inf')<value<float('inf')):return 'INVALID'
    if value<0:return 'INVALID'
    if abs(value-limit)<=band:return 'NEAR_THRESHOLD'
    return 'PASS' if value<limit else 'FAIL'


def checks(metrics):
    # Force strict JSON serialization first, including nested intermediate values.
    canonical(metrics)
    t=metrics['trace'];a=metrics['algebra'];hi=metrics['high_rule'];q=metrics['quadrature']
    scale=max(t['velocity_scale'],t['pressure_scale'])
    def scaled(x):return x/scale if x is not None and scale>0 else None
    values={
      'periodic_coverage': 'PASS' if t['periodic_slave_indices_complete'] else 'FAIL',
      'wall_coverage': 'PASS' if t['wall_indices_complete'] else 'FAIL',
      'reconstruction':compare(scaled(t['reconstruction_max_abs']),SOFTWARE_LIMIT),
      'periodic_trace':compare(scaled(t['periodic_max_abs']),SOFTWARE_LIMIT),
      'wall_trace':compare(scaled(t['wall_max_abs']),SOFTWARE_LIMIT),
      'pressure_integral_vs_CSR':compare(a['independent_c_vs_matrix_residual'],SOFTWARE_LIMIT) if a else 'MISSING',
      'finite_positive_driven_field':'PASS' if hi['positive_driven_field'] else 'FAIL'
    }
    for name,value in q['normalized_changes'].items():
        if value is None and hi['p_exact2']==0 and name.startswith('p_'):continue
        values['postprocess_quadrature_'+name]=compare(value,QUAD_LIMIT)
    status='PASS' if all(s=='PASS' for s in values.values()) else ('INCONCLUSIVE' if all(s in {'PASS','NEAR_THRESHOLD'} for s in values.values()) else 'FAIL')
    return dict(status='SOFTWARE_CONSISTENCY_'+status,items=values,
                normalized_software_limit=SOFTWARE_LIMIT,decision_band=DECISION_BAND,
                band_is_rigorous_error_bound=False,physical_thresholds_activated=False,
                energy_values_recorded_without_new_gate=True,NUMERICAL_GATE='NOT_EVALUATED',
                RESULT_PASS=False,geometry_PASS=None,reference_qualified=False)


def write_unique(path,data):
    with path.open('xb') as f:f.write(canonical(data)+b'\n')


def run_synthetic_analysis(binding,trust,*,after_load_test_hook=None):
    require(binding.get('kind')==SYNTHETIC,'SYNTHETIC_ANALYSIS_REQUIRED')
    verify_binding(binding,trust)
    root=Path(binding['record_root']).resolve();out=Path(binding['analysis_output']).absolute()
    require(not out.is_relative_to(root) and not root.is_relative_to(out),'OUTPUT_OVERLAPS_INPUT')
    require(not out.is_relative_to(REAL_ROOT) and not REAL_ROOT.is_relative_to(out),'REAL_OUTPUT_FORBIDDEN')
    require(not out.exists() and out.parent.is_dir() and not out.parent.is_symlink(),'UNIQUE_EXISTING_PARENT_REQUIRED')
    out.mkdir()
    def event(stage,**extra):
        with (out/'events.jsonl').open('a') as f:
            f.write(json.dumps(dict(at=datetime.now(timezone.utc).isoformat(),stage=stage,**extra),allow_nan=False)+'\n')
    write_unique(out/'input_binding.json',binding)
    event('STARTED',analysis_id=binding['analysis_id'],kind=SYNTHETIC)
    code=2;failure=None
    try:
        s,a=read_synthetic_record(binding,trust,after_load_test_hook=after_load_test_hook)
        event('INPUTS_VERIFIED')
        metrics=extract_arrays(s,a)
        result=checks(metrics)
        # Recheck immutable inputs after all numerical postprocessing, before success.
        verify_snapshot(snapshot(root),binding['inventory'])
        verify_binding(binding,trust)
        require(blob_sha(Path(binding['acceptance_path']).read_bytes())==trust['acceptance_sha256'],'ACCEPTANCE_CHANGED_AFTER_ANALYSIS')
        require(blob_sha(Path(binding['acceptance_inputs_path']).read_bytes())==trust['acceptance_inputs_sha256'],'ACCEPTANCE_INPUTS_CHANGED_AFTER_ANALYSIS')
        write_unique(out/'metrics.json',metrics);write_unique(out/'checks.json',result)
        if result['status']=='SOFTWARE_CONSISTENCY_PASS':code=0
        elif result['status']=='SOFTWARE_CONSISTENCY_INCONCLUSIVE':code=3
        else:code=4
        event('METRICS_RECORDED',software_status=result['status'])
    except Exception as e:
        failure=dict(type=type(e).__name__,message=str(e))
        write_unique(out/'failure.json',dict(**failure,traceback=traceback.format_exc()))
        event('FAILED',**failure)
    status='SYNTHETIC_METRICS_RECORDED' if code==0 else ('SYNTHETIC_ANALYSIS_INCONCLUSIVE' if code==3 else 'SYNTHETIC_ANALYSIS_FAILED')
    write_unique(out/'status.json',dict(status=status,analysis_id=binding['analysis_id'],kind=SYNTHETIC,
                 source_run_id=binding['source_run_id'],exit_code=code,failure=failure,
                 input_inventory_sha256=binding['inventory_sha256'],binding_sha256=digest(binding),
                 actual_N8_processed=False,reference_qualified=False,RESULT_PASS=False,
                 NUMERICAL_GATE='NOT_EVALUATED',geometry_PASS=None))
    with (out/'analysis.exit_code').open('x') as f:f.write(str(code)+'\n')
    event('ENDED',exit_code=code,status=status)
    files={p.name:blob_sha(p.read_bytes()) for p in out.iterdir() if p.is_file()}
    write_unique(out/'output_manifest.json',dict(files=files,kind=SYNTHETIC,not_self_hashed=True))
    return code,out

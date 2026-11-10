"""Audit existing 1.25 nm files only. No solver or native mode calls."""
from pathlib import Path
import csv
import hashlib
import json
import math
import re
import sys
import numpy as np

REPORT=Path(__file__).resolve().parent
REPO=REPORT.parents[2]
PACKAGE=REPO/'outputs/URV_S4_1p25_data_20261104_234955'
RAW=PACKAGE/'01_raw_server/steady'
SOURCE=PACKAGE/'03_provenance/checker_analysis'
RID='URV_S4_T_dx1p25_TGESRV_v1_20261104_01'
DIGEST='758f13deecec0a26ae309e982cbcadfb1aa9bf198e58513292bd2114df49631d'
CHECKS=[]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def check(name, value, observed, expected, source):
    CHECKS.append(dict(check=name,PASS=bool(value),observed=observed,expected=expected,source=source))
    if not value:
        raise ValueError(name+': '+str(observed))


def save(name,value):
    (REPORT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n')


def main():
    manifest=json.loads((PACKAGE/'05_inventory/MANIFEST.json').read_text())
    for item in manifest['files']:
        assert sha(PACKAGE/item['path'])==item['sha256'],item['path']
    check('package_manifest',True,len(manifest['files']),'all payload hashes unchanged','05_inventory/MANIFEST.json')
    completion=json.loads((RAW/'completion.json').read_text())
    for name,digest in completion['output_sha256'].items():
        assert sha(RAW/name)==digest,name
    check('raw_outputs',True,len(completion['output_sha256']),37,'completion.json:output_sha256')
    seal=PACKAGE/'03_provenance/server_evidence/S4_TGE_SERVER_formal_launch_release_v1_20261104_01.json'
    check('release_digest',sha(seal)==DIGEST,sha(seal),DIGEST,str(seal.relative_to(PACKAGE)))
    bound=json.loads(seal.read_text())
    check('input_before_after',completion['inputs_before_sha256']==completion['inputs_after_sha256']==bound['inputs_sha256'],
          len(bound['inputs_sha256']),1437,'completion.json and release input maps')
    for name in ['read_fields.py','evidence.py','check_formal_server.py','server_stage.py']:
        key='CASE/unseen_v2_reference_checker_S4_tge_server_v1/analysis/'+name
        check('source_'+name,sha(SOURCE/name)==bound['inputs_sha256'][key],sha(SOURCE/name),bound['inputs_sha256'][key],key)
    sys.path.insert(0,str(SOURCE))
    import check_formal_server as frozen
    from evidence import kv,exact_parameters
    cfg=kv(RAW/'run_config.txt')
    result,geometry,comp=frozen.run_checks(RAW,cfg,DIGEST)
    scalar=frozen.scalars(RAW,cfg)
    acceptance=json.loads((PACKAGE/'02_acceptance/server/acceptance.json').read_text())
    check('scalar_receipt_match',scalar==acceptance['scalar'],scalar,acceptance['scalar'],'frozen scalars vs acceptance.json')
    check('geometry_receipt_match',geometry==acceptance['geometry'],geometry,acceptance['geometry'],'analytic geometry vs acceptance.json')
    check('completion_digest',sha(RAW/'completion.json')==acceptance['completion_sha256'],sha(RAW/'completion.json'),acceptance['completion_sha256'],'acceptance.json')
    check('independent_exit',(RAW/'exit_code.txt').read_text().strip()=='0' and comp['independent_process_exit_code']==0,
          comp['independent_process_exit_code'],0,'exit_code.txt and completion.json')
    check('no_timeout_or_resource_stop',comp['timed_out'] is False and comp['resource_stop_reason'] is None,
          [comp['timed_out'],comp['resource_stop_reason']],[False,None],'completion.json')

    data=np.genfromtxt(RAW/'diagnostics.csv',delimiter=',',names=True)
    p=exact_parameters(cfg)
    final=data[-p['window']:]
    values=final['Jx'];mean=math.fsum(float(x) for x in values)/p['window']
    std=math.sqrt(math.fsum((float(x)-mean)**2 for x in values)/(p['window']-1))/abs(mean)
    span=(float(max(values))-float(min(values)))/abs(mean)
    last_k=p['nu']*float(data['Jx'][-1])/p['a']
    mean_k=p['nu']*mean/p['a']
    check('independent_K',last_k==scalar['K_m3'],last_k,scalar['K_m3'],'raw last Jx and config')
    check('window_sample_std',math.isclose(std,scalar['final_window_std'],rel_tol=1e-12),std,scalar['final_window_std'],'raw final window, ddof=1')
    check('window_span',math.isclose(span,scalar['final_window_span'],rel_tol=1e-12),span,scalar['final_window_span'],'raw final window')
    check('stop_is_convergence_not_cap',scalar['steps']<p['cap'] and result['converged']=='true',
          dict(steps=scalar['steps'],maximum_steps=p['cap'],converged=result['converged']),
          'first acceptable window before maximum_steps','result.txt + full windows recomputation')
    reference=PACKAGE/'04_local_reference/local_1p25_acceptance.json'
    local=json.loads(reference.read_text())
    difference=last_k/local['scalar']['K_m3']-1
    check('build_equivalence',abs(difference)<=1e-6,difference,'abs(relative)<=1e-6','local_1p25_acceptance.json')

    local_raw=REPO/'CASE/unseen_v2_reference_S4_reuse_v1/runs/URV_S4_T_dx1p25_reuse_v1_20261103_01/steady/diagnostics.csv'
    other=np.genfromtxt(local_raw,delimiter=',',names=True)
    check('local_trajectory_schema_shape',other.dtype.names==data.dtype.names and other.shape==data.shape,
          [len(other),len(data)],'matching columns and all 12538 rows','saved local diagnostics.csv')
    trajectory={}
    for name in data.dtype.names:
        a=data[name];b=other[name]
        trajectory[name]=dict(exact_equal=bool(np.array_equal(a,b)),max_absolute_difference=float(np.max(np.abs(a-b))))
    check('local_trajectory_numeric_match',all(v['exact_equal'] for v in trajectory.values()),
          trajectory,'all parsed binary64 numbers equal for this run','server and local raw diagnostics')

    log=(RAW/'run.log').read_text()
    peak=int(re.search(r'Maximum resident set size \(kbytes\):\s*(\d+)',log).group(1))*1024
    check('peak_RSS',peak==comp['peak_rss_bytes'],peak,comp['peak_rss_bytes'],'run.log time-v and completion.json')
    check('throughput',scalar['steps']/comp['elapsed_seconds']==acceptance['measured_performance']['steps_per_second'],
          scalar['steps']/comp['elapsed_seconds'],acceptance['measured_performance']['steps_per_second'],'steps/elapsed')
    swap=int(re.search(r'Swaps:\s*(\d+)',log).group(1))
    diagnostics=dict(rows=len(data),window_steps=p['window'],full_windows=len(data)-p['window']+1,
                     first_accepted_step=scalar['steps'],maximum_steps=p['cap'],scalar=scalar,
                     final_section_relative_difference=float(data['section_relative_difference'][-1]),
                     last_step_K_m3=last_k,window_mean_K_m3=mean_k,
                     window_mean_relative_to_last=mean_k/last_k-1,
                     initial_Jx=float(data['Jx'][0]),expected_initial_Jx=p['H']*p['a']*p['dt']/2,
                     all_finite=bool(all(np.isfinite(data[n]).all() for n in data.dtype.names)),
                     local_server_trajectory=trajectory,
                     local_server_csv_bytes_equal=sha(local_raw)==sha(RAW/'diagnostics.csv'))
    gates=json.loads((REPO/'CASE/unseen_v2_reference_checker_S4_reuse_v1/common/acceptance_spec.json').read_text())
    rows=[
        ['corrected_mass_max',scalar['corrected_mass_max'],'<',gates['per_run']['compensated_mass_relative_strict']],
        ['ledger_agreement_max',scalar['ledger_agreement_max'],'<=',gates['per_run']['ledger_agreement_max']],
        ['max_density_deviation',scalar['max_density_deviation'],'<=',gates['per_run']['density_deviation_max']],
        ['max_Mach',scalar['max_Mach'],'<',gates['per_run']['Mach_strict']],
        ['final_section_relative_difference',diagnostics['final_section_relative_difference'],'<=',gates['per_run']['section_relative_max']],
        ['final_window_std',std,'<=',gates['per_run']['window_relative_sample_std_max']],
        ['final_window_span',span,'<=',gates['per_run']['window_relative_span_max']],
        ['Re_H',scalar['Re_H'],'<=',gates['new_physics_guards']['Re_H_max']],
        ['build_relative_difference',abs(difference),'<=',1e-6],
    ]
    with (REPORT/'numerical_checks.csv').open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.writer(f);writer.writerow(['metric','recomputed_value','operator','frozen_limit','PASS'])
        for key,value,operator,limit in rows:
            ok=value<limit if operator=='<' else value<=limit
            assert ok;writer.writerow([key,value,operator,limit,ok])
    save('diagnostic_audit.json',diagnostics)
    save('checks.json',CHECKS)
    save('summary_before_field_audit.json',dict(run_id=RID,checks_pass=True,geometry=geometry,
        numerical=scalar,BUILD_EQUIVALENCE_PASS=True,relative_K_difference=difference,
        measured=dict(elapsed_seconds=comp['elapsed_seconds'],peak_rss_GiB=peak/1024**3,
                      steps_per_second=scalar['steps']/comp['elapsed_seconds'],time_v_swaps=swap),
        NUMERICAL_GATE_native=result['NUMERICAL_GATE'],NUMERICAL_GATE_acceptance=acceptance['NUMERICAL_GATE'],
        RESULT_PASS=acceptance['RESULT_PASS'],geometry_PASS=acceptance['geometry_PASS'],
        S4_STAGE_ACCEPTED=False,reference_qualified=False,MODEL_COMPARISON='NOT_EVALUATED',
        physical_validation='NOT_EVALUATED',submission_ready=False))
    print(json.dumps(dict(checks=len(CHECKS),all_PASS=True,K_m3=last_k,
                         trajectory_exact_equal=True,CSV_bytes_equal=diagnostics['local_server_csv_bytes_equal'],
                         steps=scalar['steps'],maximum_steps=p['cap']),indent=2))


if __name__=='__main__':
    main()

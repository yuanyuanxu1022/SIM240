#!/usr/bin/env python3
"""Inspect all configs, geometry/q on unique meshes, and six initial output sets.
All solver modes used here have zero collideAndStream calls.
"""
from pathlib import Path
import datetime
import importlib.util
import json
import math
import shutil
import sys

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('runner',ROOT/'tools/run_case.py')
run=importlib.util.module_from_spec(spec);spec.loader.exec_module(run)


def available_memory():
    values=dict(line.split(':',1) for line in Path('/proc/meminfo').read_text().splitlines())
    return int(values['MemAvailable'].split()[0])*1024


def main():
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    base=ROOT/'evidence'/('preflight_'+stamp)
    base.mkdir()
    shutil.copy2(ROOT/'tools/run_case.py',base/'run_case_snapshot.py')
    rows=run.candidates();described=[];geometries=[];initial=[];skipped=[]
    for r in rows:
        out,code=run.launch(r,'describe',base,'describe')
        assert code==0,(r['planned_case_id'],code)
        c=run.kv(out/'effective_config.txt')
        for key,field,scale in [('h_m','h_nm',1e-9),('d_m','d_nm',1e-9),('w_m','w_nm',1e-9),('Lx_m','P_nm',1e-9),('Ly_m','Ly_nm',1e-9),('dx_m','dx_nm',1e-9)]:
            assert abs(float(c[key])-float(r[field])*scale)<1e-20
        assert abs(float(c['dt_s'])/float(r['dt_s'])-1)<1e-12
        assert abs(float(c['nominal_volume_m3'])/(float(r['fluid_volume_nm3'])*1e-27)-1)<1e-12
        dt=float(c['dt_s']);h=float(c['h_m']);d=float(c['d_m']);nu=float(r['nu_m2_s'])
        assert int(c['window_steps'])==math.ceil(.75*h*h/(nu*dt)-1e-9)
        assert int(c['maximum_steps'])==math.ceil(8*(h+d)**2/(nu*dt)-1e-9)
        described.append(str(out.relative_to(ROOT)))
    unique={}
    for r in rows:
        key=tuple(r[n] for n in ['h_nm','d_nm','w_nm','P_nm','Ly_nm','dx_nm'])
        unique.setdefault(key,r)
    for index,r in enumerate(sorted(unique.values(),key=lambda r:int(r['fluid_nodes_expected']))):
        # A conservative guard based on the measured 1,990,656-node zero-step probe.
        expected=int(r['fluid_nodes_expected'])*1409444*1024/1990656*1.15+1.5*1024**3
        available=available_memory()
        if expected>available:
            skipped.append({'case':r['planned_case_id'],'estimated_required_bytes':expected,'available_bytes':available})
            continue
        out,code=run.launch(r,'precheck',base,'geometry',timeout=90)
        assert code==0,(r['planned_case_id'],code)
        result=run.kv(out/'result.txt');audit=run.kv(out/'boundary_audit.txt')
        assert result['collide_and_stream_calls']=='0' and result['formal_simulation']=='false'
        assert all(result[k]=='true' for k in ['geometry_PASS','converter_PASS','q_audit_PASS'])
        assert int(result['fluid_nodes'])==int(r['fluid_nodes_expected'])
        assert int(result['candidate_links'])==int(result['installed_links'])
        assert float(result['q_min'])==float(result['q_max'])==.5
        assert result['fallback_count']=='0' and audit['unresolved_link_count']=='0'
        geometries.append({'row':r['planned_case_id'],'output':str(out.relative_to(ROOT)),
                           'nodes':int(result['fluid_nodes']),
                           'resources':json.loads((out/'resource_usage.json').read_text())})
        print(f'zero-step geometry {index+1}/{len(unique)}: {r["planned_case_id"]}',flush=True)
    for r in rows:
        if not ((r['role']=='new_dev' and (r['w_nm'],r['d_nm']) in [('60','25'),('240','120')]) or
                (r['role']=='smooth' and r['h_nm']=='75')):continue
        out,code=run.launch(r,'initialize',base,'initial_fields')
        assert code==0,(r['planned_case_id'],code)
        result=run.kv(out/'result.txt')
        assert result['collide_and_stream_calls']=='0' and result['frames_written']=='1'
        assert result['finite']=='true' and result['NUMERICAL_GATE']=='NOT_EVALUATED'
        initial.append({'row':r,'output':str(out.relative_to(ROOT))})
    assert len(initial)==6 and len(described)==90
    report={'ok':not skipped,'wrapper_snapshot':str((base/'run_case_snapshot.py').relative_to(ROOT)),
            'configuration_rows':len(described),'unique_meshes':len(unique),
            'actual_geometry_prechecks':len(geometries),'geometry_records':geometries,
            'skipped_for_memory':skipped,'initial_output_sets':initial,
            'configuration_output_directories':described,
            'collide_and_stream_calls':0,'formal_simulations':0,
            'NUMERICAL_GATE':'NOT_EVALUATED','RESULT_PASS':False,
            'source_sha256':run.sha(ROOT/'src/variable_groove_transport.cpp'),
            'binary_sha256':run.sha(ROOT/'build/variable_groove_transport')}
    (ROOT/'evidence/preflight.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    print(json.dumps({k:v for k,v in report.items() if k not in ['geometry_records','initial_output_sets','configuration_output_directories']},ensure_ascii=False))
    if skipped:raise SystemExit('Some fine-mesh checks need more available memory; see the report.')


if __name__=='__main__':main()

"""Materialize two performance identities and a closed seal. No native calls."""
from pathlib import Path
import argparse
import importlib.util
import json
import os
import sys

CASE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(CASE/'analysis'))
from perf_contract import (ROOT,CASE,B_PATH,B_SHA,ELF_SHA,IDS,CASES,MODULES,SCIENCE,
    REVIEW,IMPLEMENTATION,PROTOCOL_DIR,PREP,STAGE,PURPOSE,need,sha,kv,load,save,
    protocol,verify_B,verify,no_symlinks,now)


def identities():
    b=verify_B()
    need(not (CASE/'performance_runs').exists(),'identity root exists; no overwrite')
    original={r['planned_case_id']:r for r in b['prepared_runs']}
    records=[]
    for rid,ident in zip(IDS,CASES):
        run=CASE/'performance_runs'/rid/'steady';no_symlinks(run)
        run.mkdir(parents=True,exist_ok=False)
        cfg=dict(kv(original[ident]['run_config_path']),run_id=rid,output_directory=str(run))
        path=run/'run_config.txt'
        path.write_text(''.join(k+'='+v+'\n' for k,v in cfg.items()))
        (run/'run_manifest.txt').write_text(f'run_id={rid}\nmode=steady\n')
        records.append(dict(run_id=rid,source_planned_case_id=ident,run_config_path=str(path),
                            run_config_sha256=sha(path),output_directory=str(run)))
    save(CASE/'evidence/identity_plan.json',dict(prepared_benchmark_runs=records,
         performance_time_stepping_authorized=False,formal_simulation_authorized=False))
    save(CASE/'evidence/adoption.json',load(IMPLEMENTATION/'adoption.json'))
    print(json.dumps(dict(identities_prepared=2,native_calls=0,authorized=False)))


def runtime_environment():
    files={}
    for module in list(sys.modules.values()):
        name=getattr(module,'__file__',None)
        if not name:continue
        p=Path(name)
        if p.suffix=='.pyc':
            try:p=Path(importlib.util.source_from_cache(str(p)))
            except ValueError:continue
        if p.is_file():files[str(p.resolve())]=sha(p)
    for line in Path('/proc/self/maps').read_text().splitlines():
        columns=line.split(None,5)
        if len(columns)==6 and columns[5].startswith('/'):
            p=Path(columns[5])
            if p.is_file():files[str(p.resolve())]=sha(p)
    executable=str(Path(sys.executable).resolve());files[executable]=sha(executable)
    cpu=next((line.split(':',1)[1].strip() for line in Path('/proc/cpuinfo').read_text().splitlines()
              if line.startswith('model name')),'NOT_AVAILABLE')
    return dict(recorded_at=now(),python_executable=executable,python_sha256=sha(executable),
        python_version=sys.version,host=os.uname().nodename,platform=list(os.uname()),CPU_model=cpu,
        runtime_files_sha256=files,native_build_reused=True,new_native_build=False,
        dependencies_captured='loaded Python sources/extensions and mapped libraries; no new installation')


def seal():
    b=verify_B();p=protocol()
    target=CASE/'evidence/preparation_perf.json'
    need(not target.exists(),'closed performance seal exists; refusing overwrite')
    tests=load(IMPLEMENTATION/'software_checks.json')
    need(tests.get('SOFTWARE_CHECK_PASS') is True and tests.get('native_calls')==0,
         'passing nonnative software evidence required')
    envpath=CASE/'evidence/runtime_environment.json'
    save(envpath,runtime_environment())
    inputs=dict(b['inputs_sha256']);inputs[str(B_PATH)]=B_SHA
    for folder in [CASE/'scripts',CASE/'analysis',CASE/'tests',CASE/'evidence',REVIEW]:
        for path in sorted(folder.rglob('*')):
            if path.is_file():
                need('__pycache__' not in path.parts,'cache must not enter preparation')
                inputs[str(path)]=sha(path)
    for path in [CASE/'README.md',IMPLEMENTATION/'adoption.json',IMPLEMENTATION/'software_checks.json',
                 IMPLEMENTATION/'software_tests.log',PROTOCOL_DIR/'PERFORMANCE_PROTOCOL.md',
                 PROTOCOL_DIR/'performance_protocol.json']:
        inputs[str(path)]=sha(path)
    env=load(envpath);inputs.update(env['runtime_files_sha256'])
    plan=load(CASE/'evidence/identity_plan.json')
    for r in plan['prepared_benchmark_runs']:
        for path in [Path(r['run_config_path']),Path(r['output_directory'])/'run_manifest.txt']:
            inputs[str(path)]=sha(path)
    data=dict(protocol_id='S2-MIP-v1-PERF',schema_version='S2-PERF-BINDING-1',
        stage=STAGE,purpose=PURPOSE,kind=PREP,created_at=now(),B_path=str(B_PATH),B_sha256=B_SHA,
        native_binary=b['provenance']['native_binary'],native_binary_sha256=ELF_SHA,
        native_build_environment=b['provenance']['build_environment'],
        native_source_revision=b['source_revision'],native_formal_simulation_flag_preserved=True,
        prepared_benchmark_runs=plan['prepared_benchmark_runs'],prepared_benchmark_run_ids=IDS,
        approved_benchmark_run_ids=[],approved_benchmark_runs=[],approved_formal_run_ids=[],
        approved_run_ids=[],approved_runs=[],actual_benchmark_run_ids=[],actual_formal_run_ids=[],
        performance_time_stepping_authorized=False,formal_simulation_authorized=False,
        simulation_authorized=False,native_zero_step_authorized=False,
        AI_may_start_native=False,user_manually_starts=True,automatic_retry_authorized=False,
        native_window_steps=p['native_window_steps'],native_maximum_steps=p['native_maximum_steps'],
        resources=p['resources'],budget=p['budget'],performance_windows=p['performance_windows'],
        inputs_sha256=inputs,performance_status='NOT_EXECUTED',zero_audit_repeated=False,
        F04='OPEN_OUT_OF_SCOPE',**SCIENCE)
    need(all(sha(path)==digest for path,digest in inputs.items()),'cannot seal changed input')
    save(target,data);digest=sha(target)
    verify(target,digest)
    with target.with_suffix('.json.sha256').open('x') as stream:stream.write(digest+'\n')
    print(json.dumps(dict(preparation_sha256=digest,inputs=len(inputs),native_calls=0,
                         performance_time_stepping_authorized=False,formal_simulation_authorized=False)))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('action',choices=['identities','seal'])
    {'identities':identities,'seal':seal}[parser.parse_args().action]()

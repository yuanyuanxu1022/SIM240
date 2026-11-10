#!/usr/bin/env python3
"""Bind completed preparation evidence; optionally prepare only the first 8-case command.
Does not compile, advance flow, or authorize/launch another stage.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import shlex
import subprocess

ROOT=Path(__file__).resolve().parents[1]
PROJECT=ROOT.parents[2]
spec=importlib.util.spec_from_file_location('runner',ROOT/'tools/run_case.py')
run=importlib.util.module_from_spec(spec);spec.loader.exec_module(run)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--prepare-foundation-command',action='store_true')
    args=parser.parse_args()
    cpp=ROOT/'src/variable_groove_transport.cpp';binary=ROOT/'build/variable_groove_transport'
    pre=json.loads((ROOT/'evidence/preflight.json').read_text())
    assert pre['ok'] and pre['actual_geometry_prechecks']==42 and pre['configuration_rows']==90
    assert pre['source_sha256']==run.sha(cpp) and pre['binary_sha256']==run.sha(binary)
    for name in ['independent_geometry.json','initial_fields.json','rejection_checks.json']:
        assert json.loads((ROOT/'evidence'/name).read_text())['ok']
    assert (ROOT/'evidence/build_exit_code.txt').read_text().strip()=='0'
    original_wrapper=ROOT/pre.get('wrapper_snapshot','evidence/preflight_wrapper_snapshot/run_case.py')
    checked=0
    folders=set(pre['configuration_output_directories'])
    folders.update(record['output'] for record in pre['geometry_records'])
    folders.update(record['output'] for record in pre['initial_output_sets'])
    for relative in sorted(folders):
        folder=ROOT/relative
        manifest=folder/'run_manifest.json'
        if not manifest.exists():continue
        m=json.loads(manifest.read_text())
        assert m['mode'] in ['describe','precheck','initialize'] and not m['formal_simulation']
        for path,expected in m['inputs_sha256'].items():
            file=Path(path)
            if file==ROOT/'tools/run_case.py' and run.sha(file)!=expected:file=original_wrapper
            assert run.sha(file)==expected,(path,'preflight input no longer matches archived snapshot')
        assert (folder/'exit_code.txt').read_text().strip()=='0'
        checked+=1
    assert checked==138
    protected=json.loads((ROOT/'evidence/protected_inputs.json').read_text())
    assert all(run.sha(PROJECT/path)==h for path,h in protected.items())
    env=json.loads((ROOT/'evidence/build_environment.json').read_text())
    assert all(run.sha(path)==h for path,h in env['library_hashes'].items())
    dependencies=(ROOT/'build/variable_groove_transport.d').read_text().replace('\\\n',' ')
    first_rule=dependencies.split('\n',1)[0].split(':',1)[1]
    headers={}
    for path in shlex.split(first_rule):
        file=Path(path)
        if not file.is_absolute():file=(ROOT/'src'/file).resolve()
        headers[str(file)]=run.sha(file)
    (ROOT/'evidence/compiled_dependencies.json').write_text(json.dumps(headers,ensure_ascii=False,indent=2))
    bound=[cpp,ROOT/'src/Makefile',binary,ROOT/'protocol/execution.json',ROOT/'protocol/candidate_cases.csv',
           ROOT/'protocol/foundation_references.json',ROOT/'evidence/compiled_dependencies.json']
    bound+=list((ROOT/'tools').glob('*.py'))
    bound+=list(ROOT/'evidence'/name for name in ['preflight.json','independent_geometry.json','initial_fields.json','rejection_checks.json'])
    binding={str(path):run.sha(path) for path in bound}|headers|env['library_hashes']
    report={'preparation_complete':True,'compiler_exit_code':0,'described_rows':90,'actual_q_geometry_meshes':42,
            'initial_output_sets':6,'preflight_actions_verified':checked,'old_protected_inputs':len(protected),
            'compiled_dependency_files':len(headers),'bound_inputs_sha256':binding,
            'zero_step_wrapper_snapshot_retained':True,
            'wrapper_update_after_preflight':'steady stage whitelist strengthened; numerical kernel unchanged',
            'NUMERICAL_GATE':'NOT_EVALUATED','RESULT_PASS':False,'steady_runs_started':0}
    (ROOT/'evidence/preparation_binding.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    if args.prepare_foundation_command:
        cases=[r['planned_case_id'] for r in run.candidates() if r['role'] in ['regression','smooth']]
        assert len(cases)==8
        release={'released':True,'release_kind':'launch_preconditions_for_user_started_foundation_only',
                 'allowed_case_ids':cases,'bound_inputs_sha256':binding,
                 'NUMERICAL_GATE':'NOT_EVALUATED','RESULT_PASS':False,
                 'user_must_start':True,'next_stage_released':False,'steady_runs_started':0}
        (ROOT/'evidence/formal_run_release.json').write_text(json.dumps(release,ensure_ascii=False,indent=2))
        inner=f'cd {shlex.quote(str(ROOT))} && exec python3 tools/run_stage.py --stage foundation --batch-id foundation_20261023_v1 --execute'
        command='tmux new-session -d -s d4-foundation-20261023 '+shlex.quote(inner)
        (ROOT/'NEXT_COMMAND.txt').write_text(command+'\n')
        subprocess.run(['bash','-n'],input=command,text=True,check=True)
    print(json.dumps({k:v for k,v in report.items() if k!='bound_inputs_sha256'},ensure_ascii=False))


if __name__=='__main__':main()

#!/usr/bin/env python3
"""Final preparation checks only; never starts the prepared diagnostic."""
import argparse
import ast
import json
import subprocess
from pathlib import Path

from run_diagnostic import CASE, sha, check_bound, validate_build, dump_new


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--run-id',required=True)
    args=parser.parse_args()
    target=CASE/'reports/run_ready.json'
    if target.exists(): raise FileExistsError('Ready evidence already exists')
    run=CASE/'runs'/args.run_id
    manifest=json.loads((run/'manifest.json').read_text())
    build=json.loads((CASE/'reports/build_precheck.json').read_text())
    validate_build(build)
    check_bound(manifest['source_files'])
    assert manifest['run_id']==args.run_id
    assert manifest['command']==[build['binary']['path'],'steady','T',str(run)]
    assert sha(CASE/'reports/build_precheck.json')==manifest['build_record_sha']
    assert not any((run/name).exists() for name in ('run.log','exit_code.txt','result.txt','mass_ledger.csv'))
    for script in (CASE/'scripts').glob('*.py'): ast.parse(script.read_text())
    syntax_sources=[CASE/'PROTOCOL.md',CASE/'README.md',*(CASE/'src').glob('*'),*(CASE/'scripts').glob('*.py')]
    whitespace=[]
    for path in syntax_sources:
        p=subprocess.run(['git','diff','--no-index','--check','/dev/null',str(path)],capture_output=True,text=True)
        # --no-index may return 1 for a file difference even with --check clean.
        assert p.returncode in (0,1) and not p.stdout and not p.stderr,(str(path),p.stdout,p.stderr)
        whitespace.append(str(path.relative_to(CASE)))
    source=(CASE/'src/fine_T_diagnostic.cpp').read_text()
    header=(CASE/'src/mass_ledger.h').read_text()
    assert source.count('lattice.collideAndStream();')==1
    assert all(token in header for token in ('film_nodes,recess_nodes','rho_min_id,rho_max_id',
                                             'max_reconstruction_residual','densityRecorded'))
    session='fine-t-mass-v2-'+args.run_id.split('T')[1][:6]
    p=subprocess.run(['tmux','has-session','-t',session],text=True,capture_output=True)
    assert p.returncode!=0,'Chosen tmux session already exists'
    ready={'run_ready':True,'run_id':args.run_id,'run_directory':str(run),'tmux_session':session,
           'build_record_sha256':sha(CASE/'reports/build_precheck.json'),
           'run_manifest_sha256':sha(run/'manifest.json'),
           'current_run_manifest_txt_sha256':sha(run/'run_manifest.txt'),
           'final_verifier_sha256':sha(Path(__file__)),
           'python_AST_and_whitespace_PASS':True,'files_checked':whitespace,
           'source_tokens_restored':build['source_tokens_restored'],
           'synthetic_Cpp_arithmetic_PASS':build['synthetic_test']['PASS'],
           'compilation_exit_code':build['commands'][-2]['exit_code'],
           'geometry_PASS':build['precheck']['result']['geometry_PASS'],
           'q_audit_PASS':build['precheck']['result']['q_audit_PASS'],
           'precheck_independent_exit_code':build['precheck']['independent_exit_code'],
           'time_stepping_started':False,'formal_reference_accepted':False,
           'legacy_fine_T_status':'FAIL','numerical_and_result_gates':'not_evaluated_for_new_diagnostic'}
    dump_new(target,ready)
    print(json.dumps({'output':str(target),'run_ready':True,'session':session,
                      'time_stepping_started':False,'formal_reference_accepted':False},ensure_ascii=False))


if __name__=='__main__': main()

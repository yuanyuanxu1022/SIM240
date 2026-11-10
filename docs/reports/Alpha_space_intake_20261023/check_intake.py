#!/usr/bin/env python3
"""One-shot read-only intake; precheck runner without --run; never calls a solver."""
from pathlib import Path
import datetime as dt
from zoneinfo import ZoneInfo
import hashlib
import json
import subprocess
import sys

ROOT=Path('/home/dell/yuanyuanxu/SIM240')
BASE=ROOT/'CASE/09_dynamic_liquid_gas/alpha_c_validation_20261022'
OUT=Path(__file__).resolve().parent
SEARCH_ROOTS=[ROOT,Path('/home/dell/yuanyuanxu/SIM240_代码图片数据_20261022'),
              Path('/home/dell/yuanyuanxu/SIM240_第一篇论文_导师审阅材料_20261022')]

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
    if (OUT/'intake.json').exists():raise RuntimeError('intake snapshot exists; no overwrite or repeated polling')
    protocol=json.loads((BASE/'protocol.json').read_text());batch=protocol['batch_prefix']+'_alpha'
    binding=json.loads((BASE/'evidence/build_binding.json').read_text())
    mismatches=[p for p,h in binding['sha256'].items() if not Path(p).is_file() or sha(p)!=h]
    expected=[]
    for case in protocol['stages']['alpha']:
        run_id=batch+'_'+case['id'];evidence=BASE/'evidence'/batch/run_id;output=BASE/'output'/batch/run_id
        expected.append(dict(case_id=case['id'],run_id=run_id,expected_steps=case['steps'],
            evidence_directory=str(evidence),output_directory=str(output),
            independent_exit_exists=(evidence/'exit_code.txt').is_file(),
            config_exists=(output/'config.json').is_file(),result_exists=(output/'result.json').is_file()))
    command=['rg','--files','--hidden','--no-ignore','-g','!**/.git/**','-g','*manifest.json','-g','exit_code.txt','-g','verdict.json']+[str(p) for p in SEARCH_ROOTS]
    search=subprocess.run(command,capture_output=True,text=True,timeout=30)
    if search.returncode not in (0,1):raise RuntimeError('bounded metadata search error '+search.stderr)
    matches=[s for s in search.stdout.splitlines() if batch in s or 'alpha_c_validation_20261022/output/' in s or 'alpha_c_validation_20261022/analysis_alpha/' in s]
    (OUT/'metadata_search.json').write_text(json.dumps(dict(command=command,exit_code=search.returncode,
        matched_formal_alpha_paths=matches,stderr=search.stderr),indent=2)+'\n')
    processes=[]
    for proc in Path('/proc').iterdir():
        if not proc.name.isdigit():continue
        try:
            args=[s.decode(errors='replace') for s in (proc/'cmdline').read_bytes().split(b'\0') if s]
            cwd=(proc/'cwd').resolve()
            relevant=any(Path(a).name in {'alpha_diffusion','coupled_check'} for a in args)
            relevant|=any(Path(a).name=='run_suite.py' and (str(BASE) in a or cwd==BASE) for a in args)
            if relevant:processes.append(dict(pid=int(proc.name),cwd=str(cwd),argv=args))
        except (OSError,ValueError):pass
    tmux=subprocess.run(['tmux','list-sessions','-F','#{session_name}'],capture_output=True,text=True,timeout=10)
    sessions=[s for s in tmux.stdout.splitlines() if 'alpha' in s.lower()]
    (OUT/'process_snapshot.json').write_text(json.dumps(dict(processes=processes,tmux_exit=tmux.returncode,
        matching_sessions=sessions,tmux_stderr=tmux.stderr,one_snapshot_only=True),indent=2)+'\n')
    # Reviewed runner: absence of --run takes the precheck-only return branch.
    precheck_command=[sys.executable,str(BASE/'run_suite.py'),'--stage','alpha']
    precheck=subprocess.run(precheck_command,cwd=BASE,capture_output=True,text=True,timeout=30)
    (OUT/'precheck.json').write_text(json.dumps(dict(command=precheck_command,exit_code=precheck.returncode,
        stdout=precheck.stdout,stderr=precheck.stderr,execute_option_present=False,solver_started=False),indent=2)+'\n')
    ready=(BASE/'evidence'/batch/'manifest.json').is_file() and (BASE/'evidence'/batch/'exit_code.txt').is_file()
    payload=dict(checked_Beijing=dt.datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),batch_id=batch,
        protocol_id=protocol['protocol_id'],expected_case_count=len(expected),cases=expected,
        formal_batch_manifest_exists=(BASE/'evidence'/batch/'manifest.json').is_file(),
        formal_batch_independent_exit_exists=(BASE/'evidence'/batch/'exit_code.txt').is_file(),
        formal_output_root_exists=(BASE/'output').exists(),frozen_verdict_exists=(BASE/'analysis_alpha/verdict.json').is_file(),
        searched_roots=[str(p) for p in SEARCH_ROOTS],matching_formal_metadata_paths=matches,
        matching_processes=processes,matching_tmux_sessions=sessions,
        bound_files_verified=len(binding['sha256']),bound_input_mismatches=mismatches,
        precheck_exit_code=precheck.returncode,precheck_executed_no_run_option=True,
        complete_results_available_for_acceptance=bool(ready),
        acceptance_status='NOT_EVALUATED_RESULTS_NOT_FOUND' if not ready and not matches else 'REQUIRES_FURTHER_INTAKE',
        frozen_analyzer_executed=False,max_phase_drift=None,mode_error=None,diffusion_rate_error=None,
        NUMERICAL_GATE='NOT_EVALUATED',RESULT_PASS='NOT_EVALUATED',geometry_PASS='NOT_EVALUATED',
        new_simulation_started=False,new_compilation=False,new_numerical_acceptance=False,
        previous_preparation_only=dict(local_checks=62424,zero_step_initializations=20,not_formal_space_results=True),
        prior_C_first_step_forecast='preparation-only algebra prediction; not measured C results',
        limits='Only listed local roots and one local process/session snapshot checked; no claim about other machines or arbitrary paths.',
        next_action='Locate existing completed batch if run elsewhere; otherwise user may use original NEXT_COMMAND. Do not auto-start/restart or enable C.')
    (OUT/'intake.json').write_text(json.dumps(payload,indent=2,ensure_ascii=False)+'\n')
    assert not mismatches
    print(json.dumps({k:payload[k] for k in ('checked_Beijing','batch_id','expected_case_count','bound_files_verified','bound_input_mismatches','precheck_exit_code','acceptance_status')},indent=2))

if __name__=='__main__':main()

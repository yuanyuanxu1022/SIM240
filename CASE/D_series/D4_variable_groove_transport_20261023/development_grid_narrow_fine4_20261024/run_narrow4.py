#!/usr/bin/env python3
"""Exactly the four released 1.25nm narrow development grid references. Default is read-only validation."""
from pathlib import Path
import argparse,csv,datetime,fcntl,hashlib,importlib.util,json,os,shutil,subprocess
HERE=Path(__file__).resolve().parent;CASE=HERE.parent
spec=importlib.util.spec_from_file_location('frozen_D4_case_runner',CASE/'tools/run_case.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
sha=base.sha
PROJECT=CASE.parents[2]
def resolve_bound(p):
    path=Path(p);return path if path.is_absolute() else PROJECT/path
def csvrows(p):return list(csv.DictReader(Path(p).open(encoding='utf-8-sig')))
def stage_rows():return csvrows(HERE/'stage_cases.csv')
def policy():return json.loads((HERE/'policy.json').read_text())
def writej(p,v):Path(p).write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def canonical_allowed(r):
    return (r['role']=='grid_reference' and r['blind_geometry']=='False' and r['h_nm']=='75' and r['dx_nm']=='1.25' and r['acceleration_m_s2']=='100000' and r['direction'] in ('P','T') and (r['w_nm'],r['d_nm']) in (('60','25'),('60','120')))
def validate_table():
    canonical=csvrows(CASE/'protocol/candidate_cases.csv');selected=stage_rows()
    expected=[r for r in canonical if canonical_allowed(r)]
    if len(expected)!=4 or len(selected)!=4:raise RuntimeError('four-case table required')
    if {r['planned_case_id'] for r in selected}!={r['planned_case_id'] for r in expected}:raise RuntimeError('stage differs from exact held-development set')
    for row in selected:
        match=[r for r in canonical if r['planned_case_id']==row['planned_case_id']]
        if len(match)!=1 or row!=match[0]:raise RuntimeError('stage row changed from canonical source')
    return selected
def validate_row(row,release):
    if release.get('released') is not True:raise RuntimeError('stage is not released')
    if row.get('planned_case_id') not in release.get('allowed_case_ids',[]):raise RuntimeError('case outside grid_narrow_fine4 stage')
    if not canonical_allowed(row):raise RuntimeError('role/geometry outside grid_narrow_fine4')
    match=[r for r in stage_rows() if r['planned_case_id']==row['planned_case_id']]
    if len(match)!=1 or row!=match[0]:raise RuntimeError('row differs from frozen stage table')
def config_text(row):
    p=json.loads((CASE/'protocol/execution.json').read_text());tag=policy()['batch_id']
    runid=row['planned_case_id'].replace('CAND_','D4_',1)+'_'+tag
    out=CASE/'results'/tag/runid/'steady'
    config=dict(mode='steady',run_id=runid,output_directory=str(out),direction=row['direction'],dx_nm=row['dx_nm'],h_nm=row['h_nm'],d_nm=row['d_nm'],w_nm=row['w_nm'],period_nm=row['P_nm'],Ly_nm=row['Ly_nm'],nu_m2_s=row['nu_m2_s'],acceleration_m_s2=row['acceleration_m_s2'],window_tstar=p['window_tstar'],max_time_H_diffusion=p['max_time_H_diffusion'],frame_tstar=','.join(str(v) for v in p['frame_tstar']))
    return ''.join(f'{k}={v}\n' for k,v in config.items())
def template_path(row):return HERE/'launch_configs'/(row['planned_case_id']+'.txt')
def resource_check(p,available=None,free=None):
    if available is None:available=int(next(s.split()[1] for s in Path('/proc/meminfo').read_text().splitlines() if s.startswith('MemAvailable:')))*1024
    if free is None:free=shutil.disk_usage(CASE).free
    if available<p['minimum_available_RAM_bytes']:raise RuntimeError('insufficient available RAM')
    if free<p['minimum_free_disk_bytes']:raise RuntimeError('insufficient free disk')
    return dict(MemAvailable_bytes=available,disk_free_bytes=free)
def validate_binding(release):
    bindings=release.get('bound_inputs_sha256')
    if not bindings:raise RuntimeError('missing actual input binding')
    for p,h in bindings.items():
        if not resolve_bound(p).is_file() or sha(resolve_bound(p))!=h:raise RuntimeError('bound input changed: '+p)
def runtime_environment(release,environ=None):
    env=os.environ if environ is None else environ
    for key in ('OMPI_COMM_WORLD_SIZE','PMI_SIZE','MV2_COMM_WORLD_SIZE'):
        if key in env and env[key]!='1':raise RuntimeError('exactly one MPI rank required')
    if env.get('SIM240_OLB_ROOT','/home/dell/openlb')!='/home/dell/openlb':raise RuntimeError('OpenLB root differs from local binding')
    current=subprocess.run(['git','-C','/home/dell/openlb','rev-parse','HEAD'],capture_output=True,text=True,check=True).stdout.strip()
    if current!=release['OpenLB_commit']:raise RuntimeError('OpenLB HEAD changed')
def ensure_new_batch(batch_id):
    if batch_id!=policy()['batch_id']:raise RuntimeError('only the fixed batch ID is accepted')
    batch=CASE/'results'/batch_id
    if batch.exists():raise RuntimeError('batch already exists; refuse overwrite or restart')
    return batch
def ensure_case_not_completed(row):
    prefix=row['planned_case_id'].replace('CAND_','D4_',1)+'_'
    if any((CASE/'results').glob('*/'+prefix+'*/steady/result.txt')):raise RuntimeError('case already has a formal result; do not rerun')
def validate_ready(batch_id,release):
    if release.get('batch_id')!=batch_id:raise RuntimeError('release/batch mismatch')
    if json.loads((HERE/'release.json').read_text())!=release:raise RuntimeError('release changed after loading')
    selected=validate_table();validate_binding(release);runtime_environment(release)
    if release.get('allowed_case_ids')!=[r['planned_case_id'] for r in selected]:raise RuntimeError('release whitelist differs from ordered stage table')
    batch=ensure_new_batch(batch_id)
    for row in selected:
        validate_row(row,release);ensure_case_not_completed(row)
        if template_path(row).read_text()!=config_text(row):raise RuntimeError('prepared steady configuration differs')
    resources=resource_check(policy());return selected,batch,resources
def execute_batch(selected,batch,release):
    p=policy();progress=[];code=0
    # Protect this entry from concurrent starts; mkdir also rejects an existing batch.
    with (HERE/'execution.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        selected,batch,resources=validate_ready(p['batch_id'],release)
        original_release_hash=sha(HERE/'release.json')
        batch.mkdir(parents=True,exist_ok=False)
        writej(batch/'stage_manifest.json',dict(batch_id=p['batch_id'],stage='grid_narrow_fine4_development',started_UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),case_ids=[r['planned_case_id'] for r in selected],release_sha256=sha(HERE/'release.json'),resources_before=resources,analysis_automatically_run=False,next_stage_automatically_run=False,independent_acceptance='pending'))
        writej(batch/'stage_progress.json',[])
        try:
            for row in selected:
                if sha(HERE/'release.json')!=original_release_hash:raise RuntimeError('release bytes changed after batch start')
                validate_binding(release);runtime_environment(release);resources=resource_check(p);ensure_case_not_completed(row)
                out,m=base.prepare(row,'steady',batch,p['batch_id'])
                if (out/'run_config.txt').read_bytes()!=template_path(row).read_bytes():raise RuntimeError('runtime config differs from frozen prepared config')
                m.update(stage='grid_narrow_fine4_development',stage_release_sha256=sha(HERE/'release.json'),resources_before=resources,independent_acceptance='pending')
                m['inputs_sha256'].update({str(resolve_bound(k)):v for k,v in release['bound_inputs_sha256'].items()});m['inputs_sha256'][str(HERE/'release.json')]=sha(HERE/'release.json')
                writej(out/'run_manifest.json',m)
                command=['/usr/bin/time','-f','{"max_rss_kb":%M,"elapsed_seconds":%e}','-o',str(out/'resource_usage.json')]+m['command']
                with (out/'run.log').open('w') as log:
                    completed=subprocess.run(command,cwd=CASE,stdout=log,stderr=subprocess.STDOUT)
                code=completed.returncode;(out/'exit_code.txt').write_text(str(code)+'\n')
                unchanged=all(sha(path)==h for path,h in m['inputs_sha256'].items())
                writej(out/'inputs_after.json',dict(unchanged=unchanged))
                progress.append(dict(case_id=row['planned_case_id'],output=str(out.relative_to(batch)),exit_code=code));writej(batch/'stage_progress.json',progress)
                if not unchanged:raise RuntimeError('bound inputs changed during case')
                if code:break
                result=base.kv(out/'result.txt')
                if result.get('NUMERICAL_GATE')!='PASS' or result.get('geometry_PASS')!='true' or result.get('RESULT_PASS')!='false':raise RuntimeError('unexpected solver result flags; independent acceptance still pending')
        except BaseException as error:
            (batch/'stage_error.txt').write_text(repr(error)+'\n');code=code or 2
        finally:
            (batch/'exit_code.txt').write_text(str(code)+'\n')
            writej(batch/'stage_completion.json',dict(finished_UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),attempted_cases=len(progress),exit_code=code,independent_acceptance='pending',next_stage_started=False))
    return code
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--batch-id',required=True);ap.add_argument('--execute',action='store_true');a=ap.parse_args()
    if a.batch_id!=policy()['batch_id']:raise SystemExit('only the fixed grid_narrow_fine4 batch ID is accepted')
    if not (HERE/'release.json').is_file():raise SystemExit('separately reviewed grid_narrow_fine4 release is missing')
    release=json.loads((HERE/'release.json').read_text())
    selected,batch,resources=validate_ready(a.batch_id,release)
    if not a.execute:
        print(json.dumps(dict(ok=True,cases=4,batch_id=a.batch_id,will_run=False,result_directory_created=False,resources=resources,case_ids=[r['planned_case_id'] for r in selected]),ensure_ascii=False));return
    code=execute_batch(selected,batch,release)
    print(json.dumps(dict(exit_code=code,next_stage_started=False,independent_acceptance='pending')));raise SystemExit(code)
if __name__=='__main__':main()

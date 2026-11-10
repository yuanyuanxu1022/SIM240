"""Independent saved-file/exit/source checks. No simulation, compilation or write probe."""
from datetime import datetime
from zoneinfo import ZoneInfo
import hashlib
import json
from pathlib import Path
import subprocess
import sys

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
P=REPO/'CASE/D_series/D4_variable_groove_transport_20261023/reference_backend_min18_20261025/pilot_record_v3_1_20261026'
E=HERE/'evidence'
def read(p):return json.loads(p.read_text())
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for x in iter(lambda:f.read(1048576),b''):h.update(x)
    return h.hexdigest()
def obj_sha(d):return hashlib.sha256(json.dumps(d,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def verify_map(mapping,base):
    bad=[p for p,h in mapping.items() if not (base/p).is_file() or sha(base/p)!=h]
    assert not bad,bad
    return {'count':len(mapping),'mismatches':bad}

def main():
    assert (E/'mounted_after_user.exit_code').read_text().strip()=='0'
    d=read(E/'mounted_after_user.json');assert d['status']=='BOUNDED_VOLUME_PROBES_PASS_ONLY'
    assert d['probe_source_sha256']==sha(HERE/'probe_volume.py')
    assert d['authorized_to_solve'] is False and d['real_solver_called'] is False and d['actual_run_id'] is None
    assert not d['forbidden_backend_modules_loaded']
    before,after=(json.loads(d[k]['stdout']) for k in ('layout_before','layout_after'))
    for x in (before,after):
        assert x['status']=='LAYOUT_CHECK_PASS_ONLY' and all(x['checks'].values())
        assert x['work']['capacity_bytes']==536870912 and x['work']['empty'] is True
        assert x['record']['mount']['filesystem']=='ext4' and x['work']['st_dev']!=x['record']['st_dev']
    small=d['persistent'];assert small['bytes']==1048576 and sha(Path(small['file']))==small['sha256']
    cap=d['capacity'];assert cap['successful_write_bytes']==536870912 and cap['errno']==28
    assert cap['available_bytes_when_full']==0 and cap['free_inodes_when_full']>0 and cap['full_volume_child_exit']==28
    h=hashlib.sha256()
    for _ in range(512):h.update(b'V'*1048576)
    assert h.hexdigest()==cap['fill_sha256']
    # Locate this exact controller record; do not infer completion from directory existence.
    record_parent=Path(after['record']['path'])
    matches=[p for p in record_parent.glob('volume_probe_mounted_*/probe_result.json')
             if read(p).get('started_at_Asia_Shanghai')==d['started_at_Asia_Shanghai']]
    assert len(matches)==1,matches
    control=matches[0].parent
    assert (control/'compiler.exit_code').read_text().strip()=='0'
    assert (control/'loader.exit_code').read_text().strip()=='0'
    assert (control/'loader.stdout.log').read_text().strip()=='CACHE_LOAD_PASS'
    assert (control/'full_volume_child.independent_exit_code').read_text().strip()=='28'
    assert read(control/'capacity_probe.json')==cap
    assert d['cache']['compiler_exit']==d['cache']['loader_exit']==0
    archives=[]
    for item in d['archives']:
        record=Path(item['record_dir']);c,s,m=(read(record/name) for name in ('contract.json','STARTED.json','capture_manifest.json'))
        a=read(record/'archive_manifest.json');lock=read(record/'source_lock.json')
        assert c['authorized_to_execute'] is False and c['approval'] is None
        assert c['physical_plan']['execution_authorized'] is False
        assert s['kind']==m['kind']=='SYNTHETIC_PROCESS_NOT_PDE'
        assert m['children_stopped'] is True and m['archive_status']=='ARCHIVE_COMPLETE'
        assert m['independent_exit_code']==a['independent_exit_code']==item['independent_exit_code']
        assert int((record/'independent_exit_code.txt').read_text())==m['independent_exit_code']
        assert m['inputs_unchanged'] is True and s['inputs_sha256_before']==m['inputs_sha256_after']==lock['files']
        assert sha(record/'source_lock.json')==c['source_lock_sha256']
        assert all(x['contract_sha256']==obj_sha(c) and x['run_id']==c['run_id'] for x in (s,m,a))
        assert a['source_work_dir']==c['work_dir'] and a['archive_dir']==str(record/'archive')
        assert a['work_files']==m['work_files']
        actual={str(p.relative_to(record/'archive')):{'sha256':sha(p),'bytes':p.stat().st_size}
                for p in (record/'archive').rglob('*') if p.is_file()}
        assert actual==a['work_files']
        assert not Path(c['work_dir']).exists()  # Explicit synthetic-source cleanup, never real data.
        command=[sys.executable,'-B',str(P/'readback.py'),str(record/'archive'),'--record-dir',str(record)]
        if item['mode']=='failure':
            assert m['independent_exit_code']==7
            assert (record/'archive/partial.bin').read_bytes()==b'partial-raw-fixture'
            command.append('--archive-only')
        else:assert m['independent_exit_code']==0
        proc=subprocess.run(command,capture_output=True,text=True,timeout=10)
        (E/('independent_'+item['mode']+'_readback.log')).write_text(proc.stdout+proc.stderr)
        (E/('independent_'+item['mode']+'_readback.exit_code')).write_text(str(proc.returncode)+'\n')
        assert proc.returncode==0,proc.stderr
        archives.append({'mode':item['mode'],'record_dir':str(record),'raw_files_rehashed':len(actual),
            'original_exit':m['independent_exit_code'],'independent_readback_exit':proc.returncode})
    sources=verify_map(read(P/'source_lock.json')['files'],REPO)
    protected=verify_map(read(REPO/'docs/reports/G4_derivation_source_audit_20261025/protected_inputs.json'),REPO)
    v3=verify_map(read(REPO/'docs/reports/D4_pilot_v3_review_20261026/review_inputs_sha256.json'),REPO)
    # A fresh final check confirms current state, independently of the saved snapshot.
    proc=subprocess.run([sys.executable,'-B',str(P/'precheck_layout.py')],capture_output=True,text=True,timeout=10)
    assert proc.returncode==0 and all(json.loads(proc.stdout)['checks'].values())
    (E/'current_layout_verified.json').write_text(proc.stdout)
    report={'status':'PASS_BOUNDED_ENVIRONMENT_PROBES_ONLY','checked_at_Asia_Shanghai':datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),
        'controller_record':str(control),'work_capacity_bytes':536870912,'work_empty_after_probes':True,
        'persistent_small_file_pass':True,'cache_compile_load_exit':[0,0],'ENOSPC_errno':28,'ENOSPC_write_bytes':536870912,
        'full_volume_independent_exit':28,'archives':archives,'source_binding':sources,'protected_history':protected,'prior_v3':v3,
        'real_solver_called':False,'actual_run_id':None,'real_backend_end_to_end':'NOT_TESTED',
        'NUMERICAL_GATE':'NOT_EVALUATED','RESULT_PASS':False,'geometry_PASS':None,'prediction_permission':'HOLD'}
    with (E/'mounted_independent_verification.json').open('x') as f:json.dump(report,f,indent=2);f.write('\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()

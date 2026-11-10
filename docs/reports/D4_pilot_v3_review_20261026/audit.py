"""Source/hash audit, saved synthetic archive readback and kind-dispatch counterexample.
No solve, mesh, assembly, process fixture, mount or cgroup mutation.
"""
import ast
import copy
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import sys
from unittest.mock import patch

OUT=Path(__file__).resolve().parent
REPO=OUT.parents[2]
P=REPO/'CASE/D_series/D4_variable_groove_transport_20261023/reference_backend_min18_20261025/pilot_record_v3_20261026'
def read(p):return json.loads(p.read_text())
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
def write(p,d):
    with p.open('x') as f:json.dump(d,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')
def verify(items,base):
    errors=[str(base/p) for p,h in items.items() if not (base/p).is_file() or sha(base/p)!=h]
    assert not errors,errors
    return dict(count=len(items),mismatches=errors)

def main():
    d={'timestamp_utc':datetime.now(timezone.utc).isoformat()}
    d['source_lock']=verify(read(P/'source_lock.json')['files'],REPO)
    d['v3_artifacts']=verify(read(P/'evidence/final_integrity.json')['artifact_sha256'],P)
    d['v2_package']=verify(read(REPO/'docs/reports/D4_pilot_v2_release_review_20261026/review_inputs_sha256.json'),REPO)
    d['protected_history']=verify(read(REPO/'docs/reports/G4_derivation_source_audit_20261025/protected_inputs.json'),REPO)
    d['earlier_terminal_inputs']=verify(read(REPO/'docs/reports/D4_reference_terminal_review_20261026/review_inputs_sha256.json'),REPO)
    d['syntax_modules']=len(list(P.glob('*.py')))
    for p in P.glob('*.py'):ast.parse(p.read_text())
    d['existing_tests']=read(P/'evidence/test_summary.json')
    assert d['existing_tests']['tests']==32 and d['existing_tests']['failures']==d['existing_tests']['errors']==0
    assert (P/'evidence/test_no_solve.exit_code').read_text().strip()=='0'
    sys.path.insert(0,str(P))
    import common,readback,resources
    c=read(P/'contract_template.json');common.validate(c)
    try:common.validate(c,execution=True)
    except common.Rejected as exc:d['default_execution_rejection']=str(exc)
    else:raise AssertionError('Unexpected execution permission')
    d['archive_checks']=[]
    for f in sorted((P/'evidence').rglob('capture_manifest.json')):
        if read(f).get('archive_status')=='ARCHIVE_COMPLETE':
            d['archive_checks'].append({'path':str(f.parent),'result':readback.check_archive(f.parent)})
    offline=max((P/'evidence').glob('offline_*/offline_check.json'),key=lambda p:p.stat().st_mtime_ns)
    record=Path(read(offline)['record_dir']);work=record/'archive'
    d['offline_baseline']={'numerical_fixture':readback.check(work),'capture':readback.check_capture(record,work)}
    original=readback.load_json
    def inject_unknown(path):
        obj=original(path)
        if Path(path)==record/'capture_manifest.json':
            obj=copy.deepcopy(obj);obj['kind']='UNKNOWN_REVIEW_INJECTION'
        return obj
    with patch.object(readback,'load_json',side_effect=inject_unknown):
        unknown=readback.check_capture(record,work)
    d['kind_counterexample']={'method':'in-memory metadata injection into saved SYNTHETIC capture only',
        'changed_field':'capture_manifest.kind','replacement':'UNKNOWN_REVIEW_INJECTION',
        'observed':unknown,'expected':'reject unknown/inconsistent kind before choosing real or synthetic validation',
        'files_changed':False,'real_record_or_approval_created':False}
    assert unknown['status']=='CAPTURE_BINDING_PASS'
    mount=Path('/run/user/1000/sim240_pilot_n8_work_20261026')
    record_parent=Path('/home/dell/yuanyuanxu/SIM240_runtime_records/reference_pilot_n8_20261026')
    draft=common.template(mount,record_parent,c['cgroup_parent']);common.validate(draft)
    write(OUT/'path_contract_draft.json',draft)
    d['proposed_paths']={}
    for name,path in [('work_mount',mount),('record_parent',record_parent)]:
        ancestor=path
        while not ancestor.exists():ancestor=ancestor.parent
        st=os.statvfs(ancestor)
        d['proposed_paths'][name]={'path':str(path),'exists':path.exists(),'nearest_existing_ancestor':str(ancestor),
            'ancestor_mount':resources.mount_identity(ancestor),'ancestor_writable':os.access(ancestor,os.W_OK),
            'ancestor_available_bytes':st.f_bavail*st.f_frsize}
    d['uid_gid']=[os.getuid(),os.getgid()]
    d['MemAvailable_bytes']=int(next(x.split()[1] for x in Path('/proc/meminfo').read_text().splitlines() if x.startswith('MemAvailable:')))*1024
    resources.cgroup_parent_check(c['cgroup_parent'])
    d['cgroup_readonly']={'parent':c['cgroup_parent'],'status':'READ_ONLY_PREREQUISITE_PASS',
        'controllers':(Path(c['cgroup_parent'])/'cgroup.subtree_control').read_text().strip(),'group_created':False}
    d['forbidden_backend_modules_loaded']=[k for k in sys.modules if k.split('.')[0] in {'petsc4py','dolfinx','dolfinx_mpc','ufl'}]
    assert not d['forbidden_backend_modules_loaded']
    d.update(real_solver_called=False,existing_32_tests_rerun=False,mounts_created=False,actual_run_id=None,
             status='REVIEW_HOLD_ONE_SCHEMA_FIX_AND_VOLUME_PREPARATION')
    write(OUT/'audit_evidence.json',d)
    write(OUT/'review_inputs_sha256.json',{str(p.relative_to(REPO)):sha(p) for p in P.rglob('*') if p.is_file() and '__pycache__' not in p.parts})
    print(json.dumps({k:d[k] for k in ('source_lock','v3_artifacts','v2_package','protected_history','earlier_terminal_inputs','kind_counterexample','proposed_paths','MemAvailable_bytes','status')},indent=2))

if __name__=='__main__':main()

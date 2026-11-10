"""Read-only source/resource audit plus copied manual-array counterexample. No PDE."""
import ast
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
from datetime import datetime, timezone

REPO = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
P = REPO/'CASE/D_series/D4_variable_groove_transport_20261023/reference_backend_min18_20261025/pilot_record_v2_20261026'
def load(p): return json.loads(p.read_text())
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda:f.read(1048576),b''): h.update(chunk)
    return h.hexdigest()
def write(p,x):
    with p.open('x') as f: json.dump(x,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')
def verify(items,base):
    bad=[]
    for name,expected in items.items():
        p=base/name
        if not p.is_file() or sha(p)!=expected:bad.append(name)
    return {'count':len(items),'mismatches':bad}

def main():
    results={'timestamp_utc':datetime.now(timezone.utc).isoformat(),'real_solver_called':False}
    for name,items,base in [
        ('source_lock',load(P/'source_lock.json')['files'],REPO),
        ('protected_history',load(REPO/'docs/reports/G4_derivation_source_audit_20261025/protected_inputs.json'),REPO),
        ('previous_terminal_inputs',load(REPO/'docs/reports/D4_reference_terminal_review_20261026/review_inputs_sha256.json'),REPO),
        ('previous_package_artifacts',load(P/'evidence/final_integrity.json')['artifact_sha256'],P)]:
        results[name]=verify(items,base)
    modules=list(P.glob('*.py'))
    for p in modules:ast.parse(p.read_text(),filename=str(p))
    results['syntax_module_count']=len(modules)
    sys.path.insert(0,str(P))
    import common
    c=load(P/'contract_template.json')
    common.validate(c,execution=False)
    try: common.validate(c,execution=True)
    except common.Rejected as exc:results['draft_execution_rejection']=str(exc)
    else:raise AssertionError('Draft unexpectedly accepted')
    results['contract']={k:c[k] for k in ('version','planned_id','status','authorized_to_execute','approval','run_id')}
    results['paths']={k:{'path':c[k],'exists':Path(c[k]).exists(),'parent_exists':Path(c[k]).parent.exists()} for k in ('work_dir','record_dir')}
    from resources import cgroup_parent_check
    try: cgroup_parent_check(c['cgroup_parent']);cg='READ_ONLY_PREREQUISITE_PASS'
    except Exception as exc:cg=repr(exc)
    results['cgroup']={'parent':c['cgroup_parent'],'read_only_check':cg,
        'controllers':(Path(c['cgroup_parent'])/'cgroup.subtree_control').read_text().strip(),
        'group_created':False}
    results['MemAvailable_bytes']=int(next(x.split()[1] for x in Path('/proc/meminfo').read_text().splitlines() if x.startswith('MemAvailable:')))*1024
    st=os.statvfs(REPO);results['repository_disk_free_bytes']=st.f_bavail*st.f_frsize
    mounts=[]
    for line in Path('/proc/self/mountinfo').read_text().splitlines():
        left,right=line.split(' - ',1)
        if right.split()[0]!='tmpfs':continue
        p=Path(left.split()[4].replace('\\040',' '))
        try:
            s=os.statvfs(p)
            if p.is_dir() and os.access(p,os.W_OK):mounts.append({'path':str(p),'capacity_bytes':s.f_blocks*s.f_frsize,'within_cap':s.f_blocks*s.f_frsize<=c['resource_limits']['output_bytes']})
        except OSError:pass
    results['writable_tmpfs_mounts']=mounts
    # Counterexample reuses saved synthetic data only; does not launch fixture child.
    import numpy as np
    import readback
    src=P/'evidence/process_edf90e44f5/work/success'
    if not src.exists():
        candidates=list((P/'evidence/process_edf90e44f5').rglob('solution/manifest.json'))
        assert len(candidates)==1,candidates
        src=candidates[0].parent.parent
    copied=OUT/'counterexample_work'
    shutil.copytree(src,copied)
    baseline=readback.check(copied)
    spec=load(copied/'solution/manifest.json')
    for name,index in [('reconstructed_solution',0),('velocity_reconstructed_values',0)]:
        file=copied/'solution'/f'{name}.npy';a=np.load(file,allow_pickle=False);a[index]=7.;np.save(file,a,allow_pickle=False)
        spec['files'][file.name]['sha256']=sha(file)
    (copied/'solution/manifest.json').write_text(json.dumps(spec,indent=2)+'\n')
    changed=readback.check(copied)
    results['reconstruction_counterexample']={'kind':'COPIED_SYNTHETIC_MANUAL_ARRAYS_NOT_PDE',
        'source':str(src),'baseline':baseline,'after_internal_velocity_1_to_7':changed,
        'algebraic_vector_unchanged':True,'expected_reconstruction_discrepancy':6.,
        'scope':'check(work) only; no claim of a REAL capture passing; regenerated array hashes isolate missing numerical linkage'}
    assert baseline['status']=='DIAGNOSTIC_READBACK_PASS'
    assert changed['status']=='DIAGNOSTIC_READBACK_PASS'
    forbidden=[k for k in sys.modules if k.split('.')[0] in {'petsc4py','dolfinx','dolfinx_mpc','ufl'}]
    results['forbidden_backend_modules_loaded']=forbidden
    assert not forbidden
    assert all(not results[k]['mismatches'] for k in ('source_lock','protected_history','previous_terminal_inputs','previous_package_artifacts'))
    write(OUT/'audit_evidence.json',results)
    inputs={str(p.relative_to(REPO)):sha(p) for p in P.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
    write(OUT/'review_inputs_sha256.json',inputs)
    print(json.dumps({k:v for k,v in results.items() if k not in ('reconstruction_counterexample','writable_tmpfs_mounts')},indent=2))
if __name__=='__main__': main()

"""Read-only proposed-volume checks. Never mounts, writes probes, or starts a process."""
import json
import os
from pathlib import Path

HERE=Path(__file__).resolve().parent
def mount(path):
    candidates=[]
    for line in Path('/proc/self/mountinfo').read_text().splitlines():
        left,right=line.split(' - ',1);a=left.split();b=right.split()
        point=Path(a[4].replace('\\040',' ').replace('\\134','\\'))
        if path.is_relative_to(point):candidates.append((len(point.parts),dict(point=str(point),filesystem=b[0],
            mount_id=a[0],device=a[2],options=a[5].split(','),super_options=b[2].split(','))))
    return max(candidates,key=lambda x:x[0])[1]

def inspect(path):
    if not path.exists():return {'path':str(path),'exists':False}
    s=path.stat();fs=os.statvfs(path)
    return dict(path=str(path),exists=True,canonical=path.resolve()==path,is_directory=path.is_dir(),
        uid=s.st_uid,gid=s.st_gid,mode=oct(s.st_mode&0o777),st_dev=s.st_dev,
        writable=os.access(path,os.W_OK),mount=mount(path.resolve()),capacity_bytes=fs.f_blocks*fs.f_frsize,
        available_bytes=fs.f_bavail*fs.f_frsize,available_inodes=fs.f_favail,
        empty=path.is_dir() and next(path.iterdir(),None) is None)

def main():
    c=json.loads((HERE/'path_contract_draft.json').read_text())
    work,record=Path(c['work_dir']).parent,Path(c['record_dir']).parent
    w,r=inspect(work),inspect(record)
    checks={'work_exists':w['exists'],'record_exists':r['exists']}
    if w['exists']:
        options=set(w['mount']['options'])
        checks.update(work_exact_tmpfs_mount=w['mount']['point']==str(work) and w['mount']['filesystem']=='tmpfs',
            work_canonical_directory=w['canonical'] and w['is_directory'],work_empty=w['empty'],
            work_owner_mode=w['uid']==1000 and w['gid']==1000 and w['mode']=='0o700',
            work_options={'rw','nosuid','nodev'}<=options and 'noexec' not in options,
            work_capacity=0<w['capacity_bytes']<=512*1024**2,work_writable=w['writable'])
    if r['exists']:
        checks.update(record_canonical_directory=r['canonical'] and r['is_directory'],
            record_persistent=r['mount']['filesystem'] in {'ext4','xfs','btrfs','zfs'},
            record_owner_mode=r['uid']==1000 and r['gid']==1000 and r['mode']=='0o700',
            record_capacity=r['available_bytes']>=2*1024**3,record_writable=r['writable'])
    if w['exists'] and r['exists']:checks['separate_devices']=w['st_dev']!=r['st_dev']
    mem=int(next(x.split()[1] for x in Path('/proc/meminfo').read_text().splitlines() if x.startswith('MemAvailable:')))*1024
    checks['memory_available']=mem>=6*1024**3
    group=Path(c['cgroup_parent'])
    checks['delegated_memory_pids']=(group.exists() and os.access(group,os.W_OK)
        and {'memory','pids'}<=set((group/'cgroup.subtree_control').read_text().split()))
    checks['run_paths_unused']=not Path(c['work_dir']).exists() and not Path(c['record_dir']).exists()
    out=dict(status='LAYOUT_CHECK_PASS_ONLY' if all(checks.values()) else 'LAYOUT_NOT_READY',checks=checks,
        work=w,record=r,MemAvailable_bytes=mem,authorization=False,real_solver_called=False,
        limitations=['No write/fsync/ENOSPC/dynamic-library-load probe performed','Not a run permit'])
    print(json.dumps(out,indent=2,ensure_ascii=False))
    return 0 if all(checks.values()) else 2

if __name__=='__main__':raise SystemExit(main())

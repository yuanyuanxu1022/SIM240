"""Finite process supervision; hard memory cgroup and capped tmpfs prerequisites."""
import os
from pathlib import Path
import signal
import time


def hard_output_volume(parent, limit):
    parent=Path(parent).resolve(strict=True)
    found=False
    for line in Path('/proc/self/mountinfo').read_text().splitlines():
        left,right=line.split(' - ',1)
        point=left.split()[4].replace('\\040',' ').replace('\\134','\\')
        if point==str(parent) and right.split()[0]=='tmpfs':
            found=True
    stat=os.statvfs(parent)
    if not found or stat.f_blocks*stat.f_frsize>limit or any(parent.iterdir()):
        raise ValueError('DEDICATED_EMPTY_CAPPED_TMPFS_REQUIRED')
    return dict(mechanism='preexisting_dedicated_tmpfs', capacity_bytes=stat.f_blocks*stat.f_frsize,
                note='kernel filesystem capacity; inode/metadata exhaustion may fail earlier')


def cgroup_parent_check(parent):
    parent=Path(parent).resolve(strict=True)
    if not parent.is_relative_to(Path('/sys/fs/cgroup')):
        raise ValueError('CGROUP_V2_PATH_REQUIRED')
    if not {'memory','pids'}<=set((parent/'cgroup.subtree_control').read_text().split()):
        raise ValueError('DELEGATED_MEMORY_PIDS_CONTROLLERS_REQUIRED')
    if not os.access(parent,os.W_OK):
        raise ValueError('CGROUP_PARENT_NOT_WRITABLE')
    return parent


class MemoryGroup:
    def __init__(self,parent,name,limit):
        self.path=cgroup_parent_check(parent)/name
        self.path.mkdir(exist_ok=False)
        try:
            for name,value in [('memory.max',limit),('memory.swap.max',0),('memory.oom.group',1),('pids.max',32)]:
                (self.path/name).write_text(str(value))
            if (self.path/'memory.max').read_text().strip()!=str(limit):
                raise ValueError('MEMORY_LIMIT_NOT_INSTALLED')
            if not (self.path/'cgroup.kill').exists():
                raise ValueError('CGROUP_KILL_REQUIRED')
        except BaseException:
            self.path.rmdir()
            raise

    def stats(self):
        return {name:(self.path/name).read_text().strip() for name in
                ('memory.max','memory.peak','memory.events','pids.events','cgroup.events')}

    def kill(self):
        (self.path/'cgroup.kill').write_text('1')

    def drain(self):
        self.kill()
        deadline=time.monotonic()+2
        while 'populated 1' in (self.path/'cgroup.events').read_text() and time.monotonic()<deadline:
            time.sleep(.01)
        if 'populated 1' in (self.path/'cgroup.events').read_text():
            raise RuntimeError('CGROUP_DID_NOT_EMPTY')

    def close(self):
        self.drain()
        self.path.rmdir()


def tree_rss(pid):
    # A diagnostic sample only. Real memory enforcement uses memory.max.
    pending=[pid]; seen=set(); rss=0
    while pending:
        current=pending.pop()
        if current in seen: continue
        seen.add(current)
        try:
            status=Path(f'/proc/{current}/status').read_text()
            for line in status.splitlines():
                if line.startswith('VmRSS:'): rss+=int(line.split()[1])*1024
            pending.extend(map(int,Path(f'/proc/{current}/task/{current}/children').read_text().split()))
        except (FileNotFoundError,ProcessLookupError): pass
    return rss


def bytes_written(root):
    return sum(p.stat().st_size for p in Path(root).rglob('*') if p.is_file() and not p.is_symlink())


def supervise(proc,work,limits,group=None):
    start=time.monotonic(); reason=None; sent=None; peak_sample=0; peak_output=0
    while True:
        pid,status,usage=os.wait4(proc.pid,os.WNOHANG)
        if pid:
            code=os.waitstatus_to_exitcode(status); proc.returncode=code
            break
        peak_sample=max(peak_sample,tree_rss(proc.pid))
        peak_output=max(peak_output,bytes_written(work))
        now=time.monotonic()
        if reason is None:
            if now-start>=limits['wall_seconds']: reason='WALL_TIMEOUT'
            elif peak_sample>limits['memory_bytes']: reason='SAMPLED_MEMORY_EXCEEDED'
            elif peak_output>limits['output_bytes']: reason='SAMPLED_OUTPUT_EXCEEDED'
            if reason:
                try: os.killpg(proc.pid,signal.SIGTERM)
                except ProcessLookupError: pass
                sent=now
        elif sent is not None and now-sent>=limits['grace_seconds']:
            if group: group.kill()
            try: os.killpg(proc.pid,signal.SIGKILL)
            except ProcessLookupError: pass
            sent=None
        time.sleep(.02)
    # Child exit must never leave background descendants writing after hashing.
    if group: group.drain()
    try: os.killpg(proc.pid,signal.SIGKILL)
    except ProcessLookupError: pass
    stats=group.stats() if group else None
    if stats and int(dict(line.split() for line in stats['memory.events'].splitlines()).get('oom_kill','0')):
        reason='CGROUP_MEMORY_OOM'
    return dict(independent_exit_code=code, stop_reason=reason,
                direct_child_peak_RSS_KiB=usage.ru_maxrss,
                direct_child_cpu_seconds=usage.ru_utime+usage.ru_stime,
                sampled_tree_peak_RSS_bytes=peak_sample, sampled_output_peak_bytes=peak_output,
                wall_seconds=time.monotonic()-start,
                sampling_interval_seconds=.02,
                wall_limit_note='deadline detected by polling; grace/OS scheduling adds termination latency',
                memory_enforcement='cgroup_v2_memory.max' if group else 'SYNTHETIC_SAMPLE_ONLY',
                cgroup_stats=stats)

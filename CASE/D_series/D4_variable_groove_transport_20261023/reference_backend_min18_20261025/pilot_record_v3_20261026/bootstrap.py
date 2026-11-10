"""Join the preconfigured memory cgroup before exec of the fixed worker."""
import os
from pathlib import Path
import sys

if __name__=='__main__':
    group=Path(sys.argv[1])
    (group/'cgroup.procs').write_text(str(os.getpid()))
    os.execvpe(sys.argv[2],sys.argv[2:],os.environ.copy())

"""Fixed short process fixtures. No fluid/backend imports or linear solve."""
import sys
import time
from pathlib import Path
import numpy as np
from records import arrays


def fixture(root):
    arrays(root/'system',dict(csr_indptr=np.array([0,1,2,2,2,2],dtype=np.int64),
           csr_indices=np.array([0,1],dtype=np.int64),csr_values=np.array([1.,1.]),
           rhs_before=np.array([1.,0,0,0,0]),rhs_after=np.array([1.,0,0,0,0]),
           pressure_null_vector=np.array([0.,0,1,1,1])/np.sqrt(3)),
           dict(matrix_shape=[5,5],record_kind='SYNTHETIC_MANUAL_ARRAYS_NOT_PDE'))
    x=np.array([1.,0,2,2,2])
    fields=dict(algebraic_solution_before_backsub=x,reconstructed_solution=x,
        velocity_reconstructed_dof_indices=np.array([0,1],dtype=np.int64),
        pressure_reconstructed_dof_indices=np.array([2,3,4],dtype=np.int64),
        velocity_reconstructed_values=x[:2].copy(),wall_velocity_dof_indices=np.array([1],dtype=np.int64),
        periodic_slave_dofs=np.array([2],dtype=np.int64),periodic_master_dofs=np.array([3],dtype=np.int64),
        periodic_coefficients=np.ones(1),
        pressure_raw_P1=x[2:].copy(),pressure_zero_mean_P1=np.zeros(3),pressure_area_weights_hat2=np.ones(3))
    arrays(root/'solution',fields,dict(record_kind='SYNTHETIC_MANUAL_ARRAYS_NOT_PDE'))


if __name__=='__main__':
    mode=sys.argv[1];print('SYNTHETIC_STDOUT',mode,flush=True);print('SYNTHETIC_STDERR',file=sys.stderr,flush=True)
    if mode=='success': fixture(Path.cwd())
    elif mode=='failure':
        (Path.cwd()/'partial.bin').write_bytes(b'partial-raw-fixture');raise SystemExit(7)
    elif mode=='sleep':
        import subprocess,os
        child=subprocess.Popen([sys.executable,'-c','import time;time.sleep(20)'])
        (Path.cwd()/'descendant_pid.txt').write_text(str(child.pid))
        time.sleep(20)
    elif mode=='output':
        with Path('growing.bin').open('wb') as out:
            for _ in range(200):out.write(b'x'*65536);out.flush();time.sleep(.005)
    elif mode=='memory':
        values=[]
        for _ in range(512):values.append(bytearray(1024*1024));time.sleep(.002)
    else: raise SystemExit('UNKNOWN_FIXED_FIXTURE')

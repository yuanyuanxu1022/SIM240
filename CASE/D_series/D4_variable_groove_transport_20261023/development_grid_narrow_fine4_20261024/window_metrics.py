"""All windows, bounded deviation workspace, two-pass sample variance (ddof=1)."""
import numpy as np
from numpy.lib.stride_tricks import sliding_window_view

def metrics(main,cross,n,work_bytes=16*1024**2):
    main=np.asarray(main,dtype=float);cross=np.asarray(cross,dtype=float)
    if main.ndim!=1 or main.shape!=cross.shape or n<2 or len(main)<n:raise ValueError('invalid window inputs')
    if not np.isfinite(main).all() or not np.isfinite(cross).all():raise ValueError('nonfinite window inputs')
    # NumPy std uses a full deviation temporary per chunk; allow two copies of it.
    if work_bytes<2*n*8:raise ValueError('workspace too small for one window')
    block=max(1,work_bytes//(2*n*8));count=len(main)-n+1
    std=np.empty(count);span=np.empty(count);cm=np.empty(count)
    for start in range(0,count,block):
        stop=min(start+block,count)
        windows=sliding_window_view(main[start:stop+n-1],n)
        means=windows.mean(axis=1)
        if np.any(means==0):raise ValueError('zero mean window')
        std[start:stop]=windows.std(axis=1,ddof=1)/np.abs(means)
        span[start:stop]=np.ptp(windows,axis=1)/np.abs(means)
        cm[start:stop]=np.max(np.abs(sliding_window_view(cross[start:stop+n-1],n)),axis=1)
    return std,span,cm,{'window_steps':n,'windows':count,'block_rows':block,'max_dense_deviation_bytes':min(block,count)*n*8,'work_budget_bytes':work_bytes,'sample_ddof':1}

#!/usr/bin/env python3
"""Independently recompute every 1000-sample window in the selected nine records."""
from pathlib import Path
import csv
import hashlib
import json
import numpy as np

ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
def main():
    cases=json.loads((OUT/'nine_record_review.json').read_text());results=[];inputs={}
    for r in cases:
        p=ROOT/r['path']/'diagnostics.csv';inputs[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
        col='Jx' if r['case'] in ['Smooth75','EX240_parallel'] else 'Jy'
        J=[];cross=[];saved=[]
        with p.open() as f:
            for row in csv.DictReader(f):
                J.append(float(row['J']));cross.append(abs(float(row[col])));saved.append(float(row['window_rel_std']))
        J=np.array(J);cross=np.array(cross);view=np.lib.stride_tricks.sliding_window_view(J,1000)
        cv=np.lib.stride_tricks.sliding_window_view(cross,1000);first=None;maxdiff=0.
        for start in range(0,len(view),512):
            block=view[start:start+512];mean=block.mean(axis=1);deviation=block-mean[:,None]
            np.square(deviation,out=deviation)
            std=np.sqrt(deviation.sum(axis=1)/999)/np.abs(mean)
            span=(block.max(axis=1)-block.min(axis=1))/np.abs(mean)
            cr=cv[start:start+512].max(axis=1)
            good=np.flatnonzero((std<=1e-6)&(span<=5e-6)&(cr<=1e-12))
            if first is None and len(good):first=int(start+good[0]+999)
            maxdiff=max(maxdiff,float(np.max(np.abs(std-np.array(saved[start+999:start+999+len(std)])))))
        assert first==len(J)-1,(r['case'],r['dx_nm'],first,len(J)-1)
        results.append(dict(case=r['case'],dx_nm=r['dx_nm'],complete_windows=len(view),
                            first_qualifying_step=first,saved_final_step=len(J)-1,
                            first_stop_matches=True,max_std_difference_from_saved=maxdiff))
    report=dict(rows=sum(r['rows'] for r in cases),records=len(cases),all_first_stops_match=True,
                windows=sum(r['complete_windows'] for r in results),records_detail=results,
                workspace_deviation_array_bytes_max=512*1000*8,solver_started=False)
    (OUT/'full_window_review.json').write_text(json.dumps(report,indent=2)+'\n')
    (OUT/'window_read_inputs_sha256.json').write_text(json.dumps(inputs,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='records_detail'}))
if __name__=='__main__':main()

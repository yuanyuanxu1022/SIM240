#!/usr/bin/env python3
"""Run unchanged frozen analyzer with only a NumPy-scalar JSON exporter adapter.

No equations, thresholds, references or input files change. Original exit2/log
remain. This writes a fresh adapted output; it does not overwrite the failed one.
"""
from pathlib import Path
import json
import runpy
import sys
import numpy as np

BASE=Path(__file__).resolve().parents[1]
HERE=Path(__file__).resolve().parent
conversions={}
original=json.JSONEncoder.default

def scalar_export(self,obj):
    if isinstance(obj,np.generic):
        name=type(obj).__module__+'.'+type(obj).__name__
        conversions[name]=conversions.get(name,0)+1
        return obj.item()
    return original(self,obj)

if __name__=='__main__':
    json.JSONEncoder.default=scalar_export
    sys.path.insert(0,str(BASE))
    sys.argv=[str(BASE/'analyze_completed.py'),'--stage','alpha','--output',str(HERE/'frozen_export_adapted')]
    code=0
    try:runpy.run_path(str(BASE/'analyze_completed.py'),run_name='__main__')
    except SystemExit as exc:code=exc.code or 0
    finally:
        json.JSONEncoder.default=original
        with (HERE/'serialization_adapter_record.json').open('x') as f:
            f.write(json.dumps(dict(scope='JSON serialization of numpy scalars only',
                conversions=conversions,adapted_exit_code=code,frozen_source_modified=False,
                thresholds_modified=False,original_failed_exit_code=2),indent=2)+'\n')
    sys.exit(code)

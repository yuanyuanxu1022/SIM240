#!/usr/bin/env python3
"""Freeze this execution/acceptance layer once. Never compiles or invokes a solver."""
import ast
import json
from binding import ROOT,FROZEN_FILES,binding_path,make_binding,verify_binding

def main():
    if binding_path().exists():raise RuntimeError('binding already exists; no overwrite')
    for name in FROZEN_FILES:
        if name.endswith('.py'):ast.parse((ROOT/name).read_text())
    payload=make_binding()
    with binding_path().open('x') as f:f.write(json.dumps(payload,indent=2)+'\n')
    verify_binding()
    print('C_EXECUTION_LAYER_FROZEN',len(payload['sha256']),'inputs; no solver or compilation')

if __name__=='__main__':main()

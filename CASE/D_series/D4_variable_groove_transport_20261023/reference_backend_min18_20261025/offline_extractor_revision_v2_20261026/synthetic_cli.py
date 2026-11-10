"""Synthetic analysis process only. Real N8 paths are rejected by the reader."""
import argparse
import json
import sys
from pathlib import Path
from analysis_record import run_synthetic_analysis
from binding import digest,read_json


def main():
    p=argparse.ArgumentParser();p.add_argument('--binding',required=True,type=Path)
    p.add_argument('--trust',required=True,type=Path);p.add_argument('--trust-sha256',required=True)
    a=p.parse_args()
    trust=read_json(a.trust)
    if digest(trust)!=a.trust_sha256:
        print('TRUST_ANCHOR_CHANGED',file=sys.stderr);return 2
    try:
        code,out=run_synthetic_analysis(read_json(a.binding),trust)
    except Exception as e:
        print(type(e).__name__+': '+str(e),file=sys.stderr);return 2
    print(json.dumps(dict(analysis_output=str(out),analysis_exit_code=code,kind='SYNTHETIC_ONLY')))
    return code


if __name__=='__main__':raise SystemExit(main())

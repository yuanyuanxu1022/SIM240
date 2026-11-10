"""Read-only TGE preparation inspection; no execute switch or child processes."""
from pathlib import Path
import argparse,json,sys
CASE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(CASE.parent/'unseen_v2_reference_checker_S4_tge_v1/analysis'))
from tge_stage import verify_seal,require_pristine,static_summary

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--release',type=Path,required=True);ap.add_argument('--release-sha256',required=True)
    args=ap.parse_args()
    try:
        b=verify_seal(args.release.resolve(),args.release_sha256);require_pristine(b)
        print(json.dumps(static_summary(b),indent=2));code=0
    except Exception as e:print(type(e).__name__+': '+str(e),file=sys.stderr);code=2
    raise SystemExit(code)

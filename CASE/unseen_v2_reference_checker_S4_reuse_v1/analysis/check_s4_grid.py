"""Read-only local grid report from existing independently accepted S4 packets."""
from pathlib import Path
import argparse,json
from evidence import save
from contracts import output_location,release_inputs
from stage_s4 import verify_seal,validate_formal_authority,CASE
from s4_grid import grid_for_direction

def analyze(release,expected_sha,output):
    bound=verify_seal(release,expected_sha);validate_formal_authority(bound)
    accepted={r['run_id']:json.loads((CASE/'analysis_results'/r['run_id']/'acceptance.json').read_text()) for r in bound['prepared_runs']}
    reports=[grid_for_direction(bound,d,accepted,expected_sha) for d in ('P','T')]
    output=output_location(output,[*release_inputs(release),CASE/'analysis_results'],[release]);output.mkdir(parents=True,exist_ok=False)
    result=dict(stage='S4_THIN_GRID',release_sha256=expected_sha,directions=reports,GRID_CHECKS_PASS=all(r['GRID_CHECKS_PASS'] for r in reports),
        REFERENCE_QUALIFIED_FOR_CASE=False,MODEL_COMPARISON='NOT_EVALUATED',physical_validation='NOT_EVALUATED',submission_ready=False,solver_executed=False)
    save(output/'grid_report.json',result);return result

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--release',type=Path,required=True);parser.add_argument('--release-sha256',required=True);parser.add_argument('--out',type=Path,required=True);args=parser.parse_args()
    try:result=analyze(args.release,args.release_sha256,args.out)
    except Exception as error:
        import sys
        print(type(error).__name__+': '+str(error),file=sys.stderr);raise SystemExit(2)
    raise SystemExit(0 if result['GRID_CHECKS_PASS'] else 2)

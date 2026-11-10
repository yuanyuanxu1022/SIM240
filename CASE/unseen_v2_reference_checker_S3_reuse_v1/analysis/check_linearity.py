"""Offline local S3 control report; never runs native code or the 24-case aggregate."""
from pathlib import Path
import argparse,json
from evidence import need,sha,save
from contracts import output_location,release_inputs
from stage_s3 import verify_seal,validate_formal_authority
from s3_baselines import control_for_direction

def analyze(release,expected_sha,output):
    bound=verify_seal(release,expected_sha);validate_formal_authority(bound)
    case=Path(__file__).resolve().parents[2]/'unseen_v2_reference_S3_reuse_v1'
    accepted={}
    for r in bound['prepared_runs']:
        p=case/'analysis_results'/r['run_id']/'acceptance.json'
        need(p.is_file(),'new acceptance missing')
        accepted[r['run_id']]=json.loads(p.read_text())
    reports=[control_for_direction(bound,d,accepted,expected_sha) for d in ('P','T')]
    output=output_location(output,[*release_inputs(release),case/'analysis_results'],[release])
    # Freeze a new report only after all evidence was checked; no write inside old inputs.
    output.mkdir(parents=True,exist_ok=False)
    result=dict(stage='S3_REG_LINEARITY',release_sha256=expected_sha,directions=reports,
        S3_CONTROL_PASS=all(r['CONTROL_PASS'] for r in reports),REFERENCE_QUALIFIED_FOR_CASE=False,
        MODEL_COMPARISON='NOT_EVALUATED',physical_validation='NOT_EVALUATED',submission_ready=False,solver_executed=False)
    save(output/'linearity.json',result)
    return result
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--release',type=Path,required=True);p.add_argument('--release-sha256',required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    try:r=analyze(a.release,a.release_sha256,a.out)
    except Exception as error:
        import sys
        print(type(error).__name__+': '+str(error),file=sys.stderr);raise SystemExit(2)
    raise SystemExit(0 if r['S3_CONTROL_PASS'] else 2)

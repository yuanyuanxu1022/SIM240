"""Bind reviewed preparation to a local user-started fourteen-case permit."""
from pathlib import Path
import json,datetime,subprocess,shutil
HERE=Path(__file__).resolve().parent;CASE=HERE.parent;PROJECT=CASE.parents[2]
def sha(p):
    import hashlib
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
def main():
    if (HERE/'release.json').exists():raise SystemExit('release exists; never silently rebind existing version')
    preparation=json.loads((HERE/'evidence/preparation.json').read_text());review=json.loads((HERE/'evidence/prebinding_review.json').read_text())
    assert preparation['ok'] and review['ok'] and preparation['formal_steady_runs']==0
    assert preparation['collide_and_stream_calls']==0 and review['other_canonical_rows_rejected']==76
    assert not (CASE/'results/development_remaining14_20261024_v1').exists()
    original=json.loads((PROJECT/'docs/reports/D4_prediction_readiness_20261024/protected_inputs.json').read_text())
    assert all(sha(p)==v for p,v in original.items())
    plan=CASE/'development_completion_plan_20261024';plan_hashes=json.loads((plan/'artifact_hashes.json').read_text())
    assert all(sha(p)==v for p,v in plan_hashes.items())
    bind=dict(original);bind.update(plan_hashes)
    # The readiness verdict itself and proposal manifest are additional provenance.
    for p in [PROJECT/'docs/reports/D4_prediction_readiness_20261024/REPORT.md',PROJECT/'docs/reports/D4_prediction_readiness_20261024/readiness.json',PROJECT/'docs/reports/D4_prediction_readiness_20261024/final_integrity.json',plan/'artifact_hashes.json',plan/'final_integrity.json']:
        bind[str(p)]=sha(p)
    for p in HERE.rglob('*'):
        if p.is_file() and '__pycache__' not in p.parts and p.name not in ('release.json','execution.lock'):
            bind[str(p)]=sha(p)
    commit=subprocess.run(['git','-C','/home/dell/openlb','rev-parse','HEAD'],capture_output=True,text=True,check=True).stdout.strip()
    assert commit=='882924a9cfc8dcdf82909e39530789cb6f5ebcc4'
    import csv
    rows=list(csv.DictReader((HERE/'stage_cases.csv').open()))
    assert len(rows)==14
    release=dict(release_id='D4_remaining14_local_release_20261024_v1',batch_id='development_remaining14_20261024_v1',created_UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),released=True,meaning='local technical readiness for explicit user start; no scientific result or teacher approval claimed',user_authorized_preparation=True,AI_started_formal_run=False,teacher_approval_independently_verified=False,allowed_case_ids=[r['planned_case_id'] for r in rows],OpenLB_commit=commit,allowed_role='new_dev',numerical_protocol='unchanged original protocol/execution.json',bound_inputs_sha256=bind,analysis_automatically_run=False,next_stage_automatically_run=False,grid_released=False,prediction_released=False)
    with (HERE/'release.json').open('x') as f:json.dump(release,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps(dict(released=True,allowed_cases=14,bound_inputs=len(bind),release_sha256=sha(HERE/'release.json'),formal_run_started=False)))
if __name__=='__main__':main()

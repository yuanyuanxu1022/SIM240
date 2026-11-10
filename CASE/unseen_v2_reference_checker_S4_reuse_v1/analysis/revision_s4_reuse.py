"""Exact S1 ELF reuse with independently bound completed S3 predecessor files."""
from pathlib import Path
import difflib,json,math
from evidence import need,sha,kv

REVISION='URV-S4-S1-ELF-REUSE-v1'
ELF_SHA='5c3836e97c99feab88cd8e41773237f6ff642a10558f151b11e112563382b07b'
PARENT_SHA='04836ee00515ac961f80022153eb398ea1692f03b943ca713e7414ce9716b574'

def verify_predecessors(bound,anchor):
    """Only files/hashes/arithmetic; no imported old runner or reader execution."""
    from contracts import covered
    inputs=bound['inputs_sha256']
    release=covered(anchor['predecessor_release_path'],inputs)
    need(sha(release)==anchor['predecessor_release_sha256']==PARENT_SHA,'S4 exact S3 predecessor changed')
    prior=json.loads(release.read_text())
    need(prior['stage']=='S3_REG_LINEARITY' and prior['S4_authorized'] is False,'S3 must not grant S4 authority')
    need(all(inputs.get(p)==h for p,h in prior['inputs_sha256'].items()),'S4 drops historical input closure')
    need(bound['provenance']==prior['provenance'],'S4 genuine build roles changed')
    review=covered(anchor['predecessor_review_path'],inputs)
    need(sha(review)==anchor['predecessor_review_sha256'],'S3 completed review changed')
    reviewed=json.loads(review.read_text())
    need(reviewed['S3_FOUR_RUN_ACCEPTANCE'] is True and reviewed['S3_CONTROL_PASS'] is True and
         reviewed['S2_TWO_MIDPOINT_REUSE_ACCEPTANCE'] is True and reviewed['S3_release_sha256']==PARENT_SHA,
         'completed S3 and S2 prerequisites required')
    case=release.parents[1];points={}
    for record in prior['approved_runs']:
        run=Path(record['output_directory']);cp=covered(str(run/'completion.json'),inputs)
        ap=covered(str(case/'analysis_results'/record['run_id']/'acceptance.json'),inputs)
        c=json.loads(cp.read_text());a=json.loads(ap.read_text());cfg=kv(covered(record['run_config_path'],inputs))
        need(a['run_id']==c['run_id']==record['run_id'] and a['planned_case_id']==c['planned_case_id']==record['planned_case_id'],'predecessor identity')
        need(a['completion_sha256']==sha(cp) and a['release_sha256']==c['release_sha256']==PARENT_SHA,'predecessor completion binding')
        need(c['inputs_before_sha256']==c['inputs_after_sha256']==prior['inputs_sha256'] and c['inputs_unchanged'] is True,'predecessor input drift')
        need(c['independent_process_exit_code']==a['independent_exit_code']==0 and c['timed_out'] is False and c['resource_stop_reason'] is None,'predecessor process failure')
        need(a['RESULT_PASS'] is True and a['geometry_PASS'] is True and a['NUMERICAL_GATE']=='PASS','predecessor not accepted')
        actual={str(p.relative_to(run)) for p in run.rglob('*') if p.is_file() and p.name!='completion.json'}
        need(actual==set(c['output_sha256']),'predecessor output file set drift')
        for name,h in c['output_sha256'].items():
            path=(run/name).resolve();need(path.is_relative_to(run),'predecessor path escape')
            need(sha(covered(str(path),inputs))==h,'predecessor raw drift')
        raw=kv(run/'result.txt');K=float(cfg['nu_m2_s'])*float(raw['J_main_m2_s'])/float(cfg['acceleration_m_s2'])
        need(math.isclose(K,a['scalar']['K_m3'],rel_tol=1e-13),'predecessor K mismatch')
        points[(cfg['direction'],float(cfg['acceleration_m_s2']))]=K
    for d in ('P','T'):
        report=json.loads(covered(str(case/'launch_attempts'/PARENT_SHA/f'linearity_{d}.json'),inputs).read_text())
        refs=next(r for r in prior['baseline_references'] if r['direction']==d)
        vals=[points[(d,50000.)],refs['K_m3'],points[(d,200000.)]]
        L=(max(vals)-min(vals))/(sum(vals)/3)
        need(report['K_m3']==vals and report['CONTROL_PASS'] is True and L<=.001 and
             math.isclose(L,report['K_span_over_mean'],rel_tol=1e-14),'predecessor linearity mismatch')
    batch=json.loads(covered(str(case/'launch_attempts'/PARENT_SHA/'S3_completed.json'),inputs).read_text())
    need(batch['solver_runs']==4 and batch['S3_CONTROL_PASS'] is True and batch['next_stage_started'] is False,'S3 completed batch missing')

def verify_s4_reuse(bound,observed,checker_case):
    from contracts import covered
    from stage_s4 import validate_records,validate_formal_authority
    path=checker_case/'s4_revision/anchor.json';anchor=json.loads(covered(str(path),bound['inputs_sha256']).read_text())
    need(anchor['revision_id']==REVISION and anchor['simulation_authorized'] is False,'source anchor is not authority')
    need(bound.get('source_revision')==dict(id=REVISION,anchor=str(path),sha256=sha(path)),'S4 anchor binding mismatch')
    validate_records(bound,checker_case)
    need(observed==anchor['native_source_sha256'],'S4 source changed')
    binary=covered(bound['provenance']['native_binary'],bound['inputs_sha256'])
    need(str(binary)==anchor['native_binary_path'] and sha(binary)==anchor['native_binary_sha256']==ELF_SHA,'S4 original ELF required')
    source_by_name={Path(p).name:covered(p,bound['inputs_sha256']) for p in bound['provenance']['native_sources']}
    diffanchor=covered(anchor['source_diff_anchor_path'],bound['inputs_sha256'])
    need(sha(diffanchor)==anchor['source_diff_anchor_sha256'],'historical source-diff anchor drift')
    old=json.loads(diffanchor.read_text())
    need(set(source_by_name)==set(old['diffs']),'source diff map incomplete')
    for name,rec in old['diffs'].items():
        base=covered(rec['baseline_path'],bound['inputs_sha256']);delta=covered(rec['path'],bound['inputs_sha256'])
        need(sha(base)==rec['baseline_sha256'] and sha(delta)==rec['sha256'],'historical baseline/diff changed')
        actual=''.join(difflib.unified_diff(base.read_text().splitlines(True),source_by_name[name].read_text().splitlines(True),fromfile='baseline/'+name,tofile='revision/'+name))
        need(actual==delta.read_text(),'source no longer reconstructed by historical diff')
    audit=json.loads(covered(anchor['machine_audit_path'],bound['inputs_sha256']).read_text())
    need(audit['SOURCE_REVISION_AUDIT']=='PASS' and audit['binary_sha256']==ELF_SHA and
         anchor['instruction_audit_status']=='REUSED_EXACT_ELF_SCOPED_PASS','scoped historical audit mismatch')
    verify_predecessors(bound,anchor)
    if bound.get('simulation_authorized') is True:validate_formal_authority(bound)

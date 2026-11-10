"""Shared provenance contract for C execution and acceptance. No solver calls."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PARENT = ROOT.parent
EXECUTION_ID = 'C_BINDING_COMPAT_20261024_v2'
BATCH = 'alpha_c_20261024_binding_v2_c'
ALPHA_BATCH = 'alpha_c_20261022_v1_alpha'
PARENT_ID = 'ALPHA_C_DIAGNOSTICS_20261022_v1'
PARENT_SHA = 'a3409a57013cf537b969547075fe245c0012cac4185830406d4c616670ccba9a'
OLD_AGENTS = '5700b378f82065dd40fd04cec710b7ff16e228b50fcd9b303e4fcee83a8429c3'
NEW_AGENTS = '59d1cc514821d3a5caf4114db9267022fd6bfe85a4d2f26edfe20c4fb9e4fb9c'
ALPHA_VERDICT_SHA = '018467d378507ce4b90f467d39acb3e00cd5748c2b328173e3780db6520fdfa9'
ALPHA_EXPORT_SHA = 'd1a0701351664989b16fb775e756efabec30093432197dd57ddfc284ac858b3d'
FROZEN_FILES = ('binding.py','run_c.py','analyze_completed_c.py','freeze_execution.py',
                'test_binding.py','compatibility.json','physical_contract.json',
                'README.md','PROTOCOL_ADDENDUM.md')
GATES = dict(NUMERICAL_GATE='NOT_EVALUATED',RESULT_PASS='NOT_EVALUATED',geometry_PASS='NOT_EVALUATED')

def require(value, message):
    if not value: raise RuntimeError(message)

def read_bytes(path): return Path(path).read_bytes()
def digest(data): return hashlib.sha256(data).hexdigest()
def sha(path, read=read_bytes): return digest(read(Path(path)))
def read_json(path, read=read_bytes): return json.loads(read(Path(path)))
def now(): return datetime.now(timezone.utc).isoformat()
def binding_path(root=ROOT): return root/'execution_binding.json'
def paths(root=ROOT): return root/'evidence'/BATCH, root/'output'/BATCH
def command(case, output): return [str(PARENT/'build/coupled_check'),case['id'],str(output)]

def source_contract(protocol):
    result={k:protocol[k] for k in ('backend','material','thresholds','c_output')}
    result.update(parent_protocol_id=protocol['protocol_id'],cases=protocol['stages']['c'])
    return result

def checked_dependencies(root=ROOT, read=read_bytes):
    """Strict parent verification with one exact, reviewed administrative exception."""
    pb=PARENT/'evidence/build_binding.json'
    require(sha(pb,read)==PARENT_SHA,'parent binding changed')
    parent=read_json(pb,read); hashes=parent['sha256']
    require(parent['protocol_id']==PARENT_ID and len(hashes)==3401,'parent identity/count')
    agents=PARENT.parents[2]/'AGENTS.md'
    require(hashes.get(str(agents))==OLD_AGENTS,'unexpected historical AGENTS')
    require(sha(agents,read)==NEW_AGENTS,'unreviewed current AGENTS change')
    expected=dict(hashes);expected[str(agents)]=NEW_AGENTS
    for p,h in expected.items(): require(sha(p,read)==h,'parent/current input changed: '+p)
    policy=read_json(root/'compatibility.json',read)
    require(policy==dict(change_type='reviewed_administrative_file_only',path=str(agents),
        parent_sha256=OLD_AGENTS,accepted_current_sha256=NEW_AGENTS,
        reviewed_diff_sha256=sha(PARENT/'c_prerun_review_20261024/AGENTS_only_difference.diff',read),
        parent_binding_sha256=PARENT_SHA,alpha_verdict_sha256=ALPHA_VERDICT_SHA,
        alpha_export_provenance_sha256=ALPHA_EXPORT_SHA,other_changes_allowed=False),'compatibility policy changed')
    reconstructed=PARENT/'c_prerun_review_20261024/AGENTS_frozen_reconstructed.md'
    require(sha(reconstructed,read)==OLD_AGENTS,'historical administrative reconstruction changed')
    # Verify actual bytes of both revisions and their exact diff, not just policy labels.
    import difflib
    diff=''.join(difflib.unified_diff(read(reconstructed).decode().splitlines(True),read(agents).decode().splitlines(True),
        fromfile='frozen_reconstructed_AGENTS.md',tofile='current_AGENTS.md'))
    diffpath=PARENT/'c_prerun_review_20261024/AGENTS_only_difference.diff'
    require(read(diffpath).decode()==diff,'administrative diff inconsistent')
    protocol=read_json(PARENT/'protocol.json',read)
    require(protocol['protocol_id']==PARENT_ID and read_json(root/'physical_contract.json',read)==source_contract(protocol),'physical contract changed')
    vp=PARENT/'analysis_alpha/verdict.json'; ep=PARENT/'analysis_alpha/EXPORT_PROVENANCE.json'
    require(sha(vp,read)==ALPHA_VERDICT_SHA and sha(ep,read)==ALPHA_EXPORT_SHA,'alpha acceptance/provenance changed')
    verdict=read_json(vp,read); export=read_json(ep,read)
    mp=PARENT/'evidence'/ALPHA_BATCH/'manifest.json'; manifest=read_json(mp,read)
    require(verdict['stage']=='alpha' and verdict['batch_id']==ALPHA_BATCH and verdict['operator_contract_pass'] is True,'alpha contract not accepted')
    require(verdict['build_binding_sha256']==PARENT_SHA and verdict['input_manifest_sha256']==sha(mp,read),'alpha dependency digest')
    require(manifest['source_binding']==parent and manifest['batch_id']==ALPHA_BATCH and manifest['protocol_id']==PARENT_ID,'alpha historical binding')
    require(manifest['independent_exit_code']==0 and manifest.get('finished_utc') and manifest['source_hashes_unchanged'] and not manifest['source_mismatches'],'alpha incomplete')
    alpha_exit=mp.parent/'exit_code.txt'
    require(int(read(alpha_exit))==0,'alpha batch independent exit')
    require([r['id'] for r in verdict['all_cases']]==[c['id'] for c in protocol['stages']['alpha']] and
            all(r['operator_contract_pass'] is True for r in verdict['all_cases']) and
            len(verdict['matrix_checks'])==7 and all(r['passed'] is True for r in verdict['matrix_checks']),'alpha matrix acceptance')
    require(len(verdict['input_sha256'])==391,'alpha input set changed')
    for p,h in verdict['input_sha256'].items():
        require(sha(p,read)==h,'alpha raw evidence changed: '+p);expected[p]=h
    require(export['verdict_sha256']==ALPHA_VERDICT_SHA and export['original_frozen_analyzer_exit_code']==2 and export['adapted_analyzer_exit_code']==0,'alpha export history changed')
    independent=PARENT/'analysis_20261023/independent_review.json'
    require(sha(independent,read)==export['independent_review_sha256'],'alpha independent review changed')
    extras=(pb,vp,ep,alpha_exit,independent,reconstructed,diffpath)
    for p in extras: expected[str(p)]=sha(p,read)
    for name in FROZEN_FILES: expected[str(root/name)]=sha(root/name,read)
    dep=dict(batch_id=ALPHA_BATCH,manifest_sha256=sha(mp,read),verdict_sha256=ALPHA_VERDICT_SHA,
             export_provenance_sha256=ALPHA_EXPORT_SHA,parent_binding_sha256=PARENT_SHA,
             original_input_count=391,operator_contract_pass=True)
    return expected,dep,protocol

def make_binding(root=ROOT):
    hashes,dependency,protocol=checked_dependencies(root)
    return dict(schema_version=2,execution_id=EXECUTION_ID,batch_id=BATCH,physics_protocol_id=PARENT_ID,
                created_utc=now(),parent_binding_sha256=PARENT_SHA,
                administrative_change=read_json(root/'compatibility.json'),alpha_dependency=dependency,
                sha256=hashes,**GATES)

def verify_binding(root=ROOT, read=read_bytes):
    bound=read_json(binding_path(root),read)
    require(bound['schema_version']==2 and bound['execution_id']==EXECUTION_ID and bound['batch_id']==BATCH and
            bound['physics_protocol_id']==PARENT_ID and bound['parent_binding_sha256']==PARENT_SHA,'new binding identity')
    for k,v in GATES.items():require(bound[k]==v,'formal Gate changed')
    hashes,dependency,protocol=checked_dependencies(root,read)
    require(bound['sha256']==hashes,'new execution inputs/set changed')
    require(bound['alpha_dependency']==dependency and bound['administrative_change']==read_json(root/'compatibility.json',read),'new binding dependency changed')
    return bound,protocol

def post_mismatches(bound, binding_sha, root=ROOT):
    bad=[]
    for p,h in bound['sha256'].items():
        if not Path(p).is_file() or sha(p)!=h:bad.append(p)
    if not binding_path(root).is_file() or sha(binding_path(root))!=binding_sha:bad.append(str(binding_path(root)))
    return bad

def validate_completed(root, bound):
    """Execution provenance only. Numerical frame contents are checked separately."""
    protocol=read_json(PARENT/'protocol.json');cases=protocol['stages']['c']
    ev,out=paths(root); mp=ev/'manifest.json'; manifest=read_json(mp)
    require(manifest['schema_version']==2 and manifest['execution_id']==EXECUTION_ID and manifest['protocol_id']==EXECUTION_ID and
            manifest['physics_protocol_id']==PARENT_ID and manifest['batch_id']==BATCH and manifest['stage']=='c','C manifest identity')
    require(manifest['source_binding']==bound and manifest['execution_binding_sha256']==sha(binding_path(root)) and
            manifest['alpha_dependency']==bound['alpha_dependency'],'C manifest binding/dependency')
    require(manifest.get('finished_utc') and manifest['independent_exit_code']==0 and int((ev/'exit_code.txt').read_text())==0 and
            manifest['source_hashes_unchanged'] and manifest['source_mismatches']==[],'C batch incomplete/changed')
    require([e['case_id'] for e in manifest['cases']]==[c['id'] for c in cases],'C missing/reordered/duplicate cases')
    wanted={BATCH+'_'+c['id'] for c in cases}
    require({p.name for p in out.iterdir()}==wanted and {p.name for p in ev.iterdir()}==wanted|{'manifest.json','exit_code.txt'},'C batch directory set')
    for case,entry in zip(cases,manifest['cases']):
        rid=BATCH+'_'+case['id'];sub=ev/rid;data=out/rid
        require(entry['run_id']==rid and entry['stage']=='c' and entry['parameters']==case and entry['command']==command(case,data) and
                entry['cwd']==str(PARENT),'C child identity/command/parameters')
        require(entry==read_json(sub/'manifest.json') and entry['independent_exit_code']==0 and int((sub/'exit_code.txt').read_text())==0 and
                entry.get('started_utc') and entry.get('finished_utc'),'C child incomplete')
        require(datetime.fromisoformat(entry['finished_utc'])>=datetime.fromisoformat(entry['started_utc']),'C child time order')
        require((sub/'console.log').stat().st_size>0,'C child log empty')
        required={'config.json','result.json','frame_schema.json','history.csv','step1_pre.bin.gz',
                  'step1_post_collision.bin.gz','step1_post_stream.bin.gz','frames'}
        require(required.issubset({p.name for p in data.iterdir()}),'C required evidence missing')
        require({p.name for p in (data/'frames').iterdir()}=={f'step_{t}.bin.gz' for t in range(65)},'C frames missing/extra')
        result=read_json(data/'result.json')
        require(all(result[k]==64 for k in ('requested_steps','completed_steps','NS_collide_calls','CH_collide_calls')) and result['safe'] is True,'C zero-step/partial/unsafe result')
    return manifest,cases

def file_hashes(root):
    ev,out=paths(root)
    return {str(p.resolve()):sha(p) for base in (ev,out) for p in sorted(base.rglob('*')) if p.is_file()}

def summarize(results):
    require(len(results)==4 and all(not r['initialization_only'] for r in results),'C numeric results count/zero-step')
    implementation=all(r['implementation_contract_pass'] is True for r in results)
    amounts=all(r['physical_amount_drift_within_budget'] is True for r in results)
    safety=all(r['safety_pass'] is True for r in results)
    return dict(implementation_contract_pass=implementation,physical_amount_drift_within_budget=amounts,
                safety_pass=safety,complete_C_contract_pass=implementation and amounts and safety,**GATES)

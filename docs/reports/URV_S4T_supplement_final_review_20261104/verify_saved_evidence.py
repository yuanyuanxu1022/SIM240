"""Read saved evidence and do scalar arithmetic only; no project imports or subprocesses."""
from pathlib import Path
import datetime
import hashlib
import json
import math

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OLD = ROOT / 'CASE/unseen_v2_reference_S4_reuse_v1'
DRAFT = ROOT / 'docs/reports/URV_S4T_spatial_supplement_draft_20261104'

def read(p):
    return json.loads(Path(p).read_text())

def sha(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda: f.read(4*1024**2), b''):
            h.update(b)
    return h.hexdigest()

def kv(p):
    return dict(line.split('=', 1) for line in Path(p).read_text().splitlines()
                if '=' in line and not line.startswith('#'))

def require(ok, message):
    if not ok:
        raise ValueError(message)

def verify_mapping(mapping):
    for path, expected in mapping.items():
        require(sha(path) == expected, 'hash mismatch: ' + str(path))

def main():
    target = HERE / 'evidence_review.json'
    require(not target.exists(), 'report already exists; no overwrite')
    release_path = OLD / 'evidence/S4_formal_launch_release_v1_20261104_01.json'
    release_sha = sha(release_path)
    require(release_sha == 'e5f7de1e584b776f8cc9bf1dbb31f198422ce10984ba8ad7d729220afdcdd19b', 'wrong release')
    release = read(release_path)
    verify_mapping(release['inputs_sha256'])
    refs = read(DRAFT / 'baseline_references.json')
    require([r['dx_nm'] for r in refs] == [2.5, 1.25], 'wrong baseline family')
    summaries = []
    for ref in refs:
        rec = next(r for r in release['prepared_runs'] if r['run_id'] == ref['run_id'])
        for key in ['config', 'completion', 'acceptance']:
            require(sha(ref[key+'_path']) == ref[key+'_sha256'], 'baseline identity hash')
        run = Path(rec['output_directory'])
        cfg = kv(ref['config_path']); c = read(ref['completion_path']); a = read(ref['acceptance_path'])
        require(sha(rec['run_config_path']) == rec['run_config_sha256'] == ref['config_sha256'], 'config binding')
        require(cfg['direction'] == a['direction'] == 'T', 'wrong direction')
        require(float(cfg['dx_nm']) == a['dx_nm'] == ref['dx_nm'], 'wrong grid')
        for k, v in {'h_nm':30, 'd_nm':80, 'w_nm':120, 'period_nm':240, 'Ly_nm':240,
                     'nu_m2_s':1e-6, 'acceleration_m_s2':100000}.items():
            require(float(cfg[k]) == v, 'wrong physical parameter ' + k)
        require(c['run_id'] == a['run_id'] == cfg['run_id'] == ref['run_id'], 'wrong identity')
        require(a['stage'] == 'S4_THIN_GRID' and c['planned_case_id'] == a['planned_case_id'] == rec['planned_case_id'], 'wrong stage')
        require(a['RESULT_PASS'] is True and a['geometry_PASS'] is True and a['NUMERICAL_GATE'] == 'PASS', 'unaccepted baseline')
        require(a['independent_exit_code'] == c['independent_process_exit_code'] == 0, 'bad exit')
        require(c['timed_out'] is False and c['resource_stop_reason'] is None, 'resource failure')
        require(c['inputs_unchanged'] is True and c['inputs_before_sha256'] == c['inputs_after_sha256'] == release['inputs_sha256'], 'source drift')
        require(a['completion_sha256'] == sha(ref['completion_path']), 'acceptance/completion mismatch')
        require(c['release_sha256'] == a['release_sha256'] == ref['original_release_sha256'] == release_sha, 'release mismatch')
        require(c['output_sha256'] == ref['original_output_sha256'], 'output map mismatch')
        actual = {str(p.relative_to(run)) for p in run.rglob('*') if p.is_file() and p.name != 'completion.json'}
        require(actual == set(c['output_sha256']), 'output set drift')
        for name, h in c['output_sha256'].items():
            p = (run/name).resolve()
            require(p.is_relative_to(run) and sha(p) == h, 'output binding failure')
        raw = kv(run/'result.txt')
        k = float(cfg['nu_m2_s'])*float(raw['J_main_m2_s'])/float(cfg['acceleration_m_s2'])
        require(math.isclose(k, a['scalar']['K_m3'], rel_tol=1e-13) and k == ref['K_m3'], 'K mismatch')
        summaries.append(dict(run_id=ref['run_id'], K_m3=k, raw_files=len(actual), bindings_valid=True))
    grid = []
    for direction in ['P', 'T']:
        ks = []
        for tag in ['5', '2p5', '1p25']:
            rid = f'URV_S4_{direction}_dx{tag}_reuse_v1_20261103_01'
            run = OLD/'runs'/rid/'steady'; cfg = kv(run/'run_config.txt'); raw = kv(run/'result.txt')
            a = read(OLD/'analysis_results'/rid/'acceptance.json')
            k = float(cfg['nu_m2_s'])*float(raw['J_main_m2_s'])/float(cfg['acceleration_m_s2'])
            require(math.isclose(k, a['scalar']['K_m3'], rel_tol=1e-13), 'saved K mismatch')
            ks.append(k)
        x, y = ks[0]-ks[1], ks[1]-ks[2]
        require(x*y > 0 and min(abs(x), abs(y))/ks[2] > 1e-14, 'invalid differences')
        p = math.log(abs(x/y))/math.log(2); d = abs(ks[1]/ks[2]-1)
        gci = 1.25*d/math.expm1(p*math.log(2))
        grid.append(dict(direction=direction, K_m3=ks, p=p, D=d, GCI=gci,
                         GRID_CHECKS_PASS=p > 0 and d <= .01 and gci <= .01))
    require(grid[0]['GRID_CHECKS_PASS'] and not grid[1]['GRID_CHECKS_PASS'], 'historical result changed')
    tge_path = ROOT/'CASE/unseen_v2_reference_S4_tge_v1/evidence/preparation_A.json'
    tge = read(tge_path)
    verify_mapping(tge['inputs_sha256'])
    permissions = {k:v for k,v in tge.items() if k.endswith('_authorized')}
    require(all(v is False for v in permissions.values()), 'unexpected TGE execution authority')
    require(tge['approved_runs'] == tge['actual_formal_run_ids'] == [], 'unexpected TGE execution record')
    pristine = []
    for rec in tge['prepared_runs'] + tge['zero_prepared_runs']:
        names = sorted(p.name for p in Path(rec['output_directory']).iterdir())
        require(names == ['run_config.txt', 'run_manifest.txt'], 'prepared output directory used')
        pristine.append(dict(run_id=rec['run_id'], files=names))
    verify_mapping(read(HERE/'protected_inputs.json'))
    result = dict(checked_at=datetime.datetime.now().astimezone().isoformat(),
                  scope='saved hashes, bindings and scalar arithmetic only; no full checker replay',
                  original_inputs_verified=len(release['inputs_sha256']), original_release_sha256=release_sha,
                  baselines=summaries, original_grid=grid, original_S4_STAGE_ACCEPTED=False,
                  TGE_preparation_sha256=sha(tge_path), TGE_input_count=len(tge['inputs_sha256']),
                  TGE_execution_permissions=permissions, TGE_prepared_directories=pristine,
                  protected_input_count=len(read(HERE/'protected_inputs.json')),
                  static_evidence_checks_pass=True, native_calls=0, field_reader_calls=0,
                  full_scientific_checker_replays=0, new_run_ids=[], reference_qualified=False)
    with target.open('x') as f:
        json.dump(result, f, indent=2); f.write('\n')
    print(json.dumps({k:result[k] for k in ['static_evidence_checks_pass','original_inputs_verified',
                                          'TGE_input_count','protected_input_count','native_calls']}))

if __name__ == '__main__':
    main()

"""Export only independently accepted references, with rechecked raw/protocol bindings."""
from pathlib import Path
import argparse,csv,hashlib,json,math
HERE=Path(__file__).resolve().parent;CASE=HERE.parent;PROJECT=CASE.parents[2]
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
def load(p):return json.loads(Path(p).read_text())
def kv(p):return dict(s.split('=',1) for s in Path(p).read_text().splitlines() if '=' in s)
def canonical():return {r['planned_case_id']:r for r in csv.DictReader((CASE/'protocol/candidate_cases.csv').open(encoding='utf-8-sig'))}
def resolve(p):
    p=Path(p);return p.resolve() if p.is_absolute() else (PROJECT/p).resolve()
def canonical_digest(obj):return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def bundle_row(source,scalar,evidence,bound):
    ident=scalar['planned_case_id'];row=canonical()[ident]
    if row['blind_geometry']!='False' or row['role'] not in ('new_dev','grid_reference'):raise ValueError('only nonreserved development references')
    if row['dx_nm'] not in ('5','2.5','1.25') or (row['h_nm'],row['d_nm'],row['w_nm']) not in (('75','25','60'),('75','120','60'),('75','120','240')):raise ValueError('outside three grid families')
    out=Path(source).resolve();m=load(out/'run_manifest.json');r=kv(out/'result.txt');cfg=kv(out/'run_config.txt')
    if m['planned_case_id']!=ident or m['run_id']!=scalar['run_id'] or r['run_id']!=m['run_id'] or cfg['run_id']!=m['run_id']:raise ValueError('identity mismatch')
    if (out/'exit_code.txt').read_text().strip()!='0' or r['NUMERICAL_GATE']!='PASS' or r['geometry_PASS']!='true' or r['RESULT_PASS']!='false':raise ValueError('raw result not eligible')
    if not scalar['independent_numerical_gate'] or not scalar['geometry_PASS']:raise ValueError('independent scalar reference invalid')
    if not m['formal_simulation'] or m['model_prediction_data'] or cfg['mode']!='steady' or m['command']!=[str(CASE/'build/variable_groove_transport'),str(out/'run_config.txt')]:raise ValueError('formal mode or command differs')
    if cfg['output_directory']!=str(out):raise ValueError('output binding mismatch')
    for k,q in [('h_nm','h_nm'),('d_nm','d_nm'),('w_nm','w_nm'),('period_nm','P_nm'),('Ly_nm','Ly_nm'),('dx_nm','dx_nm'),('nu_m2_s','nu_m2_s'),('acceleration_m_s2','acceleration_m_s2')]:
        if cfg[k]!=row[q]:raise ValueError('canonical config mismatch '+k)
    if cfg['direction']!=row['direction'] or float(row['P_nm'])!=2*float(row['w_nm']) or row['P_nm']!=row['Ly_nm']:raise ValueError('direction or geometry family differs')
    for k,x in [('rho_phys_kg_m3',1000),('mu_phys_Pa_s',.001),('nu_phys_m2_s',1e-6),('tau',1)]:
        if not math.isclose(float(r[k]),x,rel_tol=1e-14):raise ValueError('material mismatch')
    for k,x in [('descriptor','D3Q19_FORCE'),('collision','ForcedBGK'),('periodicity','x_y')]:
        if r[k]!=x:raise ValueError('numerical method mismatch')
    if float(r['Keff_m3'])!=scalar['K_m3']:raise ValueError('K identity mismatch')
    for k,h in m['inputs_sha256'].items():bound[str(resolve(k))]=h
    for k,h in m['OpenLB_build_environment']['library_hashes'].items():bound[str(resolve(k))]=h
    for p in out.rglob('*'):
        if p.is_file():
            resolved=str(p.resolve());actual=sha(p)
            if resolved in bound and bound[resolved]!=actual:raise ValueError('raw input changed')
            bound[resolved]=actual
    return dict(h_nm=row['h_nm'],d_nm=row['d_nm'],w_nm=row['w_nm'],P_nm=row['P_nm'],Ly_nm=row['Ly_nm'],dx_nm=row['dx_nm'],direction=row['direction'],nu_m2_s=row['nu_m2_s'],rho_kg_m3=row['rho_kg_m3'],tau=row['tau'],acceleration_m_s2=row['acceleration_m_s2'],run_id=m['run_id'],planned_case_id=ident,K_m3=r['Keff_m3'],numerical_gate_pass=True,geometry_pass=True,independent_reference_accepted=True,acceptance_evidence=str(evidence),raw_output=str(out))

def verify_bundle(path):
    obj=load(path)
    if obj.get('schema')!='D4_bound_grid_references_v1' or not obj.get('bound_inputs_sha256'):raise ValueError('invalid bound bundle')
    check=dict(obj);digest=check.pop('bundle_sha256',None)
    if digest!=canonical_digest(check):raise ValueError('bundle payload hash differs')
    for k,h in obj['bound_inputs_sha256'].items():
        if sha(k)!=h:raise ValueError('evidence binding changed '+k)
    ids=set()
    for r in obj['rows']:
        if r['run_id'] in ids or r['evidence_bundle_sha256']!='BOUND_BY_CONTAINER':raise ValueError('duplicate or unbound reference')
        ids.add(r['run_id'])
        evidence=Path(r['acceptance_evidence'])
        if str(evidence.resolve()) not in obj['bound_inputs_sha256']:raise ValueError('acceptance evidence unbound')
        if evidence.name=='REPORT.md' and evidence.parent.name in ('D4_remaining14_acceptance_20261024','D4_prediction_readiness_20261024'):
            sub='scalar_acceptance' if evidence.parent.name=='D4_remaining14_acceptance_20261024' else 'screen_acceptance'
            records=load(evidence.parent/sub/'scalar_results.json')
            matches=[s for s in records if s['run_id']==r['run_id']]
        else:
            cert=load(evidence)
            if cert.get('independent_acceptance')!='PASS':raise ValueError('unaccepted certificate')
            matches=[s for s in cert['scalars'] if s['run_id']==r['run_id']]
        if len(matches)!=1:raise ValueError('reference absent from acceptance evidence')
        rebuilt=bundle_row(r['raw_output'],matches[0],evidence,{})
        if any(r.get(k)!=v for k,v in rebuilt.items()):raise ValueError('export row differs from bound raw source')
    return obj['rows']

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);ap.add_argument('--certificate',type=Path,action='append',default=[]);a=ap.parse_args()
    bound={};result=[];geoms={('75','25','60'),('75','120','60'),('75','120','240')}
    sources=[(PROJECT/'docs/reports/D4_remaining14_acceptance_20261024','scalar_acceptance'),(PROJECT/'docs/reports/D4_prediction_readiness_20261024','screen_acceptance')]
    for base,sub in sources:
        # Prior independent reports are frozen local evidence, verified against their artifact manifests.
        hashes=load(base/'artifact_hashes.json')
        for k,h in hashes.items():
            p=resolve(k) if Path(k).is_absolute() or str(k).startswith('docs/') else base/k
            if sha(p)!=h:raise ValueError('historical acceptance artifact changed '+str(p))
            bound[str(p.resolve())]=h
        for mapping in ['input_hashes.json','flow_files_sha256.json']:
            for k,h in load(base/sub/mapping).items():
                p=resolve(k)
                if sha(p)!=h:raise ValueError('historical raw data changed '+str(p))
                bound[str(p)]=h
        scalar=load(base/sub/'scalar_results.json');flow=load(base/sub/'flow_frames.json')
        if not flow['ok'] or not flow['all_payloads_finite']:raise ValueError('historical flow evidence failed')
        cases={r['row']['run_id']:r for r in load(base/sub/'field_cases.json')}
        for s in scalar:
            row=canonical()[s['planned_case_id']]
            if (row['h_nm'],row['d_nm'],row['w_nm']) not in geoms or row['acceleration_m_s2']!='100000':continue
            result.append(bundle_row(cases[s['run_id']]['output'],s,base/'REPORT.md',bound))
    for cert in a.certificate:
        obj=load(cert)
        if obj.get('independent_acceptance')!='PASS':raise ValueError('certificate not accepted')
        for k,h in obj['bound_inputs_sha256'].items():
            if sha(k)!=h:raise ValueError('new acceptance changed')
            bound[k]=h
        bound[str(cert.resolve())]=sha(cert)
        for s in obj['scalars']:result.append(bundle_row(s['output'],s,cert,bound))
    ids=[r['run_id'] for r in result]
    if len(ids)!=len(set(ids)):raise ValueError('duplicate reference')
    for k,h in bound.items():
        if sha(k)!=h:raise ValueError('bound reference input changed '+k)
    for r in result:r['evidence_bundle_sha256']='BOUND_BY_CONTAINER'
    obj={'schema':'D4_bound_grid_references_v1','rows':result,'bound_inputs_sha256':bound,'original_thresholds_unchanged':True};obj['bundle_sha256']=canonical_digest(obj)
    with a.output.open('x') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')
    verify_bundle(a.output);print(json.dumps({'exported_references':len(result),'bound_paths':len(bound),'coarse_only':not bool(a.certificate),'simulation_executed':False}))
if __name__=='__main__':main()

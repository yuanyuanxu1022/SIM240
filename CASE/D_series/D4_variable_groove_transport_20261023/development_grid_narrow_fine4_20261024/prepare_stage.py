"""Prepare configs and zero-step checks only. Never passes steady to a subprocess."""
from pathlib import Path
import csv,json,math,itertools,importlib.util,subprocess,datetime
HERE=Path(__file__).resolve().parent;CASE=HERE.parent;PROJECT=CASE.parents[2]
spec=importlib.util.spec_from_file_location('remaining_runner',HERE/'run_narrow4.py')
runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)
def writej(n,v):(HERE/n).write_text(json.dumps(v,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
def geometry(row,boundary):
    nx,ny,nh,nd,nw=[round(float(row[k])/float(row['dx_nm'])) for k in ('P_nm','Ly_nm','h_nm','d_nm','w_nm')]
    edge=(nx-nw)/2
    def fluid(x,z):return z>=0 and z<nh+nd*(edge<=x%nx<nx-edge)
    count=links=0
    directions=[v for v in itertools.product((-1,0,1),repeat=3) if sum(c*c for c in v) in (1,2)]
    for ix in range(nx):
        for iz in range(nh+nd):
            x,z=ix+.5,iz+.5
            if not fluid(x,z):continue
            count+=ny
            for cx,cy,cz in directions:
                if not fluid(x+cx,z+cz):
                    assert fluid(x+.25*cx,z+.25*cz) and not fluid(x+.75*cx,z+.75*cz)
                    links+=ny
    assert count==int(row['fluid_nodes_expected'])==int(boundary['material_1'])
    assert links==int(boundary['candidate_links'])==int(boundary['valid_distance_links'])==int(boundary['installed_links'])
    for key in ('geometric_fallback_count','missing_fluid_neighbour_fallback_count','unresolved_link_count'):assert int(boundary[key])==0
    for key in ('q_min','q_max','installed_q_min','installed_q_max'):assert float(boundary[key])==.5
    assert boundary['geometry_PASS']==boundary['q_audit_PASS']=='true'
    return dict(expected_fluid_nodes=count,expected_links=links,independent_D3Q19_directions=len(directions))
def main():
    if (HERE/'evidence/preparation.json').exists():raise SystemExit('preparation already exists; do not overwrite')
    original=json.loads((PROJECT/'docs/reports/D4_grid_narrow_fine4_preparation_20261024/protected_inputs_before.json').read_text())
    assert all(runner.sha(p)==v for p,v in original.items())
    plan=CASE/'development_completion_plan_20261024'
    for p,v in json.loads((plan/'artifact_hashes.json').read_text()).items():assert runner.sha(p)==v
    canonical=runner.csvrows(CASE/'protocol/candidate_cases.csv')
    ids=[r['planned_case_id'] for r in runner.csvrows(plan/'development_grid12.csv') if r['dx_nm']=='1.25' and r['w_nm']=='60']
    selected=[next(r for r in canonical if r['planned_case_id']==ident) for ident in ids]
    assert len(selected)==4 and all(runner.canonical_allowed(r) for r in selected)
    with (HERE/'stage_cases.csv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(selected[0]));w.writeheader();w.writerows(selected)
    runner.validate_table();runner.ensure_new_batch(runner.policy()['batch_id'])
    launch=HERE/'launch_configs';launch.mkdir(exist_ok=False)
    for r in selected:
        runner.template_path(r).write_text(runner.config_text(r));runner.ensure_case_not_completed(r)
    build=subprocess.run(['make','-C',str(CASE/'src'),'--question'],capture_output=True,text=True)
    assert build.returncode==0,'bound build is out of date; do not overwrite it without separate review'
    prior=json.loads((CASE/'evidence/preflight.json').read_text())
    assert runner.sha(CASE/'src/variable_groove_transport.cpp')==prior['source_sha256']
    assert runner.sha(CASE/'build/variable_groove_transport')==prior['binary_sha256']
    writej('evidence/build_reuse.json',dict(mode='REUSE_PREVIOUSLY_COMPILED_BOUND_BINARY',make_question_command=['make','-C',str(CASE/'src'),'--question'],exit_code=build.returncode,stdout=build.stdout,stderr=build.stderr,source_sha256=prior['source_sha256'],binary_sha256=prior['binary_sha256'],new_compilation=False))
    records=[];zero=HERE/'evidence/zero_step_checks';zero.mkdir(exist_ok=False)
    for row in selected:
        runner.resource_check(runner.policy())
        described,code=runner.base.launch(row,'describe',zero,'grid_narrow_fine4_describe_20261024',timeout=60)
        assert code==0
        effective=runner.base.kv(described/'effective_config.txt')
        h,d,dx=[float(row[k])*1e-9 for k in ('h_nm','d_nm','dx_nm')];nu=float(row['nu_m2_s']);dt=dx*dx/(6*nu)
        n=math.ceil(.75*h*h/(nu*dt)-1e-9);cap=math.ceil(8*(h+d)**2/(nu*dt)-1e-9)
        assert int(effective['window_steps'])==n==16200 and int(effective['maximum_steps'])==cap
        for key,expected in [('h_m',h),('d_m',d),('w_m',float(row['w_nm'])*1e-9),('Lx_m',float(row['P_nm'])*1e-9),('Ly_m',float(row['Ly_nm'])*1e-9),('dx_m',dx),('dt_s',dt),('acceleration_m_s2',1e5),('nu_m2_s',1e-6),('phi',.5)]:
            assert math.isclose(float(effective[key]),expected,rel_tol=1e-13,abs_tol=1e-25),(key,effective[key],expected)
        assert effective['formal_simulation']=='false'
        out,code=runner.base.launch(row,'precheck',zero,'grid_narrow_fine4_precheck_20261024',timeout=60)
        assert code==0
        result=runner.base.kv(out/'result.txt');boundary=runner.base.kv(out/'boundary_audit.txt')
        assert result['collide_and_stream_calls']=='0' and result['formal_simulation']=='false'
        assert result['geometry_PASS']==result['converter_PASS']==result['q_audit_PASS']=='true'
        independent=geometry(row,boundary)
        records.append(dict(case_id=row['planned_case_id'],describe_output=str(described),precheck_output=str(out),window_steps=n,maximum_steps=cap,geometry_PASS=True,q_PASS=True,collide_and_stream_calls=0,resources=json.loads((out/'resource_usage.json').read_text()),**independent))
    assert all(runner.sha(p)==v for p,v in original.items())
    writej('evidence/preparation.json',dict(ok=True,prepared_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),stage_cases=4,steady_configs=4,describe_runs=4,geometry_precheck_runs=4,distinct_geometries=2,independent_geometry_and_q_checks=True,collide_and_stream_calls=0,formal_steady_runs=0,binary_reused_without_recompile=True,old_protected_count=len(original),old_protected_unchanged=True,formal_batch_exists=False,resources=runner.resource_check(runner.policy()),records=records))
    print(json.dumps(dict(ok=True,describe_runs=4,precheck_runs=4,formal_steady_runs=0)))
if __name__=='__main__':main()

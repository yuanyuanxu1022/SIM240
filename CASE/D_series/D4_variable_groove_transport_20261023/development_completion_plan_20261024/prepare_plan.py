"""Generate review-only case/config/resource plans. Never imports or launches a solver."""
from pathlib import Path
from fractions import Fraction
import csv,json,hashlib,math,datetime,shutil
HERE=Path(__file__).resolve().parent;CASE=HERE.parent;PROJECT=CASE.parents[2]
REVIEW=PROJECT/'docs/reports/D4_prediction_readiness_20261024'
GiB=1024**3
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for x in iter(lambda:f.read(1048576),b''):h.update(x)
    return h.hexdigest()
def readcsv(p):return list(csv.DictReader(Path(p).open(encoding='utf-8-sig')))
def writej(n,v):(HERE/n).write_text(json.dumps(v,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
def writecsv(n,rs):
    with (HERE/n).open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(rs[0]));w.writeheader();w.writerows(rs)
def ceiling(x):return (x.numerator+x.denominator-1)//x.denominator
def main():
    if (HERE/'preparation.json').exists():raise SystemExit('Prepared plan exists; retain it and create a new version for changes.')
    protected=json.loads((REVIEW/'protected_inputs.json').read_text())
    assert all(sha(p)==v for p,v in protected.items())
    readiness=json.loads((REVIEW/'readiness.json').read_text());assert readiness['SCREEN_RESULT_PASS'] is True
    plan=readcsv(CASE/'protocol/candidate_cases.csv');table={r['planned_case_id']:r for r in plan}
    inventory=readcsv(REVIEW/'matrix_inventory.csv')
    missing=[table[r['planned_case_id']] for r in inventory if r['formal_result_present']=='False' and (r['role']=='new_dev' or (r['role']=='grid_reference' and r['reserved']=='False'))]
    coarse=sorted([r for r in missing if r['role']=='new_dev'],key=lambda r:(float(r['w_nm']),float(r['d_nm']),r['direction']))
    grids=sorted([r for r in missing if r['role']=='grid_reference'],key=lambda r:(-float(r['dx_nm']),float(r['w_nm']),float(r['d_nm']),r['direction']))
    assert len(coarse)==14 and len(grids)==12 and all(r['blind_geometry']=='False' for r in missing)
    # Read only the accepted development screen's resource records.
    samples=[];base_steps={}
    for r in json.loads((REVIEW/'screen_acceptance/scalar_results.json').read_text()):
        resource=CASE/'results/development_screen_20261023_v1'/r['run_id']/'steady/resource_usage.json'
        use=json.loads(resource.read_text());samples.append(dict(direction=r['direction'],a=r['acceleration_m_s2'],elapsed_seconds=use['elapsed_seconds'],steps=r['steps'],fluid_nodes=248832,seconds_per_fluid_node_record=use['elapsed_seconds']/(248832*(r['steps']+1)),source=str(resource)))
        if r['acceleration_m_s2']==1e5:base_steps[r['direction']]=r['steps']
    slow=max(r['seconds_per_fluid_node_record'] for r in samples)
    preflight=json.loads((CASE/'evidence/preflight.json').read_text())
    mesh_records={}
    for r in preflight['geometry_records']:
        q=table[r['row']];key=tuple(float(q[k]) for k in ('h_nm','d_nm','w_nm','P_nm','dx_nm'));mesh_records[key]=r
    now=datetime.datetime.now(datetime.timezone.utc).isoformat()
    mem={s.split(':')[0]:int(s.split()[1])*1024 for s in Path('/proc/meminfo').read_text().splitlines() if s.startswith(('MemTotal:','MemAvailable:','SwapTotal:','SwapFree:'))}
    free=shutil.disk_usage(CASE).free
    batch_info={
      'DEV14':dict(batch_id='development_remaining14_20261024_v1',predecessor='accepted development_screen_20261023_v1',minimum_available_RAM_GiB=2),
      'GRID_MID6':dict(batch_id='development_grid_mid6_20261024_v1',predecessor='DEV14 independently accepted',minimum_available_RAM_GiB=6),
      'GRID_NARROW_FINE4':dict(batch_id='development_grid_narrow_fine4_20261024_v1',predecessor='GRID_MID6 numerical and field acceptance; two-level comparisons descriptive',minimum_available_RAM_GiB=4),
      'GRID_WIDE_FINE_P':dict(batch_id='development_grid_wide_fine_P_20261024_v1',predecessor='two narrow geometry grid families accepted; separate long-run budget and RAM review',minimum_available_RAM_GiB=22),
      'GRID_WIDE_FINE_T':dict(batch_id='development_grid_wide_fine_T_20261024_v1',predecessor='GRID_WIDE_FINE_P numerical/field acceptance and resource review',minimum_available_RAM_GiB=22)
    }
    rows=[];configdir=HERE/'planned_configs';configdir.mkdir()
    for r in coarse+grids:
        h,d,w,P,dx=[Fraction(r[k]) for k in ('h_nm','d_nm','w_nm','P_nm','dx_nm')]
        group='DEV14' if r['role']=='new_dev' else ('GRID_MID6' if dx==Fraction('2.5') else ('GRID_NARROW_FINE4' if w==60 else 'GRID_WIDE_FINE_'+r['direction']))
        nodes=ceiling((P*P*h+w*P*d)/dx**3);assert nodes==int(r['fluid_nodes_expected'])
        window=ceiling(Fraction(9,2)*h*h/(dx*dx));cap=ceiling(48*(h+d)**2/(dx*dx))
        dt=float(dx*dx*Fraction(1,10**18)/Fraction(6,10**6))
        nx,ny,nz=int(P/dx),int(P/dx),int((h+d)/dx)
        memory_record=mesh_records[(float(h),float(d),float(w),float(P),float(dx))]
        # 6 Float32 components; padded full domain, up to 12 frames, text records.
        output_bytes=12*(nx+8)*(ny+8)*(nz+8)*24+(cap+1)*600+(nx+8)*(nz+8)*600+1024**2
        scenario_steps=min(cap,math.ceil(base_steps[r['direction']]*(5/float(dx))**2))
        record={**r,'plan_batch':group,'planned_batch_id':batch_info[group]['batch_id'],'window_steps':window,'maximum_steps':cap,'computed_dt_s':dt,'computed_fluid_nodes':nodes,'existing_geometry_precheck_peak_RSS_KiB':memory_record['resources']['max_rss_kb'],'existing_geometry_precheck_evidence':memory_record['output'],'step_cap_work_extrapolated_hours':nodes*(cap+1)*slow/3600,'screen_scaled_stopping_scenario_hours':nodes*(scenario_steps+1)*slow/3600,'estimated_uncompressed_output_bytes':output_bytes,'formal_run_prepared':False}
        rows.append(record)
        spec=dict(status='PLANNED_ONLY_NOT_A_RUN',planned_case_id=r['planned_case_id'],planned_batch_id=batch_info[group]['batch_id'],run_id_template=r['planned_case_id'].replace('CAND_','D4_',1)+'_'+batch_info[group]['batch_id'],solver_parameters=dict(mode='steady',direction=r['direction'],dx_nm=r['dx_nm'],h_nm=r['h_nm'],d_nm=r['d_nm'],w_nm=r['w_nm'],period_nm=r['P_nm'],Ly_nm=r['Ly_nm'],nu_m2_s=r['nu_m2_s'],acceleration_m_s2=r['acceleration_m_s2'],window_tstar=.75,max_time_H_diffusion=8,frame_tstar=[0,.01,.02,.05,.1,.2,.5,1,2,4,8]),rho_kg_m3=1000,tau=1,expected_window_steps=window,expected_maximum_steps=cap,expected_fluid_nodes=nodes,execution_released=False)
        (configdir/(r['planned_case_id']+'.json')).write_text(json.dumps(spec,ensure_ascii=False,indent=2)+'\n')
    assert len({r['planned_case_id'] for r in rows})==26
    writecsv('remaining_coarse14.csv',[r for r in rows if r['role']=='new_dev']);writecsv('development_grid12.csv',[r for r in rows if r['role']=='grid_reference']);writecsv('case_budget26.csv',rows)
    batches=[]
    for label,info in batch_info.items():
        subset=[r for r in rows if r['plan_batch']==label]
        reserve=math.ceil((4*GiB+2*sum(r['estimated_uncompressed_output_bytes'] for r in subset))/GiB)
        batches.append(dict(group=label,**info,cases=len(subset),minimum_free_disk_GiB=reserve,max_existing_precheck_peak_RSS_GiB=max(r['existing_geometry_precheck_peak_RSS_KiB'] for r in subset)*1024/GiB,step_cap_work_extrapolated_hours=sum(r['step_cap_work_extrapolated_hours'] for r in subset),screen_scaled_stopping_scenario_hours=sum(r['screen_scaled_stopping_scenario_hours'] for r in subset),snapshot_RAM_sufficient=mem['MemAvailable']>=info['minimum_available_RAM_GiB']*GiB,snapshot_disk_sufficient=free>=reserve*GiB,parallel_solver_processes=1,MPI_ranks=1,execution_released=False,automatic_next_batch=False))
    writecsv('batches.csv',batches);writej('batches.json',batches)
    writej('resource_snapshot.json',dict(time_utc=now,memory_bytes=mem,free_disk_bytes=free,performance_samples=samples,slowest_sample_seconds_per_node_record=slow,runtime_estimates_are_not_guarantees=True,output_estimate_assumptions='12 frames; 6 Float32 components; full mesh padded by 8 per dimension; 600 bytes/diagnostic row; 600 bytes/slice row; 2x total size +4GiB batch headroom',all_26_output_reserve_GiB=math.ceil((2*sum(r['estimated_uncompressed_output_bytes'] for r in rows)+4*GiB)/GiB),no_resource_reclamation_performed=True))
    sources=[CASE/'protocol/candidate_cases.csv',CASE/'protocol/execution.json',CASE/'development_stage_20261023/stage_cases.csv',CASE/'development_stage_20261023/held_grid_references.csv',CASE/'evidence/preflight.json',REVIEW/'matrix_inventory.csv',REVIEW/'readiness.json',REVIEW/'protected_inputs.json',REVIEW/'screen_acceptance/scalar_results.json',HERE/'prepare_plan.py',HERE/'GRID_PROTOCOL.md',HERE/'grid_policy.json',HERE/'compare_grid.py']
    sources += [Path(r['source']) for r in samples]
    writej('input_hashes.json',{str(p):sha(p) for p in sources})
    writej('preparation.json',dict(plan_id='D4_development_completion_plan_20261024_v1',created_utc=now,status='REVIEWABLE_PLAN_NOT_EXECUTION_RELEASE',coarse_cases=14,grid_cases=12,config_templates=26,batches=5,original_protected_count=len(protected),original_protected_unchanged=all(sha(p)==v for p,v in protected.items()),solver_source_changed=False,binary_recompiled=False,solver_runs=0,grid_results_read=False,prediction_results_read=False,run_directories_created=False,release_created=False,technical_runner_implemented=False,formal_input_binding_prepared=False,teacher_approval_claimed=False,new_run_id=None,next_action='Review plan and implement/audit a separately bound DEV14 execution entry; keep grids and prediction held.'))
    print(json.dumps(batches,ensure_ascii=False,indent=2))
if __name__=='__main__':main()

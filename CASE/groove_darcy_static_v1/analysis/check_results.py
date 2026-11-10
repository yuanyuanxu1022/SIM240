#!/usr/bin/env python3
"""GDI checker 1.0.0. Read completed runs only; no solver imports or launches."""
import argparse
import json
import math
from pathlib import Path
import re
from sdi_metrics import evaluate, read_csv, sha

CHECKER_VERSION='GDI-1.0.0'
def require(ok,message):
    if not ok: raise ValueError(message)
def numbers(path):return read_csv(path)
def relative_difference(actual,expected):return abs(actual-expected)/max(abs(expected),1e-300)
def metric(checks,name,value,limit):
    require(math.isfinite(value),'Nonfinite metric '+name)
    checks.append(dict(name=name,value=value,limit=limit,satisfied=value<=limit))
def ids(rows,count):
    result={}
    for r in rows:
        i=int(r['cell_id']); require(i==r['cell_id'] and 0<=i<count and i not in result,'Duplicate/invalid cell id')
        result[i]=r
    require(len(result)==count,'Incomplete cell table')
    return result

def expected_configuration(cfg,protocol):
    require(cfg['case_id']=='GDI01' and cfg['protocol_id']=='GDI-v1','Unsupported GDI identity')
    require(protocol['protocol_id']=='GDI-v1' and protocol['first_case_only']=='GDI01','Wrong protocol')
    require(cfg['thresholds']==protocol['inherited_SDI_thresholds'] and cfg['linear_solver']==protocol['inherited_linear_solver'],'Frozen thresholds changed')
    q=protocol['inputs']; h=q['mesaGap_m'];d=q['grooveDepth_m'];w=q['grooveWidth_m'];P=q['period_m']
    require(q['family']=='V2_published_rounded' and q['groove_axis']=='y' and q['drive_axis']=='x' and q['porous_zone_cells']==512,'Wrong GDI01 formula/direction/zone')
    H=h+w/P*d;a=h**3;b=(h+d)**3
    kp=(a+b)/24/(1+1.7685*(d/w)**1.6331)
    kt=(a*b)/(6*(a+b))/(1+0.4900*(d/w)**0.6990)
    require(cfg['pressure_units']=='Pa' and cfg['velocity_definition']=='U=J/H','Wrong pressure/velocity definition')
    require(cfg['H_m']==q['H_m'] and cfg['mesh_cells']==q['mesh_cells'] and cfg['L_m']==q['L_m']
        and cfg['mu_Pa_s']==q['mu_Pa_s'] and cfg['rho_kg_m3']==q['rho_kg_m3'] and cfg['G_Pa_per_m']==q['G_Pa_m'],'Shared physical input mismatch')
    for x,y in [(cfg['K_m3'][0][0],kt),(cfg['K_m3'][1][1],kp),(cfg['H_m'],H),
        (cfg['D_m_minus2'][0][0],H/kt),(cfg['D_m_minus2'][1][1],H/kp)]:require(abs(x/y-1)<=1e-12,'K/H/D formula mismatch')
    require(cfg['K_m3'][0][1]==0 and cfg['K_m3'][1][0]==0,'Off-axis input')
    return cfg

def integration_checks(cfg,protocol,cells,faces,coefficients,evidence,history,solver):
    checks=[];N=512;C=ids(cells,N);D=ids(coefficients,N);R=ids(evidence,N)
    H=cfg['H_m'];mu=cfg['mu_Pa_s'];G=cfg['G_Pa_per_m'];lx,ly,_=cfg['L_m'];nx,ny,_=cfg['mesh_cells']
    dx=lx/nx;dy=ly/ny;dp=G*lx;Ustar=cfg['K_m3'][0][0]*G/mu/H;Qs=H*Ustar*ly
    extra=protocol['additional_pre_run_fixed_checks'];ctol=extra['coefficient_relative_tolerance']
    ex=cfg['D_m_minus2'];target=[[ex[0][0],ex[0][1],0],[ex[1][0],ex[1][1],0],[0,0,0]]
    maxD=max(target[0][0],target[1][1]);coefError=0;grid={}
    for i,c in C.items():grid[(round(c['x_m']/dx-.5),round(c['y_m']/dy-.5))]=i
    for i in C:
        require(D[i]['zone_member']==1,'Cell outside porous zone')
        coefError=max(coefError,abs(D[i]['H_m']/H-1))
        for a in range(3):
            for b in range(3):coefError=max(coefError,abs(D[i]['D'+'xyz'[a]+'xyz'[b]+'_m_minus2']-target[a][b])/maxD)
    metric(checks,'actual_model_coefficient_relative',coefError,ctol)
    volume=math.fsum(c['volume_m3'] for c in cells)
    sums=dict(momentum=[],deltaU=[],force=[],gradient=[],source=[],diag=[],split=[])
    energy=[];maxDP=0
    def dot(A,B):return math.fsum(a*b for a,b in zip(A,B))
    def norm(v):return math.sqrt(dot(v,v))
    for (ix,iy),i in grid.items():
        c=C[i];v=c['volume_m3'];r=R[i];u=[c['U'+a+'_m_s'] for a in 'xyz'];old=[r['old_U'+a+'_m_s'] for a in 'xyz']
        pr=(24 if ix==0 else (c['p_Pa']+C[grid[ix-1,iy]]['p_Pa'])/2)
        pl=(0 if ix==nx-1 else (c['p_Pa']+C[grid[ix+1,iy]]['p_Pa'])/2)
        pb=(c['p_Pa'] if iy==0 else (c['p_Pa']+C[grid[ix,iy-1]]['p_Pa'])/2)
        pt=(c['p_Pa'] if iy==ny-1 else (c['p_Pa']+C[grid[ix,iy+1]]['p_Pa'])/2)
        gradient=[(pl-pr)/dx,(pt-pb)/dy,0]
        d=[[D[i]['D'+a+b+'_m_minus2'] for b in 'xyz'] for a in 'xyz']
        force=[mu*v*dot(row,u) for row in d]
        actualForce=[r['force_'+a+'_N'] for a in 'xyz']
        residual=[force[a]/v+gradient[a] for a in range(3)]
        a=mu*sum(d[k][k] for k in range(3))
        src=[v*(a*old[k]-mu*dot(d[k],old)) for k in range(3)]
        sums['momentum'].append(norm(residual)/G);sums['deltaU'].append(norm([x-y for x,y in zip(u,old)])/Ustar)
        sums['force'].append(norm([x-y for x,y in zip(actualForce,force)])/(G*v))
        sums['gradient'].append(norm([r['grad_p'+a+'_Pa_m']-gradient[k] for k,a in enumerate('xyz')])/G)
        sums['source'].append(norm([r['source_'+a+'_N']-src[k] for k,a in enumerate('xyz')])/(G*v))
        sums['diag'].append(abs(r['diag_kg_s']/(v*a)-1))
        # Consistency of deferred splitting at the saved old U.
        oldForce=[mu*v*dot(row,old) for row in d]
        sums['split'].append(norm([r['diag_kg_s']*old[k]-r['source_'+a+'_N']-oldForce[k] for k,a in enumerate('xyz')])/(G*v))
        energy.append(dot(actualForce,u));maxDP=max(maxDP,abs(c['p_Pa']-r['old_p_Pa'])/dp)
    weights=[C[i]['volume_m3'] for i in grid.values()]
    rms=lambda vals:math.sqrt(math.fsum(x*x*w for x,w in zip(vals,weights))/volume)
    derived=dict(momentum_L2_relative=rms(sums['momentum']),momentum_max_relative=max(sums['momentum']),
        delta_U_L2_relative=rms(sums['deltaU']),delta_U_max_relative=max(sums['deltaU']),delta_p_max_relative=maxDP)
    for name in ['momentum_L2_relative','momentum_max_relative']:metric(checks,name,derived[name],extra['unsplit_momentum_relative_L2_and_max'])
    for name in ['delta_U_L2_relative','delta_U_max_relative']:metric(checks,name,derived[name],extra['outer_velocity_change_relative_L2_and_max'])
    metric(checks,'delta_p_max_relative',maxDP,extra['outer_pressure_change_relative_max'])
    for name in ['force','source','diag','split']:metric(checks,name+'_independent_consistency',max(sums[name]),ctol)
    metric(checks,'exported_gradient_consistency',max(sums['gradient']),extra['unsplit_momentum_relative_L2_and_max'])
    imbalance={i:[] for i in C}
    for f in faces:
        imbalance[int(f['owner'])].append(f['phi_m3_s'])
        if f['neighbour']>=0:imbalance[int(f['neighbour'])].append(-f['phi_m3_s'])
    matrixMismatch=math.fsum(abs(math.fsum(imbalance[i])+R[i]['pressure_matrix_raw_residual_m3_s']) for i in C)/Qs
    metric(checks,'pressure_matrix_residual_vs_conservative_flux',matrixMismatch,ctol)
    raw=math.fsum(abs(r['pressure_matrix_raw_residual_m3_s']) for r in evidence)
    n=int(solver['outer_iterations']);require(n==solver['outer_iterations'] and 1<=n<=2000 and len(history)==n,'Missing outer iteration history')
    historyOK=True
    for k,row in enumerate(history,1):
        require(all(v>=0 for v in row.values()),'Negative iteration diagnostic')
        require(row['outer']==k and row['linear_iterations']==int(row['linear_iterations']) and 0<=row['linear_iterations']<=2000,'Invalid iteration count')
        require(row['initial_raw_L1_m3_s']>0 and row['final_raw_L1_m3_s']>=0,'Invalid residual normalization')
        historyOK &= row['normalized_residual']<=1e-12 and row['true_normalized_residual']<=1e-12
        require(abs(row['final_raw_L1_m3_s']/row['initial_raw_L1_m3_s']-row['true_normalized_residual'])<=ctol,'History true residual inconsistent')
    metric(checks,'all_pressure_solves_converged',0 if historyOK else 1,0)
    require(solver['iterations']==history[-1]['linear_iterations'],'Final linear iteration identity mismatch')
    for key in ['normalized_residual','true_normalized_residual']:require(abs(solver[key]-history[-1][key])<=ctol,'Final solver/history mismatch')
    require(relative_difference(raw,history[-1]['final_raw_L1_m3_s'])<=ctol,'Matrix residual sum mismatch')
    require(relative_difference(raw,solver['raw_residual_L1_m3_s'])<=ctol,'Raw pressure residual metadata mismatch')
    for key,value in derived.items():metric(checks,key+'_history_consistency',abs(value-history[-1][key]),extra['unsplit_momentum_relative_L2_and_max'])
    Q=math.fsum(f['phi_m3_s'] for f in faces if f['patch']=='xHigh');W=dp*Q;E=math.fsum(energy)
    metric(checks,'force_based_energy_relative',abs(E-W)/max(abs(W),1e-300),cfg['thresholds']['power_dissipation_relative'])
    metric(checks,'force_based_positive_energy',0 if E>=0 and W>0 else 1,0)
    return dict(checks=checks,derived=derived,force_dissipation_W=E,pressure_power_W=W)

def strip_comments(text):return re.sub(r'//[^\n]*','',re.sub(r'/\*.*?\*/','',text,flags=re.S))
def block(text,name):
    match=re.search(r'\b'+re.escape(name)+r'\s*\{',text);require(match is not None,'Missing native block '+name)
    start=match.end();i=start;level=1
    while level and i<len(text):
        if text[i]=='{':level+=1
        elif text[i]=='}':level-=1
        i+=1
    require(level==0,'Truncated native block');return text[start:i-1]
def native_values(text,keyword,count,components):
    match=re.search(r'\b'+keyword+r'\s+(uniform|nonuniform)\s+',text);require(match is not None,'Missing native field '+keyword)
    tail=text[match.end():]
    if match[1]=='uniform':body=tail.split(';',1)[0]
    else:
        header=re.match(r'List<\w+>\s+(\d+)\s*\(',tail);require(header is not None and int(header[1])==count,'Native list size mismatch')
        start=header.end();i=start;level=1
        while level and i<len(tail):
            if tail[i]=='(':level+=1
            elif tail[i]==')':level-=1
            i+=1
        require(level==0,'Truncated native list');body=tail[start:i-1]
    vals=[float(v) for v in re.findall(r'[-+]?(?:\d*\.\d+|\d+\.?\d*)(?:[eE][-+]?\d+)?',body)]
    require(all(math.isfinite(v) for v in vals),'Nonfinite native field')
    if match[1]=='uniform':require(len(vals)==components,'Bad uniform value');vals*=count
    require(len(vals)==count*components,'Bad native value count');return vals
def native_check(case,cells,faces):
    result={};cells=sorted(cells,key=lambda c:c['cell_id'])
    dims={'p':[1,-1,-2,0,0,0,0],'U':[0,1,-1,0,0,0,0],'J':[0,2,-1,0,0,0,0],'phi':[0,3,-1,0,0,0,0],'phi_U':[0,3,-1,0,0,0,0]}
    for name,columns in [('p',['p_Pa']),('U',['U'+a+'_m_s' for a in 'xyz']),('J',['J'+a+'_m2_s' for a in 'xyz']),('phi',['phi_m3_s']),('phi_U',['phi_U_m3_s'])]:
        text=strip_comments((case/'1'/name).read_text());match=re.search(r'dimensions\s*\[([^\]]+)\]',text)
        require(match is not None and [int(v) for v in match[1].split()]==dims[name],'Wrong native field dimensions')
        if name in ['p','U','J']:
            expected=[c[k] for c in cells for k in columns];vals=native_values(text,'internalField',len(cells),len(columns));require(vals==expected,'Native cell field/CSV mismatch')
        else:
            interior=sorted((f for f in faces if f['neighbour']>=0),key=lambda f:f['face_id'])
            vals=native_values(text,'internalField',len(interior),1);require(vals==[f[columns[0]] for f in interior],'Native internal flux/CSV mismatch')
            for patch in ['xLow','xHigh','yLow','yHigh']:
                rows=sorted((f for f in faces if f['patch']==patch),key=lambda f:f['face_id'])
                vals=native_values(block(block(text,'boundaryField'),patch),'value',len(rows),1)
                require(vals==[f[columns[0]] for f in rows],'Native boundary flux/CSV mismatch')
        result[name]='equal_to_CSV'
    ptext=strip_comments((case/'1/p').read_text());bd=block(ptext,'boundaryField')
    require(all(v==24 for v in native_values(block(bd,'xLow'),'value',32,1)),'Wrong native inlet pressure')
    require(all(v==0 for v in native_values(block(bd,'xHigh'),'value',32,1)),'Wrong native outlet pressure')
    return result

def check_run(run):
    manifest=json.loads((run/'run_manifest.json').read_text())
    require(manifest['case_id']=='GDI01' and manifest['protocol_id']=='GDI-v1' and re.fullmatch(r'GDI01_v1_[A-Za-z0-9_]+',manifest['run_id']),'Wrong bound run identity')
    require(len(manifest['files'])>=20,'Missing bound input evidence')
    seen=set()
    for rec in manifest['files']:
        p=Path(rec['path']);require(not p.is_absolute() and '..' not in p.parts and str(p) not in seen,'Unsafe/duplicate manifest path')
        seen.add(str(p));require(sha(run/p)==rec['sha256'],'Bound input changed: '+str(p))
    needed=['common/GDI01.json','common/protocol.json','bin/grooveDarcyStaticFoam','lib/libgroovePorosity.so',
        'openfoam/constant/polyMesh/cellZones','openfoam/constant/fvModels','provenance/analysis/check_results.py',
        'provenance/analysis/sdi_metrics.py','provenance/common/release_manifest.json']
    require(all(p in seen for p in needed),'Required manifest binding missing')
    require(sha(run/'provenance/common/release_manifest.json')==manifest['release_manifest_sha256'],'Release snapshot mismatch')
    release=json.loads((run/'provenance/common/release_manifest.json').read_text())
    require(release['case_id']=='GDI01' and release['protocol_id']=='GDI-v1','Wrong release snapshot')
    released={r['path']:r['sha256'] for r in release['files']}
    for stored,original in [('bin/grooveDarcyStaticFoam','build/bin/grooveDarcyStaticFoam'),('lib/libgroovePorosity.so','build/lib/libgroovePorosity.so'),
        ('common/GDI01.json','common/GDI01.json'),('common/protocol.json','common/protocol.json'),
        ('provenance/analysis/check_results.py','analysis/check_results.py'),('provenance/analysis/sdi_metrics.py','analysis/sdi_metrics.py')]:
        require(sha(run/stored)==released[original],'Run copy differs from sealed release: '+stored)
    require(manifest['libraries']==release['libraries'],'Runtime library binding metadata changed')
    require(sha(Path(__file__))==sha(run/'provenance/analysis/check_results.py'),'Checker differs from launched copy')
    require(sha(Path(__file__).with_name('sdi_metrics.py'))==sha(run/'provenance/analysis/sdi_metrics.py'),'Metric kernel differs from launched copy')
    execution=json.loads((run/'execution.json').read_text())
    require(execution['case_id']=='GDI01' and execution['run_id']==manifest['run_id'],'Execution identity mismatch')
    require(execution['status']=='completed' and len(execution['steps'])==1,'Run incomplete or failed')
    step=execution['steps'][0];require(step['label']=='openfoam' and step['exit_code']==0 and not step['timed_out'],'Missing zero independent exit')
    require('-solve' in step['argv'] and '-auditOnly' not in step['argv'],'Not a flow execution')
    cfg=json.loads((run/'common/GDI01.json').read_text());protocol=json.loads((run/'common/protocol.json').read_text())
    require(sha(run/'common/protocol.json')==cfg['GDI_protocol_sha256'],'Protocol binding mismatch')
    expected_configuration(cfg,protocol)
    d=run/'openfoam/GDI_output';cells=numbers(d/'cells.csv');faces=numbers(d/'faces.csv');solver=json.loads((d/'solver.json').read_text())
    require(solver['run_id']==manifest['run_id'] and solver['case_id']=='GDI01' and solver['protocol_id']=='GDI-v1','Output identity mismatch')
    require(solver['source_route']=='native_porosityForce_source_rho_U' and solver['model_type']=='grooveDarcy' and solver['porous_zone_cells']==512,'Wrong native source metadata')
    require(solver['pressure_matrix_sign']==-1 and solver['physical_time_advanced'] is False,'Wrong pressure sign or transient mode')
    log=(run/'logs/openfoam.log').read_text()
    require(len(re.findall(r'Solving for p,',log))==solver['outer_iterations'],'Pressure solve log/history count mismatch')
    base,grid=evaluate(cfg,cells,faces,solver)
    extra=integration_checks(cfg,protocol,cells,faces,numbers(d/'coefficients.csv'),numbers(d/'momentum_residual.csv'),numbers(d/'iteration_history.csv'),solver)
    native=native_check(run/'openfoam',cells,faces)
    comparisons=[]
    baseline=run/'references/C01'
    accepted=json.loads((baseline/'accepted_analysis.json').read_text())
    require(accepted['run_id']=='SDI_C01_v1_20261030_01' and accepted['RESULT_PASS'] is True,'Invalid baseline acceptance')
    require(sha(baseline/'original_run_manifest.json')==accepted['run_manifest_sha256'],'Baseline original manifest mismatch')
    original_hashes={x['path']:x['sha256'] for x in accepted['raw_files']}
    for label,folder in [('two_dimensional','two_dimensional'),('openfoam','openfoam/SDI_output')]:
        for name in ['cells.csv','faces.csv','solver.json']:require(sha(baseline/folder/name)==original_hashes[f'{folder}/{name}'],'Baseline snapshot changed')
        old,oldGrid=evaluate(cfg,numbers(baseline/folder/'cells.csv'),numbers(baseline/folder/'faces.csv'),json.loads((baseline/folder/'solver.json').read_text()))
        require(old['interface_checks_satisfied'],'Existing baseline no longer satisfies frozen metrics')
        values={}
        for field,scale in [('p_Pa',24),('Jx_m2_s',cfg['K_m3'][0][0]*cfg['G_Pa_per_m']/cfg['mu_Pa_s']),('Jy_m2_s',cfg['K_m3'][0][0]*cfg['G_Pa_per_m']/cfg['mu_Pa_s'])]:
            values[field]=max(abs(grid[k][field]-oldGrid[k][field]) for k in grid)/scale
        values['Q']=abs(base['boundary_Q_m3_s']['xHigh']-old['boundary_Q_m3_s']['xHigh'])/base['analytic_expected_Q_m3_s']
        for name,value in values.items():metric(comparisons,label+'_'+name+'_cross_relative',value,cfg['thresholds']['cross_implementation_relative'])
    checks=base['checks']+extra['checks']+comparisons;passed=all(c['satisfied'] for c in checks)
    raw=[dict(path=str(p.relative_to(run)),sha256=sha(p)) for sub in [d,run/'openfoam/1',run/'logs'] for p in sorted(sub.rglob('*')) if p.is_file()]
    raw.append(dict(path='execution.json',sha256=sha(run/'execution.json')))
    return dict(checker_version=CHECKER_VERSION,kind='COMPLETED_GDI_RUN_ANALYSIS',protocol_id='GDI-v1',case_id='GDI01',run_id=manifest['run_id'],
        results=base,integration=extra,cross_checks=comparisons,native_field_readback=native,checks=checks,
        NUMERICAL_GATE='PASS' if passed else 'FAIL',RESULT_PASS=passed,geometry_PASS=True,
        geometry_scope='synthetic_average_domain_only',physical_validation='NOT_EVALUATED',independent_human_acceptance=False,
        raw_files=raw,run_manifest_sha256=sha(run/'run_manifest.json'))

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run-dir',type=Path,required=True);p.add_argument('--report',type=Path,required=True);a=p.parse_args()
    run=a.run_dir.resolve();report=a.report.resolve()
    if report.exists() or report.is_relative_to(run):raise ValueError('Use a new external report path; raw run is read-only')
    try:result=check_run(run)
    except (ValueError,KeyError,OSError,TypeError,IndexError) as exc:
        result=dict(kind='INCOMPLETE_OR_INVALID_EVIDENCE',error=str(exc),NUMERICAL_GATE='NOT_EVALUATED',RESULT_PASS=None,geometry_PASS=None,physical_validation='NOT_EVALUATED')
    report.parent.mkdir(parents=True,exist_ok=True);report.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:result.get(k) for k in ['kind','NUMERICAL_GATE','RESULT_PASS','geometry_PASS']}))
    return 0 if result.get('RESULT_PASS') is True else 2
if __name__=='__main__':raise SystemExit(main())

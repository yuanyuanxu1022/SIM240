#!/usr/bin/env python3
"""Validate existing no-solve audit output; this script launches nothing."""
import ast
import json
import math
from pathlib import Path
import sys
PKG=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(PKG/'analysis'))
from check_results import expected_configuration, ids, numbers
from sdi_metrics import sha

def main():
    cfg=json.loads((PKG/'common/GDI01.json').read_text());protocol=json.loads((PKG/'common/protocol.json').read_text())
    expected_configuration(cfg,protocol)
    d=PKG/'build/audit_case/GDI_audit';audit=json.loads((d/'audit.json').read_text())
    assert audit['audit_only'] and audit['flow_solved'] is False and audit['solve_calls']==0
    assert audit['cells']==audit['zone_cells']==512 and audit['source_route']=='native_porosityForce_source_rho_U'
    assert audit['model_type']=='grooveDarcy' and audit['momentum_dimensions']=='force'
    assert audit['pressure_matrix_symmetric'] and audit['pressure_matrix_positive_diagonal']
    cells=numbers(d/'cells.csv');faces=numbers(d/'faces.csv');coeff=ids(numbers(d/'coefficients.csv'),512);matrix=ids(numbers(d/'matrix.csv'),512)
    assert len(cells)==512 and len(faces)==1072
    ids(cells,512);dx=cfg['L_m'][0]/16;dy=cfg['L_m'][1]/32;H=cfg['H_m'];mu=cfg['mu_Pa_s']
    assert all(c['p_Pa']==0 and all(c['U'+a+'_m_s']==0 and c['J'+a+'_m2_s']==0 for a in 'xyz') for c in cells)
    grid={};positions={}
    for c in cells:
        i=round(c['x_m']/dx-.5);j=round(c['y_m']/dy-.5)
        assert (i,j) not in grid and 0<=i<16 and 0<=j<32
        assert max(abs(c['x_m']/dx-i-.5),abs(c['y_m']/dy-j-.5),abs(c['z_m']/H-.5),abs(c['volume_m3']/(dx*dy*H)-1))<=1e-10
        grid[i,j]=c;positions[int(c['cell_id'])]=(i,j)
        r=coeff[int(c['cell_id'])];m=matrix[int(c['cell_id'])];assert r['zone_member']==1
        assert abs(r['H_m']/H-1)<=1e-12
        for a in 'xyz':
            for b in 'xyz':
                val=r['D'+a+b+'_m_minus2'];target=cfg['D_m_minus2']['xy'.index(a)]['xy'.index(b)] if a in 'xy' and b in 'xy' else 0
                assert abs(val-target)/max(cfg['D_m_minus2'][0][0],cfg['D_m_minus2'][1][1])<=1e-12
        expected=mu*(r['Dxx_m_minus2']+r['Dyy_m_minus2'])*c['volume_m3']
        assert abs(m['momentum_diag_kg_s']/expected-1)<=1e-12
        assert all(m['momentum_source_'+a+'_N']==0 for a in 'xyz')
        assert m['pressure_diagonal']>0 and m['rAU']>0
        assert abs(m['rAU']*expected/c['volume_m3']-1)<=1e-12
    facekeys=set();counts={p:0 for p in ['internal','xLow','xHigh','yLow','yHigh']}
    for f in faces:
        axis=0 if abs(f['Sx_m2'])>=abs(f['Sy_m2']) else 1
        s=f['S'+'xy'[axis]+'_m2'];other=f['S'+'yx'[axis]+'_m2']
        assert s!=0 and math.hypot(other,f['Sz_m2'])/abs(s)<=1e-10
        i=round(f['x_m']/dx-(.5 if axis==1 else 0));j=round(f['y_m']/dy-(.5 if axis==0 else 0))
        key=(axis,i,j);assert key not in facekeys;facekeys.add(key)
        assert max(abs(f['x_m']/dx-i-(.5 if axis==1 else 0)),abs(f['y_m']/dy-j-(.5 if axis==0 else 0)),abs(f['z_m']/H-.5),abs(abs(s)/((dy if axis==0 else dx)*H)-1))<=1e-10
        own=int(f['owner']);nei=int(f['neighbour']);assert own in positions
        if nei>=0:assert nei in positions and f['patch']=='internal'
        else:assert f['patch'] in counts and f['patch']!='internal'
        counts[f['patch']]+=1
        assert f['phi_m3_s']==f['phi_U_m3_s']==0
    assert counts==dict(internal=976,xLow=32,xHigh=32,yLow=16,yHigh=16)
    source=(PKG/'application/grooveDarcyStaticFoam.C').read_text()
    assert 'grooveTransport.H' not in source and 'Kparallel' not in source and 'Kperpendicular' not in source
    assert 'momentum(-wrapper->source(rho,U))' in source and 'probe' in source
    assert source.index('return 0;',source.index('if(audit)'))<source.index('pressure.solve()')
    assert source.count('.solve()')==1
    origin=json.loads((PKG/'common/metric_origin.json').read_text());old=ast.parse(Path(origin['source']).read_text());new=ast.parse((PKG/'analysis/sdi_metrics.py').read_text())
    for name in origin['functions']:
        a=next(n for n in old.body if isinstance(n,ast.FunctionDef) and n.name==name)
        b=next(n for n in new.body if isinstance(n,ast.FunctionDef) and n.name==name)
        assert ast.dump(a,include_attributes=False)==ast.dump(b,include_attributes=False)
    for rec in json.loads((PKG/'common/subclass_binding.json').read_text()):assert sha(Path(rec['source']))==sha(PKG/rec['copied_path'])==rec['sha256']
    assert not (PKG/'runs').exists() and not (PKG/'cases/GDI01/GDI_output').exists() and not (PKG/'cases/GDI01/1').exists()
    report=dict(status='NO_SOLVE_AUDIT_PASS_NOT_FLOW_VALIDATION',cells=512,zone_cells=512,active_faces=1072,
        runtime_wrapper='porosityForce',runtime_model='grooveDarcy',coefficient_probe_matches=True,
        zero_initial_fields=True,positive_momentum_diagonal=True,symmetric_pressure_matrix=True,
        all_SDI_metric_function_ASTs_unchanged=True,subclass_source_and_library_unchanged=True,
        flow_solved=False,solve_calls=0,run_id=None,physical_validation='NOT_EVALUATED',
        audit_files={str(p.relative_to(PKG)):sha(p) for p in sorted(d.iterdir()) if p.is_file()})
    (PKG/'reports/static_audit.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ['status','cells','zone_cells','flow_solved','solve_calls']}))
if __name__=='__main__':main()

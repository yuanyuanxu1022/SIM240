#!/usr/bin/env python3
"""Independent arithmetic/native-field readback. No solver import or launch."""
import csv
import hashlib
import json
import math
import re
from pathlib import Path

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[2]
RUN=ROOT/'CASE/interface_static_darcy_v1_2/runs/SDI_C03_v1_2_20261030_01'


def read_csv(path):
    with path.open() as f:
        return [{k:v if k=='patch' else float(v) for k,v in row.items()} for row in csv.DictReader(f)]


def strip_comments(text):
    return re.sub(r'//[^\n]*','',re.sub(r'/\*.*?\*/','',text,flags=re.S))


def value_list(text,keyword,count,components):
    m=re.search(r'\b'+re.escape(keyword)+r'\s+(uniform|nonuniform)\s+',text)
    if not m:raise ValueError('Missing '+keyword)
    tail=text[m.end():]
    if m[1]=='uniform':
        body=tail.split(';',1)[0]
        values=[float(v) for v in re.findall(r'[-+]?(?:\d*\.\d+|\d+\.?\d*)(?:[eE][-+]?\d+)?',body)]
        assert len(values)==components
        return values*count
    header=re.match(r'List<\w+>\s+(\d+)\s*\(',tail)
    assert header and int(header[1])==count
    start=header.end();level=1;i=start
    while level:
        if tail[i]=='(':level+=1
        elif tail[i]==')':level-=1
        i+=1
    values=[float(v) for v in re.findall(r'[-+]?(?:\d*\.\d+|\d+\.?\d*)(?:[eE][-+]?\d+)?',tail[start:i-1])]
    assert len(values)==count*components and all(math.isfinite(v) for v in values)
    return values


def block(text,name):
    m=re.search(r'\b'+re.escape(name)+r'\s*\{',text);assert m
    start=m.end();i=start;level=1
    while level:
        if text[i]=='{':level+=1
        elif text[i]=='}':level-=1
        i+=1
    return text[start:i-1]


def main():
    cfg=json.loads((RUN/'common/C03.json').read_text());mu=cfg['mu_Pa_s'];H=cfg['H_m'];lx,ly,_=cfg['L_m'];G=cfg['G_Pa_per_m']
    K=cfg['K_m3'][0][0];Ustar=K*G/(mu*H);Qstar=K*G/mu*ly
    derived={};readback={}
    for name,rel in [('two_dimensional','two_dimensional'),('openfoam','openfoam/SDI_output')]:
        cells=read_csv(RUN/rel/'cells.csv');faces=read_csv(RUN/rel/'faces.csv');V=math.fsum(c['volume_m3'] for c in cells)
        q={p:math.fsum(f['phi_m3_s'] for f in faces if f['patch']==p) for p in ['xLow','xHigh','yLow','yHigh']}
        residual={int(c['cell_id']):[] for c in cells}
        for f in faces:
            residual[int(f['owner'])].append(f['phi_m3_s'])
            if f['neighbour']>=0:residual[int(f['neighbour'])].append(-f['phi_m3_s'])
        Umean=math.fsum(c['Ux_m_s']*c['volume_m3'] for c in cells)/V
        power=G*lx*q['xHigh'];diss=math.fsum(mu*(cfg['D_m_minus2'][0][0]*c['Ux_m_s']**2+cfg['D_m_minus2'][1][1]*c['Uy_m_s']**2)*c['volume_m3'] for c in cells)
        derived[name]=dict(cells=len(cells),active_faces=len(faces),Umean_m_s=Umean,Q_m3_s=q,
                           analytic_U_m_s=Ustar,analytic_Q_m3_s=Qstar,
                           recovered_K_from_U_m3=mu*H*Umean/G,recovered_K_from_Q_m3=mu*q['xHigh']/(G*ly),
                           pressure_relative_max=max(abs(c['p_Pa']-G*(lx-c['x_m'])) for c in cells)/(G*lx),
                           local_mass_relative=math.fsum(abs(math.fsum(v)) for v in residual.values())/Qstar,
                           global_mass_relative=abs(math.fsum(q.values()))/Qstar,
                           pressure_power_W=power,dissipation_W=diss,energy_relative=abs(diss/power-1),
                           p_cell_min_Pa=min(c['p_Pa'] for c in cells),p_cell_max_Pa=max(c['p_Pa'] for c in cells))
        if name=='openfoam':
            cells=sorted(cells,key=lambda c:c['cell_id'])
            expected_dims={'p':[1,-1,-2,0,0,0,0],'U':[0,1,-1,0,0,0,0],'J':[0,2,-1,0,0,0,0],
                           'phi':[0,3,-1,0,0,0,0],'phi_U':[0,3,-1,0,0,0,0]}
            for field,columns in [('p',['p_Pa']),('U',['Ux_m_s','Uy_m_s','Uz_m_s']),('J',['Jx_m2_s','Jy_m2_s','Jz_m2_s'])]:
                text=strip_comments((RUN/'openfoam/1'/field).read_text());dims=[int(v) for v in re.search(r'dimensions\s*\[([^\]]+)\]',text)[1].split()]
                assert dims==expected_dims[field]
                values=value_list(text,'internalField',len(cells),len(columns))
                raw=[c[k] for c in cells for k in columns];diff=max(abs(x-y) for x,y in zip(values,raw));assert diff==0
                readback[field]=dict(values=len(values),dimensions=dims,max_absolute_difference_from_csv=diff)
                if field=='p':
                    boundaries=block(text,'boundaryField')
                    assert value_list(block(boundaries,'xLow'),'value',1,1)==[24.]
                    assert value_list(block(boundaries,'xHigh'),'value',1,1)==[0.]
            for field,column in [('phi','phi_m3_s'),('phi_U','phi_U_m3_s')]:
                text=strip_comments((RUN/'openfoam/1'/field).read_text());dims=[int(v) for v in re.search(r'dimensions\s*\[([^\]]+)\]',text)[1].split()]
                assert dims==expected_dims[field]
                interior=sorted([f for f in faces if f['neighbour']>=0],key=lambda f:f['face_id'])
                values=value_list(text,'internalField',len(interior),1)
                diffs=[abs(x-f[column]) for x,f in zip(values,interior)]
                boundary=block(text,'boundaryField')
                for patch in ['xLow','xHigh','yLow','yHigh']:
                    rows=sorted([f for f in faces if f['patch']==patch],key=lambda f:f['face_id'])
                    vals=value_list(block(boundary,patch),'value',len(rows),1)
                    diffs.extend(abs(x-f[column]) for x,f in zip(vals,rows))
                assert max(diffs)==0
                readback[field]=dict(values=len(diffs),dimensions=dims,max_absolute_difference_from_csv=max(diffs))
    manifest=json.loads((RUN/'run_manifest.json').read_text());bad=[]
    for rec in manifest['files']:
        if hashlib.sha256((RUN/rec['path']).read_bytes()).hexdigest()!=rec['sha256']:bad.append(rec['path'])
    assert not bad
    report=dict(run_id=manifest['run_id'],kind='INDEPENDENT_LOCAL_ARITHMETIC_NOT_INDEPENDENT_HUMAN_REVIEW',
                raw_run_files_verified=len(manifest['files']),changed_bound_files=bad,derived=derived,native_field_readback=readback,
                scientific_thresholds_changed=False,raw_data_modified=False,solver_run=False)
    (OUT/'independent_raw_audit.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(native_fields_read_back=list(readback),native_csv_differences_zero=True,run_files_verified=len(manifest['files']),solver_run=False)))


if __name__=='__main__':main()

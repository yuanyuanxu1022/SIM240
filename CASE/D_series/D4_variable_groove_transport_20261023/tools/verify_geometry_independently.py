#!/usr/bin/env python3
"""Independent extruded 2D material/ray enumeration, checked against real 3D audits."""
from pathlib import Path
import itertools
import json
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
kv=lambda p:dict(s.split('=',1) for s in Path(p).read_text().splitlines() if '=' in s)
report=json.loads((ROOT/'evidence/preflight.json').read_text())
records=[]
for record in report['geometry_records']:
    out=ROOT/record['output'];c=kv(out/'run_config.txt');r=kv(out/'result.txt')
    dx=float(c['dx_nm']);nx=round(float(c['period_nm'])/dx);ny=round(float(c['Ly_nm'])/dx)
    nh=round(float(c['h_nm'])/dx);nd=round(float(c['d_nm'])/dx)
    edge=(float(c['period_nm'])-float(c['w_nm']))/(2*dx);end=nx-edge
    x,z=np.meshgrid(np.arange(nx)+.5,np.arange(nh+nd)+.5,indexing='ij')
    def fluid(xx,zz):
        xx=np.remainder(xx,nx)
        return (zz>=0)&(zz<nh+nd*((xx>=edge)&(xx<end)))
    isfluid=fluid(x,z);count=int(isfluid.sum())*ny
    assert count==int(r['fluid_nodes'])
    links=0
    for cx,cy,cz in itertools.product([-1,0,1],repeat=3):
        if cx*cx+cy*cy+cz*cz not in [1,2]:continue
        hits=isfluid&~fluid(x+cx,z+cz)
        links+=int(hits.sum())*ny
        assert np.all(fluid(x+.25*cx,z+.25*cz)[hits])
        assert not np.any(fluid(x+.75*cx,z+.75*cz)[hits])
    assert links==int(r['candidate_links'])==int(r['installed_links'])
    assert float(r['q_min'])==float(r['q_max'])==.5
    records.append({'run_id':r['run_id'],'fluid_nodes':count,'candidate_links':links,'matches_actual_installed_links':True})
assert len(records)==42
result={'ok':True,'actual_meshes_checked':len(records),'method':'independent 2D exact geometry, 18 D3Q19 rays and periodic extrusion',
        'records':records,'solver_run':False,'geometry_only':True,'NUMERICAL_GATE':'NOT_EVALUATED'}
(ROOT/'evidence/independent_geometry.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
print(json.dumps({k:v for k,v in result.items() if k!='records'},ensure_ascii=False))

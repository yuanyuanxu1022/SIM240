#!/usr/bin/env python3
"""Extract existing coefficients and the log-ratio convex hull; no fitting."""
from pathlib import Path
import csv,json,math
HERE=Path(__file__).resolve().parent;OLD=HERE.parent/'bivariate_piecewise_comparison_20261022'
fits=[f for f in json.loads((OLD/'fits.json').read_text()) if f['scheme']=='full' and f['model']=='C4']
rr=list(csv.DictReader((OLD/'training_data.csv').open(encoding='utf-8-sig')))
coords=sorted({(math.log(float(r['h'])/120),math.log(float(r['d'])/120)) for r in rr})
def cross(o,a,b):return (a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0])
def half(points):
    ans=[]
    for p in points:
        while len(ans)>=2 and cross(ans[-2],ans[-1],p)<=0:ans.pop()
        ans.append(p)
    return ans
hull=half(coords)[:-1]+half(list(reversed(coords)))[:-1]
planes=[]
for (x,y),(xx,yy) in zip(hull,hull[1:]+hull[:1]):
    a,b=yy-y,x-xx;norm=math.hypot(a,b);planes.append([a/norm,b/norm,-(a*x+b*y)/norm])
assert all(a*x+b*y+c<=1e-12 for x,y in coords for a,b,c in planes)
output={'status':'existing retrospective C4 rewritten by exact similarity variables; not a newly fitted or finally locked model',
'phi':.5,'period_rule':'P=2w','original_reference_w_nm':120,'coefficients':{f['direction']:f['coefficients'] for f in fits},
'coefficient_order':['a','b','c','q'],'original_form':'Delta=exp(a)*(d/w)^b*(h/w)^c*exp(q*ln(h/w)^2)',
'gap_scaled_form':'Delta=exp(a)*(d/h)^b*(w/h)^(-(b+c))*exp(q*ln(w/h)^2)',
'log_domain_halfspaces':planes,'sample_ratio_vertices':[[math.exp(x),math.exp(y)] for x,y in hull],
'domain_note':'convex hull in ln(h/w),ln(d/w) of existing 18 geometries; membership does not guarantee prediction accuracy',
'model_lock_created':False}
(HERE/'coefficients_and_domain.json').write_text(json.dumps(output,ensure_ascii=False,indent=2));print(json.dumps(output['sample_ratio_vertices']))

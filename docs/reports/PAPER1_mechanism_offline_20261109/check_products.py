"""Independent scalar consistency of produced tables and unchanged raw inputs."""
from pathlib import Path
import csv,json,math,hashlib
p=Path(__file__).resolve().parent
def rows(n):return list(csv.DictReader((p/n).open()))
def close(a,b):assert math.isclose(a,b,rel_tol=2e-12,abs_tol=1e-27),(a,b)
power=rows('power_checks.csv');parts=rows('strain_components.csv')
regions=rows('spatial_regions.csv');pos=rows('positive_excess_diagnostic.csv')
assert len(power)==24 and len(rows('field_checks.csv'))==12
checks=0
for r in power:
    cc=[x for x in parts if x['run_id']==r['run_id'] and x['scheme']==r['scheme']]
    assert len(cc)==6 and all(float(x['power_W'])>=0 for x in cc)
    close(sum(float(x['power_W']) for x in cc),float(r['strain_W']))
    close(sum(float(x['fraction_of_strain']) for x in cc),1)
    close(sum(float(x['R_component_over_R_LC']) for x in cc),float(r['R_strain_over_R_LC']))
    close(float(r['R_strain_over_R_LC']),float(r['R_drive_over_R_LC'])*float(r['strain_W'])/float(r['input_W']))
    checks+=4
    ids=[x for x in pos if x['run_id']==r['run_id'] and x['scheme']==r['scheme']]
    close(sum(float(x['R_excess_term_over_R_LC']) for x in ids),float(ids[0]['sum_terms_over_R_LC']))
    close(sum(float(x['term_fraction_of_positive_sum']) for x in ids),1);checks+=2
    if float(r['d_nm'])==0:
        assert not any(x['run_id']==r['run_id'] for x in regions)
        continue
    for radius in (.125,.25,.5):
        rr=[x for x in regions if x['run_id']==r['run_id'] and x['scheme']==r['scheme'] and float(x['r_over_h'])==radius]
        assert len(rr)==4
        for name in ['fluid_volume_fraction','strain_power_fraction','saved_power_fraction']:
            close(sum(float(x[name]) for x in rr),1)
        close(sum(float(x['R_region_over_R_LC']) for x in rr),float(r['R_strain_over_R_LC']))
        checks+=4
m=json.loads((p/'source_manifest.json').read_text())
changed=[f for f,d in m.items() if hashlib.sha256(Path(f).read_bytes()).hexdigest()!=d]
assert not changed,changed
result={'checks':checks,'produced_table_consistency':True,'protected_scientific_inputs':len(m),'changed_inputs':changed,
        'normalization_is_not_rebalanced_to_close_energy':True,'formal_scientific_acceptance':False}
(p/'product_checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(result,ensure_ascii=False))

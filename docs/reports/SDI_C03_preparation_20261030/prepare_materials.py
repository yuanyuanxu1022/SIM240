"""Create an isolated C03 preparation package. Does not invoke any solver."""
import difflib
import hashlib
import json
import shutil
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[3]
REPORT = Path(__file__).resolve().parent
OLD = PROJECT/'CASE/interface_static_darcy_v1_1'
NEW = PROJECT/'CASE/interface_static_darcy_v1_2'


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def write_json(p, value):
    p.write_text(json.dumps(value, indent=2)+'\n')


def main():
    if NEW.exists():
        raise FileExistsError('C03 package exists; no overwrite')
    roots = ['CASE/interface_static_darcy_v1', 'CASE/interface_static_darcy_v1_1',
             'docs/reports/SDI_C01_results_20261030',
             'docs/reports/SDI_C02_preparation_20261030',
             'docs/reports/SDI_C02_results_20261030']
    preserved = [dict(path=str(p.relative_to(PROJECT)), sha256=sha(p))
                 for rel in roots for p in sorted((PROJECT/rel).rglob('*')) if p.is_file()]
    write_json(REPORT/'preservation_before.json', dict(roots=roots, files=preserved))
    for rel in ['common', 'analysis', 'scripts', 'tests', 'reports',
                'openfoam/cases/C03/0', 'openfoam/cases/C03/constant', 'openfoam/cases/C03/system']:
        (NEW/rel).mkdir(parents=True, exist_ok=False)
    reuse=json.loads((OLD/'reports/solver_reuse.json').read_text())
    for rec in reuse['files']:
        source=PROJECT/rec['original_path']
        if sha(source)!=rec['sha256'] or sha(OLD/rec['path'])!=rec['sha256']:
            raise ValueError('Source/binary reuse binding mismatch')
        target=NEW/rec['path'];target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    write_json(NEW/'reports/solver_reuse.json', reuse)
    for rel in ['reports/inherited_C01_preparation.json','reports/inherited_C01_release_manifest.json','.gitignore']:
        shutil.copy2(OLD/rel, NEW/rel)
    shutil.copytree(OLD/'openfoam/cases/C02/constant/polyMesh', NEW/'openfoam/cases/C03/constant/polyMesh')
    for source_name in ['prepare_c02.py','audit_c02.py','run_c02.py','seal_release.py']:
        s=(OLD/'scripts'/source_name).read_text().replace('C02','C03').replace('c02','c03')
        s=s.replace('1.1.0','1.2.0').replace('SDI_C03_v1_1_','SDI_C03_v1_2_')
        if source_name=='prepare_c02.py':
            s=s.replace("pressure_units='Pa',", "coefficient_input_id=case['input_id'], orientation_id=case['orientation_id'],\n               pressure_units='Pa',")
        if source_name=='audit_c02.py':
            start=s.index("    for key in ['K_m3','D_m_minus2']:")
            end=s.index('    commands=[]', start)
            s=s[:start]+'''    planned=next(c for c in proto['planned_cases'] if c['case_id']=='C03')
    c01=next(c for c in proto['planned_cases'] if c['case_id']=='C01')
    assert planned['input_id']=='original_local_cubic'
    assert planned['orientation_id']==c01['orientation_id']=='groove_along_long_y'
    assert cfg['coefficient_input_id']==planned['input_id'] and cfg['orientation_id']==planned['orientation_id']
    source=json.loads(Path(cfg['source_paths']['coefficient_source']).read_text())
    row=next(r for r in source['rows'] if r['input_id']==planned['input_id'] and r['orientation_id']==planned['orientation_id'])
    assert cfg['K_m3']==row['K_global_m3'] and cfg['D_m_minus2']==row['D_global_m_minus2_conditional_total_drag']
    h,d=75e-9,100e-9
    original_perp=(h+d)**3*h**3/(6*((h+d)**3+h**3))
    original_para=((h+d)**3+h**3)/24
    for a,expected in enumerate([original_perp,original_para]):
        assert abs(cfg['K_m3'][a][a]/expected-1)<2e-15
    assert cfg['K_m3'][0][1]==cfg['K_m3'][1][0]==0
    assert cfg['D_m_minus2'][0][1]==cfg['D_m_minus2'][1][0]==0
    oldcase=ROOT.parent/'interface_static_darcy_v1/openfoam/cases/C01'
    newcase=ROOT/'openfoam/cases/C03'
    same_files=['0/p','system/blockMeshDict','system/controlDict','system/fvSchemes','system/fvSolution']
    same_files += ['constant/polyMesh/'+name for name in ['boundary','faces','neighbour','owner','points']]
    for rel in same_files:
        if (newcase/rel).read_bytes()!=(oldcase/rel).read_bytes():
            raise ValueError('C01/C03 boundary/mesh/numerics changed: '+rel)
    # Only Kxx/Kyy may differ in the two-dimensional input.
    def read_input(path):
        return dict(line.split() for line in path.read_text().splitlines() if line.strip())
    oldinput=read_input(ROOT.parent/'interface_static_darcy_v1/common/C01_2d.txt')
    newinput=read_input(ROOT/'common/C03_2d.txt')
    assert set(oldinput)==set(newinput)
    for key in oldinput:
        if key not in ['Kxx','Kyy']:assert oldinput[key]==newinput[key], key
''' +s[end:]
        (NEW/'scripts'/source_name.replace('c02','c03')).write_text(s)
    checker=(OLD/'analysis/check_results.py').read_text()
    newer=checker.replace('Checker 1.1.0: read completed C01 or C02 outputs',
                         'Checker 1.2.0: read completed C01, C02 or C03 outputs')
    newer=newer.replace('CHECKER_VERSION = "1.1.0"','CHECKER_VERSION = "1.2.0"')
    newer=newer.replace('SUPPORTED_CASES = {"C01", "C02"}','SUPPORTED_CASES = {"C01", "C02", "C03"}')
    (NEW/'analysis/check_results.py').write_text(newer)
    (REPORT/'checker_1_1_to_1_2.diff').write_text(''.join(difflib.unified_diff(checker.splitlines(True), newer.splitlines(True), fromfile='checker-1.1.0', tofile='checker-1.2.0')))
    for name in ['test_checker.py','test_geometry_release.py']:
        s=(OLD/'tests'/name).read_text()
        if name=='test_geometry_release.py':s=s.replace("case_id='C03'", "case_id='C04'")
        (NEW/'tests'/name).write_text(s.replace('C02','C03'))
    print(json.dumps(dict(new_package=str(NEW.relative_to(PROJECT)), old_files_snapshotted=len(preserved), flow_solved=False)))


if __name__=='__main__':
    main()

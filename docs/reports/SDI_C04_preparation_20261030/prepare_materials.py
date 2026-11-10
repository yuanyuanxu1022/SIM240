"""Create isolated SDI C04 inputs/tools; never execute a flow solver."""
import difflib
import hashlib
import json
import shutil
from pathlib import Path

PROJECT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
OLD=PROJECT/'CASE/interface_static_darcy_v1_2'
NEW=PROJECT/'CASE/interface_static_darcy_v1_3'


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    if NEW.exists():raise FileExistsError('C04 package exists; refusing overwrite')
    roots=['CASE/interface_static_darcy_v1','CASE/interface_static_darcy_v1_1','CASE/interface_static_darcy_v1_2',
           'docs/reports/SDI_C01_results_20261030','docs/reports/SDI_C02_results_20261030',
           'docs/reports/SDI_C03_results_20261030','docs/reports/SDI_C03_preparation_20261030',
           'docs/reports/SDI_C02_preparation_20261030']
    files=[dict(path=str(p.relative_to(PROJECT)),sha256=sha(p)) for rel in roots
           for p in sorted((PROJECT/rel).rglob('*')) if p.is_file()]
    (OUT/'preservation_before.json').write_text(json.dumps(dict(roots=roots,files=files),indent=2)+'\n')
    for rel in ['common','analysis','scripts','tests','reports','openfoam/cases/C04/0',
                'openfoam/cases/C04/constant','openfoam/cases/C04/system']:
        (NEW/rel).mkdir(parents=True,exist_ok=False)
    reuse=json.loads((OLD/'reports/solver_reuse.json').read_text())
    for rec in reuse['files']:
        src=PROJECT/rec['original_path']
        assert sha(src)==rec['sha256']==sha(OLD/rec['path'])
        target=NEW/rec['path'];target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,target)
    (NEW/'reports/solver_reuse.json').write_text(json.dumps(reuse,indent=2)+'\n')
    for rel in ['reports/inherited_C01_preparation.json','reports/inherited_C01_release_manifest.json','.gitignore']:
        shutil.copy2(OLD/rel,NEW/rel)
    shutil.copytree(OLD/'openfoam/cases/C03/constant/polyMesh',NEW/'openfoam/cases/C04/constant/polyMesh')
    for name in ['prepare_c03.py','run_c03.py','seal_release.py']:
        text=(OLD/'scripts'/name).read_text().replace('C03','C04').replace('c03','c04')
        text=text.replace('1.2.0','1.3.0').replace('SDI_C04_v1_2_','SDI_C04_v1_3_')
        (NEW/'scripts'/name.replace('c03','c04')).write_text(text)
    old=(OLD/'analysis/check_results.py').read_text()
    new=old.replace('Checker 1.2.0: read completed C01, C02 or C03 outputs',
                    'Checker 1.3.0: read completed C01, C02, C03 or C04 outputs')
    new=new.replace('CHECKER_VERSION = "1.2.0"','CHECKER_VERSION = "1.3.0"')
    new=new.replace('SUPPORTED_CASES = {"C01", "C02", "C03"}',
                    'SUPPORTED_CASES = {"C01", "C02", "C03", "C04"}')
    (NEW/'analysis/check_results.py').write_text(new)
    (OUT/'checker_1_2_to_1_3.diff').write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='checker-1.2.0',tofile='checker-1.3.0')))
    for name in ['test_checker.py','test_geometry_release.py']:
        text=(OLD/'tests'/name).read_text()
        if name=='test_geometry_release.py':text=text.replace("case_id='C04'","case_id='C05'")
        (NEW/'tests'/name).write_text(text.replace('C03','C04'))
    print(json.dumps(dict(old_files_snapshotted=len(files),package=str(NEW.relative_to(PROJECT)),flow_solved=False)))


if __name__=='__main__':main()

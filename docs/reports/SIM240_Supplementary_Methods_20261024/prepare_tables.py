#!/usr/bin/env python3
"""Create numbered, small supplementary tables from the existing method audit.

Recheck each selected raw result against the saved audit; never execute a solver
or modify a run. The 52 D2/D3 entries, 18 G4 entries and 9 archived entries are
separate evidence inventories, not a count of independent new simulations.
"""
import csv
import hashlib
import json
import math
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
OLD=ROOT/'docs/reports/Methods_support_audit_20261022'
TARGET=ROOT/'docs/reports/SIM240_中文稿_导师审阅版_20261022.md'
assert not (HERE/'manuscript_before.md').exists(),'拒绝覆盖本轮前稿快照'
(HERE/'manuscript_before.md').write_bytes(TARGET.read_bytes())
(HERE/'support_index_before.md').write_bytes((OLD/'SUPPORTING_MATERIALS_INDEX.md').read_bytes())
hashes={}


def read(p):
    p=Path(p)
    if not p.is_absolute():p=ROOT/p
    b=p.read_bytes()
    try:key=str(p.relative_to(ROOT))
    except ValueError:key=str(p)
    hashes[key]=hashlib.sha256(b).hexdigest()
    return b.decode(errors='replace')


def kv(p):
    return dict(x.split('=',1) for x in read(p).splitlines() if '=' in x)


def table(name,rows):
    with (HERE/name).open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)


audit=json.loads(read(OLD/'support_audit.json'))
read(OLD/'REPORT.md')
read(OLD/'verification.json')
run_table=[]
for r in audit['runs']:
    data=kv(r['result']);manifest=kv(r['manifest'])
    assert math.isclose(float(data['Keff_m3']),r['K'],rel_tol=2e-15)
    assert math.isclose(float(data['dx_m'])*1e9,r['dx_nm'],rel_tol=1e-12)
    assert math.isclose(float(data['mesa_gap_m'])*1e9,r['h'],rel_tol=1e-12)
    assert math.isclose(float(data['groove_depth_m'])*1e9,r['d'],rel_tol=1e-12)
    assert manifest['binary_sha256']==r['binary_sha256']
    assert read(Path(r['result']).with_name('exit_code.txt')).strip()==r['shell_exit']
    run_table.append(dict(run_id=r['run_id'],group=r['group'],h_nm=r['h'],d_nm=r['d'],dx_nm=r['dx_nm'],
                          direction=r['direction'],K_m3=r['K'],recorded_PASS=r['recorded_PASS'],
                          independent_exit_code=r['shell_exit'],result_path=r['result'],manifest_path=r['manifest'],
                          binary_sha256=r['binary_sha256'],log_style=r['log_style'],log_path=r['log']))
assert len(run_table)==52
table('Table_S1_run_inventory.csv',run_table)
table('Table_S2_refinement.csv',audit['refinements'])
g4=[]
for r in audit['G4_runs']:
    data=kv(Path(r['path'])/'result.txt')
    assert math.isclose(float(data['Keff_m3']),r['K'],rel_tol=2e-15)
    assert math.isclose(float(data['R_eff_Pa_s_per_m3']),r['R'],rel_tol=2e-15)
    assert read(Path(r['path'])/'exit_code.txt').strip()==r['shell_exit']
    g4.append(dict(nx=r['nx'],direction=r['direction'],acceleration_m_s2=r['acceleration'],
                   run_id=r['run_id'],K_m3=r['K'],R_Pa_s_per_m3=r['R'],
                   recorded_PASS=r['recorded_PASS'],independent_exit_code=r['shell_exit'],
                   result_path=str(Path(r['path'])/'result.txt')))
table('Table_S3_periodic_checks.csv',g4)
grid=[]
for r in audit['archived_grid']:
    data=kv(Path(r['path'])/'result.txt')
    j=float(data['J_m2_s'] if r['case']=='Smooth75' else data['J_main_m2_s'])
    assert math.isclose(j*1e-11,r['K'],rel_tol=2e-15)
    assert read(Path(r['path'])/'exit_code.txt').strip()==r['shell_exit']
    grid.append(dict(grid=r['dx'],case=r['case'],K_m3=r['K'],
                     analytic_error_percent=r.get('analytic_error_percent',''),recorded_PASS=r['recorded_PASS'],
                     independent_exit_code=r['shell_exit'],result_path=str(Path(r['path'])/'result.txt')))
table('Table_S4_grid_archive.csv',grid)

titles=['几何、采样与运行清单','当前数值实现与物性换算','边界连线与低Mach诊断','停止条件与统计',
        '通量、输运系数与参考高度','局部立方律的一维平均关系','双网格敏感性','周期复制与三驱动力检查',
        '平板基准与历史三网格','历史构建来源与日志','方法引文核实边界']
main_locations=['§2.1、表1','§2.1、式1','§2.1','§2.1、§3.1','§2.2、式2','§2.3、式3','§2.3表2、§3.3表4','§2.4','§3.2—3.4','§2.1、§3.4','§2.1、§2.3及相关引文']
table_for={1:'表S1',7:'表S2',8:'表S3',9:'表S4'}
mapping=[dict(previous_index=f'S{i}',supplement_section=f'S{i}',title=t,
              anchor=f'sm-s{i}',document='SUPPLEMENTARY_METHODS.md',main_location=main_locations[i-1],
              supplementary_table=table_for.get(i,'')) for i,t in enumerate(titles,1)]
table('SUPPLEMENT_NUMBER_MAP.csv',mapping)
(HERE/'input_hashes.json').write_text(json.dumps(hashes,ensure_ascii=False,indent=2)+'\n')
(HERE/'preparation.json').write_text(json.dumps(dict(date='2026-10-24',table_rows={'S1':52,'S2':8,'S3':18,'S4':9},
                                                   section_count=11,protected_input_count=len(hashes),
                                                   manuscript_before_sha256=hashlib.sha256(TARGET.read_bytes()).hexdigest()),indent=2)+'\n')
print(json.dumps(dict(tables={'S1':52,'S2':8,'S3':18,'S4':9},sections=11),ensure_ascii=False))

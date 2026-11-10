"""Prepare metadata and algebraic expectations only; never decode field arrays."""
from pathlib import Path
import csv
import hashlib
import json
import shutil
import importlib.util
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
OLD = ROOT/'docs/reports/PAPER1_four_cases_inventory_20261105'


def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for data in iter(lambda:f.read(1024*1024),b''):
            h.update(data)
    return h.hexdigest()


def write_csv(name, rows):
    with (OUT/name).open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


old_hashes=json.loads((OLD/'read_inputs_sha256.json').read_text())
before={p:sha(ROOT/p) for p in old_hashes}
drift=[p for p,h in old_hashes.items() if before[p]!=h]
if drift:
    raise RuntimeError('Prior protected evidence changed; stop and review: '+repr(drift))
inventory=json.loads((OLD/'inventory.json').read_text())
run_records=[r for r in inventory['runs'] if r['role']=='main']
assert len(run_records)==4
inputs=[]
geometries=[]
run_plans=[]
new_sources={}
for r in run_records:
    run=r['run_id']
    depth=25 if '_d25_' in run else 100
    direction='P' if run.endswith('_P') else 'T'
    base=ROOT/'CASE/D_series/D2_groove_error_map/results'/run
    final_step=int(r['result']['steps_completed'])
    for filename,hash_before in before.items():
        p=ROOT/filename
        if not p.is_relative_to(base):
            continue
        role='scalar_or_provenance'
        stage='input_binding'
        if p.suffix in ('.vti','.vtm','.pvd'):
            role='vtk_payload' if p.suffix=='.vti' else 'vtk_reference'
            stage='material_initial' if '_iT0000000' in p.name else 'final_readback'
        elif p.name=='field_slice.csv':
            role='high_precision_XZ_velocity_anchor'
            stage='future_spatial_crosscheck'
        elif p.name in ('energy_dissipation.csv','pressure_profile.csv'):
            role='preserve_only_not_in_flux_analysis'
        inputs.append({'run_id':run,'path':filename,'sha256':hash_before,
                       'bytes':p.stat().st_size,'role':role,'stage':stage})
    final_vti=[]
    metadata=[]
    for item in r['vtk_structural_inventory']:
        if item['type']!='ImageData':
            continue
        p=ROOT/item['path']
        # XML parsing only; no decoding, unpacking, reader, or array processing.
        tree=ET.parse(p)
        top=tree.getroot()
        metadata.append({'path':item['path'],'root':top.attrib,
                         'image':[e.attrib for e in top.iter('ImageData')],
                         'piece':[e.attrib for e in top.iter('Piece')],
                         'arrays':[e.attrib for e in top.iter('DataArray')],
                         'point_data_blocks':len(list(top.iter('PointData'))),
                         'cell_data_blocks':len(list(top.iter('CellData')))})
        if f'_iT{final_step:07d}iC' in p.name:
            final_vti.append(item['path'])
    assert len(final_vti)==1
    nG=48*48*10
    nC=24*48*(depth//5)
    nC0=24*48*5
    nExt=nC-nC0
    for region,nodes in [('G',nG),('C',nC),('F',nG+nC),('C0',nC0),('Cplus',nExt)]:
        geometries.append({'run_id':run,'region':region,'expected_nodes':nodes,
                           'expected_volume_m3':nodes*(5e-9)**3,
                           'quantity_status':'analytic_geometry_expectation_not_readback'})
    run_plans.append({'run_id':run,'geometry_nm':{'h':50,'d':depth,'w':120,'P':240},
                      'dx_nm':5,'direction':direction,
                      'velocity_component_index':1 if direction=='P' else 0,
                      'final_step':final_step,'final_vti':final_vti[0],
                      'section_axis':'y' if direction=='P' else 'x',
                      'original_section_indices':[12,36] if direction=='P' else [6,24],
                      'original_section_coordinates_nm':[62.5,182.5] if direction=='P' else [32.5,122.5],
                      'csv_anchor_native_y_index':24,'csv_anchor_y_nm':122.5,
                      'metadata':metadata,'readback_status':'NOT_EXECUTED',
                      'flux_result':None,'partition_result':None})

check_defs=[
 ('R01','identity','核SHA/结果末步/PVD-VTM闭包','与绑定值一致','停止，保留来源变化记录'),
 ('R02','reader','PointData/material/velocity分量、有限核心点','元数据、分量数、有效点有限','停止，不插值或换字段'),
 ('R03','coordinates','物理坐标/步长/去重/halo剔除','原生格点与解析单胞相符','停止，不移动坐标或平均重复点'),
 ('R04','geometry','材料掩膜与解析几何逐点比较','F/G/C/C0/Cplus计数与集合关系','停止，不用解析掩膜覆盖错误材料'),
 ('R05','anchor','原生y=122.5nm与CSV按x,z逐点匹配','速度正确Float32转换逐点一致','停止，不搜索最像切面'),
 ('R06','J','独立体积离散积分对result/末diagnostics','记录差值与导出/浮点预算','超预算停止，未建预算则NOT_EVALUATED'),
 ('R07','Q','P两y截面/T两x截面对原Q记录','法向速度积分，按导出/浮点预算','超预算停止，不放宽物理阈值'),
 ('R08','full_sections','每例48个截面Q及G/C部分','仅报告沿程变化，不设新物理PASS线','缺面则停；变化如实报告'),
 ('R09','algebra','平均截面Q与J恒等式','仅容许内部积和舍入','不一致则停积分代码'),
 ('R10','partition','JG+JC=J及浅深G/C0/Cplus增量和','同一数组同一权重的自洽','不一致则停分区比较'),
 ('R11','signed','符号/反向通量/近零分母','保留负值；区间含0不报比例','禁止裁剪负值或宣称死区'),
 ('R12','provenance','全部读入输入前后哈希/输出独立目录','0输入变化，保存脚本/环境/日志','变化或越界即停止'),
 ('R13','software','非对称轴/halo/台阶/Float32合成夹具','预定闭式及结构期望','夹具不合格不读实际场'),
]
write_csv('CHECKS.csv',[{'check_id':i,'category':c,'purpose':p,'criterion':crit,
                        'on_failure':fail,'status':'NOT_EXECUTED'}
                       for i,c,p,crit,fail in check_defs])
questions=[
 ('Q01','导出场能否复现保存的J/Q','R01-R07','可以检查文件/统计一致性','不是独立物理解或物理验证'),
 ('Q02','公共层与槽区分别贡献多少方向输运','R04-R07,R10-R11','四组末态离散贡献/体积/均速','不等于阻力份额或独立恒流通道'),
 ('Q03','新增深度与旧空间流动变化各对应多少增量','R10-R11','G/C0/Cplus的带符号增量记账','不等于深度变化的独立因果拆分'),
 ('Q04','横槽沿程怎样经过深浅区域','R07-R08','总Q和区域Q随x变化','不单独证明瓶颈或侧壁唯一机制'),
 ('Q05','单片CSV能否代表沿y结构','R05及沿y变化诊断','该组保存场的单片代表性','不假设三维场由单片复制'),
 ('Q06','横槽3.38%是否准确连续解收益','本方案不能完成','不能回答','需要匹配网格/来源等证据'),
 ('Q07','V2新几何预测/真实填充是否可靠','本方案不能完成','不能回答','四组已知且无界面固定间隙'),
]
write_csv('QUESTIONS.csv',[dict(zip(['question_id','question','dependency','answer_scope','limit'],r)) for r in questions])
write_csv('INPUTS.csv',inputs)
write_csv('EXPECTED_GEOMETRY.csv',geometries)
plan={'plan_id':'PAPER1_FOUR_FIELDS_READBACK_PLAN_20261105_v1','date':'2026-11-05',
      'scope':'prepare_offline_readback_and_flux_comparison_plan_only',
      'reviewable_plan':True,'formal_protocol_adopted':False,
      'checker_implemented':False,'synthetic_checks_executed':False,
      'readback_executed':False,'partition_results_available':False,
      'solver_execution_authorized':False,'execution_command_delivered':False,
      'new_simulation_run_id':None,'runs':run_plans,
      'preferred_runtime':{'pvpython_path':shutil.which('pvpython'),
                           'ordinary_python_vtk_available':importlib.util.find_spec('vtk') is not None,
                           'numpy_available':importlib.util.find_spec('numpy') is not None,
                           'runtime_version_verified':False,'reader_started':False},
      'excluded':['solver','compile','vtk_array_decode_in_this_task','dissipation_integration',
                  'reserved_predictions','new_grid_runs','gate_changes','plot_rendering'],
      'formulas':{'J':'sum_F(u_e*dx^3)/(Lx*Ly)',
                  'Q_P':'sum_at_y(u_y*dx^2)','Q_T':'sum_at_x(u_x*dx^2)',
                  'J_region':'sum_region(u_e*dx^3)/(Lx*Ly)',
                  'depth_increment':'delta(J_G)+delta(J_C0)+J_Cplus_deep'},
      'scientific_status_unchanged':{'S4_STAGE_ACCEPTED':False,'reference_qualified':False,
                                   'MODEL_COMPARISON':'NOT_EVALUATED',
                                   'physical_validation':'NOT_EVALUATED','submission_ready':False}}
(OUT/'PLAN.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n')
for p in [OLD/'inventory.json',OLD/'verification.json',OLD/'read_inputs_sha256.json',
          OLD/'REPORT.md',ROOT/'CASE/D_series/D2_groove_error_map/src/d2_groove_error_map.cpp',
          Path('/home/dell/openlb/src/io/vtkWriter.hh')]:
    new_sources[str(p)]=sha(p)
(OUT/'source_manifest.json').write_text(json.dumps({'prior_134_protected':before,
       'additional_direct_sources':new_sources},ensure_ascii=False,indent=2)+'\n')
changed=[p for p,h in before.items() if sha(ROOT/p)!=h]
changed_extra=[p for p,h in new_sources.items() if sha(Path(p))!=h]
assert len(inputs)==84
assert len(geometries)==20
assert len({x['run_id'] for x in inputs})==4
assert all(r['flux_result'] is None and r['partition_result'] is None for r in run_plans)
assert all((ROOT/r['final_vti']).is_file() for r in run_plans)
verify={'date':'2026-11-05','original_protected_count':len(before),
        'original_protected_changed':changed,'additional_sources_changed':changed_extra,
        'prior_protected_hash_drift':drift,'named_run_count':4,'input_rows':len(inputs),
        'geometry_expectation_rows':len(geometries),'planned_checks':len(check_defs),
        'questions':len(questions),'plan_structure_valid':True,
        'field_arrays_decoded':False,'synthetic_fixtures_executed':False,
        'actual_field_checks_executed':False,'flux_integrations_executed':False,
        'new_scientific_validation':False}
(OUT/'verification.json').write_text(json.dumps(verify,ensure_ascii=False,indent=2)+'\n')
if changed or changed_extra:
    raise RuntimeError('Read-only input protection failed')
print(json.dumps(verify,ensure_ascii=False))

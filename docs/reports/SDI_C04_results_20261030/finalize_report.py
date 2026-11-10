"""Verify completed C04 evidence and preservation; synchronize handoffs. No solve."""
import ast
import difflib
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

OUT=Path(__file__).resolve().parent
PROJECT=OUT.parents[2]


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def write(name,value):
    (OUT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n')


CURRENT='''## C04满足原SDI-v1，与C02公式对照及C03方向对照均已完成（2026-10-30）

- 用户本轮明确授权完整分析C04已有结果，比较C02同方向原公式/V2及C03同原公式沿/横槽；只分析，不重跑或改门槛。C04 run_id=SDI_C04_v1_3_20261030_01，2026-10-30 15:37:25北京时间完成，两端退出0、无超时，二维90次/OF32次。入口 `docs/reports/SDI_C04_results_20261030/REPORT.md`、METRICS.md及interface_analysis.json。
- 使用启动留存同版检查器1.3.0，原SDI-v1两端各23项、跨端4项共50项数值检查全部满足：NUMERICAL_GATE=PASS、RESULT_PASS=true、geometry_PASS=true（仅512单元合成平均域）；physical_validation=NOT_EVALUATED、independent_human_acceptance=false。原execution.json/result_acceptance=NOT_EVALUATED不改，独立验收写在本轮外部报告，不升级旧科学Gate。
- 25份运行绑定、46份发布文件及21运行库哈希匹配，协议thresholds/linear_solver、源系数/方向与检查器版本核对。原生p/U/J/phi/phi_U与CSV逐项相同，另以math.fsum复算均值、Q、局部守恒、恢复K及耗散。C04 Umean约1.927083333333333e-6m/s，Jx约2.4088541666666664e-13m²/s，Q约1.15625e-17m³/s，恢复沿槽Kxx约2.4088541666666665e-22m³；证据binding_audit.json、independent_raw_audit.json。
- C04压力最大相对解析偏差二维2.20490e-13/OF6.24426e-13；逐单元流量不平衡绝对和/解析Q为1.80976e-11/2.07209e-11（门槛1e-8）；真实归一化残差5.65572e-13/6.47518e-13（门槛1e-12）；跨端Q相对差1.63236e-13。耗散与压力功率约2.775e-16W，能量核对满足。其余原门槛及数值见METRICS.md，50项不是50个独立物理验证。
- 三例相同24/0Pa、24×48μm、H=125nm、μ=0.001Pa·s、512网格、U=J/H、D=H K⁻¹及原门槛；每组10份边界/网格/离散文件、6份求解源码/Make/二进制相同。C04/C02同为槽沿x/驱动x，仅原/V2系数改变；实际Q比二维2.313089024342067/OF2.313089024341704，解析2.3130890243424327。以原公式为基准，V2沿槽Q低56.7678%，静态R_Q=Δp/Q高131.3089%。
- C04/C03同为原公式，K/D主值成对交换（槽沿x/y，驱动均x）；实际沿/横槽Q比二维3.6956052262167565/OF3.695605226217497，解析3.6956052262174715；静态R_沿/R_横约0.27059167。两组压力场最大差约1e-11Pa。倍率仅描述性核对，不增Gate；这些是输入系数方向性的再现，不是挤压F/V或物理准确性证明。证据C04_C02_C03_comparison.json。
- C02/C03本轮只读重验各50项满足，除版本元数据外与旧分析的全部指标/Gate/原始文件哈希相同。结合既有C01记录，原/V2×沿/横槽四个静态主对照均有局部接口验收记录。320份既有包/结果/报告和三次运行共120份原始文件集/哈希保持，见preservation_before.json、run_preservation.json、verification.json；state_sync.json保存本状态/交接替换回执。
- 新改动仅本轮SDI_C04_results_20261030分析报告/只读脚本/证据与本状态、最新交接；无求解/重跑/编译/拟合/真实N8提取/提交推送/对外发送。原C01严格零几何识别未评价及修正记录保持。真实沟槽独立参照、一般斜向/复杂压力、网格独立、严格误差界、新条件预测、挤压/两相/动态、内置DarcyForchheimer接入仍未验证。
- 旧D4_N8_diag_v3_1_20261026_v1仍NUMERICAL_GATE=NOT_EVALUATED、RESULT_PASS=false、geometry_PASS=null；reference_qualified=false、strict_error_bound_established=false、submission_ready=false、预测HOLD与历史FAIL不变。本轮任务已完成，下一具体动作为用户阅读报告并决定后续控制项或独立参考范围；未准备/启动C05或其他计算，不新增长算授权。接手从本报告和原始证据继续；常规工作GPT-6.1 Sol｜High，疑难物理矛盾/最终冻结按协议GPT-6 Astra｜High。
'''


def main():
    if (OUT/'verification.json').exists():raise FileExistsError('Final verification exists')
    stamp=datetime.now(ZoneInfo('Asia/Shanghai')).isoformat()
    analysis=json.loads((OUT/'interface_analysis.json').read_text())
    count=sum(len(r['checks']) for r in analysis['results'].values())+len(analysis['cross_checks'])
    assert count==50 and analysis['NUMERICAL_GATE']=='PASS' and analysis['RESULT_PASS'] is True
    assert all(c['satisfied'] for r in analysis['results'].values() for c in r['checks'])
    assert all(c['satisfied'] for c in analysis['cross_checks'])
    references={'C02':'docs/reports/SDI_C02_results_20261030/interface_analysis.json',
                'C03':'docs/reports/SDI_C03_results_20261030/interface_analysis.json'}
    for case,rel in references.items():
        old=json.loads((PROJECT/rel).read_text());new=json.loads((OUT/f'{case}_reanalysis.json').read_text())
        old.pop('checker_version',None);new.pop('checker_version');assert old==new,case
    before=json.loads((OUT/'preservation_before.json').read_text())
    oldfiles={r['path']:r['sha256'] for r in before['files']}
    now={str(p.relative_to(PROJECT)):sha(p) for rel in before['roots'] for p in sorted((PROJECT/rel).rglob('*')) if p.is_file()}
    assert oldfiles==now
    write('preservation_verification.json',dict(checked_at=stamp,files=len(now),file_sets_identical=True,
          all_sha256_identical=True,roots=before['roots']))
    runs=[PROJECT/'CASE/interface_static_darcy_v1_1/runs/SDI_C02_v1_1_20261030_01',
          PROJECT/'CASE/interface_static_darcy_v1_2/runs/SDI_C03_v1_2_20261030_01',
          PROJECT/'CASE/interface_static_darcy_v1_3/runs/SDI_C04_v1_3_20261030_01']
    preserved=[]
    for run in runs:
        files=[dict(path=str(p.relative_to(PROJECT)),sha256=sha(p)) for p in sorted(run.rglob('*')) if p.is_file()]
        assert all(oldfiles[r['path']]==r['sha256'] for r in files)
        preserved.append(dict(run_id=run.name,files_checked=len(files),files=files,all_unchanged=True))
    rawcount=sum(r['files_checked'] for r in preserved)
    write('run_preservation.json',dict(runs=preserved,total_raw_run_files=rawcount,
          original_execution_and_acceptance_unchanged=True))
    for p in OUT.glob('*.py'):ast.parse(p.read_text())
    sync=[]
    for rel in ['docs/reports/SIM240_AI_CONTEXT.md','docs/reports/AI_HANDOFF_20261015.md']:
        p=PROJECT/rel;original=p.read_text();start=original.index('## ');end=original.find('\n## ',start+3)
        assert end>start and original[start:end].startswith('## C04已实际运行完成，尚待原SDI-v1完整结果验收')
        (OUT/(p.stem+'_before.md')).write_text(original)
        revised=original[:start]+CURRENT+original[end:];oldsha=sha(p);p.write_text(revised)
        assert revised.endswith(original[end:])
        delta=OUT/(p.stem+'_update.diff')
        delta.write_text(''.join(difflib.unified_diff(original.splitlines(True),revised.splitlines(True),fromfile=rel+' before',tofile=rel+' after')))
        sync.append(dict(path=rel,before_sha256=oldsha,after_sha256=sha(p),only_current_section_replaced=True,
                         subsequent_sections_unchanged=True,diff=delta.name))
    write('state_sync.json',dict(checked_at=stamp,files=sync,AI_launched_solver=False))
    package=PROJECT/'CASE/interface_static_darcy_v1_3'
    release=json.loads((package/'common/release_manifest.json').read_text())
    paths={p for run in runs for p in run.rglob('*') if p.is_file()}
    paths.update(package/r['path'] for r in release['files']);paths.add(package/'common/release_manifest.json')
    for rel in ['docs/reports/Static_Darcy_interface_protocol_20261030/protocol.json',
                'docs/reports/Static_Darcy_interface_protocol_20261030/PROTOCOL.md',
                'docs/reports/Static_Darcy_interface_protocol_20261030/INTERFACE_REVIEW.md',
                'docs/reports/Shared_transport_interface_20261030/coefficient_examples.json',
                'docs/reports/SDI_C01_results_20261030/interface_analysis_geometry_v1_1.json',
                'docs/reports/SDI_C01_results_20261030/interface_analysis.json',
                'docs/reports/SDI_C03_results_20261030/audit_raw_results.py']:
        paths.add(PROJECT/rel)
    paths.update(PROJECT/p for p in references.values())
    paths.update(p for p in OUT.iterdir() if p.is_file())
    write('source_manifest.json',dict(created_at=stamp,
          scope='Three completed raw runs, C04 preparation, frozen input sources, methods and analysis artifacts',
          local_sha256_verified=True,independent_human_verified=False,
          excludes='This manifest and final verification to avoid circular hashes',
          files=[dict(path=str(p.relative_to(PROJECT)),sha256=sha(p)) for p in sorted(paths)]))
    v=dict(checked_at=stamp,case_id='C04',run_id=analysis['run_id'],protocol_id='SDI-v1',checker_version=analysis['checker_version'],
          numerical_checks=count,all_numerical_checks_satisfied=True,NUMERICAL_GATE='PASS',RESULT_PASS=True,
          geometry_PASS=True,geometry_scope='synthetic_average_domain_only',physical_validation='NOT_EVALUATED',
          independent_human_acceptance=False,checker_matches_launch_copy=True,thresholds_unchanged=True,
          coefficient_family_and_direction_verified=True,C02_C03_reanalyses_identical_except_version=True,
          C04_C02_same_direction_formula_comparison_completed=True,C04_C03_same_formula_direction_comparison_completed=True,
          native_fields_equal_CSV=True,independent_local_arithmetic_completed=True,
          existing_files_preserved=len(now),raw_run_files_preserved=rawcount,original_execution_acceptance_unchanged=True,
          no_solver_run=True,no_new_compilation=True,no_refit=True,no_next_case_preparation_or_execution=True,
          no_commit_or_push=True,old_formal_gates_unchanged=True,reference_qualified=False,
          strict_error_bound_established=False,submission_ready=False,prediction='HOLD')
    write('verification.json',v)
    links=[]
    for p in [OUT/'REPORT.md',OUT/'METRICS.md']:
        for target in re.findall(r'\[[^\]]+\]\(([^)]+)\)',p.read_text()):
            if '://' in target or target.startswith('#'):continue
            assert (p.parent/target.split('#')[0]).resolve().exists(),target
            links.append(dict(source=p.name,target=target))
    for r in sync:assert sha(PROJECT/r['path'])==r['after_sha256']
    for r in json.loads((OUT/'source_manifest.json').read_text())['files']:
        assert sha(PROJECT/r['path'])==r['sha256'],r['path']
    v.update(local_links_checked=len(links),local_links_all_exist=True,source_manifest_files_verified=len(paths),state_hashes_verified=True)
    write('verification.json',v)
    print(json.dumps({k:v[k] for k in ['numerical_checks','NUMERICAL_GATE','RESULT_PASS','existing_files_preserved',
          'raw_run_files_preserved','source_manifest_files_verified','local_links_checked']},ensure_ascii=False))


if __name__=='__main__':main()

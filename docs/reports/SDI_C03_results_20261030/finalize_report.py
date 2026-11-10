"""Bind completed-result evidence, check preservation, and update shared state. No solve."""
import ast
import difflib
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[2]


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def write(name,value):
    (OUT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n')


CURRENT='''## C03满足原SDI-v1，原公式与V2横槽对照已完成（2026-10-30）

- 用户本轮明确授权完整分析已有C03并与C01横槽对照，仅结果分析，不重跑、不改门槛。C03 run_id=SDI_C03_v1_2_20261030_01；本机2026-10-30 05:39:42完成，两端退出0、无超时，二维106次、OF40次。入口 `docs/reports/SDI_C03_results_20261030/REPORT.md`、METRICS.md及interface_analysis.json。
- 启动留存检查器与当前1.2.0相同，按原SDI-v1两端各23项、跨端4项共50项数值检查全部满足。NUMERICAL_GATE=PASS、RESULT_PASS=true、geometry_PASS=true（仅512单元合成平均域），physical_validation=NOT_EVALUATED、independent_human_acceptance=false。原execution.json/result_acceptance=NOT_EVALUATED仍不改，独立结果记录在本轮外部报告；不升级旧科学Gate。
- 25份运行绑定、44份发布文件及21个运行库哈希匹配，协议thresholds/linear_solver、系数源、方向与启动版本核对。原生p/U/J/phi/phi_U与CSV逐项一致；另以math.fsum重算平均量、Q、守恒、恢复K及耗散，见binding_audit.json、independent_raw_audit.json。两端恢复Kxx约6.518158783783783e-23m³，Umean约5.214527027027027e-7m/s；Q约3.1287162162167e-18m³/s。
- C03压力最大相对解析偏差二维7.01476e-14/OF2.14643e-13，局部流量不平衡绝对和/解析Q为2.14468e-11/2.63246e-11（门槛1e-8），能量偏差约1.59e-13/1.22e-13；真实归一化残差6.70220e-13/8.22680e-13（门槛1e-12），跨端Q相对差3.66877e-14。其余指标与原门槛完整列于METRICS.md，不代表50个独立物理验证。
- C01/C03实际对照来自两例原始CSV：相同24/0Pa、24×48μm、H=125nm、512网格、μ=0.001Pa·s、槽沿y/驱动x、U=J/H、D=H K⁻¹；10份边界/网格/离散字典及6份求解源码/Make/二进制相同，唯一物理输入变化为V2→原公式K/D。C01只读重验除版本元数据外与旧分析逐项相同，未重跑。证据C01_reanalysis.json、C01_C03_comparison.json。
- C03/C01实际Q比二维1.4313684610460748、OF1.4313684610460977，对应解析1.4313684610462438；两例压力场最大差约3.74e-12/5.61e-12Pa。以原公式为分母，V2静态Q低约30.1368%，R_Q=Δp/Q高约43.1368%。这是输入系数导致的平均模型变化，倍率仅描述性核对，不增Gate，不是挤压阻力F/V或原/V2物理准确性结论。
- 本轮222份既有包/结果/报告与两次运行共80份原始文件集和哈希保持，见preservation_before.json、run_preservation.json、verification.json。新改动仅本轮SDI_C03_results_20261030报告/只读审计和对照脚本/证据与本状态、最新交接，state_sync.json留存更新。无求解/编译/重跑/重新拟合/真实N8提取/提交推送/对外发送；C01严格零几何识别的原未评价与修正记录均保留。
- C01/C02/C03分别只在既定静态平均接口范围通过；真实沟槽独立参照、一般斜槽、复杂压力、网格独立、严格误差界、未拟合新条件、挤压/两相/动态及内置DarcyForchheimer接入仍未验证。旧D4_N8_diag_v3_1_20261026_v1仍NUMERICAL_GATE=NOT_EVALUATED、RESULT_PASS=false、geometry_PASS=null；reference_qualified=false、strict_error_bound_established=false、submission_ready=false、预测HOLD与历史FAIL不变。
- 本轮任务已完成。下一具体动作是用户阅读本报告并决定后续研究范围；若继续预定主对照，C04仅为可讨论的后续项，本轮未准备/启动C04，也不新增长算授权。接手从本报告、原始证据及本条继续，不依赖旧聊天；常规后续代码/数值工作GPT-6.1 Sol｜High，疑难物理矛盾或公式最终冻结按协议GPT-6 Astra｜High。
'''


def main():
    if (OUT/'verification.json').exists():raise FileExistsError('Final report verification exists')
    stamp=datetime.now(ZoneInfo('Asia/Shanghai')).isoformat()
    analysis=json.loads((OUT/'interface_analysis.json').read_text())
    count=sum(len(r['checks']) for r in analysis['results'].values())+len(analysis['cross_checks'])
    assert count==50 and analysis['NUMERICAL_GATE']=='PASS' and analysis['RESULT_PASS'] is True
    assert all(c['satisfied'] for r in analysis['results'].values() for c in r['checks'])
    assert all(c['satisfied'] for c in analysis['cross_checks'])
    old=json.loads((ROOT/'docs/reports/SDI_C01_results_20261030/interface_analysis_geometry_v1_1.json').read_text())
    new=json.loads((OUT/'C01_reanalysis.json').read_text());new.pop('checker_version')
    assert old==new
    before=json.loads((OUT/'preservation_before.json').read_text())
    oldfiles={r['path']:r['sha256'] for r in before['files']}
    current={str(p.relative_to(ROOT)):sha(p) for rel in before['roots']
             for p in sorted((ROOT/rel).rglob('*')) if p.is_file()}
    assert oldfiles==current
    write('preservation_verification.json',dict(checked_at=stamp,files=len(current),
          file_sets_identical=True,sha256_all_identical=True,roots=before['roots']))
    runs=[ROOT/'CASE/interface_static_darcy_v1/runs/SDI_C01_v1_20261030_01',
          ROOT/'CASE/interface_static_darcy_v1_2/runs/SDI_C03_v1_2_20261030_01']
    preserved=[]
    for run in runs:
        files=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in sorted(run.rglob('*')) if p.is_file()]
        assert all(oldfiles[r['path']]==r['sha256'] for r in files)
        preserved.append(dict(run_id=run.name,files_checked=len(files),files=files,all_unchanged=True))
    write('run_preservation.json',dict(runs=preserved,total_raw_run_files=sum(r['files_checked'] for r in preserved),
          original_execution_and_acceptance_unchanged=True))
    for p in OUT.glob('*.py'):ast.parse(p.read_text())
    sync=[]
    for rel in ['docs/reports/SIM240_AI_CONTEXT.md','docs/reports/AI_HANDOFF_20261015.md']:
        p=ROOT/rel;original=p.read_text();start=original.index('## ');end=original.find('\n## ',start+3)
        assert end>start and original[start:end].startswith('## C03已实际运行完成，尚待SDI-v1完整结果验收')
        (OUT/(p.stem+'_before.md')).write_text(original)
        revised=original[:start]+CURRENT+original[end:]
        before_sha=sha(p);p.write_text(revised);assert revised.endswith(original[end:])
        diff=OUT/(p.stem+'_update.diff')
        diff.write_text(''.join(difflib.unified_diff(original.splitlines(True),revised.splitlines(True),fromfile=rel+' before',tofile=rel+' after')))
        sync.append(dict(path=rel,before_sha256=before_sha,after_sha256=sha(p),
                         only_current_first_section_replaced=True,subsequent_sections_unchanged=True,diff=diff.name))
    write('state_sync.json',dict(checked_at=stamp,files=sync,solver_launched=False))
    package=ROOT/'CASE/interface_static_darcy_v1_2'
    release=json.loads((package/'common/release_manifest.json').read_text())
    paths={p for run in runs for p in run.rglob('*') if p.is_file()}
    paths.update(package/r['path'] for r in release['files'])
    paths.add(package/'common/release_manifest.json')
    for rel in ['docs/reports/Static_Darcy_interface_protocol_20261030/protocol.json',
                'docs/reports/Static_Darcy_interface_protocol_20261030/PROTOCOL.md',
                'docs/reports/Static_Darcy_interface_protocol_20261030/INTERFACE_REVIEW.md',
                'docs/reports/Shared_transport_interface_20261030/coefficient_examples.json',
                'docs/reports/SDI_C01_results_20261030/interface_analysis_geometry_v1_1.json',
                'docs/reports/SDI_C01_results_20261030/interface_analysis.json',
                'docs/reports/SDI_C02_results_20261030/audit_raw_results.py']:
        paths.add(ROOT/rel)
    paths.update(p for p in OUT.iterdir() if p.is_file())
    write('source_manifest.json',dict(created_at=stamp,
          scope='Completed raw runs, unchanged C03 package, upstream protocol/coefficients and this analysis evidence',
          local_sha256_verified=True,independent_human_verified=False,
          excludes='This manifest and final verification, avoiding circular hashes',
          files=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in sorted(paths)]))
    verification=dict(checked_at=stamp,case_id='C03',run_id=analysis['run_id'],protocol_id='SDI-v1',
          checker_version=analysis['checker_version'],numerical_checks=count,all_numerical_checks_satisfied=True,
          NUMERICAL_GATE='PASS',RESULT_PASS=True,geometry_PASS=True,geometry_scope='synthetic_average_domain_only',
          physical_validation='NOT_EVALUATED',independent_human_acceptance=False,
          checker_matches_launch_copy=True,thresholds_unchanged=True,coefficient_direction_verified=True,
          C01_reanalysis_identical_except_version=True,C01_C03_actual_raw_comparison_completed=True,
          native_fields_equal_CSV=True,independent_local_arithmetic_completed=True,
          existing_files_preserved=len(current),raw_run_files_preserved=sum(r['files_checked'] for r in preserved),
          original_execution_acceptance_unchanged=True,no_solver_run=True,no_new_compilation=True,
          no_refit=True,no_next_case_preparation_or_execution=True,no_commit_or_push=True,
          old_formal_gates_unchanged=True,reference_qualified=False,strict_error_bound_established=False,
          submission_ready=False,prediction='HOLD')
    write('verification.json',verification)
    checked=[]
    for p in [OUT/'REPORT.md',OUT/'METRICS.md']:
        for target in re.findall(r'\[[^\]]+\]\(([^)]+)\)',p.read_text()):
            if '://' in target or target.startswith('#'):continue
            assert (p.parent/target.split('#')[0]).resolve().exists(),target
            checked.append(dict(source=p.name,target=target))
    for rec in sync:assert sha(ROOT/rec['path'])==rec['after_sha256']
    for rec in json.loads((OUT/'source_manifest.json').read_text())['files']:
        assert sha(ROOT/rec['path'])==rec['sha256'],rec['path']
    verification.update(local_links_checked=len(checked),local_links_all_exist=True,
                        source_manifest_files_verified=len(paths),state_hashes_verified=True)
    write('verification.json',verification)
    print(json.dumps({k:verification[k] for k in ['numerical_checks','NUMERICAL_GATE','RESULT_PASS',
         'existing_files_preserved','raw_run_files_preserved','source_manifest_files_verified','local_links_checked']},ensure_ascii=False))


if __name__=='__main__':main()

"""Verify sealed C04 preparation and preserve old evidence; synchronize handoffs. No solve."""
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
ROOT=PROJECT/'CASE/interface_static_darcy_v1_3'


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def write(name,value):
    (OUT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n')


CURRENT='''## C04原公式沿槽包静态核对完成，启动命令已备、实际执行待确认（2026-10-30）

- 用户明确授权准备C04、保持原SDI-v1边界/平均定义/门槛，静态核对后交付启动命令；本轮不由AI启动。新独立包 `CASE/interface_static_darcy_v1_3/`，入口README.md、common/C04_SPEC.md；详细证据 `docs/reports/SDI_C04_preparation_20261030/REPORT.md`。C04是SDI原公式沿槽例，不是旧路线表参数扫描Case04。
- C04原公式、槽沿x、驱动沿x；与C02作同方向原/V2对照，与C03作同公式方向对照。保持24/0Pa、24×48μm、H=125nm、μ=0.001Pa·s、512单元、U=J/H及D=H K⁻¹、总阻力不重复加壁面剪切。Kxx=2.4088541666666665e-22、Kyy=6.518158783783783e-23m³；K/D相对C03同时交换。原协议thresholds和linear_solver逐项相同，10份边界/网格/离散字典与C02相同。
- 两份C++、两份Make和两个二进制与C01哈希相同，复用真实编译证据，本轮未新编译。C04路径checkMesh通过；二维audit-only及OF auditOnly退出0，仅矩阵装配、初始压力0、flow_solved=false，无压力迭代。准备几何通过仅指合成平均域。
- 检查器1.3.0只扩展C04支持及版本说明，全部函数AST与1.2.0相同；15项人造功能测试通过，完整日志留存。只读C01/C02/C03旧结果，各50项指标、Gate和原始文件哈希与旧分析逐项一致，仅忽略版本元数据；无CFD重跑。证据regression_comparison.json和包内reports/functional_tests.log/json。
- 新封装46文件、21运行库绑定，默认只读preflight通过。命令身份/bash语法核对通过，sdi_c04会话未占用、预留运行目录不存在。planned_run_id=SDI_C04_v1_3_20261030_01，actual_run_id=null、run_completed=false，NUMERICAL_GATE=NOT_EVALUATED、RESULT_PASS=null、geometry_PASS=true（仅准备阶段合成平均域）、physical_validation=NOT_EVALUATED、independent_human_acceptance=false。命令回执launch_command.json，不调用C03脚本或复用C03编号；材料/命令已备不等于实际执行。
- C04解析预期（不是结果）：Ux约1.927083333333333e-6m/s、Jx约2.4088541666666664e-13m²/s、Q约1.15625e-17m³/s；C04/C02解析Q比2.3130890243424327，C04/C03为3.6956052262174715，仅描述性预期、不增倍率Gate或物理准确性结论。
- C01—C03旧包/运行及相关报告346份文件集和哈希保持，见preservation_before.json、verification.json。本轮仅新包/准备报告/命令回执及本状态、最新交接，state_sync.json留存更新；未创建C04 runs、时间1或SDI_output，AI未执行求解/重跑/拟合/真实N8提取/建立tmux会话/提交推送/对外发送。C01/C02/C03既有局部接口通过及C03/C01对照保留，C01历史严格零几何识别记录不覆盖。
- 真实沟槽独立参照、一般斜向/复杂压力、网格独立、严格误差界、未拟合新条件、挤压/两相/动态及内置DarcyForchheimer接入仍未验证。旧D4_N8_diag_v3_1_20261026_v1仍NUMERICAL_GATE=NOT_EVALUATED、RESULT_PASS=false、geometry_PASS=null；reference_qualified=false、strict_error_bound_established=false、submission_ready=false、预测HOLD和历史FAIL不变。
- 下一具体动作：用户在本机终端执行本轮单条sdi_c04 tmux命令并返回输出（无输出也说明），随后单次核查启动/完成状态；完成后另按原SDI-v1分析C04并对照C02/C03。只允许该例两端、失败/超时即停、不重试、不自动进入C05或其他Gate。命令交付后Codex停止本任务，不等待或轮询；用户请求不授予AI代启动或其他长算权限。启动核查GPT-6.1 Sol｜Low；完整结果分析GPT-6.1 Sol｜High。
'''


def main():
    if (OUT/'verification.json').exists():raise FileExistsError('Final verification exists')
    stamp=datetime.now(ZoneInfo('Asia/Shanghai')).isoformat()
    release=json.loads((ROOT/'common/release_manifest.json').read_text())
    prep=json.loads((ROOT/'reports/preparation.json').read_text())
    command=json.loads((OUT/'launch_command.json').read_text())
    assert release['case_id']=='C04' and release['planned_run_id']=='SDI_C04_v1_3_20261030_01'
    assert release['actual_run_id'] is None and release['flow_run_authorized_by_preparation'] is False
    for r in release['files']:assert sha(ROOT/r['path'])==r['sha256'],r['path']
    for r in release['libraries']:assert sha(Path(r['path']))==r['sha256'],r['path']
    assert len(release['files'])==46 and len(release['libraries'])==21
    assert prep['flow_solver_executed'] is False and prep['new_compilation_performed'] is False
    assert all(c['exit_code']==0 for c in prep['commands'])
    assert prep['two_dimensional_audit']['flow_solved'] is False and prep['openfoam_audit']['flow_solved'] is False
    assert command['planned_run_id']==release['planned_run_id'] and command['AI_launched_solver'] is False
    assert not (ROOT/'runs').exists()
    for rel in ['openfoam/cases/C04/1','openfoam/cases/C04/SDI_output']:assert not (ROOT/rel).exists()
    before=json.loads((OUT/'preservation_before.json').read_text())
    old={r['path']:r['sha256'] for r in before['files']}
    now={str(p.relative_to(PROJECT)):sha(p) for rel in before['roots'] for p in sorted((PROJECT/rel).rglob('*')) if p.is_file()}
    assert old==now
    write('preservation_verification.json',dict(checked_at=stamp,old_files_preserved=len(old),
          file_sets_identical=True,all_sha256_identical=True,roots=before['roots']))
    for p in ROOT.rglob('*.py'):ast.parse(p.read_text())
    for p in ROOT.rglob('*.json'):json.loads(p.read_text())
    sync=[]
    for rel in ['docs/reports/SIM240_AI_CONTEXT.md','docs/reports/AI_HANDOFF_20261015.md']:
        p=PROJECT/rel;original=p.read_text();start=original.index('## ');end=original.find('\n## ',start+3)
        assert end>start and original[start:end].startswith('## C03满足原SDI-v1')
        backup=OUT/(p.stem+'_before.md');backup.write_text(original)
        revised=original[:start]+CURRENT+original[end:];old_sha=sha(p);p.write_text(revised)
        assert revised.endswith(original[end:])
        delta=OUT/(p.stem+'_update.diff')
        delta.write_text(''.join(difflib.unified_diff(original.splitlines(True),revised.splitlines(True),fromfile=rel+' before',tofile=rel+' after')))
        sync.append(dict(path=rel,before_sha256=old_sha,after_sha256=sha(p),only_current_section_replaced=True,
                         subsequent_sections_unchanged=True,backup=backup.name,diff=delta.name))
    write('state_sync.json',dict(checked_at=stamp,files=sync,AI_launched_solver=False))
    paths={p for p in ROOT.rglob('*') if p.is_file()}
    paths.update(p for p in OUT.iterdir() if p.is_file())
    for rel in ['docs/reports/Static_Darcy_interface_protocol_20261030/protocol.json',
                'docs/reports/Shared_transport_interface_20261030/coefficient_examples.json',
                'CASE/interface_static_darcy_v1_1/common/C02.json','CASE/interface_static_darcy_v1_2/common/C03.json']:
        paths.add(PROJECT/rel)
    write('source_manifest.json',dict(created_at=stamp,scope='C04 preparation, upstream input source, comparison configurations and preparation evidence',
          independent_human_verified=False,excludes='This manifest and final verification to avoid circular hashes',
          files=[dict(path=str(p.relative_to(PROJECT)),sha256=sha(p)) for p in sorted(paths)]))
    verification=dict(checked_at=stamp,case_id='C04',protocol_id='SDI-v1',checker_version='1.3.0',
          release_files_verified=46,runtime_libraries_verified=21,old_files_preserved=len(old),
          synthetic_tests=15,old_case_regressions={'C01':50,'C02':50,'C03':50},checker_function_ASTs_unchanged=True,
          input_direction_verified=True,boundaries_average_definitions_and_thresholds_unchanged=True,
          new_compilation_performed=False,reused_compilation_identity_verified=True,static_mesh_and_matrix_checks_satisfied=True,
          read_only_preflight_satisfied=True,launch_command_syntax_and_identity_checked=True,
          planned_run_id=release['planned_run_id'],actual_run_id=None,flow_solver_executed=False,
          NUMERICAL_GATE='NOT_EVALUATED',RESULT_PASS=None,geometry_PASS=True,geometry_scope='preparation_static_synthetic_domain_only',
          physical_validation='NOT_EVALUATED',independent_human_acceptance=False,old_scientific_gates_unchanged=True,
          no_next_case=True,no_commit_or_push=True)
    write('verification.json',verification)
    docs=[ROOT/'README.md',ROOT/'common/C04_SPEC.md',ROOT/'common/CHECKER_CHANGELOG.md',OUT/'REPORT.md']
    links=[]
    for p in docs:
        for target in re.findall(r'\[[^\]]+\]\(([^)]+)\)',p.read_text()):
            if '://' in target or target.startswith('#'):continue
            assert (p.parent/target.split('#')[0]).resolve().exists(),(p,target)
            links.append(dict(source=str(p.relative_to(PROJECT)),target=target))
    for r in sync:assert sha(PROJECT/r['path'])==r['after_sha256']
    for r in json.loads((OUT/'source_manifest.json').read_text())['files']:
        assert sha(PROJECT/r['path'])==r['sha256'],r['path']
    verification.update(local_links_checked=len(links),local_links_all_exist=True,source_manifest_files_verified=len(paths),state_hashes_verified=True)
    write('verification.json',verification)
    print(json.dumps({k:verification[k] for k in ['case_id','release_files_verified','runtime_libraries_verified','old_files_preserved',
         'synthetic_tests','old_case_regressions','flow_solver_executed','source_manifest_files_verified','local_links_checked']},ensure_ascii=False))


if __name__=='__main__':main()

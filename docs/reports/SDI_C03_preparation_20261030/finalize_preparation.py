"""Check sealed preparation/preservation and synchronize project handoffs; no solve."""
import ast
import difflib
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

PROJECT=Path(__file__).resolve().parents[3]
REPORT=Path(__file__).resolve().parent
ROOT=PROJECT/'CASE/interface_static_darcy_v1_2'


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def dump(p,value):p.write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n')


CURRENT='''## C03原公式横槽材料与静态核对完成，保持未启动（2026-10-30）

- 用户裁定仅准备SDI-v1 C03原公式横槽对照，保持边界、平均定义和验收门槛，暂不启动。新增独立包 `CASE/interface_static_darcy_v1_2/`，入口README.md、common/C03_SPEC.md；详细证据 `docs/reports/SDI_C03_preparation_20261030/REPORT.md`。此C03不是旧路线表Case03。
- C03与C01同为槽沿y、x压差24/0Pa、G=1e6Pa/m、H=125nm、24×48μm、512单元，U=J/H，D=H K⁻¹；只将V2系数换为original_local_cubic。字典/网格逐字节对照，共同输入和原SDI-v1 thresholds/linear_solver逐项一致；不重复加壁面剪切或另一份阻力源。
- 已核对两份C++、Make配置和两个二进制与C01哈希一致，复用原真实编译证据，本轮未新编译。C03路径checkMesh通过；二维audit-only及OF auditOnly退出0，仅检查输入/装配矩阵，无压力求解，initial_p_max=0。geometry_PASS=true仅指合成平均域，不是实际沟槽几何。
- 检查器1.2.0只增加C03身份支持及版本说明，所有函数AST与1.1.0相同，保留既有几何修正。15项人造数据测试通过；只读已有C01/C02，各50项数值检查、全部指标/Gate与原始文件哈希和旧分析一致。原C01严格零识别未评价记录及后续修正证据保留。
- 新封装绑定44文件、21运行库，默认只读preflight通过；launch_ready仅技术材料齐备，flow_run_authorized_by_preparation=false。planned_run_id=SDI_C03_v1_2_20261030_01，actual_run_id=null，run_completed=false，NUMERICAL_GATE=NOT_EVALUATED、RESULT_PASS=null、geometry_PASS=true（仅合成平均域）、physical_validation=NOT_EVALUATED、independent_human_acceptance=false。无runs目录、SDI_output、时间1场或新tmux会话。
- C03解析预期（不是结果）：Kxx=6.518158783783783e-23m³、Dxx=1.917719468739877e15m⁻²，Ux约5.214527027027026e-7m/s、Q约3.1287162162162162e-18m³/s；C03/C01解析Q比1.4313684610462438仅描述性核对，不增门槛或声称物理改善。两例预期压力相同，真实准确性仍需独立沟槽/实验参考。
- 原C01/C02两发布包及既有结果/报告223份旧文件集和哈希保持，详见preservation_verification.json。已完成C01、C02接口NUMERICAL_GATE=PASS、RESULT_PASS=true、geometry_PASS=true（仅合成平均域）状态保持，未重跑。旧D4_N8_diag_v3_1_20261026_v1仍NUMERICAL_GATE=NOT_EVALUATED、RESULT_PASS=false、geometry_PASS=null；reference_qualified=false、strict_error_bound_established=false、submission_ready=false、预测HOLD与历史FAIL不变。
- 本轮只准备C03、静态检查和旧例只读回归，沿用scientific-writing组织报告；改动为新包/新报告与本状态/最新交接。无流动求解、新实际run_id、拟合、真实N8提取、物理放行、下一例启动、提交推送或对外发送。现有卡点为C03尚未获启动授权且无计算结果；独立准确性/网格证据缺口也未解除。
- 下一具体动作：保持C03未启动，等待用户后续明确启动指令；届时仅该例两端，完成后按原SDI-v1另行读取原始证据并对照C01，不自动重试、C04或其他Gate。本轮不交付启动命令，无新增长算授权。下一阶段GPT-6.1 Sol｜High；疑难理论矛盾或最终物理裁决另按协议GPT-6 Astra｜High。
'''


def main():
    if (REPORT/'verification.json').exists():raise FileExistsError('Final verification exists')
    stamp=datetime.now(ZoneInfo('Asia/Shanghai')).isoformat()
    before=json.loads((REPORT/'preservation_before.json').read_text())
    prior={r['path']:r['sha256'] for r in before['files']}
    now={str(p.relative_to(PROJECT)):sha(p) for rel in before['roots']
         for p in sorted((PROJECT/rel).rglob('*')) if p.is_file()}
    assert prior==now, 'Old evidence file set or content changed'
    dump(REPORT/'preservation_verification.json',dict(checked_at=stamp,
         files_checked=len(prior),file_sets_identical=True,all_sha256_identical=True,
         roots=before['roots'],no_old_files_modified=True))
    release=json.loads((ROOT/'common/release_manifest.json').read_text())
    assert release['case_id']=='C03' and release['planned_run_id']=='SDI_C03_v1_2_20261030_01'
    assert release['flow_run_authorized_by_preparation'] is False and release['actual_run_id'] is None
    for r in release['files']:assert sha(ROOT/r['path'])==r['sha256'], r['path']
    for r in release['libraries']:assert sha(Path(r['path']))==r['sha256'], r['path']
    assert len(release['files'])==44 and len(release['libraries'])==21
    oldrelease=json.loads((PROJECT/'CASE/interface_static_darcy_v1_1/common/release_manifest.json').read_text())
    assert release['libraries']==oldrelease['libraries']
    assert not (ROOT/'runs').exists()
    for rel in ['openfoam/cases/C03/1','openfoam/cases/C03/SDI_output']:
        assert not (ROOT/rel).exists()
    for p in ROOT.rglob('*.py'):ast.parse(p.read_text())
    for p in ROOT.rglob('*.json'):json.loads(p.read_text())
    sync=[]
    for rel in ['docs/reports/SIM240_AI_CONTEXT.md','docs/reports/AI_HANDOFF_20261015.md']:
        p=PROJECT/rel;original=p.read_text()
        start=original.index('## ');end=original.find('\n## ',start+3)
        assert end>start and original[start:end].startswith('## C02已完成并满足SDI-v1')
        revised=original[:start]+CURRENT+original[end:]
        backup=REPORT/(p.stem+'_before.md');backup.write_text(original)
        delta=REPORT/(p.stem+'_update.diff')
        delta.write_text(''.join(difflib.unified_diff(original.splitlines(True),revised.splitlines(True),fromfile=rel+' (before)',tofile=rel+' (after)')))
        before_sha=sha(p);p.write_text(revised)
        assert revised.endswith(original[end:])
        sync.append(dict(path=rel,before_sha256=before_sha,after_sha256=sha(p),
                         only_current_first_section_replaced=True,subsequent_sections_unchanged=True,
                         backup=backup.name,diff=delta.name))
    dump(REPORT/'state_sync.json',dict(checked_at=stamp,files=sync,CFD_solver_launched=False))
    manifest_paths=[p for p in sorted(ROOT.rglob('*')) if p.is_file()]
    manifest_paths += [PROJECT/'docs/reports/Static_Darcy_interface_protocol_20261030/protocol.json',
                       PROJECT/'docs/reports/Shared_transport_interface_20261030/coefficient_examples.json']
    manifest_paths += [p for p in sorted(REPORT.iterdir()) if p.is_file()]
    dump(REPORT/'source_manifest.json',dict(created_at=stamp,
         scope='C03 package, bound upstream design/coefficient source and preparation evidence existing at seal',
         excludes='This manifest and final verification to avoid self reference',
         files=[dict(path=str(p.relative_to(PROJECT)),sha256=sha(p)) for p in manifest_paths]))
    verification=dict(checked_at=stamp,kind='PREPARATION_ONLY_NO_C03_FLOW_SOLUTION',
         case_id='C03',protocol_id='SDI-v1',checker_version='1.2.0',
         release_files_verified=len(release['files']),runtime_libraries_verified=len(release['libraries']),
         old_files_preserved=len(prior),test_count=15,synthetic_tests_satisfied=True,
         C01_unchanged_numerical_checks=50,C02_unchanged_numerical_checks=50,
         preflight=dict(kind='OBSERVED_DEFAULT_RUNNER_TERMINAL_RESULT',preflight_satisfied=True,
                        flow_solver_executed=False,planned_run_id=release['planned_run_id']),
         thresholds_and_linear_solver_unchanged=True,new_compilation_performed=False,
         flow_solver_executed=False,no_run_directory=True,no_flow_output=True,
         actual_run_id=None,planned_run_id=release['planned_run_id'],
         NUMERICAL_GATE='NOT_EVALUATED',RESULT_PASS=None,geometry_PASS=True,
         geometry_scope='synthetic_average_domain_only',physical_validation='NOT_EVALUATED',
         independent_human_acceptance=False,flow_run_authorized=False,
         old_scientific_gates_unchanged=True)
    dump(REPORT/'verification.json',verification)
    docs=[ROOT/'README.md',ROOT/'common/C03_SPEC.md',ROOT/'common/CHECKER_CHANGELOG.md',REPORT/'REPORT.md']
    links=[]
    for p in docs:
        for target in re.findall(r'\[[^\]]+\]\(([^)]+)\)',p.read_text()):
            if '://' in target or target.startswith('#'):continue
            destination=(p.parent/target.split('#')[0]).resolve()
            assert destination.exists(), (str(p),target)
            links.append(dict(source=str(p.relative_to(PROJECT)),target=target,exists=True))
    verification['local_links_checked']=len(links)
    verification['local_links_all_exist']=True
    dump(REPORT/'verification.json',verification)
    print(json.dumps(dict(release_files=44,libraries=21,old_files_unchanged=len(prior),
                          local_links_checked=len(links),handoffs_updated=2,C03_flow_solved=False)))


if __name__=='__main__':main()

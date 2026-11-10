"""Create isolated S4 engineering copies; never run any native/build/VTK code."""
from pathlib import Path
import json,shutil,hashlib
ROOT=Path('/home/dell/yuanyuanxu/SIM240');OUT=Path(__file__).resolve().parent
OLD=ROOT/'CASE/unseen_v2_reference_checker_S3_reuse_v1_1';OLDCASE=ROOT/'CASE/unseen_v2_reference_S3_reuse_v1_1'
CHECK=ROOT/'CASE/unseen_v2_reference_checker_S4_reuse_v1';CASE=ROOT/'CASE/unseen_v2_reference_S4_reuse_v1'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
load=lambda p:json.loads(Path(p).read_text())
def write(p,s):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s)
assert not CHECK.exists() and not CASE.exists()
for folder in ['analysis','common','revision','s1_revision','s2_revision','s3_revision']:
    shutil.copytree(OLD/folder,CHECK/folder,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
for name in ['test_checker.py','test_packet_guards.py','test_residuals.py','fixtures_contract.py']:
    write(CHECK/'tests'/name,(OLD/'tests'/name).read_text())
stage=(OLD/'analysis/stage_s3.py').read_text().replace('S3','S4').replace('stage_s3','stage_s4').replace('v1_1','v1').replace('v1.1','v1').replace('S4_REG_LINEARITY','S4_THIN_GRID')
stage=stage.replace("CASES = tuple(f'URV1_U_REG_{d}_dx2p5_a{a}' for a in (50000, 200000) for d in ('P', 'T'))", "CASES = tuple(f'URV1_U_THIN_{d}_dx{dx}_a100000' for dx in ('5', '2p5', '1p25') for d in ('P', 'T'))")
stage=stage.replace("RUN_IDS = tuple(f'URV_S4_{d}_a{a}_reuse_v1_20261103_01' for a in (50000, 200000) for d in ('P', 'T'))", "RUN_IDS = tuple(f'URV_S4_{d}_dx{dx}_reuse_v1_20261103_01' for dx in ('5', '2p5', '1p25') for d in ('P', 'T'))")
stage=stage.replace("{'2.5': 14400}","{'5': 3600, '2.5': 14400, '1.25': 43200}")
stage=stage.replace("bound.get('S4_authorized') is False and ", '')
stage=stage.replace('len(records) == 4','len(records) == 6').replace('== 4','== 6').replace('four','six').replace('twelve','eighteen')
stage=stage.replace('from zero_evidence import','from zero_evidence_s4 import')
write(CHECK/'analysis/stage_s4.py',stage)
zero=(OLD/'analysis/zero_evidence.py').read_text().replace('len(records)==len(plan)==12','len(records)==len(plan)==18').replace('twelve original','eighteen original').replace('len(seen)==4','len(seen)==6').replace('four unique','six unique')
write(CHECK/'analysis/zero_evidence_s4.py',zero)
contracts=(OLD/'analysis/contracts.py').read_text()
needle="        if bound.get('source_revision', {}).get('id') == 'URV-S3-S1-ELF-REUSE-v1.1':"
assert contracts.count(needle)==1
contracts=contracts.replace(needle,"        if bound.get('source_revision', {}).get('id') == 'URV-S4-S1-ELF-REUSE-v1':\n            from revision_s4_reuse import verify_s4_reuse\n            verify_s4_reuse(bound, observed, checker_case)\n        elif bound.get('source_revision', {}).get('id') == 'URV-S3-S1-ELF-REUSE-v1.1':")
write(CHECK/'analysis/contracts.py',contracts)
runner=(OLDCASE/'scripts/run_S3.py').read_text().replace('S3','S4').replace('stage_s3','stage_s4').replace('v1_1','v1')
runner=runner.replace("need(dx == 2.5, 'S4 requires original 2.5 nm grid')","need(dx in (5, 2.5, 1.25), 'S4 requires original three grids')")
start=runner.index('        from s3_baselines import control_for_direction')
end=runner.index('\n\n\ndef main():',start)
runner=runner[:start]+'''    from s4_grid import grid_for_direction
    reports = [grid_for_direction(bound, d, accepted_points, expected_sha) for d in ('P', 'T')]
    save(attempt / 'S4_grid_report.json', dict(stage='S4_THIN_GRID', directions=reports,
        GRID_CHECKS_PASS=all(r['GRID_CHECKS_PASS'] for r in reports), reference_qualified=False,
        MODEL_COMPARISON='NOT_EVALUATED', next_stage_started=False))
    need(all(r['GRID_CHECKS_PASS'] for r in reports), 'S4 grid evidence failed; no retry/extension/next stage')
    save(attempt / 'S4_completed.json', dict(stage='S4_THIN_GRID', solver_runs=6,
        GRID_CHECKS_PASS=True, next_stage_started=False, reference_qualified=False,
        MODEL_COMPARISON='NOT_EVALUATED'))
'''+runner[end:]
write(CASE/'scripts/run_S4.py',runner)
audit=(OLDCASE/'scripts/audit_S3_zero.py').read_text().replace('S3','S4').replace('stage_s3','stage_s4').replace('v1_1','v1').replace('from zero_evidence import','from zero_evidence_s4 import')
audit=audit.replace('twelve','eighteen').replace('native_describe=4','native_describe=6').replace('native_precheck=4','native_precheck=6').replace('native_initialize=4','native_initialize=6').replace('initialized_frames_read=4','initialized_frames_read=6').replace('planned_initial_field_reads=4','planned_initial_field_reads=6')
write(CASE/'scripts/audit_S4_zero.py',audit)
fixture=(OLD/'tests/fixtures_zero_v1_1.py').read_text().replace('S3','S4').replace('stage_s3','stage_s4').replace('v1_1','v1').replace('from zero_evidence import','from zero_evidence_s4 import')
fixture=fixture.replace("a=50000 if ident.endswith('a50000') else 200000", "a=100000;dx='5' if '_dx5_' in ident else ('2.5' if '_dx2p5_' in ident else '1.25')")
fixture=fixture.replace("dx_nm='2.5',h_nm='60.0'","dx_nm=dx,h_nm='30.0'")
for key in ['native_describe','native_precheck','native_initialize','initialized_frames_read']:fixture=fixture.replace(key+'=4',key+'=6')
write(CHECK/'tests/fixtures_zero_s4.py',fixture)
tests=(OLD/'tests/test_zero_v1_1.py').read_text().replace('fixtures_zero_v1_1','fixtures_zero_s4').replace('from zero_evidence import','from zero_evidence_s4 import').replace('stage_s3','stage_s4').replace('S3','S4').replace('twelve_records_and_four','eighteen_records_and_six').replace('len(f.fields),4','len(f.fields),6')
tests=tests.replace("dx_m='5e-9'","dx_m='9e-9'")
write(CHECK/'tests/test_zero_s4.py',tests)
write(CASE/'README.md', '''# S4 薄间隙三网格隔离接入准备

采用S4-MIP-v1，仅新增阶段/来源/权限和软件检查。直接引用同一S1 ELF，未改物理、未构建。
准备A全部执行权限关闭；六正式身份和18零步身份只是预留。
默认入口只读；原生18次零步及6次真实初态读取、性能推进、正式计算均另行授权。
科学common、check_results.py/evidence.py/read_fields.py保持原字节。
阶段内网格报告不放行完整参考资格、不比较V2、不进入S5或24条聚合。
''')
write(CHECK/'README.md', '''# S4 独立检查器接入

沿用原URV-v1/MRP/A1科学判据。S4专属来源和权限分支、zero_evidence_s4逐条R1/R2、六配置三网格证据；旧S3检查模块保留原样。
软件合成测试不产生原生/场读取或物理验收。原生18+6另行授权，准备封存不是启动合同。
''')
prior=ROOT/'docs/reports/URV_S4_prerun_scope_review_20261103_200311'
adoption=dict(protocol_id='S4-MIP-v1',user_instruction_verbatim='采用 S4-MIP-v1 最小范围后，隔离实现 S4 接入与软件检查，交付执行权限关闭的准备 A；原生审计、性能推进及正式计算仍另行授权。',
    scope_protocol_path=str(prior/'PROTOCOL.md'),scope_protocol_sha256=sha(prior/'PROTOCOL.md'),
    scope_decision_path=str(prior/'scope_decision.json'),scope_decision_sha256=sha(prior/'scope_decision.json'),
    implementation_authorized=True,build_required=False,native_zero_step_authorized=False,initial_field_readback_authorized=False,
    performance_time_stepping_authorized=False,formal_simulation_authorized=False)
write(CASE/'evidence/adoption.json',json.dumps(adoption,ensure_ascii=False,indent=2)+'\n')
oldanchor=load(OLD/'s3_revision/anchor.json');r3=OLDCASE/'evidence/S3_formal_launch_release_v1_1_20261103_01.json'
anchor=dict(revision_id='URV-S4-S1-ELF-REUSE-v1',simulation_authorized=False,status='EXACT_ELF_REUSE_NOT_EXECUTION_AUTHORITY',
    native_binary_path=oldanchor['native_binary_path'],native_binary_sha256=oldanchor['native_binary_sha256'],native_source_sha256=oldanchor['native_source_sha256'],
    machine_audit_path=oldanchor['machine_audit_path'],instruction_audit_status=oldanchor['instruction_audit_status'],
    predecessor_release_path=str(r3),predecessor_release_sha256=sha(r3),
    predecessor_review_path=str(ROOT/'docs/reports/URV_S3_completed_review_20261103_172033/independent_review.json'),
    predecessor_review_sha256=sha(ROOT/'docs/reports/URV_S3_completed_review_20261103_172033/independent_review.json'),
    source_diff_anchor_path=str(OLD/'s2_revision/anchor.json'),source_diff_anchor_sha256=sha(OLD/'s2_revision/anchor.json'))
write(CHECK/'s4_revision/anchor.json',json.dumps(anchor,indent=2)+'\n')
print('Isolated S4 scaffolding created; no native calls or copied build.')

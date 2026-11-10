#!/usr/bin/env python3
"""Consolidate completed-result evidence and update shared state; never solve."""
from pathlib import Path
import csv
import datetime
import difflib
import hashlib
import json

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
CASE = ROOT / 'CASE/unseen_v2_reference_S0_mrp_v1_a1'
CHECKER = ROOT / 'CASE/unseen_v2_reference_checker_mrp_v1_a1'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path):
    return json.loads(Path(path).read_text())


def save(name, value):
    with (OUT / name).open('x') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def main():
    data = load(OUT / 'data_audit.json')
    protected = load(OUT / 'protected_inputs_before.json')
    assert all(sha(path) == value for path, value in protected.items())
    boundpath = CASE / 'evidence/S0_launch_release_A1_20261102_01.json'
    bound = load(boundpath)
    criteria = ['MASS_CAPTURE_INTEGRITY', 'SAME_INPUT_REPLAY', 'CORRECTED_LEDGER_UNCHANGED',
                'PHYSICAL_OUTPUT_GUARD', 'URV_RESULT_PASS', 'RESULT_PASS']
    summaries = {}
    numerical = []
    for direction in ('P', 'T'):
        rid = data['directions'][direction]['run_id']
        audit = data['directions'][direction]
        original = load(OUT / f'recheck_{direction}/original_urv/acceptance.json')
        supplementary = load(OUT / f'recheck_{direction}/mass_repair_review.json')
        execution = load(OUT / f'checker_{direction}_execution.json')
        fields = load(OUT / f'recheck_{direction}/original_urv/fields.json')
        assert execution['independent_checker_exit_code'] == 0
        assert original['NUMERICAL_GATE'] == 'PASS' and original['geometry_PASS']
        assert all(supplementary[key] is True for key in criteria)
        assert supplementary == load(CASE / 'analysis_results' / rid / 'mass_repair_review.json')
        assert original == load(CASE / 'analysis_results' / rid / 'original_urv/acceptance.json')
        assert fields['PASS'] and fields['actual_reader'] and len(fields['frames']) == 10
        assert len(supplementary['replays']) == audit['capture_records']
        summaries[direction] = dict(run_id=rid, URV_NUMERICAL_GATE='PASS', geometry_PASS=True,
            URV_RESULT_PASS=True, RESULT_PASS=True, LEGACY_EXACT_REGRESSION=True,
            **{key:supplementary[key] for key in criteria if key not in ('URV_RESULT_PASS','RESULT_PASS')},
            SOURCE_REVISION_AUDIT='PASS_WITHIN_FROZEN_A1_SCOPE',
            S0_REVISION_DISPOSITION='DIRECTION_ACCEPTED',
            steps=audit['steps_completed'], diagnostic_rows=audit['diagnostic_rows'],
            K_m3_independent=original['scalar']['K_m3'], K_m3_native=audit['gates']['Keff_m3'],
            K_relative_change=original['regression']['relative_K_change'],
            native_exit=audit['native_exit_code'], independent_checker_exit=0,
            captures=audit['capture_records'], independently_reread_frames=10,
            raw_physical_files_exact=audit['physical_output_files_exact'],
            HISTORICAL_EXCLUSIVE_ATTRIBUTION='NOT_ESTABLISHED')
        gates = audit['gates']
        for key, op, limit in [
            ('max_mass_abs_relative','<',1e-10),('max_mass_ledger_agreement','<=',1e-13),
            ('max_density_deviation','<=',1e-6),('max_Mach','<',.05),
            ('section_relative_difference','<=',1e-5),('window_main_rel_std','<=',1e-6),
            ('window_main_rel_span','<=',5e-6),('window_cross_abs_max','<=',1e-12)]:
            value = gates[key]
            passed = value < limit if op == '<' else value <= limit
            assert passed
            numerical.append(dict(direction=direction,metric=key,value=value,operator=op,limit=limit,PASS=passed))
        for key, value, limit in [('Re_H',original['scalar']['Re_H'],.01),
                                  ('K_relative_change',original['regression']['relative_K_change'],1e-4)]:
            assert value <= limit
            numerical.append(dict(direction=direction,metric=key,value=value,operator='<=',limit=limit,PASS=True))
    with (OUT / 'numerical_gates.csv').open('x', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(numerical[0])); writer.writeheader(); writer.writerows(numerical)
    disposition = dict(review_id='URV-A1-S0-RESULTS-20261102', reviewed_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        protocol_id='URV-v1', addenda=['URV-MRP-v1','URV-MRP-v1-A1'], stage='S0_REGRESSION',
        release_sha256=sha(boundpath), S0_RESULT_PASS=True, S0_REVISION_DISPOSITION='ACCEPTED_NEW_A1_PAIR',
        repair_regression_blocker_resolved=True, directions=summaries,
        protected_original_file_count=len(protected), all_original_files_unchanged=True,
        bound_input_count=len(bound['inputs_sha256']), native_solver_invocations_this_task=0,
        native_builds_this_task=0, frozen_offline_checker_invocations=2,
        actual_saved_frames_read_this_review=20, density_records_replayed=212,
        density_binary64_values_replayed=12211200, rho_payload_bytes=97689600,
        T_difference_points_replayed=190, historical_differing_entries_reproduced=380,
        T_new_vs_old_legacy_differences=0, physical_files_byte_identical_per_direction=27,
        old_v12_T_FAILURE_preserved=True, old_failed_MRP_static_candidate_preserved=True,
        HISTORICAL_EXCLUSIVE_ATTRIBUTION='NOT_ESTABLISHED', reference_qualified=False,
        strict_error_bound_established=False, submission_ready=False,
        MODEL_COMPARISON='NOT_EVALUATED', physical_validation='NOT_EVALUATED',
        S1_authorized=False, S1_started=False, automatic_retry=False,
        new_instruction_or_evidence_contradiction=False, new_Astra_ruling_invoked=False,
        independent_human_scientific_signoff=False)
    save('disposition.json', disposition)
    P = data['directions']['P']; T = data['directions']['T']
    report = f'''# A1 两条 S0 完整结果复核：新修复版本验收通过

日期：2026-11-02。结论：按原 URV-v1、URV-MRP-v1 与已采用 A1 范围，两条新身份全部通过原验收、旧轨迹精确回归和密度补证。S0_REVISION_DISPOSITION=ACCEPTED_NEW_A1_PAIR，解除本次观察量修复回归阻塞。旧 v1.2 横槽失败与上一 MRP 静态失败永久保留；没有改原门槛或自动进入 S1。本记录为用户自有项目的 AI 辅助数值验收，不是独立人工科学终审、参考资格或模型预测验证。

## 1. 身份、授权和原始证据

P：URV_S0_P_A1_20261102_01，沿槽+y；T：URV_S0_T_A1_20261102_01，横槽+x。实际原始目录为 CASE/unseen_v2_reference_S0_mrp_v1_a1/runs/<run_id>/steady。正式合同 S0_launch_release_A1_20261102_01.json 的 SHA 为 {sha(boundpath)}，1548项输入、编译／依赖／源／库／原规则及新增授权绑定全部相符。实际 A1 ELF 为 c1fc2a1eeacced8f11a9bb045c25d70936b7be03fe5495a0b8f51789bd8fe8af，OpenLB 标识882924a9cfc8，D3Q19 ForcedBGK、单MPI／单线程、CPU_SISD；编译器13.3.0的既有真实构建记录受封存保护，本轮没有重编译。

两条 completion 的输入前后字典均等于合同，原生独立退出0、未超时、捕获最终化无错。真实原生墙钟P {P['native_wall_seconds']:.3f}s、T {T['native_wall_seconds']:.3f}s。所有 completion 绑定原始文件逐项SHA通过，实际文件闭包分别为P {P['actual_raw_files']}项、T {T['actual_raw_files']}项（包含各自completion）；没有以不存在的旁文件补证。原自动检查的两方向通过回执及S0_completed.json均存在，tmux已结束。

本轮在全新recheck_P／recheck_T中重新运行原封存check_mass_repair.py：它重新调用未改的原URV验收和独立VTK读回，再对完整密度做离线重放；两条独立检查退出均0。新验收JSON与原自动检查JSON完整相等，不仅比较PASS位。本轮没有调用求解器、capture最终化器或覆盖原始/自动检查输出。{len(protected)}项受保护既有文件前后相符，旧结果、失败和源码保持。

## 2. 固定问题和完整轨迹

h75/d100/w120/P=Ly240/dx5nm、rho1000kg/m³、nu1e-6m²/s、tau1、a1e5m/s²、平均H125nm；边界仍xy周期、真实沟槽Bouzidi静止壁面。J为速度体积分除以平面面积（m²/s），K=nu J/a（m³），U=J/H。原1013步统计窗、58800步上限和首个合格窗即停逻辑保持，没有强迫对齐步数或补跑。

| 项目 | P沿槽 | T横槽 |
|---|---:|---:|
| 真实推进步数 | 4342 | 2953 |
| 全轨迹诊断行数（含0步） | 4343 | 2954 |
| 原20列与旧D4 | 全部精确相同 | 全部精确相同 |
| 原5个修正账本列与v1.2 | 全部精确相同 | 全部精确相同 |
| NUMERICAL_GATE | PASS | PASS |
| geometry_PASS | true | true |
| 原URV_RESULT_PASS | true | true |
| 专项RESULT_PASS | true | true |
| 独立复算K（m³） | {summaries['P']['K_m3_independent']:.16g} | {summaries['T']['K_m3_independent']:.16g} |
| 独立复算K相对旧值变化 | {summaries['P']['K_relative_change']:.16g} | 0 |

原20列按原解析器读为浮点后逐元素精确比较，无新增容差；两方向合计145940个旧列值相同。5个修正账本列合计36485个值相同。原生P Keff={P['gates']['Keff_m3']:.17g}m³，独立公式复算尾位相差1ULP；与旧轨迹无差异，仍采用原K变化≤1e-4规则，未把CSV文本逐字符相同混作原要求。新旧D4／v1.2数据比对明细见data_audit.json及新regression_comparison.json。

## 3. 原数值、几何及保存场门槛

| 指标 | P | T | 原要求 |
|---|---:|---:|---|
| 补偿质量最大相对变化 | {P['gates']['max_mass_abs_relative']:.8g} | {T['gates']['max_mass_abs_relative']:.8g} | <1e-10 |
| 两修正账本最大差 | {P['gates']['max_mass_ledger_agreement']:.8g} | {T['gates']['max_mass_ledger_agreement']:.8g} | ≤1e-13 |
| 最大密度偏离 | {P['gates']['max_density_deviation']:.8g} | {T['gates']['max_density_deviation']:.8g} | ≤1e-6 |
| 最大Mach | {P['gates']['max_Mach']:.8g} | {T['gates']['max_Mach']:.8g} | <0.05 |
| Re_H（独立复算） | 2.89997153e-5 | 1.55304647e-5 | ≤0.01 |
| 末窗相对标准差 | {P['gates']['window_main_rel_std']:.8g} | {T['gates']['window_main_rel_std']:.8g} | ≤1e-6 |
| 末窗相对跨度 | {P['gates']['window_main_rel_span']:.8g} | {T['gates']['window_main_rel_span']:.8g} | ≤5e-6 |
| 横向通量绝对最大值（m²/s） | {P['gates']['window_cross_abs_max']:.8g} | {T['gates']['window_cross_abs_max']:.8g} | ≤1e-12 |
| 末态截面相对差 | {P['gates']['section_relative_difference']:.8g} | {T['gates']['section_relative_difference']:.8g} | ≤1e-5 |

旧质量最大相对变化P0、T8.934175019802938e-13，仍作为旧统计列报告，正式质量门仍使用补偿账本。所有数据有限、主通量正、材料不变，原收敛时间与所有完整统计窗由未改检查器重算。

两方向均57600核心流体节点，candidate=valid=installed32448，fallback=unresolved=0；独立q范围0.5到0.5000000000000018，满足0.5±1e-10；体积7.1999999999982183e-21m³在原1e-10相对门内。密度映射有序为cuboid/x/y/z、无overlap。各10个保存场实际经pvpython/VTK读取，共20帧，压力／速度／耗散／材料和诊断接口通过。每方向27个身份无关物理输出与v1.2逐字节相同，其中21个VTK容器／载荷文件加6个剖面／切片／帧计划文件。无需元数据例外或放宽数值比较。

## 4. 密度采集和横槽190点／380项重放

P 11份=独立initial_reference一次＋原10个诊断时点；T 201份=独立initial_reference一次＋190个原差异时点＋10个无差异对照。212份均严格57600个little-endian binary64、460800bytes，纯rho总97689600bytes，共12211200个实际密度值。映射、每份SHA、索引、原生ELF、原常量、phase和时间位模式均通过；原始索引与最终索引及completion相互绑定。每方向真正初态与diagnostic step0是两份独立记录，内容精确相同；未混用分母或由VTK反推密度。

所有记录环境保持fe_round=0、MXCSR控制8064(0x1f80)、double8bytes、IEC559和CPU FMA=true；rho_phys位模式408f400000000000、dx位模式3e35798ee2308c3a；volume位模式始终3bc10022090d20c1。原A1体积路径审计PASS仍限于冻结范围，不扩为全程序机器形式等价。

对每份同一次measure捕获的实际密度，独立Python按原顺序从+0重放：前三次乘法各binary64舍入，最后用math.fma融合；另用最后乘与加分开舍入重放v1.2。融合质量／补偿质量／密度差与本次原生记录位模式逐项一致。T全部190点的融合结果对应旧D4，分开结果对应失败v1.2；质量与质量误差共380个旧差异逐项重现，连有符号差值也与封存差异表一致。10个无差异对照点以及P10点也通过。FMA精确有理数构造例的算术校验通过，构造例不是历史输入。

首次差异step11：融合质量7.199999999999219e-18kg，分开路径约7.199999999999222e-18kg，后者减前者3.0814879110195774e-33kg。最大质量差step1141：融合7.199999999999966e-18kg、分开7.199999999999892e-18kg，有符号差-7.395570986446986e-32kg；质量相对误差差-1.0271626370072865e-14。原差异点范围11至2414。A1全轨迹相对旧D4的mass和mass_error差异均为0。

逐时点见T_same_density_replay_190.csv，逐原差异条目见T_380_entry_reconstruction.csv，例子见T_worked_examples.json。空间累计前缀的ULP差异另外保存在重放JSON中，不把空间累计数量当时间差异数，也不把小尾差当物理质量损失。

## 5. 裁定与边界

本次允许结论：在新A1运行实际捕获的密度输入上，两运算路径逐点重现既有差异，支持该舍入机制的充分解释；新版本两方向原精确回归、补偿守卫、物理输出与完整补证均通过，可解除本次统计修复回归阻塞。SOURCE_REVISION_AUDIT在既定范围PASS、LEGACY_EXACT_REGRESSION=true、MASS_CAPTURE_INTEGRITY=true、SAME_INPUT_REPLAY=true、CORRECTED_LEDGER_UNCHANGED=true、PHYSICAL_OUTPUT_GUARD=true；详见disposition.json。

历史唯一归因仍NOT_ESTABLISHED：旧运行190点的逐格密度未保存，新运行不能找回它们。旧v1.2的T RESULT_PASS=false／exit2、380项差异及前个MRP静态FAIL均保持。原生result.txt中的RESULT_PASS=false是保留的原生汇总字段，独立URV和MRP回执承担本次结果认证；不改原始false，也不混用其含义。

S0通过仅覆盖h75统计移植与A1修复。reference_qualified=false、strict_error_bound_established=false、MODEL_COMPARISON和physical_validation=NOT_EVALUATED、submission_ready=false不变，不能据此证明V2新条件预测更准或挤压压力／阻力应用已闭环。完整未见条件参考仍需原URV路线中的光滑基准、网格／驱动力检查及冻结模型比较。S1未授权、未启动；本轮不生成下一阶段运行包或命令，不自动重跑。

本轮使用scientific-writing组织证据；技能来源已核公开当前v2：Kassis, T., Agarwal, V., He, Y., Patel, D., & Brueckner, A. M. (2026), Scientific Agent Skills: A Library of Procedural Knowledge for Research Agents, https://doi.org/10.48550/arXiv.2609.00065。该引用只说明工作辅助，不是数值证据。未使用第三方期刊保密审稿材料，未外发项目内容、提交或推送。没有新的指令或证据矛盾，未新增Astra裁定。
'''
    with (OUT / 'REPORT.md').open('x') as stream:
        stream.write(report)
    section = '''## A1新版本两方向S0完整验收通过，修复回归阻塞已解除；S1未启动（2026-11-02）

- 用户本轮授权按原URV-v1／MRP／A1分析两条已有结果，不重跑／进入S1。两条运行与自动检查均结束，S0_completed.json存在；本轮在新目录重新执行未改check_mass_repair.py／原URV及实际VTK读回，不执行求解器。当前入口docs/reports/URV_A1_S0_results_review_20261102/REPORT.md、disposition.json、verification.json、recheck_P/T/、data_audit.json、T_same_density_replay_190.csv与T_380_entry_reconstruction.csv。
- 新身份URV_S0_P_A1_20261102_01（沿槽+y）、URV_S0_T_A1_20261102_01（横槽+x）分别4342／2953步、4343／2954行，原生及本轮独立检查均退出0。NUMERICAL_GATE=PASS、geometry_PASS=true、URV_RESULT_PASS=true，MRP各分项及RESULT_PASS=true；新独立JSON与自动回执完整相等。S0_REVISION_DISPOSITION=ACCEPTED_NEW_A1_PAIR，本次观察量修复回归阻塞解除；这是新版本限定数值验收，不是人工科学签字或参考／预测放行。
- 原20列全部完整精确回归旧D4、零新增容差；原5个修正账本列全轨迹精确对应v1.2。独立K P9.834076003216203e-23、T4.449022023188299e-23m³；相对旧值变化P1.1102230246251565e-16、T0，均在原≤1e-4内。P原生K尾位9.834076003216204e-23保留，不混作诊断轨迹差异。补偿质量最大相对变化P6.419766481290786e-16、T1.069961080215131e-15；全部原质量／密度／Mach／Re／统计窗／截面／几何门通过。
- P11份、T201份真实密度捕获全部完整，212×57600个binary64，rho97689600bytes。phase／初态分母／映射／时间／常量／FP环境／原生ELF／raw及最终索引SHA和completion闭包通过。212份独立同输入重放与本次原生记录位模式一致；T190差异点双路径逐项重现旧D4与失败v1.2的质量／误差共380项，最大mass差7.395570986446986e-32kg、mass_error差1.0271626370072865e-14，最大step1141。A1相对旧D4的差异0；T10个无差异对照与P10点通过。仅支持舍入机制充分解释，历史逐格密度相同仍未建立。
- 20保存帧经pvpython实际重新读取，两方向各27份物理输出与v1.2逐字节相同（21VTK＋6表），补偿和物理输出未改。57600节点、32448安装链、q0.5±1e-10、fallback/unresolved0。正式合同SHA cf7f1aaccf22b8d47b0c81147b9f9dcb22d07615f45664b09c9f7d1347826148与1548项输入保持；A1 ELF c1fc2a1eeacced8f11a9bb045c25d70936b7be03fe5495a0b8f51789bd8fe8af，OpenLB882924a9cfc8。2362项既有保护文件本轮前后不变，无源码／检查器／阈值／封存或原始结果修改，无构建或求解器调用。
- 旧v1.2 P接受／T拒绝、380差异／exit2及前个MRP静态FAIL均保留；原生result.txt的RESULT_PASS=false不改，独立回执按原职责认证。HISTORICAL_EXCLUSIVE_ATTRIBUTION=NOT_ESTABLISHED；reference_qualified=false、strict_error_bound_established=false、submission_ready=false，MODEL_COMPARISON/physical_validation=NOT_EVALUATED。旧细T、C/h75、V2/G4、D4预测HOLD、旧N8 D4_N8_diag_v3_1_20261026_v1、GDI01及外部声明范围不变；F04范围外，不把新S0接受写成论文闭环。
- 当前任务完成，S0无须重跑。下一具体动作可在另定范围下核对S1光滑基准h30/d0、dx1.25nm沿／横槽的运行前材料与原合同兼容性；本轮没有实现下一阶段／合同或命令，S1未授权／未启动。常规准备和完整验收GPT-6.1 Sol｜High；新指令／证据矛盾由指定GPT-6 Astra｜High裁定。本轮无新矛盾／新Astra调用，没有提交推送或项目资料外发。

'''
    for name in ('SIM240_AI_CONTEXT.md', 'AI_HANDOFF_20261015.md'):
        old = (OUT / ('before_' + name)).read_text()
        start = old.index('## '); end = old.index('\n## ', start + 3)
        new = old[:start] + section + old[end + 1:]
        assert new.split('\n## ', 2)[2] == old.split('\n## ', 2)[2]
        (ROOT / 'docs/reports' / name).write_text(new)
        with (OUT / (name + '.diff')).open('x') as stream:
            stream.write(''.join(difflib.unified_diff(old.splitlines(True), new.splitlines(True),
                fromfile='before/' + name, tofile='after/' + name)))
    assert all(sha(path) == value for path, value in protected.items())
    save('verification.json', dict(disposition, all_original_files_unchanged=True,
        shared_states_updated=True, later_historical_state_sections_preserved=True,
        acceptance_thresholds_unchanged=True, native_sources_unchanged=True,
        all_original_auto_acceptances_unchanged=True, complete_replay_matches_auto_receipts=True))
    sources = [boundpath, CASE / 'evidence/build_environment.json',
        CHECKER / 'common/acceptance_spec.json', CHECKER / 'analysis/check_results.py',
        CHECKER / 'analysis/check_mass_repair.py', CHECKER / 'analysis/mass_capture.py',
        CHECKER / 'revision/revision_anchor.json', CHECKER / 'revision/density_capture_schedule.json',
        ROOT / 'docs/reports/URV_S0_mass_repair_protocol_20261101/PROTOCOL.md',
        ROOT / 'docs/reports/URV_S0_results_review_20261101/legacy_differences_T.csv']
    save('source_manifest.json', dict(verified_by='AI-assisted actual byte/provenance/full trajectory/offline replay/VTK verification',
        human_verifier=None, sources={str(path):sha(path) for path in sources}))
    files = {str(path.relative_to(ROOT)):sha(path) for path in OUT.rglob('*') if path.is_file()}
    for name in ('SIM240_AI_CONTEXT.md','AI_HANDOFF_20261015.md'):
        path = ROOT / 'docs/reports' / name; files[str(path.relative_to(ROOT))] = sha(path)
    save('document_manifest.json', files)
    print(json.dumps(dict(S0_RESULT_PASS=True, protected=len(protected), original_input_count=1548,
                          replayed_records=212, actual_saved_frames_read=20,
                          native_solver_calls=0, S1_started=False)))


if __name__ == '__main__':
    main()

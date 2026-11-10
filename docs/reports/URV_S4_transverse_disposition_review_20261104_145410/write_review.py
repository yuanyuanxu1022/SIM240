"""Write an internal disposition review; all execution permissions stay closed."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import hashlib,json

ROOT=Path('/home/dell/yuanyuanxu/SIM240');OUT=Path(__file__).resolve().parent
CASE=ROOT/'CASE/unseen_v2_reference_S4_reuse_v1'
OLD=ROOT/'docs/reports/URV_S4_completed_review_20261104_143205'
load=lambda p:json.loads(Path(p).read_text())
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(name,v):
    with (OUT/name).open('x') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
a=load(OUT/'existing_evidence_audit_v1_1.json');g=a['grid'];v=a['volume_static_path'][-1]
geo=load(OUT/'candidate_geometry_static.json')['geometry'];now=datetime.now(ZoneInfo('Asia/Shanghai')).isoformat()
protected=load(OUT/'protected_before_v1_1.json');assert all(sha(p)==h for p,h in protected.items())
release=CASE/'evidence/S4_formal_launch_release_v1_20261104_01.json';b=load(release)
source_paths=[release,OLD/'REPORT.md',OLD/'independent_review.json',OLD/'independent_grid_report.json',
    ROOT/'docs/reports/URV_S4_formal_scope_resource_review_20261104_090724/PROTOCOL.md',
    ROOT/'CASE/unseen_v2_reference_checker_S4_reuse_v1/common/acceptance_spec.json',
    ROOT/'CASE/unseen_v2_reference_checker_S4_reuse_v1/analysis/evidence.py',
    ROOT/'CASE/unseen_v2_reference_checker_S4_reuse_v1/analysis/stage_s4.py',
    ROOT/'CASE/unseen_v2_reference_checker_S4_reuse_v1/analysis/s4_grid.py',
    CASE/'scripts/run_S4.py',ROOT/'CASE/unseen_v2_reference_S1_a1_v1/src/urv_reference.cpp']
save('reviewed_sources.json',dict(sources=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p),
    verification='AI_FILE_AND_ARITHMETIC_CHECKED_NOT_HUMAN_FINAL_REVIEW') for p in source_paths],
    protected_snapshot='protected_before_v1_1.json',read_only_CASE=True))
scope=dict(protocol_id='S4-TDR-v1',kind='DISPOSITION_SCOPE_REVIEW_NOT_EXECUTION_AUTHORITY',
    scope_review_completed=True,original_S4_stage_accepted=False,original_failure_preserved=True,
    recommendation='ONE_NEW_TRANSVERSE_DX0P625_SPATIAL_SUPPLEMENT_AFTER_FEASIBILITY_AND_NEW_AUTHORIZATION',
    candidate=dict(direction='T',dx_nm=.625,h_nm=30,d_nm=80,w_nm=120,period_nm=240,Ly_nm=240,
        acceleration_m_s2=100000,nu_m2_s=1e-6,H_nm=70,
        native_binary_reuse='STATICALLY_COMPATIBLE_NOT_NATIVE_AUDITED',native_binary_sha256=b['provenance']['native_binary_sha256'] if 'native_binary_sha256' in b['provenance'] else sha(Path(b['provenance']['native_binary'])),
        fluid_nodes=v['core_fluid_nodes'],window_steps=v['window_steps'],maximum_steps=v['maximum_steps'],
        dt_s=v['dt_s'],volume_rounding_relative_estimate=v['relative_to_exact_nominal'],
        proposed_reference_grids_nm=[2.5,1.25,.625],original_grids_nm=[5,2.5,1.25]),
    minimum_new_formal_runs_if_adopted=1,existing_reference_runs=[r['run_id'] for r in a['transverse_records'][1:]],
    proposed_future_native_zero_calls=3,proposed_future_initial_field_reads=1,
    native_zero_audit_authorized=False,initial_field_readback_authorized=False,
    implementation_authorized=False,build_authorized=False,performance_time_stepping_authorized=False,
    formal_simulation_authorized=False,automatic_retry_authorized=False,automatic_extension_authorized=False,
    S5_authorized=False,run_ids_created=[],approved_run_ids=[],launch_command_created=False,
    required_before_formal=['isolation_and_provenance_adapter','software_and_static_checks','separately_authorized_3_plus_1_zero_audit',
        'candidate_resource_evidence_and_single_limited_PERF_if_route_retained','explicit_formal_budget_and_user_authority'],
    formal_solver_wall_cap_seconds=None,formal_checker_cap_seconds=None,
    reference_qualified=False,MODEL_COMPARISON='NOT_EVALUATED',physical_validation='NOT_EVALUATED',submission_ready=False)
save('scope_decision.json',scope)

table='\n'.join(f"|{r['dx_nm']:g}|{r['K_end_m3']:.12e}|{r['terminal_span']*1e6:.6f}|{r['final_vs_last_window_mean']*1e6:.6f}|{r['slice_over_volume_K_minus_one']:.4e}|" for r in a['transverse_records'])
report=f'''# S4 横槽网格失败的处置审查：S4-TDR-v1

日期：{now}。这是用户请求的只读范围审查与最小补证建议，属于AI辅助内部工作报告；不是正式执行协议或人工科学终审。

**审定意见：保留原S4横槽网格FAIL。现有证据不足以将其改判；如继续争取薄间隙横槽参考资格，最小新增空间证据候选是一条dx=0.625nm的横槽T，并引用原2.5/1.25nm两条作前置基准。优先审同一ELF复用及资源可行性，暂不实施/构建/原生审计/性能推进/正式计算。** 这项新增证据须在单独的前瞻性补充协议中评价，不回写原5/2.5/1.25nm三格的失败。

## 1. 本轮核了什么

已读项目状态/最新交接、历史路线说明、S4-MIP/S4-FRD范围及冻结门槛、既有六条完整独立验收、原生配置/源码、阶段身份/检查器/控制器。复核原正式release SHA `{sha(release)}` 的3284项输入，连同原始结果与上轮验收报告共{a['protected_files_unchanged']}份受保护文件前后内容一致；原输入/输出/报告未修改。本轮未重跑科学检查器或保存场读取器，未查实时进程；只用已结束证据做参数、CSV及二进制64位算术核对。

## 2. 现有证据足以排除哪些简单解释

原六配置在去除身份/目录、方向与dx后物理输入相同：h30/d80/w120/P=Ly240nm、平均H70nm、a100000m/s²、nu1e-6m²/s、rho1000kg/m³、tau1，固定全充液、x/y周期和静止无滑移壁。J为按平面面积归一的通量，K=nuJ/a（m³），平均速度U=J/H，阻力R=mu/K。横槽始终T/+x。各方向并未混用，h与H未互换。

三档独立枚举几何/材料/壁面链数与已有原生审计一致；节点体积和q在原容差内。三份双精度切片重新积分所得K与全域K最大相对差{max(abs(r['slice_over_volume_K_minus_one']) for r in a['transverse_records']):.5e}，远小于本次网格变化，不支持“导度单位/取向/平均归一换错”这一简单解释。核对相容不证明所有边界离散实现都无误。

|横槽dx (nm)|末态K (m³)|末窗跨度 (ppm)|末态相对末窗均值 (ppm)|切片K／全域K−1|
|---|---:|---:|---:|---:|
{table}

原2.5/1.25nm末态差为{g['mid_fine_relative_change']*100:.9f}%；用末窗均值作**诊断性对照**为{g['mid_fine_last_window_mean_change']*100:.9f}%，仍>1%。因此不能靠改取末窗平均值消除此次失败；原验收仍按冻结末态K，没有改用均值。原细格K若单独向上变化且中格不动，至少需上升{g['fine_relative_increase_needed_if_mid_fixed']*100:.6f}%才够到1%门；这是阈值算术，不是续算预期，也不是允许续算的证据。

各条最后一窗已通过原时间稳态门；但末窗小幅波动并不提供到无限时间稳态的严格偏差上界。三档停止的物理时刻不同，不能据此证明全部网格差仅由空间误差造成。本轮不做指数尾拟合或角点奇异性归因；若后续出现时间证据矛盾，应先隔离审查时间收敛，而不是盲目加密。

## 3. 当前失败的准确含义

T三档K随加密连续下降，观测阶p={g['observed_order']:.9f}正且有限；中细变化{g['mid_fine_relative_change']*100:.9f}%>1%，细格GCI估计{g['GCI_fine']*100:.9f}%≤1%。冻结协议两项均须通过，故原横槽和S4阶段FAIL保持。原生/单条独立结果通过、沿槽网格通过不改变此结论。

观测到的是横槽对网格仍有超出协议的敏感性。具体是壁面/角点离散、时间偏差或其他数值环节，现有证据不足以唯一判定。没有证据支持改公式、改物理参数、修求解器或放宽1%门槛。

## 4. 最小补证为什么是一条新的横槽

若用户选择继续补空间收敛证据，推荐只新增同几何/同驱动T的0.625nm网格。它延续r=2，和已接受2.5/1.25nm构成新的嵌套三档，最少只需一个新正式求解点。沿槽已有通过的网格证据，本轮没有提出重算P或重算六条的必要依据。

原5/2.5/1.25nm全部留在报告，原中细1.3284%失败永久保留；新2.5/1.25/0.625nm分支必须事先冻结、无论通过或失败均报告。即使新分支通过，也只能说明新的网格补证判据通过，不能伪称原S4协议追溯通过，不能自动更新原24条聚合、参考资格或进入S5。外推K、旧GCI、同公式OpenFOAM结果都不能替代这个缺失的实际新网格结果。新补证方案是看到失败后设计，应如实标为前瞻性追加数值验证，不冒称最初预注册矩阵。

如不接受追加资源，可选择保持薄间隙横槽参考未合格，在之后另定论文/资格范围时透明报告这一限制。该选择不会消除原24条聚合缺口，也不授权跳过S5、自动做局部V2评分或宣称全部闭环。本轮不替用户改研究目标。

## 5. 同一二进制与合同兼容性

原生解析器按运行输入计算网格尺寸，0.625nm满足长度整数对齐，输入模式和物理核不需因这份候选改写；S1 ELF静态可复用，SHA `{scope['candidate']['native_binary_sha256']}`。目前无理由改C++/重新构建。但此处只是源码/数值兼容性，不是0.625nm原生接入已验证。

阻断在现有阶段控制与合同：stage_s4固定六个身份，原case_matrix只有原矩阵，s4_grid固定5/2.5/1.25nm，run_S4.wall_cap也仅收三档且输出路径已用。旧release仅授权原六条，禁止自动续算/扩展。**不能直接把dx改为0.625、把旧命令再跑一次，或给原包加一条来绕过冻结。** 若方案采用，需新隔离阶段身份/元数据和来源适配，单条新输出目录，引用两份旧completion/acceptance与其原合同SHA；原科学阈值/模型/边界/平均定义不变，新增元数据与适配差异须单列复核。

A1体积逐节点舍入路径做了纯算术预审：Python/NumPy顺序binary64累加在原三档均精确重现原生结果。对0.625nm预测体积相对名义值约{v['relative_to_exact_nominal']:.6e}，在1e-10内，目前不支持为此修复观察量。候选仍需原生零步实际验证，纯算术不是geometry_PASS或原生输出证据。

## 6. 候选规模与必须补的资源证据

候选流体节点{v['core_fluid_nodes']:,}，是旧细格的8倍；纯几何预计壁面链{geo['candidate_links']:,}，dt={v['dt_s']:.16e}s，原0.75统计窗10368步、原最大时间对应1486848步。按解析射线静态枚举q范围为{geo['q_min']:.16g}–{geo['q_max']:.16g}（原1e-10容差内），不冒充实际安装审计。

仅按流体节点每点19个double值的一组分布量就需{v['one_population_set_fluid_only_bytes']/1024**3:.6f}GiB；它没有计入固体包络、重叠、其他数组、边界、缓存与读场内存，不能据此断言原8GiB进程地址空间上限一定足够，也未证明必须突破8GiB。当前机器资源/候选峰值/RSS和吞吐本轮未测，不据旧快照预留资源。

已有T1.25nm求解4326.036s/12537步。若每步成本随节点×8，且停止物理时刻相同使步数×4，条件算术为138433.155s≈38.4537h。**这不是测速、预计完成时间或预算保证。** 原S4的12h授权不能拿来自动扩展到38.5h或48h，也不能保证12h会完成。由此建议在正式求解前补候选自己的受限资源/吞吐证据。

## 7. 最小后续准备范围与分阶段停止

1. 采用范围后才可隔离准备：同一ELF复用证明、单配置阶段/来源/授权适配、两份旧基准引用、独立检查器入口、原科学门槛及新网格分支。先软件与静态核对，不为了“检查能否运行”擅自调用原生。
2. 另予明确原生许可后，最少一个配置describe/precheck/initialize共3次、初态保存场读回1次（3＋1）；新输出/新绑定。检查节点/材料/链/q/体积、初态/半步力、单位与读场闭合。此时推进0步，不能当稳态或性能证据。具体资源/各调用时间上限须在发执行合同前裁定；本轮未签发。
3. 若3＋1合格且继续保留此路线，建议另行冻结并授权一条T0.625的有限PERF：例如原生启动起最多1800s，或首次完整诊断step≥2048即停，以先到者为准；不重试、不转正式。这个上限只是待采用草案，不是当前许可。初始化计时/RSS、推进分段速度、输出/地址空间和停止清理证据都要保存；可能未覆盖10368完整窗，不能据此报稳态接受或保证后续时长。原8GiB限制若不够则停，不能静默提高。
4. 资源证据之后再审正式单条范围/地址空间/墙钟/检查时间/磁盘与用户授权。正式上限当前未定，不交启动命令；任何新资源决策独立记录，不覆盖旧S4绑定。若资源不足或时间风险不可接受，停在准备/资源审查层，不自动改网格/并行/物理问题。
5. 获准正式运行并完成后，按原单条门槛独立接受新点；按前瞻性新补充协议报告新旧两个三档分支。中细差与GCI仍各≤1%、r2/Fs1.25、同向非近零差/正有限p；任何失败保留，无自动再加第五格。严格误差界/实验验证仍不由此建立。后续参考资格恢复、原矩阵聚合/追加协议以及S5关系须另审，不自动推进。

## 8. 本轮交付与边界

本轮审查范围已完成，补证建议未由用户采用/实现，`implementation_authorized=false`、原生/读场/PERF/正式/重试/加时/S5权限均false；新run_id、执行合同、启动命令均未生成。旧S4_STAGE_ACCEPTED=false、reference_qualified=false、MODEL_COMPARISON/physical_validation未评价、submission_ready=false；F04 OPEN及全部历史FAIL/声明范围保持。

证据：existing_evidence_audit_v1_1.json是有效算术结果，candidate_geometry_static.json、scope_decision.json、reviewed_sources.json及protected_before_v1_1.json。首次报告脚本因NumPy布尔值JSON序列化失败，初稿与半份JSON保留；仅修正本报告序列化后重做纯读取/算术，未调用原生、科学检查器或读场器，无科学证据冲突。

使用[peer-review](/home/dell/.codex/skills/peer-review/SKILL.md)；工具出处Kassis等(2026)，[Scientific Agent Skills](https://arxiv.org/abs/2609.00065)，同日先前公开核对为v2，仅工作流出处，不作为CFD论据。作者仍需人工科学复核；本报告不是期刊决定。
'''
(OUT/'REPORT.md').write_text(report)
draft='''# S4-TDR-v1 最小追加准备草案（未采用／未实现／不授权执行）

审查结论与证据见REPORT.md；机器可读范围见scope_decision.json。

- 研究问题：同一h30/d80/w120/P240nm、T方向、a100000m/s²下，加至0.625nm后新的空间网格证据是否合格？
- 最少正式新增：仅1条T0.625nm；以原2.5/1.25nm的两份已接受结果作原合同引用。旧5/2.5/1.25nm失败原样保留。
- 同一ELF优先复用；不得改原C++、科学门槛、边界、质量路径/平均定义，不把候选冒充原24点之一。若发现确需修改，退回另定范围。
- 准备工作：新隔离阶段身份与来源绑定、旧基准只读引用、检查器/控制器适配、3＋1零步入口、资源预审材料；准备不等于原生许可。当前不创建任何CASE包或run_id。
- 后续3＋1、单条有限PERF、正式计算三种许可分别办理；软件检查允许范围亦须在采用准备范围后明确。当前全部关闭。
- 数值门槛与原URV完全保持；新网格分支仍r2/Fs1.25、中细差/GCI各≤1%、p正有限/差同号非近零。原网格失败不能被新分支覆盖。
- 原8GiB/12h不可自动挪用或提高；先取得新尺度原生接入及资源证据，再裁定正式预算。有限PERF示例1800s或首次完整诊断step≥2048，未采用。
- 停点：本轮仅报告与草案；采用后可另行限定隔离准备，仍不默认启动原生、PERF、正式或S5。最终参考资格/聚合如何纳入追加网格另审。
'''
(OUT/'MINIMUM_PREPARATION_DRAFT.md').write_text(draft)
section=f'''## S4横槽处置范围审查完成：推荐单条0.625nm候选，先接入/资源补证，全部执行关闭（{now}）

用户要求另行审定横槽网格未过的处置范围，先核已有证据和最小补证，不自动新算。本轮只读审查完成，入口{OUT.relative_to(ROOT)}/REPORT.md、MINIMUM_PREPARATION_DRAFT.md、scope_decision.json、existing_evidence_audit_v1_1.json。未实施CASE接入、未构建/原生/科学检查器/VTK/PERF/正式/重跑/加时/S5，无新run_id/执行合同/启动命令。

原S4已结束且六条独立接受的上轮证据保持：docs/reports/URV_S4_completed_review_20261104_143205/REPORT.md，正式release SHA{sha(release)}；3284输入及本轮含旧验收报告共{a['protected_files_unchanged']}受保护文件一致。T三档K=3.64797692375804e-24/3.517910669377557e-24/3.471791836744987e-24m³，末态中细差1.328387035%>1%；用末窗均值只作诊断差1.328375385%，仍失败。三格参数/几何/方向/切片积分一致，末窗约5ppm不等于无限时间偏差界；尚未唯一归因角点/壁面/时间或空间误差，不改公式/阈值。原T/S4网格FAIL、六条per-run PASS、P网格PASS分别保留。

最小建议（未采用/实现）：只增T0.625nm，引用原T2.5/1.25nm构成前瞻性新嵌套三档；原5/2.5/1.25失败永久保留，不追溯改判、不自动更新24点聚合/参考资格/S5。原生同一S1 ELF静态可复用，但现stage_s4/s4_grid/runner/矩阵/旧六条权限不接收新档，需新隔离身份/元数据/来源与检查接口；不改原包或挪用旧命令。新候选纯静态节点16515072、链1964544、dt6.510416666666667e-14s、window10368、cap1486848；A1体积舍入预估相对差1.58396e-11在1e-10内，原三档静态累加均精确重现原生，非新原生证据。

候选规模为旧细格8倍。仅流体节点一组19个double分布量2.33789GiB不是峰值/地址空间保证；旧T1.25耗时4326.036s，假设成本×8和同物理停止时刻步数×4才得38.4537h，非实测/预报。未测候选RSS/速度，不自动采用旧8GiB/12h或加时。采用准备范围后先软件静态；3＋1原生审计须另许可；合格后建议单条有限PERF（1800s或首次完整诊断step≥2048示例）另冻结授权，再据实另裁正式预算/权限。没有强行规定新正式时限或允许超8GiB。

S4-TDR-v1为已完成的处置范围审查，不是执行许可或已冻结补充资格协议；所有准备实施/原生/读场/PERF/正式/重试/加时/S5权限false。reference_qualified=false、MODEL_COMPARISON/physical_validation未评价、strict_error_bound/submission_ready=false、F04 OPEN、S0–S3接受及全部历史FAIL/MRP/A1/S2-LRP/被拒B/作者声明范围保持。报告helper NumPy bool JSON错误初稿/半份输出保留，已仅修报告序列化重算，不涉及科学矛盾或CFD重跑。

下一具体动作：用户采用最小草案后，另行限定隔离准备同一ELF接入、单配置阶段/旧基准引用/检查适配与3＋1审计入口；不自动原生审计、PERF或正式/S5。若用户不采用追加资源，保留薄间隙横槽参考未合格，另定科学表述范围，不改原矩阵。常规GPT-6.1 Sol｜High；新证据矛盾/疑难归因按用户偏好GPT-6 Astra｜High，未真实切换。

'''
changed=[]
for name in ['SIM240_AI_CONTEXT.md','AI_HANDOFF_20261015.md']:
    path=ROOT/'docs/reports'/name;before=path.read_text();(OUT/(name+'.before.txt')).write_text(before)
    start=before.index('\n## ')+1;end=before.find('\n## ',start+1)
    if end<0:end=len(before)
    after=before[:start]+section+before[end:].lstrip('\n')
    assert path.read_text()==before,'concurrent edit; stop'
    path.write_text(after);(OUT/(name+'.after.txt')).write_text(after);changed.append(str(path.relative_to(ROOT)))
assert all(sha(p)==h for p,h in protected.items())
save('final_verification.json',dict(scope_review_complete=True,protected_files_unchanged=len(protected),
    shared_state_updated=changed,CASE_files_modified=0,native_calls=0,builds=0,checker_calls=0,VTK_calls=0,
    PERF_advances=0,formal_runs=0,reruns=0,extensions=0,S5_started=False,original_S4_FAIL_preserved=True))
save('document_manifest.json',{str(p.relative_to(OUT)):sha(p) for p in OUT.rglob('*') if p.is_file() and p.name!='document_manifest.json'})
print(json.dumps(dict(report=str(OUT/'REPORT.md'),protected_unchanged=len(protected),shared_updated=changed,
    scope_review_completed=True,implementation_authorized=False,simulation_authorized=False),ensure_ascii=False,indent=2))

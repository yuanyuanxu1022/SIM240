#!/usr/bin/env python3
"""Maintain shared handoff and bind read-only review artifacts, never code/results."""
from pathlib import Path
import difflib
import hashlib
import json
import re

ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
OLD=ROOT/'CASE/unseen_v2_reference_v1'
NEW=ROOT/'CASE/unseen_v2_reference_checker_v1_1'

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for data in iter(lambda:f.read(1<<20),b''):h.update(data)
    return h.hexdigest()

def save(p,data):
    if p.exists():raise FileExistsError(p)
    p.write_text(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False)+'\n')

ENTRY='''## URV v1.1只读复核完成：两项残留待修、历史待确认、S0未启动（2026-11-01）

- 用户范围：只读复核v1.1及合同要求，继续核实外部数据历史；获得真实确认后再准备S0正式执行绑定，不自动启动。新入口`docs/reports/URV_checker_v1_1_readonly_review_20261101/REPORT.md`、findings.json、verification.json、history_status.json。审查编号URV-v1.1-READONLY-20261101非求解run_id；实际新正式run_id=[]，没有生效合同、启动命令或正式运行目录。
- 当前结论：原70项测试本轮复跑全部通过，原F02差异先保存逻辑及20列完整样例在本轮范围成立；额外隔离人工检查复现F01/F03各一残留，执行准备HOLD。没有撤销或覆盖旧70通过记录，也不将其当所有输入边界充分证明。AI自审非独立人工验收；本轮只读，没有修改v1.1、原求解器、协议、测试或门槛。
- R1(HIGH，F01残留)：contracts.py:16—26的release_inputs遇任一运行/基准声明缺字段即返回[]，丢失已知有效保护路径；公开入口在binding拒绝前创建输出。人工对照保留有效P基准，仅删另一声明output_directory，正常组无写入，缺字段组在人工基准内创建analysis_malformed/failure.json，两者均exit2。只在新人工目录，不触及真实结果。需在任何mkdir/save前对声明解析失败停止，不以空保护集合继续，并增加“有效基准+不完整其他声明”组合测试；本轮未修。
- R2(MEDIUM，F03残留)：contracts.py:79—81只过滤合并式-D/-U宏token；人工完整捕获命令保留-DURV_PREPARATION_ONLY=0，再加入分离式-D URV_PREPARATION_ONLY=1并同步人工哈希，binding仍返回成功。只证实文本解析遗漏，没有调用编译器或测真实最终宏值，没有生成错误正式程序。需统一解析合并/分离的-D/-U再按唯一明确0校验；本轮未修。测试中的CONFIRMED/授权为人工元数据，不是作者确认。
- 原v1.1主要来源角色/依赖/逐条身份检查及正常合同路径保护仍有证据；F02差异保存先于原K1e-4/旧轨迹停止条件已核，旧P4343行、T2954行及人工失败例的完整20列报表均在。原numerics与reader主体七函数源码逐字节一致。新URV完整稳态结果端到端验收仍NOT_EVALUATED。F04多合同汇总仍为既有后续OPEN事项，未纳入本轮修订或提前授权。
- 封存/保护：原准备seal e0eb9a54c1c1168d25483a085e70462d04cfa76aeb4922dddbea17b07b1811cb及1432输入、新检查器seal df3003c57560576548e9b0988507bc2f7a63982522988d5a284cc75fdd0f35ce及21输入均匹配；原830文件、v1.1与前轮报告/历史输入等2606既有文件前后保持。原URV_PREPARATION_ONLY=1不动。本轮native编译0、求解0、实际VTK数据读取0；现有reader测试只导入并拒绝非法输出，不读场。未拟合、提交推送或对外发送项目材料。
- 外部历史：已查原v1.1 common、原历史记录、最新状态，没有新真实确认；已单独询问作者是否有新结论及核查范围，最后已收到的明确答复仍“尚不能确认，需要核查”，状态PENDING_AUTHOR_CHECK，以history_status.json快照为准。不能从本地无匹配或测试字段推定其他机器/未归档/他人数据未使用。两个候选h60/d80、h30/d80,w120/P240nm未认定已确认未见。
- S0原两条h75草案维持未生效，正式程序/配置SHA与批准编号未形成；h75/d100/w120/P=Ly240、dx5nm、H125nm，P=+y/T=+x，窗1013/上限58800、K差≤1e-4及完整20共同列口径不变。本轮没有准备生效绑定；即使后续历史获确认，仍需收口R1/R2并核验后再准备真实构建、逐条配置编号目录及独立退出/资源/原始产物合同，不自动启动。
- 新正式NUMERICAL_GATE=NOT_EVALUATED、RESULT_PASS=false、geometry_PASS=null；reference_qualified=false、strict_error_bound_established=false、submission_ready=false，MODEL_COMPARISON/physical_validation=NOT_EVALUATED。旧细T FAIL、C/h75限定资格、V2/G4锁、D4预测HOLD、旧N8 D4_N8_diag_v3_1_20261026_v1及NOT_EVALUATED/false/null、GDI01既有接入结果均保持。
- 当前停点：只读复核完成，新增证据仅报告/人工反例/现有测试复跑与共享状态维护，未新增流场或物理验证。下一具体任务可另授权隔离小版本仅修R1/R2并增加对应反例，保留v1.1封存；作者继续核查外部历史，二者满足后再进入S0正式执行绑定准备。F04后续汇总前单独处理。常规修订/复核建议GPT-6.1 Sol｜High；疑难理论/多证据矛盾/最终公式冻结依原规则GPT-6 Astra｜High。

'''

def main():
    initial=json.loads((OUT/'protected_inputs_before.json').read_text())
    assert all(sha(p)==s for p,s in initial.items())
    verify=json.loads((OUT/'verification.json').read_text())
    assert verify['readonly_review_completed'] and verify['existing_tests_passed']
    original_history=ROOT/'docs/reports/URV_v1_readonly_review_S0_20261101/external_data_history.json'
    history=json.loads(original_history.read_text())
    assert history['literal_answer']=='尚不能确认，需要核查'
    save(OUT/'history_status.json',dict(record_date='2026-11-01',status='PENDING_AUTHOR_CHECK',
        latest_received_explicit_answer='尚不能确认，需要核查',latest_answer_source=str(original_history),
        latest_answer_source_sha256=sha(original_history),current_turn_question_asked=True,
        new_explicit_answer_received_as_of_this_snapshot=False,new_confirmation_found_in_checked_records=False,
        confirmation_not_inferred_from_silence=True,formal_binding_effective=False,
        checked_sources=[str(NEW/'common/data_history_status.json'),str(original_history),
                         str(ROOT/'docs/reports/SIM240_AI_CONTEXT.md')],
        unverified_scope='other machines, unarchived/private or third-party result history',
        no_machinewide_scan_or_external_contact=True))
    for name in ['SIM240_AI_CONTEXT.md','AI_HANDOFF_20261015.md']:
        path=ROOT/'docs/reports'/name;old=path.read_text()
        assert old==(OUT/'before'/name).read_text(), 'concurrent shared-state update'
        start=old.index('\n## ')+1;end=old.index('\n## ',start+1)+1
        new=old[:start]+ENTRY+old[end:];path.write_text(new)
        (OUT/(name+'.diff')).write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='before/'+name,tofile='after/'+name)))
        assert new[new.index('\n## ',new.index('\n## ')+1)+1:]==old[end:]
    links=0
    for target in re.findall(r'\]\(([^)]+)\)',(OUT/'REPORT.md').read_text()):
        if '://' in target:continue
        assert (OUT/target.split('#')[0]).exists(),target
        links+=1
    assert all(sha(p)==s for p,s in initial.items())
    assert not (OLD/'results').exists() and not (NEW/'results').exists()
    save(OUT/'final_verification.json',dict(readonly_review_delivery_PASS=True,
        formal_execution_readiness='HOLD',existing_tests_passed=70,residual_findings=['R1','R2'],
        frozen_inputs_unchanged=len(initial),source_changes=False,threshold_changes=False,
        local_links_checked=links,shared_context_and_handoff_updated=True,
        native_compiler_calls=0,solver_calls=0,S0_started=False,effective_S0_binding=False,
        external_history='PENDING_AUTHOR_CHECK',formal_NUMERICAL_GATE='NOT_EVALUATED',
        RESULT_PASS=False,geometry_PASS=None,reference_qualified=False,submission_ready=False))
    files={str(p.relative_to(ROOT)):sha(p) for p in OUT.rglob('*') if p.is_file() and p.name!='source_manifest.json'}
    for name in ['SIM240_AI_CONTEXT.md','AI_HANDOFF_20261015.md']:
        p=ROOT/'docs/reports'/name;files[str(p.relative_to(ROOT))]=sha(p)
    save(OUT/'source_manifest.json',dict(files=files))
    print(json.dumps(dict(readonly_review_delivery_PASS=True,formal_execution_readiness='HOLD',
        residual_findings=['R1','R2'],frozen_inputs_unchanged=len(initial),S0_started=False)))

if __name__=='__main__':main()

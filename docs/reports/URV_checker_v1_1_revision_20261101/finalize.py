#!/usr/bin/env python3
"""Seal checker-only preparation, update handoff, then verify frozen originals."""
from pathlib import Path
import difflib
import hashlib
import json
import re

ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
OLD=ROOT/'CASE/unseen_v2_reference_v1'
NEW=ROOT/'CASE/unseen_v2_reference_checker_v1_1'

def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()

def save(p,data):
    if p.exists():raise FileExistsError(p)
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False)+'\n')

ENTRY='''## URV检查器v1.1修订验证完成，外部历史待核查，S0未启动（2026-11-01）

- 用户范围：在隔离新版本最小修订F01—F03并验证，保留原准备封存；外部历史继续核查，S0保持未启动。新代码入口`CASE/unseen_v2_reference_checker_v1_1/README.md`；证据`docs/reports/URV_checker_v1_1_revision_20261101/REPORT.md`、verification.json、tests_final.log。修订编号URV-CHECKER-v1.1-20261101不是求解run_id；actual_formal_run_ids=[]，无启动命令或生效执行合同。
- F01已修：公开检查入口先规范化/核验输出，再独占创建新目录；raw自身/子目录/父目录、符号链接、既有目录、批次任一raw、合同声明的基准/输入与原/新CASE均受保护。非法目标只stderr/exit2不写文件；失败仅写入本次合法创建目录。独立reader入口同样在读场前保护。F02已修：来源通过后先保存regression_comparison.json，含K新旧/相对差及所有共同列差异/长度，再按原1e-4和旧轨迹一致要求判定；失败保留差异和失败回执，无成功acceptance、不加宽门槛。
- F03已修：新contracts.py强制URV-EXEC-1.1合同、native源/程序/构建配方/构建记录/编译器/.d依赖/链接和动态库、检查器与协议全覆盖；解析捕获.d/ldd的闭包并核哈希。物理源需匹配原准备锚点，准备构建和模糊宏定义拒绝。approved_runs强制run_id→case→配置路径/SHA→唯一目录，单阶段/原矩阵/时间帧计划对应；完成记录再核真实目录配置。未来合同格式见新版本EXECUTION_CONTRACT_REQUIREMENTS.md，本轮没有生成真实执行合同。
- 已验证：70Python测试通过=35原回归+35新增，0失败/错误；8个Python源在内存编译核语法，未生成CASE缓存。原diagnostics/check_slice/compare_legacy/aggregate及reader的payloads/leaves/audit逐字节一致，evidence.py与原common文件逐字节保留。质量/J/K/方向/平均/窗口/GCI/敏感性与全部物理门槛不变。原35通过、扩展69通过、补reader入口覆盖后70通过，日志保留。
- 可复查证据：旧h75 P4343行/T2954行20共同列自对照及明确人工改一项J后的20列失败报表已保存；只是既有控制/人工软件验证，不是新S0运行。前轮被原binding接受的缺项人工合同现用新版真实CLI拒绝exit2，无成功记录。测试中的授权/CONFIRMED和惰性程序/库只为人工验证，不是作者声明、真实构建或执行许可。新URV完整稳态输出端到端验收仍NOT_EVALUATED。
- 原包保护：原CASE830文件与1432项准备绑定不变；另1725项前轮审查/历史保护输入哈希一致。原准备封存e0eb9a54c1c1168d25483a085e70462d04cfa76aeb4922dddbea17b07b1811cb保留，原源码/二进制/URV_PREPARATION_ONLY=1未动；旧URV_ZERO_20261101_01的72次零步/24帧证据保留为历史。本轮native编译/求解0、实际VTK数据读取0，未拟合、提交推送或对外发送项目材料。新检查器有独立CHECKER_REVISION_PREPARATION_ONLY封存，不是执行release。
- F04仍OPEN_OUT_OF_SCOPE：24条汇总CLI仍共用一个合同SHA，不兼容各阶段独立封存；aggregate未改。未来多合同汇总前单独修订，不为此提前授权24条或回写旧completion。F01—F03的软件修订完成不等于S0执行准备齐备。
- 外部历史仍PENDING_AUTHOR_CHECK：作者最后答复“尚不能确认，需要核查”，源`docs/reports/URV_v1_readonly_review_S0_20261101/external_data_history.json`保持。两个候选h60/d80与h30/d80、w120/P240nm仍不能认定已确认未见。原S0草案仅未生效材料，正式程序/配置/合同SHA及批准编号仍未形成；S0 h75/d100/dx5的原窗口1013/上限58800、K差≤1e-4及20列比较口径保持。
- 当前新正式NUMERICAL_GATE=NOT_EVALUATED、RESULT_PASS=false、geometry_PASS=null；reference_qualified=false、strict_error_bound_established=false、submission_ready=false，MODEL_COMPARISON/physical_validation=NOT_EVALUATED。旧细T FAIL、C/h75限定离散资格、V2/G4锁、D4预测HOLD、旧N8 D4_N8_diag_v3_1_20261026_v1及NOT_EVALUATED/false/null、GDI01既有接入结果不变。
- 当前停点：本轮仅检查器修订与软件准备验证完成；新目录/本轮报告及当前状态/最新交接为改动范围，原准备包和旧审查结论不覆写。下一具体动作只读复核v1.1及来源合同要求，作者继续核实外部数据历史；获得真实确认后再另行准备S0正式构建、逐条配置编号目录、独立退出/资源/原始产物捕获与生效合同，保持不自动启动。F04后续汇总前单独处理。常规复核建议GPT-6.1 Sol｜High，疑难理论/多证据矛盾/最终公式冻结依原规则GPT-6 Astra｜High。

'''

def main():
    original=json.loads((OUT/'original_case_before.json').read_text())
    protected=json.loads((OUT/'protected_inputs_before.json').read_text())
    assert original=={str(p):sha(p) for p in OLD.rglob('*') if p.is_file()}
    assert all(sha(p)==s for p,s in protected.items())
    status=json.loads((OUT/'verification.json').read_text())
    assert status['software_preparation_PASS'] and status['unit_tests']==70 and not status['S0_started']
    assert not (OLD/'results').exists() and not (NEW/'results').exists()
    files={str(p):sha(p) for p in NEW.rglob('*') if p.is_file()}
    save(NEW/'evidence/revision_seal.json',dict(
        revision_id='URV-CHECKER-v1.1-20261101',kind='CHECKER_REVISION_PREPARATION_ONLY',
        simulation_authorized=False,approved_run_ids=[],actual_formal_run_ids=[],S0_started=False,
        external_data_history='PENDING_AUTHOR_CHECK',F04='OPEN_OUT_OF_SCOPE',
        source_preparation_seal=str(OLD/'evidence/preparation_seal.json'),
        source_preparation_sha256=sha(OLD/'evidence/preparation_seal.json'),inputs_sha256=files,
        verification_sha256=sha(OUT/'verification.json'),tests_log_sha256=sha(OUT/'tests_final.log')))
    digest=sha(NEW/'evidence/revision_seal.json')
    (NEW/'evidence/revision_seal.sha256').write_text(digest+'\n')
    for name in ['SIM240_AI_CONTEXT.md','AI_HANDOFF_20261015.md']:
        path=ROOT/'docs/reports'/name;old=path.read_text()
        assert old==(OUT/'before'/name).read_text(), 'concurrent state update'
        start=old.index('\n## ')+1;end=old.index('\n## ',start+1)+1
        new=old[:start]+ENTRY+old[end:]
        path.write_text(new)
        (OUT/(name+'.diff')).write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='before/'+name,tofile='after/'+name)))
        assert new[new.index('\n## ',new.index('\n## ')+1)+1:]==old[end:]
    links=0
    for p in [NEW/'README.md',NEW/'EXECUTION_CONTRACT_REQUIREMENTS.md',OUT/'REPORT.md']:
        for target in re.findall(r'\]\(([^)]+)\)',p.read_text()):
            if '://' in target:continue
            assert (p.parent/target.split('#')[0]).exists(),(str(p),target)
            links+=1
    assert all(sha(p)==s for p,s in files.items())
    assert original=={str(p):sha(p) for p in OLD.rglob('*') if p.is_file()}
    assert all(sha(p)==s for p,s in protected.items())
    save(OUT/'final_verification.json',dict(DELIVERY_PASS=True,F01='ADDRESSED_AND_TESTED',F02='ADDRESSED_AND_TESTED',
        F03='ADDRESSED_AND_TESTED',F04='OPEN_OUT_OF_SCOPE',tests=70,original_CASE_files_preserved=830,
        checker_revision_seal_sha256=digest,revision_input_count=len(files),local_links_checked=links,
        shared_context_and_handoff_updated=True,external_data_history='PENDING_AUTHOR_CHECK',
        S0_started=False,formal_execution_binding_effective=False,actual_formal_run_ids=[],
        native_compiler_calls=0,solver_calls=0,formal_NUMERICAL_GATE='NOT_EVALUATED',RESULT_PASS=False,
        geometry_PASS=None,reference_qualified=False,submission_ready=False))
    outputs={str(p.relative_to(ROOT)):sha(p) for p in OUT.rglob('*') if p.is_file() and p.name!='source_manifest.json'}
    outputs.update({str(p.relative_to(ROOT)):sha(p) for p in NEW.rglob('*') if p.is_file()})
    for name in ['SIM240_AI_CONTEXT.md','AI_HANDOFF_20261015.md']:
        p=ROOT/'docs/reports'/name;outputs[str(p.relative_to(ROOT))]=sha(p)
    save(OUT/'source_manifest.json',dict(files=outputs))
    print(json.dumps(dict(DELIVERY_PASS=True,revision_seal_sha256=digest,tests=70,original_CASE_preserved=True,
        S0_started=False,external_data_history='PENDING_AUTHOR_CHECK')))

if __name__=='__main__':main()

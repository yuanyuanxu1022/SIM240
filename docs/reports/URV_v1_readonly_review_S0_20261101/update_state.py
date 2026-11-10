#!/usr/bin/env python3
"""Update only the leading current-state entry; preserve all following sections."""
from pathlib import Path
import difflib
import json

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[2]
ENTRY='''## URV-v1只读复核完成，S0绑定草案暂停生效（2026-11-01）

- 本轮用户范围：只读复核准备包，随后确认外部数据历史，再另行准备S0两条h75回归执行绑定；当前不启动。用户已回答外部历史“尚不能确认，需要核查”，记录`docs/reports/URV_v1_readonly_review_S0_20261101/external_data_history.json`，状态PENDING_AUTHOR_CHECK，不能填CONFIRMED或认定候选未见。此前本地无匹配只限已查范围，不替代作者事实核查。
- 新入口`docs/reports/URV_v1_readonly_review_S0_20261101/REPORT.md`、findings.json、review_verification.json及`S0_DRAFT_NOT_EXECUTABLE/S0_binding_DRAFT.json`。本轮审查编号URV-READONLY-S0-20261101，非求解run_id。实际新正式run_id=[]，没有启动命令、正式运行目录或执行授权生效。
- 只读复核：原准备CASE全830文件保持；1432项准备输入、旧C/h75及回归1686绑定匹配；既有零步审计796文件哈希匹配。24组从配置独立复算材料/体积/边界，19处源码替换逆向恢复D4。原编译exit0、72次零步调用/24帧reader与35测试通过证据保留为前轮事实；本轮没有重复编译、原生预检、求解器或VTK reader调用，没有修改封存源/程序/协议/门槛。原URV_ZERO_20261101_01仍只为零步审计。
- 发现执行前缺口F01(HIGH)：check_run拒绝out在原run内后，main异常分支仍向该out写failure.json；仅在新人工目录用真实CLI复现，未触碰实际结果。F02(MEDIUM)：h75逐列差异在need失败前未保存，与“保存差值并暂停”不符；人工helper计算+静态控制流核对。F03(HIGH)：binding未强制native源/程序/编译依赖/库覆盖，run名单未强制逐条case/配置SHA/目录对应；人工缺native清单仍被binding接受，人工字段不是用户确认/执行合同。F01—F03在生效S0绑定前须修订或等效外层约束并验证，本轮未改源码。
- F04(MEDIUM)：24条汇总CLI共用同一合同SHA，不兼容S0—S5分阶段各自封存；静态核对+明确mock来源层的人工SHA分支核查。该项需在后续汇总前解决，不阻塞S0单条接受，不为此提前授权全部24条或回写旧completion。四反例均新报告内隔离人工材料，不是流场解/新物理证据。
- S0两条未生效材料已静态整理：h75/d100/w120/P=Ly240、dx5nm，H125nm，P=+y/T=+x；a1e5、rho1000、nu1e-6、mu.001、tau1；dt4.166666666666667e-12s，窗1013/上限58800，57600流体点/32448壁连接/q=.5。旧D4基准K为P9.834076003216204e-23、T4.449022023188299e-23m³；仅旧基准非新结果。旧完整20共同列/全部输出及独立foundation证书SHA已列；原raw RESULT_PASS=false保留。K差≤1e-4与全部原URV数值/几何门槛不变，差异应先保存、无法解释则停。每条wall3600s/AS8GiB、单rank/thread/cuboid、overlap3，启动前RAM/磁盘另核。
- 草案明确INACTIVE_BINDING_DRAFT_NOT_EXECUTION_RELEASE；simulation_authorized=false、approved_run_ids=[]，候选编号仅PROPOSED_，模板mode=describe且输出DRAFT_NOT_AN_EXECUTION_DIRECTORY。正式程序SHA/最终配置SHA/执行清单SHA为空，当前URV_PREPARATION_ONLY=1程序只列准备来源，没有移除保护或创建正式执行合同/外层运行器。作者历史未确认且F01—F03未解决，所以当前执行就绪HOLD，而非已可启动。
- 当前正式NUMERICAL_GATE=NOT_EVALUATED、RESULT_PASS=false、geometry_PASS=null，MODEL_COMPARISON/physical_validation=NOT_EVALUATED；reference_qualified=false、strict_error_bound_established=false、submission_ready=false。旧C/h75限定离散资格、旧细T FAIL、V2/G4锁、D4预测HOLD、旧N8 run_id=D4_N8_diag_v3_1_20261026_v1及NOT_EVALUATED/false/null、GDI01既有接入结果均保持。前轮零步准备证据未被否定，但不能作为本轮执行审查放行。
- 改动仅新增本轮报告/人工反例/不生效草案并维护本状态与最新交接；没有改旧CASE/源码/结果/协议，没有编译/正式求解/重跑/拟合/新物理验证/提交推送/对外发送。审查为作者请求的AI自审，不是独立人工验收。具体缺口、原始定位、验证边界及作者待查事项见REPORT。
- 当前停点：只读复核完成，外部历史待作者按范围核查，S0正式绑定未生效。下一具体任务可另授权新版本最小修订F01—F03及反例核验，保留旧准备包；作者并行核实外部历史。两项完成后再准备S0正式构建/逐条配置编号目录/完整来源和独立退出资源产物合同，当前不启动、不进入S1；F04后续汇总前单独处理。常规修订/复核建议GPT-6.1 Sol｜High；实质理论疑难/多证据矛盾或最终公式冻结依原规则GPT-6 Astra｜High。

'''

def main():
    changes=[]
    for name in ['SIM240_AI_CONTEXT.md','AI_HANDOFF_20261015.md']:
        path=ROOT/'docs/reports'/name;old=path.read_text()
        assert old==(OUT/'before'/name).read_text(), 'concurrent state change'
        start=old.index('\n## ')+1;end=old.index('\n## ',start+1)+1
        new=old[:start]+ENTRY+old[end:]
        path.write_text(new)
        (OUT/(name+'.diff')).write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='before/'+name,tofile='after/'+name)))
        assert new[new.index('\n## ',new.index('\n## ')+1)+1:]==old[end:]
        changes.append(str(path))
    (OUT/'state_update.json').write_text(json.dumps(dict(updated=changes,remaining_history_preserved=True),indent=2)+'\n')

if __name__=='__main__':main()

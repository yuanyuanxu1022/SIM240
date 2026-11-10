#!/usr/bin/env python3
"""Replace only the current entry, preserving all remaining historical sections."""
from pathlib import Path
import difflib
import json

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[2]

ENTRY='''## URV-v1隔离实现、编译与零步审计完成，正式计算保持未启动（2026-11-01）

- 用户范围：按已采用URV-v1实现隔离参考程序及独立检查器，编译与零步审计；不启动正式计算。新入口`CASE/unseen_v2_reference_v1/README.md`、`docs/reports/URV_v1_preparation_20261101/REPORT.md`及verification.json。审计编号`URV_ZERO_20261101_01`，非正式求解run_id；当前实际正式run_id=[]，没有启动命令。
- 已实现：D4绑定源的隔离物理内核，C原字节mass_stats.h与补偿物理质量/密度差账本；旧顺序mass/mass_error、原初态分母与旧门状态保留。19处列明替换可逆恢复原D4全文，几何/壁面、初始化/体力/碰撞参数、J/剖面与原统计窗定义未改；质量严格<1e-10、账本差≤1e-13及URV-v1其他门槛保持。物理源码相同不代替之后S0真实回归。
- 此次编译exit0，mpic++/g++13.3.0，OpenLB当前HEAD882924a9cfc8dcdf82909e39530789cb6f5ebcc4；程序SHA9a139fc569b901b01c4709d5e5cd6c9ff89e66a9a42e67a198d3a96faadd08d3。依此次编译.d/链接绑定1393项依赖、15动态库；当前环境与工作树状态已记录，不冒充历史构建或干净快照。源码/二进制/编译证据见CASE/evidence/build_environment.json。
- 原生零步：24describe+24真实precheck+24initialize，覆盖8种几何/网格及全部方向/驱动力。独立XZ解析求交/Y挤出核材料/体积/连接，candidate=valid=installed、q=.5、fallback/unresolved0。h60/d80/dx1.25为2949120流体点/490752壁面连接；h30/d80同格2064384点/490752连接。零步几何PASS单列，不冒充正式geometry_PASS。
- 24初始化VTK帧均实际reader核完整引用payload、核心唯一流体坐标、材料/速度/周期压力/运动学耗散与积分J；Float32导出/Float64求和界内匹配双精度测量。初速度含a*dt/2，与体力方案一致。全部实际collideAndStream调用0；本准备版URV_PREPARATION_ONLY=1，steady误用已实测在有效配置/场创建前拒绝。单进程/线程、地址空间8GiB下完成初始化不代表正式峰值内存/耗时/全程输出已测。
- 独立检查器已实现，不导入求解器/拟合器。核来源/独立退出、全轨迹双账本、全部窗口和首次停止、几何/单位/剖面/回归、三驱动力/三格参考资格及敏感性带比较。35Python测试及2C++算术测试通过；两条旧h75完整轨迹只读窗口复算匹配。2个外部CLI反例均exit2且无成功记录。首轮q逐位相等断言、第二轮人工薄间隙/主要条件断言错误均保留失败日志并按原协议修正，未改物理门槛。检查器尚未经新URV完整稳态输出端到端核验。
- 准备封存CASE/evidence/preparation_seal.json为PREPARATION_ONLY_NOT_EXECUTION_RELEASE，SHAe0eb9a54c1c1168d25483a085e70462d04cfa76aeb4922dddbea17b07b1811cb，1432输入绑定；simulation_authorized=false、preparation_only_build=true、approved_run_ids=[]。原URV协议/预测逐字节保留，采用记录common/adoption.json仅覆盖本轮实施。82项选定保护输入前后一致；另对照前轮C/h75及h75回归1686既有绑定全部保持。
- 当前科学状态：新正式NUMERICAL_GATE=NOT_EVALUATED、RESULT_PASS=false、稳态geometry_PASS未评估、REFERENCE_QUALIFIED_FOR_CASE=false、MODEL_COMPARISON/physical_validation=NOT_EVALUATED。reference_qualified=false、strict_error_bound_established=false、submission_ready=false；旧D4预测HOLD、旧N8 run_id=D4_N8_diag_v3_1_20261026_v1及NOT_EVALUATED/false/null、原细T FAIL、C/h75限定资格、V2/G4锁和GDI01既有接入结果不变。未产生新稳态参考K或公式成绩。
- 改动范围：只新增隔离CASE、本轮报告与维护本状态/最新交接；没有修改旧源码/结果/协议/锁，没有正式求解/重跑/拟合/提交推送/对外发送。原生源码存在、此次编译、零步安装与初始化、检查器准备测试已核，正式运行与独立验收未做。没有正式启动命令或正式运行器包交付。
- 当前停点：本轮准备任务完成；下一具体动作只读复核此准备包。作者外部未归档数据历史仍PENDING；后续须确认历史并另行准备S0两条h75回归的逐条配置/目录/编号/资源/执行合同，开放时间推进需新构建及绑定，不覆盖本准备封存。每阶段仍分别获准、用户启动、完成后验收，不自动进入S0或后续批次。常规审核建议GPT-6.1 Sol｜High；疑难理论/矛盾裁决或最终公式结论冻结按原规则建议GPT-6 Astra｜High。

'''

def main():
    paths=[]
    for name in ['SIM240_AI_CONTEXT.md','AI_HANDOFF_20261015.md']:
        p=ROOT/'docs/reports'/name
        old=p.read_text();before=(OUT/'before'/name).read_text()
        if old!=before: raise RuntimeError('state changed since task start; do not overwrite '+str(p))
        start=old.index('\n## ')+1
        end=old.index('\n## ',start+1)+1
        new=old[:start]+ENTRY+old[end:]
        p.write_text(new)
        (OUT/(name+'.diff')).write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='before/'+name,tofile='after/'+name)))
        assert new[new.index('\n## ',new.index('\n## ')+1)+1:]==old[end:]
        paths.append(str(p))
    (OUT/'state_update.json').write_text(json.dumps(dict(updated=paths,remaining_history_preserved=True),indent=2)+'\n')

if __name__=='__main__':main()

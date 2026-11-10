#!/usr/bin/env python3
"""Apply the explicitly authorized Section 4 and corresponding prose revision."""
import difflib
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
PREVIOUS=ROOT/'docs/reports/Methods_and_Section4_review_20261022'
TARGET=ROOT/'docs/reports/SIM240_中文稿_导师审阅版_20261022.md'
candidate=PREVIOUS/'Section4_revision_candidate.md'
before_bytes=TARGET.read_bytes()
before=before_bytes.decode()
expected=json.loads((PREVIOUS/'edit_record.json').read_text())['after_sha256']
assert hashlib.sha256(before_bytes).hexdigest()==expected,'目标稿与已审快照不同，须先核对并发改动'
assert not (HERE/'manuscript_before.md').exists(),'本轮已执行，拒绝覆盖快照'
(HERE/'manuscript_before.md').write_bytes(before_bytes)
inputs=json.loads((PREVIOUS/'input_hashes.json').read_text())
for f in PREVIOUS.iterdir():
    if f.is_file():
        inputs[str(f.relative_to(ROOT))]=hashlib.sha256(f.read_bytes()).hexdigest()
assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in inputs.items())
(HERE/'input_hashes.json').write_text(json.dumps(inputs,ensure_ascii=False,indent=2)+'\n')

s=before
changes=[]


def replace(old,new,key):
    global s
    assert s.count(old)==1,(key,s.count(old))
    s=s.replace(old,new)
    changes.append(key)


old_section='## 4 结果'+s.split('## 4 结果',1)[1].split('## 5 讨论',1)[0]
candidate_section='## 4 结果'+candidate.read_text().split('## 4 结果',1)[1]
replace(old_section,candidate_section.rstrip()+'\n\n---\n\n','section4_candidate_adopted')

replace('间隙越薄，这一不对称越明显。',
        '在共同覆盖该槽深区间的50、75、125 nm三档间隙中，沿槽相对增益随间隙增大而减弱；在125 nm间隙下仍约为39.2%。',
        'abstract_trend_domain')
replace('**其二，局部立方律在全部 36 个样点上都高估输运系数，无一例外。**',
        '**其二，以5 nm网格的离散数值结果为参考，局部立方律在全部36个主方向样点上均高估输运系数。**',
        'abstract_reference_definition')
replace('在 45° 驱动下，模型预测的流向偏离显式结果 9.20°。',
        '在45°驱动下，两组主值重建的通量方向相差9.20°。',
        'abstract_angle_reconstruction')
replace('基于已公布系数的经验修正把沿槽最大绝对残差降至 10.5%、跨槽（$h\\ge 50$ nm）降至 6.9%，但在最薄间隙的跨槽分量上仍有 −18.7% 的残差；且该修正的系数只含槽深与槽宽之比，不含间隙。',
        '按已公布舍入系数作回顾性评价，经验修正后的最大绝对残差为沿槽18点10.5%、跨槽18点18.7%；其中 $h\\ge50$ nm的15个跨槽点为6.9%。在 $(h,d)=(25,100)$ nm跨槽点，5 nm参考下的偏差由+16.36%变为−18.71%，绝对偏差反而增大。修正仅以 $d/w$ 为自变量，剩余残差仍随间隙变化，其来源尚未分解。',
        'abstract_full_and_subset_residuals')
replace('问题在于：**它成立的前提是各局部段落之间互不干扰。** 对纳米级沟槽、且凸台下只剩几十纳米连通液层的情形，这个前提是否成立，需要直接检验。',
        '问题在于，这一局部平板组合未显式解析侧壁附近的横向速度耦合和深浅区域连接处的流动。在槽深与槽宽相近、凸台下仍有连通液层的几何中，该近似能否准确给出整体输运，需要直接检验。',
        'introduction_local_model_assumption')
replace('先用显式几何建立两个主值的真实响应',
        '先用显式几何计算两个主值的离散数值响应',
        'introduction_reference_terminology')

old_discussion='### 5.1'+s.split('### 5.1',1)[1].split('### 5.2',1)[0]
new_discussion='''### 5.1 局部平板组合的局限与候选机制

本文在全部采样主方向上观察到相对于离散数值参考的正偏差，且两方向偏差幅度不同。这表明局部立方律在所检查条件下高估通流能力，但仅凭全局系数不能确定偏差由哪一部分流动主导。

沿槽局部模型将深区与浅区的平板导度作算术平均，没有显式解析相邻区域的横向黏性耦合及侧壁附近的速度变化。侧壁剪切和深浅区域间的动量交换可作为后续检查的候选因素；本文未量化它们对总通量或耗散的贡献，不能据现有结果认定某种“拖拽”已经解释全部高估。

跨槽模型将局部平板阻力按一维串联关系组合，而显式流动还需通过台阶连接区域。台阶附近的速度重分布及黏性耗散可能影响整体阻力，但本文没有独立测量局部阻力份额，也未证明阻力必由最窄处控制。

参数趋势也需要限定。固定间隙的已采样槽深序列中，沿槽偏差随 $d/w$ 增大；但加入25 nm间隙后，沿槽偏差不再对所有槽深都随间隙增大而单调减小。特别是 $d=100$ nm时，偏差从 $h=25$ nm的139.14%上升至 $h=50$ nm的154.24%。因此，不能把“间隙越薄，某一机制越强”作为已验证的机制规律。

以上机制仍需独立耗散分解或适用条件一致的参考解检验。相关矩形线栅挤压研究已报告简单润滑模型的局限 [11]，但其加载方式、填充状态与比较基线不同，不能把其力比直接用于解释本文固定间隙下的系数偏差。

'''
replace(old_discussion,new_discussion,'discussion_mechanisms_and_nonmonotonicity')
replace('最薄间隙的跨槽分量网格敏感性最大（−4.43%），现有几何特定加密尚不能转化为全地图不确定度上界。',
        '在四个已检查加密几何中，最薄间隙 $(h,d)=(25,100)$ nm的跨槽分量网格敏感性最大（−4.43%，以5 nm结果为分母）；现有几何特定加密尚不能转化为全地图不确定度上界。\n\n修正效果同样需要按样点范围与参考网格分别报告。跨槽全18点的最大绝对残差为18.7%，6.9%只适用于 $h\\ge50$ nm的15点子集。最薄间隙 $d=100$ nm跨槽点在5 nm参考下的绝对偏差由16.36%增至18.71%；换成2.5 nm参考后，则由21.76%降至14.94%。因此，整体最坏偏差下降不能替代逐点评价，局部改善判断还受到数值参考分辨率影响。V2未显式包含间隙，且剩余残差随间隙变化；这提示其表征范围受限，但不能单独证明间隙缺项是残差的唯一来源。',
        'discussion_correction_scope_and_grid')
replace('**一、** 在本文采样的全充液矩形沟槽中，增加槽深对沿槽与跨槽输运的影响明显不同。间隙 50 nm 时槽深由 25 增至 120 nm，$K_{yy}$ 增至 3.55 倍，$K_{xx}$ 仅增至 1.034 倍。',
        '**一、** 在本文采样的全充液矩形沟槽中，增加槽深对沿槽与跨槽输运的影响明显不同。间隙50 nm时槽深由25增至120 nm，$K_{yy}$ 增至3.55倍，$K_{xx}$ 仅增至1.034倍。在共同覆盖该槽深区间的50、75、125 nm三档间隙中，沿槽相对增益随间隙增大而减弱，但在125 nm时仍约为39.2%。',
        'conclusion_geometric_trend')
replace('**二、** 局部立方律在全部 36 个主方向样点上都高估输运系数：$K_{yy}$ 高估 +10.30% 至 +204.85%，$K_{xx}$ 高估 +8.11% 至 +54.19%。这是系统行为，不是个别点的偏差。',
        '**二、** 以5 nm离散数值结果为参考，局部立方律在全部36个主方向样点上均高估输运系数：$K_{yy}$ 高估+10.30%至+204.85%，$K_{xx}$ 高估+8.11%至+54.19%。沿槽偏差在固定间隙的已采样序列中随槽深增大，但不对全部槽深都随间隙增大而单调减小。上述结果不构成连续参数域上的普遍规律，也未确定单一主导机制。',
        'conclusion_error_trend_and_limits')
replace('45° 驱动下流向偏离 9.20°。评价此类模型必须分别检验两个主值及其比值。',
        '45°驱动下由两组主值重建的通量方向相差9.20°。评价此类模型需同时检验两个主值及其比值。',
        'conclusion_angle_reconstruction')
replace('**四、** 现有经验修正把沿槽残差降至一成量级，但未消除间隙依赖，最薄间隙跨槽残差仍达 −18.7%。其精度应连同采样范围、参考网格与数据使用历史一并报告，不能推广为任意几何或动态压印过程的预测关系。',
        '**四、** 按公布系数回顾性评价，V2修正后的最大绝对残差为沿槽18点10.5%、跨槽18点18.7%，其中 $h\\ge50$ nm的15个跨槽点为6.9%。在 $(25,100)$ nm跨槽点，5 nm参考下的绝对偏差反而增大，局部改善判断也依赖参考网格。修正未消除残差的间隙依赖，评价需同时报告样点范围、参考网格与数据使用历史，不能推广为任意几何或动态压印过程的预测关系。',
        'conclusion_correction_scope_and_exception')

replace('局部立方律误差随间隙变化（机制）','局部立方律误差随间隙变化（参数依赖）','figure_list_parameter_dependence')
replace('可用于直观展示"跨槽串联、沿槽并联"的图像。',
        '可补充展示速度与耗散分布；成品图本身不能替代阻力或耗散贡献的独立分解。',
        'optional_field_plot_mechanism_limit')
replace('7. **明确区分**"机制候选"与"已验证结论"：4.2 与 5.1 中关于并联拖拽、串联损失的解释均标注为推测。',
        '7. **明确区分**“机制候选”与“已验证结论”：§4.1与§5.1将串并联图像、侧壁剪切和台阶附近流动重分布作为定性解释或待核因素，不据全局系数认定单一机制。',
        'appendix_mechanism_summary')
replace('本轮随后仅审查 §4，未修改该章；逐项意见、原始数据复算与候选订正文案见',
        '上一轮随后仅审查§4、未修改该章；该停点现已由D.4所述修订接续。上一轮逐项意见、原始数据复算与候选订正文案见',
        'appendix_previous_stage_label')
s+='''
### D.4 §4写入与跨章节表述同步（2026-10-22）

按用户明确授权，将 `Methods_and_Section4_review_20261022/Section4_revision_candidate.md` 的§4写入本稿，并同步摘要、引言中的对应假设表述、§5.1/§5.3及结论：限定单调趋势的参数范围、删除错误数量级和含混倍数、明确流向角由主值重建、同时列全18点与15点子集残差，并报告最薄间隙跨槽点的局部变差与网格依赖。侧壁剪切、台阶附近速度重分布和间隙缺项均不作为已证实的唯一原因。图件清单中的“机制”标签及本附录对应摘要同步收紧。

本轮变更记录、前稿快照、逐项主张核对和输入保护检查见 `docs/reports/Section4_sync_20261022/REVISION_NOTE.md` 与 `verification.json`。方法章和已有科学参数不变；无新仿真、优化器或数值/物理Gate升级。
'''
assert TARGET.read_bytes()==before_bytes,'写入前检测到并发稿件改动'
TARGET.write_text(s)
(HERE/'revision.diff').write_text(''.join(difflib.unified_diff(before.splitlines(True),s.splitlines(True),fromfile='manuscript_before.md',tofile=TARGET.name)))
(HERE/'edit_record.json').write_text(json.dumps(dict(changes=changes,before_sha256=hashlib.sha256(before_bytes).hexdigest(),after_sha256=hashlib.sha256(TARGET.read_bytes()).hexdigest(),candidate_sha256=hashlib.sha256(candidate.read_bytes()).hexdigest()),ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(changed_groups=len(changes),target=str(TARGET),section4_adopted=True),ensure_ascii=False))

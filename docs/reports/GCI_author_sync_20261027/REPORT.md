# 作者采用范围：GCI表及限定文字同步记录

日期：2026-10-27。用户明确授权“按作者采用范围同步候选表和限定文字，保持新增计算关闭”。执行范围依据上一轮`GCI_decision_review_20261027/CANDIDATE_TEXT.md`及已完成的Astra独立复核，不新增理论裁决、假设或严格误差界。

## 已同步内容

1. 正式稿`SIM240_中文稿_导师审阅版_20261022.md`的§3.3采用候选限定段落，指向补充材料S9、表S5；同时更新附录B的补充表数量及S9对应关系。
2. `SIM240_Supplementary_Methods_20261024/SUPPLEMENTARY_METHODS.md`的S9新增表S5，给出6项指标的p、外推值、ea、e_ext、细格GCI及失败点依赖。保留原表S4的9项记录与所有原始状态；S1—S4不重编号。
3. `Table_S5_conditional_gci.csv`逐字节复制上一轮已复核候选表，保留三格原始值、两个r、Fs及完整精度。三个依赖历史细T失败点的指标为K_perpendicular、eta_perpendicular、anisotropy。
4. 同步渐近性限定及平板解析比较：历史confirmed标签不作为独立渐近证据；平板统一细格分母的0.0271495%与GCI 0.0352348%比较，仅支持该工况与积分量。未引入原错误报告的G1“13.5倍覆盖”、机制归因或第四格结论。
5. 更新补充README、编号对应CSV以及项目状态/交接；原审查报告、候选及旧证书保留原字节。

## 核对与保护

改前快照见`before/`；四份正文/补充入口文件的差异见`document_changes.diff`；改动清单见`applied.json`。核对结果见`verification.json`，检查脚本`verify_sync.py`不调用求解器、不重算原场，仅检查文件、表格一致性和字节保护。保护范围见`protected_inputs.json`，不宣称重验全仓库或全部原始场。

最终17项文档核对全部通过：36份选定保护输入字节不变、50条本地链接及锚点可解析、6行表值与候选一致。初次检查仅因检查器未识别源码链接的`:行号`后缀报两处不存在；已修正检查器并通过复验，初始结果保留为`verification_initial.json`，没有为通过检查改写原源码链接。

本轮保留历史细T质量指标1.1967043900362632e-10、阈值1e-10及独立exit3，并在表S5附近明示。历史G2 Step3 FAIL/INCONCLUSIVE、5nm离散参考口径、全参数域严格误差界未建立，以及[10]发表版未逐页核对的限制均保持。

## 当前停止点

本次是已审定候选的作者授权文档同步，无新编译、求解、网格、拟合、真实N8提取、第二项或Git提交/推送。无新run_id。已有N8 run_id=D4_N8_diag_v3_1_20261026_v1；NUMERICAL_GATE=NOT_EVALUATED、RESULT_PASS=false、geometry_PASS=null、reference_qualified=false、strict_error_bound_established=false、submission_ready=false，预测HOLD。

方法引文原件、历史构建来源与数值参考资格缺口继续开放，详见原资料合同和上一轮裁定；补表不作为这些缺口已闭合的依据。正式稿仍待作者最终科学审定，尚未做期刊版式验收或发布。

本轮无需新增计算。若后续继续，只读检查作者整稿及来源合同中尚缺证据即可；新增网格需另立验证/预算合同并取得明确运行授权。

## 流程来源

采用scientific-writing技能整理和核对已授权修订。按技能要求，仅在本同步记录列流程来源，不加入CFD论文的方法引文：Kassis, T., Agarwal, V., He, Y., Patel, D., & Brueckner, A. M. (2026). Scientific Agent Skills: A Library of Procedural Knowledge for Research Agents. [arXiv:2609.00065](https://doi.org/10.48550/arXiv.2609.00065)。本轮在线核对作者和版本记录。

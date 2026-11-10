## S4T采用前终审完成：原草案需修订，已有TGE准备保留，执行权限关闭（2026-11-04T16:26:33.295842+08:00）

用户范围为“在采用和最终冻结前，终审新网格资格衔接、旧证据复用及资源规则，执行权限继续关闭”。终审入口 `docs/reports/URV_S4T_supplement_final_review_20261104/REPORT.md`、AMENDMENT_DRAFT.md、decision.json、evidence_review.json。裁定REVISE_BEFORE_ADOPTION_AND_FREEZE；v0.2修订条款未采用，最终执行合同未冻结。现有独立TGE最小准备已采用/实现的记录保持，不能继续统称工作区无准备，也不能视为v0.1资源或新资格规则已采用。

可保留T2.5/1.25/0.625nm族及两条旧T原合同复用，原1%门槛及旧S4 FAIL不变。五项修订：新T证据到P/T参考资格的具体条件（含S5仅dx2.5三力、F04来源汇总）；父检查器与读场同时占内存的整体预算；TGE原8GiB/300s与v0.1的16GiB/分模式时限不得混用；输出/临时/分析总范围及父子超时；固定tau下dx与dt联合加密不证明唯一空间根因。修订资源候选为整任务组18GiB、单大进程地址空间16GiB、可用RAM22GiB，需先验证整组限制机制及可行性，未采用/未实施，不是提高原权限。48h正式/4h检查仍仅候选，短PERF不能证明整窗或完成保证。

核对原release3284输入、TGE准备A3695输入、旧T两基准完整来源/输出与旧六点K/网格算术；3727项保护输入核对一致，详见完整性记录。旧P网格PASS，T中细1.328387035%>1% FAIL。原S4六run_id仍URV_S4_{P/T}_dx{5/2p5/1p25}_reuse_v1_20261103_01；现有TGE仅预留URV_S4_T_dx0p625_TGE_v1_20261104_01及3个零步身份，四目录核对仅config/manifest，approved/actual为空。本轮无新增运行身份、无CASE修改/构建/原生/读场/PERF/正式/原科学检查器重放，只有文档/绑定与标量核对。另一工作流准备材料仅快照，不覆盖。

原S4_STAGE_ACCEPTED=false、reference_qualified=false、MODEL_COMPARISON/physical_validation未评价、strict_error_bound/submission_ready=false、F04 OPEN保持。下一具体动作：将终审修订条款与现有TGE准备的身份映射、资源决策整理成一致待采用文本，仍不修改CASE或开启执行；如以后改变已封存资源，必须新准备版本和软件核对，不改原A。当前无需用户启动计算，不交命令，不自动3＋1/PERF/正式/重试/延长/S5。本轮为当前AI终审意见，未声称模型切换、独立Astra签署或人工审稿。


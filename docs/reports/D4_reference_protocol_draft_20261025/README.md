# 独立截面参考、加强停止与几何覆盖：待审入口

2026-10-25。用户授权起草协议并比较验证要求与资源，明确不启动计算。状态：**DRAFT / 未批准 / 未冻结 / 未实现 / 未运行**。本轮只做现有来源核对、组合计数和方案文档，没有求解Poisson/Stokes/NS，也没有OpenLB初始化、编译或时间推进。

推荐先做独立截面方法的小规模实现与基准准备，再按实测成本判断后续；加强停止对照另行审查。新方法与加细原LBM回答不同问题，当前没有选定已合格新参考或解除旧窄槽FAIL后的停止。

## 本轮交付

- [独立参考方法待审协议](REFERENCE_METHOD_DRAFT.md)：沿槽标量Poisson、横槽周期Stokes，物理压力符号与零均值、独立积分、平板/制造解/网格/角点/惯性验证。
- [加强停止待审协议](STOP_COMPARISON_DRAFT.md)：3几何网格、P/T共6项，同一离散设置从初态匹配，保存旧停止点，两方向共同预定终点；不覆盖或续写旧运行。
- [覆盖与资源比较](COVERAGE_AND_RESOURCES.md)：10代表几何、30基础网格、2匹配尺度审计网格、分批与估计假设。
- [机器可读草案](proposal.json)、[10几何表](geometry_coverage10.csv)、[30网格规模表](reference_mesh_budget30.csv)、[尺度网格2行](scale_audit_meshes2.csv)、[停止对照6行](stop_comparison6.csv)、[资源情景](resource_comparison.json)。这些不是求解器输入、正式run_id或运行许可。

## 科学采用前仍须裁定

1. **后端与实现版本。** 拟议贴体P2/P1有限元需要新的周期约束、压力规范和验证环境；系统Python缺相应主要依赖，尚未选定/安装后端。官方演示不是本项目周期沟槽的验证证据。
2. **新容差与总预算的含义。** 候选参考中细差0.25%、条件GCI0.5%、代数/积分变化各0.01%、停止与Stokes建模差各0.05%，均为看过旧结果后提出的待审研究要求。它们属于不同证据层，部分诊断相关，不能直接当独立统计量合成，也不能据此宣称所有数值误差总上界≤0.5%。如果负责人要求总预算≤0.5%，正式冻结前必须明确分项分配及可靠估计方式；本草案的总参考误差预算尚未最终裁定。旧1%/.5%网格目标和模型3%/5%评价不改。
3. **覆盖与保留角色。** 10点覆盖四个比例角点、薄/厚间隙及两组尺度对照，但不保证全域；3个新点为开发诊断，避开旧保留几何。已见数据不重新命名盲测，外部接触记录仍须核验。
4. **资源与实施范围。** FE真实耗时未测，8 GiB只是候选预算；B0/B1/B2时间额度不是耗时预测。6项停止比较约16.82小时是按历史速度的情景；0.625 nm四项约187.85小时为更粗略工作量情景。均属于原60项之外的拟议增量，不能凭这份文件启动。

## 本轮核对与保护

`build_plan.py`和`add_scale_audit.py`只生成表格与元数据，不导入或执行求解器。`verify_draft.py`独立核对几何范围/比例、保留组排除、尺度匹配、网格组合计数、原记录绑定和共同停止步数，核全部受保护输入前后不变、文档本地链接及状态更新范围。结果见[verification.json](verification.json)，没有将这些静态核对称为流动或参考精度PASS。

旧数值/几何/已保存场证据保持；无条件“无fallback”的表述仍以[上一轮澄清](../D4_reference_static_audit_20261025/REPORT.md)为准。旧网格v2两个窄槽5FAIL/1PASS、开发网格数值/场10/12、宽细2项缺失和G4 v1锁全部保留。预测与宽细仍HOLD；没有新拟合、参考采用、求解器更改、长算命令、Git提交或推送。状态及交接只替换当前第一篇入口，其余章节不变。

下一具体动作：审查本草案的压力/周期约束、验证预算、代表覆盖与分批次序，确定优先实施范围；如获新的实现授权，只准备独立后端与B0基准，不自动计算B1/B2/S0或进入预测。

## 来源与辅助方法

本地依据：D4原design/execution/PROTOCOL、G4 v1合同、已验收16行开发来源与原resource记录、`D4_reference_static_audit_20261025`及前轮修订建议；完整SHA在[protected_inputs.json](protected_inputs.json)。原保护4034路径与新读产物合并为4057个去重路径，集合重叠不相加。本轮没有重新验收原始流场或重新推断旧首次停止点。

外部方法来源均于2026-10-25访问：[DOLFINx官方Taylor–Hood/压力零空间例程](https://docs.fenicsproject.org/dolfinx/main/python/demos/demo_stokes.html)，[NASA NPARC网格收敛方法](https://www.grc.nasa.gov/www/wind/valid/tutorial/spatconv.html)。前者支持候选离散方法，后者支持条件网格诊断；均不提供本项目的新容差，也不证明本项目方法已实现/验证。

本轮采用scientific-critical-thinking和scientific-writing组织证据与待审规则。辅助工具来源：Kassis, T., Agarwal, V., He, Y., Patel, D., & Brueckner, A. M. (2026). *Scientific Agent Skills: A Library of Procedural Knowledge for Research Agents*. [arXiv:2609.00065](https://arxiv.org/abs/2609.00065)。已打开摘要页核对当前v2及作者/题名/年份，未列期刊参考；该引用不支持CFD物理结论。未向外部服务发送项目内容，科学采用由研究者/老师负责。

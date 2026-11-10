# GCI 判据与补证路线裁定（作者采用候选）

日期：2026-10-27。范围：复核用户提交的 `Celik_GCI_verification_20261027/REPORT.md`，推荐报告路线及是否增加第四网格。未修改原报告、历史CSV、原后处理源码、冻结协议或正式稿。本目录是新审查记录，不是替代历史Gate。

**决定建议：选 A，准备最小条件性GCI表；当前不建议立即增加0.625 nm。** 补表解决可核算性和披露问题，不消除参考资格、渐近性及全域误差证据缺口。删除[10]不能解决这些缺口；单纯方法性引用本身也不意味着必须报告本项目所有GCI量，不能泛称“引用一次就是违规”。

本轮已调用独立 `GPT-6 Astra｜High` 审查代理 `/root/gci_theory_review`，完成原文、代数及证据解释复核；这是实际独立复核，不是主会话模型配置变更。其结论与本报告一致。主代理另从9份既有result与退出码重算6项，未导入求解器或执行原后处理脚本。

## 1 必须修正的判断

1. **同组三点的比值不提供独立渐近证据，但不是恒为PASS。** 在当前单调正阶分支，`p=ln|ε32/ε21|/ln r`，且 `GCI32/(r^p GCI21)=|φ1/φ2|`。源码 `postprocess_grid.py:188–220` 与6行归档一致，数值恒等残差最大2.23e-16（浮点容差内一致，不是六行逐位相等）。例如细/中/粗值1、1.1、1.5给p=2而比值0.9091，会失败。当前阈值对正值等价于以中格为分母的细中差幅不超过5%；不是对未知连续解误差或渐近性的独立测试。
2. **观测阶接近形式阶是支持迹象，不能倒推低阶不合格。** ASME作者文稿PDF第6页、文本243–247说明正向支持及反向限制；表1还含低于1的示例。平板p≈1.991支持近二阶行为，沟槽p<2本身既不证明未渐近，也不证明已渐近。不能把“二阶”强制当作每个比值指标的已证明理论阶。正确结论是现有证据不足以独立确认沟槽渐近区。归档eta_parallel的p为0.939762729，不是0.938。
3. **0.625 nm仍为等比，非等比也不自动解决循环验证。** 5/2.5/1.25/0.625均为2倍细化。对同组三点的单幂模型，非等比满足 `ε32/ε21=r21^p(r32^p−1)/(r21^p−1)`，相应GCI比仍化为`|φ1/φ2|`。第四点的价值是用原三点预测新点，再检查预测残差和两个相邻三元组的p/外推值稳定性。p稳定在1.26只能支持所查范围内有效阶稳定，不能唯一归因几何奇性。
4. **成本不是4倍。** 历史细T原始记录保存3,686,400流体节点、D3Q19、Lx=Ly=240 nm；协议明确固定tau、dt∝dx²。保持原三维域等比例细化时，节点/基础内存约8倍，同物理时长步数约4倍，基础节点更新工作量约32倍。仅为条件尺度估计，不是实测运行预算。改二维或缩周期需另审等价性。
5. **较低p给出较大GCI不等于已证实保守误差界。** 对本次固定细中差，T用观测p的0.551022%大于强置p=2的约0.255052%；这只是两种计算的比较。保留历史细T质量FAIL，其质量指标1.1967043900362632e-10大于1e-10，独立exit3。T、eta_T、各向异性三行均依赖该失败点，必须一起标注。
6. **G1的“13.5倍覆盖”分子分母对象错配。** 原`richardson_summary.csv`的0.098068%是外推值对解析解的误差，1.323053%是细格GCI。原`matrix_summary.csv`保存细格K=3.556718529952092e-23、解析K=3.515625e-23，细格真实误差为1.168883%（解析分母）；统一细格分母为约1.1554%，覆盖约1.145，不能写13.5。该历史G1链的粗、中记录另有FAIL，本轮不将它作为新增合格校准。
7. **短窗波动不是剩余稳态误差界。** `rel_std≤1e−6`远小于网格差，仅支持保存窗口内波动较小，不能证明迭代误差不污染p。慢衰减过程可以同时有小波动和较大剩余偏差。
8. **Mach变化不推出误差不按dx²缩放。** 固定物理速度、tau的扩散标度下，u_lat=u_phys dt/dx∝dx、Ma∝dx，通常O(Ma²)项反而随dx²变化。具体混合误差原因未判定，不据此解释低阶。
9. **报告原替换句不能直接照搬。** 六项细中差以细格归一的范围实际为0.083855%—0.612125%，不是0.08%—1.3%。原CSV有p/外推/GCI但没有ea输出列；源码计算了ea，未计算或报告e_ext。新增候选表补齐两者。

## 2 最小表与解析检验

见 [CANDIDATE_TEXT.md](CANDIDATE_TEXT.md) 和 [candidate_gci_table.csv](candidate_gci_table.csv)。CSV同时给原始三格值、Fs、两个r、外推值、ea、e_ext、GCI和失败点依赖。量的定义：K为m³，eta方向=该方向K/同格Smooth K，各向异性=K_parallel/K_perpendicular。网格细/中/粗1.25/2.5/5 nm；Fs=1.25；h=75nm，沟槽d=100nm，P=240nm；其余物理参数沿用STEP3_PROTOCOL，不扩展适用几何。

G2 Smooth解析误差为0.027156875%（解析值分母），GCI为0.035234840%（细格值分母）。为严格比较，统一细格分母后的解析误差为0.027149502%，覆盖比为1.297808；等价的绝对误差比较得到同一比值。支持“此指定平板积分量中估计幅度覆盖解析偏差”，不称已校准整个估计器，不推至沟槽、其他几何或严格覆盖概率，也不作“唯一证据”的未经穷尽声明。

## 3 后续最少证据及停止点

- 当前可完成：采用最小表及随数FAIL说明；将归档的confirmed标注解释为历史标签而不作为论文渐近依据。保持历史文件原样，未来若修工具另建版本，禁止回写历史PASS。
- 数值参考升级前仍需：闭合历史细T/方案C的资格与来源链，区分短窗收敛记录和剩余迭代误差证据，核验误差模型适用性。不得用一次新增细网格替代这些证据。
- 只有明确需要强化连续解精度主张时，再单独制定第四点或独立参考验证合同：先冻结预测方式、几何/实现一致性、迭代污染检查和资源预算，再由用户明确授权启动。当前不提供启动命令。
- 原方法版本：本轮使用ASME官网四作者方法文稿，已目视PDF第6—7页；式(4)和式(6)出现21/12上标差异，候选采用自身统一符号φ_ext定义，未冒称逐字转录。发表版DOI `10.1115/1.2960953` 仍未逐页核对；三篇缺失原文/构建档案任务继续开放。

保持：历史G2 Step3 FAIL/INCONCLUSIVE，5nm离散参考口径、全图严格误差界未建立。无新run_id、编译、求解、真实N8提取、第二项、拟合、Git提交/推送。旧N8 run_id=D4_N8_diag_v3_1_20261026_v1；NUMERICAL_GATE=NOT_EVALUATED、RESULT_PASS=false、geometry_PASS=null、reference_qualified=false、strict_error_bound_established=false、submission_ready=false，预测HOLD。

## 4 核对依据与方法说明

- 原始网格档案：`CASE/03_grid_convergence/G2_EX240_grid_convergence/archive/g2_grid_20260917T165045+0800/` 下9份steady/result.txt、exit_code.txt及g2_richardson_gci.csv。
- G1比较：`CASE/00_validation/G1_Poiseuille_Bouzidi_Validation/results/g1_v2_20260916T202853+0800/{richardson_summary,matrix_summary}.csv`。
- 源码/协议：`CASE/03_grid_convergence/G2_EX240_grid_convergence/scripts/postprocess_grid.py`、`STEP3_PROTOCOL.md`。
- 被复核报告：`docs/reports/Celik_GCI_verification_20261027/REPORT.md`；旧独立审查：`docs/reports/reviewer_numerics_20261018_v1/REPORT.md:112`已记录同一比值退化。
- [ASME官方方法文稿](https://www.asme.org/wwwasmeorg/media/resourcefiles/shop/journals/jfenumaccuracy.pdf)，本轮读取并核原始公式页面。
- 使用peer-review、scientific-writing与pdf技能；流程来源仅列本审查报告，不加入CFD论文方法引文：Kassis, T., Agarwal, V., He, Y., Patel, D., & Brueckner, A. M. (2026). Scientific Agent Skills: A Library of Procedural Knowledge for Research Agents. [arXiv:2609.00065](https://doi.org/10.48550/arXiv.2609.00065)。本轮在线核对作者及当前版本记录。

验证：`recomputed.json`保留9项既有标量记录与6行独立算术；`verification.json`记录归档p/GCI一致、比值恒等容差及27份实际读取输入的SHA不变。该检查不是重新验收9次运行的全部原始场或质量时间序列，不扩大为新物理验证。

# 引言第二段：局部立方律、两种平均与无需拟合

日期：2026-11-07。用户要求审读引言第二段，本轮只核对应表述、已有方法来源和原公式代数，形成候选。未改正式引言，前轮已合入摘要保持。

## 原段

> 对平行线槽，最常用的做法是局部立方律：把每一处局部高度当作一段独立的平行平板通道，其导度按 $h^3/12$ 计算；沿槽方向把深槽与浅凸台的导度作算术平均，跨槽方向作调和平均。这一处理简洁、无需拟合、只依赖几何，因而被广泛采用。

## 审读判断

原公式及沿槽算术/横槽调和的方向正确。应澄清：

- “最常用/广泛采用”是采用频率判断，现有来源足以支持介绍该构造，不必使用排他/频率措辞。
- $h$在本文特指凸台下的残余间隙，局部总间隙宜写$H$；浅区H=h，深区H=h+d。局部深度积分导度为k(H)=H³/12，单位m³；与通常以m²计的渗透率不同。不改h³的物理指数，只消除符号混同。
- 有导度的是深区与凸台下浅区的液体，“浅凸台的导度”易误解为固体也承载流量。
- 算术/调和平均是局部平板组合近似内的并联/串联关系，不是从全Stokes解测出了阻力份额。沿槽的权重来自横向宽度占比；横槽来自沿流动方向交替段的长度占比；本文两者均为1/2，不用流体体积比例替代。
- “无需拟合”限定原始局部立方律：在本文牛顿流体、无滑移等条件及导度定义下，用几何即可算原式，不含由流动数据标定的经验系数。它仍有局部平板假设，不能据无经验参数判定精确；V2另有数据确定的乘性修正系数，不适用这一措辞。

## 平均关系

令ks=h³/12，kd=(h+d)³/12，本文等宽情况下：

- 沿槽Kyy_LC=(ks+kd)/2。
- 横槽Kxx_LC=[(1/2)/ks+(1/2)/kd]⁻¹=2kskd/(ks+kd)。

它们正好化为正文式（3）。本轮按既有5 nm主表36行几何代入这两种平均，与保存原式值一致，差别仅浮点舍入；详见algebra_check.json。不是新的CFD计算、模型精度证明或新物理验证。

在局部模型中，沿槽深浅区域承受共同的沿槽压力梯度，宽度平均其通量，得到算术平均；横槽各交替段承载相同的稳态深度积分通量，将压力降相加得到阻力平均，故对导度取调和平均。真实台阶流动的侧壁与连接耦合正是后续评价对象，不提前据这一电路类比确定耗散或阻力分区。

方法来源沿用正文[4] Patir–Cheng及补充S6、S11；已有原文核对定位印刷第15页式（23）（24），先还原其归一化高度才能与本稿K定义比较。本轮读取已有指定页核对报告，不冒称本轮重新打开/渲染原PDF或完成新的全文审查。没有引入新文献身份。

## 中文候选

> 对平行线槽，可用局部立方律近似构造等效导度：在牛顿流体和无滑移假设下，将局部间隙H视为独立平行平板通道，其深度积分导度为H³/12。在这一组合中，沿槽按并联关系取局部导度的宽度加权算术平均，横槽按串联关系取长度加权调和平均[4]；本文槽与凸台等宽，两区权重均为1/2。该原始公式由几何及局部平板关系确定，不含通过流动数据标定的经验系数。

## 英文对应候选

> For parallel grooves, the local cubic law approximates effective conductance by treating each local gap H as an independent parallel-plate channel with depth-integrated conductance H³/12 under Newtonian and no-slip assumptions. In this construction, a parallel combination gives the width-weighted arithmetic mean along the grooves, whereas a series combination gives the length-weighted harmonic mean across them [4]. Grooves and ribs have equal widths here, giving weights of 1/2. The original relation follows from geometry and the local-plate model without coefficients calibrated to flow data.

引言候选介绍定义和选择，不放展开的两条主公式或证明；完整符号、单位及式（3）仍在方法章。下一段可据此引出该组合没有显式解析的作用及需评价的条件，但本轮不提前审改第三段。

## 停点

第一、二段候选均未合入，正式双语摘要与正文保持。本轮五项输入受保护，只新增本目录及两状态，无新仿真run_id、求解、拟合、数值/理论接受、上传或投稿；历史FAIL、参考和投稿资格不变。使用scientific-writing与academic-humanizer已读流程，来源记录沿用前轮修订报告，不作为独立科学证据。

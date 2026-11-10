# Alpha参数化与C粗网格耦合诊断执行协议 v1

协议ID：ALPHA_C_DIAGNOSTICS_20261022_v1。2026-10-22。
本文件与protocol.json共同在正式空间推进前冻结，由evidence/build_binding.json绑定。准备中可修复编译/输出错误，须保留失败记录；冻结后不按轨迹改参数、阈值或分析窗口。

## 范围、依赖与人工接续

本次授权为独立实现、编译核查和冻结协议。准备阶段允许真实CellD局部碰撞、静态代数/合成数据检查、--initialize-only零步初始化；**没有任何新正式空间推进**。

- alpha阶段：10组同物理域线性扩散、4组实际本构短扩散、2组源项单步，共16组。用户独立启动；完成后另行分析。
- C阶段：4组64³/64步完整NS/CH耦合收支诊断。程序已准备，但runner须见alpha阶段完整冻结验收通过且证据哈希一致，才接受用户单独启动C。程序不自动串联两阶段，不自动分析或启动下一Gate。
- C细网格、alpha16空间细化、D约束平衡、Laplace、润湿、移动壁、沟槽K与真实GHY预测均不在本执行范围。三类正式Gate保持NOT_EVALUATED。

所有空间运行单MPI进程、CPU_SISD、D3Q19、全周期、核心坐标0..N−1、overlap3。无壁面，不能据此获得壁面geometry_PASS。

## 1. 局部实现与准备验收

共享OpenLB代码/库不改。dimension_corrected_ch.h与旧A+B文件逐字节相同，保留三维修正源项系数

\[
b_i=w_i[-(d+2)/2+(c_i\cdot c_i)/(2c_s^2)].
\]

新增CH专用CH_ALPHA字段，冻结为每个运行的均匀常数。新平衡分布：

\[
f_0^{eq}=\phi-(1-w_0)\alpha\mu-w_0,
\quad f_{i>0}^{eq}=w_i\alpha\mu-w_i.
\]

CHEM_POTENTIAL字段始终保留原mu，原NS耦合继续用−phi Gmu；不得全局缩放mu。新类型无专用CSE，明确采用通用fallback，编译静态断言与配置记录共同检查。

CH实际CellD矩阵：D2Q9/D3Q19；alpha=1/4/16；tau=.6/1/1.4/2.5；phi=.1/.5/.9；mu=−.004/0/.003；S=−.0002/0/.0002；平衡/零和非平衡。检查独立分布公式、通用/CSE-fallback一致、源零一二阶矩、alpha1对旧正确源项实现回归、mu字段未被修改。绝对限1e-12。

NS实际CellD矩阵：延用旧A1输入公式，tau端点改为1/1.25，rho=.0012/.1/1；含正负/零力、平衡/非平衡和微小raw速度置零分支；压力.0007。检查独立分布、压力恢复、半步力速度、raw动量增量及置零修正；绝对限1e-12。该矩阵是局部代数验证，不是空间输运通过。

## 2. Alpha空间矩阵与固定迁移率

逐项ID/参数/步数以protocol.json为准，配置编译进src/alpha_configs.h，CLI不接受自由改步数或物性。

线性10组：N16/32，每格5波矢x/y/z/xy/xyz，即(1,0,0)/(0,1,0)/(0,0,1)/(1,1,0)/(1,1,1)。物理域各40nm，dx2.5/1.25nm、dt1.0416666667e-13/2.6041666667e-14s，alpha1/4，tau_CH均1；W物理10nm（4/8格）、sigma_SI=.03N/m。beta*=6.25e-5/1.5625e-5，kappa*=1.25e-4保持。M_SI均1.7361111111e-17m²/(Pa·s)，为模型输入非实测。

线性化中心phi0=.1、振幅1e-3，mu=a(phi−phi0)−kappa Lphi，a=f0''(.1)=.46beta。粗/细128/512步，同物理时长。u、S均0。

实际非线性4组：N16/32各中心.1/.9、振幅1e-4、x波矢；原ChemPotentialPhaseFieldProcessor，ADDEND0，粗/细16/64步，分别用上述实际sigma/W；u、S均0。每一步保存完整phi/mu及字段CSV，不以线性指数替代非线性真解。

源项单步2组：N8、alpha1/4、tau1，其余格子参数用粗格主值。phi=.35+.08cos(X+.31)+.04sin(Y+.2)+.02cos(X+Y+.7)，u=.01Gphi，S=u·Gphi，S_old=S_initial，SOURCE=S。两组仅检验系数/迁移位置，**不是同物理M细化**。保存初始/碰撞后/迁移后/刷新后的全部19分布与字段。

独立参考：numerical_reference.py按实际OpenLB描述子顺序重建19×19完整传播矩阵，初始19个分布模态由实际数据另算；tau1用g=1−alpha Lambda(a+kappa Lambda)/6交叉验证。reference/曲线只用于观测L2，不影响求解器演化。

运行前静态参考已确认粗格xyz的连续率偏差约6.215%、细格约1.594%。因此本轮**独立协议**预定粗/细连续率限7%/2%，不继承或修改旧B1的人造系数5%/2%门槛；此为测试点离散精度限，非K误差预算或正式物理Gate。

Alpha验收：

- 完整步数、配置、有限值、节点/坐标、独立退出码/manifest与绑定齐备。
- 线性全程复模态误差/A≤1e-8；全程观测场L2/初始RMS≤1e-8，3D初末场独立重算。未逐步保存线性全场，不冒称全程独立3D重建。
- 固定拟合窗ceil(.25*steps)..steps，实测率相对同窗离散参考≤1e-4；连续率粗≤7%、细≤2%；五方向细化误差下降；轴向归一化率spread≤.002。两网格不称GCI。
- 无源组全程最大相量相对漂移≤1e-9，最大值/发生步/末态分别报告。
- 非线性每步全场mu与精确更新Delta phi=(alpha/6)Lmu误差≤1e-12；链接能量定义和有限步余项重算，能量余额/节点≤1e-12。
- 单步源项组：逐分布碰撞、周期迁移、逐点phi更新及(DeltaQ+sum(SOURCE))/N³绝对残差均≤1e-12。局部公式使用sum_i b_i SOURCE(x−c_i)，不用点上−S替代。允许预期的非零DeltaQ，不列入无源守恒漂移。

Alpha安全停止：分布/字段有限、phi在[.05,.95]、无源相量漂移≤1e-6；安全退出不等于满足1e-9验收限。源项单步不机械套用Q不变。

## 3. C粗网格参数与初态

4组ID：C_equal_mu0、C_equal_constitutive、C_target_mu0、C_target_constitutive。64³、dx2.5nm、L160nm，64步；dt1.0416666667e-13s，共6.6666666667e-12s。CH tau1/alpha1，sigma*=2.0833333333e-5、W4、beta*=6.25e-5、kappa*=1.25e-4。

equal的rho端点[1,1]，target为[1,.0012]；NS tau端点均[1,1.25]。保持的是运动黏度端点，equal的phi1端动力黏度为.015Pa·s，不是保持气体动力黏度的密度单变量对照。mu0组人工强制mu=0，为零力保持控制，不是假称自由能平衡；constitutive组用实际离散本构。

初态按上轮C_PARAMETER_PLAN.md：液片中心x=L/2、a0约40nm，小扰动

\[
a(y,z)=a_0+1\mathrm{nm}[\sin(2\pi y/L+.37)\cos(2\pi z/L+.19)+.25\cos(4\pi y/L+.23)],
\quad\phi=.5[1+\tanh(2(|x-L/2|-a)/10\mathrm{nm})].
\]

初始化前二分a0使离散mean(phi)=.5；运行中不截断phi、不补相量、不设密度下限。初始化分布舍入造成约1e-16量级相量差须原样记录。NS初始raw j=0、构造分布用p_h=0；随后耦合会产生半步力速度和恢复压力，不能仍声称报告u/p均为零。CH平衡分布用该组真实mu或mu0。

时间层冻结：初始化缓存刷新→mu→CH平衡分布→缓存/mu刷新→恰一次耦合→初始化专用SOURCE=S_old=S0。此后每步：保存旧状态→NS/CH实际collide→逐分布检查→各AndStream→迁移检查→检查预测rho>0→刷新phi缓存/mu→恰一次耦合生成下一步SOURCE→测量/保存。测量不重复调用会改S_old的耦合。

## 4. C证据与实现收支

每步0..64保存history和完整16字段三维gzip二进制，列、形状/字节序在frame_schema.json；坐标顺序(x,y,z,field)，小端float64，最后维16：phi,mu,SOURCE,SOURCE_OLD,u3,raw-j3,F3,p_h,rho,tau。SOURCE_OLD是当前物理S_n，SOURCE是下一碰撞使用的AB值。固定命名快照0/1/16/32/64已包含于全程字段，不另复制CSV。

额外第1步保存38列NS/CH完整分布：step1_pre、step1_post_collision、step1_post_stream，列为ns_f0..18,ch_f0..18。后处理独立重算该步完整碰撞/迁移；其他步保留程序分阶段最大残差及每步全场，可独立核宏观收支，**不能冒称所有步完整分布均离线复核**。

实现合同（每步/全程最大值）：

- rho/tau映射、mu本构、F=−phi Gmu、S=u·Gphi、AB与启动规则、带半步力速度恢复，绝对误差≤1e-12。
- CH碰撞/迁移分布、逐节点精确一步式误差≤1e-12；相量总账(DeltaQ+sum(SOURCE_old_frame))/N³≤1e-12。
- NS实际分布独立式/迁移误差≤1e-12。令cut=rho[snapped(j/rho)−j/rho]，snap阈值为既有1e-15，则raw J增量扣sum(F)+sum(omega*cut)后，每节点残差≤1e-12。
- P=sum(rho u)=J+sum(cut)+sum(F)/2。P增量扣半步前后力的梯形和、旧sum(omega*cut)、新旧sum(cut)差后，每节点残差≤1e-12。
- 全程字段/分布有限、rho>0、Mach<.05；mu0控制的局部phi变化和速度≤1e-12。

物理相量/插值质量诊断分别要求全程最大相对漂移≤1e-9。即使上述实现账闭合，超限仍须报告物理预算未满足；equal组mass恒定不能掩盖Q变化。不用末态代替全程峰值，也不把可解释漂移改称守恒通过。

**运行前已知预警**：由独立零步全场重算S0，再用DeltaQ=−sum(SOURCE)代数预测，equal/target真实本构组首步相量相对变化分别约−2.36935425e-9 / +8.29233009e-9，预计已超过1e-9；人工mu0组为0。evidence/c_initial_budget_forecast.json明确标记非实测首步、没有时间积分。本轮保留参数/阈值，C用于检验实际全耦合收支及漂移来源，不能承诺物理守恒通过。不能在结果出来后以“已被源项解释”豁免物理预算。

## 5. 能量分账及解释边界

Fh=sum[f0−kappa phi Lphi/2]，D=−M<mu,Lmu>，M=1/6。对旧状态计算source迁移工作Wsrc=<mu,sum b_i SOURCE(x−c_i)>，实际Wmu=<mu,Delta phi>，Rtime=DeltaF−Wmu。实现余额(DeltaF+D−Wsrc−Rtime)/N³绝对限1e-12；是精确离散收支检查，不是完整热力学耗散定理。

另外分列当前对流功−<mu,S>、AB对流功−<mu,SOURCE>、源项迁移修正、毛细功<u,Fcap>、动能、梯度估计黏性耗散和动能差额。条件性质量扩散项Jrho=−(rho1−rho0)M Gmu及相应动能项只记量级；未证明NS含匹配的扩散动量通量，不强设这些物理余项为零或总能量逐步单调。mu0控制不能当作本构自由能平衡证据。

C的实现合同、物理量漂移预算、安全性分别报告。64步不能证明平衡/压力收敛，不能提取K或给第二篇充分性结论。

## 6. 冻结、完成证据与失败保留

每阶段独立batch_id/run_id、完整日志、全部参数/config/result、独立退出码、运行前后绑定哈希。阶段所有规定算例完成且输入未变才能验收。runner默认预查，--run才执行；不覆盖/恢复/重试、不自动后处理/下一阶段。

冻结绑定含源码、OpenLB全src树/版本/库/配置、新二进制、协议、参考、分析/runner与准备报告。第一篇可能并行更新的共享入口不加入运行绑定，以本目录准备报告快照为准。

旧A/B与实际谱审查的3045项去重输入保护；初次CH局部别名冲突、C统计函数命名冲突与静态参考矩阵形状错误等准备失败记录保留。初次验证器遇到并行第一篇入口更新，已改为记录快照而非覆盖最新内容；不涉及科学门槛改变。

Alpha预计证据预留3GiB，C预留12GiB；C每步字段加首步分布的原始未压缩数据约9.68GB，gzip后大小取决于实际结果。未实测正式推进耗时，不沿用旧球滴成本作承诺。

方法前置来源：`../actual_mobility_review_20261022/REVIEW.md`、`../ab_diffusion_validation_20261022/PROTOCOL.md`与本机源码。原alpha公式出处Ju等预印本：https://arxiv.org/pdf/2311.10827v1 ，Eqs2.17/2.27；本轮未重做文献推导。主材料全是模型输入，非GHY实测。

# 槽宽、间隙和槽深修正关系：方程推导、具体相关式及适用边界

2026-10-23。对象：充分充液、固定间隙、单相牛顿液体、无滑移、周期矩形直槽；沿槽y/P、横槽x/T。用户要求把修正系数写成w、h、d的关系式并说明如何推出。本文件是可供老师逐式核查的推导说明，数学推理与AI数值复核不代替老师的独立审核。

**本轮结论：从Stokes方程可严格推出自变量、长度三次齐次性及理想模型下的物理边界；以既有C4系数可立即给出显式F(w,h,d)。C4的具体四项函数形式和数值系数属于既有数据的经验闭合，不能冒称为完整流动方程的精确闭式解。** 不重新拟合，不启动OpenLB，不修改V2/C4、原始结果或冻结许可，不生成最终model_lock。

## 1　先固定物理量与几何

h为凸台下最小间隙，d为槽深，w为槽宽，P为周期，φ=w/P。源几何局部高度H(x)取h或h+d，沟槽沿y无限/周期延伸。当前资料和相关式均φ=.5、P=2w；固定周期改变w会改变φ，不能套用同一组系数。

驱动强度G=ρa，单位Pa/m；压力写成宏观线性部分加周期扰动。项目定义

\[
 J_i=\frac{1}{PL_y}\int_\Omega u_i\,dV,
 \qquad K_i=\frac{\mu J_i}{G},
 \qquad R_i=\frac{G}{J_i}=\frac{\mu}{K_i}.
 \tag{1}
\]

J的单位m²/s，K的单位m³，R的单位Pa·s/m³。这里的K是深度积分导度，不能混成单位m²的Darcy渗透率。源位置：D2/src/d2_groove_error_map.cpp第38—41行面积/体积定义、第515行通量归一化、第802—804行K与R。不得以单胞周期扰动压力最大减最小替代G。

## 2　由控制方程推出变量与相似性

在可忽略惯性的连续介质近似中，

\[
 -\nabla p'+\mu\nabla^2\mathbf u+G\mathbf e_i=0,
 \qquad\nabla\cdot\mathbf u=0.
 \tag{2}
\]

壁面u=0，x/y周期。取间隙h作为特征长度：

\[
 \mathbf x=h\hat{\mathbf x},\quad
 \mathbf u=\frac{Gh^2}{\mu}\hat{\mathbf u},\quad
 p'=Gh\hat p,
 \qquad s=\frac wh,\quad t=\frac dh.
 \tag{3}
\]

代入(2)后G、μ及绝对长度消失，剩余无量纲几何为s、t和φ。沿槽均匀性还使L_y在通量归一化中消去。由体积分再多出一个长度因子，得到

\[
 \boxed{K_i=h^3\,\kappa_i(s,t;\phi)}.
 \tag{4}
\]

同一结论可写成K_i=w³\tilde\kappa_i(h/w,d/w;φ)。在同一φ、边界条件和Stokes模型内，

\[
 K_i(\lambda w,\lambda h,\lambda d)=\lambda^3K_i(w,h,d).
 \tag{5}
\]

这是方程推出的相似关系。若考虑惯性、固定物理滑移长度、非牛顿本构、界面或可压缩性，则可能需要额外无量纲参数；本说明未证明这些扩展仍满足(4)—(5)。沿槽完全发展的单向速度会消去对流项；横槽的Stokes近似仍须以低Re和驱动力响应证据支持，不能仅用低Mach替代。

**固定w的数据并不自动缺少二维信息。** 令α=h/w、β=d/w，在固定w=w0时，(h,d)→(α,β)的Jacobian为diag(1/w0,1/w0)，秩为2。现有h、d变化已经采样二维比例函数。数学上可用于建立候选相关式；改变w的算例用于检验转用、扩展比例域和分辨率影响。此前把“必须先做独立槽宽扫描才能建立双变量关系”作为绝对前提，表述过强。

## 3　从局部立方律得到基准式

局部高度H的平板解为u(z)=Gz(H−z)/(2μ)，深度积分J(H)=GH³/(12μ)。因此沿槽条带并联、横槽条带串联近似为

\[
 K_\parallel^{LC}=\frac{(1-\phi)h^3+\phi(h+d)^3}{12},
 \qquad
 K_\perp^{LC}=\frac{1}{12[(1-\phi)h^{-3}+\phi(h+d)^{-3}]}.
 \tag{6}
\]

在φ=.5时，

\[
 \boxed{K_\parallel^{LC}=\frac{h^3+(h+d)^3}{24}},\qquad
 \boxed{K_\perp^{LC}=\frac{h^3(h+d)^3}{6[h^3+(h+d)^3]}}.
 \tag{7}
\]

式(6)来自局部平板组合；不能把它当成含侧壁和连接段全部流动的精确场解。

定义导度修正F、阻力修正C和超额阻力Δ：

\[
 F_i=\frac{K_i}{K_i^{LC}},\quad
 C_i=\frac{R_i}{R_i^{LC}}=\frac{1}{F_i},\quad
 \Delta_i=C_i-1=\frac{K_i^{LC}}{K_i}-1.
 \tag{8}
\]

故

\[
 \boxed{K_i=\frac{K_i^{LC}}{1+\Delta_i}},\qquad
 \boxed{R_i=\frac{\mu}{K_i^{LC}}(1+\Delta_i)}.
 \tag{9}
\]

LC同样为长度三次齐次式，所以F、C、Δ只依赖s、t、φ。阻力乘1+Δ，导度乘1/(1+Δ)，不能混用。

## 4　给出可以代入w、h、d的具体公式

既有18几何C4对超额阻力的对数采用

\[
 \ln\Delta_i=a_i+b_i\ln\beta+c_i\ln\alpha+q_i(\ln\alpha)^2,
 \quad \alpha=h/w,\ \beta=d/w.
 \tag{10}
\]

其系数来自2026-10-22的回顾性拟合，18个P点和18个T点分别拟合。本轮没有重新估计系数。这个四项选择是经验近似：既不等同完整二阶Taylor展开（还缺交叉项、ln²β），也不是由Stokes方程唯一强制的函数形式。

用β=t/s、α=1/s代换并整理，严格代数等价地得到

\[
 \boxed{\Delta_i(s,t)=A_i\,t^{b_i}s^{-p_i}
          \exp[-r_i(\ln s)^2]},
 \quad A_i=e^{a_i},\ p_i=b_i+c_i,\ r_i=-q_i.
 \tag{11}
\]

因此所需的明确修正式为

\[
 \boxed{F_i(w,h,d)=
 \left[1+A_i\left(\frac dh\right)^{b_i}
 \left(\frac hw\right)^{p_i}
 \exp\!\left\{-r_i\left[\ln\left(\frac wh\right)\right]^2\right\}\right]^{-1}}.
 \tag{12}
\]

|方向i|A_i|b_i|p_i|r_i|
|---|---:|---:|---:|---:|
|沿槽∥（P/y）|1.439322109362748|1.5996745971805324|0.9067146568707773|0.28288991331900903|
|横槽⊥（T/x）|0.5282632943141873|0.7768339511443813|0.5411597594375912|0.4708598723288494|

把(12)代入(7)、(9)，就是同时输入w、h、d，输出两方向K或R的连续公式。没有逐算例独立系数，也没有人造固定断点。w、h、d必须使用同一长度单位；K计算使用米才直接得到m³。原C4与H4的比较未发现两段式稳定优势，本轮不把61.24nm称为物理临界。

例：w120/h75/d100nm时，F_P≈.4168496538、F_T≈.6841783250；候选K_P≈1.0041300255e−22m³、K_T≈4.4595829589e−23m³。这是已有C4的计算值，不是新增DNS结果。

## 5　由方程得到物理约束，检查相关式是否越界

以下是理想Stokes、周期、无滑移和充分充液模型下的能量推导，适用范围不包括所有真实工艺。将z截面写为D={(x,z):0<x<P,0<z<H(x)}，定义I_i(v)=∫_D v_i dA、E(v)=∫_D|∇v|²dA。对应的单位驱动弱解满足a(U,v)=I_i(v)。由Cauchy–Schwarz及等号在U处成立，

\[
 K_i=\frac1P\sup_{v\in V_i,\ v\ne0}
       \frac{I_i(v)^2}{E(v)}.
 \tag{13}
\]

V_P是沿槽标量H¹无滑移/周期速度空间；V_T是横槽二维无散矢量空间。式(13)是一个精确变分表示，但仍包含几何域上的极值，不是简单的四系数闭式公式。

对每个x，令q(x)=∫_0^{H(x)}v_i dz。垂直方向的平板最小能量不等式给出

\[
 \int_0^{H(x)}(\partial_z v_i)^2 dz\ge\frac{12q(x)^2}{H(x)^3}.
 \tag{14}
\]

沿槽再用加权Cauchy–Schwarz可得E≥12I²/∫H³dx；横槽则由不可压缩与无穿透得q(x)恒定，故E≥12q²∫H⁻³dx。代入(13)分别给出K_P≤K_P^LC、K_T≤K_T^LC。

全域包含0<z<h的平板流体层。将平板Poiseuille试探速度在该层之外延拓为0，仍满足无滑移、周期及横槽无散约束；代入(13)即得K_i≥h³/12。因此

\[
 \boxed{\frac{h^3}{12}\le K_i\le K_i^{LC}},\qquad
 \boxed{\frac{h^3/12}{K_i^{LC}}\le F_i\le1}.
 \tag{15}
\]

进一步，将横槽试探速度的u_x分量放宽为沿槽标量试探函数并丢弃额外的u_z耗散，可得K_T≤K_P。以上是本轮给出的可审查推理，不以已有数据的符合替代证明，也不自动改写既有研究结论或数值Gate；矩形台阶在弱形式中按Lipschitz域与H¹函数处理。任意初始未稳态、有限惯性/可压缩离散结果不能不加限定地沿用这些理想模型约束。

**C4满足正值和F≤1，并不自动满足(15)的下界。** 现有36样点及比例域内12756个方向/位置扫描未发现下界违反（有限检查，不是整个域内的严格证明）；但h75/w120/d10000nm时，横槽C4给K约为平板值的.11417，违反下界。这证明它不能作为任意槽深的全域公式。极浅槽也有域外反例。程序默认拒绝超出原比例包络的输入，未用裁剪/删点掩盖这个问题。

若老师要求全域满足边界，可以把下一轮闭合目标改写为

\[
 K_i=K_{flat}+\frac{K_i^{LC}-K_{flat}}{1+\Psi_i(s,t)},\quad\Psi_i\ge0,
 \tag{16}
\]

其中K_flat=h³/12。这在结构上满足(15)，但Ψ的具体形状和系数尚未拟合/验证；不能把(16)的结构约束称为新模型已完成。沿槽和横槽的深槽极限还需分别处理，不能共同假设K随深度必然饱和。

## 6　适用范围应写成比例域

现有数据w120/P240，h25/50/75/125nm，d25/50/75/100/120nm（h25缺d75、120）。其外包矩形为

\[
 5/24\le\alpha=h/w\le25/24,\qquad5/24\le\beta=d/w\le1.
 \tag{17}
\]

外包矩形不等于整个矩形已验证。代码采用lnα、lnβ平面中原18点的凸包作为保守内插筛选；顶点对应(α,β)：(5/24,5/24)、(25/24,5/24)、(25/24,1)、(5/12,1)、(5/24,5/6)。凸包内部也不自动具有误差保证。

w变化时，可用相似映射h0=120h/w、d0=120d/w（长度以nm计）定位原比例域。例如w240/h75/d120映射到原w120/h37.5/d60的比例位置，属于现有包络内插；并非已有h37.5/d60的DNS记录。新开发8几何中3个落在旧包络内、5个在外，详见domain_screen_new_dev.csv。因此：现有数据足以建立候选二维关系；扩大到新开发的整个候选范围，仍有实际的比例外推和验证任务，不能借相似性跳过。

## 7　本轮完成与未完成

- 已完成：方程无量纲化和三次相似关系；LC基准与导度/阻力修正倒数关系；C4的Gap尺度显式代换；原36点/64输入保护复核；比例域、SI/nm单位、缩放代数和物理边界检查。改写公式与存档C4相对差最大1.11e−15。没有重拟合或新流场求解。
- 既有全数据回顾性拟合误差：沿槽MAE1.6483%、最大7.6502%；横槽MAE2.1010%、最大4.5249%。既有整层留h C4 MAE2.1201%/2.6006%，整层留d2.2054%/3.4787%；留d沿槽最坏12.9364%。这些是同一批数据的回顾性检查，不能写成所有新槽宽的误差界。
- 未完成：有限四系数形式从完整场方程的唯一严格推导、全参数域极限闭合、改变φ、独立新几何和新宽度验证、全域网格独立性。对(13)—(15)的完整形式推理已写出，但尚无独立人工/同行复核，不据此自动升级发表或项目Gate。
- 下一条动作应先让老师核对(12)是否满足其“correlation公式”的目标，或是否要求进一步的场级级数解；不是自动启动全部扩展计算。已有首6项许可保持原样，本轮不执行，也不把本候选改为最终model_lock。

可计算工具：dimensionless_correlation.py和coefficients_and_domain.json。复核：先运行build_parameters.py（仅提取原系数），再运行derive_and_check.py。默认使用nm输入，K输出m³；完整证据checks.json、recomputed36.csv、input_hashes.json。资料以独立推导目录追加到共享包；不改写原V2/C4文件，实际上传版本以共享Git记录及项目交接为准。

## 8　来源与辅助工具

[E1] 项目源定义：CASE/D_series/D2_groove_error_map/src/d2_groove_error_map.cpp；本轮64项保护/原36份result定位见input_hashes.json、recomputed36.csv。

[E2] 既有模型及统计：docs/reports/bivariate_piecewise_comparison_20261022/PROTOCOL.md、FORMULAS.md、fits.json、full_fit_predictions.csv、full_fit_summary.csv、cv_summary.csv；本轮只读，不修改。

[E3] Mortensen, N. A., Okkels, F., & Bruus, H. (2005). Reexamination of Hagen–Poiseuille flow: Shape dependence of the hydraulic resistance in microchannels. Physical Review E, 71, 057301. https://doi.org/10.1103/PhysRevE.71.057301 。作者公开记录https://arxiv.org/abs/physics/0412015于本轮核对。用于流道几何与Poiseuille导度框架背景，不作为本项目C4系数来源。

[E4] Dewangan, M. K., & Datta, S. (2020). Effective permeability tensor of confined flows with wall grooves of arbitrary shape. Journal of Fluid Mechanics, 891, A12. https://doi.org/10.1017/jfm.2020.134 。本轮查阅出版社全文https://www.cambridge.org/core/journals/journal-of-fluid-mechanics/article/089D6608B5CF065BAC9B1C4F7D42FBCF ，其谱/摄动理论有小图案尺度等条件；不把该近似的张量关系直接当成本矩形槽全域精确式。

辅助工具采用scientific-writing技能组织证据与限定。相关程序库引用：Kassis, T., Agarwal, V., He, Y., Patel, D., & Brueckner, A. M. (2026). Scientific Agent Skills: A Library of Procedural Knowledge for Research Agents. arXiv:2609.00065. https://doi.org/10.48550/arXiv.2609.00065 。本轮核对当前记录为2026-09-02修订的v2；引用采用无版本后缀的当前记录。该文不是流体公式的理论来源。

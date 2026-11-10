# 导度—阻力接口说明

日期：2026-10-30。**定义与条件性换算草案；不是最终理论冻结、OpenFOAM 字典或数值放行。**

## 1. 先统一量的含义

现行稿件§2.2及 D2 当前源码给出：

\[
J_i=\frac{1}{A_{\rm plan}}\int_{\Omega_f}u_i\,dV,
\qquad K_i=\frac{\mu J_i}{G_i},\qquad G_i=\rho a_i.
\]

速度先在流体体积内积分，再除以平面面积得到 J（m²/s），最后乘 μ 并除驱动 G（Pa/m）得到 K（m³）。材料1流体域与周期 core-cell 的积分范围按原源码；固体速度不作为液体流量。当前源码仅是定义证据，不自动证明历史可执行文件来源已闭合。

在宏观压力模型中，沿用深度积分面内通量 J 的符号（其他报告也写 q），不是直接将 J 当平均速度：

\[
\mathbf J=-\frac{\mathbf K}{\mu}\nabla p_g,
\quad p_g=p-p_b,\quad \mathbf G=-\nabla p_g.
\]

因此正驱动 G 应得到同向通量；不要把额外的 μ 再乘进 K，也不要将 ρa 与压力梯度重复施加。

|量|符号|单位|
|---|---|---|
|深度积分通量|J|m²/s|
|液体体积平均速度|Ubar|m/s|
|深度积分导度|K|m³|
|按所选平均定义的渗透率|κ|m²|
|面内通量阻力系数|μK⁻¹|Pa·s/m³|
|Darcy 系数张量（本说明记 D，避免与槽深混淆）|D|m⁻²|
|挤压载荷/速度|R_sq|N·s/m|

最后三项不具有同一单位；尤其旧 result.txt 的 `R_eff_Pa_s_per_m3=μ/K` 不是 OpenFOAM 直接要求的 D。

## 2. 125 nm 的平均厚度来自哪里

对完整等宽周期，流体体积/平面面积为

\[
H_{\rm store}=\frac{|\Omega_f|}{A_{\rm plan}}=h+\phi_g d_g,
\quad \phi_g=\frac{w}{P}=\frac12.
\]

基准 h=75 nm、d_g=100 nm，故 H_store=125 nm；槽顶包络高度为 H_env=175 nm。两个原始 result.txt 都记录 H_ref≈125 nm，按记录流体体积/平面面积复算也一致至本轮算术检查精度。

本接口优先准备的约定是

\[
\overline{\mathbf U}_{f}=\frac{1}{|\Omega_f|}\int_{\Omega_f}\mathbf u\,dV,
\qquad \mathbf J=H_{\rm store}\overline{\mathbf U}_{f}.
\]

这使 \(\boldsymbol\kappa=\mathbf K/H_{\rm store}\)。它是“流体体积平均速度”的定义；不表示 OpenFOAM 的任意 cell velocity 已经自动等于它，更不表示可随意把实际计算域厚度改成125 nm并保留所有原壁面条件。

如果采用175 nm包络内的表观平均速度 U_s，则 J=H_env U_s，且 U_s=(H_store/H_env)Ubar_f。该几何中的包络体积流体比为5/7，而槽平面占比是1/2。多孔方程若另带孔隙率因子，还须同时核它的压力项/阻力项；**不能只改 H 或把 0.5 填作体积孔隙率。**有限截断图案也必须实算储液厚度。

## 3. 条件性 K→κ→Darcy 换算

当模型明确采用上述 Ubar_f、相同压力梯度，并让 Darcy 项承担全部未解析平均阻力时，定义

\[
-\nabla p_g=\mu\mathbf D_{\rm total}\overline{\mathbf U}_{f},
\quad \boldsymbol\kappa=\mathbf K/H_{\rm store},
\quad \mathbf D_{\rm total}=H_{\rm store}\mathbf K^{-1}.
\]

主轴上是 \(D_\parallel=H_{\rm store}/K_\parallel\)、\(D_\perp=H_{\rm store}/K_\perp\)。单位检验为 m/m³=m⁻²。

OpenFOAM Foundation 13 官方 DarcyForchheimer 源项为

\[
\mathbf S=-\left(\mu\mathbf D+\frac{\rho|\mathbf U|}{2}\mathbf F\right)\mathbf U.
\]

D 的单位为 m⁻²，Forchheimer 系数 F 为 m⁻¹。拟先检查低惯性线性关系，因此面内 F 候选为零。以每体积动量方程记源时 Darcy 阻力是 −μDU；若方程已除密度，每质量加速度源为 −νDU，ν=μ/ρ。密度不是再乘进 D 的因子。依据：[Foundation 13 DarcyForchheimer 源码说明](https://cpp.openfoam.org/v13/DarcyForchheimer_8H_source.html)及本机对应 H/Templates.C（E09/E10）。

这里只给出面内2×2映射。Dzz、竖向速度约束、厚度实现和完整3D模型未确定，JSON保留 null；不能为了凑三分量字典随意填一个竖向阻力。

### 已解析壁面时，不能再照搬总阻力

有两类不同路线，后续必须明确选定：

- **总阻力平均路线**：用 K 代表包含原沟槽固壁影响的完整面内输运；需要相容的速度/储液/源项定义。上式是它的条件性接口。不能再默认施加一套重复计算同一阻力的上下壁剪切。
- **解析无滑移壁面路线**：计算域显式产生厚度方向剪切，另加阻力只能表示经过审核的剩余影响。不能直接用 `H/K` 当附加阻力，更不能无依据用两个逆导度相减当通用精确公式。若需要负“附加阻力”，须重新检查几何/模型；OpenFOAM负阻力参数还有特殊倍率语义，不能用来任意补偿。

此外，保留面内黏性扩散或惯性项的平均动量方程可能与纯 Reynolds 方程不同；即使 D 已按单位换对，也须检查这些项的影响，不能预设两平台严格相等。参考单层网格不等于已经实现相容的厚度平均理论。

## 4. 原系数与 V2，以及两槽向的张量

仅针对已有等宽基准，使用现行稿件式(3)(6)：

\[
K_\parallel^{\rm mod}=\frac{(h+d_g)^3+h^3}{24},
\quad K_\perp^{\rm mod}=\frac{(h+d_g)^3h^3}{6[(h+d_g)^3+h^3]},
\]
\[
K_i^{\rm V2}=F_i K_i^{\rm mod},\quad
F_\parallel=\frac{1}{1+1.7685(d_g/w)^{1.6331}},\quad
F_\perp=\frac{1}{1+0.4900(d_g/w)^{0.6990}}.
\]

本轮只代入公布舍入系数；不调用拟合程序、不扩大占空比/槽宽适用范围、不称为独立预测。条件性数值见 [COEFFICIENT_EXAMPLES.md](COEFFICIENT_EXAMPLES.md)。

令槽轴单位向量 t=(cosθ,sinθ)，横槽 n=(−sinθ,cosθ)，则

\[
\mathbf K=K_\parallel\mathbf t\mathbf t^{\mathsf T}
+K_\perp\mathbf n\mathbf n^{\mathsf T},
\quad
\mathbf D=H_{\rm store}\left(\frac{\mathbf t\mathbf t^{\mathsf T}}{K_\parallel}
+\frac{\mathbf n\mathbf n^{\mathsf T}}{K_\perp}\right).
\]

θ从固定全局+x量起；槽沿长边y时θ=90°，Kxx=K_perp、Kyy=K_parallel；槽沿短边x时θ=0°，两主值在全局x/y交换。不能旋转 K 而把 D 留在原坐标。一般非对角张量要取矩阵逆，不能逐元素倒数；本轮只准备0°/90°，没有新增斜向算例。

## 5. 静态接口检查与瞬时挤压的方程符号

先准备定间隙静态检查：V=0、选择一个方向的 G，候选恒系数平均关系为 J=(K/μ)G，Ubar=J/H_store。可检查 H_store Ubar 是否还原 J。有限边缘或额外黏性项存在时，不能将均匀代数式强当所有位置的精确解；应选择与所核关系相容的边界。驱动大小与停止门槛尚未定，本轮不求解。

对刚性均匀闭合，深度积分守恒为

\[
\frac{\partial H_{\rm store}}{\partial t}+\nabla\cdot\mathbf J=0,
\quad \partial_tH_{\rm store}=-V,
\quad -\nabla\cdot(\mathbf K\nabla p_g)=\mu V.
\]

因此恒系数主轴表达的二阶导数和应为 −μV；正闭合、正导度和零边缘过压应对应正内部过压。现行稿件式(7)与此一致；旧 D3 脚本用另一符号求解后以 abs 返回载荷幅值，不能原样复制为带符号压力场实现。本轮不改该历史脚本，也不对旧结果作新的物理裁决。

在 J=H_store Ubar 的平均描述下，守恒是 `∂t H_store + div(H_store Ubar)=0`。空间均匀H的瞬时挤压要求 `div Ubar=V/H_store`；固定域中直接施加零散度而不提供相应体积变化，不是同一个挤压问题。可用经过审核的运动几何或相容平均源项实现；其选择尚未定，不能靠修改压力或给位移参数命名来代替。

## 6. 输出换算与需要保留的分项

二维压力阻力先写 `F_p=∫_A p_g dA`、`R_p=F_p/V`。三维应另记录环境压力扣除后的模具总法向力 F_σ（压力与黏性应力分开）；确认作用面、投影面积和符号一致后，才能约定哪个量是主指标 F_net。不能拿一端总力、一端压力积分而不记录差别。

OpenFOAM 的 p 若是动力压力，按 Pa 输出；若选定单相求解器使用运动学压力（m²/s²），须在常密度条件下乘ρ恢复Pa。p_rgh还涉及静水压定义，不能仅按字段名与二维p_g对比。本草案拟关闭重力，但字段单位和环境压力扣除仍须记录。

各边排液量取 `Q_e=∫_edge J·n ds`，四边净和取向外为正。刚性均匀闭合时预期 Q_net=V A；不能将各边绝对值相加掩盖倒流或守恒误差。静态V=0阶段R_sq与方向挤压比不适用，不以除零或零值填充。

## 7. 后续实施前检查清单与科学边界

后续实施协议应明确：同一份共用输入的哈希；原/V2版本；同一全局坐标与旋转；平均速度/厚度；总阻力或解析壁面路线；压力单位/驱动方式；真实闭合体积变化；边缘与力定义；网格/求解精度、资源及预定门槛。当前全部科学 Gate 仍未评价。

接口的初步检查可包含光滑极限、无驱动零流、单向压力驱动恢复K、两主轴交换、闭合时压力符号、体积守恒。前几项是实现核查；实际基准/求解器结果尚不存在，不能用本轮代数恒等式当流动基准已通过。

独立显式沟槽参考需要自己满足来源、几何、边界、精度及守恒检查，且不采用本项目原/V2的等效K作为输入。已有两个局部OpenLB K放入降阶模型只产生第三组系数输入，不是新的显式挤压参照。若修正后不改善或方向比变差，后续也应保留；不通过更改阈值或重新拟合隐藏结果。

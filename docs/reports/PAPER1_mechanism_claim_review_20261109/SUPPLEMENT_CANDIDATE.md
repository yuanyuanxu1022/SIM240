# 机制补充候选 / Mechanism supplement candidate

2026-11-09，未合入正式补充。下列M编号为本模块局部编号；不改变既有附录E或补充S1–S13。作者须随本模块保留逐运行表，不能只采用份额而删去分母和余额。

## 中文：定义与推导

沿用附录E的固定全充液、不可压缩、常黏度牛顿Stokes流、静止无滑移固壁及周期条件。截面Ω在xz平面，槽沿y，周期P=2w，H(x)=h或h+d。令归一化速度为 $\boldsymbol v=\boldsymbol u/J$，单位m⁻¹；它不同于正文闭合速度V和附录E的 $\boldsymbol U=\mu\boldsymbol u/G$。定义

\[
R_{\rm grad}=\frac\mu P\int_\Omega |\nabla\boldsymbol v|^2\,dA,
\quad R_i^{LC}=\mu/K_i^{LC},\quad R=G/J.
\]

在上述连续条件下，Stokes能量关系给出 $R_{\rm grad}=R$。物理耗散采用 $2\mu D:D$；其全域积分等于梯度能量，但两者不逐点相等。

沿槽取 $v=v_y$ 和 $b=z(H-z)/(2K_\parallel^{LC})$。由于 $P^{-1}\int_\Omega v\,dA=1$，沿z分部积分给出 $\int_\Omega v_zb_z\,dA=\int_\Omega b_z^2\,dA=P/K_\parallel^{LC}$，从而

\[
R-R_\parallel^{LC}=\frac\mu P\int_\Omega
\left[(\partial_xv)^2+(\partial_zv-\partial_zb)^2\right]dA.\tag{M1}
\]

第二项为速度剖面的厚度导数偏离，兼含剖面形状与局部通量分配变化。

横槽取 $v=v_x$、$s=v_z$ 和 $c=6z(H-z)/H^3$。无散度及无滑移条件使 $\int_0^{H(x)}v\,dz=1$ 对几乎处处x成立；可由固体内延零后的弱散度条件证明，覆盖台阶。逐列有 $\int v_zc_z\,dz=\int c_z^2\,dz=12/H^3$，故

\[
R-R_\perp^{LC}=\frac\mu P\int_\Omega
\left[(\partial_zv-\partial_zc)^2+(\partial_xv)^2+
(\partial_xs)^2+(\partial_zs)^2\right]dA.\tag{M2}
\]

表中按剖面导数偏离、主速度沿程梯度及垂直速度梯度三组报告，最后一组包括最后两项。不可压缩约束 $\partial_xv=-\partial_zs$ 表明这些组并非独立机制，也非唯一归组。

b与c可在台阶处沿x不连续，推导只使用逐列z导数；它们没有被当成完整Stokes可容许试探场。真实速度仍须满足所有竖壁零迹，弱解有限能量即可，无需角点经典二阶可导。平板极限d=0使右端为零，并恢复 $K=h^3/12$。

## 中文：离散实现与数值界限

以保存的J归一化各末态，按当前诊断脚本构造两种壁邻梯度和节点积分。每个正项除以RLC得s_j，S=Σs_j，驱动差额E=R/RLC−1。份额定义为100s_j/S%，余额为100(S−E)/E%；未把S调整为E。主表取2.5 nm作为两宽度均有的比较档位，同时保留5 nm及窄槽1.25 nm；选择该档位不认证最细网格或连续参考资格。

应变总功率相对输入功的余额使用另一分母Pin，不能与上述额外阻力余额混用。主模板10目标的前者为−0.5803%至+0.00259%；后者5 nm最坏绝对值1.5555%，2.5 nm最坏0.5336%。宽槽仅两档网格，窄槽历史网格目标未通过。两模板份额最大差0.4252个百分点，不是份额误差界。完整原生应力矩功率、两种速度梯度功率及离散散度均保留，避免只展示较小余额。

角点区域按r/h=1/8、1/4、1/2的三种半径报告，并同时给出体积分数。区域功率描述功率位置，不等于相对局部模型的新增阻力，更不提供独立因果贡献。主文不据某一半径称角点主导。

## English: definitions and derivation

We retain the assumptions of Appendix E: a fixed, fully liquid-filled domain; incompressible Newtonian Stokes flow with constant viscosity; stationary no-slip walls; and matched periodic boundaries. The cross-section Ω lies in the xz plane, the groove extends along y, the period is P=2w, and H(x) is h or h+d. Let $\boldsymbol v=\boldsymbol u/J$, with units of m⁻¹, distinct from the closure speed V in the main text and $\boldsymbol U=\mu\boldsymbol u/G$ in Appendix E. Define

\[
R_{\rm grad}=\frac\mu P\int_\Omega |\nabla\boldsymbol v|^2\,dA,
\quad R_i^{LC}=\mu/K_i^{LC},\quad R=G/J.
\]

The continuous Stokes energy balance gives $R_{\rm grad}=R$ under these assumptions. Physical dissipation is $2\mu D:D$; its integral over the full domain equals the gradient energy, although the local densities generally differ.

For along-groove flow, set $v=v_y$ and $b=z(H-z)/(2K_\parallel^{LC})$. Since $P^{-1}\int_\Omega v\,dA=1$, integration by parts in z gives $\int_\Omega v_zb_z\,dA=\int_\Omega b_z^2\,dA=P/K_\parallel^{LC}$. Expanding the square yields Eq. (M1). Its second term measures departure of the thickness derivative of the velocity profile and includes changes in both profile shape and local flux allocation.

For across-groove flow, set $v=v_x$, $s=v_z$, and $c=6z(H-z)/H^3$. Incompressibility and no slip imply $\int_0^{H(x)}v\,dz=1$ for almost every x. This follows from the weak divergence condition after extending the velocity by zero into the solid and therefore includes the steps. Columnwise, $\int v_zc_z\,dz=\int c_z^2\,dz=12/H^3$, which gives Eq. (M2). We report profile-derivative departure, the streamwise gradient of the main velocity, and vertical-velocity gradients as three groups, combining the last two terms into the third group. The incompressibility constraint $\partial_xv=-\partial_zs$ shows that these are neither independent mechanisms nor a unique grouping.

The baselines b and c may be discontinuous in x at steps. The derivation uses only their columnwise z derivatives and does not treat them as admissible velocity fields for the full Stokes problem. The actual velocity retains zero trace on every vertical wall. A finite-energy weak solution suffices; classical second derivatives at the corners are not required. The flat-channel limit d=0 makes the right-hand sides vanish and recovers $K=h^3/12$.

## English: discrete implementation and limitations

Each final state is normalized using its saved J, with the two near-wall derivative treatments and nodal integration implemented in the diagnostic script. Let s_j be each nonnegative term divided by RLC, S=Σs_j, and E=R/RLC−1 be the driving excess. Shares are defined as 100s_j/S%, and the residual is 100(S−E)/E%. S is not adjusted to equal E. The main comparison uses 2.5 nm because it is available for both widths; the 5 nm and narrow-groove 1.25 nm results are retained. This choice does not qualify the comparison as a finest-grid or continuous reference.

The residual of total strain power relative to input power uses a different denominator, Pin, and must not be confused with the excess-resistance residual. For the ten targets under the primary derivative treatment, the former ranges from −0.5803% to +0.00259%; the largest absolute value of the latter is 1.5555% at 5 nm and 0.5336% at 2.5 nm. Only two grids are available for the wide groove, and the historical grid target for the narrow groove was not met. The maximum difference in shares between the two derivative treatments is 0.4252 percentage points; this is not an error bound. Native stress-moment power, both gradient-based power estimates and discrete divergence residuals are retained, rather than selectively reporting the smaller residuals.

Corner neighborhoods are reported for all three radii r/h=1/8, 1/4 and 1/2, together with their volume fractions. Regional power locates dissipation; it is neither the additional resistance omitted by the local model nor an independent causal contribution. No claim of corner dominance is based on a single radius.

## 随文保存的证据 / Accompanying evidence

数据均来自上一轮目录，不复制或改写原CSV。完整运行身份和来源见 [field_checks.csv](../PAPER1_mechanism_offline_20261109/field_checks.csv)；原生与梯度功率见 [power_checks.csv](../PAPER1_mechanism_offline_20261109/power_checks.csv)；正项、份额和绝对差额见 [positive_excess_diagnostic.csv](../PAPER1_mechanism_offline_20261109/positive_excess_diagnostic.csv)；应变六分量见 [strain_components.csv](../PAPER1_mechanism_offline_20261109/strain_components.csv)；三半径区域数据见 [spatial_regions.csv](../PAPER1_mechanism_offline_20261109/spatial_regions.csv)。读取与导数实现见 [diagnose_fields.py](../PAPER1_mechanism_offline_20261109/diagnose_fields.py)，来源绑定见 [source_manifest.json](../PAPER1_mechanism_offline_20261109/source_manifest.json)。本轮压缩核对见 [review_numbers.json](review_numbers.json)。

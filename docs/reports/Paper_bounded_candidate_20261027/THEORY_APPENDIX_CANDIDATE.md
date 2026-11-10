## 附录 E　理想Stokes模型下局部立方律的上界性质（候选）

本附录承接既有终审推导，作者采用待确认。结论只针对以下连续模型，不对本文离散数值参考的误差作保证。

设一个周期的截面为 $\Omega=\{(x,z):0<x<P,\,0<z<H(x)\}$，其中 $H(x)$ 在浅区为 $h$、槽内为 $h+d$，且 $h>0$。沟槽沿 $y$ 方向平移不变。假设液体全充满、不可压缩、牛顿且黏度恒定，固壁静止无滑移，周期面成对匹配；只施加一次均匀驱动 $G\mathbf e_i$，其中 $G>0$，流动满足Stokes方程。沿槽方向 $i=y$ 可用单向标量场，跨槽方向 $i=x$ 用二维不可压缩速度场。

令 $\mathbf U=\mu\mathbf u/G$、$\Pi=p'/G$，其中 $p'$ 为周期压力扰动。此处 $\mathbf U$ 为有量纲的缩放速度，单位m²，与式（7）的闭合速度 $V$ 不同。则

$$
-\Delta\mathbf U+\nabla\Pi=\mathbf e_i,
\qquad\nabla\cdot\mathbf U=0,
\qquad K_i=\frac1P\int_\Omega U_i\,\mathrm dA.
\tag{E1}
$$

弱式取速度本身为测试函数，固壁边界项为零，周期面相互抵消，压力功由不可压缩条件消去，得到

$$
\mathcal D:=\int_\Omega|\nabla\mathbf U|^2\,\mathrm dA
=\int_\Omega U_i\,\mathrm dA=P K_i.
\tag{E2}
$$

对几乎每个 $x$，定义截面积分 $q_i(x)=\int_0^{H(x)}U_i\,\mathrm dz$。两端零壁迹及辅助函数 $\psi=z[H(x)-z]/2$ 给出 $q_i=\int_0^{H(x)}\psi'\partial_zU_i\,\mathrm dz$。由Cauchy–Schwarz不等式及 $\int_0^{H(x)}(\psi')^2\,\mathrm dz=H(x)^3/12$，

$$
\int_0^{H(x)}|\partial_zU_i|^2\,\mathrm dz
\ge\frac{12q_i(x)^2}{H(x)^3}.
\tag{E3}
$$

台阶竖壁位于有限个 $x$ 位置，不影响该几乎处处成立的截面不等式；完整场仍满足竖壁无滑移条件。

沿槽的 $q_y$ 可随 $x$ 改变。对式（E3）积分，并再用加权Cauchy–Schwarz不等式，

$$
P K_\parallel=\mathcal D
\ge\frac{12\left(\int_0^Pq_y\,\mathrm dx\right)^2}
{\int_0^PH^3\,\mathrm dx}
=\frac{12(PK_\parallel)^2}{\int_0^PH^3\,\mathrm dx},
\qquad
K_\parallel\le\frac{\langle H^3\rangle}{12}.
\tag{E4}
$$

跨槽流动的连续性及固壁无穿透条件使 $q_x$ 为常数，由式（E1）有 $q_x=K_\perp$。因此

$$
P K_\perp=\mathcal D\ge12K_\perp^2\int_0^PH^{-3}\,\mathrm dx,
\qquad
K_\perp\le\frac{1}{12\langle H^{-3}\rangle},
\tag{E5}
$$

其中 $\langle f\rangle=P^{-1}\int_0^P f(x)\,\mathrm dx$。对本文等宽槽/凸台，式（E4）和式（E5）的右端分别为正文式（3）的两个局部立方律导度，故

$$
K_{yy}\le K_{yy}^{\rm mod},
\qquad K_{xx}\le K_{xx}^{\rm mod}.
\tag{E6}
$$

以上保留非严格上界；无槽平板 $d=0$ 时可取等号。该结论解释了所列理想模型中的主值偏差方向，不提供具体偏差幅度，也不确定 $K_{yy}/K_{xx}$ 的模型偏差符号。本文5 nm数据相对于连续解的误差仍须由独立的数值参考证据判断。上界不构成局部耗散机制份额、V2预测精度或真实压印过程保真度的证明。

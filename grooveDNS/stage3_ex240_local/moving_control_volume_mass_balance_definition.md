# SIM-EC1XT240 连续移动控制体积质量定义

> Historical internal directory names such as `stage3_ex240_local` are retained for reproducibility. The correct physical/model designation is `SIM-EC1XT240`.

## 三种独立几何与质量量

### 旧full-cell质量

历史量继续原样输出：

\[
M_{full}(t)=\rho_{phys}\Delta x^3
\sum_{m\in\{1,4,5\}}\rho_i(t).
\]

求和只遍历单MPI rank的core cells，包含压力边界材料4/5，不包含overlap。转换前材料集合
固定为57,600个cell，因此`M_full`始终把每个流体标签cell当成完整`dx^3`，不响应位于cell
内部的连续Bouzidi壁面位置。它作为历史比较量保留，不再单独代表连续移动流体域质量。

### 连续流体体积

压头凸台表面为`z=h(t)`，中央120 nm凹槽顶为`z=h(t)+100 nm`。基底为`z=0`，因此：

\[
V_f(t)=L_xL_yh(t)+(120\,nm)L_y(100\,nm).
\]

其中`Lx=Ly=240 nm`。这个体积只由连续几何决定，即使材料标签尚未转换也连续变化。

### Geometry-aware质量

每个格子控制体积中心为`(x_i,y_i,z_i)`，z范围为
`[z_i-dx/2,z_i+dx/2]`。设该x位置的连续压头表面为`z_p(x,h)`，解析流体体积分数为：

\[
\alpha_i(t)=\operatorname{clamp}\left(
\frac{\min(z_i+\Delta x/2,z_p)-\max(z_i-\Delta x/2,0)}{\Delta x},0,1
\right).
\]

随后定义：

\[
M_{geom}(t)=\rho_{phys}\Delta x^3\sum_i\alpha_i(t)\rho_i(t).
\]

本几何的x分界`0/60/180/240 nm`都与dx=5 nm控制体积面重合，压头为0°水平面，所以
alpha只需上述z向解析交长；无需随机采样或拟合。普通流体cell为1，完全固体cell为0，
被连续壁面切割的顶层cell位于0与1之间。alpha只读取`h(t)`、几何分区、cell中心与dx，
不读取rho、质量、出口通量或残差。

## 几何体积验证

`geometry_volume_fraction_validation.csv`在step 0、100、500、650、1000、1156、1500和
2000比较`sum(alpha_i*dx^3)`与上式解析体积。8点最大绝对差
`2.12304e-33 m^3`，最大相对差`2.96239e-13`，属于浮点累加误差。

step 2000时：

- `h=74.4208 nm`，位移`0.5792 nm`；
- 解析体积`7.16663808e-21 m^3`；
- alpha积分体积`7.166638079997876e-21 m^3`；
- full-cell体积仍为`7.2e-21 m^3`；
- 连续扫掠体积`3.336192e-23 m^3`。

此时上下两类压头表面各切割对应顶层cell；切割cell的alpha为`0.88416`。在首次材料转换
前不会出现需要从solid标签读取rho的正alpha cell。

## 移动域质量残差

沿用项目符号，分别定义：

\[
R_{geom}=M_{geom}(t)-M_{geom}(0)-M_{in}(t)+M_{out}(t),
\]

\[
R_{full}=M_{full}(t)-M_{full}(0)-M_{in}(t)+M_{out}(t).
\]

宏观通量继续用压力面`rho*u_n*dx^2`梯形积分。population通量在collision之后按本机
D3Q19完整population `F_i=f_i+w_i`统计跨两个压力面的incoming/outgoing链接，并逐step
累加。两者使用不同离散时间口径，因此分别报告，不要求逐位相等。

生产移动域门禁使用局部rho加权的`R_geom`；`global average rho * V_f`只作为粗略对照。
连续扫掠体积没有被直接加减到残差，也没有通过质量数据反求alpha。

## 冻结验收

质量门槛仍为`max |R_geom/M_geom(0)| <= 1e-3`，没有放宽。稳定性、rho、Mach、非法link、
材料变化和f3/f8/f17检查继续独立执行。`R_full`保留，但不再单独触发连续移动域FAIL。


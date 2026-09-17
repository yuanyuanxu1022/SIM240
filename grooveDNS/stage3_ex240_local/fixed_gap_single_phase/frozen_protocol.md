# SIM-EC1XT240 固定间隙单相流动基准冻结协议

## 范围

- 固定显式结构：`Lx=Ly=240 nm`，x方向`60+120+60 nm`，槽深`100 nm`；
- 固定间隙：`h=75,70,65 nm`；三者均可由`dx=5 nm`的cell-centred节点与halfway bounce-back精确表示；
- x/y双周期，z=0基底和带槽压头固定无滑移；
- 单相全充液，不含FreeSurface、接触角、液滴或空气；
- 每个h分别运行X/Y单方向体力`a=1e5 m/s2`，其他体力分量严格为0；
- `rho=1000 kg/m3`，`nu=1e-6 m2/s`，`dt=1e-11 s`，`tau=1.7`，D3Q19 ForcedBGK；
- 功能网格`dx=5 nm`，不是网格无关结果。

## 输出定义

`A_plan=Lx*Ly`，`J_i=integral(u_i dV)/A_plan`，`K_ij=mu*J_i/(rho*a_j)`。

明确取`H_ref=V_nominal/A_plan=h+50 nm`，并定义：

- `B_ij=K_ij/H_ref`，单位m2；
- 深度积分阻力`R_J,j=(rho*a_j)/J_j=mu/K_j`，单位Pa s/m3；
- 平均速度阻力`R_U,j=(rho*a_j)/mean(u_j)=mu/B_j`，单位Pa s/m2。

这些量是固定周期单元的线性响应，不是动态压印载荷，也不是宏观模型中已验证的阻力系数。

## 收敛与验收

- 短测：100步；正式上限30000步；
- 最近1000步主J：`std/abs(mean)<=1e-6`且`span/abs(mean)<=5e-6`；
- 交叉J窗口最大绝对值`<=1e-12 m2/s`；
- 全过程流体质量最大绝对相对漂移`<=1e-10`；
- 最大`|rho-1|<=1e-6`（短测`<=1e-7`）；
- Mach`<=0.05`，两同方向截面通量相对差`<=1e-5`；
- 无NaN/Inf，material场不变，流体节点/体积与解析值一致。

压力场由本地OpenLB `SuperLatticePhysPressure3D`按`p=cs2*(rho-1)`及converter输出。周期体力驱动没有入口—出口压力差，因此只解释局部压力扰动；驱动压强梯度为`rho*a`。

## 运行顺序

先运行h=75 nm的X/Y短测；通过后依次完成h=75、70、65 nm的X/Y正式运行。运行前不根据结果调整参数或阈值。


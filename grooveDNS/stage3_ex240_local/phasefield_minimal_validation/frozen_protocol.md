# STEP 6-G well-balanced Cahn–Hilliard 最小验证冻结协议

本目录不使用 SIM-EC1XT240 几何，只验证本机 OpenLB 三维 well-balanced Cahn–Hilliard 实现。

共同参数：D3Q19 Navier–Stokes + D3Q19 Cahn–Hilliard 双 lattice；`tau_liquid=1`、`tau_gas=0.8`、`tau_phase=1`、`rho_liquid=rho_gas=1`、界面宽度4格、表面张力0.01格子单位、零外力。等密度是隔离算法功能的数值基准，不代表真实液体—空气密度比。

## CA：平壁接触角

- 域64×40×64格；x/z周期，y上下为固壁；半径18格液滴接触下壁。
- 输入接触角100°，按本机示例约定以`pi-theta`写入`THETA`。
- 正式运行6000步，VTK每500步。
- PASS：无NaN/Inf；Mach≤0.05；rho∈[0.8,1.2]；phi∈[-0.05,1.05]；相场总量漂移≤1e-3；末态测量角与输入差≤5°；末5次测量范围≤2°。

## LP：三周期球形液滴Laplace验证

- 域64³格，三方向周期；半径16格球形液滴。
- 正式运行4000步，VTK每400步。
- PASS：共同稳定性和守恒门槛；末态`|Δp|-2σ/R`相对误差≤15%；末5次Δp范围/均值≤5%。

短测试只验证初始化与推进，不替代正式物理验收。失败后不调参、不扫描。

# 单位与两相后端审查（2026-10-21）

这是第二篇模型支线的实现审查，以第一篇方法和验证问题为基础；不改变第一篇稿件、数据、协议或历史判定。最终状态见PREPARATION_STATUS.md。

## 证据链与继承边界

第一篇方法依据：docs/reports/第一篇论文_第2章方法草稿_20261017.md，黏度—时间步关系式(6)、解析壁面与q=1/2、深度积分K定义。原地图主批μ=1mPa·s；15mPa·s是另两点黏度对照。本点12mPa·s仅受GHY观测量级启发。

本机OpenLB HEAD=882924a9cfc8dcdf82909e39530789cb6f5ebcc4；CITATION.cff自标1.9.0。编译日志的OLB_VERSION来自构建环境，出现9bad48a-dirty，不能将它当作OpenLB源码版本。新运行manifest单独记录实际HEAD、源树全量哈希及库/二进制哈希。未修改共享OpenLB库。

原基线：grooveDNS/stage3_ex240_local/phasefield_minimal_validation/phasefield_minimal_validation.cpp及frozen_protocol.md。R1是等密度历史证据，不覆盖当前ρ比833.33、μ比666.67；原始PASS/FAIL保持。以下问题限定于本轮核对到的当前源码，不反推全部历史二进制。

## 已核算的映射

取液相密度ρref=1000kg/m³、Δx=2.5nm、τl=1、νl=μl/ρl=1.2e−5m²/s：

Δt=(τl−1/2)Δx²/(3νl)=8.68055555556e−14s。

ρl*=1，ρg*=0.0012；νg=1.5e−5m²/s，τg=1/2+3νgΔt/Δx²=1.125。动态黏度比约667不意味着运动黏度比667；后者为0.8（液/气）。

σ*=σΔt²/(ρrefΔx³)=1.44675925926e−5；压力尺度ρref(Δx/Δt)²=8.2944e11Pa；速度尺度Δx/Δt=28800m/s。G=1e7Pa/m对应体积力*=GΔt²/(ρrefΔx)=3.01408179012e−14。

audit_mapping.py从模型design.json读取并往返核对ρ、两相动态黏度、σ。它生成明确的SI映射头文件；格子几何和OpenLB内部converter保持格子恒等单位，所有物理输出显式换算。不得调用这个恒等converter的getPhys函数冒充SI。

## 本轮发现与修正

| 项目 | 当前旧源码/后端观察 | 新隔离程序处理 |
|---|---|---|
| 相别端点 | 旧注释和球滴φ=0液/1气，但RHOS={rhoG,rhoL}和TAUS={tauG,tauL}；后端确实计算a0+(a1−a0)φ | 数组按φ端点改为{液,气}，初始化同式，逐节点检查 |
| 初始化次序 | 旧代码先构建平衡，再赋RHO；初始化后恢复CH分布但STATISTIC/PHIWETTING可能未同步 | 先赋字段，再构建；每次化学势计算前从实际分布刷新相场缓存 |
| 密度安全 | 旧rho∈[0.8,1.2]是等密度门槛；当前ρ*=1−0.9988φ | 气相合法ρ*=0.0012；φ≥1.00120144173已非正，耦合除ρ前拦截，不截断φ |
| 力的单位 | phaseFieldCoupling.h把EXTERNAL_FORCE直接加到加速度，而BODY_FORCE除以ρ | 压力梯度对应均匀BODY_FORCE；静滴两者都零 |
| 压力读法 | momenta::BulkPressure返回p_h；外部RHO才是物质密度 | 同时记录p_h和体相机械压力候选；正式Laplace提取需再审 |
| 边界距离 | 通用cuboid求交在本点测得q偏差1.220703125e−4，无法满足严格半格审计 | 沿用第一篇解析交点方法，显式平壁求交、q=1/2，检查NS与CH两套links |
| 周期节点数 | inclusive端点使请求0..N产生N+1节点 | 周期轴使用0..N−1，独立计数与平面归一化一致 |

v1平壁link失败、v3平壁相场缓存/密度失败均保留在evidence与output独立run_id。它们是本轮开发初始化失败，不是旧正式物理FAIL，也不被后续编译/修复抹去。

## 后端位置与推导

- /home/dell/openlb/src/dynamics/phaseFieldCoupling.h：WellBalancedCahnHilliardPostProcessor约672–733行、化学势约736–768行、LinearTauViscosity约1104–1122行、RhoWettingStatistics约654–669行。
- /home/dell/openlb/src/dynamics/equilibrium.h：CahnHilliardZerothOrder约92–120行，其二阶矩决定CH迁移率；forcing.h约470行为对流源项。
- /home/dell/openlb/src/dynamics/momenta/elements.h：BulkPressure约206–239行；dynamics.h约331与447行绑定NS/CH模型。
- /home/dell/openlb/src/boundary/setBouzidiBoundary.h：距离设置、fallback与WellBalanced壁处理。全源树哈希随每次诊断保存。

公开[OpenLB equilibrium.h文档](https://www.openlb.net/DoxyGen/html/dc/d02/equilibrium_8h_source.html)也显示CH零阶平衡分布的化学势写法，但网页标为1.8.1，不能替代本机提交核查。迁移率和压力张量公式是本轮按已读实现作的连续方程推导，不声称完成Chapman–Enskog独立证明或离散机械应力验证。

## 尚不能放行的物理判断

高密度比的密度正性、寄生流、CH扩散与毛细松弛必须在目标点检查；τ值远离0.5不能独自证明稳定。旧0.01格子表面张力比当前大约691倍，旧4000/6000步不能直接继承为充分稳态时间。

time_scale_estimates.json给出尺度估计：R=40nm时黏性毛细时间约1.6e−8s（184320步）；200步仅1.736e−11s。它只适合找启动问题，不能验收静滴达到平衡。CH物理迁移率是数值模型参数，仍需独立敏感性证据。最终K的驱动速度很低，还需证明界面数值寄生流不会淹没方向性响应。

真实GHY仍只提供单次约25°C、10–50s⁻¹的五点流变数据。ρ、σ、两表面角、水时点无新增证据；本轮理想参数不能写回GHY材料表。

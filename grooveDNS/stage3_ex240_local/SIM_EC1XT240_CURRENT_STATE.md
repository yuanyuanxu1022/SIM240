# SIM-EC1XT240 CURRENT STATE

> Historical internal paths such as `stage3_ex240_local` are retained for reproducibility. The correct model designation is **SIM-EC1XT240**.

## 1. 当前研究目标

当前研究对象是 SIM-EC1XT240 纳米显式结构的单周期局部模型：x周期240 nm，由60 nm左半凸台、120 nm沟槽和60 nm右半凸台组成；y宽240 nm，沟槽深100 nm。当前任务是验证固定基底上方带槽压头连续下移10 nm时的真实OpenLB移动边界、动态拓扑和单相开放排液质量闭合。

STEP 5通过后，才进入原计划STEP 6：液滴、气相/空气、润湿与填槽。当前结果不是液滴压印结果，也不包含两相、接触角或困气模型。

## 2. 冻结基线

- STEP 4冻结源码：`/home/dell/yuanyuanxu/SIM240/grooveDNS/stage3_ex240_local/explicit_piston_zouhe_moving_control_volume_longrun.cpp`
- SHA-256：`9444c61aab6cc67499211f2724d109923d91d9bc0fe66747446acf2da5e399e2`
- OpenLB：`5953d8a-dirty`，真实`SuperGeometry`/`SuperLattice`
- lattice：D3Q19，带`BOUZIDI_DISTANCE`和`BOUZIDI_VELOCITY`字段；BGK；overlap=3
- 空间与物性：dx=5 nm，rho=1000 kg/m³，nu=1e-6 m²/s
- 时间映射：dt=1e-11 s，tau=1.7
- 运动：h=75→65 nm，10000步五次平滑轨迹，T=1e-7 s；最大物理壁速0.1875 m/s，最大格子壁速3.75e-4
- 边界：x周期；y两端等rho=1的Zou/He压力边界；z=0固定无滑移基底；上方moving Bouzidi压头；192条跨x周期固壁link修复保留
- 最终目标位移：10 nm

冻结验收标准：

- Mach `<=0.05`
- rho保持`[0.8,1.2]`
- 无NaN/Inf
- 无非法或遗漏link
- material变化与解析几何预测一致
- 移动控制体积质量残差`|R|<1e-3`

STEP 4转换前长程门禁已PASS：开放C运行2000步、位移0.5792 nm，最大Mach `4.34610e-4`，rho=`[0.997560668,1.022618246]`，最大`|R_geom|=1.687520e-4`，非法link和material转换均为0。

## 3. STEP 5 已完成的关键结论

### A. 静态material＋动态Bouzidi虚拟链接

**FAIL。** STEP 5.4保持material不变，仅更新解析Bouzidi links。step 3595后产生2304个ghost-storage节点和11708条切换链接；Mach仍低，但移动控制体积质量不闭合，随后rho越界。根因是ghost-storage populations没有与移动物理控制体积一致的守恒定义。

### B. 动态material拓扑事务

已实现并验证真实事务：预测→保存状态→material提交→dynamics切换→population阶段→Bouzidi刷新→geometry/lattice同步→推进。

- 首次`fluid -> solid`：step 3595
- displacement：`2.501015275 nm`
- 转换节点：2304（凸台底面层1152＋槽顶层1152）
- material提交、NoDynamics切换、SuperGeometry同步正确
- periodic material mapping正确
- Bouzidi links正确，非法link=0
- 无NaN/Inf；0→3 nm最大Mach `1.050757e-3`，rho稳定

### C. 提交瞬时population

material/dynamics提交瞬间，2304节点的stored `f0...f18`最大变化为0；按当前OpenLB shifted定义恢复的population-consistent mass也没有瞬时损失。问题不应再描述为“material conversion失败”。

### D. NoDynamics质量读取口径

`NoDynamics::computeRho()`固定返回1，而stored-population密度为`rho_pop=1+sum(f_i)`。旧审计因此存在跳变，但改用全域population-consistent质量后仍为：

`max |R_pop| = 1.20808380745e-3`，FAIL。

### E. Moving-wall sweep项

step 3594→3595的连续墙面扫掠体积为`9.16066037937e-26 m³`，质量为`9.39541922710e-23 kg`。加入该审计项后：

`max |R_corrected| = 1.19503461408e-3`，仍FAIL。

该墙项只解释首次转换事件步剩余缺口约7.08%。

## 4. 已排除原因

- 不是material提交数量或位置错误
- 不是dynamics切换错误
- 不是SuperGeometry同步错误
- 不是periodic material mapping错误
- 不是非法、遗漏或错误q的Bouzidi link
- 不是material提交瞬间直接删除stored populations
- 不是`NoDynamics rho=1`审计口径能够完全解释
- 不是简单moving-wall swept-volume项能够完全解释
- 不是高Mach、rho爆发或NaN/Inf导致的数值发散

## 5. 当前唯一核心问题

当前主要未闭合量出现在`fluid -> solid`拓扑转换后的第一次collision/streaming/Bouzidi离散population交换。step 3594→3595扣除物理墙面扫掠后，剩余未闭合质量约为：

`1.23380470441e-21 kg`

下一步必须在link/population层追踪`fluid cell -> new solid topology -> Bouzidi -> streaming/collision`中的具体population去向，判断是否存在丢弃、重复、覆盖或缺失的离散交换项。动态material拓扑、几何和稳定性本身已经工作，不能再笼统归因于“material conversion失败”。

## 6. 下一任务

下一任务不是增加STEP编号或继续泛化审计，而是：**STEP 5 convergence task**。

1. 只针对step 3594→3595建立link-level population mass ledger；
2. 数值解释剩余约`1.2338e-21 kg`缺口；
3. 找到具体离散路径后，只实施一个有物理依据的最小修复；
4. 修复先运行0→3 nm；
5. 若满足`|R|<1e-3`，直接执行最终0→10 nm；
6. 不再进行1 nm、5 nm等中间位移验证；
7. 10 nm通过后关闭STEP 5，进入原计划STEP 6。

## 7. 关键文件

- `/home/dell/yuanyuanxu/SIM240/grooveDNS/stage3_ex240_local/explicit_piston_zouhe_moving_control_volume_longrun.cpp` — STEP 4冻结的转换前moving-control-volume基线。
- `/home/dell/yuanyuanxu/SIM240/grooveDNS/stage3_ex240_local/explicit_piston_virtual_link_moving_geometry.cpp` — STEP 5.4静态material/ghost-storage失败候选源码。
- `/home/dell/yuanyuanxu/SIM240/grooveDNS/stage3_ex240_local/step5_4_moving_geometry_design_report.md` — STEP 5.4失败证据、link变化和根因范围。
- `/home/dell/yuanyuanxu/SIM240/grooveDNS/stage3_ex240_local/step5_5_dynamic_material/dynamic_topology_manager.h` — 动态material事务、dynamics切换和同步模块。
- `/home/dell/yuanyuanxu/SIM240/grooveDNS/stage3_ex240_local/step5_5_dynamic_material/first_material_conversion_test.cpp` — STEP 5.5 v3首次真实转换冻结测试。
- `/home/dell/yuanyuanxu/SIM240/grooveDNS/stage3_ex240_local/step5_5_dynamic_material/mass_audit_consistency_test.cpp` — 同物理演化的`M_geom_old/M_pop`双口径审计程序。
- `/home/dell/yuanyuanxu/SIM240/grooveDNS/stage3_ex240_local/step5_wall_motion_mass_audit_report.md` — STEP 5-C墙面扫掠项及剩余缺口结论。
- `/home/dell/yuanyuanxu/SIM240/grooveDNS/stage3_ex240_local/step5_5_dynamic_material/output/mass_audit_consistency_0to3nm_v1_20260909/first_conversion_history.csv` — 0→3 nm逐步质量、通量、rho和Mach时序。
- `/home/dell/yuanyuanxu/SIM240/grooveDNS/stage3_ex240_local/step5_5_dynamic_material/output/mass_audit_consistency_0to3nm_v1_20260909/conversion_event_mass_audit.csv` — 2304节点提交前后即时population质量账本。
- `/home/dell/yuanyuanxu/SIM240/grooveDNS/stage3_ex240_local/step5_5_dynamic_material/output/mass_audit_consistency_0to3nm_v1_20260909/wall_motion_corrected_history.csv` — 加入事件墙面扫掠项后的修正残差时序。

## 8. READ THIS FIRST

- 新Codex会话优先阅读本文件。
- 不重新扫描历史报告，除非本文件明确指向。
- 不重复已经排除的假设。
- 不擅自放宽`1e-3`质量阈值。
- 不加入两相、液滴、润湿或空气。
- 不修改STEP 4冻结源码。
- 核心任务优先收敛STEP 5，不继续扩展子步骤。

# h75 / dx1.25 / T 质量旁路诊断 v2

日期：2026-10-13。独立准备、编译与零推进预检；4000 步诊断由用户另行启动。历史源、v1、旧结果与 FAIL 保留。

目标单周期 Lx=Ly=240 nm、h=75 nm、D=100 nm、Wg=120 nm、dx=1.25 nm、dt=2.604166666666667e-13 s、tau=1、rho=1000 kg/m³、nu=1e-6 m²/s、a_x=1e5 m/s²。D3Q19_FORCE/ForcedBGK、原静止 Bouzidi、x/y 周期、overlap3、1rank/1cuboid/1计算线程。几何、初始化、动力学和旧统计及旧门禁沿用历史 SHA 对应源码。

## 源码与观察器

求解器源从独立审查快照机械复制；去除 12 个诊断标记块后应恢复历史生成源。新增部分只读原 measure 的 rho/Measurement，Observer 不接收 OpenLB 对象，不增加 lattice processing context、通信、population 或材料写入。源级一致不保证新编译的运行结果逐位一致。

v2 仅增强独立 Observer：拒绝重复/遗漏的流体密度观测、检查 rhoPhys/dx；每步记录 film/recess 节点数及 delta-rho 和、密度极值 ID、整数节点定义的名义体积；汇总质量误差重构残差。film 为 z_phys∈(0,h)，recess 为其上额外凹槽，按 core z 索引1–60和61–140区分，互斥且覆盖所有流体。预期 film=2,211,840、recess=1,474,560。

## 样本与验收

计划 step0–4000 共4001行，保留原1000样本J收敛规则与60000步上限，另加4000步诊断截止。若提前收敛，覆盖须报不完整。固定 double-rho 快照0/119/120/624/625/626/3732/3733/4000，加短程旧质量误差峰值快照。单独保存唯一流体ID mask，逐步材料/core指纹与mask一致。ID、hash必须按整数解析。

同步记录原 double 质量、Neumaier物理质量/rho/delta、long-double物理质量/rho/delta。每种误差用自己的初态；e_delta=[sum_delta(t)−sum_delta(0)]/[N+sum_delta(0)]。新账本一致性与旧误差分解重构目标均≤1e-13，仅为诊断精度条件。

旧质量门槛严格 max(abs(e_old))<1e-10，density≤1e-6、Mach<0.05、最终section差≤1e-5、cross≤1e-12、J窗口std≤1e-6/span≤5e-6、q=0.5±1e-10、fallback/unresolved0、finite与几何/材料原定义均不变。

运行输出保持 formal_reference_accepted=false。预计未达到正式稳态或旧质量门禁未过时原程序 exit=3；诊断覆盖完成、独立退出、legacy门禁和高精度质量分别审查，不将诊断程序的退出解释成正式通过。

分阶段 collision/stream/Bouzidi 及分区 link 收支尚未实现。如稳定全域账本提示真实变化，再独立设计阶段定位，不改变 collideAndStream 次序。本诊断回答全域统计偏差与质量变化的分解，不直接验收正式细网格 K。

## 来源、运行与资源

当前库标 CONTROLLED_CURRENT_ENVIRONMENT：历史完整dirty库/构建未恢复。完整当前include/静态库/动态依赖hash、OpenLB HEAD/diff/status、source/header/recipe/protocol和binary hash、构建命令与stdout/stderr必须独立保存。运行前校验已冻结文件，使用新唯一run_id并记录外部退出码和全部输出SHA。

预算：1计算线程、建议8 GiB可用RAM及2 GiB磁盘；实际耗时/RSS尚需诊断测量。编译与零推进预检不等于4000步运行，也不等于完整细T门禁通过。只有完成后续根因、全程参考及兼容网格链审查，才讨论网格误差与排液优势的正式量化。

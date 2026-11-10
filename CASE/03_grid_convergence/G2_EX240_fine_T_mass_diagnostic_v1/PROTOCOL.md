# 细T质量旁路诊断协议 v1

冻结日期：2026-10-13；状态为源码准备/静态验收，运行授权=false。母协议与历史FAIL不更改。

## 范围与来源

目标h=75 nm、dx=1.25 nm、T/+x，单rank/单cuboid/单计算线程。基准源：`../G2_EX240_grid_convergence/build/generated/g2_ex240_dx1p25.cpp`，历史SHA `898cbe394a4528ae3ef925002ccb16eb33da433651276457e5913b128174281e`。旧run身份是`g2_grid_20260917T165045+0800 / dx1p25_EX240_perpendicular / steady`。

本目录源码副本新增块之外与基准逐token相同，包括rho/u初始化、force映射、ForcedBGK、Bouzidi、几何与通信、原质量乘加、J窗口、输出及return逻辑。header观察器只接收数值/ID和Measurement读取结果，无OpenLB对象引用，没有新增processing context/communication/force/population写入。源级相同不能证明重新编译后的逐位动力学相同，后者仍待受控运行。

## 计算范围与快照

计划完整覆盖step0–4000，共4001行；推进次数4000；物理时长1.041666666666667e-9 s。原maximumSteps=60000保留，追加诊断截止，并保留原J窗口的提前停止规则。若意外在4000之前收敛退出，diagnostic_coverage_complete=false，不能伪称覆盖全部快照或自动续跑。

固定rho快照为0、119、120、624、625、626、3732、3733、4000；额外保留本短程旧质量最大峰值的完整rho快照，覆盖新峰位移。固定节点mask在step0保存，后续每步严格检查相同的流体ID序列、四类material计数及完整core材料指纹。snapshot为原computeRho得到的binary64，排除solid/halo，没有插值/Float32转换。

原initial measure不改变；step0第一次旁路重新读取相同初态，记录其旧mass应等于原initial.mass。每步先完成原collideAndStream，再在原measure内复用已经读取的rho；先执行原统计，随后追加旁路累加。材料观测只多读material分类；不会改写几何。每个新输出flush/close可检测I/O错误，拒绝已有诊断输出/快照目录。

## 账本与验收

原账本：material1 core的`sum(rho*rhoPhys*dx*dx*dx)`，e_old=(M−M0)/M0，全程严格max(abs(e_old))<1e-10。该表达式、旧M0与累计max都保留。补偿账本使用同一double物理质量项的Neumaier；long double另算物理质量、rho和及sum(rho−1)。各新误差使用各自同精度初态，稳定误差为`[sum_delta(t)−sum_delta(0)]/[N+sum_delta(0)]`。

其余原阈值：density≤1e-6、Mach<0.05、最终section差≤1e-5、cross≤1e-12，1000样本J标准差/abs(mean)≤1e-6、span/abs(mean)≤5e-6，q=0.5±1e-10、fallback/unresolved0、正确几何体积、finite、material和独立退出。代码未修改这些数值。新账本一致性目标≤1e-13仅用于诊断可信度，不替代或放宽1e-10旧门禁。

准备验收：源差异局限12块、所有物理/推进/门槛恢复一致；参考算术重现旧M0；补偿与fsum一致，long-double参考误差<1e-13；二进制schema正常读取并拒绝重复/空mask、截断、错hash/NaN；来源/库/配方及资源清单完整。实际C++算术、编译、precheck和运行输出尚未验证，必须在后续分别验收。

未来运行验收：4001连续step、每步N1=3686400/core=5345280且mask不变；9固定快照和峰值完整；Neumaier/long-double/delta/离线fsum一致性≤1e-13；旧误差分解重构残差≤1e-13；legacy诊断与新账本同step同步；所有原始文件SHA不变。若高精度也显著漂移，结论为需阶段定位；若只旧账本越界，报告统计偏差贡献及误差预算。任何分支均不自动改变旧FAIL。

## 来源与执行边界

当前库HEAD=882924a9cfc8dcdf82909e39530789cb6f5ebcc4，实际include树、静态库、当前dirty diff/status和编译器信息记录在preparation_manifest。历史标签5953d8a-dirty不能证明历史库状态；因此准备包标CONTROLLED_CURRENT_ENVIRONMENT_NOT_HISTORICAL_REBUILD。新源码将OLB_VERSION编译字符串写成实读HEAD，这是版本标签声明，不是物理改变。

未编译的binary SHA、完整build log、实际RSS/walltime与运行等价性都保持未产生。未来正式run需独立run_id、完整build/参数/source/library/binary/protocol manifest、新空输出目录、完整log和外部shell exit；保留旧CASE return3与诊断覆盖完成两个不同结论。此处只冻结要求，没有创建run目录或执行命令。

论文影响：准备包不新增任何迁移率结果。阶段collision/stream/Bouzidi/link收支未实现；这一轮先获取缺失的同步全域rho账本。根因仍未闭环，三高度为固定网格候选，下一Gate不自动放行。

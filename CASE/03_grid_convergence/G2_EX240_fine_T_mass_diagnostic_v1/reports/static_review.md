# 隔离细T诊断静态审查

审查日期：2026-10-13。准备状态：STATIC_PREPARATION_PASS_NOT_COMPILED。生产代码、原数据和历史FAIL保留。

源码审查：12个新增标记块之外，与历史SHA匹配的基准源逐token相同（字符串内空白也被保留比较）。原质量乘加、initial M0、collideAndStream、force/collision/边界/几何/单位映射、阈值和原结果/return保持。新增块的职责为header/Observer参数、只读shape/material/rho观测、T限制、创建观察器、逐步账本、4000步诊断截止与诊断完成输出。

观测器不接收OpenLB对象，不调用computeU/computeRho、setField、通信或processing context；只复用原measure读取到的rho与原Measurement。每个core观测的严格递增ID保证本单cuboid遍历无重复；每步计数及hash检查，流体ID逐点与初态mask一致。该结构提供源级无状态写入证据，但不能证明不同构建的运行结果逐位相同。

参考算术已通过：原3686400项double乘加重现M0=7.1999999993792838e-18 kg；Neumaier常量质量与fsum一致，M0相对偏差−8.62105942189828e-11。Python/Numpy long-double平台64位有效位的常量累加相对偏差约1.677e-14，低于1e-13诊断目标；最终double切片稳定平均delta=9.372583727647783e-15。符号抵消与顺序变化测试通过，二进制格式正常往返；空mask、重复/乱序ID、截断、错fingerprint与NaN六类异常被拒绝。精确结果与运行环境见preparation_manifest。

这些是Python参考算术及schema测试，实际C++头文件未被编译/执行；不声称C++算术单元测试通过、precheck通过或运行无侵入性已验证。当前没有新binary、run目录、solver输出、实际RSS/walltime或新的PASS结果。

当前库/依赖/源已绑定；历史完整dirty库无法恢复，prepare包标CONTROLLED_CURRENT_ENVIRONMENT_NOT_HISTORICAL_REBUILD。完整build日志和binary SHA在下一编译任务取得。若未来输入SHA变化，make compile的检查应拒绝执行，需重新独立评审绑定，不能偷偷使用变化后的库。

关键边界：原稳态提前停止规则仍保留，意外提前停止导致4001行/9快照覆盖不完整，应如实报诊断不完整。4000步停止也不授予正式参考PASS。原CASE return3与诊断覆盖完成是不同证据；后续必须同时读取result、diagnostic_status、独立shell退出及快照哈希。

资源预算见run_config：1rank/1计算线程、8 GiB RAM、2 GiB磁盘；observer有效载荷约84.4 MiB，10rho+mask约309.4 MiB，尚需原VTK/字段/通信。每步全core材料hash及三种累加有新增时间开销，未作时间保证。

下一项仅为独立编译验收与零推进precheck（需下一任务授权），随后再由用户决定短程计算；本轮没有提供或执行运行命令。历史FAIL未解除，根因尚待同步瞬态证据。

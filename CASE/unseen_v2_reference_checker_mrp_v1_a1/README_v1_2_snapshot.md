# URV 检查器 v1.2：R1/R2 隔离修订

本目录从 v1.1 隔离复制。物理协议 URV-v1、合同结构 URV-EXEC-1.1、数值算术和门槛保持。旧 v1.1 及其封存保留。

R1：合同声明必须完整解析。任一输入/运行/回归基准路径声明有错误，立即报错退出；在任何分析目录创建或写入前停止，不再返回空保护集合继续。单条与批次共用此规则。

R2：统一识别合并与分离书写的 -D/-U，要求 URV_PREPARATION_ONLY 恰好一次、明确为0；重复、冲突、取消定义、无值定义均拒绝。其他宏名不视为该宏。

77项软件测试通过（原70项及7项新增方法，含多项子用例）。4个旧测试用的“缺失合同”被调整为明确人工路径声明，以继续检查其原来的内部失败条件；物理断言没有放宽。首次3失败日志保留。

analysis/check_results.py、analysis/evidence.py、analysis/read_fields.py 和 common/ 全部保持 v1.1 原字节。仅 analysis/contracts.py 与必要软件测试修订；F02先保存完整差异再停止的行为保留，F04多合同汇总仍在后续范围。

common/ 内 PENDING 是旧材料快照，不覆盖当前作者确认。当前明确答复和适用范围见 ../../docs/reports/URV_external_history_confirmation_20261101/author_declaration.json；核查位置未提供、独立外部审计未做。新S0执行准备在同级 unseen_v2_reference_S0_v1_2，正式启动授权保持关闭。

软件测试及零步准备不证明新稳态结果正确。新URV完整稳态端到端验收仍 NOT_EVALUATED；不得把修订封存当作计算启动许可。

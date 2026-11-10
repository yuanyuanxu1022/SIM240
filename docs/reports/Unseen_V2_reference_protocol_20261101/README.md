# URV-v1运行前材料

**24项具体协议候选已准备；没有启动、编译或原生零步计算。** 先读[PROTOCOL.md](PROTOCOL.md)，再看[case_matrix.csv](case_matrix.csv)和[acceptance_spec.json](acceptance_spec.json)。

- 12项主参考：两个新几何、两方向、三网格。
- 12项必要控制：新统计副本h75回归2、薄平板2、中格额外驱动力8。
- 原C/h75网格链已有[本轮限定复核](../C_h75_reference_review_20261101/REPORT.md)，不需要在本方案里先重算其细网格。
- [model_predictions_before_reference.csv](model_predictions_before_reference.csv)是原模型/V2提前预测；参考列空白。[prediction_seal.json](prediction_seal.json)记录当前预测哈希，执行前仍须最终封存。
- [preparation_bindings.json](preparation_bindings.json)是已有实现依据；拟用的新统计副本尚未实现。[describe_only_templates](describe_only_templates/)只供参数审查，mode=describe，计划标识不等于实际run_id。
- [protocol.json](protocol.json)记录阶段/资源/未就绪项；[data_history_status.json](data_history_status.json)保留外部数据历史待确认；[static_verification.json](static_verification.json)是离线检查，不是编译、安装或物理验收。

本文由AI按scientific-writing技能组织，不代替作者确认、正式合同采用或人工科学签字。旧协议/FAIL/G4锁不变，没有借本方案解锁旧D4预测。

# 执行记录

2026-11-10。首次执行check_existing.py退出1：方向字符串断言预期T=transverse，但8条原result实际一致使用P=parallel、T=perpendicular。逐条读取核实后只改检查器词汇映射，第二次完整运行退出0。首次执行发生在写CSV/verification之前；未改原始结果或论文，未启动仿真。失败不是科学反例或原Gate失败。

最终生成selected_records.csv、paired_evidence.csv、mechanism_link.csv及verification.json。检查内容为旧来源绑定、原K算术、两方向配对、共同倍率公式、已有正项和及账差衔接、保护文件无漂移。没有进行拟合、优化求解、交叉验证或原流场再处理。

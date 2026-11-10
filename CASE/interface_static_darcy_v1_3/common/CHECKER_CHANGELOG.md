# 检查器1.3.0：增加C04身份支持，计算与门槛不变

相对1.2.0仅修改模块说明、CHECKER_VERSION和SUPPORTED_CASES，增加C04。全部函数AST逐一相同，原SDI-v1阈值和平均定义不变；保留1.1引入的面向量几何舍入识别，原始Sf/phi值不改。

支持范围仍限已完成C01—C04的既定非零x主轴、对角系数、512网格平均问题。未支持C05或一般斜向/新网格/变厚度问题；不改旧C01严格零识别的未评价记录。

15项人造数据测试通过，包含C04身份与错误C01输入拒绝、未支持C05拒绝、几何舍入接受/真实倾斜拒绝、平均厚度/守恒/符号异常识别；日志与记录在reports/functional_tests.log、functional_tests.json。

使用本版只读回读C01、C02、C03已完成原始结果，各50项数值检查、全部指标、Gate及原始文件哈希与既有分析逐项相同（仅忽略版本元数据），没有重跑CFD。对照diff、三个回归JSON及regression_comparison.json见[准备报告目录](../../../docs/reports/SDI_C04_preparation_20261030/REPORT.md)。

以上是检查器功能和兼容性证据，不是C04结果。C04尚未启动，NUMERICAL_GATE=NOT_EVALUATED、RESULT_PASS=null，几何仅静态合成平均域通过。

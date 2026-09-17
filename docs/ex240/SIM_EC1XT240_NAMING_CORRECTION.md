# SIM-EC1XT240 名称勘误说明

## 正式名称

本项目此前部分文档中使用的 `EX240` 是名称误写。正确的物理/模型名称为：

**SIM-EC1XT240**

从2026-09-08起，新报告、新注释、图题及正式研究材料统一使用
`SIM-EC1XT240`。如果需要描述局部模型，应写作“SIM-EC1XT240局部模型”或
“SIM-EC1XT240局部显式几何”。

## 对已有研究结果的影响

本次仅纠正名称，不改变任何几何尺寸、材料定义、物性、边界条件、单位换算、数值算法、
运行参数或历史仿真结果。尤其没有改变：

- 60 nm + 120 nm + 60 nm的周期几何和100 nm沟槽深度；
- Bouzidi与Zou/He pressure实现；
- lattice resolution、material编号、converter、黏度、密度、壁速和压力；
- x/y周期设置及192条跨周期固壁link修复；
- C650和转换前长程观察的任何数值或判定。

名称错误不影响`SIM-EC1XT240.OAS`的既有解析，也不意味着重新解释版图、改变凹凸极性
或重新运行仿真。

## 历史文件与路径

为保证运行命令、脚本依赖、manifest、源码哈希和历史结果可复现，既有内部路径、文件名、
run-id、输出描述符及冻结报告正文不做追溯性改写。例如以下名称继续原样保留：

- `stage3_ex240_local/`；
- `ex240_homogenization/`；
- `ex240_h65_dns`及其源码、构建目标和run-id；
- `OpenLB_EX240_progress_report.md`、`ex240_layout_report.md`；
- 既有`output/ex240_*`目录和VTK数据集名称。

这些字符串是历史内部标识，不再被解释为正确的模型名称。

> Historical internal directory names such as `stage3_ex240_local` are retained for reproducibility. The correct physical/model designation is `SIM-EC1XT240`.

历史诊断报告、结果文件、manifest和已记录hash没有因本次勘误被修改。引用历史材料时，
正文应使用正确名称，并可在首次引用时说明括号内路径为历史保留名称。

本轮已同步纠正活动项目总览、阶段三设计审查正文/标题、两张设计SVG图题、阶段三修订
方案标题，以及静态几何后处理脚本未来生成图的标题；没有重新生成或覆盖旧PNG/PDF。

## 后续写作约定

- 正式名称：`SIM-EC1XT240`；
- OAS文件：`SIM-EC1XT240.OAS`；
- 内部遗留路径：保持原拼写并使用代码格式；
- 不再用旧误写指代物理模型；仅在讨论搜索结果、勘误内容或历史内部标识时保留它。

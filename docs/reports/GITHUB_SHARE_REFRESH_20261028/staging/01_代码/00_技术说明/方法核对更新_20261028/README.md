# 2026-10-28 方法、图件与条件GCI资料

本目录是代码、图片、数据和核对元数据的阶段更新。没有新增求解结果或参考精度放行。来源原件、完整正文、真实N8场、账号资料不在本轮上传范围。

## 本轮新增和更新

- 更新两份绘图脚本、两份图件说明，以及图2/图3的PNG/PDF/SVG各三种格式；数据曲线与前轮核对口径保持，文字标签采用已审订正。
- 增加历史条件Richardson/GCI表及对应只读分析源码/复算记录。表内列p、网格比、Fs、外推值、ea、e_ext、GCI和失败点依赖。
- 保存Bouzidi、Guo、Celik指定方法核对的接收元数据和当前实现片段/哈希；不附第三方论文PDF、全文文本或页面图片。
- 保存四组历史构建的资料接收合同，以及当前未闭合项的结构化清单。

## 怎么查看

1. [条件GCI表](../../../03_数据/方法核对_20261028/表S5_条件GCI.csv)。三个依赖历史细横槽失败记录的指标仍有明确标记，不是精度证书。
2. [现有记录复算源码](../../计算与分析/GCI复核_20261028/recompute_existing.py)与[保存的复算结果](../../计算与分析/GCI复核_20261028/recomputed.json)。源码按原项目路径组织，本目录不承诺脱离原材料即可直接复算，也未在本轮重新执行。
3. [Bouzidi六项对应状态](Bouzidi原文对应/contract_receipt.json)及[当前实现片段](Bouzidi原文对应/current_implementation.json)：固定壁q、线性两分支、时间层、零壁速与q=.5。PDF9页包含出版社封面及连续8页正文，文件只记录元数据，不附原件。
4. [Guo/Celik接收记录](Guo与GCI原文对应/contract_receipt.json)：P9指定力项/速度与P10发表版指定步骤及版本对应已核。该文件产生时间早于Bouzidi新原件，其P8未收到字段是历史快照；当前P8状态以本目录第3项为准。
5. [历史构建合同](历史构建合同/MINIMUM_EVIDENCE_CONTRACT.md)、[四组状态](历史构建合同/binary_group_contract.csv)、[历史发现记录](历史构建合同/build_evidence.json)。22/22/6/2分组的完整源码/依赖/编译身份仍未闭合；当前源码不能补作旧版本证明。
6. [当前剩余项](当前证据状态/remaining_items.json)与[52份manifest的字段核对记录](当前证据状态/current_evidence_checks.json)。只盘点现存资料，不开展实际N8分析。

## 证据与使用范围

本轮文件的原路径、目标路径、大小与SHA256保存在仓库根文件清单中。JSON内的本机绝对路径、源PDF身份和验证记录是来源信息，不表示共享包收齐了这些外部原件。verification.json保留原任务的检查范围，不是本共享副本重新运行的验收证书。完整性核对另见本轮共享检查记录。

Bouzidi与Guo的当前源码对应不等于全部历史程序来源已恢复；Celik原文与GCI表齐备不等于已经确认渐近区、参考已合格或全域误差界已建立。

N8仍仅ONE_N8_DIAGNOSTIC_ACCEPTED；NUMERICAL_GATE=NOT_EVALUATED、RESULT_PASS=false、geometry_PASS=null。reference_qualified=false、strict_error_bound_established=false、submission_ready=false，预测HOLD。真实N8提取、第二项及新增求解均未启动。历史FAIL完整保留。

原有其他代码、数据和几何沿用父提交；本轮没有重做旧8591项的全量源文件校验、编译或绘图。新文件及本轮替换项已作逐字节绑定；其余保留Git父提交中的原文件。

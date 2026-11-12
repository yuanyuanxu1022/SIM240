# v2.1 停止规则与延拓来源：指定模型静态复核工作稿

日期：2026-11-11。作者明确请求 GPT-6 Astra High 对 v2.1 实施作方法/实现自审；本报告不是期刊指派审稿、人工独立数值验收或启动许可。作者负责最终科学声明。按已授权自有项目审查使用 peer-review 的证据定位、影响与最小修复框架；没有期刊评审委托，不捏造期刊政策核准或工具 intake PASS。未对外搜索或上传未公开材料。本子任务唯一写入文件是本报告；共享状态和正式目录同步由主代理处理。

## 结论与适用快照

**最终受审候选在本次限定范围内剩余静态阻塞为 0。旧审查 B1—B5 与粗网格预算不一致已关闭。** 完整字段规则、tight 独立收紧、限定的 T 平板例外、正常结束/停止原因、延拓来源链和零残差处理，在最终实现中彼此一致。可以记录“指定模型静态复核完成”，不能据此报告任何新数值结果、参考资格或执行授权。

受审目录为 `CASE/.paper1_fvm_v21_candidate_20261111/`，最终 `release_manifest.json` SHA256：

```text
f1531d4091a6279a5db2df5cff75875d279d4ffc981f52ae5502bedd98ffc292
```

本审查独立重算 release 所列 **212 份本地文件 + 23 份外部工具/依赖，0 漂移**。受审对象是此完整候选，而非另一会话曾留下的混合接口正式 v2 目录。只有把同一 release 及全部绑定文件逐字节同步到 `CASE/paper1_fvm_stokes_reference_v2/` 并核验无漂移后，正式目录才能引用本结论；若修改规则、消费者或绑定输入，应再核变更。仅目录名不同、不改变文件字节的同步不改变本次科学/实现结论。

最终 release 仍写 `PREPARED_NOT_RUN`、`PENDING_ASTRA_V21_RECHECK`、`numerical_execution_authorized=false`；本报告没有更改这些执行控制元数据。审查“已完成”与发布闸门“尚未更新”应分别记录，不应继续把本轮当作审查未发生，也不能擅自解除启动限制。

## 复核范围与方法

- 已读项目规则、当前状态、路线/历史状态入口、最新便携交接及旧 v2 `ASTRA_REVIEW.md`；以当前状态顶部的五项阻塞为起点，不采用旧准备 PASS 覆盖旧 v2 的新问题。
- 逐项审查候选 `acceptance.py`、`run_one.py`、`postprocess.py`、`prepare.py`、`freeze_release.py`、协议/配置/README、两份 manifest 和测试源码。
- 只读核对本机 Foundation 13 的 `simpleControl::loop`、`convergenceControl::converged/endIfConverged`、`singleRegionConvergenceControl::criteriaSatisfied`、`getInitialTypeResiduals`、`Time::running/loop` 及 consistent mapFields 写场分支。
- 独立确认 solver C++、ELF、`comparison_inputs.json` 与 v1 字节相同；26 份 case 元数据逐份等于 canonical plan，prepared 输入 SHA 无漂移，候选中 runtime/referenceEvidence 目录均为 0。
- 阅读主代理保存的 `tests_candidate_final.log`，其记录为 46/46 合成检查通过；本子任务没有重复运行这套会写临时 fixture 的测试。另执行 4 个**纯内存合成**边界检查：打印 Uy 且达标时接受、打印 Uy 但不达标时拒绝、普通残差恰等于 1e-10 时拒绝、tight 残差恰等于 1e-11 时拒绝。四项均符合规则，不涉及实际流场或 PDE。
- 没有求解、编译、blockMesh/checkMesh/mapFields 执行、实际原场再处理、保留预测场读取或数值 Gate 验收。本轮 run_id=null，无新增计算结果。

## B1：完整字段与 T 平板例外——关闭

位置：`acceptance.py:40–82`；`prepare.py:187–205`、`:232–244`；`PROTOCOL.md:48–62`。

真实沟槽 P 只检查存在的标量 v；T 的每轮允许且要求 `Ux/Uz/p`，若打印 Uy 则必须为 `Ux/Uy/Uz/p` 并同时检查 Uy。缺字段、重复 p、顺序错误、负值、非有限值均拒收。普通 p/U/v 恢复严格 `<1e-10`；不再存在只看 Ux 的 OR 分支。初始归一化残差是操作性停止指标，并未被报告成连续导度误差界。

Uz 例外须同时满足 `d_nm=0`、`direction=T`、`level=flat` 及显式元数据标志；Uz 求解记录仍须存在且有限非负。例外保留 p/Ux 的普通残差门槛，要求实际导出 `max|Uz|/max|Ux|≤1e-9` 且主幅值有限正值，并要求 K/剖面解析误差各≤0.1%。P 平板不要求不存在的 p/Ux。原生残差控制仍可能因平板微小 Uz 的归一化残差不达标而继续运行，但正常达 cap 后可按本版本明确的条件接受；这没有把同一例外移植到真实沟槽。

影响与处置：旧 v2 可能接受压力/垂直动量未达标的沟槽问题已经消除。无需新增第七方向、几何或物理验证任务。

## B2：tight 不能复用普通停止精度——关闭

位置：`acceptance.py:11–20`、`:65–73`；`prepare.py:187–205`；`postprocess.py:328–332`。

最终唯一 `RULE` 结构带 `version=v2.1_stopping_fix`、`declared_residuals.normal/tight` 和 branches；prepared manifest 中的整份规则与该 RULE 独立比对相等。runner/reader 使用同一 `steady_stop(text, meta, rule, ...)` 接口，未留下两套 schema 或新旧 helper 混接。

本固定发布的普通 p/U/v 均为 1e-10、tight 均为 1e-11，比较均严格小于；tight 线性容差 1e-13，其余 1e-12，relTol=0。tight 从 fine 初始化可以保留，但自身末轮完整字段必须达到其更严格门槛，然后才使用原有 `|Ktight/Kfine−1|≤0.05%` 检查。K 接近不能替代 tight 自己达标。

## B3：真实日志轮次、正常结束与停止原因——关闭

位置：`acceptance.py:41–63`、`:83–100`；`run_one.py:203–221`；`postprocess.py:235–279`；本机 `simpleControl.C:79`、`convergenceControl.C:89–125`、`Time.C:884–950`。

本 C++ 不逐轮打印 Time；固定 `nNonOrthogonalCorrectors=0` 下每轮确为一次 v，或各一次 Ux/(Uy)/Uz/p。原生检查取 solvei=0，向量取初始残差 cmptMax，并用严格 `<`。当前解析器按首字段开始分轮且核完整顺序，不再任意抓全文末条 p/Ux。

必须独立 exit=0、最后非空行 End、完整末轮字段达标。native 字符串没有绕过字段标准；其报告须出现在最后求解之后，报告值须等于 startTime+轮数。源码 `simple.loop` 先检查上一完整轮收敛，再进入 `Time::loop`；本机 `Time::running` 使用 `value < endTime−0.5*deltaT`，因此当前 `ceil(endTime−startTime−0.5)` 在 deltaT=1 及 seed start=0.5 下正确。native 与 cap 同时满足时 native 优先符合本机调用次序。正常 cap 接收明确属于事后判定，wall-clock/异常/无法归类的提前结束均拒收。

读回器独立重算 stopping 字典并严格比对，并核原生最终场目录时间等于 startTime+轮数。顺带核对 Time 在较大半整数时间下会自动增加 timePrecision，当前 `.5` 末态命名没有发现由默认六位精度导致的不兼容。

## B4：种子、映射和末态来源闭合——关闭

位置：`run_one.py:93–147`、`:199–244`；`postprocess.py:132–173`、`:217–283`；`freeze_release.py:44–49`。

源在映射前须通过本 release 的完整 `read_case`；源 case/run/release、独立退出/完整日志、收敛、CSV、原生终场、五份网格身份均核验。源时刻直接取回执绑定的终场时刻，不再任意选源目录最新时间。几何/方向与 canonical 前一层依赖由运行前和递归读回共同约束。

mapFields 的绝对路径和 SHA 已列入外部指纹；seed 回执绑定 source receipt/run/release、源时刻/原场/mesh、映射 argv/log/exit、seeded checkMesh 日志/exit、目标时间及映射字段 SHA。后处理递归验证固定 coarse→mid→fine→tight 链，源漂移或断链拒收。目标映射输入在 `runtime/seed_inputs` 留存并逐字节验证，避免 `purgeWrite` 清除 0.5 后无法查原初场。

只读核对本机 `MapConsistentVolFields.H`：`-consistent` 情况下目标字段尚不存在时会走 NO_READ 创建分支并写入目标时间；因此不预建 0.5 原场与本机工具实现相容。没有执行实际映射，不将源码兼容性核对写成实际 mapFields 成功证据。

这里的来源闭合依赖冻结可信 runner 实际产生回执与 SHA，并保留原文件；它不是对人为重写全部原始文件及所有回执的密码学签名认证。当前任务无需引入额外签名系统或扩大物理算例。

## B5 与预算/文档一致性——关闭

位置：`acceptance.py:23–30`、`:71–73`；`postprocess.py:272–275`；`PROTOCOL.md:62`；`prepare.py:30–36`。

正式 stopping 字典比较不再除以 measured residual，零残差可被正常接收且 0/非0 字典不一致会被拒收。`same_residual` 对 0/0、0/非0、负值和非有限值的辅助边界处理合理。审查过程中发现协议原称正式比较使用相对≤1e-9、实际代码使用整个字典严格相等；主代理已在最终快照修正文档，现明确辅助函数不放宽正式字典比较。此项已关闭，未要求降低接收严格度。

实际 manifest/case 配置与文档一致：coarse 1800s，flat 3600s；mid/fine/tight 为 14400/43200/43200s。它们是预算上限，不是工期或收敛保证。

## 范围保护与仍未验证事项

- 固定四沟槽几何六方向，6 coarse+6 mid+6 fine+6 tight+2 flat=26 输入，无扩点。三主网格、tight 定义、K 单位 m³、六方向既有比较输入未改变。
- 导度差 2%、基准 A 差 2%、角差 0.40°，及原网格/代数条件保持。coarse/mid 仍保存收支诊断但不额外套用最细层 0.1% 门槛；fine/tight/flat 原有检查继续执行。
- `run_one.py:172–177` 在任一真实沟槽前逐一独立读回本 release 的 P/T 平板，二者都须 LOCAL_CHECKS_PASS。v1 平板或带外长跑不能顶替。
- 本 release 两平板及六方向全部未执行；新停止规则下的实际收敛、映射后的数值表现、墙钟预算够用、网格参考资格和 2% 交叉一致性均未验证。46 合成检查及本报告不能替代这些证据。
- 原 v1 T 平板 FAIL、S4/D4 历史 FAIL，以及 `reference_qualified=false`、`strict_error_bound_established=false`、`submission_ready=false` 不变；论文数字、系数及既有资格 Gate 不因本报告改变。
- 最小后续动作是主代理将**已审同字节快照**同步正式 v2 并更新项目交接，保留旧未放行快照。实际求解仍须作者另行授权；不自动批跑、重试、增配或进入下一 Gate。

## 最终受审 SHA256

| 文件 | SHA256 |
|---|---|
| release_manifest.json | f1531d4091a6279a5db2df5cff75875d279d4ffc981f52ae5502bedd98ffc292 |
| acceptance.py | 651518eaec217dfa33ea962989a9437bce170a1cb90ffe82b65b849871c643a4 |
| run_one.py | 8d3c41e4301740216296678c6b4024112157b314301ddeaf0cb76864ff670191 |
| postprocess.py | efc8db0505a99ea12e2b9b16abf96f10ffa1fc9c04d34f214012e3d906f7bca9 |
| prepare.py | 4fe82a6e814696ae1ea68dae60cb232c123fe740cbe2d597cb08dcb94e92f5a0 |
| freeze_release.py | 83ce76183ec7915eb6f16f00ede55d9a259b902b2c1c88b44e2216a622dcfa33 |
| PROTOCOL.md | edfea85061696f854721015fe224db5a26df0a38a7fda5a6ad127d9a58bc82cb |
| run_config.md | e5e29e48587c5b943fb377be062d5a028097f5bbdb9ff089fb5a71a312ea1961 |
| prepared_manifest.json | 3f13b93533164b5931562c2a49374c3b2ca004dc6296d0df08b2e53849f40f0f |
| solver/paper1StokesReference.C | 7936bc254f6d1577a72adaff9b627e102ed1600f282fbbd9a179fe7a3ace5c84 |
| bin/paper1StokesReference | 73b1f633b96f0074abcd30358e83b57790f00c29aef1ef493f08345f3453f352 |
| tests/test_stopping.py | 108fcba0e04540a5ea1dcd984f79f8b5d499f265048a1bc96e4545786c9f645a |
| tests/test_postprocess.py | 2f083800f85f589a7a070866826c16eab57906a8b88be0442e39adb791ab8c78 |

下一步模型：GPT-6.1 Sol｜High；任务：同字节同步正式目录、核指纹并维护项目交接，无求解启动。若改变上述冻结科学规则或开始最终结果放行审查，再使用 GPT-6 Astra｜High。

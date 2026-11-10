# GHY物性与成对输运准备停点

2026-10-21。本轮执行范围：补查GHY物性、判断12mPa·s近似并准备Kxx/Kyy方向算例。没有新增OpenLB计算，不替换第一篇范围，不改旧协议或历史PASS/FAIL。

## 已完成

已核项目状态与旧选胶资料，有限联网检索GHY身份；没有找到能与用户样品关联的ρ、σ、θ证据。用户明确产品/配方与两表面材料均不知道，水辅助脱模加入时点也不清楚。未知项已保留null；没有用其他胶水、水接触角或“典型值”冒填。

已建立GHY材料表与测量记录模板、参数补全路径，并逐点计算12mPa·s近似偏差。新建 `paired_transport/Kxx/case.json`、`Kyy/case.json` 与唯一 `shared_case.json`，两方向不允许覆盖材料/初态等共同项，配套只读 `preflight.py` 与防错回归检查。

## 当前判断

- ρ、σ、实际两表面润湿：**未补成可用数值**；需要同批样品/实际表面测量或可验证的原始资料。未知品牌并非永久障碍，同批样品与表面追溯可以建立依据。
- 水：**角色未知**。若只在流动/固化后帮助脱模，可论证前段不含水；若输运时已有水膜，则胶/气两相可能不足，不能继续默认为两相。
- μ=12mPa·s：仅候选。对30、40、50s⁻¹三个观测点，以实测值为分母偏差5.5066%、0.7994%、1.1958%；对10s⁻¹偏差37.5585%。没有连续平台、独立重复或模拟局部剪切率覆盖证据，不认可为整个10–50s⁻¹或更宽范围的已验证恒黏度模型。
- Kxx/Kyy：**成对配置与协议草案已建立**；不是已经可运行的真实GHY OpenLB算例。物性、初态、驱动/通量/窗口、单位映射和求解器均待完成。

## 检查证据

`materials/GHY_20261014/assess_constant_viscosity.py`独立exit0；其JSON保存分母不同的两种误差口径。`paired_transport/test_preflight.py`五项防错测试exit0；检查缺物性/水角色、方向映射、初态覆盖、候选值/非法数值和单位等不会被放行。

`paired_transport/preflight.py --report .../preparation_report.json`实际exit2，表示准备不足；pair_structure_consistent=true、preparation_complete=false、simulation_started=false。该退出码是检查程序主动报告缺项，不是仿真FAIL，也不是物理或数值Gate通过。

没有新OpenLB源码、可执行文件、编译、几何/q运行审计、短测、正式run或独立数值验收。NUMERICAL_GATE、RESULT_PASS、geometry_PASS均NOT_EVALUATED；run_id不适用。Python检查通过不能代替以上任一步。

## 下一条具体动作

接续核查仍未收到新工艺或实测数据；物性与水时点未补全，参数未冻结。已新增 `materials/GHY_20261014/EXPERIMENTAL_CONFIRMATION_REQUEST.md`，把实验端须确认的实际顺序、样品批次、两表面和测量记录集中成一页；冻结判断见 `paired_transport/freeze_decision_20261021.json`。本轮只查记录并整理缺口，没有重复测试或新增计算/验证。

先取得可编号的同批GHY与实际表面处理/工艺顺序记录；按 `materials/GHY_20261014/PROPERTY_COMPLETION.md` 补25°C密度，随后带正确密度做液气表面张力，两实际表面润湿与流变稳态/重复。若连样品/表面都无法取得，应明确转为理想流体方法研究，不能继续声称真实GHY预测；本轮尚未作该范围变更。

待水是否参与输运、ρ/σ/θ和恒黏度适用范围有依据，再冻结共同初态和K提取协议，实作并编译求解器。若需要长算，仅交付一条核验过的tmux命令，由用户启动；本轮未生成或交付任何长算命令。

入口：`README.md`、`PARAMETER_CARD.md`、`materials/GHY_20261014/PROPERTY_COMPLETION.md`、`paired_transport/PROTOCOL_DRAFT.md`、`paired_transport/preparation_report.json`。共享状态与最新日期交接已同步本停点。

# S3正式四条范围与资源审查结果

审查时间2026-11-03 15:44:03 +08:00；使用peer-review技能核对用户自有项目协议与实现。结论：**S3-FRD-v1范围与当前v1.1准备B及控制器兼容；正式授权未收到、执行绑定未生成、计算未启动。**

主协议PROTOCOL.md审定四条冻结身份/顺序、原URV科学门、资源与真实授权绑定前条件；formal_binding_plan.json仅为关闭权限的不可执行计划。

四条按低P→低T→高P→高T顺序，a50000/200000、dx2.5nm；a100000两条只读复用原S2中档各自合同，未纳入新批准列表。每条独立验收通过才下一条；第三条之后P三点L≤0.001才第四条；第四条后检查T。失败即停、不重跑/加时/进入S4/S5。原单条数值/几何与0.1%控制阈值未改。

B SHA a5b69ec95180bf92327a3bba1311639dd2a5fb1bec412cd80c3869dda2a47f92，2609输入全部一致；完整12+4原始零步收据及独立验收绑定仍通过。四正式目录净，无launch_attempts/analysis_results或正式release。B默认只读入口退出0、solver_executed=false；B被正式/零步权限验证拒绝。原S2中档双向完整来源和数据通过，只读复用不迁移授权。原同一ELF及15动态库一致。保护文件2616份前后未变。

资源决策保持1进程/1线程、8GiB每受限进程地址空间、启动内存≥12GiB/盘≥100GiB、逐条盘≥8GiB、每条输出4GiB。当前资源快照18.77GiB内存/317.64GiB盘满足门槛；不预留未来资源。相同中格S2真实P/T求解843.95/479.97s支持优先复用既定4h预算，无需新增性能推进，不承诺S3耗时。

四条求解各4h合计16h；检查外层各1h合计最多4h，文件/来源校验另计，非20h严格批次上限。字段读取器1h在外层检查之内，不另外叠加。协议如实说明超时只限定直接进程，若超时保持HOLD，另查读取器残留，不声称整个进程树已清理；本轮不改实现。

授权前条件与未来字段清单已明确：用户真实覆盖四条顺序续行和标准检查、原预算/失败停止/仅手动启动；未来release继承B全部输入并追加B/侧文件、真实授权及本范围证据，绑定固定四身份和原零步收据；新日志不列为不可变输入，保留原包。没有生成伪授权记录或可执行命令。

本轮第一次只读汇总因本报告脚本dict重复mode字段中止，发生于资源/进程快照前；旧脚本和错误另存audit_scope_first_pass_failed.py、first_pass_error.json。仅修正新报告脚本后复核成功；计算包、B及科学判据均未改。这是本轮报告工具问题，不是CASE物理/数值失败，未重跑求解器或原生审计。

本轮CASE写0/源码0/构建0/native0/VTK reader0/推进0/测试重跑0。科学门、S3控制/参考/模型/物理/投稿状态不升级，历史FAIL/旧v1 HOLD/F04 OPEN/作者声明范围保持。

证据：verification.json、configurations.json、S2_baseline_references.json、resources.json、formal_binding_plan.json、clean_environment_ldd.txt、protected_inputs_before.json、audit_scope.py、PROTOCOL.md、AUTHORIZATION_SCOPE.txt、final_integrity.json、report_manifest.json。共享状态/最新交接同步后可从文件接续。

下一具体动作：获得明确采用并覆盖本完整四条的真实授权后，复核封存与届时资源，生成正式独立执行绑定并交付一条用户手动命令；保持不自动启动。建议GPT-6.1 Sol｜High。

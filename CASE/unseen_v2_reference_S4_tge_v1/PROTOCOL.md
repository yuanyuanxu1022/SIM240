# S4-TGE-PREP-v1：已采用的最小隔离准备范围

本轮用户授权准备及其必要软件/静态验证，不授权任何原生、读场、PERF或正式求解。此文件不是启动合同。

## 物理与身份

仅T横槽+x，h30/d80/w120/P=Ly240nm，dx0.625nm，平均H70nm，a100000m/s²、nu1e-6m²/s、rho1000kg/m³、mu.001Pa·s、tau1、D3Q19_FORCE/ForcedBGK、x/y周期及Bouzidi静止无滑移。
J按平面面积归一（m²/s），K=nuJ/a（m³），U=J/H，R=mu/K；半步体力、MRP/A1质量与体积路径保持。S0专用h75密度捕获不适用。
同一S1 ELF及真实构建来源只读复用；原native_sources/Makefile不改、不重编译。
计划正式run_id=URV_S4_T_dx0p625_TGE_v1_20261104_01，planned_case_id含SUPPLEMENT，不属于原24条。正式只预留config/manifest，不提供执行入口。

## 准备A与软件边界

新stage/配置/只读检查/零步控制器/零步结果检查在新CASE隔离，原科学evidence、zero_evidence和read_fields以原绝对路径与指纹引用，不拷贝改写门槛。
准备A输入清单包含原完整构建/输入、原S4六条和失败报告、旧两基准的完成/接受、准备采用证据、全部新脚本/配置与已结束的软件检查记录；不绑定未来活动日志。
必要软件检查使用参数/权限/路径的拒绝用例与mock，禁止启动原生或pvpython。准备检查不得拿--execute做连通性测试。

## 后续3＋1（当前未授权）

仅describe/precheck/initialize各1次，全部推进0步，initialize后读回1份真实初态场。顺序固定、失败即停、不重试、不进入性能或正式。
建议每次原生和读取各300s、进程地址空间8GiB，12GiB可用RAM、首批100GiB/每次8GiB空闲盘、单次4GiB输出，1进程/1线程/1cuboid/overlap3。此为未采用资源提案；执行合同须独立绑定真实用户3＋1授权和该资源方案采用，不从旧S4许可继承。
执行前核A与当时资源、3个输出目录仍净。独立receipt/退出码、collideAndStream=0、几何/材料/链/q/体积、半步力初态、VTK闭包/单位/积分关联按原R1/R2检查。候选几何与峰值内存不能由静态预测替代。

## 新旧网格与科学停点

原5/2.5/1.25nm三档FAIL保持。新2.5/1.25/0.625nm追加分支只在独立采用/授权/正式完成接受后评价；r2/Fs1.25、差同号非近零、p正有限、中细差和GCI各≤1%全部保持。
本准备不实现正式预算、正式结果控制器、跨阶段聚合或新参考资格放行；均在候选接入/资源证据之后另定范围。没有以原12h自动改为38.5h或48h。
3＋1通过后仍须独立准备/授权有限PERF及正式计算。未授权时入口拒绝原生；reference_qualified=false、MODEL_COMPARISON/physical_validation未评价、submission_ready=false、S5未启动。

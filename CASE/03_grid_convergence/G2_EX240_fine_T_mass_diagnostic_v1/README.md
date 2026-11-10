# h75 / dx1.25 / T 隔离质量诊断准备包

状态：**STATIC_PREPARATION_PASS_NOT_COMPILED**。本轮只准备与静态审查，没有编译、precheck或solver运行。历史细T仍FAIL；当前目录不是新的正式参考算例。

依据：[既有独立复核协议](../../reports/fine_T_mass_audit_20261013_v2/fine_T_recheck_protocol.md)。新诊断只回答“普通double全域质量账本是否解释瞬态峰值”，阶段collision/stream/link诊断待同步高精度账本显示真实变化后再设计。

|文件|作用|
|---|---|
|[src/fine_T_diagnostic.cpp](src/fine_T_diagnostic.cpp)|从历史SHA匹配的细网格源码添加12个标记块；只接受T；原60000上限、收敛规则和门禁保留，另加4000步诊断截止|
|[src/mass_ledger.h](src/mass_ledger.h)|同一rho读取的旁路账本、材料指纹、binary64快照；不接收lattice/cell/geometry对象|
|[PROTOCOL.md](PROTOCOL.md)、[run_config.md](run_config.md)|范围、参数、验收及资源预算|
|[ledger_schema.md](ledger_schema.md)|CSV、掩模和密度快照格式及公式|
|[scripts/check_static.py](scripts/check_static.py)|去掉新增标记块后恢复基准；核对绑定输入，不启动计算|
|[scripts/test_arithmetic.py](scripts/test_arithmetic.py)|Python参考算术与二进制格式测试；明确不等于C++运行验收|
|[scripts/snapshot_format.py](scripts/snapshot_format.py)|未来double快照独立解码；拒绝重复ID、截断、错误指纹和NaN|
|[reports/preparation_manifest.json](reports/preparation_manifest.json)|现有证据/当前库/配方SHA、环境、算术结果、缺失编译/程序状态|
|[reports/source_additions.patch](reports/source_additions.patch)|原源码与隔离副本差异|
|[reports/static_review.md](reports/static_review.md)|静态验收结果及边界|

检查复用命令（在本机SIM240目录执行；只读检查）：

```bash
python3 -B CASE/03_grid_convergence/G2_EX240_fine_T_mass_diagnostic_v1/scripts/check_static.py --check-bound-inputs
```

没有运行脚本或tmux启动命令。Makefile默认只显示准备状态；compile目标要求后续任务显式设置ALLOW_BUILD=1，并先验证输入SHA。它只构建本目录独立binary，不覆盖旧程序。编译前还要确认静态审查结论、保存完整编译日志和新程序SHA；目前这两项明确为未产生。

下一任务若授权编译，先编译与零推进precheck审查，再另行准备短程运行目录与独立exit记录。当前源码保留旧return逻辑，预计短程因未收敛/旧质量门禁以3退出；应同时读diagnostic_status，不能用进程退出码单独认定诊断覆盖失败或CASE成功。

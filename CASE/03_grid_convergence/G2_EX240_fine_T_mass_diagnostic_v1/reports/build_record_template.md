# 后续独立编译记录模板（当前未产生构建）

状态：NOT_COMPILED。binary SHA=null，build stdout/stderr未创建；本文件只给后续验收清单。

1. 确认本准备包preparation_manifest SHA、当前输入/库/编译器检查结果，并记录独立build_id和时间。
2. 保存完整编译/链接命令、compiler版本、MPI compile/link flags、环境和目录；Makefile记录候选配方，实际命令以完整日志为准。
3. 独立输出到本CASE/build/fine_T_diagnostic；拒绝覆盖旧/现有binary，拒绝改旧CASE/build。
4. 保存独立编译退出码、完整stdout/stderr、source/header/Makefile及binary SHA、库HEAD/dirty差异/include/lib SHA。
5. 执行后续授权的零推进precheck时，记录geometry/q/material/converter与独立程序/shell退出。它仍不证明质量根因或短程运行成功。
6. 对实际C++旁路累加做非LBM算术测试，核对DBL/LDBL位数、重构/一致性、二进制write-read；当前Python参考测试不能代替它。

后续run必须另有新run_id、源/程序/协议/库hash、完整参数、MPI/thread、独立log与shell exit、diagnostic_status、所有rho/mask快照hash。不能把本模板内容记作已完成证据。

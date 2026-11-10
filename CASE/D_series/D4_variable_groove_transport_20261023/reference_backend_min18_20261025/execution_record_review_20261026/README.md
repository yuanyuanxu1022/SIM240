# 失败向量、独立子进程和逐项资源：待审实现，未求解

2026-10-26。用户授权补齐记录链的准备实现，同时要求参考协议与运行许可确定前**不启动计算**。此目录是独立候选版本，保持原 `solver_result_review_20261025/candidate_solver.py`、`DRAFT_v2`、18项冻结白名单、G4 v1和历史网格FAIL原样。没有正式run_id、真实场、KSP实例或PDE求解。

## 接线范围

- [`recorded_solver.py`](recorded_solver.py) 复制前一候选并只在异常路径增加归档回调。它仍先核18项执行位、release和A/b哈希，之后才有唯一的 `ksp.solve()`。若未来求解迭代/残差/周期回填/压力后处理失败，异常处理优先取**回填前**代数向量；若尚未创建向量则如实标缺；连同KSP原因、迭代数、残差历史和已有诊断送归档。归档本身失败会抛独立错误，不能悄悄把失败写成成功。当前该KSP分支未执行，所以不能说已验证其运行时行为。
- [`failure_archive.py`](failure_archive.py) 写唯一失败目录、`partial_algebraic_solution_before_backsub.npy`和 `failure_manifest.json`。即使向量含NaN/Inf也逐字节保留，并单独统计非有限数；它不是合格流场或数值PASS。输入/矩阵/右端/发布版本绑定由调用者带入。
- [`child_record.py`](child_record.py) 的真实入口先读磁盘上18项白名单并核release、命令与输入哈希，当前18项全部在创建目录/子进程前拒绝。未来若经另版协议和审核更新白名单，单项子进程会保存`STARTED.json`、完整stdout/stderr、独立退出码、前后输入哈希、日志哈希及**全部已写文件**的路径/大小/哈希，失败留下的部分文件也在清单内；通过`wait4`取得**该直接子进程**的峰值RSS、CPU时间/页错误，并量测输出目录文件字节。它不借用父进程的累计子进程高水位。
- [`reviewed_worker.py`](reviewed_worker.py) 为未来受审的单项工作进程：同样先查冻结白名单，再核设置上界和源哈希，组装后绑定矩阵/RHS哈希，调用带失败归档的候选；若成功，只记录`UNVERIFIED`原始数组及诊断，仍需独立科学验收。当前命令行入口对18项均直接拒绝，未进入组装。

完整链的设计是：父进程捕获→子进程再次核白名单/release→组装与候选求解→成功写16组原始数组，或失败保存部分代数向量→父进程留下独立退出/完整日志/逐项资源。**这条真实链没有运行测试**；本轮只核每个关键接口和拒绝顺序。[合成测试](evidence/synthetic_tests.json)验证带NaN/Inf的失败向量位模式、无向量失败、两次独立短子进程exit7及各自资源、完整日志/部分输出、无覆盖，并核真实入口及候选在白名单处拒绝。[独立静态复核](evidence/independent_review.json)为`PASS_PREPARATION_ONLY`，4233保护路径无变。

## 仍须完成后才能提运行许可

1. 冻结参考协议与真实release，独立审查worker/父进程**同一份**逐项命令、source/plan/A/b哈希、输出目录和run_id绑定。现在release JSON只是待审数据结构，字段`APPROVED`字符串不能独自成为授权；当前白名单保持false。
2. 实际KSP异常分支、成功写出和父子进程连跑均未验证；需在获得运行许可后的受控小问题中验证，同时独立复核所有原始文件。程序被整机断电、父进程自身被杀或磁盘写满时，不保证完整最终manifest；`STARTED.json`和已写部分文件必须作为不完整证据保留。
3. `wait4`只计工作进程本身，不保证计入其可能创建的JIT/外部子进程；当前单进程后端尚未完成正式运行证明。没有运行时RAM/时长硬限制或自动终止机制，4GiB/4GiB/2小时仍是未验证的草案预算；超预算只能在逐项结束后决定后续RESOURCE_HOLD，不能降科学门槛。
4. 通量/散度、周期迹、能量、物理单位、平板/MMS解析误差、标量9项及独立验收尚未补齐。独立exit0、KSP收敛或写出完整均不自动构成 `NUMERICAL_GATE`、`RESULT_PASS`或`geometry_PASS`。

当前 `NUMERICAL_GATE=NOT_EVALUATED`、`RESULT_PASS=false`、`geometry_PASS=null`、预测HOLD。无真实计算启动命令，无Git提交或推送。

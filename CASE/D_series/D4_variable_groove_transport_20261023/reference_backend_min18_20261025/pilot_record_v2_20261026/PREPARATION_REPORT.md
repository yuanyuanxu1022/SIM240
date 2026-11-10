# 三项缺口的准备实现与无求解核查

2026-10-26。版本`D4_PILOT_RECORD_V2_20261026_PREPARATION`。

**本轮授权的实现与无求解测试完成，准备复核PASS_PREPARATION_ONLY；真实运行许可仍为HOLD。** 没有实际有限元矩阵组装、PETSc实例/PDE求解、OpenLB编译或推进、公式重拟合、Git提交/推送。所有短进程均为固定合成夹具，不是物理算例。没有实际pilot run_id，模板中的编号仅是未发布占位符。

## 1. 按终审三项缺口交付

|终审项|本轮实现|已有验证|还不能据此声称|
|---|---|---|---|
|B1 一致的执行许可|common.py定义新合同；assembly.py使用旧物理plan，另带execution_contract；solver.py核新合同和旧N8装配SHA；父进程/worker核同一run_id、路径、命令、环境与来源|旧plan仍false；错ID/物理输入/命令/环境/输出/缺依赖/默认未授权均拒绝；真实public solver与worker未授权时先拒绝|未产生批准合同；没有运行真实装配/求解链|
|B2 可复算记录|保存本次A的CSR、b投影前后、约化n、gauge、物理plan、单元P2/P1映射及16组场数组；独立退出/日志、输入前后SHA和文件清单。KSP创建失败、快照提取失败保留首个错误；工作卷归档写满时在独立记录卷保存原始错误与归档错误|手写数组重算残差；改错向量并重新哈希仍被数值读回判FAIL；文件损坏/多文件拒绝；假KSP成功、创建/求解/残差/回填失败，失败向量实际落盘读回；P2边中点/P1映射检查|真实矩阵/解的写出和真实PETSc异常仍未试；原始场保存不能替代完整物理验收|
|B3 有限资源与停止|resources.py实现超时/终止/清空后代；真实内存要求cgroup v2，工作空间要求已有专用容量≤512MiB的tmpfs；父记录留独立卷|短合成超时/输出抽样超限停止；64MiB cgroup实际触发OOM并记退出−9；普通磁盘不能替代工作卷|本轮未准备专用工作卷，未实测该卷写满路径；4GiB生产预算和真实后端耗时未验证|

旧18项CSV和contract不是执行许可；它们描述原物理输入并继续保持false。新合同并列提供执行权限，没有猴子补丁、修改旧全局变量或将旧plan标成已授权。首项只限MMS mixed N8；第二项平板/其余17项都没有入口许可。

真实A/b需要匹配旧N8预检字节SHA；这不是重新组装过的证据。新assembly适配只增加投影前b的保存及并列合同；旧方程、驱动、压力符号、零空间和物理输入不变。solver与前版差异见[evidence/review_diffs/solver.patch](evidence/review_diffs/solver.patch)。

## 2. 无求解测试及独立进程证据

[最终测试日志](evidence/test_no_solve.log)与[独立测试退出码](evidence/test_no_solve.exit_code)：**16个测试方法、0失败、0错误、0跳过，独立exit0**。精确列表和是否加载后端见[test_summary.json](evidence/test_summary.json)。假KSP是测试文件中的Python对象，没有调用PETSc；测试进程未加载petsc4py、DOLFINx或MPC后端。

实际保留了每个合成进程的STARTED、stdout/stderr、独立退出码、前后输入哈希及已写文件清单。当前最终批次证据入口：

- `evidence/process_edf90e44f5/fixture_index.json`：手写数组成功、exit7部分输出、超时、输出抽样超限四个短进程。0.4秒超时夹具约0.427秒终止并记录−15；输出监测夹具设100KiB，观测约196649字节后终止，这是**抽样超调**，不是硬磁盘容量试验。
- `evidence/memory_6394e68a67/memory_test.json`：真实内核memory.max=67108864字节的短夹具，memory.peak=67108864，OOM被记录，独立exit−9、原因CGROUP_MEMORY_OOM；该cgroup只包含合成测试进程，结束已清空并删除。
- [cli_checks.json](evidence/cli_checks.json)：默认预查、独立读回、仅查询依赖元数据各有命令/日志/独立exit0。默认预查明确EXECUTION_NOT_AUTHORIZED，无真实输出目录。
- [independent_readback.log](evidence/independent_readback.log)：另一个解释器进程只读取合成数组与父记录，残差/零空间/压力平均/周期及壁面读回通过，21个工作文件哈希完整。record_kind明确SYNTHETIC；没有将夹具标为流体结果。

早期12/14/15项阶段测试及来源绑定保留为first/second/third/fourth_attempt记录；后续因增加失败快照/P2映射检查、隔离JIT配置影响及保存工作卷写满时的首个错误而更新源码后重新测试，未覆盖这些早期记录。以上数量只指最终测试集，不能把各轮累加成独立科学验证数。

## 3. 独立读回的实际范围

[readback.py](readback.py)不导入求解器或组装函数，以CSR逐行乘法计算`‖Ax−b‖/‖b‖`，分别核投影前后b、左右常数压力零空间、相容性和投影变化；检查压力原值/去均值、速度/压力到混合向量映射、周期/固壁值。真实记录必须有完整16数组、三角网格和单元P2/P1映射，并与父记录的run_id、目录、合同SHA、文件清单一致。

命令行只读取已有目录并输出JSON，不写运行目录，也不自动推进阶段。没有父进程记录时，真实记录不能获得读回通过。通量/能量、解析L2误差、强散度、三格/ALG/QUAD及完整18项验收明确为NOT_EVALUATED。读回PASS只限上述代数/记录检查。

## 4. 来源、环境与资源前提

[source_lock.json](source_lock.json)绑定354个去重路径，包括13份新Python模块、旧物理/压力/记录接口、协议来源、环境锁、实际解释器/核心二进制及相关后端Python代码。新模板绑定source lock的SHA，必需模块缺失拒绝。各集合重叠，不与旧保护计数相加。

[独立准备复核](evidence/independent_preparation.json)确认旧4233保护路径和前次终审138份输入均未变；13个新模块语法解析通过。依赖名称通过仅查询元数据确认，没有导入后端求解。

检查本机已安装DOLFINx的jit.py发现它支持用户JIT配置覆盖缓存位置；为避免外部配置改变工作卷记录口径，新环境固定XDG_CACHE_HOME、XDG_CONFIG_HOME及TMPDIR到新工作目录，数值库线程固定1，HOME保留原值。没有修改用户配置或base环境。

真实入口的工作卷条件目前**未准备、未端到端测试**。实现选择拒绝普通磁盘，要求已有、空、专用、容量≤512MiB的tmpfs挂载点；本轮不挂载、不调整系统。父记录位于另一磁盘卷以保留空间耗尽时的退出证据。内存上限机制有小夹具实证，但不意味着4GiB对真实计算足够。600秒超时含组装/JIT/求解/写出，终止有20ms监测间隔、5秒宽限和调度延迟。

内存限制接口口径采用[Linux内核官方cgroup v2说明](https://docs.kernel.org/admin-guide/cgroup-v2.html)。memory.max存在短暂超调可能；本报告不将事后RSS或单个夹具峰值当作生产预算上界。

## 5. 当前停点

本轮交付的是三项修订的代码、记录合同草案、无求解证据与独立读回入口。没有批准的真实合同，没有正式运行目录或流场；不能把准备PASS写成运行许可PASS。**尚待后续审查：新适配层真实后端接线、工作卷资源前提、正式诊断合同与具体授权。** 首次真实后端测试只能在取得许可之后进行，不要求提前证明它已经成功。

NUMERICAL_GATE=NOT_EVALUATED、RESULT_PASS=false、geometry_PASS=null，预测HOLD；旧网格FAIL、G4 v1、原18项及历史结果保持。项目当前状态与最新交接已同步；下一步只审本版本及明确剩余前提，不自动启动求解或扩展开发范围。

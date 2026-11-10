# GDI01宿主、独立检查器和全域包已实现；编译与不求解审计完成

2026-10-30。用户范围：按GDI-v1实现并编译最小动量—压力宿主、独立检查器和全域GDI01包，完成不求解审计，暂不启动流场。交付入口为 [包说明](../../../CASE/groove_darcy_static_v1/README.md)。**本轮没有新流场run_id、没有调用压力solve分支，不能报告GDI数值或物理验证通过。**

## 实现与物理意义

[grooveDarcyStaticFoam.C](../../../CASE/groove_darcy_static_v1/application/grooveDarcyStaticFoam.C)通过标准fvModel::New创建porosityForce，再通过source(rho,U)装配物理动量矩阵。子类由运行时加载，类型和cellZone核对；宿主不包含K公式、不读取输入D代替实际模型。几何计算H，归一化速度只用于停止诊断；物理p/U内部初值为零。

首例对应原C01：V2横槽，h_m75nm、槽深100nm、槽宽/周期120/240nm，H=b125nm，24×48µm，16×32×1共512单元；全域groove区域包含0—511每个单元恰好一次。保持24/0Pa，侧边p零梯度/U滑移、z empty，无惯性、额外黏性或第二份Darcy阻力。源系数与方向由子类力响应探针独立读出，实际动量仍由标准wrapper装配。

采用原协议迹分裂外迭代和压力修正，完整动量残差和U/p外迭代变化参与停止。压力方程整体乘−1形成正对角对称矩阵，因此实际保守phi=phiHbyA+已装配矩阵flux()，与原协议标准Laplacian写法等价；没有改物理方程或门槛。冻结GDI-v1文件均以原字节副本保存common/，历史“未实现”字段不回写；本报告和preparation.json描述当前实现。

## 实际编译和不求解检查

宿主已在Foundation13（Build13-ced05121dd03、linux64GccDPInt32Opt）实际编译。子类共享库复用此前已编译字节，并与原源码/库哈希绑定，没有重编译原子类或改动系统源码。首次编译发现fvModels头文件目录层级错误、第二次发现finite辅助函数与系统符号冲突，均已修正；三份编译日志保留，最终编译成功且无上述警告/错误。首次wmake产生的无用空lnInclude目录已移除，不保留安装目录改动。

已实际执行：

- checkMesh：512单元、二维、正体积、正交；Mesh OK。
- 新宿主auditOnly：标准porosityForce实际选择grooveDarcy，512/512区域覆盖、实际系数响应、零初场、正动量对角、对称正对角压力矩阵均核对。审计分支返回位于唯一pressure.solve()调用之前；输出solve_calls=0，日志无压力求解。
- Python独立静态核对：512单元/1072有效面、坐标/面积/体积、初场、实际D/H、实际矩阵对角/源及rAU核算满足；原SDI的3个纯数据函数AST与原检查器完全一致。
- 四种原生拒绝测试：半区覆盖、错误压力单位、非零初始压力、错误槽向，都仅执行auditOnly，均以预定原因非零退出，没有进入流场求解。这些是预期拒绝测试，不是新物理算例失败。

证据副本在本目录logs/与audit_evidence/；包内原始准备记录为reports/preparation.json、reports/static_audit.json、reports/negative_audit_tests.json。宿主审计病例在build/audit_case；正式cases/GDI01模板没有审计/流场输出，不能把两者混用。

## 独立结果检查器

[analysis/check_results.py](../../../CASE/groove_darcy_static_v1/analysis/check_results.py)独立于C++宿主读取完成后的运行，只接受真实GDI01身份；旧C01身份不会冒写进新manifest。保留原SDI的23项单端指标，再加原协议规定的接入守卫，并分别与既有C01二维/旧OF作4项对照。实际总检查数由未来读取后的报告给出，本轮没有“新流场PASS检查数”。

检查器读取源/二进制/库/字典/协议/参考绑定，核独立退出和压力求解日志/外迭代次数，解析原生p/U/J/phi/phi_U并逐值对CSV。完整动量核对从压力和边界独立重建梯度，从D响应和U复算力；验证延期源项、矩阵对角、完整力平衡、最后一步U/p变化、压力残差与面通量收支、能量及历史。保留每份原始输出哈希，分析仅写到新的外部报告，不覆盖运行数据或自动执行仿真。

14项单元/回归测试已通过：包括明确标为人工内存数据的解析场，以及错误力、矩阵、源、梯度、未收敛旧速度、错误D、缺区/缺历史、NaN和错身份拒绝。8组既有C01–C04数据的全部23项指标/输出与原验收逐项相同；原生字段解析器还回读了既有C01实际输出。没有写出伪造GDI运行包或把人工数组当成仿真证据。**新宿主实际求解分支及完成后整条验收路径仍待后续真实运行验证。**

## 运行包、绑定与边界

scripts/run_gdi01.py默认仅只读预检，不创建runs目录或分配run_id。显式执行分支要求新的GDI01_v1_编号，拒绝覆盖；封存源/二进制/库/网格/字典/检查器/参考快照，串行300秒超时、2GiB地址空间上限、独立退出码，失败即停，不重试、不自动分析、不进入下一例。峰值RSS未测量。

发布清单common/release_manifest.json保留每份包文件及ldd实际运行库哈希。默认预检输出在本报告目录preflight.json；准备包“已实现/已封存”与“已获准/已启动”分别记录。本轮未交付tmux命令，也未创建运行目录；新run_id=null。

```text
host_source_prepared: true
host_compiled: true
result_checker_implemented: true
full_zone_GDI01_template_prepared: true
no_solve_audit: PASS
read_only_preflight: PASS
flow_solved: false
run_id: null
NUMERICAL_GATE: NOT_EVALUATED
RESULT_PASS: null
geometry_PASS: null
physical_validation: NOT_EVALUATED
independent_human_acceptance: false
```

静态审计PASS只表示当前准备检查，不替代新运行的NUMERICAL_GATE/RESULT_PASS/geometry_PASS。原C01–C04局部接口PASS和旧D4_N8_diag_v3_1_20261026_v1（NUMERICAL_GATE=NOT_EVALUATED、RESULT_PASS=false、geometry_PASS=null）保持；reference_qualified=false、strict_error_bound_established=false、submission_ready=false、预测HOLD及历史FAIL不变。

## 当前停点

仅新建CASE/groove_darcy_static_v1及本准备报告，更新当前状态/交接。旧包、子类源码/库、协议和旧原始结果受保护，哈希核验见preservation_verification.json。没有新PDE求解、旧例重跑、拟合、挤压推进、下一Gate、提交推送或对外发送。

下一具体动作是用户另定GDI01启动时机；后续若获准，交付经绑定的新编号启动命令，用户独立运行，结束后只读验收。当前保持未启动，无新增长算授权。动态间隙连续性和独立物理参考仍按原接口另定范围。

准备报告沿用scientific-writing组织证据；流程文献引用与核对记录见 [GDI-v1原协议入口](../GrooveDarcy_static_protocol_20261030/README.md)，不将技能或AI检查称为独立人工科学验证。实现依据为本机Foundation13的porosityForce、fvModel、fvMatrix与correctPressure源码，实际编译和审计为本轮兼容性证据。

# GDI01：grooveDarcy 动量—压力宿主与独立结果检查器

本包按GDI-v1实现首个定间隙接入问题：V2横槽、24/0Pa、h_m=75nm、H=b=125nm、24×48µm、16×32×1。**宿主已实际编译；全512单元区域及不求解审计已完成；没有启动流场计算。** 本包不自动进入GDI02、SDI C05、挤压或下一科学Gate。

关键入口：[宿主源码](application/grooveDarcyStaticFoam.C)、[独立检查器](analysis/check_results.py)、[全域GDI01模板](cases/GDI01/constant/fvModels)、[原协议副本](common/PROTOCOL.md)、[准备报告](../../docs/reports/GDI01_preparation_20261030/REPORT.md)。`common/protocol.json`是原设计快照，保留当时“未实现”字段；当前实施证据在reports/preparation.json和准备报告，不回写冻结协议。

## 实际求解链

几何→运行时注册的grooveDarcy→标准porosityForce的source(rho,U)→物理动量矩阵→分步压力/速度迭代→J=HU与边界Q。宿主不包含K公式，不从输入表直接读取D作为求解系数，也不加入惯性、黏性Laplacian或第二份阻力。

H由与子类一致的几何计算，用于平均和通量。gdiProperties的velocityScale仅用于外迭代/守恒诊断的归一化，不用于初始化或驱动；初始内部p/U严格为零。实际阻力系数另以模型力响应获取供审计，未代替标准source装配。

压力方程按GDI-v1整体乘−1以形成正对角对称矩阵：−laplacian(rAU,p)=−div(phiHbyA)。因此保守phi=phiHbyA+所装配矩阵的flux()，等价于原协议phiHbyA−标准压力Laplacian通量；不能把符号变换只做一半。动量—压力外迭代最多2000次，每次压力PCG/DIC最多2000次，固定容差和松弛按原协议。

程序启动时必须显式指定auditOnly或solve模式，默认不求解。auditOnly分支在首次矩阵装配后返回，位于唯一pressure.solve()之前；使用零初场导出GDI_audit，输出solve_calls=0。正式求解模式需要GDI01_v1_前缀的新run_id；1/只是稳态输出存放位置，不表示推进1秒物理时间。

## 独立验收

analysis/sdi_metrics.py仅复制原C04检查器的3个纯数据函数，AST逐项相同，来源hash在common/metric_origin.json。外层检查器保留真实GDI身份，没有冒写C01，也不导入/调用C++求解器。

除原SDI指标外，检查器从单元压力和规定边界独立重建Gauss梯度，从实际力响应D和U复算力；核对矩阵对角、延期源项、完整动量残差、最后一步U/p变化、原始压力矩阵残差和保守通量的对应、外迭代/线性历史、原生场/CSV一致性，再分别对照C01二维与旧OF结果。阻力耗散不重复乘mu或体积。

只有完成运行、有独立退出记录、绑定输入/检查器相符、原始证据齐全，才能输出数值PASS。不求解审计、缺文件或错身份不能转为结果PASS。14项检查器单元/回归测试使用明确标注的内存人工解及已有数据；这些不构成新GDI求解结果或独立物理验证。4个原生非法输入测试始终使用auditOnly。

## 证据与权限

`build/bin/grooveDarcyStaticFoam`为本轮编译产物；`build/lib/libgroovePorosity.so`逐字节复制此前已编译子类库，未重新编译或修改原子类。正式模板cases/GDI01覆盖全部512单元；build/audit_case为独立审计副本，不能当成已运行流场。

scripts/run_gdi01.py默认只读预检，不创建runs/或新run_id。显式execute模式仅供后续用户单独启动：每次分配新编号、拒绝覆盖、封存全部输入/源/二进制/库/参考快照、串行300秒超时和2GiB地址空间限制，失败即停、不自动重试/验收/下一例；峰值RSS尚未测量。准备状态和启动授权分别记录。

本轮无流场run_id、无新压力/速度解；GDI的NUMERICAL_GATE/RESULT_PASS/geometry_PASS仍未评价，physical_validation=NOT_EVALUATED。旧C01–C04验收与历史FAIL不变，reference_qualified=false、strict_error_bound_established=false、submission_ready=false、预测HOLD保持。宿主求解分支未执行，首次实际收敛和运行输出仍需后续计算核实。

挤压接口仍见冻结材料common/squeeze_interface.json和原报告SQUEEZE_INTERFACE.md；本包没有间隙推进、挤压源、两相或载荷积分。

## 维护入口

Allwmake只编译宿主；prepare_case.py只准备一次模板；audit_case.py只检查既有审计输出；seal_release.py只封存发布和ldd运行库。源码或字典变更后须重新编译/审计/测试/封存，不能直接沿用旧release。运行命令未在本轮交付，当前按用户要求停在准备完成。

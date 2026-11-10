# 诊断输出 schema v1

所有诊断输出只属于新run。旧diagnostics.csv/result/result_summary/boundary仍由原代码写出，schema和门禁不变。它们与mass_ledger按step一一对齐；原diagnostics中的窗口是J统计，不是质量窗口。

## mass_ledger.csv

|字段组|定义|
|---|---|
|step,time_s|整数step与step*dt，连续0–4000|
|core_nodes,material0–3,material_hash|完整core计数，流体material1=3686400；hash是所有唯一ID/material的FNV-1a 64位；整数解析不可转浮点|
|legacy_M0_kg,legacy_M_kg,legacy_e,legacy_peak|原double基准/当前质量/当前误差/全程峰值，没有替换|
|volume_seq_m3,density_integral_seq|原volume和rho积分，普通double不同乘加路径|
|nominal_M_kg|整数N*rhoPhys*dx³，用long-double表达，独立参照，不作为原门禁分母|
|mass_neumaier_kg,mass_long_double_kg|前者对原double物理质量项补偿；后者逐项long-double乘法及求和|
|rho_neumaier,rho_long_double|rho和；后者仍可能包含长序列累加偏差，不能替代稳定delta交叉检查|
|delta_neumaier,delta_long_double|sum(rho−1)，输入来自同一computeRho的double值|
|M0_neumaier_kg,M0_long_double_kg,delta0|各算法step0自己的同精度基准|
|e_neumaier,e_long_double,e_delta|各自相对基准的质量变化；e_delta=(delta−delta0)/(N+delta0)|
|max_e_neumaier,max_e_long_double,max_e_delta|各自全程max绝对误差，只记录诊断，不授予正式PASS|
|bias_t_kg,bias0_kg|legacy_M−mass_neumaier，用long-double做差；差异包括double项乘法与求和路径|
|reconstruction_residual|[(massComp−M0comp)+(bias_t−bias0)]/legacy_M0−legacy_e；重构检查而非独立守恒证明|
|agreement_relative|max(abs(eComp−eLong),abs(eComp−eDelta),abs(eLong−eDelta))，目标≤1e-13|
|double_mant_dig,long_double_mant_dig|实际C++编译平台DBL/LDBL位数；若long double不更宽，高精度来源不足|
|Jx,Jy,Jz,Q1,Q2,Mach,rho_min,rho_max,finite|来自同一原Measurement，没有再次读取速度或修改force|

header按long-double max_digits10写文本，double值可能打印更多位但不创造额外精度。Neumaier使用sum+correction，源码见mass_ledger.h；不得将其与Kahan名称混用。FNV是变动筛查而非密码学身份；文件SHA和显式流体ID序列另行验证。

## binary64快照

全部little-endian，原生IEEE binary64；不满足平台要求时编译应拒绝。无struct padding，字段逐个write。

|文件|头部顺序/长度|payload|
|---|---|---|
|fluid_mask.bin|magic8=`FTMMASK1`；uint64 N；uint64 core_material_hash；int32 nx,ny,nz，总36字节|N个uint64唯一fluid ID|
|rho_step_<step>.bin|magic8=`FTMRHO1`+NUL；int32 step；uint64 N；uint64 hash，总28字节|N个double rho，与mask顺序相同|
|peak_rho.bin|同rho格式，step为短程最大legacy_e首次出现步|完整峰值rho；峰移无需存每个刷新峰值的全场文件|

ID=(x*192+y)*145+z，x/y/z都是core索引。对任意ID，z=ID%145，y=(ID//145)%192，x=ID//(145*192)。core原点z=−dx/2，因此z=0层为底壁；物理位置x=(x+0.5)dx、y=(y+0.5)dx、z=(z−0.5)dx。mask只保存material1。material_hash来自全部5345280个core节点按x-y-z顺序的ID与material，而非halo。

独立decoder为scripts/snapshot_format.py。必须结合runtime总N和manifest SHA验收，decoder通用的小样本单元测试不等于现场3686400点覆盖。全局平均delta通过也不能排除局部正负质量残差相消。

## diagnostic_status.txt

诊断覆盖、样本数/末步、legacy_result_PASS、legacy_mass_gate_PASS、旧质量峰值/峰步、max_e_delta、账本一致性、LDBL位数分别输出。恒定声明diagnostic_only=true与formal_reference_accepted=false。原CASE返回逻辑保持；预计4000步未收敛而return3，外部shell退出须另行记录。I/O/掩模错误会抛异常导致非正常退出，不能把它解释成旧mass FAIL。

本schema没有collision前后/periodic link净交换或分区守恒结论；需要时另建阶段诊断版本，不能由快照平均值补造。

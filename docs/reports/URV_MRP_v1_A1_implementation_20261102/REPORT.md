# URV-MRP-v1-A1：体积舍入恢复、构建与静态审计

2026-11-02。**已在新隔离候选中应用用户采用的体积附属修订，实际构建成功，107项软件测试通过。原分开乘加路径已在两个测量主干恢复；57600个体积空间累计值全部与原参考一致。本次采用范围内静态审计PASS，S0仍HOLD，尚无原生零步或正式流场结果。**

这项PASS只对应已采用的观察量改动、列明的浮点数据流和源码／构建来源核对，不表示所有传递内核已经完成形式化机器等价证明，不等于新URV数值、几何或结果验收通过。

## 1. 用户采用与实际修改

本轮原话：“用体积附属修订后，在新隔离候选中恢复该项舍入路径，重新构建并审计；出现新的指令或证据矛盾时，由 GPT-6 Astra｜High 裁定。正式运行仍另行授权。”

采用记录见adoption.json，绑定原URV-MRP-v1、上轮A1草案和具体补丁SHA。原草案的DRAFT状态是历史快照，没有回写；本轮采用另存。执行范围为隔离修改、构建、软件检查和静态审计，原生零步及正式运行未执行，也未从旧S0授权推导新授权。

新目录：

- `CASE/unseen_v2_reference_S0_mrp_v1_a1/`：native候选与真实构建记录。
- `CASE/unseen_v2_reference_checker_mrp_v1_a1/`：检查器隔离副本和A1精确来源绑定。
- 本报告目录：采用、源码差异、指令、算术、测试、保护和交接证据。

主程序相对上一失败候选只改一处：

```cpp
const volatile T roundedCellVolume = dx * dx * dx;
value.volume += roundedCellVolume;
```

差异与上轮proposed_volume_rounding.patch逐字一致，见[applied_volume_rounding.patch](applied_volume_rounding.patch)。未修改遍历、单位、节点、初始值、质量helper、补偿账本或密度捕获；三个header和Makefile保持上轮原字节。未改全局浮点选项、碰撞、力、边界、物性、收敛规则或任何门槛。

## 2. 实际构建与来源

新候选ELF SHA256：

```text
c1fc2a1eeacced8f11a9bb045c25d70936b7be03fe5495a0b8f51789bd8fe8af
```

编译、链接均实际成功，记录在native/evidence/build.log和build_environment.json；编译器、源码、依赖文件、三项静态库、运行库及OpenLB版本分别捕获，构建脚本没有调用流场二进制。编译器及静态／动态库哈希与上一候选相同。172条编译warning保存在完整日志中，warning类别及数量与上一候选相同，没有新类别；不把“构建退出0”说成无warning。

原失败ELF `6f83f1482473b6bd99f28b353c060282f031b2c394c2f4417196a8f40bd995ec`、其SOURCE_REVISION_AUDIT=FAIL、Astra裁定、103项测试和封存全部保持，不用新候选覆盖。

## 3. 两个测量主干的实际指令

反汇编由新ELF静态读取，完整文件new_disassembly.txt，测量函数new_measure.txt，质量helper片段legacy_mass_helper_disassembly.txt。详细地址与判断见instruction_audit.json。

| 路径 | 恢复后的体积运算 | 实际调用 |
|---|---|---|
| capture非空 | 421b3、421ea两次VMULSD；421ee/421f6单项double存取；421fe VADDSD | initial_reference、逐步diagnostic；P/T均可 |
| capture为空 | 4288e、428bd两次VMULSD；428c1/428c9单项double存取；428d1 VADDSD | 循环后的final；未来获准的initialize也走此主干 |

两条路径均实现RN(volume+RN(RN(dx×dx)×dx))，体积偏移+8的最终累加不再使用FMA。不是根据volatile字样放行，而是核对了编译后的乘法、舍入存取、加法及数据依赖。

质量helper仍在308c4、308d4、308e4作三个VMULSD并经double存取固定舍入，308f4最终FMA；header字节保持。P/T仅选择截面索引，两方向各自均能走capture非空与为空主干。主调用者已核对：24657初态、2493d逐步测量均传非空capture；2522d最终测量传空；266e5是尚未执行的initialize调用点。

## 4. 其余静态审计与边界

已逐项核对正常有限值测量路径：同次computeU／computeRho及原rho复制、速度模长平方与开方、压力换算、补偿质量单项乘法、Neumaier两个大小分支、rho−1账本、densityIntegral、三个速度体积分、两个截面流量、测量后的归一化、初态分母和误差减法后除法。停止逻辑和参数／几何／碰撞／体力源码保持，主源码逆向去除唯一A1补丁后完整等于上一候选。

另静态比对26个选定computeRho/U/J和碰撞相关函数的浮点寄存器数据流／调用序列：与原v1.2及上一失败候选均匹配，记录在selected_kernel_v12_comparison.json、selected_kernel_comparison.json。该比对进行了重定位／偏移归一化，不能当作完整地址等价或全部传递闭包证明。冷异常路径未作穷尽形式证明，真实运行仍须原始数值、几何、来源、旧20列和密度证据验收。

本次所查范围没有发现新的指令／证据矛盾，因此没有再次调用Astra；上轮Astra关于保留失败、仅采用后在新目录恢复体积原舍入的裁定已落实。没有修改用户模型配置。若后续运行或审计出现新矛盾，仍按用户指定交GPT-6 Astra｜High裁定，不自动改门槛。

## 5. 完整空间前缀与软件验证

无OpenLB的独立C++软件夹具使用与native完全相同的A1体积表达式，Python使用分开舍入参考逐项核对：

- **全部57600个空间前缀一致，差异数0**；不仅比较末值。
- 上一融合路径仍能检出196个空间前缀差异，首次ordinal15；末值仍相同。负对照证明这项检查能区分两种路径。
- 固定dx5e-9时，末态顺序体积为7.199999999998218e-21 m³；此数是软件算术量，不是本轮实际流场测得体积。

详细输出见volume_all_prefixes.json。它是已获准的软件算术验证，没有创建OpenLB格子或推进时间，不补成历史流场证据。

最终软件测试 **107项通过**，见software_tests.log：保留此前103项，新增A1全部前缀相等、旧融合差异可检出、夹具与native源码表达式一致、实际新构建完整来源绑定四项。旧“审计FAIL须拒绝”负例继续以人工失败视图执行，不改真实文件或降低断言；新源精确绑定正例与该拒绝负例分别成立。原77项检查器测试仍在其中，R1/R2及先保存差异后拒绝不变。

软件夹具通过ctypes执行C++观察量函数；夹具不含OpenLB。真实流场二进制describe/precheck/initialize/steady调用数为0。当前initialize调用的capture为空，未来这种零步输出只能检查初态统计／几何，不能代替steady路径的真实密度捕获检查。不能把107项通过改写为真实密度捕获端到端通过。

检查器analysis/和common/均与上一MRP候选原字节相同（原数值规则亦保持）；仅新revision/绑定此次真实源、diff、采用记录与本次限定审计。anchor中的instruction_audit_status=PASS只解除该静态来源阻断，不生成执行合同、approved_runs或启动授权。

## 6. 当前状态与下一步

| 证据层 | 当前状态 |
|---|---|
| 新隔离源码与采用补丁一致 | 已验证 |
| 实际构建 | PASS；原warning保留 |
| 软件检查 | 107/107通过 |
| 质量／体积指定舍入路径 | 已验证；体积全部空间前缀0差异 |
| SOURCE_REVISION_AUDIT | PASS，限定为本文列明的A1静态范围 |
| 原生零步／实际密度捕获／正式h75回归 | 未执行／未验证 |
| 新URV_NUMERICAL_GATE、geometry_PASS、URV_RESULT_PASS | NOT_EVALUATED |
| S0 | HOLD，等待原生接入与新回归证据 |
| 旧v1.2横槽失败、历史190点唯一归因 | 原失败保持；NOT_ESTABLISHED保持 |
| S1、公式比较、物理验证 | 未启动／NOT_EVALUATED |

本轮1835份受保护既有文件保持，包含上一候选与其检查器、原始结果、旧协议／封存和报告。无新正式run_id、runs目录、启动合同或启动命令，没有提交、推送或外发项目材料。

下一具体动作是在明确获准后，进行这份A1二进制两方向的原生零步接入审计，核对初始化／几何／统计输出及来源，并明确steady捕获路径的实际接入检查，再按实际证据准备新的S0运行身份与绑定。正式运行仍另行授权、由用户启动；不能把本次构建和静态PASS直接换成S0接受，不自动进入S1。

reference_qualified=false、strict_error_bound_established=false、submission_ready=false、MODEL_COMPARISON/physical_validation=NOT_EVALUATED。旧细T FAIL、C/h75限定资格、V2/G4锁、D4预测HOLD、GDI01、旧N8和外部历史声明范围保持。AI辅助使用scientific-writing组织报告，沿用[Scientific Agent Skills来源](https://doi.org/10.48550/arXiv.2609.00065)；本记录不是独立人工科学终审。

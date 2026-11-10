# URV-MRP-v1-A1：恢复体积观察量原舍入路径的附属修订草案

2026-11-02。**DRAFT_NOT_ADOPTED_NOT_APPLIED**。这是当前已审定范围之外的一项具体最小补丁提议；没有修改、重新编译或执行已失败候选。原 URV-MRP-v1、原 URV-v1 门槛、当前候选和所有历史失败保持。

## 问题和裁定

当前候选 ELF `6f83f1482473b6bd99f28b353c060282f031b2c394c2f4417196a8f40bd995ec` 中，质量 helper 按规定执行了三次逐项舍入和最后一次融合乘加，但体积观察量的最后乘加也意外被融合。原 v1.2 为分开乘加。capture 非空主干地址 0x421cd、为空主干 0x4288f；不是分别对应 P/T。P/T 各可进入两主干。

固定 dx=5e-9、57600 项的软件算术核对显示最终体积相同，196 个空间前缀不同，首次 ordinal=15，相差 1 ULP。此结果不是实际流场输出差异或时间步差异。按用户指定的 GPT-6 Astra｜High 只读裁定，`SOURCE_REVISION_AUDIT=FAIL`，候选 HOLD，不继续构建。

## 唯一拟增加的源码修改权限

如果用户采用此附属修订，允许在全新候选目录中，仅对 `measure` 的 `value.volume += dx*dx*dx` 增加局部 binary64 舍入屏障，恢复原 v1.2 的：

```text
a = RN(dx * dx)
b = RN(a * dx)
volume_next = RN(volume + b)
```

首选具体补丁见 [proposed_volume_rounding.patch](proposed_volume_rounding.patch)：把单项体积写入一个局部 `const volatile double` 再相加。不改变遍历、初始值、单位或节点集合；不以预先计算的常量代替当前 dx；不修改整个 measure 或全局浮点选项。

`volatile` 是候选实现手段，不是验收证据。新构建中必须看见两个按原顺序的 binary64 乘法、单项体积舍入存储／读取、独立加法，且不得出现 volume 最后乘加融合。若依然不满足，记录失败并停下，不能扩大白名单追逐编译器变化。

## 若采用后的实施与接受条件

1. 保留本次失败目录及 ELF；建立下一个隔离候选，不覆盖当前源、构建和 revision_anchor。
2. 仅应用本草案的体积舍入屏障；质量、补偿账本、密度捕获不扩改；给源码与最小 diff 新绑定。
3. 实际构建后，对 P/T、capture 非空／为空以及 initial/diagnostic/final 调用映射重新审计。补偿 term、Neumaier 两分支、densityIntegral、速度模长／压力、三个速度积分、两截面、归一化、初态分母、误差计算和停止逻辑逐项记录。不能从 volume 修好推定其余均通过。
4. 软件核对体积的全部 57600 个空间前缀都与原分开乘加一致；不只比较末值。保留现有构造 FMA 反例和异常证据拒绝测试。所有旧软件测试与新修订负例实际重跑。
5. 原 native 零步审计仍需明确授权；正式 h75 P/T 回归仍需新编号、真实启动合同并由用户启动。原 20 列精确轨迹、全部数值／几何／来源条件及密度重放要求不变。

本草案不授权上述任何执行。当前候选没有进入新运行，`URV_NUMERICAL_GATE`、`geometry_PASS`、`URV_RESULT_PASS` 均为 `NOT_EVALUATED`；S0 HOLD，历史唯一归因 NOT_ESTABLISHED。

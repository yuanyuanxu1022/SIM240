# 周期与三高度既有证据审查

只读取原始结果，不运行 OpenLB、不修改冻结协议、不改写历史 CSV。
默认生成 `CASE/reports/transport_evidence_audit_20261012/`；已有目录会拒绝覆盖。

从 SIM240 根目录执行：

```bash
python3 analysis/transport_evidence_audit/audit_existing.py --output-dir /absolute/new/audit-directory
```

审查包括完整 scaling 五点、周期生产十八点、Nx=1 冻结引用、G3-h 六点及 F2 六点交叉对照。
三高度数据库只和 G3-h 数值配对；不自动以目录标签或 PASS 标记推断证据完整。
F2 诊断 CSV 的三列错位仅在审查中显式按位置解释，旧 CSV 原样保留。窗口指标从末 1000 步通量重新计算。
哈希索引覆盖全部已登记原始 CSV/日志/VTK 及历史缺陷批次；是原位证据归档，不是异机备份。

测试：

```bash
cd analysis/transport_evidence_audit
python3 -m unittest test_audit_existing.py
```

`--refresh-own-report` 只用于本次固定输出路径的受控报告更新；默认不覆盖。
脚本使用标准库和已冻结检查函数，无安装依赖或修改求解器步骤。

# 第一篇 · 横向补充参考包 v2

为**已有 19 种几何**补横槽（T）方向对照的独立 FEM 包。不新增几何，不修改 v1 试点，不修改冻结的 FVM 发布，不授予参考资格。

- 科学目的、门槛、停止规则：`PROTOCOL.md`（运行前写定）
- 点集：`points.json`（登记 14 条，**实际运行 12 条**；h25 两点按作者 2026-11-13 裁定「整档薄隙不追加」排除）
- 接收依据的机器可读版本：`acceptance_rule.json`
- 求解器与复核器：`fem_pilot.py`、`verify_results.py`，与 v1 **逐字节相同**

## 使用顺序

```bash
PY=/home/dell/.workbuddy/binaries/python/envs/default/bin/python

$PY freeze_release.py --write --reason "initial freeze"   # 只在首次
$PY freeze_release.py --check                             # 任何时候可复核
$PY authorize.py --list                                   # 12 eligible / 2 excluded
$PY authorize.py --grant all --note "..."                 # 只授 12 条；excluded 点仍被拒
$PY run_queue.py --plan                                   # 只看计划，不计算
$PY run_queue.py --execute                                # 真正开始
$PY assess.py                                             # 汇总表
$PY assess.py --pairs                                     # 19 几何成对表
```

`h25_d25_T`、`h25_d50_T` 已按作者 2026-11-13 裁定排除，无需再 `--hold`：
`authorize.py --grant all` 只覆盖 12 条 eligible，即使手工把这两个 case 写进授权清单，
`check_authorization()` 仍会拒绝。

单点手动：

```bash
$PY run_one.py --case h50_d25_T --plan
$PY run_one.py --case h50_d25_T --execute
$PY verify_one.py --case h50_d25_T
```

## 拒绝运行的情形（设计如此）

- 包内任何文件或受控依赖版本与冻结清单不符（退出码 3，且不创建任何目录）
- 无 `authorization.json`，或该点不在授权清单，或授权记录的 release 与当前不符（退出码 5）
- `results/<case>` 已存在（退出码 6）：不允许把两次尝试混进同一目录
- 该 case 已有一次尝试记录（退出码 6）：每版发布每点只跑一次；确需重跑须 `--new-attempt "理由"` 并写入回执
- 复核回执已存在（退出码 6）：复核结论只写一次；确需重做须 `verify_one.py --replace`，新回执记录 `replaces_sha256`
- 点为 `EXCLUDED_BY_AUTHOR_DECISION`（h25 两点：作者已裁定整档薄隙不追加）

## 信任结构（重要）

回执本身**不是**信任锚。`runs/` 不在发布清单内，也没有签名，因此任何人都能写一份回执。

真正起作用的顺序是：`assess.py` 从 `results/<case>/` 的**原始场文件重新计算**每一项门槛，
没有场文件就永远到不了 `REFERENCE_CANDIDATE`（只会是 `NOT_RECONSTRUCTIBLE`）；
复核回执自报的 `reference_status` 只用于交叉核对，从不直接采用。

能做到的是"结论可重算、代写无效"，**不是"不可伪造"**：有写权限者若连同场文件一起整体伪造，
本包的机制挡不住。这一点在对外表述时必须写清。

## 边界

`REFERENCE_CANDIDATE` 是脚本能给的最高标签。正式参考资格需另经独立方法、精度与来源审查，不由脚本授予。`PILOT_NUMERICAL_CHECKS_PASS` 同样只是内部数值检查通过。

单点异常（场文件损坏、回执不可解析）记为该点的 `NOT_RECONSTRUCTIBLE` / `SOLVE_INCOMPLETE`
并在 `assess_problems` 写明原因，**不中断整表**，也不降级为通过。

自检（`tests/`）只在临时副本上运行，不写真实 `results/`、`runs/`，也不改 `release_manifest.json`。

`results/`、`runs/` 之外的文件应入库；`results/` 与 `runs/` 中的大场文件按既有仓库规则处理（场文件不入库，回执与 JSON 入库）。

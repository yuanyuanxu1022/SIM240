# v2.1 当前真实停点（2026-11-12 00:41核对）

## ★★ 结果（00:39）：h75_d100_P 正式 PASS，与 T 的 FAIL 构成方向对照；批处理 v21_night 已在跑

**批处理已由用户启动**（00:39:00，session `v21_night`，17 例串行）。真实进度只看 `docs/reports/PAPER1_fvm_v21_batch_20261112/execution/status.json` 与 `batch_console.log`。00:41 实况：第 4 例 `h50_d120_P_fine` 在跑，前 3 例 `h75_d100_P_tight` / `h50_d120_P_coarse` / `h50_d120_P_mid` 均 ACCEPTED。

`h75_d100_P_tight`（run_id `h75_d100_P_tight_20261112T003901_4c1da162`，墙钟 **2.21 s**，1 外迭代，末残差 `v=9.035e-13`，307200 单元）→ **`LOCAL_CHECKS_PASS`，`issues=[]`**，`K = 9.755622669731458e-23`。

**`assess()` 现报 `h75_d100_P`：`status=PASS`、`reference_accepted=true`、`delta=+0.804185%`、`alg=1.1369e-11%`、`Kref=9.755622669730348e-23`；LC `+146.9196%`、V2 `+6.7488%`、V2 改善。**

| 项 | h75_d100_T | h75_d100_P |
|---|---|---|
| 方程 | 压速耦合 Stokes | 标量 Poisson |
| `d21` / `d32` | 0.194279% / 0.082585% | 0.079154% / 0.027980% |
| `alg` | 0.00015756% | 1.1369e-11% |
| `delta` | **+2.511044%** | **+0.804185%** |
| 判定 | **FAIL** | **PASS** |

- **科学含义（仅此，不外推）**：同一几何、同一 FVM 框架、同一 h75/d100 下两方向一 FAIL 一 PASS ⇒ **该 >2% 偏差是方向相关的，不是 5 nm 离散的系统性偏差**。否定"5 nm 统一高估"作为解释。
- **P 的 `alg` 无信息量（必须如实说）**：`K_fine` 与 `K_tight` 仅 17 位末位不同（相对差 `1.1e-11%`），标量 Poisson 对本几何容差不敏感 ⇒ **P 的参考资格实质由 `d32 = 0.027980%` 承担，`alg` 判据对 P 几乎自动通过**。**不得**据此说 P 的参考比 T 更可靠（方程不同，判别力不可比）。
- 剩余离散误差：等比 `0.015285%`（delta `+0.819596%`）、保守 `0.027988%`（delta `+0.832407%`），判别力 **71.5 倍**。
- 报告：`docs/reports/PAPER1_fvm_v21_review_20261111/h75_d100_P_DIRECTION_PASS_20261112.md`
- **禁止**：不得因 P PASS 重判 T 的 FAIL，反之亦然；不得把两点外推为其余 4 个方向的结论；不改 36 条主统计与论文数字；三项目级资格仍 **false**，`selected_six_all_pass` 仍 **false**。

## 已按作者要求准备剩余17输入后台顺序命令（启动前的准备快照，已被上方实况取代）

用户希望回去睡觉，明确选择“把剩余固定输入准备成一条后台顺序命令，遇验收失败即停”；本轮授权为准备，由用户自己启动。当前无求解进程；已完成并独立接收9份，含P mid求解.6678秒、P fine3.973秒。P三层K为9.766083321436146e-23、9.758353097414943e-23、9.755622669730348e-23m³，d21=.0791537791%、d32=.0279804149%，各层LOCAL_CHECKS_PASS；P仍缺tight，不能先判该方向2%。

外部调度目录docs/reports/PAPER1_fvm_v21_batch_20261112/，不改CASE冻结源码/协议/参数/release。run_remaining.py、batch_config、start_remaining.sh、README、测试受batch_manifest绑定；原235身份0漂移，14项纯合成串行/停错测试通过，真实只读预检PREFLIGHT_PASS_NOT_STARTED。execution目录不存在，无本轮求解/网格工具/mapFields/编译/新run_id，未创建tmux。启动命令已准备在START_COMMAND.txt，session=v21_night；命令交付不等于用户已启动。

固定剩余顺序：h75/d100 P tight；h50/d120 P四层；h125/d120 P四层；h25/d100 T四层；h125/d120 T四层，共17，不增加几何/网格。逐例调用原run_one、结束后原assess独立验收；每次源和身份重核，新的局部/网格/代数/2%一致性/基准A或角差失败即停，不重试、不覆盖或自动恢复。已知h75/d100 T的合格参考下+2.511%一致性FAIL作为既有负结果保留，不能抹成PASS或因它阻止本次已明确授权的其他固定输入准备。

start_remaining.sh使用systemd-inhibit在批次存活期间临时阻止sleep/idle，/usr/bin/true短探测通过，不改持久电源配置；用户可锁屏/关闭终端，但须保持开机供电。每例原有时间/内存/文件预算不变，T可能数小时，不承诺一夜全17项完成。运行后真实停点在此目录execution/status.json，每例.runner.log/.assessment.json及batch_console.log；先读这些再报告进度，不依赖本准备快照。失败后后续未运行，需另行审查，不自动重开。

明早接续：核execution是否存在及status，保留已知T FAIL，按真实完成数逐例验收/汇报；若没有execution，不推断已启动。原历史FAIL、三项项目资格false、36条5nm统计及论文系数/数值不改，无提交推送。详见本目录README/preparation_assessment/verification。

## P mid 已完成并通过（2026-11-12 00:05 记录）

`h75_d100_P_mid` 于 **23:48:30** 结束（run_id `h75_d100_P_mid_20261111T234826_ef3cf27b`），exit 0。独立 `read_case()` → **`LOCAL_CHECKS_PASS`，`issues = []`**。

| 层 | 单元 | K (m³) | 功率收支 | 外迭代 | 墙钟 |
|---|---:|---:|---:|---:|---:|
| P coarse | 19200 | `9.766083321436146e-23` | 0.105666%（coarse 诊断，不套 0.1% 硬闸） | 2 | 0.168 s |
| P mid | 76800 | **`9.758353097414943e-23`** | **0.035477%** ≤0.1% ✓ | 2 | 0.62 s |

- `d21 = |K_mid/K_coarse − 1| = 0.079154%` ≤ 1% ✓
- `delta` **诊断**：coarse `+0.696212%`、mid `+0.775980%`。**仅诊断，不进协议**。
- **`assess()` 对 `h75_d100_P` 仍为 `NOT_ASSESSABLE`**（`d32`/`alg` 无法计算）。**P 必须跑完自己的 fine 与 tight**，不得用 T 的加密行为外推，也不得据 `+0.696%` 作"翻盘可能性小"之类的概率判断。算术校验（仅校验、非预测）：要让 delta 破 2%，`K_fine` 须 ≤ `9.641251e-23`，即比 mid 再低 1.200%；而 coarse→mid 只降 0.079%。
- **P 与 T 不可互推**：P 是标量 Poisson 单分量 `v`，T 是压速耦合 Stokes。同几何、同有限体积框架、**不同算法路径**，加密行为无先验理由相同。两档均 2 外迭代即收敛，**步数少不是正确性证据**。
- **★ 工期（已实测，勿沿用旧估）**：P coarse `0.168 s`、mid `0.62 s` ⇒ **P fine/tight 预计各几秒到几十秒**，不是 T 的 12,764 / 4,053 s 量级。
- 待跑：`h75_d100_P_fine`（已备好 `h75_d100_P_fine_START_COMMAND.txt`，**未启动**）、`h75_d100_P_tight`；另 4 点（`h25_d100_T`、`h50_d120_P`、`h125_d120_P`、`h125_d120_T`）全部未启动。
- 00:02 现查：无求解进程；`h75_d100_P_mid` 自 23:48:30 后无任何文件变动（00:00 那次重复执行被 `run_one.py:169` 的防覆盖拦住，未产生第二次运行）。


## P coarse通过并已准备P mid；T tight通过后正式对照FAIL（2026-11-11 23:41核对）

用户贴回P coarse验收与mid准备。本轮独立read_case核P coarse LOCAL_CHECKS_PASS、issues=[]：run_id=h75_d100_P_coarse_20261111T231527_172b0354，原生2外迭代，末v2.830541216e-14，exit0/End，求解.167783秒。K=9.766083321436146e-23m³；另从几何19200格/单格1.5625e-27m³积分Uy，舍入差2.22e-16相对。功率.1056662182%只作coarse诊断。P的+.69621193%是coarse诊断，正式NOT_ASSESSABLE。不能用T网格变化推出P的概率或宣称误差方向机制已证；同FVM框架但P标量/T压速耦合算法路径不同。

T tight本轮已核实实际完成：原生26340外迭代，完整LOCAL_CHECKS_PASS、功率.06606777%，K_tight=4.3400348250152633e-23m³，独立307200格积分一致；fine/tight导度变化.000157556833%≤.05%。因此冻结assess正式T reference_accepted=true、status=FAIL，delta=+2.51104405117%，KR仍按协议取fine。旧tight未跑/NOT_ASSESSABLE是历史记录，不覆盖当前。该T点LC相对独立参考+50.18655%、固定V2+4.92515%，仍改善，只报该点，不改36条5nm统计或称物理真值误差/全域验证。

当前release97ae55ff…235项指纹0漂移。已准备P mid单例：h75_d100_P_mid、76800格/.625nm，源P coarse绑定末态2→目标.5，endTime120000，求解墙钟4小时。tmux v21_p2检查时不存在、目标无runtime/证据/.5。命令与核对JSON见PAPER1_fvm_v21_review_20261111/h75_d100_P_mid_START_COMMAND.txt及mid_PREPARE_20261111.json；本轮未启动/重跑/映射/编译，命令交付不等于已启动，未制造P mid run_id。详情P_coarse_AND_T_status_RECHECK_20261111.{md,json}。下一步由作者启动P mid，完成后独立验收及中粗比较；不自动进fine。项目三false及其他历史FAIL、论文数字/系数/门槛不改。

## ★ 上一停点（23:12）：第 2 个点 `h75_d100_P_coarse` 已备好交付，等你启动（**未启动**）

**为什么在本机跑**（用户裁定「那在自己电脑跑吧」）：远端不可行有两条硬理由，不是偏好问题——
① 冻结包 `external_sha256` 绑了 23 个 `/opt/openfoam13/...` **绝对路径**哈希，三台机器的 OpenFOAM 构建各不相同（实测 `blockMesh` 本机 `567bd627…` / 103.63 `a17371f4…` / 102.55 `d46d2192…`），换机必触发 `postprocess.py:309` 的 `RELEASE_DRIFT`；
② 103.63 单核比本机慢 **2.11 倍**（2.25 GHz 限频 vs 本机 5.10 GHz，中性 OpenFOAM 基准 1.287 s→2.720 s/3 次）。

**本机跑不会卡**（依据真实 `runtime/resource.txt`，不是估算）：峰值常驻内存 coarse **66 MB** / mid 127 MB / fine 372 MB / tight 378 MB，且 `run_one.py:59` 硬设 `RLIMIT_AS=4 GiB`；CPU 只占满 **1 个核**（99% of one core），其余核闲置。唯一可感知变化是风扇声。**与 OpenLB 0.625 nm 要十几~二十几 GiB 差 40~60 倍**——那才是之前卡的真因，两件事不能混。

**起飞前复核（23:08 现算，非沿用旧结论）**：

| 项 | 结果 |
|---|---|
| `release_manifest.json` SHA | `97ae55ff…c13e5`（= 送审/审查所据值，未漂移） |
| 235 绑定身份（212 本地 + 23 外部） | 0 漂移（23:05 复核） |
| `h75_d0_P_flat` / `h75_d0_T_flat` | 均 `LOCAL_CHECKS_PASS`，`issues=[]` |
| 求解进程 / tmux 会话 | 均无 |
| `h75_d100_P_{coarse,mid,fine,tight}` | 四个全部 **未跑**（无 `runtime/`）⇒ 无覆盖/重跑风险 |

`prepared/h75_d100_P_coarse/case.json`：`dx 1.25 nm`、`19200` 单元、`direction=P`、`level=coarse`、`seed_from=null`（种子链最底层，正确）、`end_time_cap 60000`、`wall_clock 1800 s`、`exit_trigger p/U/v=1e-10`、`flat_zero_component_exception=false`。
注：`case.json` 的 `execution_authorized: false` 是 `prepare.py:244` 建件时写入的预备字段，运行链路**不读取**；放行只看 `release_manifest.json` 的 `numerical_execution_authorized=true` + `formal_review_status`。已 FAIL 的 `h75_d100_T_coarse` 同字段亦为 false 且正常执行，可作反证。

**为什么选这个点**：`h75_d100_P` 与刚 FAIL 的 `h75_d100_T` **同一几何、相反方向**。若它同样 >2%，则「超 2%」是这套 5 nm 离散的系统偏差而非方向特例；若它 ≤2%，则 T 的 2.5110% 属方向相关。这是把单点 FAIL 变成可解释结论的最省算力路径。**未跑其余三点**（`h25_d100_T`、`h50_d120_P`、`h125_d120_P`、`h125_d120_T`）。

工期参考（上一轮实测）：coarse 205 s、mid 1,144 s、fine 12,764 s、tight 4,053 s ⇒ 四层合计≈5 h；本层 coarse 预计 **5 分钟以内**。

**本轮边界**：只交付 coarse 单例命令；未启动、未 mapFields、未编译、未跑 mid/fine/tight、未改阈值或冻结代码、未重跑 T、未调 `freeze_release.py`。**命令已交付 ≠ 已启动**，无 P 点 run_id。三 false 与 T 的 FAIL、论文数字全部不变。

交接：`HANDOFF_h75_d100_P_START_20261111.md`

---

## ★ 上一停点（22:40）：tight 已通过，h75_d100_T 正式判 FAIL，delta=+2.5110%

`h75_d100_T_tight` 于 **22:34:17 自然收敛**（run_id `h75_d100_T_tight_20261111T212636_3f1bf954`），26,340.5 步、`native_convergence`、exit 0、`End`、无平板例外、墙钟 4,053 s（用上限 9.4%）。种子链 fine `65970.5` → `0.5`，`map_exit_code=0`。

**`read_case` = `LOCAL_CHECKS_PASS`，`issues = []`**。末残差 Ux `9.9991774526396363e-12`、Uz `7.4319982338434457e-12`、p `8.2949873262314988e-14`，三重全 < `1e-11`。功率收支 `0.066068%`、截面极差 `1.889e-12%`、面体 `3.286e-05%`，全 ≤0.1%。`K_tight = 4.3400348250152633e-23`。

**2b 层核心判据**：

```
|K_tight/K_fine − 1| = 0.00015756%   门槛 0.05%   → PASS（余量 317 倍）
```

⇒ fine 的迭代误差只占 `d32` 的 **0.19%**，其余 99.81% 是真离散误差。**参考资格成立，`reference_accepted = true`。**

**正式判定（`assess()` 原样输出，未改写）**：

```json
{"point":"h75_d100_T","status":"FAIL",
 "grid_mid_coarse_percent":0.194278708111717,
 "grid_fine_mid_percent":0.08258503193038225,
 "algebraic_change_percent":0.00015755683335783033,
 "reference_accepted":true,
 "delta_K_percent":2.5110440511747933,
 "Kref_m3":4.340041663047474e-23,
 "LC_error_percent":50.186548651859944,
 "V2_error_percent":4.925148722420958,
 "V2_improved":true}
```

四项前置判据（`d21 0.1943% ≤ 1%`、`d32 0.0826% ≤ 0.5%`、递减 `d32 ≤ d21`、`alg 0.00016% ≤ 0.05%`）全部通过，**`delta 2.5110% > 2%` ⇒ FAIL**。

**这是"参考可信前提下"判出的 FAIL**，不是"比不了"。三角不等式下界：`2.5110% − 0.0827% = 2.4283%`，即 OpenLB 偏离真值**至少 2.43%**，不依赖参考自身误差取哪个估计。delta 四取法（coarse `+2.2274%`、mid `+2.4264%`、fine `+2.5110%`、外推 `+2.5735%`）全部超限，结论不依赖取法。同参考下原式 `50.1865%`、V2 `4.9251%`。

**边界（严）**：本结论**只覆盖 `h75_d100_T` 一个点**。其余 5 点全 `NOT_EXECUTED`；`assess()` 顶层仍 `status=INCOMPLETE`、`execution_status=PARTIAL`、`comparison_evaluable=false`、`scientific_gate=NOT_A_GLOBAL_REFERENCE_QUALIFICATION`。**不得外推到其他几何/方向，不得据此改稿，不得因 FAIL 改判据或重跑。** 其余 5 个 tight 未启动。

验收报告：`docs/reports/PAPER1_fvm_v21_review_20261111/h75_d100_T_tight_ACCEPTANCE_20261111.md`

---

## T fine已独立验收及网格项通过，tight未跑，正式对照仍待判（2026-11-11 21:22后）

fine已自然收敛，run_id=h75_d100_T_fine_20261111T172454_09d491e9，65970外迭代、final_time65970.5、原生停止/exit0/End、无平板例外，求解12764.34秒。完整read_case LOCAL_CHECKS_PASS、issues=[]，235绑定身份0漂移及mid/coarse源链核实。另独立流式积分307200行CSV重算Kfine=4.340041663047474e-23m³。功率0.0659102663%、截面极差2.90523173e-11%、面体差0.0000328641%，均≤fine原0.1%。d21=0.1942787081%、d32=0.08258503193%，网格门槛及递减通过；d32不是剩余不确定度。

相对fine的delta诊断预演为+2.51104405117%，但冻结assess()此点仍NOT_ASSESSABLE、tight NOT_EXECUTED。若tight本身和≤0.05%求解稳定性通过，则按固定fine参考正式判该方向超2%；若tight不合格则参考未取得。不能提前说“整体正式FAIL”或“相对物理真值超2%”。coarse/mid/外推只诊断不替代资格条件。p≈1.237及角点奇异性仅候选讨论，文献L形域alpha≈.544不能直接推当前FVM导度1.09阶；不称已证明物理事实。

独立复核记录PAPER1_fvm_v21_review_20261111/h75_d100_T_fine_INDEPENDENT_RECHECK_20261111.{md,json}，保留其他会话原验收报告不冒用其过强表述。已核并准备tight单例：同网格307200/.3125nm、源fine65970.5、残差<1e-11/线性1e-13，≤0.05%K变化及最细各0.1%；求解上限12小时非工期保证。tmux v21_g4检查时不存在、目标无runtime/证据。命令和准备JSON已存h75_d100_T_tight_START_COMMAND.txt及tight_PREPARE_20261111.json，本轮未启动/映射/编译/重跑或改门槛；命令交付不等于已启动tight。原FAIL、三false及论文数字不变。

## 【预演·非裁决】h75/d100 T 的 delta 已越 2%（2026-11-11 20:50）

讲闭环时顺手预演，量级够大必须先报。**参考未定稿（fine 在跑、tight 未跑），以下不是最终判定。**

`delta = (K5/Kref − 1)×100`，`|delta| ≤ 2%` 为 PASS（PROTOCOL §4 末条）。`h75/d100 T` 的 `K5 = 4.4490220210459354e-23`。

| Kref 取值 | delta | 判定 |
|---|---:|---|
| K_coarse = `4.352084022936e-23` | **+2.2274%** | FAIL |
| K_mid = `4.343628850320e-23` | **+2.4264%** | FAIL（更大） |

**方向不利**：K 随加密在下降（+0.194279% 是往下的）。按 `d32 ≤ 0.5%` 推算 Kref 落在 4.32~4.34 区间，delta 约 **+2.4%~+3.0%**。⇒ 这条大概率最终 FAIL。这是闭环按设计工作，不是故障；含义是"OpenLB 5nm 与收敛参考差超 2%"，不能再说 2% 内一致。按 `eps_R=(1+δ)(1+ε5)−1` 传播改稿，不放宽阈值/不重拟合/不删点/不加网格。

**禁止的错误推理**：不要把 +2.4% 与论文"横槽最小高估 +8.11%"相乘或互换——8.11% 是 18 条横槽最小值（未必是这一点），且比较对象是**原式 LC**；这里量的是 **OpenLB 对收敛真值**。三个不同比较。

其余五点无 v2 数据。六点 K5 备查：`(75,100,P)` `9.834076e-23`、`(75,100,T)` `4.449022e-23`、`(25,100,T)` `2.220208e-24`、`(50,120,P)` `6.885906e-23`、`(125,120,P)` `2.801566e-22`、`(125,120,T)` `1.863709e-22`。

口径补注（2026-11-11，本轮仅文字/协议核对）：闭环要求预定容限内一致而非逐位同数；三档网格是两次加密；读回解析日志残差不等于由原场重新组装方程残差。epsilon_R=(1+delta)(1+epsilon5)−1实际为公式相对合格KR的偏差，不是OpenLB相对物理真值总误差。每方向自身参考合格即可单独比较；固定任务按协议可用PASS/FAIL/参考未取得结束。详见PAPER1_fvm_v21_review_20261111/CLOSURE_WORDING_REVIEW_20261111.md；本轮未修改冻结代码/规则/阈值或刷新fine进程，当前运行快照时间仍以原条目为准。


## 【纠错 + 现状】mid 通过；早前"mid REFERENCE_CHECK_FAIL"是我的调用口径错（2026-11-11 20:42 +08:00）

**撤回一条我此前给出的错误判定。** 我先前报 `h75_d100_T_mid = REFERENCE_CHECK_FAIL`、`issues=['seed validation: mapping invocation mismatch']`，**这是错的**。

- 根因：`postprocess.validate_seed()` 第 162 行 `expected=[tool, str(source), '-case', str(case), ...]`，其中 `str(case)` 直接取调用者传入对象。我先前用**相对路径** `Path('prepared/h75_d100_T_mid')` 调 `read_case()`，得到 `prepared/h75_d100_T_coarse`；而回执 `map_argv` 记录的是**绝对路径**（`run_one.py` 一律传绝对）。字符串不等 → 误报。**与 `-noFunctionObjects` 无关**，该参数本来就在 expected 里，`map_argv` 恰好 10 项且逐项相符。
- 实证：同一条命令内，`ROOT/'prepared'/name` 与 `Path('prepared')/name` 分别调用 → 绝对路径下 mid `LOCAL_CHECKS_PASS`、`issues=[]`；相对路径下才 `REFERENCE_CHECK_FAIL`。官方入口 `assess()` 第 318 行本来就是 `read_case(root/'prepared'/cid, ...)`，跑官方 `assess()` 亦得 mid `LOCAL_CHECKS_PASS`。
- ⇒ **证据链无恙，是临时校验脚本的口径错。** 今后用 `read_case` 复核必须传绝对路径。上述错误判定**从未写入**本文件或 `PAPER1_fvm_v21_review_20261111/` 下任何报告（已 grep 确认）。

**当前官方 `assess()` 输出**（release `97ae55ff…`、exe `73b1f633…`）：

| case | status |
|---|---|
| `h75_d0_P_flat` / `h75_d0_T_flat` | `LOCAL_CHECKS_PASS` |
| `h75_d100_T_coarse` | `LOCAL_CHECKS_PASS` |
| `h75_d100_T_mid` | `LOCAL_CHECKS_PASS` |
| `h75_d100_T_fine` | `RUN_INCOMPLETE` |
| 其余 20 个沟槽算例 | `NOT_EXECUTED` |

全局：`INCOMPLETE` / `PARTIAL` / `all_planned_records_finished=False` / `scientific_gate=NOT_A_GLOBAL_REFERENCE_QUALIFICATION`。

mid 关键数：`native_convergence` @22796，Ux `9.99823457e-11`、Uz `7.50895384e-11`、p `1.32383795e-12`，全 <1e-10，**未用平板例外**；墙钟 1144.35 s（上限 14400 s）。K `4.343628850320e-23`；**`|K_mid/K_coarse−1| = 0.194279%` ≤ 1%**。诊断量：功率收支 0.149708%（mid 不受 0.1% 闸门约束）、截面极差 3.50e-11%、面/体通量 0.000203%。

**fine 正在跑，不需要启动**：run_id `h75_d100_T_fine_20261111T172454_09d491e9`，17:25:03 由 mid 的 **22796.5** 末态 mapFields 到 `0.5`（exit 0，`-consistent -mapMethod interpolate -noFunctionObjects`），20:34 已 55503 次迭代、时间目录 `55400.5`、日志持续增长。末残差 Ux `2.54e-10` / Uz `1.94e-10` / p `1.19e-12`，末 1e4 迭代约降 2.4 倍 → 预计累计约 6.6e4 步、**21:10~21:20 结束**，远早于墙钟 43200 s。**唯一有实质风险的判据是 `power_balance_percent`**：coarse 0.3547% → mid 0.1497%，而 0.1% 闸门只对 fine/tight/flat 生效，fine 必须自己压到 ≤0.1%。本轮只读，未启动/重跑/停止任何算例，未改代码与门槛。

## T fine仍在运行，尚未生成完成证据（2026-11-11 20:22:31 +08:00快照）

用户问是否结束。本轮只读确认fine同一run_id=h75_d100_T_fine_20261111T172454_09d491e9、PID697870状态R，已运行10640秒（2小时57分20秒）。最终receipt、独立exit_code、结果CSV均未生成，仍RUN_INCOMPLETE。本轮未读新残差，旧残差值只代表对应历史时点，不套用为当前值。

记录PAPER1_fvm_v21_review_20261111/h75_d100_T_fine_AUDIT_20261111T2022.json。下一步待该单例结束后独立验收并比较细中变化；本轮无启动/重跑/停止/改参数或门槛、不持续轮询、不启动tight。尚未作最终参考资格或OpenLB/V2误差判断。

## T mid单例命令已核对并交付，尚未启动（2026-11-11 16:48:59 +08:00）

用户授权仅核对/准备h75_d100_T_mid命令。本轮235绑定身份0漂移，release97ae55ff…授权/审查位有效，P/T平板与源coarse完整独立读回仍LOCAL_CHECKS_PASS。源run_id=h75_d100_T_coarse_20261111T162843_a1e0527f，绑定末态时间11403，U/p/phi及5份mesh指纹完整。mid元数据等于冻结canonical plan、同物理条件，dx=.625nm、76800单元，seed_from=coarse、startTime=.5、endTime120000、求解墙钟14400s。目标runtime/referenceEvidence/.5均不存在，无覆盖或重跑。tmux v21_g2检查时不存在。

准备命令见PAPER1_fvm_v21_review_20261111/h75_d100_T_mid_START_COMMAND.txt，核对记录h75_d100_T_mid_PREPARE_20261111.json，状态PREPARED_NOT_STARTED。命令将只运行mid，先建网格/检查，再从指定coarse末态mapFields到.5并保留输入副本，再求解。此次未执行任何命令启动、mapFields/网格工具/求解/编译；4小时是求解安全上限，不是预计工期。命令已交付不等于用户已启动，无mid run_id。

完成后独立验收mid全部条件及source seed链，再核abs(Kmid/Kcoarse-1)≤1%的既有变化要求。只有mid接收后才讨论fine，不自动串行批跑；该层完成也不是最终独立参考资格。无代码/物理参数/冻结协议/门槛/历史FAIL/论文数字变动，三false保持。

## 首个T粗沟槽独立验收通过，尚非最终参考（2026-11-11 16:45后）

case=h75_d100_T_coarse，run_id=h75_d100_T_coarse_20261111T162843_a1e0527f。作者运行已完成；独立退出0，原生收敛11403外迭代，求解205.20秒，未用平板例外。末Ux=9.99659614609e-11、Uz=7.67221990076e-11、p=1.52235544895e-12均<1e-10。

本轮冻结read_case核完整原始结果与来源，LOCAL_CHECKS_PASS、issues=[]；235绑定指纹0漂移，release97ae55ff…不变。另独立积分19200行CSV复算K=4.3520840229361454e-23m³，与读取器一致。截面极差5.35192156029e-11%、面/体通量差0.00127532825%、功率/耗散差0.354742628872%。按事前协议coarse功率仅诊断，不套用fine的0.1%门槛；后续fine/tight仍须达该门槛。

证据PAPER1_fvm_v21_review_20261111/h75_d100_T_coarse_ACCEPTANCE_20261111.{md,json}。早先16:29 RUN_INCOMPLETE是历史快照。当前只coarse层通过，不是独立参考已资格化，也不能按此评价2%或V2；还需mid/fine/tight。下一动作仅按冻结seed链准备mid单例；本轮未启动下一层/重跑/改代码门槛，三false及旧FAIL和论文数字不变。

## 首个T粗沟槽已由作者启动，验收时仍运行（2026-11-11 16:29:14 +08:00）

用户请求完成后独立验收，但本轮现场发现运行未结束。case=h75_d100_T_coarse，run_id=h75_d100_T_coarse_20261111T162843_a1e0527f，PID675290状态R、已运行30.9秒；tmux v21_g1当前命令python3。该状态仅为时点快照，不长期假定仍存活。启动记录/运行快照绑定当前release 97ae55ff…，235项输入/外部指纹0漂移。

runtime/receipt.json、runtime/exit_code.txt、referenceEvidence均尚不存在，不能报告完成、PASS、K或与OpenLB差值。日志仅一次尾部诊断，末Ux约3.493e-4、Uz约2.392e-4、p约2.854e-6，尚未到冻结1e-10门槛；这些在途数不作最终判定。保存h75_d100_T_coarse_AUDIT_20261111.json，状态RUN_INCOMPLETE。下一步等此单例结束后读取完整日志/退出码/CSV/原场/回执，按冻结规则独立验收；本轮不等待、不持续轮询、不重跑/停止/改参数或进入mid。三项资格false及旧FAIL不变。

## 状态：两方向平板均已通过，沟槽闸门已打开，尚未启动沟槽

| 平板 | run_id | 停止 | 判定 |
|---|---|---|---|
| P | `h75_d0_P_flat_20261111T145810_b5a3ecc4` | `native_convergence`，2 迭代 | `LOCAL_CHECKS_PASS`，issues 0 |
| T | `h75_d0_T_flat_20261111T154355_ab7f0638` | `iteration_cap`，60000 迭代 | `LOCAL_CHECKS_PASS`，issues 0 |

两次运行的 `release_snapshot.json` 哈希均为 `97ae55ff…`，与当前清单一致。详细验收见 `docs/reports/PAPER1_fvm_v21_review_20261111/FLAT_VERDICT_20261111.md`。

## 一、关键数字

| 平板 | K (m³) | 解析 h³/12 | K 偏差 | 剖面 L2 | 功率收支 |
|---|---|---|---|---|---|
| P | `3.5161132813e-23` | `3.515625e-23` | **+0.013889%** | 0.009509% | 0.020830% |
| T | `3.5161132788e-23` | `3.515625e-23` | **+0.013889%** | 0.009509% | 0.020831% |

两项全部 ≤ 0.1% 门槛。P 与 T 走了两条不同代码分支、两套线性求解器，得到同一个 K（差 < 1e-7 相对），支持这个平板基准的分支一致性，不证明真实沟槽精度。

## 二、T 平板的例外与地板（必须记住）

T 跑满 60000 步，**非原生收敛**，按 T 平板例外事后接收：

- 末轮 Ux `3.43e-13`、p `1.60e-13`，均达标；**Uz `2.93e-09` 不达标**。
- 例外条件独立复核：`max|Uz|/max|Ux| = 2.0155e-14`（门槛 1e-9，差 5 个量级）；`max|Ux| = 7.03e-05` 严格正；`max|Uz| = 1.42e-18`（Uz 场实为零场）。
- **地板实证**：全程 59959 个非零 Uz 样本，中位数 `1.93e-09`，最小 `2.10e-10`，**低于 1e-10 的为 0 个**，且从 6000 步到 54000 步无衰减趋势；同期 Ux 单调衰减 12 个量级（0.99 → 7e-13）。⇒ **支持该平板在本段迭代内出现归一化残差地板；不能据此证明再十倍迭代必不达标，也不能推广到沟槽。**
- 前 41 次 Uz 残差**恰为 0**（真实零值）——v2 零残差规则（B5）在真实数据上的首次实例，未触发异常。

## 三、沟槽闸门

`run_one.py:172-177` 实测：

```text
h75_d0_P_flat -> LOCAL_CHECKS_PASS | gate OK: True
h75_d0_T_flat -> LOCAL_CHECKS_PASS | gate OK: True
GROOVE GATE: OPEN
```

26 例中仅两项平板有 `runtime/`；**24 个沟槽算例全部未运行**。

## 四、下一步：固定六方向沟槽

按 `seed_from` 顺序 **coarse → mid → fine → tight**，每方向（P/T）独立推进。首个建议命令（T 方向 h75/d100 主几何）：

```bash
tmux new -s g1 'source /opt/openfoam13/etc/bashrc && cd /home/dell/yuanyuanxu/SIM240/CASE/paper1_fvm_stokes_reference_v2 && python3 run_one.py --case h75_d100_T_coarse --execute 2>&1 | tee /tmp/g1.out; echo "=== 结束 ==="; bash'
```

注意：coarse 的 `seed_from=null`，从零初场开始，不执行 `mapFields`；只有 mid/fine/tight 才从绑定前层末态映射，并保存映射日志与输入副本。源层未接受时下一层拒绝启动。

## 五、边界与禁令

- 平板通过 **≠** 六方向参考通过。沟槽必须各自独立达标。
- 原 v1 T 平板 `−8.943434%` `REFERENCE_CHECK_FAIL`、S4/D4 历史 FAIL、`reference_qualified`/`strict_error_bound_established`/`submission_ready` 三 false **全部不变**。
- 论文数字、36 条主统计、系数、比较门槛未改。
- 运行后 `verify_release()` 仍通过（235 项绑定身份完整）。
- **不得重跑 `freeze_release.py`**：会把执行锁退回 `PENDING_ASTRA_V21_RECHECK`、抹掉 `reviewed_release_sha256`、产生第三个 SHA；且已有 `runtime/`，其自身守卫也会拒绝。
- 不得重跑已完成的算例（`run_one.py:170` 会拒绝，这是设计意图）。

## 六、身份速查

| 项 | 值 |
|---|---|
| 受审 release（Astra 复核对象） | `f1531d4091a6279a5db2df5cff75875d279d4ffc981f52ae5502bedd98ffc292` |
| 当前 release（已用于两次平板运行） | `97ae55ff9dbaad4c2aa58fbe3b3b5dac548f82400631ac5cd1e12c9ef96c13e5` |
| 绑定指纹 | 212 本地 + 23 外部，逐项相同，运行后 0 漂移 |

两 SHA 关系与逐字节证明见 `docs/reports/PAPER1_fvm_v21_review_20261111/AUTHORIZATION_DIFF_PROOF.md`。

本会话已独立复核P/T全部冻结接收条件；对应FLATS_independent_readback_and_next_20261111.json。下一步仅交付h75_d100_T_coarse的tmux后台命令，未启动。

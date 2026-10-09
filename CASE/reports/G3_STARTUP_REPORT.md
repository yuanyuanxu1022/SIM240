# G3-h 高度扫描启动报告

## 1. 启动范围

本阶段仅完成 G3-h 框架检查、编译、geometry/q 预检和零步小规模验证，不启动正式稳态高度矩阵，也不启动 G3 其他方向/角度计算。

用户指定目录 `CASE/G3_EX240_height_sweep` 在当前仓库对应：
`CASE/04_parameter_study/G3_EX240_height_sweep`。

第一阶段候选高度：`h=125 nm、75 nm、50 nm`；每个高度均检查 Parallel (P) 与 Perpendicular (T)。

## 2. G2 参数继承核对

已核对 G3-h 协议与生成器：

| 项目 | 当前值 |
|---|---|
| 功能网格 | `dx=2.5 nm` |
| 碰撞模型 | ForcedBGK |
| 格子 | D3Q19 FORCE |
| `tau` | `1.0` |
| 壁面 | link-wise Bouzidi，解析 `q=0.5` |
| 面内边界 | x/y periodic |
| 驱动 | 周期体力，`a=1e5 m/s²` |
| 几何变化 | 仅 mesa gap `h`，EX240 周期/宽度/深度不变 |

生成器使用已确认的 G2 源 SHA-256：
`4acd63db67e273f87fed487fa7d1866f18dc82c018aaba1151f44882bd021002`。

## 3. Case 与高度表示检查

`preflight_height.py` 检查通过：候选矩阵仍为 `25/50/75/100/125 nm`，且在 `dx=2.5 nm` 下分别为整数层数。第一阶段使用的层数为：

| h (nm) | 网格层数 |
|---:|---:|
| 125 | 50 |
| 75 | 30 |
| 50 | 20 |

本阶段未运行 `h=25` 或 `h=100` 的预检以外的正式扫描；未覆盖已有结果目录。

## 4. 编译结果

已为 `h=125/75/50 nm` 生成并编译独立可执行文件：

```text
build/g3_ex240_h125
build/g3_ex240_h75
build/g3_ex240_h50
```

生成源均由 G2 源机械替换高度、期望流体节点数和 case/output 标签得到；编译成功。编译过程中出现 OpenMPI `opal_ifinit` 诊断信息，但未阻止生成目标文件，随后预检在允许本地 MPI socket 的受控环境中成功完成。

为修复当前框架对仓库重排后旧 G2 路径的引用，仅修改了 G3-h 自身的 `generate_height_source.py` 和 `src/Makefile` 路径依赖；未修改 G2 源、参数或验证协议。

## 5. geometry/q 零步预检

预检命令使用 `run_precheck.sh`，模式为 `zero_step_precheck`，每个点 `collide_and_stream_calls=0`，因此不是输运结果或稳态 PASS。

| h (nm) | 方向 | geometry_PASS | q_audit_PASS | fluid_nodes | candidate=installed links | q_min=q_max | fallback | exit |
|---:|---|---|---|---:|---:|---:|---:|---:|
| 125 | P | true | true | 645120 | 130176 | 0.5 | 0 | 0 |
| 125 | T | true | true | 645120 | 130176 | 0.5 | 0 | 0 |
| 75 | P | true | true | 460800 | 130176 | 0.5 | 0 | 0 |
| 75 | T | true | true | 460800 | 130176 | 0.5 | 0 | 0 |
| 50 | P | true | true | 368640 | 130176 | 0.5 | 0 | 0 |
| 50 | T | true | true | 368640 | 130176 | 0.5 | 0 | 0 |

六个预检目录均为新的时间戳目录，例如：
`CASE/04_parameter_study/G3_EX240_height_sweep/results/precheck_h125_P_20260918T072933+0800/`。

## 6. 启动判定与边界

- Case 检查：PASS；
- G2 参数继承：PASS；
- 三个高度的 P/T geometry 与 q audit：PASS；
- 小规模验证：仅完成零步预检，`collideAndStream` 未调用；
- 正式高度扫描：未启动；
- G3 角度验证：未启动。

因此当前状态是：**G3-h 框架启动前检查完成，具备进入正式计算前的预检基础，但尚未产生任何高度输运结果。**

后续若启动正式扫描，必须为每个高度/方向建立不可覆盖的 run ID，并继续独立报告 `NUMERICAL_GATE`、`geometry_PASS` 和 `RESULT_PASS`；本报告不授权自动启动长时间计算。

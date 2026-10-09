# G3-h 正式计算前检查报告

审计日期：2026-09-17  
审计范围：G3-h 代码框架、候选高度几何、与 G2 冻结协议的参数一致性。  
执行边界：未启动任何 G3 `steady` 计算；未把零步预检表述为输运结果。

## 1. 审计结论

**G3-h 框架的 h=25/50/75/100/125 nm 静态几何定义正确，且与
G2 单胞和 dx=2.5 nm 数值协议一致；但 G3-h 不具备正式计算授权。**

原因不是几何错误，而是生产网格尚未由 G2 Step3 的 GCI 证据选定。
当前 G3-h 生成器从 G2 dx=2.5 nm 冻结源派生，只替换高度相关量；若
G2 推荐 dx=1.25 nm 或判定 GCI 不充分，必须在独立协议下生成/审计相应
网格族，不能把当前 dx=2.5 nm 框架直接当作生产设置。

## 2. G2 一致性审计

| 项目 | G2 冻结值 | G3-h 状态 | 判定 |
|---|---:|---|---|
| 源码母版 | SHA-256 `4acd63db...bd021002` | 生成器启动时强制校验同一 SHA-256 | PASS |
| 格子/碰撞 | D3Q19 `<FORCE>` / ForcedBGK / double | 直接继承母版 | PASS |
| 功能网格 | dx=2.5 nm | 直接继承，`nx=ny=96` | PASS，仅限此网格 |
| 时间步/松弛 | tau=1.0, dt=1.0416666666666667e-12 s | 直接继承 | PASS |
| 物性与驱动 | rho=1000, nu=1e-6, mu=1e-3, a=1e5 SI | 直接继承 | PASS |
| 几何 | P=240 nm；mesa/groove/mesa=60/120/60 nm；D=100 nm | 仅替换 mesa gap h | PASS |
| 边界与统计 | x/y 周期、精确 Bouzidi q=0.5、G2 的质量/Mach/收敛/截面门槛 | 协议逐项继承 | PASS |
| 输出定义 | `J_i=int(u_i dV)/A_plan`、`Keff=mu*J/(rho*a)` | 直接继承 | PASS |

`H_ref(h)=h+50 nm` 仅作为报告几何量；平滑参照使用同一 mesa gap 的
`K0(h)=h^3/12`，未以 `H_ref` 替换 h。该区分正确。

## 3. 高度几何审计

固定网格下，流体节点理论数为

```text
N_fluid = (P/dx)^2 * (h/dx)
          + (W_g/dx) * (P/dx) * (D/dx)
```

其中 `P/dx=96`、`W_g/dx=48`、`D/dx=40`。第二项为固定沟槽额外体积，
第一项为整个平面下方的 h 高液膜。生成器把该数写入每个派生源码的
`expectedFluidNodes`，并把同一 `mesaGap` 变量同时用于 material 分类、
解析壁面、计算域高度、名义体积、`H_ref` 和 `K0`。

| h (nm) | h/dx | H_ref=h+50 (nm) | N_fluid | K0=h^3/12 (m3) | 静态对应 |
|---:|---:|---:|---:|---:|---|
| 25 | 10 | 75 | 276480 | 1.3020833333333333e-24 | PASS |
| 50 | 20 | 100 | 368640 | 1.0416666666666666e-23 | PASS |
| 75 | 30 | 125 | 460800 | 3.5156250000000000e-23 | PASS |
| 100 | 40 | 150 | 552960 | 8.3333333333333333e-23 | PASS |
| 125 | 50 | 175 | 645120 | 1.6276041666666667e-22 | PASS |

全部 h 均为 2.5 nm 的整数倍，因此在当前 G3-h 功能网格上没有高度
舍入、半格偏移或名义体积不一致。它们同样是 5.0 和 1.25 nm 的整数倍；
但这不等价于已为这两个网格实现并审计 G3-h 源码。

## 4. 实际预检证据的边界

已执行的唯一 OpenLB 预检是 `h=75 nm, P`，且为零步：

```text
formal_simulation=false
collide_and_stream_calls=0
geometry_PASS=true
converter_PASS=true
q_audit_PASS=true
fluid_nodes=460800
candidate_links=installed_links=130176
q_min=q_max=0.5
fallback_count=0
exit_code=0
```

因此 h=75 nm 有实际 `geometry_PASS` 证据。其余 h 的结论是源码/解析
几何一致性 PASS，尚无各自的 OpenLB 零步 `geometry_PASS`；不得把它们写成
已运行或已验证的输运 Case。

## 5. G2 Step3 依赖状态与生产网格决定

现有 Step3 归档中，dx=5.0 和 2.5 nm 的 Smooth75、EX240 parallel、
EX240 perpendicular 都有 `result.txt` 和独立退出码；dx=1.25 nm 的
Smooth75 已有完整结果，但两个 EX240 方向只有 precheck 和 diagnostics，
没有 `steady/result.txt` 或 `steady/exit_code.txt`。

故目前没有完整的三网格 `K_parallel`/`K_perpendicular` 序列，无法按
冻结 Step3 协议计算有效 Richardson 阶、GCI 和渐近区间指标，也无法依据
“最粗且满足 GCI/相对稳定性”的规则选择生产网格。

**生产网格决定：HOLD。** 当前不能默认 dx=2.5 nm，也不能因已有两层网格
结果而推断 dx=1.25 nm 的趋势。

## 6. 正式启动前必须满足的条件

1. G2 Step3 补齐 dx=1.25 nm 的 EX240 parallel/perpendicular 完整结果、
   独立退出码与后处理；按冻结协议给出 PASS/FAIL/GCI，而非预设结论。
2. 据此冻结 G3-h 的生产 dx；若不是 2.5 nm，先建立相应网格派生链、
   物理相似量和零步边界审计，不复用当前 dx=2.5 nm 可执行文件。
3. 对五个 h 在选定网格上分别运行零步预检；对每个高度保存 material、
   candidate/installed links、q、fallback 和独立退出码。
4. 在 G1/G2 的正式数值证据允许后，才分别启动 P/T 稳态矩阵；每点独立
   报告 `NUMERICAL_GATE`、`geometry_PASS`、`RESULT_PASS`。

在以上条件满足前，本报告不提供 G3 正式运行命令。

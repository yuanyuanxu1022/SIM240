# SIM-EC1XT240 纳米压印数值研究 — 项目进度总结

> 整理日期：2026-09-07
> 范围：汇总 `grooveDNS/` 下阶段一/二/三的源码、运行结果与各报告，以及版图解析与宏观 OpenFOAM 基准的交叉结论。
> 说明：本文件是只读整理，未运行任何仿真、未修改任何源码或旧结果。
> 名称勘误（2026-09-08）：正式物理/模型名称统一为 **SIM-EC1XT240**；详见 `SIM_EC1XT240_NAMING_CORRECTION.md`。
>
> Historical internal directory names such as `stage3_ex240_local` are retained for reproducibility. The correct physical/model designation is `SIM-EC1XT240`.

---

## 1. 项目目标

用 **OpenLB** 为 SIM-EC1XT240 版图建立**多尺度**数值路线：

1. 由纳米周期单元计算输运/等效化参数（阶段一、二 + 新 homogenization）；
2. 用静态 FreeSurface 验证液滴/界面数值能力（阶段三早期自由球测试）；
3. 最终开发宏观压印模型（尚未完成）。

上游宏观基准是 `ZJ/nanrPrint` 的 OpenFOAM 案例：EC1XT240 为 1 mm×1 mm 宏观窗口，9 个半径 52 µm 的准二维液柱（3×3），压头下压 −935 nm、历时 1 s，最终间隙 65 nm；该宏观模型用 `d=(5e16,0,0) m⁻²` 的各向异性 Darcy 阻力，**不解析纳米沟槽**。

---

## 2. 总体进度快照

| 模块 | 状态 | 一句话结论 |
|---|---|---|
| 版图解析 (`ex240_layout_report.md`) | ✅ 完成 | OAS 为 120 nm 墙/120 nm 槽、240 nm 周期，50 µm 宏块接缝 +80 nm |
| 阶段一 B_yy 纵向输运 | ✅ 完成 | 直沟槽 DNS，最细网格 **B_yy = 97.6164 nm²**（非严格网格无关真值） |
| 阶段一质量/通量审计 | ⚠️ 部分完成 | dx=5 复现；dx=2.5 未收敛中间态；dx=1.25 未运行，无正式 GCI |
| 阶段二 B_xx 横向阻断 | ✅ 完成 | 连续实体墙下 **B_xx ≈ 0**（数值残差量级，独立 20000 步验证） |
| 阶段三静态几何接入 | ✅ 完成 | 单胞几何接入真实 OpenLB，10 步零场推进通过 |
| 阶段三固定间隙等效化 (h=65 nm) | ✅ 完成 | 双周期 X/Y 驱动，K 张量与 B(Href=115 nm) 已算 |
| 阶段三开放边界（压力面） | ✅ 完成（固定基线） | 修复周期 outside 语义后，h=75 nm 固定基线 100 步通过 |
| 阶段三移动压头（真实动态边界） | ⚠️ 转换前稳定 / 转换 FAIL | Zou/He 压力边界修复后转换前移动稳定（STEP4/5.3 PASS）；首次 fluid→solid 转换的 population 重分配未解决（STEP5 三候选 FAIL） |
| FreeSurface / 液滴 / 困气 / 1 mm 全版压印 | ⛔ 未开始 | 仅早期静态自由球 Gate A/B 通过，非真实压印 |
| 宏观 Darcy 标定 vs 微观 B | ⏳ 未闭环 | 微观 B/K 与宏观 `d=5e16 m⁻²` 尚未建立换算与尺度匹配 |

**一句话现状**：稳态输运与静态几何/边界已打通；移动压头经 **Zou/He 压力边界替换 LocalPressure** 后，**转换前的连续移动已稳定**（STEP 4、STEP 5.3 通过）；当前唯一卡住的是**首次 fluid→solid 材料转换的 population 重分配**（根因已定位，三个候选方案均未通过）。

---

## 3. 各阶段详细状态

### 3.1 版图解析（已完成）

`SIM-EC1XT240.OAS`：顶层 cell `TOP`、layer `1/0`，4160 个 120 nm×240 nm 矩形。
- 内部规则区：**120 nm 墙 / 120 nm 槽 / 240 nm 周期**，最小重复单元 240 nm×240 nm。
- 每 50 µm 宏块接缝处多 80 nm 间隙 → 全局 ~1 mm 版图**不是严格全局 240 nm 周期**。
- OAS 只有二维图形，**不含 z 向沟槽深度与工艺极性（凸台/凹槽）**。

### 3.2 阶段一：B_yy 纵向输运（已完成）

理想直沟槽（wall 120 nm | groove 120 nm | wall | groove | wall，Lx=600 nm，液膜高 65 nm，y 周期）的 D3Q19 Forced-BGK 单相 DNS，体力驱动 +y。

- 体力线性验证：a_y = 1e6/1e7/1e8 下 B_yy 变化 0.000%（低 Re 线性）。
- 严格等几何网格收敛（液高精确 65 nm）：

| dx | B_yy (nm²) | 相对最细网格误差 |
|---|---:|---:|
| 5.00 nm | 112.4366 | 15.18% |
| 2.50 nm | 102.3725 | 4.87% |
| 1.25 nm | **97.6164** | 0% |

- 正式最终值 **B_yy = 97.6164 nm²**（= 9.76164e-17 m²），质量相对误差 3.33e-15。
- **质量/通量审计**（`stage1_mass_flux_audit/`）：dx=5 已复现 B_yy；dx=2.5 只到未收敛中间态（外部超时）；dx=1.25 未跑。因此**尚无正式三网格 Richardson/GCI**，97.6164 nm² 只能算最细网格离散值。

### 3.3 阶段二：B_xx 横向阻断（已完成）

连续实体墙把各槽隔成封闭空腔，+x 体力下稳态为静水力学平衡，u≈0。
独立审计 `stage2_blocking_audit/` 跑满 20000 步：`qx ≈ 6.09e-15 m/s`，`Bxx_num ≈ 6.09e-27 m²`（≈6.1e-9 nm²，比 B_yy 小约 10 个量级）。
**结论：理想连续墙直槽中 B_xx 在数值容差内为零**。但该结论**不能**推广到 h>0 的带槽压头几何（凸台下液体沿 x 横向连通）。

### 3.4 阶段三：显式压印（进行中，核心环节受阻）

#### 3.4.0 压头几何（极性已确认：OAS 矩形 = 凹槽）

压头是**带凹槽的周期条纹模具**：沿 y 方向连续，x 方向「凸台/凹槽」交替，周期 240 nm。

- **凸台（mesa）**宽 120 nm：向下凸出，底面距基底 h = 下压后液膜厚度（暂定 65 nm）；
- **凹槽（recess）**宽 120 nm：向上凹进 **100 nm（实际确认）**，槽顶距基底 h+100 nm（165 nm）。

```text
z(nm) ↑
165 ┌──────────────┐          ← 凹槽顶面(roof) z = h+100 nm
    │ 凹槽 ░░░░░░░░│             ░ = 液体(深槽区)
 65 ┼──────────────┤          ← 凸台底面 z = h (液膜)
    │ 凸台 ▓▓▓▓▓▓▓▓│             ▓ = 压头实体
  0 ═══════════════╧══        ← 基底 z = 0 (固定)
    ←──凹槽120──→←凸台120──→    周期 = 240 nm
```

极性确认后，OAS 120 nm 矩形 = 凹槽、空白 = 凸台（与早期代码假设相反，但墙/槽各 120 nm 的对称结构不变，数值结果不受影响）。凸台下方 h>0 的薄液膜使液体可沿 x 跨凸台横向连通——这是不能套用阶段二 B_xx=0 的原因。

#### 3.4.1 设计与静态接入（已完成）

- `stage3_design_review/` 固定了研究对象：内部 240 nm 单胞（左/右各 60 nm 半凸台 + 中央 120 nm 槽），基底 z=0，凸台底面 z=h，槽顶 z=h+100 nm（深度 100 nm 已确认为实际值）。
- `stage3_ex240_local/static_lattice_integration.cpp` 接入真实 `SuperGeometry/SuperLattice`，D3Q19、x/y 周期、z 固壁；52,992 流体节点，10 步零场推进质量漂移为 0，材料计数不变。

#### 3.4.2 固定间隙等效化 h=65 nm（已完成）

`ex240_homogenization/`：240×240 nm 双周期带槽压头几何，dx=5 nm，X/Y 分别体力驱动（a=1e5 m/s²，tau=1.7），深度积分响应 J 与张量 K：

```
K = [[ 3.22316e-23, ~0 ],      (m³，行=响应 i，列=驱动 j)
     [ ~0,          8.20420e-23 ]]
```

- 主 B（以 H_ref = V_nominal/A_plan = **115 nm** 换写）：**B_xx ≈ 280.27 nm²，B_yy ≈ 713.41 nm²**。
- 这是**单个功能网格、单个固定间隙**的采样点，非网格无关值；H_ref=115 nm 是名义平面平均流体厚度，B 不能未经尺度匹配直接当宏观阻力倒数（K 才是本轮主结果）。

#### 3.4.3 开放边界（固定基线已通过）

带槽压头下压会缩小封闭体积，必须有出口或自由表面。先做了 y 两端 LocalPressure 开放储液边界：
- 首次失败根因：默认 `material=0` outside indicator 把 **x 周期 padding 误判为域外**，2400 个压力节点中有 60 个（位于 x 周期缝）得到零法向 → `Could not set Boundary.`
- 修复：专用 `PeriodicXOutside` 语义（x 永不 outside，y/z 按核心域判断）。
- 结果：h=75 nm 固定基线 100 步通过（非有限值 0、最大速度 0、密度 [1,1]、质量收支残差 0）。

#### 3.4.4 移动压头真实动态边界（⚠️ 转换前稳定，转换仍 FAIL）

移动压头已拆成精细 STEP 序列。**关键突破**：把开放压力面从 LocalPressure 换成 **Zou/He 压力边界**，解决了"移动就失稳"的问题——原 LocalPressure 的全 population 正则化重建与移动 Bouzidi 的斜向非平衡信息不兼容。

- **STEP 4（转换前移动控制体积长程）：✅ PASS。** 2000 步、位移 0.579 nm、最大 Mach 4.3e-4、几何质量残差 R_geom 1.7e-4（<1e-3）；引入 geometry-aware 质量定义（alpha×rho，alpha 由连续压头表面解析求得）。
- **STEP 5（单次 fluid→solid 转换）：❌ FAIL。** step 3595 首次转换 2304 节点（凸台底面 1152 + 槽顶 1152，h=72.5 nm），转换后最大 Mach 1.085、rho [0.837,1.561]、R_geom 7.6e-3。
- **STEP 5.1（根因诊断）：根因已定位。** 转换 redistribution 把 alpha×F_i 分摊到下方 5 点模板，**模板重叠**——2024 个接收节点各接 5 个源，局部 rho 瞬时到 1.58；压力节点 prescribed rho=1 与 direct population（恢复 rho 1.52）不一致，被 Zou/He moments 解释为强法向速度（Mach 0.91）。异常在 collision 之前已存在。
- **STEP 5.2 候选 A**（8 层接收 + 隔离压力节点）：Mach 0.079 > 0.05、R_geom 5.8e-3，❌ FAIL。
- **STEP 5.2 候选 B**（局部平衡重构、丢弃非平衡应力）：Mach 0.188、R_geom 5.6e-3，❌ FAIL（更差）。
- **STEP 5.3（无转换移动边界）：✅ 转换前 PASS。** 3594 步、位移 2.499 nm、Mach 9.5e-4、R_geom 9.3e-4 全通过；但证明**"无转换的完整 10 nm 在真实 Bouzidi/材料实现下拓扑不可表示"**（2304 个 fluid 节点中心进入压头实体），停在首次转换前。

**结论**：转换前的连续移动（含排液、压力分布）已稳定可信；**唯一剩余阻塞是首次材料转换的 population 重分配与 Zou/He 固定 rho 压力边界的矩不一致**，尚无安全闭合方案。未进入第二次转换、STEP 6、两相/润湿/困气。

---

## 4. 关键技术阻塞（更新 2026-09-08）

**已解决**：移动壁 + 开放压力边界的失稳。根因是 LocalPressure 的全 population 正则化重建与移动 Bouzidi 斜向非平衡信息不兼容；换用 **Zou/He 压力边界**（只闭合未知入射 population）后，转换前连续移动稳定（STEP 4 / STEP 5.3 通过）。

**当前唯一阻塞**：**首次 fluid→solid 材料转换的 population 重分配**。转换层节点的 alpha×F_i 要转移到下方持久流体节点，但：

- 接收模板重叠，局部质量高度集中（单点 rho 1→1.58）；
- Zou/He 压力 cell 的 prescribed rho=1 与转移来的 direct population 总和（恢复 rho 1.52）不一致，被 moments 解释为强法向速度（Mach 0.91，collision 前即出现）。

三个候选（原模板重叠、8 层接收+隔离压力节点、局部平衡重构）均 FAIL（Mach 0.079–1.085、R_geom 5.6e-3–7.6e-3，门槛 0.05 / 1e-3）。需要设计**压力 cell 专用、矩一致的保守转换闭合**，并分别验证质量、动量及未知 incoming population 的唯一来源。

另：OpenLB 1.8r1 仍无公开、安全的动态材料重分类一站式接口；转换需逐节点改材料/动力学/Bouzidi 链接并同步 overlap，当前均为受限手工实现（未改库）。

---

## 5. 物理/参数决策（2026-09-07 确认）与剩余待确认

### 5.1 已确认

| 决策项 | 结论 | 影响 |
|---|---|---|
| 工艺极性 | **OAS layer-1 矩形 = 凹槽（沟槽）**，空白 = 凸台（实体墙） | ⚠️ 与现有 stage3 代码假设（矩形=凸台）相反，几何 material 标签需反转 |
| 沟槽深度 d_g | **100 nm（实际确认值）** | 从”拟采用/待确认”升级为”实际” |
| 65 nm 局部映射 | **暂定为下压后液膜厚度**（凸台底面最终间隙 `h_f = 65 nm`，暂定可调） | 采用”凸台底面对齐”映射：`h(0)=1000 nm → h(tf)=65 nm` |

### 5.2 对已完成结果的说明

极性反转只是交换凸台/凹槽的 x 位置（等价平移半周期），且”墙 120 nm / 槽 120 nm”的对称结构不变，因此：

- 阶段一 `B_yy = 97.6164 nm²`、阶段二 `B_xx ≈ 0`、h=65 nm 的 K 张量 **数值均不受影响**；
- 但 stage3 显式几何代码（`stage3_ex240_local/`、`ex240_homogenization/`）的 material 标签需反转，才与”矩形=凹槽”一致。

### 5.3 仍待确认

1. **供液**：局部初始液体体积/形状；
2. **润湿**：基底与压头接触角；
3. **气体**：是否接受”固定参考气压 + 忽略困气动力学”的 FreeSurface 基线。

---

## 6. 可写入论文 vs 需限定 vs 不能写

**可直接写**：单相 D3Q19 理想直沟槽周期输运实现；B_yy 网格序列及最细离散值；连续实体墙下 B_xx≈0；精确体积分数静态自由球 1200 步稳定。

**需加限定**：97.6164 nm² 仅是最细网格计算值（无 GCI）；静态 FreeSurface 无 trapped-air；8×8×8 体积分数是高阶采样近似；h=65 nm 等效化 K/B 是单点功能网格结果。

**当前不能写**：已验证完整 SIM-EC1XT240 版图、真实纳米沟槽压印、液滴融合/排气、移动压头质量守恒、困气压力。

---

## 7. 下一步（两条路线）

- **A 继续开发（工作量大、风险高）**：新增 `DynamicMaterialMap` / `ConversionTransaction` / `NeighborhoodUpdater` / `MovingBoundary`，先做 A0（<0.5dx 无转换的连续交点短测），再 A1（完整 10 nm + 两层节点转换 + 开放域质量账本）；若必须改库核心则先申请授权。
- **B 暂停阶段三（更稳妥）**：整理阶段一/二 + 静态 FreeSurface + h=65 等效化成果，补 GCI/总质量守恒/Laplace 验证后向老师汇报，等待工艺极性/深度/65 nm 映射/供液润湿四项决策。

---

## 8. 关键文件索引

| 内容 | 路径 |
|---|---|
| 版图解析 | `ex240_layout_report.md` |
| 阶段一/二/三总进度（旧） | `grooveDNS/OpenLB_EX240_progress_report.md` |
| 阶段一主 README 与 B_yy 完整推导 | `grooveDNS/README.md` |
| 阶段一质量/通量审计 | `grooveDNS/stage1_mass_flux_audit/stage1_three_grid_validation_report.md` |
| 阶段二阻断独立验证 | `grooveDNS/stage2_blocking_audit/stage2_blocking_validation_report.md` |
| 阶段三几何与工况定义 | `grooveDNS/stage3_design_review/stage3_geometry_and_case_definition.md` |
| 阶段三静态接入（10 步） | `grooveDNS/stage3_ex240_local/stage3_static_lattice_integration_report.md` |
| h=65 nm 固定间隙等效化 | `grooveDNS/ex240_homogenization/ex240_h65_homogenization_report.md` |
| 开放边界周期法向修复 | `grooveDNS/stage3_ex240_local/stage3_periodic_pressure_normal_fix_report.md` |
| 移动压头真实动态实现方案 | `grooveDNS/stage3_ex240_local/stage3_real_moving_boundary_implementation_plan.md` |
| 移动压头 10 nm 测试（失败记录） | `grooveDNS/stage3_ex240_local/stage3_explicit_piston_10nm_validation_report.md` |
| 宏观 OpenFOAM 基准参数核查 | `ZJ/nanrPrint/reports/EC1XT240_droplet_mold_parameter_report.md` |

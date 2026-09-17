# SIM240 阶段三步骤4：f3 上游因果与 LocalPressure 非零流诊断

日期：2026-09-08（Asia/Shanghai）  
工作目录：`grooveDNS/stage3_ex240_local/`

## 结论先行

步骤4仍为 **FAIL**，不得进入延长观察或步骤5材料转换。

`(0,0,13)`只是异常 `f3` 的接收 cell。真正的 `f3` 在上方 LocalPressure cell
`(0,0,14)` 的 `CombinedRLBdynamics`（LocalPressure 矩计算、全 population
regularized reconstruction 与嵌套 BGK collision）中生成，随后由 streaming 原样写入
`(0,0,13)`。220步逐算子记录中该复制的最大绝对误差为0。

反向追踪把反馈闭合为：

`(0,0,14).f8`（LocalPressure 已知 population）  
→ LocalPressure momenta / CombinedRLB collision  
→ `(0,0,14).f17`  
→ 同一步 streaming 到 `(0,1,15).f17`  
→ moving Bouzidi 方向17在 PostStream 覆盖 `(0,1,15).f8`  
→ 下一步经该普通流体 cell 的 collision/streaming 回到 `(0,0,14).f8`。

因此第二条链**重新连回了 `f8/f17` population 对**，但已不是原来同一双边界
cell上的直接双写，而是跨两个相邻 cell 的两步反馈。`f3` 是这个失稳矩在 z 方向的
输出分支，不是反馈环中唯一的 population。

固定几何、弱非零压力流的 LocalPressure 基准650步稳定；把移动壁与压力面隔开两层
普通流体后仍在 step 247 失稳。故当前根因不是“LocalPressure 对任何非零流都不稳定”，
也不再局限于同 cell 交线；最符合证据的分类是：

> **LocalPressure 与 moving-wall 产生的斜向非平衡 population 的兼容性问题。**
> 直接邻接会加快反馈，但不是失稳存在的必要条件。

## 保护与实际文件

此前第一候选、periodic seam 诊断、192条周期固壁 link 修复、B/C 650步结果及相位平移
对照均未修改或覆盖。冻结哈希和本轮命令见
`stage4_f3_diagnosis_run_manifest.txt`。

本轮新增或修改：

- `explicit_piston_f3_reverse_trace.cpp`：新增 C 的1–220步逐算子因果 trace，并增加已知稳定
  A 工况中共享普通流体 cell 的 population 参考；沿用第一处交线修复和周期感知固壁 link。
- `explicit_localpressure_nonzero_baseline.cpp`：固定几何、LocalPressure 弱非零流650步基准。
- `explicit_piston_pressure_separated_control.cpp`：移动壁与压力面隔离对照。
- `analyze_f3_reverse_trace.py`：只读处理逐算子 CSV，生成参考差值、选定步因果表和全部
  LocalPressure 输入 population 贡献表。
- `Makefile`：仅增加上述三个独立目标。
- `stage4_f3_diagnosis_run_manifest.txt`：哈希、命令、退出状态及首次诊断源编译失败记录。

没有修改 OpenLB、阶段一、阶段二、其他阶段三目录或原 `tmp/`。

## 工况与结果

| 工况 | 用途 | 步数 | 结果 |
|---|---|---:|---|
| C 逐算子 trace | 第一修复 + 周期固壁 link 修复；moving Bouzidi + LocalPressure | 220 | 完成；复现 step 209 的增长链 |
| A population 参考 | moving Bouzidi + 封闭侧壁 | 220（已有全局A为650） | trace完成；已有A-650稳定，最大Mach `5.33e-4` |
| LocalPressure 非零流基准 | 固定几何，无Bouzidi；x/z周期，y两端小压差 | 650 | **PASS** |
| pressure–moving 分离对照 | moving Bouzidi + LocalPressure；两层普通流体隔开 | 650 | **FAIL**：Mach step 247，rho step 278 |

所有移动诊断保持原 C 的 `dx=5 nm`、`dt=1e-11 s`、物性、五次轨迹和壁速；没有材料
转换、参数调稳、速度/密度裁剪或质量归一化。

## f3 的最早偏离和逐算子来源

### 时间定义

本 OpenLB 版本没有独立的“LocalPressure postprocessor 前/后”状态。LocalPressure 使用
`CombinedRLBdynamics`，在同一次 cell collision 调用中依次完成：固定密度与压力矩计算、
边界应力计算、19个 population regularized reconstruction、嵌套 BGK collision。因此
本报告的 `post_LP_reconstruction_and_collision` 是能由公开执行路径取得的最细边界。

### 三个时间点

1. step 2：moving Bouzidi 的最初壁速扰动经 streaming 到达 `(0,0,14)`。
2. step 3：`(0,0,14)` 的 LocalPressure/CombinedRLB collision 首次生成非零
   `f3=2.4997471e-12`，同一步 streaming 将其无误差复制到 `(0,0,13).f3`。这是
   `f3` 的**最早可验证偏离**。
3. step 4：共享普通流体 Bouzidi cell `(0,1,15)` 的 PostStream `f8` 与稳定 A 参考的
   绝对差首次超过预定分析分辨值 `1e-12`：C为 `1.22414275e-10`，A为
   `1.24914015e-10`，差 `-2.49974047e-12`。此后该差持续增长。

`(0,0,14)` 的 collision 后 `f3` 经短暂换号后，从 step 52 起保持负号且
`|f3|` 每步单调增长至 trace 终点：

| step | collision后 `(0,0,14).f3` |
|---:|---:|
| 3 | `2.4997471e-12` |
| 52 | `-1.2708119e-9` |
| 100 | `-1.6069677e-6` |
| 160 | `-8.9807855e-5` |
| 200 | `-1.3636621e-3` |
| 209 | `-2.5281646e-3` |

所以必须区分：最早因果偏离是step 3；相对于稳定参考可清晰分辨的反馈差是step 4；
`f3` 本身进入不再回落的单调 runaway 分支是step 52。这三者都早于step 209的Mach门槛。

### step 209 的跨阈过程

- `(0,0,14)` collision 后：`f3=-2.5281646e-3`，边界矩Mach `0.0433386`。
- 已保留的遗漏周期link旧trace中，`(0,0,13)` Mach由collision后的`0.04713`升到
  streaming后的`0.05056`。
- 本轮采用几何正确的192条周期link基线后，对应值为`0.0489324→0.0524851`；
  streaming后 `f3=-2.5281646e-3`。数值略变但跨阈步骤和因果方向不变。
- 后续 PostStream communication 和 Bouzidi 不再修改 `(0,0,13)`。

因此 streaming 是step 209使接收 cell 跨阈的阶段，但不是制造异常 `f3` 的算子；制造者
是 donor cell 的 LocalPressure/CombinedRLB collision。

## f3 的上游 population

低 y 面的 LocalPressure 法向为 `direction=1, orientation=-1`。本版本
`FixedPressureMomentum` 读取 `c_y=0` 和 `c_y=-1` 的14个 populations；固定密度为1，
法向速度分子中 `c_y=-1` 项权重为 `-2`，`c_y=0` 项权重为 `-1`。

step 209、collision 前 `(0,0,14)` 的最大贡献如下：

| 排名 | population | shifted值 | 对法向速度分子的贡献 |
|---:|---:|---:|---:|
| 1 | `f0` | `4.1006243e-2` | `-4.1006243e-2` |
| 2 | `f8` | `-1.3598939e-2` | `+2.7197878e-2` |
| 3 | `f10` | `8.3383437e-3` | `-8.3383437e-3` |
| 4 | `f1` | `8.2750083e-3` | `-8.2750083e-3` |
| 5 | `f3` | `-2.0569018e-3` | `+2.0569018e-3` |
| 6 | `f9` | `-5.7654134e-4` | `+1.1530827e-3` |

全部14项及各步排名保存在
`output/f3_reverse_causal_trace_C_v3_20260908/localpressure_f3_input_population_contributions.csv`。
`f0/f1/f10`是已经被前几轮 LocalPressure reconstruction 带入反馈的局部矩分量；跨边界
耦合的关键载体仍是 `f8`。LocalPressure collision 同时输出 `f3` 和未知侧 `f17`；
`f17` 经 streaming 到 `(0,1,15)` 后被方向17 Bouzidi 读入并用来覆盖 opposite population
`f8`，从而闭环。

例如step 209：

- donor collision 输出 `f17=-1.6724099e-2`；
- streaming 后 `(0,1,15).f17` 完全相同；
- Bouzidi 前该 cell `f8=-1.7996066e-4`；
- Bouzidi 后 `f8=-1.5609655e-2`；
- 稳定A中同一普通流体 cell 的对应 `f8=9.9686898e-6`。

这说明第一处 `f8/f17` 修复方向是正确的：它去除了原双边界 cell 的直接冲突并延迟了
失稳；但只修同 cell 归属并未处理相邻 cell 间同构的 `f17→Bouzidi→f8→LocalPressure`
反馈，所以不完整。

## LocalPressure 固定几何非零流基准

为避免把“固定壁 + LocalPressure + 零场”的B-650过度外推，新建16×16×16节点直通域：
x/z周期、y两端 LocalPressure，密度从 `1+1e-6` 到 `1-1e-6`，其余单位映射、D3Q19、
BGK与本项目一致；无 moving Bouzidi。

预先冻结的验收为：650步有限、Mach≤0.01、rho∈[0.99,1.01]、存在非零流、最大相对
质量收支残差≤`1e-5`。实际结果：

- 650步、退出码0，**PASS**；
- 最大Mach `5.0152543e-5`；
- rho范围 `[0.999999, 1.000001]`；
- 低端向外通量 `-9.2231110e-14 kg/s`（即流入）；
- 高端向外通量 `+9.2657777e-14 kg/s`；
- 最大绝对相对质量收支残差 `2.9134733e-14`；
- 无非有限值。

方向和两端通量符号符合从高密度端向低密度端的弱压力驱动。本测试证明当前
LocalPressure实现能稳定处理简单非零正向流；它不是完整的压力边界精度验证。

## moving wall 与 LocalPressure 分离对照

诊断域将 y 延长到280 nm；移动压头只占 `20≤y<260 nm`，两端缓冲段保留初始形状的
固定顶壁。压力面 cell与最近 moving-Bouzidi cell 的 lattice-index距离为3，中间有两层
普通流体；全程 `pressure_moving_dual_cells=0`。dx、dt、物性、移动轨迹、壁速、压力值和
冻结阈值与原C相同，无材料转换。

结果仍为 **FAIL**：

- step 247 首次Mach>0.05；
- step 278 首次rho超出[0.8,1.2]；
- 650步内尚无NaN/Inf，但最大Mach已达 `1.51018e11`，属于巨大有限值发散；
- 首异常仍位于低 y LocalPressure 面、mesa下方；
- 非法link=0、材料转换=0、材料场不变；
- 因解已发散，650步质量与通量数值不具物理解读意义。

和原C的step 209相比，隔离只把首次Mach门槛推迟到step 247。因此直接交线/共享cell会
增强反馈，但不是必要条件；moving-wall产生的斜向非平衡扰动传播到 LocalPressure 后仍会
激发同类增长。

## 根因判断与第三候选边界

证据已足以设计、但本轮没有实施第三个候选。最小且证据最充分的下一候选是：

> 保持两端相同参考压力和真实开放排液物理条件，把整个压力面从“重建全部19个
> populations”的 LocalPressure 改为本版本受支持、只闭合未知法向 populations 的
> `ZouHePressure`；继续保留固壁交线的唯一边界归属和周期感知固壁 links。

理由是固定非零 LocalPressure 基准稳定，而失稳闭环具体经过其全 population
regularized reconstruction；第一候选中局部改为 ZouHe 已延迟失稳。该候选仍必须先做
B-650和转换前C-650回归，不能由本报告直接判定有效，也不能通过调黏度、dt、壁速或裁剪
population来替代。

## 对本轮十个问题的直接回答

1. **`(0,0,13)`是否只是异常接收cell？** 是。其step 209异常 `f3` 来自
   `(0,0,14)`，streaming复制误差为0。
2. **`(0,0,14).f3`何时开始偏离？** step 3首次可验证非零偏离；step 52起
   `|f3|`单调增长。相对于稳定A共享普通流体参考，闭环载体 `f8` 在step 4出现首个
   ≥`1e-12`的清晰差值。
3. **第一个制造异常f3的operator？** `(0,0,14)` 的 LocalPressure
   `CombinedRLBdynamics` collision；streaming只搬运它。
4. **依赖哪些上游populations？** LocalPressure读取全部14个 `c_y∈{0,-1}` 项；
   step 209主要矩贡献是 `f0、f8、f10、f1、f3、f9`。因果闭环的跨cell载体是
   `f8`，返回支路是 `f17`。
5. **是否连回此前f8/f17链？** 是，population对相同，但由“同双边界cell”转移为
   `(0,0,14)` LocalPressure 与 `(0,1,15)` moving Bouzidi 间的两步空间反馈。
6. **LocalPressure固定几何非零流是否稳定？** 是，650步PASS，最大Mach
   `5.02e-5`，最大相对质量收支残差 `2.91e-14`。
7. **与moving wall分离后是否稳定？** 否；Mach step 247、rho step 278，650步巨大
   有限值发散。
8. **根因分类？** `LocalPressure—moving wall非平衡population兼容问题`；它比“同cell
   交线问题”更一般。没有证据支持周期halo或普通streaming复制错误。
9. **是否足够设计第三候选？** 是；可测试全压力面 `ZouHePressure` 的唯一未知
   population闭合，但本轮未实施、未判PASS。
10. **是否仍停留步骤4？** 是。当前生产C仍不满足冻结阈值。

**不允许进入延长观察；不允许进入步骤5单次材料转换账本。**

## 数据位置

- C逐算子trace：`output/f3_reverse_causal_trace_C_v3_20260908/`
- 稳定A population参考：`output/f3_moving_closed_A_population_reference_20260908/`
- LocalPressure非零流基准：`output/localpressure_fixed_nonzero_flow_650_20260907/`
- moving/pressure分离对照：`output/moving_piston_pressure_separated_C650_20260908/`
- 可复现分析：`analyze_f3_reverse_trace.py`

本轮没有运行完整10 nm、2000步延长、材料转换、液滴、润湿、空气、网格扫描或任何
参数调稳。

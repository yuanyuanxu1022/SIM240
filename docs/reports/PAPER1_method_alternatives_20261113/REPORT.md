# 19P＋4T、DOE与替代参考方法：定点文献核查

日期：2026-11-13。用户目的已澄清：主要希望第一篇的方法与成果同横向项目形成学术区分，并非已确认“使用FVM便必须署某项目名”的合同要求。本轮只查文献、下载公开材料并静态读代码；无安装、编译、求解器启动/续跑/停止、拟合、母稿修改、Gate或参考资格变化。不是系统综述，不作全体文献不存在的结论。

## 1. 三个维度不能混为二选一

| 维度 | 本项目含义 | 回答的问题 |
|---|---|---|
| 覆盖目标：19P＋4T | 19个几何的沿槽和4个几何的横槽，共23条目标方向参考；不是23个几何或全19几何双向覆盖 | 哪些K需要另一个实现的合格参照？ |
| DOE：选点与分析组织 | 当前已有h50/75/125×d25/50/75/100/120共15几何，h25三个几何单列；18几何36个OpenLB方向结果全部保留 | 参数趋势怎样、代表点为何有代表性？ |
| 求解方法：LBM/FVM/FEM等 | 可对同一选定几何与同一边值问题使用不同离散或表示方法 | 怎样独立求K？ |

因此可以“用DOE组织点集，用FEM完成19P＋4T”，或经老师同意采用较少的成对代表几何。DOE不是求解器，也不能代替独立数值检查。目标是全沿槽图交叉支撑时，19P＋4T覆盖更充分；目标是基准与代表几何的各向异性比较时，DOE指导的成对子集效率更高，但支持范围更小。NIST要求先写清目标再选设计，不以设计名称替代证据目标。

## 2. 针对当前目的的建议

**正式落地首选：独立二维混合有限元（FEM），分别求沿槽Poisson与横槽Stokes。** 理由是同一工具可以覆盖两方向、无滑移矩形边界及周期条件；选择稳定速度/压力配对并固定压力零空间后，可用稀疏直接法求离散稳态系统，减少对当前SIMPLE外迭代路径的依赖。尖角仍需局部网格与收敛核查，FEM不自动更准，不承诺耗时或门槛通过。FreeFEM官方文档给出P2/P1 Taylor–Hood Stokes示例和周期有限元空间语法；这些是实现基础，不是本项目现成经过验收的求解器。

**最值得进一步做静态适配的专门候选：Xue 2025周期有理逼近。** 它更贴合横槽周期尖角Stokes问题，原文及代码支持范围已核；新颖的方法名称不自动成为本文贡献。若其环境与适配成本可接受，可作为横槽参考路线候选；沿槽仍需独立Poisson解。现在不宣布替换已合格FVM，不同时启动FEM、BEM和有理逼近三个开发项目。

用户的学术区分应体现在研究问题、代码来源、几何/数据集合及贡献上：第一篇围绕固定全充液理想Stokes问题的双主导度、各向异性失真、理论约束与有限经验修正；既有OpenFOAM平均模型接入保留为接口核对，其与显式沟槽独立参考各有任务。仅换软件名不足以证明成果独立；成果归属与致谢仍须依真实投入及导师/机构安排处理，不由本报告推断。用户未提出隐去实际资助或贡献的要求。

## 3. 找到的直接相关原文与代码

### 3.1 Xue（2025）：周期尖角通道有理逼近——新找到、最贴近横槽的专门候选

Y. Xue, *Computing Stokes flows in periodic channels via rational approximation*, Proc. R. Soc. A 481, 20240676 (2025), DOI: https://doi.org/10.1098/rspa.2024.0676 。Crossref和arXiv刊发对应已核。出版社直达页面本轮工具访问失败，核读的是完整arXiv:2407.14864v1（19页），不是已逐字核对的出版排版版。

- §1式(1.1)–(1.5)：二维不可压Stokes、速度周期和每周期固定压力降；稳态Poiseuille工况两壁静止、无滑移。§2给尺度换算。
- §5.1–5.3：边界采样、域外极点、Arnoldi正交化与线性最小二乘；周期性写入三角有理基底。它是数值有理逼近，不是无截断的精确闭式，也不是普通全域Fourier级数。
- §6.1、图4(b)，预印本PDF第10–11页：明确计算带直角的周期通道；第11页图4已渲染目视核对。例子为两面图案壁，尚不是本项目一平壁一槽壁的同条件例。
- 作者仓库：https://github.com/YidanXue/periodic_Stokes_flow ，README与`poiseuille_sharp.m`已取得并静态核读；固定commit `7235ab345324a5928d9c04360567214be067b396`，未执行。脚本含直角通道、静壁、压力梯度与解析导数形式的速度/压力函数。
- 尚须适配：一壁平直；槽/凸台各半；本项目h,d,w和P归一化；取消不适合目标的几何对称捷径；由通量求K；在未参与配点的边界位置独立验残差，并检查极点/次数/配点及通量积分收敛。
- 论文示例的速度与位数不外推为本项目运行时间或误差保证。代码推荐MATLAB R2023b并依赖Chebfun的`aaa.m`，README也提到Octave；本轮未证实本机兼容运行。根目录LICENSE查询404，未核全仓库授权，不将第三方代码纳入本轮Git或承诺可直接重发布。

### 3.2 Brubeck–Trefethen（2022）与Xue–Waters–Trefethen（2024）：尖角本身并不排除高精度函数逼近

P. D. Brubeck and L. N. Trefethen, *Lightning Stokes Solver*, SIAM J. Sci. Comput. 44 (2022), A1205–A1226, DOI: https://doi.org/10.1137/21M1408579 。牛津出版PDF在web工具可读，curl本地下载超时为不完整文件；已另取完整arXiv:2107.01572，后者PDF抽取成功。论文使用靠近角点聚集的域外极点及Goursat表示处理Stokes双调和问题，示例包含台阶通道；普通步进示例的进出口条件不能直接冒充周期槽。

Y. Xue, S. L. Waters and L. N. Trefethen, *Computation of Two-Dimensional Stokes Flows via Lightning and AAA Rational Approximation*, SIAM J. Sci. Comput. 46 (2024), A1214–A1234, DOI: https://doi.org/10.1137/23M1576876 。取得完整arXiv:2306.13545v2，相关方法与代码 https://github.com/YidanXue/LARS 。一般区域能力不能替代专门周期实现的核验，因此对本项目优先看2025周期扩展。

结论：不能统称“谱方法只适合规则矩形、不适合沟槽直角”。普通光滑全局展开可能受角点奇异性影响，域分解、奇异函数增强及有理逼近有专门处理方法。本项目既有Ng2017已取得接受稿也明确使用矩形区域分解和特征函数匹配；这是另一条半解析路线，但其双槽壁与清流层等效滑移定义不能直接套成本项目全流体K。

### 3.3 Bystricky–Pålsson–Tornberg（2021）：边界积分已有周期尖角通道方案

L. Bystricky, S. Pålsson and A.-K. Tornberg, *An accurate integral equation method for Stokes flow with piecewise smooth boundaries*, BIT Numer. Math. 61 (2021), 309–335, DOI: https://doi.org/10.1007/s10543-020-00816-1 。在线首发2020-08-07，卷期2021，二者不矛盾。取得完整出版PDF；摘要、§2–5说明周期二维通道和允许角点的Lipschitz边界，Nyström离散加递归压缩逆预条件（RCIP）处理角点奇异性，文中亦有液滴扩展；本项目只涉及其单相Stokes基础，不扩展两相任务。

它说明BEM可行，不能证明实现成本必然最低。没有本项目现成代码和同条件K验收，暂不推荐从零搭整套BEM。

另查Barnett、Marple、Veerapaneni、Zhao的 *A unified integral equation scheme for doubly-periodic Laplace and Stokes boundary value problems in two dimensions*, arXiv:1611.08038。官方摘要明确无需周期Green函数或Ewald格点求和。该摘要展示的是双周期、光滑夹杂，不能据此认证本项目单周期尖角通道；它只足以纠正“周期BEM必用Ewald”的绝对说法。

### 3.4 Hecht（2012）与FreeFEM官方文档：最稳妥的工程备选基础

F. Hecht, *New development in freefem++*, J. Numer. Math. 20 (2012), DOI: https://doi.org/10.1515/jnum-2012-0013 。本轮核Crossref元数据及官方完整文档，未取得并逐节核该软件论文全文，不以软件论文题名认证本项目精度。

官方Stokes模型：https://doc.freefem.org/models/navier-stokes-equations.html ，Taylor–Hood小节使用二次速度P2和一次压力P1；周期空间：https://doc.freefem.org/models/static-problems.html 的periodic boundary conditions小节。二维矩形槽可贴体剖分，角点局部加密；周期配对与压力均值/零空间、体力及功率账要显式定义，不能直接复制带压力罚项的教程然后默认其影响为零。

## 4. 对用户方法分类的纠正

- **换LBM库不等于毫无独立性**：可查实现差错，特别是边界实现；共同的LBM近似和相似格点误差可能保留。与另一个方法解同一边值问题相比，证据互补性不同，不能简单打成“不能算独立”。
- **润滑近似不宜作为本项目的通用真值**：适用假设和有证明的截断误差估计需分开；Wilkening等在符合正则性条件时能给定量约束，理想矩形台阶不能直接套。不能把全部渐近理论说成只给定性趋势。
- **平板是最直接的精确基准，不是所有可解析/半解析问题的全集**；矩形槽已有特征函数匹配研究。是否同条件取决于边界、域、驱动和通量定义。
- **理论上下界是连续模型约束**；不认证离散K精度、V2准确度或物理真实性。用户给出的界宽倍率本轮没有逐点复算，不作为新结论背书。
- **MD/DSMC分类应按任务**：MD可以提供不同物理层面的信息，但不等于相同连续Stokes方程的另一种离散；DSMC通常针对稀薄气体，不适合直接用来裁判本项目液体Stokes K。本篇无需增加这条路线。

## 5. 本项目可落地的方程与验证对象

沿槽，在真实二维截面Ω求：`−μΔv_y=G`，壁面无滑移、x周期，`K_parallel=μ/(G P)∫Ω v_y dA`。横槽求：`−μΔu+∇p'=G e_x`、`div u=0`，周期速度及周期扰动压力、壁面无滑移；也可等价使用无体力且每周期压力降Δp=GP的形式。二者只能选一种驱动记账方式，不能叠加。

横槽截面通量`q=∫u_x dz`在理想稳态不可压条件下沿x不变，`K_perp=μ P q/Δp`，单位m³。Xue代码的无量纲周期为2π、`dp=1`表示压力梯度参数，不能不换算就抄成nm几何或把流量当K。P在本项目是沿槽方向标签时也要与周期P的符号区分。

新方法只在平板归一化、周期/壁面/压力零空间、线性求解误差、网格或函数基底收敛、通量积分和功率核对后才能承担参考任务。数值阈值须在新协议中先定；旧FVM协议及FAIL原样保留，不将FVM日志残差阈值机械移植给FEM或有理逼近。当前仅为方法候选研究，不改变原19P＋4T目标或R2待裁定状态。

## 6. 当前工程事实与下一步停点

当前被调用的Python为`/home/dell/miniconda3/bin/python3`；本次PATH未找到FreeFem++、MATLAB、Octave，当前Python中dolfinx/skfem未发现，gmsh命令存在。此为当前会话环境检查，不代表服务器和所有Python环境均无这些软件，未安装任何软件。

最新状态入口另有冻结FVM发布的系统库指纹及跨机回执阻塞报告；本轮没有重新执行其自检，也没有试图绕开。该阻塞是既有发布/执行证据链的问题，不证明FVM方法在科学上失效；h125T已出现数值收敛但资格未授予的新证据，不能再沿用“残差永远不可达”的旧话。

推荐下一步只做**二维FEM方案的静态设计与环境可获得性核查**，同时保留本报告已完成的Xue周期代码适配问题单；先选择一条正式路线，再另行授权安装/测试/运行。科学覆盖可按原19P＋4T或老师认可的DOE代表成对子集实施，两者都可用FEM。已有合格FVM证据继续可追溯，不为改方法回写旧结果。

## 7. 检索范围、访问限制与证据

本轮使用定点web检索、Crossref单DOI记录、官方arXiv、作者/大学存档、FreeFEM官方文档和GitHub作者代码。关键词涵盖periodic Stokes、rectangular grooves/eigenfunction matching、corner singularities、Taylor–Hood、Ewald-free boundary integral。不是完整查新，不据此声明FEM或有理逼近在本领域首次应用。

完整PDF、抽取文本与第三方脚本仅留库外`SIM240_runtime_records/method_alternatives_20261113/`；本报告的SOURCE_MANIFEST和CODE_SOURCE只保留路径、URL、版本与指纹。Brubeck一条初始DOI候选查到别的题名，已明确拒绝，不入引用；正确DOI从论文首页取得并经Crossref匹配。牛津PDF下载超时不当成全文取得；改取完整arXiv版本。Xue2025出版页面访问失败、完整预印本取得，不混称版本。

工具方法：paper-lookup、literature-review、scientific-critical-thinking。Kassis等(2026), *Scientific Agent Skills: A Library of Procedural Knowledge for Research Agents*, https://doi.org/10.48550/arXiv.2609.00065 ，仅为工具方法参考；当前元数据本会话此前已核，不作为流动物理证据。

# 定向文献核对与检索边界（2026-11-10）

目的：确认数值验证是否仅能靠另一软件/实验，以及二维独立参考与可计算误差控制是否有依据。本轮是定向方法查证，不是穷尽性综述或新颖性认证；不向搜索服务提交未发表稿件。

## 主要来源及支持范围

1. NASA NPARC, Verification Assessment：https://www.grc.nasa.gov/www/wind/valid/tutorial/verassess.html 。网页全文可读；支持解析/高精度数值基准、网格检查及不同算法比较的分工，也明确另一程序可能不准确。不引用其老页面中“尚无标准”等时代性句子作为2026年事实。
2. NASA NPARC, Overview of CFD Verification and Validation：https://www.grc.nasa.gov/WWW/wind/valid/tutorial/overview.html 。网页全文可读；支持数学实现核验与面向实验的物理验证的区别，不据此建立五级强弱阶梯。
3. Lederer P. L., Merdon C., Guaranteed upper bounds for the velocity error of pressure-robust Stokes discretisations。arXiv:2008.05816v2（2021修订）：https://arxiv.org/html/2008.05816v2 。已读§2.1、§2.3定理2.1及其条件，以及§5的散度相关限制；全文可读。Crossref按精确标题检索rows=2，首条作者/题名匹配，发表记录为Journal of Numerical Mathematics（2022），DOI 10.1515/jnma-2021-0078。查询及结构化返回见crossref_metadata.json。框架证明速度误差控制，原文§2.1是齐次Dirichlet边界，未找到periodic字样；故不得说直接给本项目周期槽的K界，必须适配边界与目标量。
4. Vohralík M., A posteriori error estimates via equilibrated fluxes（作者2025/2026课程）：https://who.rocq.inria.fr/Martin.Vohralik/Pages/APost.html 。作者页面可读，确认primal/dual、平衡重构、Stokes及自适应等方法路线；作为方法地图，不替代第3项原始论文证明。
5. DOLFINx官方Stokes/Taylor–Hood例程：https://docs.fenicsproject.org/dolfinx/main/python/demos/demo_stokes.html 。已读方程、二维方腔边界、P2/P1空间及线性求解器说明。仅支持现有独立有限元框架有Stokes基础构件，不意味着已具备本项目周期槽脚本或误差认证。
6. Ng C.-O. (2017), Effective slip for Stokes flow between two grooved walls with an arbitrary phase shift，Fluid Dynamics Research 49, 025516，DOI 10.1088/1873-7005/aa5b58。作者机构记录：https://hub.hku.hk/handle/10722/231998 。本轮核题名/作者/DOI/双槽壁范围；结合当前稿已有边界说明，不直接拿其两槽壁或清流层滑移量当作本文一平一槽全流体积分K。未声称本轮重新解读其整篇全文或已完成适配。

## 搜索记录

web查询：
- Stokes flow guaranteed upper lower bounds permeability equilibrated stress finite element goal oriented error estimate
- fully computable a posteriori error estimates Stokes equations equilibrated flux Vohralik
- Ng 2017 pressure driven Stokes flow rectangular grooves walls eigenfunction expansion longitudinal transverse
- site.docs.fenicsproject.org dolfinx Stokes Taylor Hood demo
- site.arxiv.org "Guaranteed upper bounds" "Lederer" "Merdon"
- site.nasa.gov verification validation CFD grid convergence code verification analytical solutions manufactured solutions

Crossref查询URL及首2条返回已结构化保存；第二条为不相关书章，未采用。arXiv与作者机构/官方文档仅使用公开研究内容。未采用维基百科、论坛或商业二手综述作技术依据。

访问限制：Computers & Mathematics with Applications论文DOI10.1016/j.camwa.2013.12.011的ScienceDirect正文403，仅摘要/元信息可见，未作为本方案核心证明。部分检索到的goal-oriented上下界论文只相对overkill mesh，不混写成连续解认证。MMS检索只作代码核验路线补充，不声称可直接确定真实槽几何的生产K。

工具/技能：scientific-critical-thinking用于拆分证据问题，paper-lookup用于公开来源定向查证及Crossref元数据；不以技能或AI模型名称作为独立科学证据。

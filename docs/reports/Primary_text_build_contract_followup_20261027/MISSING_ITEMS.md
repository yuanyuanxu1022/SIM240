# 可直接交接的缺失材料清单

2026-10-27，按原[最小证据合同](../Primary_text_build_evidence_20261027/MINIMUM_EVIDENCE_CONTRACT.md)接收；不授权新计算。

|项|应取得的原件|身份入口|收到后检查|
|---|---|---|---|
|P8|M. Bouzidi, M. Firdaouss, P. Lallemand. *Momentum transfer of a Boltzmann-lattice fluid with boundaries*. Physics of Fluids 13(11), 3452–3459 (2001)，完整8页；作者版本须标明|[DOI](https://doi.org/10.1063/1.1399290)|固定边界插值、q、时间层、q=0.5及当前实现对应|
|P9|Z. Guo, C. Zheng, B. Shi. *Discrete lattice effects on the forcing term in the lattice Boltzmann method*. Physical Review E 65, 046308 (2002)，完整6页|[DOI](https://doi.org/10.1103/PhysRevE.65.046308)|力项、速度定义、半步修正、密度/单位和当前实现对应|
|P10|I. B. Celik, U. Ghia, P. J. Roache, C. J. Freitas, H. Coleman, P. E. Raad. *Procedure for Estimation and Reporting of Uncertainty Due to Discretization in CFD Applications*. Journal of Fluids Engineering 130(7), 078001 (2008)，发表版完整4页|[DOI](https://doi.org/10.1115/1.2960953)|与已有四作者方法文稿逐页对应，步骤3—5、迭代误差说明，文稿式4/6上标差异的发表版情况|

可使用合法机构订阅、馆际互借或作者公开版本。取得文件时保留原始文件和来源说明，不需要改名或拆页。仅在另一篇文章的参考文献页出现题名/DOI，不算收到原件。

历史构建：

- `285f67a0aa31ee63bc527b78619a1141c039e01bf8c910c1c4e137d6447c928c`：22项记录，对应原程序仍待找回。
- `efd24c98efd8d7709893df3e8db2bc7537ab149b1d45bc8d22c5eac4ca7e3f81`：2项记录，对应原程序仍待找回。
- `57611b21584c8f32dabd5d4ff240616c65f245930b00a1a40dae5f8d3169f2d6`：22项，现存D2程序匹配；仍缺同次完整构建输入与实际命令。
- `85cc9dee8db9a245419a3a152efb72fc9958e29b8dac7a356f4667e54fd5bf66`：6项，现存D3程序匹配；仍缺同次完整构建输入与实际命令。

每组可共用一套有直接关联的源码/补丁、OpenLB与链接库快照、编译器和真实命令日志，不必52项各复制一套。若无法恢复，保留来源限制；新建基线不等于恢复旧来源。材料到齐前，不开始新的编译、求解或理论审定。

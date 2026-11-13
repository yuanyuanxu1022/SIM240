# h125/d120 FEM补充对照候选措辞（未合入）

## 当前状态即可使用的中文表述

作为补充数值核验，在h=125 nm、d=120 nm、w=120 nm和P=240 nm的同一周期矩形沟槽上，采用P2/P1混合有限元求解横槽Stokes问题。5、2.5和1.25 nm三档网格的导度依次为1.839540、1.837897和1.837113×10⁻²² m³，后两次相邻网格变化为0.0893%和0.0427%。保存场经过导度重积分、方程残差及截面通量检查。该结果目前按经复核的FEM试点结果报告，不赋予既有FVM协议下的正式参考身份。

将FEM横槽细网格结果与同条件、已通过原参考接收的FVM沿槽结果（2.784040×10⁻²² m³）组合，得到候选主值比Kyy/Kxx=1.5154。相对于这组组合数值，局部立方律的沿槽和横槽导度偏差分别为+149.33%和+56.42%，固定V2分别为−9.94%和+4.98%。V2减小了两主导度的偏差幅度，但方向比仍低估14.21%；对于相对槽轴45°的驱动，由同一对主值重建的平均通量方向仍相差+4.15°。这些单几何结果单列于原36条5 nm主比较之外，不构成新增独立盲测或全参数域精度保证。

## English candidate with the same current status

As a supplementary numerical check, the transverse Stokes problem was solved using a P2/P1 mixed finite-element discretization for the same periodic rectangular-groove geometry with h=125 nm, d=120 nm, w=120 nm, and P=240 nm. The conductances on the 5, 2.5, and 1.25 nm meshes were 1.839540, 1.837897, and 1.837113×10⁻²² m³, respectively; the successive relative changes were 0.0893% and 0.0427%. The archived fields were checked by reintegration of conductance, reconstruction of the discrete-equation residual, and cross-sectional flux calculations. This result is reported as a checked FEM pilot result and has not been qualified under the existing FVM reference protocol.

Combining the fine-mesh FEM transverse value with the previously qualified FVM longitudinal value under matching conditions (2.784040×10⁻²² m³) gives a candidate principal-conductance ratio Kyy/Kxx=1.5154. Relative to this combined numerical comparison, the longitudinal and transverse deviations of the local cubic-law formula are +149.33% and +56.42%; the corresponding deviations of the fixed V2 correction are −9.94% and +4.98%. V2 reduces the magnitudes of both conductance deviations, but still underestimates the principal-conductance ratio by 14.21%. For forcing at 45° to the groove axis, the mean-flux direction reconstructed from the same principal values retains a difference of +4.15°. These single-geometry results are reported separately from the original 36 comparisons against the 5 nm reference and do not constitute a new independent blind test or a parameter-domain accuracy guarantee.

## 中英文表注

P表示沿槽y方向，T表示横槽x方向；A=KP/KT=Kyy/Kxx。组合对照的P采用已合格FVM值，T采用尚未正式资格化的FEM试点值，不能将该表列为已合格参考计数。各方向偏差定义为(K方法/K组合对照−1)×100%；方向比偏差以A组合对照为分母。β=atan(KT/KP)表示相对槽轴45°驱动下重建的平均通量方向，角差为β方法−β组合对照，不是独立斜向仿真。网格变化不作为严格误差界；不同离散方法的原始网格间距不等价。正式接收后须引用独立FEM接收记录并更新身份文字，不能只删除“试点”两字。

P denotes the longitudinal y direction and T the transverse x direction; A=KP/KT=Kyy/Kxx. The combined comparison uses the qualified FVM value for P and the FEM pilot value, not yet formally qualified, for T; this table is excluded from counts of qualified reference pairs. Directional deviations are (Kmethod/Kcombined−1)×100%, and ratio deviations use Acombined as the denominator. β=atan(KT/KP) is the mean-flux direction reconstructed for forcing at 45° to the groove axis; angular differences are βmethod−βcombined and are not results of independent oblique-flow simulations. Successive mesh changes are not rigorous error bounds, and nominal mesh spacings are not equivalent across discretization methods. Formal adoption requires a separate FEM acceptance record and corresponding status updates, not simply deletion of the word “pilot”.

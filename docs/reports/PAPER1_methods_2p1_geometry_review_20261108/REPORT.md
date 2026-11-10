# §2.1几何、坐标和间隙定义审读

日期：2026-11-08，Asia/Shanghai。用户要求审读几何定义、坐标方向与间隙参数。本轮范围为开头几何文字、图1/图注及相邻几何采样说明；不重审后面的离散/碰撞/驱动实现，不改正式稿、图片或代码。

## 现有开头两段

计算域取周期线槽的一个单胞。图案沿 $x$ 方向重复，沟槽沿 $y$ 方向延伸，因此沿槽输运记作 $\parallel$（对应 $K_{yy}$），跨槽输运记作 $\perp$（对应 $K_{xx}$）。

周期 $P=240$ nm、槽宽 $w=120$ nm，槽与凸台等宽。凸台底面距平面基底为 $h$（残余间隙），槽顶距基底为 $h+d$（$d$ 为槽深）。全部可用空间由液体充满。


## 裁定

现有P240nm、w120nm、y沿槽Kyy/x跨槽Kxx、h残隙与h+d槽内高度的定义基本正确。建议补z厚度坐标、凸台总宽度和宽度占比，显式区分局部间隙H(x)、最小残隙h及体积等效参考高度H_ref。固定间隙指同一个算例内固定，非全部算例h相同，也不表示动态压印已验证。

### 参数对应

|符号|定义|基准h75/d100时|
|---|---|---|
|P|横槽x方向的图案周期|240nm|
|w|槽的横向宽度|120nm|
|P−w|一个周期内的凸台总宽度|120nm；图示左右各半个凸台，不能把两侧当两个完整凸台|
|w/P|几何槽宽占比|1/2；不是液体体积分数或全充液的孔隙率|
|h|凸台底面与基底的最小残隙|75nm|
|d|从凸台底面到槽顶的竖向高差，即槽深|100nm|
|H(x)|局部总间隙，浅区h、槽内h+d|75或175nm|
|H_ref|V_fluid/A_plan=h+(w/P)d，等宽时h+d/2|125nm；用于平均速度/导度换算，不是另一处真实壁间距|

z=0取基底上表面，凸台底面z=h，槽顶z=h+d；台阶竖壁仍属于无滑移固壁。流体在0<z<h贯通整个周期，上部槽区补充液体体积。图案沿x重复而沿y平移不变；数值L_y=240nm并取周期，是计算单胞长度，并非声明y方向存在另一个槽纹波长。

H_ref已在§2.2及补充S5定义，建议正文开头只引入H(x)，H_ref公式保留在§2.2，避免重复。以h替H_ref或以H_ref替局部H代入立方律都改变原问题，不是符号互换。基准数值仅用于解释，不把h75/d100写成全部主矩阵共同条件。

相邻计算域句“L_x=L_y=240nm，即恰好一个图案周期”建议收紧为“L_x=P=240nm，横槽方向包含一个图案周期；沿槽方向取L_y=240nm，x、y方向均采用周期边界”。这是描述精度修订，不改域尺寸或边界实现。

## 图文核对

实际查看现存Fig1 PNG并读取生成脚本：图(b)的h、d、w、P位置及图(c)K_parallel纵向/K_perp横向与正文相容，未发现方向画反。图(b)为x–z截面、y垂直纸面；图(c)为x–y俯视。建议以后改图时补清z厚度方向，并把“along groove”文字移到纵向箭头旁；当前文字紧邻横向箭头，存在误读风险。y轴箭头在当前成图中不完整，源码箭头端点P+44=284超出y显示上限268，可在改图时一并处理。本轮不执行改图或重新导出。

(a)为有液面/运动模具的工艺背景，(b)(c)为本论文固定全充液构型，图注应显式区分，避免误读成本文模拟了整个滴胶—下压—固化过程。已有图制作记录提及的真实接触角及前人符号对齐未经本轮核对，不作为本次文字依据。

### 图注候选

图1 压印工艺背景与全充液计算单胞。(a) 滴胶、下压填充及固化脱模的工艺示意；该动态过程不属于本文求解对象。(b) 单胞的x–z横截面，标示周期P、槽宽w、槽深d及凸台下残余间隙h，槽内总间隙为h+d。(c) x–y俯视图，槽沿y延伸，Kyy为沿槽导度，Kxx为横槽导度；面内边界周期匹配。本文计算采用固定几何、全充液单胞。

Figure 1. Imprint-process context and the fully filled computational unit cell. (a) Schematic stages of dispensing, pressing and filling, and curing and demolding; these dynamics are outside the present calculation. (b) Unit-cell cross-section in the x–z plane, showing period P, groove width w, groove depth d and residual gap h beneath the ribs. The total gap within a groove is h+d. (c) Plan view in the x–y plane. Grooves extend along y, with Kyy denoting along-groove and Kxx across-groove conductance. In-plane boundaries are periodically matched. The calculations use a fixed, fully filled unit cell.

## 开头两段中文候选

计算域取周期矩形直沟槽的一个单胞。以平面基底表面为z=0，z轴沿间隙厚度方向；图案沿x方向重复，沟槽沿y方向延伸。因此，沿槽导度记为K_parallel（对应Kyy），横槽导度记为K_perp（对应Kxx）。

图案周期P=240 nm，槽宽w=120 nm，凸台宽度P−w=120 nm，槽宽占比w/P=1/2。凸台底面距基底的残余间隙为h>0，槽深为d，槽顶距基底为h+d；相应局部总间隙H(x)在凸台下为h，在槽内为h+d。所有可用流体空间均由液体充满。每个算例内几何与间隙保持固定，不同算例通过改变h和d构成采样矩阵。

上述K_parallel/K_perp、Kyy/Kxx为候选文件中的纯文本符号，正式采用时按现有排版写为K_\parallel、K_\perp、K_{yy}和K_{xx}，不改变方向定义；本轮不新增编号公式。

## 英文对应候选

The computational domain is one unit cell of periodic straight rectangular grooves. The planar substrate surface is at z=0, with z directed across the gap thickness. The pattern repeats in x, and the grooves extend along y. Along-groove conductance is denoted by K_parallel, corresponding to Kyy; across-groove conductance is denoted by K_perp, corresponding to Kxx.

The pattern period is P=240 nm and the groove width is w=120 nm, giving a rib width P−w=120 nm and a groove-width fraction w/P=1/2. The rib underside is separated from the substrate by the residual gap h>0. The groove depth is d, so the groove roof is at height h+d above the substrate. The local gap H(x) is therefore h beneath a rib and h+d within a groove. Liquid fills the entire available fluid volume. Geometry and gap remain fixed within each case; h and d vary between cases to form the sampled matrix.

## 相邻采样文字

表1仍描述18种主比较几何，不包含h100新增几何。在h25时仅d25/50/100，缺d75/120；不得把h和d的最小/最大数值写成完整连续参数域或完整矩阵。其余h50/75/125各五种槽深，采样与网格间距分别说明。主/加密/新增结果角色沿用§1.3已审候选和§2.1数据表；本轮不改表1或后面的数值方法。

## 实际证据与核对范围

读取当前中英文稿开头几何与参考高度定义、补充S5/S6、图PNG/生成脚本/记录、当前D2源码参数/上壁函数/方向映射、h75/d100两方向历史result及P方向run_manifest.txt。原尝试位置steady/manifest.json不存在，后按目录检索读取实际run_manifest.txt，不能据不存在的JSON推断资料缺失。

当前源码定义槽区60≤x<180nm、上壁mesaGap或mesaGap+grooveDepth、P驱动y与T驱动x；历史基准结果保存h75、d100、w120和H_ref125nm，两方向一致。当前源码存在与历史字段相容，不等于历史二进制全部来源已绑定；当前源码与旧285f67a0二进制的来源关系不由这次文字核查关闭。不编译、不运行或重新验收几何。parameter_consistency.json只是参数/记录一致性检查，不产生geometry_PASS或参考资格。

输入哈希见source_manifest.json，状态及保护核对见verification.json。使用已读scientific-writing和academic-humanizer；程序性来源沿用§1.2第一段审读记录中Kassis等Scientific Agent Skills（2026，arXiv:2609.00065），不另添正文科学引文。未新增外部资料检索或向外发送稿件。

## 停点

本轮仅本目录与两共享状态更新。正式中英文引言及§2.1未合入候选，摘要既有合入保持；图/生成脚本/源码/结果/门槛不改。无新求解、编译、拟合、场处理、原轨迹接受、run_id、Gate或上传；S4原FAIL、reference_qualified=false、strict_error_bound_established=false、submission_ready=false保持，无新长算授权。

下一具体动作：审§2.1的采样矩阵与表1标题/计数，并核其与主比较及新增结果的范围关系；若用户要求采用本轮候选，再同步中英文及图注，图片修改单独据实际要求执行。

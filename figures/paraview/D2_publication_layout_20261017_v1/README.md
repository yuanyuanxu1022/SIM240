# SIM240 统一论文图包

日期：2026-10-17。范围：仅现有h75_d100_dx5基准P/T数据后处理，未运行、编译、轮询或停止仿真，不改变历史PASS/FAIL或冻结门槛。图像排版已完成；目标期刊适配和人工作者批准尚未完成。

## 打开哪里

- 先看 `PREVIEW.png`：四张图的快速拼览，仅供浏览，不代替单图投稿。
- **实际采用 `figures_v2/`**：四张单图，每张都有PNG、PDF和SVG。`figures/`是保留的首轮排版，图3图例一度靠近曲线；最终已移到坐标轴上方，不再遮挡数据。
- `CAPTIONS.md`：可复制的中英文图注与英文替代文字草稿；作者应核对后使用。
- `QA_RECORD.json`与`MANUAL_REVIEW.json`：自动检查、具体发现及目视核查分别记录，不能把自动报告当作期刊或物理验收证书。

| 图 | 文件名主干 | 用途 |
|---|---|---|
| 图1 | Fig1_velocity_XY | 同z=37.5 nm的沿槽/跨槽速度大小对照 |
| 图2 | Fig2_velocity_XZ | 同y=120 nm的沿槽/跨槽速度大小对照 |
| 图3 | Fig3_velocity_profiles | 沟槽中心与凸台下的取样位置、沿槽速度高度曲线 |
| 图4 | Fig4_dissipation_XZ | 同y=120 nm的跨槽耗散分布，灰色明确标出固体 |

图号为本图包临时编号；正文采用时按文章顺序调整。

## 统一了什么

使用同一DejaVu Sans字体层级、白底、nm空间坐标、明确的驱动方向、相同的固体灰色与名义几何轮廓。多面板用(a)/(b)标识。速度图共用Viridis、线性0–1.8×10⁻⁴ m/s，无逐图归一化；剖面曲线画的是u_y分量而非速度大小。耗散为原单位m²/s³，独立采用Viridis、线性0–32，不与速度共用数值范围，也不误写成W/m³。正交视角和定量空间轴避免透视或拉伸误导。

曲线以橙色实线和蓝色虚线双重编码。对两颜色的白底对比计算分别为3.867和5.185；两颜色的灰度亮度差只有约8.214（小于所用10的启发式阈值），因此保留线型及文字区分，不宣称只靠配色即可完整兼容灰度或色觉差异。

## 科学口径必须保留

这些数据来自D2基准 `h75_d100_dx5_P/T`，不是保存目录名称所暗示的D1液滴算例，也不是独立 `mu15_...` 目录。记录tau=1、dx=5 nm、dt=4.166666666666667×10⁻¹² s，对应BGK映射nu≈1×10⁻⁶ m²/s；若沿用模型rho=1000 kg/m³，相应mu为1 mPa·s，不能标为15 mPa·s。未修改旧场物性或按比例伪造新场。

图1虚线只是上方沟槽边缘的投影，z=37.5 nm两侧和中央均为液体。图2中P方向的+y进入纸面（⊗），不是平面内流线。本轮不绘制未经核查的回流/涡或凭空添加流线。

场图采用已经检查材料与名义几何的**5 nm点样本足迹**：每个原始/线性探针点值占据对应5 nm半格单元，分片常值，不平滑、不进行墙面速度/耗散外推或体积平均。名义壁面仍为z=0/75/175 nm。图4与用户GUI初稿使用同一原T场及相同0–32范围，但显示方式由POINTS+Threshold改为此样本足迹；原因是点材料Threshold会删掉混合边界单元，不能将它侵蚀后的边缘当真实墙面。此显示方式改变已明确披露，原GUI初稿PNG/pvsm未覆盖。

两份用户CSV各1001个插值取样，按有效mask、material约1（绝对容差10⁻⁶）及有限值筛选，保留沟槽971、凸台933点；其余保留为NaN间断，不补成零速度、不把插值样本当独立网格节点或统计重复。全部有效液体点重新在原P场取样，与CSV速度分量的最大绝对差为0。源CSV与`profile_validation.json`保留路径、数量、哈希和实际范围；`figures_v2/profile_*_plotted.csv`提供带选择标记的绘图数据表，不修改原CSV。

图片不能单独验证Jain/平板模型失效，未叠加理论对照，也不采用“+146%高估”的未在本图包重算断言。耗散热点不等于已闭合的能量收支或网格无关的角点耗散；本轮未进入此前暂缓的机制验收任务。

## 导出与检查

所有图采用同一字号体系，按各自图形比例设置工作尺寸：图1/3为180×95 mm、图2为180×85 mm、图4为140×100 mm。PNG为450 DPI工作导出，实际像素分别3188×1683、3188×1505、3188×1683和2480×1771；全不透明。目标期刊与最终版宽尚未锁定，这些是工作尺寸，不是期刊要求或合规保证。

PDF中的字体已检查嵌入，PNG及PDF重渲染已目视，SVG保留可编辑文字（显示仍依赖字体可用性）。场图嵌入栅格，轴、文字和曲线可编辑/矢量化，不宣称所有内容均是矢量。每个速度/耗散采样格中心在原生渲染和最终排版中与其共享LUT的8-bit RGB差均为0，原始场与既有证据及用户输入哈希未变。

实际8-bit Viridis表仍存在2个极小亮度反向阶差（最小约−2.8304×10⁻⁴），记录在QA中；不声称严格灰度单调或完整可访问性认证。`GRAYSCALE_PREVIEW.png`仅作灰度浏览，不代替色觉模拟或印刷转换检验。

## 证据与人工复核

`source_manifest.json`和`claims.csv`把图注句子绑定到数据、方法与图像记录；`CAPTIONS_AUDIT.md`保留机器可读标记和句子哈希，`source_locations.json`另存本地路径/哈希及机器检查状态。所有来源的**人工核实状态仍为unverified**，不捏造人工审核姓名或批准记录。AI/程序的来源、数值和版面检查另行记录。图形已生成，图注仍待负责的人工作者审核；`submission_ready=false`，也未准备作者、基金、伦理或AI披露的虚假声明。本地未发表来源在受控schema中按restricted保守处理，未向外部服务上传。schema结构检查已通过，但仍有本地来源无公共标识的警告，未为消除警告补造DOI或网址。

## 从哪里复现

保留原始场、用户CSV和先前图组目录。速度直接复用已核对的原生PNG和元数据，源位于 `../D2_h75_d100_dx5_PT_publication_20261017_v1/rendered_v4/`，不对旧PNG重新着色。耗散状态为 `rendered/dissipation_footprints.pvsm`；几何/轴/图例由下列脚本复现。.pvsm不包含原始场，必须保留其输入路径或重新定位。

```bash
/usr/bin/pvpython --force-offscreen-rendering figures/paraview/D2_publication_layout_20261017_v1/render_dissipation.py --output-dir /absolute/path/to/new-render-directory
```

后续使用`assemble.py`时会读取本包`rendered/`及`profile_validation.json`。现有包可直接重排至全新目录，脚本拒绝覆盖：

```bash
/home/dell/miniconda3/envs/sim240-analysis/bin/python figures/paraview/D2_publication_layout_20261017_v1/assemble.py --output-dir /absolute/path/to/new-figure-directory
```

`validate_profiles.py`用于原P场与用户CSV的独立取样核对，`check_outputs.py`用于颜色/哈希/元数据/PDF字体和预览。脚本及其输入、辅助技能代码哈希见各manifest。本机ParaView5.11/VTK9.2、Matplotlib3.11.1、Pillow12.2.0；不为复现另装环境或重新运行OpenLB。

## 软件与规范来源

本地使用paraview-publication、scientific-visualization、matplotlib、scientific-writing和pdf技能。已在2026-10-17核对以下软件规范来源的arXiv当前记录（修订于2026-09-02，未列期刊版本），并在本包引用；它不是流动物理或创新性证据：

Kassis, T., Agarwal, V., He, Y., Patel, D., & Brueckner, A. M. (2026). *Scientific Agent Skills: A Library of Procedural Knowledge for Research Agents*. [arXiv record](https://arxiv.org/abs/2609.00065), [DOI](https://doi.org/10.48550/arXiv.2609.00065).

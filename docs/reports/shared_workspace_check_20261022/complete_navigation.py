from pathlib import Path
import csv,json,shutil,hashlib
P=Path('/home/dell/yuanyuanxu/SIM240'); W=P.parent/'SIM240_代码图片数据_20261022'; O=P/'docs/reports/shared_workspace_check_20261022'
prev=list(csv.DictReader((P.parent/'第一篇论文_整理版_20261022/99_文件索引/全部文件对应表.csv').open(encoding='utf-8-sig')))
rows=list(csv.DictReader((W/'文件清单.csv').open(encoding='utf-8-sig')));M={r['原项目路径']:r['本文件夹路径'] for r in rows}
check=json.loads((O/'check_results.json').read_text());protocols=set(check['excluded_case_instructions']);added=[]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for r in prev:
 rel=r['原项目路径'];p=Path(rel);dest=None
 if rel in M:continue
 if rel in protocols:dest=Path('01_代码/00_技术说明')/p
 elif rel.startswith('CASE/') and p.suffix in {'.png','.pdf','.svg'}:dest=Path('02_图片/03_附加结果与历史验证')/Path(*p.parts[2:])
 elif rel.startswith('figures/paraview/') and p.suffix=='.json':dest=Path('03_数据/流场绘图数据')/Path(*p.parts[2:])
 elif rel in {'figures/paper/Fig1_caption_and_record.md','figures/paper/Fig4_caption_and_record.md','figures/paper/Fig7_Fig8_caption_and_record.md'}:dest=Path('02_图片/00_图片说明')/p.name
 elif rel=='docs/ex240/ex240_layout_report.md':dest=Path('04_几何')/p.name
 if dest is None:continue
 source=P/rel;target=W/dest
 assert sha(source)==r['SHA256'],rel
 target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target);assert sha(target)==r['SHA256']
 nr={'原项目路径':rel,'本文件夹路径':str(dest),'字节数':str(target.stat().st_size),'SHA256':r['SHA256']};rows.append(nr);M[rel]=str(dest);added.append(nr)
with (W/'文件清单.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
# Provide a normalized derived table with explicit pointers into the current folder.
pts=list(csv.DictReader((O/'36项汇总与原始值对应.csv').open(encoding='utf-8-sig')))
with (W/'03_数据/00_数据索引/36项主方向数据_模型对照.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(pts[0]));w.writeheader();w.writerows(pts)

def loc(rel):return M[rel]
figs=[('图01_工艺与单胞几何','figures/paper/make_fig1.py','docs/ex240/SIM-EC1XT240.OAS','几何由源码常量构造；不是实际压印过程计算结果'),('图02_输运系数与各向异性','figures/paper/make_fig4.py','CASE/D_series/D2_groove_error_map/results/summary.csv','另用d75_summary、h25_summary、d120_summary共四表'),('图03_误差随间隙变化','figures/paper/make_fig7_fig8.py','CASE/D_series/D2_groove_error_map/results/summary.csv','四表；E=(K_model/K_reference−1)×100%'),('图04_误差分布热图','figures/paper/make_fig7_fig8.py','CASE/D_series/D2_groove_error_map/results/summary.csv','四表；斜线格为未采样组合，不是丢失数据')]
maprows=[]
for name,script,data,note in figs:maprows.append({'图片':f'02_图片/01_主要图片/{name}.png','生成脚本':loc(script),'主要数据或几何':loc(data),'说明':note})
maprows.append({'图片':loc('CASE/D_series/D3_squeeze_error_propagation/results/Fig9_error_propagation.png'),'生成脚本':loc('CASE/D_series/D3_squeeze_error_propagation/make_fig9.py'),'主要数据或几何':loc('CASE/D_series/D3_squeeze_error_propagation/results/table1_load_and_peak.csv'),'说明':'附加误差传播分析；坐标约定需看该脚本，不能直接套主坐标；未在本轮重算'})
with (W/'图片_代码_数据对应表.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(maprows[0]));w.writeheader();w.writerows(maprows)
text='''# 工作路线与查看顺序

范围：固定几何、充分充液、单相沟槽中的方向性输运，以及简化模型相对数值参考的偏差。没有在本工作区证明液滴铺展、气液界面、实际压头运动或固化过程。

**当前注意：图01(c)横向箭头附近的英文along groove放错了方向。沿槽为y，横槽为x；看图时以坐标轴和K的方向定义为准。图像本轮未改，应修正后再正式共享。**

## 想回答什么

真实矩形沟槽的输运能力在两个方向有什么不同？把沟槽不同高度的局部平板关系组合起来，能否准确估计整体输运能力？偏差在什么间隙、深度和方向下明显？

## 为什么按这个顺序计算

1. 先用有解析解的平板流动检查数值实现，再查网格、周期复制和驱动力响应，明确数值证据范围。
2. 固定周期240nm、槽宽120nm，改变残余间隙h和槽深d，分别沿y、跨x驱动，提取深度积分输运系数K。
3. 把18种几何的36个主方向结果组成地图，另用8个加密、6个斜向和2个黏度对照作附加检查；这些共52项。历史基准和周期复制不计入52项。
4. 将数值K与局部立方律条纹组合比较，得到E=(K_model/K_reference−1)×100%。四张主要图片依次展示几何、方向性、偏差曲线和偏差分布。
5. 修正模型、压力/载荷误差传播在附加数据中单列。这部分是后处理模型分析，不能当作实际移动压头仿真。

## 请先看这几处

- [几何与方向](02_图片/01_主要图片/图01_工艺与单胞几何.png)：注意上面的方向标注问题；顶部工艺图只是背景示意。
- [输运系数与各向异性](02_图片/01_主要图片/图02_输运系数与各向异性.png)：同一h下比较d和两个方向。
- [误差曲线](02_图片/01_主要图片/图03_误差随间隙变化.png)、[误差热图](02_图片/01_主要图片/图04_误差分布热图.png)：范围仅限已采样组合，不能把局部趋势概括为全程单调。
- [36项主方向数据与模型对照](03_数据/00_数据索引/36项主方向数据_模型对照.csv)：每行含汇总来源、原始结果路径、K和模型偏差。原始文件未改。
- [52项运行位置](03_数据/00_数据索引/52项运行_当前位置.csv)：从run_id找到原始结果，同目录有参数、诊断、边界记录和退出码。4项加密使用共享批次日志，不是日志丢失。
- [图片—代码—数据对应表](图片_代码_数据对应表.csv)：从图片找生成脚本，再找输入。
- [技术说明](01_代码/00_技术说明/)：保留原版本的计算配置和验收规则；旧版本不自动成为当前执行授权。无需为查看数据运行计算。

## 量与方向

h为凸台下面的残余间隙，d为槽深，槽内局部高度为h+d；沿槽y对应K_yy，横槽x对应K_xx。这里K单位是m³。若换成以m²表示的体积平均迁移率/渗透率，需要除以明确的参考高度H_ref，不能混用单位。D2的K由μJ/(ρa)提取。

## 已有证据和仍有的限制

本次直接核对36项汇总和原始K完全一致；52项结果、诊断、参数清单、独立退出码和边界记录齐全；48项有独立日志，另4项由共享日志覆盖。诊断序列完整且数值有限，不等于本次重新进行了全部数值与物理验收。

历史三网格9项原始记录和指定周期复制18项记录已收集。历史1.25nm横槽质量FAIL仍保留；可计算GCI不把该运行改成PASS。可选流场图的来源记录中unique_run_id_verified=false，其历史代码版本绑定未闭合。不要把目录内的历史诊断图都当成已认可结果。

52项manifest都有二进制哈希，但指定manifest没有记录源码哈希、OpenLB提交、编译器和编译参数；复制当前源码不能补成历史来源证明。

代码里仍有本机绝对路径，分类后代码和数据分开放置；完整OpenLB依赖与运行环境未打包，未验证换电脑可编译运行。**当前适合查看和追溯，尚未达到独立运行的完整工作区要求。**

本目录尚未对外共享，没有老师可访问的链接。本轮未运行求解器、优化器或改动原始数值。
'''
(W/'00_工作路线与查看顺序.md').write_text(text,encoding='utf-8')
(W/'使用说明.txt').write_text('请先打开00_工作路线与查看顺序.md。\n01_代码：计算、分析、图片生成，以及原始技术说明。\n02_图片：主要图片、可选流场图、附加结果和历史诊断图。\n03_数据：原始结果、汇总、日志、场数据与索引。\n04_几何：几何文件和解析说明。\n图片_代码_数据对应表.csv：从图片追到脚本和输入。\n文件清单.csv：原位置、新位置、大小和SHA256。\n图01方向标注、脚本本机路径、环境依赖和历史来源缺口见工作路线说明；尚未对外共享。\n',encoding='utf-8')
(O/'本轮补齐清单.json').write_text(json.dumps({'added_source_files':added,'source_file_count_after':len(rows),'source_bytes_after':sum(int(r['字节数']) for r in rows),'generated':['00_工作路线与查看顺序.md','图片_代码_数据对应表.csv','03_数据/00_数据索引/36项主方向数据_模型对照.csv']},ensure_ascii=False,indent=2))
print(json.dumps({'补齐来源文件':len(added),'当前来源文件数':len(rows),'当前来源字节数':sum(int(r['字节数']) for r in rows)},ensure_ascii=False))

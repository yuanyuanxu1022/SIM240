from pathlib import Path
import json,csv,hashlib,os,shutil
ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).resolve().parent;REPO=ROOT.parent/'SIM240_code_figures_data_review_20261026';STAGE=OUT/'staging';P=Path('05_第一篇文章')
source=json.loads((OUT/'source_files.json').read_text());reuse=json.loads((OUT/'reused_sources.json').read_text());coverage=json.loads((OUT/'run_coverage.json').read_text())
def write(rel,text):
 p=STAGE/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text)
def link(target):return os.path.relpath(REPO/target,REPO/P)
write(P/'README.md','''# 第一篇文章：当前稿与配套材料

更新：2026-10-28。本目录是作者当前工作稿的私有共享入口，研究范围为固定几何、全充液、单相矩形沟槽的方向性输运。上传不等于投稿、最终理论冻结或参考精度放行。

建议老师按以下顺序阅读：

1. [当前中文正文（阅读版）](当前正文_阅读版.md)：已包括历史构建裁决后的三段限定文字；附录E仍待指定范围的最终理论审查。
2. [方法补充S1—S11（阅读版）](方法补充_阅读版.md)：附表S1—S5、方法来源和失败记录。
3. [四张主图与代码/输入索引](主图与代码数据.md)：当前正文四图，PNG/PDF/SVG与生成脚本均收入。
4. [运行证据覆盖](运行证据覆盖.md)：表S1的52项、表S3的18项、表S4的9项记录，共79个表内记录入口；这些记录范围不同，不等于79个独立几何。
5. [还差什么与下一步](材料覆盖与缺口.md)：将已完成、资料收尾及条件性数值补证分开。

原字节副本在`项目文件/`下保留主项目相对结构；[当前正文原件](项目文件/docs/reports/SIM240_中文稿_导师审阅版_20261022.md)与[方法补充原件](项目文件/docs/reports/SIM240_Supplementary_Methods_20261024/SUPPLEMENTARY_METHODS.md)保持来源字节和SHA。两个阅读版仅改文件链接及四图路径显示，没有改科学文字、公式、系数、表中结果或附录E。部分原件绝对路径不能直接在GitHub打开，阅读版已映射到本仓库；整个历史三网格目录以运行索引逐项访问，未伪装成原本机目录可用。

[文件映射.csv](文件映射.csv)列出本次原字节副本和复用的既有代码/数据，SHA256可逐项核对；既有文件继续保留在仓库01—04目录，不重复上传大型数据。部分报告引用的本机全文、页图和历史before快照未分享，不能据这些报告的文件名认为它们已经收入；来源元数据与实际文件覆盖分开记录。

## 版本使用

- 以本目录当前中文正文和补充材料为准。
- [英文整合工作稿（2026-10-19历史版）](项目文件/docs/reports/SIM240_EJMB_英文整合工作稿_20261019.md)是现存英文材料，**尚未同步最新限定、来源披露和理论附录修订，不能当作当前投稿英文稿**。
- `figures/paper/Fig_fRe*`等文件为历史附加材料，未列入当前四张主图，不新增其物理解释。
- `Historical_build_binding_recovery_20261028`的过强判断已由[后续裁决](项目文件/docs/reports/Historical_build_adjudication_20261028/REPORT.md)覆盖；旧文件保留作历史证据。Current_gap_inventory中的M1缺原文等是旧盘点快照，当前接收稿状态见本目录最新缺口页。

本次不含第三方论文原件/全文提取/页面图、账号或凭据、编译产物、第二篇及真实N8原始场。既有程序与数据可追溯不等于四组完整历史构建来源已恢复，也不等于所有场文件、所有历史档案或全部连续精度证明齐备。当前仓库为私有，有权限者可访问；不承诺匿名审稿人或公众可访问，最终数据声明/持久标识仍需作者确定。
''')
write(P/'材料覆盖与缺口.md','''# 第一篇文章：已有什么、还缺什么、下一步

日期：2026-10-28。依据当前正文、S1—S11、前轮Astra历史构建裁决及最新文字同步记录作内部盘点；本轮没有重新裁决公式、建立严格界或启动仿真。

## 本次共享覆盖

当前中文正文、方法补充与表S1—S5、四主图的三种格式和生成脚本、D2/D3现存源码/分析脚本/汇总、选择的方法与来源核对记录已收入本目录。79个表内运行记录的结果与可用清单/退出/日志/诊断文件通过索引连接至本次或原仓库文件。英文仅有历史工作稿。私有共享与最终投稿材料完整性不是同一件事。

## 优先收尾，不需要启动新求解

|事项|当前状态|下一步|
|---|---|---|
|作者/导师最终采用与理论终审|三段限定已按作者范围同步；附录E及公式/结论最终理论冻结未执行|保持现有限定稿，明确终审范围后使用GPT-6 Astra｜High；最终科学责任与采用由作者/导师承担|
|作者资料与声明|当前正文附录C仍待作者、单位、通讯信息、基金/致谢、利益冲突、CRediT及实际AI使用说明|作者按真实情况提供；不代填“无冲突”等结论|
|英文与排版|四张主图已有；当前正文尚未嵌入最终版式；英文为2026-10-19旧稿|科学采用后同步英文、嵌入现有图并核编号/字体/单位；按选定目标期刊的实际要求整理，不自动重画或重算|
|最终数据/代码可用性声明|本轮增加了全文与配套材料，原正文附录C记的是旧固定快照f11c0f2|最终提交时引用实际采用的固定版本和访问方式；当前私有分享不是公开数据发布，也没有自动产生DOI。正文旧日期快照说明保留历史含义，不能当成本轮覆盖说明|
|文献[6]版本终校|完整接收稿的指定条件已核，另有30页作者格式稿；不是缺原文|最终排版版与接收稿尚未逐页对应；不要重复要求下载已取得的Bouzidi/Guo/Celik原文，不把作者格式稿的日期当作正式版本关系|
|四组历史构建来源|22/22/6/2组完整关联仍OPEN；现存匹配28只确认程序身份，来源限制已写入稿件|若能取得当时源码/依赖/编译记录，按合同接收；无法恢复的项继续披露，不按mtime补写或认定已全部恢复|

建议顺序：先由作者/导师确认限定贡献和指定范围理论终审，同时补作者声明；再同步英文和最终版式；最后核固定共享版本、可访问性和目标期刊提交资料。当前资料可以支持整篇内部审阅，尚不能宣称已完成投稿准备。

## 只有升级主张时才另立数值补证范围

- 连续解定量精度、全参数图统一误差、新几何独立预测、确定的物理机制份额等强主张，仍缺与之匹配的合格参考及误差证据。
- 历史最细横槽仍PASS=false/exit3，条件GCI不赋予合格参考资格；双网格敏感性不等于全图误差界。
- 主图标定与扩展分属两个程序SHA，潜在版本效应不能由现存数据单独识别；这不证明已有结果已算错，同程序P/T也不保证误差抵消。
- 本轮不要求自动重跑全部样点，不执行旧报告建议的单点重跑；单点一致也不能排除全图差异。若确需补证，先定保留主张与冻结合同，再另行授权。
- 后续G4/N8验证是独立工作流；真实N8提取仍未授权，不能把它或剩余全部算例机械列为当前限定稿的必做项。

当前沿用：reference_qualified=false、strict_error_bound_established=false、submission_ready=false，预测HOLD。新增计算关闭，无新run_id或启动命令。本轮上传与文件哈希核对不改变历史PASS/FAIL。

## 阅读版路径限制

补充材料中指向本机整个历史三网格目录的链接，已转到本说明页。实际9条历史结果请在[运行证据覆盖](运行证据覆盖.md)中按表S4查找。原件其余绝对路径保留出处，阅读版已映射到可共享文件；不保证所有历史报告中的本机链接和第三方全文链接在仓库中可用。
''')
figrows=['# 四张主图及对应代码/数据\n\n以当前中文正文新编号为准。以下是已有文件的原字节副本，本轮未生成图件或计算新结果。\n\n|正文编号|文件|脚本|说明|\n|---|---|---|---|\n']
for num,stem,script,desc in [(1,'Fig1_device_and_unitcell','make_fig1.py','工艺/单胞示意，不是动态压印运行结果'),(2,'Fig4_K_and_anisotropy','make_fig4.py','主地图K与各向异性'),(3,'Fig7_error_vs_gap','make_fig7_fig8.py','局部立方律偏差随间隙变化'),(4,'Fig8_error_map','make_fig7_fig8.py','偏差热图，未算格保持缺失')]:
 base=P/'项目文件/figures/paper';files=' / '.join('['+ext.upper()+']('+link(str(base/(stem+'.'+ext)))+')' for ext in ['pdf','png','svg']);figrows.append(f'|图{num}|{files}|[{script}]({link(str(base/script))})|{desc}|\n')
figrows.append('\n[全部文件映射](文件映射.csv)和[运行证据覆盖](运行证据覆盖.md)给出脚本输入对应。脚本保留原本机路径和依赖，本次未在新设备执行复现；当前源码也不能倒推所有历史二进制来源。\n')
write(P/'主图与代码数据.md',''.join(figrows))
rows=['# 表内运行记录的共享覆盖\n\n共79个表内记录入口：S1=52、S3=18、S4=9；不是79个独立几何或统一验收。PASS是保存状态，退出码也不代表整体科学验证。\n\n|来源表/行|运行/算例|记录PASS / exit|实际共享文件|\n|---|---|---|---|\n']
for r in coverage:
 parts=[]
 for a in r['artifacts']:
  label=Path(a['source']).name;parts.append('['+label+']('+link(a['target'])+')')
 rows.append('|'+r['table']+':'+str(r['table_line'])+'|'+str(r['run_id'])+'|'+str(r['recorded_PASS'])+' / '+str(r['independent_exit_code'])+'|'+' · '.join(parts)+'|\n')
write(P/'运行证据覆盖.md',''.join(rows))
with (STAGE/P/'文件映射.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.writer(f);w.writerow(['来源路径','仓库路径','字节数','SHA256','本轮方式'])
 for r in source:w.writerow([r['source'],r['target'],r['bytes'],r['sha256'],'新增原字节副本'])
 for r in reuse:w.writerow([r['source'],r['target'],r['bytes'],r['sha256'],'复用既有文件并核源SHA'])
# Global source inventory retains all existing rows and appends only controlled new source targets.
with (REPO/'文件清单.csv').open(encoding='utf-8-sig') as f:old=list(csv.DictReader(f))
new=list(old)
for r in source:new.append({'原项目路径':r['source_relative'],'本文件夹路径':r['target'],'字节数':str(r['bytes']),'SHA256':r['sha256']})
with (STAGE/'文件清单.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,fieldnames=['原项目路径','本文件夹路径','字节数','SHA256']);w.writeheader();w.writerows(new)
assert len(new)==len(old)+len(source)
count=len(new)
for name in ['README.md','00_当前进度.md','清单与核验入口.md','00_工作路线与查看顺序.md']:
 oldtext=(REPO/name).read_text()
 addition=f'**2026-10-28 第一篇完整材料入口：[当前正文、补充、图件与数据索引](05_第一篇文章/README.md)。** 本轮新增{len(source)}份原字节副本，复用并核对{len(reuse)}份既有来源；总来源清单现为{count}行。两个阅读版只适配链接，当前中文稿已含三段历史构建限定。英文旧稿未同步、附录E未最终冻结，四组完整构建来源与连续精度仍未闭合；[下一步与缺口](05_第一篇文章/材料覆盖与缺口.md)为当前入口。旧日期段按历史范围阅读，新增计算继续关闭。\n\n'
 if name=='README.md':oldtext=oldtext.replace('未收集第二篇液滴与气液界面研究算例，不含正文草稿。','未收集第二篇液滴与气液界面研究算例；第一篇当前正文与配套材料见05_第一篇文章。')
 first,sep,rest=oldtext.partition('\n');write(Path(name),first+'\n\n'+addition+rest.lstrip('\n'))
meta={'date':'2026-10-28','status':'PREPARED_FOR_AUTHORIZED_PRIVATE_UPLOAD','repo':'yuanyuanxu1022/SIM240_code_figures_data','branch':'main','private_verified':True,'source_copies':len(source),'source_bytes':sum(x['bytes'] for x in source),'reused_sources':len(reuse),'old_inventory_rows':len(old),'new_inventory_rows':count,'run_table_records':len(coverage),'reading_copy_scope':'Links and figure-file labels only; exact original copies also included','exclusions':['third-party PDFs, extracted fulltexts and page renders','credentials and account materials','build/ELF/object outputs','second paper','real N8 raw fields'],'solver_or_refit_run':False,'theory_final_freeze':False,'submission_ready':False}
write(Path('检查记录/第一篇完整材料共享_20261028.json'),json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
(OUT/'preparation.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(meta,ensure_ascii=False,indent=2))

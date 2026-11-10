from pathlib import Path
import subprocess,json
root=Path('/home/dell/yuanyuanxu/SIM240'); r=root/'docs/reports/Paper_bilingual_layout_20261028'; tmp=root/'tmp/pdfs/paper_bilingual_20261028'; out=root/'output/pdf'; tmp.mkdir(parents=True,exist_ok=True); out.mkdir(exist_ok=True)
items=[('SIM240_First_Paper_ZH_20261028',r/'CHINESE_READING.md','zh','作者审阅版；限定于既有5 nm离散参考与V2回顾性评价。作者资料及最终科学采用待完善。'),('SIM240_First_Paper_EN_20261028',root/'docs/reports/SIM240_First_Paper_English_20261028.md','en','Author-review draft. Quantitative comparisons use saved 5 nm discrete references; V2 is retrospective. Author details and final scientific approval remain pending.'),('SIM240_Supplement_ZH_20261028',root/'docs/reports/SIM240_Supplementary_Methods_20261024/SUPPLEMENTARY_METHODS.md','zh','补充材料审阅版；保留历史失败与来源限制。数据表S1–S5另存原始CSV。'),('SIM240_Supplement_EN_20261028',root/'docs/reports/SIM240_Supplementary_Methods_20261024/SUPPLEMENTARY_METHODS_EN_20261028.md','en','Supplementary author-review draft. Historical failures and provenance limits are retained. Complete Tables S1–S5 are supplied as original CSV files.')]
logs=[]
for name,p,lang,note in items:
 cmd=['/opt/quarto/bin/tools/x86_64/pandoc',str(p),'-f','markdown-implicit_figures','-t','typst','--standalone','--lua-filter',str(r/'layout.lua'),'--template',str(r/'paper_template.typ'),'-M','lang=en','-V','doc-lang='+lang,'-M','review-note='+note,'-o',str(tmp/(name+'.typ'))]
 proc=subprocess.run(cmd,capture_output=True,text=True); (r/(name+'_pandoc.log')).write_text(proc.stderr); assert proc.returncode==0,proc.stderr
 assert 'Could not convert TeX' not in proc.stderr,proc.stderr
 cmd2=['/opt/quarto/bin/tools/x86_64/typst','compile','--root',str(root),str(tmp/(name+'.typ')),str(out/(name+'.pdf'))]
 q=subprocess.run(cmd2,capture_output=True,text=True);(r/(name+'_typst.log')).write_text(q.stderr); print(name,q.returncode,q.stderr[:2000]); assert q.returncode==0
 logs.append({'name':name,'source':str(p),'output':str(out/(name+'.pdf')),'pandoc_exit':proc.returncode,'typst_exit':q.returncode})
(r/'build_results.json').write_text(json.dumps(logs,ensure_ascii=False,indent=2)+'\n')

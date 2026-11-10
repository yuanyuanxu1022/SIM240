from pathlib import Path
import zipfile,xml.etree.ElementTree as E,html,base64,posixpath,json
from weasyprint import HTML
B=Path('/home/dell/yuanyuanxu/SIM240/docs/reports/PAPER1_导师汇报_20261107_六幕版')
ppt=B/'PAPER1_导师汇报_20261107_六幕故事版.pptx'
N={'p':'http://schemas.openxmlformats.org/presentationml/2006/main','a':'http://schemas.openxmlformats.org/drawingml/2006/main','r':'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}
def esc(s):return html.escape(s or '')
def px(v):return float(v)/9525
with zipfile.ZipFile(ppt) as z:D={n:z.read(n) for n in z.namelist()}
pr=E.fromstring(D['ppt/presentation.xml']);sz=pr.find('p:sldSz',N);W,H=px(sz.get('cx')),px(sz.get('cy'))
rels={n.get('Id'):n.get('Target') for n in E.fromstring(D['ppt/_rels/presentation.xml.rels'])}
order=[int(posixpath.basename(rels[n.get('{'+N['r']+'}id')])[5:-4]) for n in pr.find('p:sldIdLst',N)]
def color(e,default='transparent'):
 if e is None:return default
 c=e.find('a:srgbClr',N)
 return '#'+c.get('val') if c is not None else default

def textbody(tx,tc=False):
 out=[]
 for p in tx.findall('a:p',N):
  pp=p.find('a:pPr',N);st='margin:0;padding:0;'
  if pp is not None:
   st+='text-align:'+{'l':'left','r':'right','ctr':'center','just':'justify'}.get(pp.get('algn'),'left')+';'
   sp=pp.find('a:lnSpc/a:spcPct',N)
   st+='line-height:'+str(float(sp.get('val'))/100000 if sp is not None else 1.2)+';'
   for tag,css in [('spcBef','margin-top'),('spcAft','margin-bottom')]:
    n=pp.find('a:'+tag+'/a:spcPts',N)
    if n is not None:st+=css+':'+str(float(n.get('val'))/100)+'pt;'
  content=[]
  for r in p:
   if r.tag=='{'+N['a']+'}br':content.append('<br>');continue
   if r.tag not in ['{'+N['a']+'}r','{'+N['a']+'}fld']:continue
   rp=r.find('a:rPr',N);ts=r.find('a:t',N)
   size=float(rp.get('sz','1400'))/100 if rp is not None else 14
   css=f'font-size:{size}pt;'
   if rp is not None:
    css+='color:'+color(rp.find('a:solidFill',N),'#1A2230')+';'
    if rp.get('b')=='1':css+='font-weight:700;'
    if rp.get('i')=='1':css+='font-style:italic;'
    bs=int(rp.get('baseline','0'))
    if bs:css+='vertical-align:'+('super' if bs>0 else 'sub')+';'
   content.append('<span style="'+css+'">'+esc(ts.text if ts is not None else '')+'</span>')
  out.append('<p style="'+st+'">'+(''.join(content) or '&nbsp;')+'</p>')
 return ''.join(out)
def geometry(s):
 xf=s.find('p:spPr/a:xfrm',N)
 if xf is None:xf=s.find('p:xfrm',N)
 if xf is None:return None
 o=xf.find('a:off',N);e=xf.find('a:ext',N)
 return [px(o.get('x')),px(o.get('y')),px(e.get('cx')),px(e.get('cy'))]
allpages=[];sizes=[]
for pos,i in enumerate(order,1):
 root=E.fromstring(D[f'ppt/slides/slide{i}.xml']);sr={n.get('Id'):n.get('Target') for n in E.fromstring(D[f'ppt/slides/_rels/slide{i}.xml.rels'])};objects=[]
 for s in root.find('p:cSld/p:spTree',N):
  g=geometry(s)
  if g is None:continue
  x,y,w,h=g;css=f'left:{x}px;top:{y}px;width:{w}px;height:{h}px;'
  sid=s.find('.//p:cNvPr',N);sid=sid.get('id') if sid is not None else '0'
  if s.tag=='{'+N['p']+'}pic':
   bl=s.find('p:blipFill/a:blip',N);rid=bl.get('{'+N['r']+'}embed');path=posixpath.normpath('ppt/slides/'+sr[rid]);ext=path.rsplit('.',1)[-1];mime='image/'+('jpeg' if ext in ['jpeg','jpg'] else ext)
   objects.append(f'<img class="obj" data-shape="{sid}" style="{css}" src="data:{mime};base64,{base64.b64encode(D[path]).decode()}"/>');continue
  tbl=s.find('.//a:tbl',N)
  if tbl is not None:
   cols=tbl.find('a:tblGrid',N);colhtml=''.join(f'<col style="width:{px(c.get("w"))}px">' for c in cols);rows=[]
   for rr in tbl.findall('a:tr',N):
    cells=[]
    for tc in rr.findall('a:tc',N):
     prop=tc.find('a:tcPr',N);pad=[px(prop.get(a,str(v))) if prop is not None else px(v) for a,v in [('marT',45720),('marR',91440),('marB',45720),('marL',91440)]]
     st='background:'+color(prop.find('a:solidFill',N) if prop is not None else None,'#FFFFFF')+';padding:'+' '.join(str(v)+'px' for v in pad)+';vertical-align:middle;'
     cells.append('<td style="'+st+'">'+textbody(tc.find('a:txBody',N),True)+'</td>')
    rows.append(f'<tr style="height:{px(rr.get("h"))}px">'+''.join(cells)+'</tr>')
   objects.append(f'<table class="obj" data-shape="{sid}" style="{css}"><colgroup>{colhtml}</colgroup>'+''.join(rows)+'</table>');continue
  prop=s.find('p:spPr',N)
  if prop is not None:
   css+='background:'+color(prop.find('a:solidFill',N))+';'
   ln=prop.find('a:ln',N)
   if ln is not None:
    co=color(ln.find('a:solidFill',N))
    if co!='transparent':css+=f'border:{max(.5,float(ln.get("w","9525"))/9525)}px solid {co};'
  tx=s.find('p:txBody',N);inner=''
  if tx is not None:
   bp=tx.find('a:bodyPr',N);pad=[px(bp.get(a,str(v))) if bp is not None else px(v) for a,v in [('tIns',45720),('rIns',91440),('bIns',45720),('lIns',91440)]]
   ins='padding:'+' '.join(str(v)+'px' for v in pad)+';'
   if bp is not None and bp.get('anchor')=='ctr':ins+='display:flex;flex-direction:column;justify-content:center;height:100%;'
   inner='<div class="tx" style="'+ins+'">'+textbody(tx)+'</div>'
  objects.append(f'<div class="obj" data-shape="{sid}" style="{css}">{inner}</div>')
 allpages.append('<section class="slide" data-slide="'+str(pos)+'">'+''.join(objects)+'</section>')
style=f'''@font-face{{font-family:NotoCJK;src:url(file:///usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc)}}
@font-face{{font-family:NotoCJK;src:url(file:///usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc);font-weight:700}}
@page{{size:{W}px {H}px;margin:0}}*{{box-sizing:border-box}}html,body{{margin:0;padding:0;background:white;font-family:NotoCJK,sans-serif}}.slide{{width:{W}px;height:{H}px;position:relative;background:white;break-after:page;overflow:hidden}}.slide:last-child{{break-after:auto}}.obj{{position:absolute;margin:0;overflow:visible}}.tx{{width:100%;height:100%;overflow:visible}}p{{overflow-wrap:normal;word-break:normal}}table{{table-layout:fixed;border-collapse:collapse}}td{{border:.5px solid #D6DCE5;overflow:visible}}'''
htmlstr='<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>第一篇导师汇报 下午修订版</title><style>'+style+'</style><body>'+''.join(allpages)+'</body></html>'
(B/'投屏版.html').write_text(htmlstr,encoding='utf8')
doc=HTML(string=htmlstr,base_url=str(B)).render()
issues=[]
# PDF renderer positions are inspected as an additional layout check.
for pn,page in enumerate(doc.pages,1):
 for b in page._page_box.descendants():
  if type(b).__name__=='LineBox' and b.element is not None:
   if b.position_x+b.width>W+1 or b.position_y+b.height>H+1:issues.append({'page':pn,'kind':'text_outside_page','x':b.position_x,'y':b.position_y,'w':b.width,'h':b.height})
(B/'pdf_render_checks.json').write_text(json.dumps({'pages':len(doc.pages),'width_px':W,'height_px':H,'issues':issues,'renderer':'WeasyPrint from editable OOXML; not native Office rendering'},ensure_ascii=False,indent=2))
if len(doc.pages)!=len(order):raise ValueError(('PDF page count',len(doc.pages)))
doc.write_pdf(B/'PAPER1_导师汇报_20261107_六幕故事版.pdf')
print('PDF pages:',len(doc.pages),'page overflow:',len(issues))

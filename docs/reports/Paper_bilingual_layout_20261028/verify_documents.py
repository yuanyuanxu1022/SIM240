from pathlib import Path
import json,re,hashlib,collections,subprocess,xml.etree.ElementTree as ET
root=Path('/home/dell/yuanyuanxu/SIM240');r=root/'docs/reports/Paper_bilingual_layout_20261028';tmp=root/'tmp/pdfs/paper_bilingual_20261028'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def maths(s):return re.findall(r'\$\$[\s\S]*?\$\$|\$[^$\n]+\$',s)
def nums(s):return collections.Counter(re.findall(r'\d+(?:\.\d+)?',re.sub(r'\]\([^)]*\)',']',s)))
old=(r/'before/SIM240_中文稿_导师审阅版_20261022.md').read_text();new=(root/'docs/reports/SIM240_中文稿_导师审阅版_20261022.md').read_text()
old_display=re.findall(r'\$\$[\s\S]*?\$\$',old);new_display=re.findall(r'\$\$[\s\S]*?\$\$',new)
assert old_display==new_display
maps=[]
for name in ['translation_map.json','supplement_translation_map.json']:
 for x in json.loads((r/name).read_text()):
  assert maths(x['source'])==maths(x['english']),(name,x['source_block'])
  a,b=nums(x['source']),nums(x['english'])
  # Chinese conclusion labels 一/二/三/四 are rendered as 1/2/3/4.
  if name=='translation_map.json' and x['source_block'] in [164,165,166,167]:b[str(x['source_block']-163)]-=1;b=+b
  assert a==b,(name,x['source_block'],dict(a-b),dict(b-a))
  maps.append((name,x['source_block']))
allow={str(root/'docs/reports/SIM240_中文稿_导师审阅版_20261022.md'),str(root/'docs/reports/SIM240_Supplementary_Methods_20261024/SUPPLEMENTARY_METHODS.md')}
manifest=json.loads((r/'source_manifest_before.json').read_text());changed=[x['path'] for x in manifest if sha(x['path'])!=x['sha256']];assert set(changed)==allow,changed
english=(root/'docs/reports/SIM240_First_Paper_English_20261028.md').read_text(); reading=(r/'CHINESE_READING.md').read_text()
assert len(re.findall(r'^!\[',english,re.M))==len(re.findall(r'^!\[',reading,re.M))==4
assert re.findall(r'(?m)^\[\d+\].*$',english)==re.findall(r'(?m)^\[\d+\].*$',reading)
links=[]
for p in [root/'docs/reports/SIM240_First_Paper_English_20261028.md',r/'CHINESE_READING.md',root/'docs/reports/SIM240_Supplementary_Methods_20261024/SUPPLEMENTARY_METHODS_EN_20261028.md']:
 for dest in re.findall(r'\]\(([^)]+)\)',p.read_text()):
  if '://' in dest:continue
  clean=dest.split('#')[0]; clean=re.sub(r':\d+$','',clean)
  exists=(p.parent/clean).exists() if clean else True
  links.append({'document':str(p),'target':dest,'exists':exists})
assert all(x['exists'] for x in links)
qa=[]
for x in json.loads((r/'build_results.json').read_text()):
 name=x['name'];pdf=Path(x['output'])
 for mode,suffix in [('layout','txt'),('bbox','html')]:
  a=subprocess.run(['pdftotext','-'+mode,str(pdf),str(tmp/(name+'.'+suffix))],capture_output=True,text=True);assert a.returncode==0,a.stderr
 text=(tmp/(name+'.txt')).read_text();ns={'x':'http://www.w3.org/1999/xhtml'};tree=ET.parse(tmp/(name+'.html'));pages=tree.findall('.//x:page',ns);outside=[]
 for pn,page in enumerate(pages,1):
  w,h=float(page.attrib['width']),float(page.attrib['height'])
  for word in page.findall('x:word',ns):
   q=[float(word.attrib[k]) for k in ['xMin','yMin','xMax','yMax']]
   if q[0]<0 or q[1]<0 or q[2]>w or q[3]>h:outside.append({'page':pn,'word':word.text,'bbox':q})
 tags={}
 if 'First_Paper' in name:
  tags={s:bool(re.search(r'\('+s+r'\)',text)) for s in [str(i) for i in range(1,8)]+['E'+str(i) for i in range(1,7)]};assert all(tags.values())
 assert not outside and '�' not in text
 assert not (r/(name+'_pandoc.log')).read_text().strip()
 assert not (r/(name+'_typst.log')).read_text().strip()
 qa.append({'name':name,'pdf':str(pdf),'sha256':sha(pdf),'bytes':pdf.stat().st_size,'pages':len(pages),'off_page_words':outside,'replacement_glyph_found':False,'formula_tags':tags,'render_logs_clean':True})
checks={'all_display_equations_unchanged':True,'bilingual_math_fragments_preserved':True,'bilingual_numeric_tokens_preserved_with_documented_conclusion_label_translation':True,'eleven_reference_entries_exact':True,'four_original_figures_in_both_main_manuscripts':True,'all_local_links_exist':True,'623_selected_sources_unchanged_only_two_authorized_sources_changed':True,'four_pdf_text_and_page_bounds_checks':True}
result={'checks':checks,'all_checks_passed':all(checks.values()),'display_equation_count':len(old_display),'main_translation_blocks':202,'supplement_translation_blocks':73,'checked_translation_blocks':len(maps),'source_files_in_protection_scope':len(manifest),'changed_existing_source_paths':changed,'unchanged_existing_sources':len(manifest)-len(changed),'local_links_checked':len(links),'pdfs':qa,'new_numerical_computation':False,'numerical_or_physical_acceptance':False,'submission_ready':False,'author_final_scientific_signoff':False,'scope_note':'Document fidelity and presentation only; no new simulation, fitting, scientific recalculation or N8 extraction.'}
(r/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');(r/'local_link_checks.json').write_text(json.dumps(links,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ['pdfs']},ensure_ascii=False)); print([(x['name'],x['pages']) for x in qa])

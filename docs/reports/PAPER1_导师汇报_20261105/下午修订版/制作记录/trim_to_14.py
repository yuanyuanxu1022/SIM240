"""Keep only pages 1-14 of the afternoon deck (delete pages 15-22).

Backs up the 22-page original first; keeps native editable OOXML, drops the
now-unused slide/notes parts, and renumbers every page marker to N / 14.
"""
from pathlib import Path
import xml.etree.ElementTree as E, zipfile, re, shutil, json

B = Path(__file__).resolve().parent.parent
BK = B / '制作记录/删15页起前_22页备份'
BK.mkdir(exist_ok=True)
FILES = ['PAPER1_导师汇报_20261105_下午修订版.pptx',
         'PAPER1_导师汇报_20261105_下午修订版.pdf',
         '下午汇报逐页讲稿.md', '先读这里_下午汇报.md']
for f in FILES:
    if not (BK / f).exists():
        shutil.copy2(B / f, BK / f)

NS = {'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
      'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
      'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}
for k, v in NS.items():
    E.register_namespace(k, v)
R = 'http://schemas.openxmlformats.org/package/2006/relationships'
CT = 'http://schemas.openxmlformats.org/package/2006/content-types'
xml = lambda r: E.tostring(r, encoding='utf-8', xml_declaration=True)

with zipfile.ZipFile(BK / FILES[0]) as z:
    D = {n: z.read(n) for n in z.namelist()}

pr = E.fromstring(D['ppt/presentation.xml'])
lst = pr.find('p:sldIdLst', NS)
rels = E.fromstring(D['ppt/_rels/presentation.xml.rels'])
lookup = {n.get('Id'): n.get('Target') for n in rels}
order = [int(re.search(r'slide(\d+)\.xml', lookup[n.get('{' + NS['r'] + '}id')]).group(1))
         for n in lst]
assert len(order) == 22, order
keep, drop = order[:14], order[14:]
print('keep:', keep)
print('drop:', drop)

# 1) remove sldId entries for dropped pages
for n in list(lst):
    sid = int(re.search(r'slide(\d+)\.xml', lookup[n.get('{' + NS['r'] + '}id')]).group(1))
    if sid in drop:
        lst.remove(n)

# 2) find notesSlide parts referenced ONLY by dropped slides, then drop relationship targets
drop_notes = set()
for i in drop:
    key = f'ppt/slides/_rels/slide{i}.xml.rels'
    if key not in D:
        continue
    for n in E.fromstring(D[key]):
        m = re.search(r'notesSlides/notesSlide(\d+)\.xml', n.get('Target', ''))
        if m:
            drop_notes.add(int(m.group(1)))
keep_notes = set()
for i in keep:
    key = f'ppt/slides/_rels/slide{i}.xml.rels'
    if key in D:
        for n in E.fromstring(D[key]):
            m = re.search(r'notesSlides/notesSlide(\d+)\.xml', n.get('Target', ''))
            if m:
                keep_notes.add(int(m.group(1)))
assert not (drop_notes & keep_notes), ('shared notes', drop_notes & keep_notes)

for n in list(rels):
    t = n.get('Target', '')
    m = re.search(r'slides/slide(\d+)\.xml', t)
    if m and int(m.group(1)) in drop:
        rels.remove(n)
E.register_namespace('', R)
D['ppt/_rels/presentation.xml.rels'] = xml(rels)

# 3) remove content-type overrides for dropped parts
ct = E.fromstring(D['[Content_Types].xml'])
for ov in list(ct):
    m = re.search(r'/ppt/(?:slides/slide|notesSlides/notesSlide)(\d+)\.xml$', ov.get('PartName', ''))
    if m and int(m.group(1)) in (set(drop) | drop_notes):
        ct.remove(ov)
E.register_namespace('', CT)
D['[Content_Types].xml'] = xml(ct)

# 4) delete the now-unused parts
for i in drop:
    for key in (f'ppt/slides/slide{i}.xml', f'ppt/slides/_rels/slide{i}.xml.rels'):
        D.pop(key, None)
for i in drop_notes:
    for key in (f'ppt/notesSlides/notesSlide{i}.xml',
                f'ppt/notesSlides/_rels/notesSlide{i}.xml.rels'):
        D.pop(key, None)

# 5) renumber page markers on kept slides, reserialize
for pos, i in enumerate(keep, 1):
    root = E.fromstring(D[f'ppt/slides/slide{i}.xml'])
    for t in root.findall('.//a:t', NS):
        if re.fullmatch(r'\d+ / 22', t.text or ''):
            t.text = f'{pos} / 14'
    D[f'ppt/slides/slide{i}.xml'] = xml(root)
E.register_namespace('', CT)
D['ppt/presentation.xml'] = xml(pr)

# 6) app.xml counts and title list
ep = 'http://schemas.openxmlformats.org/officeDocument/2006/extended-properties'
vt = 'http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes'
app = E.fromstring(D['docProps/app.xml'])
app.find('{' + ep + '}Slides').text = '14'
hp = app.find('{' + ep + '}HeadingPairs/{' + vt + '}vector')
if hp is not None:
    for j, v in enumerate(list(hp)[:-1]):
        if any(n.text == 'Slides' for n in v.iter()):
            for n in list(hp)[j + 1].iter():
                if n.tag == '{' + vt + '}i4':
                    n.text = '14'
top = app.find('{' + ep + '}TitlesOfParts/{' + vt + '}vector')
if top is not None:
    existing = [(n.text or '') for n in top]
    for n in list(top):
        top.remove(n)
    top.set('size', '14')
    # old titles were stored in presentation order; take the first 14
    for title in existing[:14]:
        E.SubElement(top, '{' + vt + '}lpstr').text = title
D['docProps/app.xml'] = xml(app)

out = B / FILES[0]
with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
    for n, v in D.items():
        z.writestr(n, v)
shutil.copy2(out, B / 'PAPER1_导师汇报_20261105_下午修订版_含一页速查.pptx')
(B / '制作记录/slide_order.json').write_text(json.dumps(keep))

# ---------- speaking script: keep header + pages 1-14 ----------
s = (BK / FILES[2]).read_text()
chunks = re.split(r'(?=^## 第 \d+ 页｜)', s, flags=re.M)
head = ('# 第一篇导师汇报：下午修订版逐页讲稿\n\n'
        '全文共 14 页（已按要求删除原第 15—22 页），约 10—12 分钟；'
        '汇报停在「1.25 nm 已完成：K 复现一致」。\n'
        '若只讲 8 分钟：第 1—6、8—9、11—14 页。\n\n'
        '开场 30 秒：原公式相对已有离散结果存在明显方向相关偏差，V2 总体改善但有反例；'
        '1.25 nm 已完成并复现 K，但薄间隙横槽网格检查仍未通过。\n\n'
        '结尾（原第 17、18 页已删，可口头收一句）：现有证据支持离散结果分析，'
        '尚不足以宣布全面验证；今天想请老师明确论文主张范围，再定两条补证路线的投入。\n\n')
(B / FILES[2]).write_text(head + ''.join(chunks[1:15]))

# ---------- read-me ----------
u = (BK / FILES[3]).read_text()
u = (u.replace('正文第 1—18 页，约 12—15 分钟；第 19—22 页为备查。',
               '全文共 14 页，约 10—12 分钟；汇报停在「1.25 nm 已完成：K 复现一致」。')
      .replace('如果只有约 8 分钟，可讲第 1—6、8—9、13—18 页，其余留作备查。第 7、10 页的趋势和流向角，可在老师追问时补充。',
               '如果只有约 8 分钟，可讲第 1—6、8—9、11—14 页。第 7、10 页的趋势和流向角，可在老师追问时补充。')
      .replace('PPT 共 22 页', 'PPT 共 14 页').replace('22 页均有新讲稿备注', '14 页均有讲稿备注')
      .replace('21 页尺寸、页码、表格和标题几何检查无发现或警告', '页尺寸、页码、表格和标题几何检查无发现或警告')
      .replace('PDF 为 22 页', 'PDF 为 14 页')
      .replace('共 22 页', '共 14 页'))
# remove the "新增第 22 页" section entirely and replace with a trim log
idx = u.find('## 新增第 22 页')
if idx != -1:
    u = u[:idx].rstrip() + '\n'
u += ('\n## 本次删页（11 月 5 日 15:25）\n\n'
      '按用户要求「14 页后面都删了」，保留第 1—14 页，删除原第 15—22 页：'
      'OpenFOAM 接入两页、当前结论与限制、请导师裁定、附录 A/B/C、以及上一轮新增的一页速查。'
      'PPT 停在「1.25 nm 已完成：K 复现一致，S4 横槽网格仍未通过」。\n\n'
      '**22 页原稿（PPTX + PDF + 讲稿 + 使用说明）完整备份**在 '
      '`制作记录/删15页起前_22页备份/`，随时可取回。'
      '单独的 `公式适用范围/一页速查_公式与证据链.pdf` 以及历史合并版 PDF 均未删除，仍在原处。\n\n'
      '删页只改汇报材料的页序与页码，未新增求解、未改门槛、未改历史 FAIL。\n')
(B / FILES[3]).write_text(u)
print('trimmed to', len(keep), 'pages; backup at', BK.name)

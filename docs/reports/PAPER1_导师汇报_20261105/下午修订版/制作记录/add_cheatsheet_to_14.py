"""Re-attach the one-page cheat sheet as page 15 of the trimmed 14-page deck.

The slide parts are restored byte-for-byte from the 22-page backup, so the
content is exactly the version the user already approved. Native editable OOXML.
"""
from pathlib import Path
import xml.etree.ElementTree as E, zipfile, re, shutil, json

B = Path(__file__).resolve().parent.parent
SRC22 = B / '制作记录/删15页起前_22页备份/PAPER1_导师汇报_20261105_下午修订版.pptx'
SRC22_SCRIPT = B / '制作记录/删15页起前_22页备份/下午汇报逐页讲稿.md'
BK = B / '制作记录/加回速查页前_14页备份'
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
NEW = 24

with zipfile.ZipFile(BK / FILES[0]) as z:
    D = {n: z.read(n) for n in z.namelist()}
with zipfile.ZipFile(SRC22) as z:
    OLD = {n: z.read(n) for n in z.namelist()}

# restore the four parts of the cheat-sheet slide from the approved 22-page version
parts = [f'ppt/slides/slide{NEW}.xml', f'ppt/slides/_rels/slide{NEW}.xml.rels',
         f'ppt/notesSlides/notesSlide{NEW}.xml', f'ppt/notesSlides/_rels/notesSlide{NEW}.xml.rels']
for p in parts:
    assert p in OLD, p
    D[p] = OLD[p]

# page marker 22 / 22 -> 15 / 15, and section label no longer says "附录 D"
root = E.fromstring(D[f'ppt/slides/slide{NEW}.xml'])
for s in root.find('p:cSld/p:spTree', NS):
    c = s.find('.//p:cNvPr', NS)
    if c is None:
        continue
    if c.get('id') == '3':
        for t in s.findall('.//a:t', NS):
            if '附录 D' in (t.text or ''):
                t.text = (t.text or '').replace('附录 D', '备查')
    if c.get('id') == '8':
        for t in s.findall('.//a:t', NS):
            if re.fullmatch(r'\d+ / 22', t.text or ''):
                t.text = '15 / 15'
D[f'ppt/slides/slide{NEW}.xml'] = xml(root)

# renumber the 14 kept pages
pr = E.fromstring(D['ppt/presentation.xml'])
lst = pr.find('p:sldIdLst', NS)
rels = E.fromstring(D['ppt/_rels/presentation.xml.rels'])
lookup = {n.get('Id'): n.get('Target') for n in rels}
order = [int(re.search(r'slide(\d+)\.xml', lookup[n.get('{' + NS['r'] + '}id')]).group(1))
         for n in lst]
assert len(order) == 14, order
for pos, i in enumerate(order, 1):
    r = E.fromstring(D[f'ppt/slides/slide{i}.xml'])
    for t in r.findall('.//a:t', NS):
        if re.fullmatch(r'\d+ / 14', t.text or ''):
            t.text = f'{pos} / 15'
    D[f'ppt/slides/slide{i}.xml'] = xml(r)

# new relationship + sldId at the end
rid = 'rId' + str(max(int(n.get('Id')[3:]) for n in rels) + 1)
E.SubElement(rels, '{' + R + '}Relationship',
             {'Id': rid, 'Type': NS['r'] + '/slide', 'Target': f'slides/slide{NEW}.xml'})
E.register_namespace('', R)
D['ppt/_rels/presentation.xml.rels'] = xml(rels)
E.SubElement(lst, '{' + NS['p'] + '}sldId',
             {'id': str(max(int(n.get('id')) for n in lst) + 1),
              '{' + NS['r'] + '}id': rid})
D['ppt/presentation.xml'] = xml(pr)
order = order + [NEW]

# content types
ct = E.fromstring(D['[Content_Types].xml'])
have = {o.get('PartName') for o in ct}
for part, typ in [(f'slides/slide{NEW}.xml', 'slide'),
                  (f'notesSlides/notesSlide{NEW}.xml', 'notesSlide')]:
    pn = '/ppt/' + part
    if pn not in have:
        E.SubElement(ct, '{' + CT + '}Override',
                     {'PartName': pn,
                      'ContentType': 'application/vnd.openxmlformats-officedocument.presentationml.' + typ + '+xml'})
E.register_namespace('', CT)
D['[Content_Types].xml'] = xml(ct)

# app.xml
ep = 'http://schemas.openxmlformats.org/officeDocument/2006/extended-properties'
vt = 'http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes'
app = E.fromstring(D['docProps/app.xml'])
app.find('{' + ep + '}Slides').text = '15'
hp = app.find('{' + ep + '}HeadingPairs/{' + vt + '}vector')
if hp is not None:
    for j, v in enumerate(list(hp)[:-1]):
        if any(n.text == 'Slides' for n in v.iter()):
            for n in list(hp)[j + 1].iter():
                if n.tag == '{' + vt + '}i4':
                    n.text = '15'
top = app.find('{' + ep + '}TitlesOfParts/{' + vt + '}vector')
if top is not None:
    titles = [n.text or '' for n in top]
    for n in list(top):
        top.remove(n)
    top.set('size', '15')
    for t in titles[:14] + ['公式与证据链：一页看懂（省略版）']:
        E.SubElement(top, '{' + vt + '}lpstr').text = t
D['docProps/app.xml'] = xml(app)

out = B / FILES[0]
with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
    for n, v in D.items():
        z.writestr(n, v)
shutil.copy2(out, B / 'PAPER1_导师汇报_20261105_下午修订版_含一页速查.pptx')
(B / '制作记录/slide_order.json').write_text(json.dumps(order))

# ---------- speaking script: restore the cheat-sheet section as page 15 ----------
s = (BK / FILES[2]).read_text()
s = s.replace('全文共 14 页（已按要求删除原第 15—22 页），约 10—12 分钟；汇报停在「1.25 nm 已完成：K 复现一致」。',
              '全文共 15 页：正文 1—14 页约 10—12 分钟；第 15 页为一页速查，老师问到公式或适用范围时翻查，不占正文时间。')
s = s.replace('若只讲 8 分钟：第 1—6、8—9、11—14 页。',
              '若只讲 8 分钟：第 1—6、8—9、11—14 页，第 15 页留作备查。')
old = SRC22_SCRIPT.read_text()
m = re.search(r'(?=^## 第 22 页｜公式与证据链)', old, flags=re.M)
assert m, 'cheat-sheet section missing in 22-page script'
section = old[m.start():].replace('## 第 22 页｜', '## 第 15 页｜', 1)
s = s.rstrip() + '\n\n' + section.strip() + '\n'
(B / FILES[2]).write_text(s)

# ---------- read-me ----------
u = (BK / FILES[3]).read_text()
u = (u.replace('全文共 14 页，约 10—12 分钟；汇报停在「1.25 nm 已完成：K 复现一致」。',
               '全文共 15 页：正文 1—14 页约 10—12 分钟，第 15 页为一页速查备查页。')
      .replace('如果只有约 8 分钟，可讲第 1—6、8—9、11—14 页。',
               '如果只有约 8 分钟，可讲第 1—6、8—9、11—14 页；第 15 页留作备查。')
      .replace('共 14 页', '共 15 页').replace('PPT 共 14 页', 'PPT 共 15 页')
      .replace('14 页均有讲稿备注', '15 页均有讲稿备注').replace('PDF 为 14 页', 'PDF 为 15 页'))
u = u.rstrip() + ('\n\n## 再调整（11 月 5 日 15:25 之后）\n\n'
                  '删页后按新要求**把一页速查重新加回**，作为第 15 页放在正文之后，备查用、不占正文时间。'
                  '该页部件从 22 页备份中原样取回（内容与已确认版一致），页眉由「附录 D」改为「备查」以避开跳号，'
                  '页码全部改为 `N / 15`。删掉的其余 7 页（OpenFOAM 两页、结论与限制、请导师裁定、附录 A/B/C）仍不恢复。\n\n'
                  '14 页中间状态已备份在 `制作记录/加回速查页前_14页备份/`，'
                  '22 页完整原稿在 `制作记录/删15页起前_22页备份/`。'
                  '仍只改汇报材料，未新增求解、未改门槛、未改历史 FAIL。\n')
(B / FILES[3]).write_text(u)
print('restored cheat sheet as page 15; total 15 pages; backup at', BK.name)

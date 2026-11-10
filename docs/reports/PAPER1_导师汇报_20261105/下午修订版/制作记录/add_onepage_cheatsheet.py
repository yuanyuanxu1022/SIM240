"""Add ONE clean, condensed cheat-sheet slide into the afternoon deck.

Keeps the 21-page original fully backed up; writes the 22-page deck in place plus
a clearly named copy. All content is native editable OOXML (text boxes / table).
"""
from pathlib import Path
import xml.etree.ElementTree as E, zipfile, re, copy, shutil, json

B = Path(__file__).resolve().parent.parent
BK = B / '制作记录/加入一页速查前_21页备份'
BK.mkdir(exist_ok=True)
FILES = ['PAPER1_导师汇报_20261105_下午修订版.pptx',
         'PAPER1_导师汇报_20261105_下午修订版.pdf',
         '下午汇报逐页讲稿.md', '先读这里_下午汇报.md']
for f in FILES:
    if not (BK / f).exists():
        shutil.copy2(B / f, BK / f)

# Reuse the proven native-editing helpers from the previous revision.
g = {'__file__': str(B / '制作记录/revise_ooxml.py')}
exec(compile((B / '制作记录/revise_ooxml.py').read_text().split('# Native edits preserve')[0],
             'native_helpers', 'exec'), g)
N = g['NS']; q = g['q']; text = g['text']; blank = g['blank_body']
box = g['box']; table = g['table']; runpara = g['runpara']; shape = g['shape']
xml = lambda r: E.tostring(r, encoding='utf-8', xml_declaration=True)

with zipfile.ZipFile(BK / FILES[0]) as z:
    D = {n: z.read(n) for n in z.namelist()}
slides = {int(re.search(r'slide(\d+)\.xml$', n).group(1)): E.fromstring(v)
          for n, v in D.items() if re.fullmatch(r'ppt/slides/slide\d+\.xml', n)}
g['slides'] = slides
NEW = max(slides) + 1          # 24
assert NEW == 24, NEW

# ---------- one clean page: clone chrome only ----------
slides[NEW] = copy.deepcopy(slides[20])
blank(NEW)
text(NEW, 3, '附录 D · 一页速查')
text(NEW, 4, '公式与证据链：一页看懂（省略版）')
text(NEW, 7, '口径：所有百分数均为同一批 18 组数据对 5 nm 离散参考的回顾性比较，不是独立预测精度；完整 23 条公式与 9 张表另存备查。')

BLUE, RED, GREY = '0E3F8C', 'D9534F', '1A2230'
PALE, LIGHT, WARN = 'E8EFF8', 'F7F9FC', 'FBECEC'

# headline band
box(NEW, .45, 1.30, 12.43, .52,
    '一句话：原公式在 18 组几何上全部高估；V2 是回顾性修正；适用范围写比例域；S4 横槽仍未通过。',
    15, True, color=BLUE, fill=PALE)

# left: four backbone formulas, generous white space
box(NEW, .45, 1.92, 6.00, .40, '①—④ 四条骨干公式', 15, True, color=BLUE)
box(NEW, .45, 2.36, 6.00, 2.56,
    '① 原式(3)　沿槽 K = [(h+d)³+h³]/24\n'
    '　　　　　 横槽 K = (h+d)³h³ / {6[(h+d)³+h³]}\n'
    '② 基准(2)　K = μJ/G = νJ/a（同一个式子）\n'
    '　　　　　 OpenLB 显式沟槽 5 nm，不输入公式系数\n'
    '③ V2(6)　 沿槽 F = 1/[1+1.7685(d/w)^1.6331]\n'
    '　　　　　 横槽 F = 1/[1+0.4900(d/w)^0.6990]\n'
    '④ 偏差(4)　E = K模型/K参考 − 1\n'
    '　　　　　 r = F(1+E) − 1（36 点核对一致）',
    13.2, color=GREY, fill=LIGHT, border='D6DCE5')

# right: one compact evidence table
rows = [
    ['数据大组', '得出什么结论', '这组的意义'],
    ['18 几何 / 36 点', '原式 36/36 全高估\n+8.11% ~ +204.85%', '偏差从哪来'],
    ['V2 拟合', '最坏残差 10.5% / 18.7%', '回顾性，非预测'],
    ['S0—S4 六条', '横槽 1.328% > 1%\n阶段未通过', '参考未闭合'],
    ['1.25 nm', 'K 相对差 0\n构建等价 PASS', '只关复现'],
    ['OpenFOAM 5 例', '静态接入一致', '只验接入'],
]
t = table(NEW, 6.65, 1.92, [2.05, 2.55, 1.63], rows, rowh=.50, fs=11.5)
for tc in t.findall('.//a:tr', N)[3].findall('a:tc', N):
    for c in tc.findall('.//a:rPr/a:solidFill/a:srgbClr', N):
        c.set('val', RED)

# bottom: three short cards — derivation / domain + S4 / OpenFOAM meaning
box(NEW, .45, 5.14, 3.95, 1.44,
    '公式怎么推出来的\n'
    '平板 h³/12 → 沿槽算术、横槽调和平均 → 式(3)。\n'
    '附录 E 证它是 Stokes 上界，只定高估方向。',
    11.8, color=GREY, fill=LIGHT, border='D6DCE5')
box(NEW, 4.55, 5.14, 3.95, 1.44,
    '适用范围与 S4\n'
    'K 三次齐次 ⇒ 自变量 α=h/w、β=d/w；18 点凸包内插值，域内不保证精度。\n'
    'S4 横槽 1.328% > 1%，阶段仍未通过。',
    11.8, color=GREY, fill=LIGHT, border='D6DCE5')
box(NEW, 8.65, 5.14, 4.23, 1.44,
    'OpenFOAM 的意义\n'
    'dᵢ = H/Kᵢ 把 K 接进平均模型；五个静态算例只验两端实现一致。\n'
    '不提供 V2 独立精度；A/B/C 流场验收尚未运行。',
    11.8, color=GREY, fill=LIGHT, border='D6DCE5')

# ---------- package plumbing: new slide + notes + content types + order ----------
R = 'http://schemas.openxmlformats.org/package/2006/relationships'
CT = 'http://schemas.openxmlformats.org/package/2006/content-types'
r = E.fromstring(D['ppt/slides/_rels/slide20.xml.rels'])
for n in r:
    if n.get('Type', '').endswith('/notesSlide'):
        n.set('Target', f'../notesSlides/notesSlide{NEW}.xml')
D[f'ppt/slides/_rels/slide{NEW}.xml.rels'] = xml(r)
r = E.fromstring(D['ppt/notesSlides/_rels/notesSlide20.xml.rels'])
for n in r:
    if n.get('Type', '').endswith('/slide'):
        n.set('Target', f'../slides/slide{NEW}.xml')
D[f'ppt/notesSlides/_rels/notesSlide{NEW}.xml.rels'] = xml(r)
D[f'ppt/notesSlides/notesSlide{NEW}.xml'] = D['ppt/notesSlides/notesSlide20.xml']

note = ('这一页是前面所有公式与证据链材料的一页速查，只留骨干，不投屏也能口头用。'
        '四条骨干公式：原式(3) 是待检验的手算近似；K=μJ/G=νJ/a 是 OpenLB 显式沟槽的独立数值基准，'
        '两个写法代数等价；式(6) 的 V2 是在原式上乘 F；式(4) 定义偏差 E 与残差 r，'
        '且 r=F(1+E)−1，这一式解释了修正后有的点变好、有的变差甚至变号。'
        '右侧表格按数据大组给结论和意义：18 组几何给出原式全高估；V2 是同一批数据的回顾性拟合；'
        'S0—S4 里横槽中细变化 1.328% 超过事先规定的 1%，阶段仍未通过；1.25 nm 只关闭服务器构建复现；'
        'OpenFOAM 五例只验证静态接入一致性，不提供 V2 精度证据。'
        '下方三块分别是公式推导链、适用范围写成比例域的理由、OpenFOAM 的意义。'
        '被老师问到精度时，可以报 10.5% / 18.7% / 1.328%，但每次都要补一句：'
        '这是拿同一批 18 组数据回头修正的回顾性残差，不是独立预测精度，也不是实验误差。'
        '本页不新增推导结论、不重拟合、不改门槛。')
nr = E.fromstring(D[f'ppt/notesSlides/notesSlide{NEW}.xml'])
for sp in nr.findall('.//p:sp', N):
    ph = sp.find('p:nvSpPr/p:nvPr/p:ph', N)
    if ph is not None and ph.get('type') == 'body':
        tx = sp.find('p:txBody', N)
        for p in tx.findall('a:p', N):
            tx.remove(p)
        for line in [note, '证据入口（相对 docs/reports）：SIM240_中文稿_导师审阅版_20261022.md 式(1)–(7) 与附录 E；PAPER1_claim_evidence_review_20261105/REPORT.md；URV_S4_completed_review_20261104_143205/REPORT.md；OpenFOAM_comparison_clarification_20261104/REPORT.md。']:
            tx.append(runpara(line, 12))
D[f'ppt/notesSlides/notesSlide{NEW}.xml'] = xml(nr)

ct = E.fromstring(D['[Content_Types].xml'])
for part, typ in [(f'slides/slide{NEW}.xml', 'slide'),
                  (f'notesSlides/notesSlide{NEW}.xml', 'notesSlide')]:
    E.SubElement(ct, '{' + CT + '}Override',
                 {'PartName': '/ppt/' + part,
                  'ContentType': 'application/vnd.openxmlformats-officedocument.presentationml.' + typ + '+xml'})
E.register_namespace('', CT)
D['[Content_Types].xml'] = xml(ct)

rels = E.fromstring(D['ppt/_rels/presentation.xml.rels'])
rid = 'rId' + str(max(int(n.get('Id')[3:]) for n in rels) + 1)
E.SubElement(rels, '{' + R + '}Relationship',
             {'Id': rid, 'Type': N['r'] + '/slide', 'Target': f'slides/slide{NEW}.xml'})
D['ppt/_rels/presentation.xml.rels'] = xml(rels)

pr = E.fromstring(D['ppt/presentation.xml'])
lst = pr.find('p:sldIdLst', N)
lookup = {n.get('Id'): n.get('Target') for n in rels}
oldorder = [int(re.search(r'slide(\d+)\.xml', lookup[n.get(q('r:id'))]).group(1)) for n in lst]
sids = {i: n for i, n in zip(oldorder, list(lst))}
sids[NEW] = E.Element(q('p:sldId'),
                      {'id': str(max(int(n.get('id')) for n in lst) + 1), q('r:id'): rid})
order = oldorder + [NEW]
for n in list(lst):
    lst.remove(n)
for pos, i in enumerate(order, 1):
    lst.append(sids[i])
    for t in slides[i].findall('.//a:t', N):
        if re.fullmatch(r'\d+ / 21', t.text or ''):
            t.text = f'{pos} / 22'
    D[f'ppt/slides/slide{i}.xml'] = xml(slides[i])
D['ppt/presentation.xml'] = xml(pr)

ep = 'http://schemas.openxmlformats.org/officeDocument/2006/extended-properties'
vt = 'http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes'
app = E.fromstring(D['docProps/app.xml'])
app.find('{' + ep + '}Slides').text = '22'
hp = app.find('{' + ep + '}HeadingPairs/{' + vt + '}vector')
if hp is not None:
    for j, v in enumerate(list(hp)[:-1]):
        if any(n.text == 'Slides' for n in v.iter()):
            for n in list(hp)[j + 1].iter():
                if n.tag == '{' + vt + '}i4':
                    n.text = '22'
top = app.find('{' + ep + '}TitlesOfParts/{' + vt + '}vector')
if top is not None:
    for n in list(top):
        top.remove(n)
    top.set('size', '22')
    for i in order:
        E.SubElement(top, '{' + vt + '}lpstr').text = ''.join(
            t.text or '' for t in shape(i, 4).findall('.//a:t', N))
D['docProps/app.xml'] = xml(app)

with zipfile.ZipFile(B / FILES[0], 'w', zipfile.ZIP_DEFLATED) as z:
    for n, v in D.items():
        z.writestr(n, v)
shutil.copy2(B / FILES[0], B / 'PAPER1_导师汇报_20261105_下午修订版_含一页速查.pptx')
(B / '制作记录/slide_order.json').write_text(json.dumps(order))

# ---------- speaking script + read-me ----------
s = (BK / FILES[2]).read_text()
s = s.replace('正文 18 页', '正文 18 页 + 速查 1 页').replace('共 21 页', '共 22 页')
s += ('\n## 第 22 页｜公式与证据链：一页看懂（省略版）\n\n'
      '备查页，老师问到公式或适用范围时翻到这一页。四条骨干公式讲清「手算原式 → 独立数值基准 → '
      '乘 F 修正 → 偏差与残差」，其中 K=μJ/G 与 K=νJ/a 是同一个式子，r=F(1+E)−1 解释了修正后变号。'
      '右侧表格按数据大组给结论与意义；下方三块是推导链、比例域适用范围、OpenFOAM 的意义。'
      '报数字时每次都补一句：这是同一批 18 组数据回头修正的回顾性残差，不是独立预测精度。\n\n'
      '证据：中文稿式(1)–(7) 与附录 E；PAPER1_claim_evidence_review_20261105/REPORT.md；'
      'URV_S4_completed_review_20261104_143205/REPORT.md；OpenFOAM_comparison_clarification_20261104/REPORT.md。\n\n')
(B / FILES[2]).write_text(s)

u = (BK / FILES[3]).read_text()
u = (u.replace('共 21 页', '共 22 页').replace('21 页均有', '22 页均有')
      .replace('PDF 为 21 页', 'PDF 为 22 页')
      .replace('第 19—21 页为备查', '第 19—22 页为备查')
      .replace('PPT 共 21 页', 'PPT 共 22 页'))
u = u.rstrip() + ('\n\n## 新增第 22 页\n\n'
                  '应要求把此前 6 页公式清单与 2 页证据链压缩成**一页整洁省略版**，'
                  '作为附录 D 备查页加入本 PPT（原生可编辑文本框与表格）。'
                  '四条骨干公式、五组数据结论、公式推导链、适用范围与 S4、OpenFOAM 意义各占一块；'
                  '不投屏也能口头用。21 页原稿已完整备份在 `制作记录/加入一页速查前_21页备份/`。'
                  '本页不新增求解、不改门槛、不改历史 FAIL。\n')
(B / FILES[3]).write_text(u)
print('added slide', NEW, 'as page', len(order), 'of 22; backup at', BK.name)

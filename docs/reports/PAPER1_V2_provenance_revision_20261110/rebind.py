#!/usr/bin/env python3
"""Refresh current bindings while preserving historical audit entries."""
from pathlib import Path
import difflib
import hashlib
import json
import re

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
R = 'docs/reports/'
MANIFEST = R + 'PAPER1_submission_package_20261109/MANIFEST.md'
AUTHORITY = R + 'PAPER1_CURRENT_FILES_AUTHORITY_20261110.md'
REGISTRY = R + 'PAPER1_width_evidence_merge_20261110/output_hashes.json'

def info(name):
    b = (ROOT / name).read_bytes()
    return {'sha256': hashlib.sha256(b).hexdigest(), 'bytes': len(b)}

def main():
    edits = json.loads((HERE / 'edits.json').read_text())
    modified = sorted({e['path'] for e in edits})
    mpath = ROOT / MANIFEST
    text = mpath.read_text()
    rows = text.splitlines(True)
    for name in modified:
        found = [i for i, line in enumerate(rows) if line.startswith('| ') and f'`{name}`' in line]
        assert len(found) == 1, (name, found)
        i = found[0]
        d = info(name)
        rows[i] = re.sub(r'`[0-9a-f]{16}` \| \d+ \|',
                         f"`{d['sha256'][:16]}` | {d['bytes']} |", rows[i])
    derived = {}
    for lang, mother in [('CN', R+'SIM240_中文稿_导师审阅版_20261022.md'),
                         ('EN', R+'SIM240_First_Paper_English_20261028.md')]:
        name = R+f'PAPER1_submission_manuscript_20261110/SIM240_submission_{lang}.md'
        d = info(name)
        derived[lang] = (name, d)
        nlines = len((ROOT/name).read_text().splitlines())
        found = [i for i,line in enumerate(rows) if line.startswith(f'| `SIM240_submission_{lang}.md` |')]
        assert len(found)==1
        mi=info(mother)
        rows[found[0]] = (f"| `SIM240_submission_{lang}.md` | {nlines} | {d['bytes']} | "
                          f"`{d['sha256'][:16]}` | 第 {'1' if lang=='CN' else '2'} 行 "
                          f"（`{mi['sha256'][:16]}`，{mi['bytes']} B） |\n")
    text=''.join(rows)
    marker='## 2 数据证据件'
    assert text.count(marker)==1
    section = '''## 1.6 V2来源与标定身份澄清（2026-11-10）

按本轮授权定点同步两正文、两补充与结论定稿：V2由本研究建立并标定，因子自变量为d/w；标定采用h=50/75/125 nm与d=25/50/100 nm的9种几何，每方向9个5 nm导度结果，分别以最小化最大绝对相对残差拟合两个参数，共四个参数。主集为18种几何、36条主方向结果，不能写成36种几何或全部36条均进入拟合目标。

两正文§1.3明确建立与标定，§4.4补方法、标定集及回顾性身份；摘要、§1.2、新增间隙段与结论中“既定/公布/published”在涉及V2来源处改为本研究所建/固定系数。两补充S2及独立结论文件同口径同步。9种扩展几何在形式选择时已可见，仍不认证独立预测；未声称完全独立原创、理论推导出四参数或全球首创。导师或组内直接前身尚待作者补充，项目内记录不替代贡献者确认。

第1—5行及§1.4派生件表已按实际文件重绑；派生脚本重新生成并通过--check。证据入口：`docs/reports/PAPER1_V2_provenance_revision_20261110/REPORT.md`、`verification.json`、`edits.json`、逐稿diff与改前快照。原公式、V2四参数、既有结果数值、单位、显示公式、图表/参考文献编号和历史FAIL均保留；仅补显已有标定信息，不重新拟合/求解，不改Gate或submission_ready=false。当前完整指纹仍见`PAPER1_width_evidence_merge_20261110/output_hashes.json`；此前各节指纹保留历史快照身份。

---

'''
    mpath.write_text(text.replace(marker,section+marker) if '## 1.6 ' not in text else text)

    apath=ROOT/AUTHORITY
    a=apath.read_text()
    rows=a.splitlines(True)
    for name in modified:
        found=[i for i,line in enumerate(rows) if line.startswith('| ') and f'`{name}`' in line]
        assert len(found)==1
        d=info(name)
        rows[found[0]]=re.sub(r'`[0-9a-f]{16}` \| \d+ \| [^|]+\|$',
                              f"`{d['sha256'][:16]}` | {d['bytes']} | 11-10 V2来源修订 |",rows[found[0]].rstrip('\n'))+'\n'
    a=''.join(rows)
    a=re.sub(r'最后更新：[^\n]+',
             '最后更新：2026-11-10（V2来源/标定身份修订，两正文/两补充/结论与派生件重绑定）。',a,count=1)
    md=info(MANIFEST)
    a=re.sub(r'（当前 `[0-9a-f]{16}`，\d+ 字节；[^\n]+',
             f"（当前 `{md['sha256'][:16]}`，{md['bytes']} 字节；新增§1.6 V2来源与标定身份澄清）。",a,count=1)
    for lang,(name,d) in derived.items():
        nlines=len((ROOT/name).read_text().splitlines())
        label='中文' if lang=='CN' else '英文'
        a=re.sub(rf'{label}投稿正文（\d+ 行，\d+ B，`[0-9a-f]{{16}}`）',
                 f"{label}投稿正文（{nlines} 行，{d['bytes']} B，`{d['sha256'][:16]}`）",a,count=1)
    a=a.replace('> **★ 投稿另有一套派生件',
                '> **注 3（2026-11-10）**：V2归属与9种几何标定方法已在两正文补清，固定系数/回顾性限定同步至两补充与结论。原公式、四参数、结果数值和FAIL不变；记录见 `PAPER1_V2_provenance_revision_20261110/REPORT.md`。本表第七节曾遗漏更新的旧派生件指纹也已按本轮实际产物同步。\n\n> **★ 投稿另有一套派生件',1) if '> **注 3（2026-11-10）**' not in a else a
    apath.write_text(a)

    reg=json.loads((ROOT/REGISTRY).read_text())
    for name in reg:
        reg[name]=info(name)
    (ROOT/REGISTRY).write_text(json.dumps(reg,ensure_ascii=False,indent=1)+'\n')
    for name in [MANIFEST,AUTHORITY,REGISTRY]:
        before=(HERE/'before'/name).read_text()
        after=(ROOT/name).read_text()
        (HERE/(Path(name).name+'.diff')).write_text(''.join(difflib.unified_diff(
            before.splitlines(True),after.splitlines(True),fromfile='before/'+name,tofile=name)))
    print('Rebound five main files, two derivatives, authority, MANIFEST and registry.')

if __name__=='__main__':
    main()

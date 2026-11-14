#!/usr/bin/env python3
"""Refresh current bindings only; retain historical revision records."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent

def main():
    before = json.loads((OUT / 'before_manifest.json').read_text())
    paths = list(before)
    current = {}
    for rel in paths[:7]:
        data = (ROOT / rel).read_bytes()
        current[rel] = {'sha256': hashlib.sha256(data).hexdigest(),
                        'bytes': len(data), 'lines': len(data.splitlines())}
    authority_path, manifest_path, readme_path = paths[7:]
    authority, manifest, readme = [(ROOT / p).read_text() for p in paths[7:]]
    for rel in paths[:5]:
        for kind in ('authority', 'manifest'):
            text = authority if kind == 'authority' else manifest
            row = next(line for line in text.splitlines() if line.startswith('| ') and '`' + rel + '`' in line)
            new = row.replace(before[rel]['sha256'][:16], current[rel]['sha256'][:16]).replace(str(before[rel]['bytes']), str(current[rel]['bytes']))
            if kind == 'authority':
                new = new.replace('11-14 DOE措辞/参考身份定点修订，数字保留', '11-14 R1—R5定点同步，数字与资格保留')
                authority = text.replace(row, new, 1)
            else:
                manifest = text.replace(row, new, 1)
    for i, rel in enumerate(paths[5:7]):
        name = Path(rel).name
        old, new = before[rel], current[rel]
        mother = paths[i]
        for kind in ('authority', 'manifest', 'readme'):
            text = {'authority': authority, 'manifest': manifest, 'readme': readme}[kind]
            rows = [line for line in text.splitlines() if line.startswith('| `' + name + '`')]
            for row in rows:
                updated = row.replace(old['sha256'][:16], new['sha256'][:16]).replace(str(old['bytes']), str(new['bytes']))
                updated = updated.replace(before[mother]['sha256'][:16], current[mother]['sha256'][:16]).replace(str(before[mother]['bytes']), str(current[mother]['bytes']))
                text = text.replace(row, updated, 1)
            if kind == 'authority': authority = text
            elif kind == 'manifest': manifest = text
            else: readme = text
    authority = authority.replace('最后更新：2026-11-14 DOE科学措辞与参考身份定点修订', '最后更新：2026-11-14 R1—R5主张层级与表注定点同步', 1)
    manifest = manifest.replace('清单当前绑定更新：2026-11-14 DOE科学措辞与参考身份定点修订', '清单当前绑定更新：2026-11-14 R1—R5主张层级与表注定点同步', 1)
    readme = readme.replace('最近一次生成：2026-11-14，DOE措辞与参考身份同步', '最近一次生成：2026-11-14，R1—R5主张层级与表注同步', 1)
    old_note = next(line for line in authority.splitlines() if line.startswith('> **本轮修订说明'))
    authority = authority.replace(old_note,
        '> **本轮修订说明（2026-11-14）**：R1—R5已同步五件母本与两份派生稿：引言区分主结论、跨方法验证及补充解释；补清混合参考和新增批次范围；h100缺加密限定OpenLB；深槽增量不作为分辨力证明；网格显示值与冻结验收的分母分别说明。全部数字、公式、引文及参考身份保留。完整检查见 `PAPER1_R1_R5_manuscript_sync_20261114/verification.json` 和 `output_hashes.json`；上一轮DOE修订记录保留历史身份。', 1)
    assert '## 1.15 R1—R5' not in manifest
    manifest += '\n---\n\n## 1.15 R1—R5主张层级与表注定点同步（2026-11-14）\n\n按作者授权落实核心主张终审的五项编辑：引言明确双向偏差、跨方法验证及固定V2回顾性评价的职责；双语补充说明混合FEM/FVM参考，事前冻结和最坏门槛值仅覆盖新增横槽批次；h100缺少的是OpenLB同几何加密；深槽增量与相邻网格变化只作量级比较；补充表网格变化保留细一级分母显示值，冻结验收继续按粗一级分母回执。未改变任何数字、参考资格、门槛或历史FAIL。\n\n五件母本、两件派生稿及当前绑定已同步。改前快照、25条逐项修改、数值/公式/引文不变性及285项输入保护核对见 `docs/reports/PAPER1_R1_R5_manuscript_sync_20261114/REPORT.md`、`edits.json`、`verification.json`、`output_hashes.json`。不新增仿真、不重拟合、不重冻；采用责任记录与投稿准备仍需独立完成。历史记录与原回执保持原字节。\n'
    (ROOT / manifest_path).write_text(manifest)
    new_manifest = (ROOT / manifest_path).read_bytes()
    old_manifest = before[manifest_path]
    authority = authority.replace('（当前 `' + old_manifest['sha256'][:16] + '`，' + str(old_manifest['bytes']) + ' 字节；',
        '（当前 `' + hashlib.sha256(new_manifest).hexdigest()[:16] + '`，' + str(len(new_manifest)) + ' 字节；', 1)
    for path, text in ((authority_path, authority), (readme_path, readme)):
        (ROOT / path).write_text(text)
    print('Refreshed three current registries; historical records retained.')

if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Generate 状态计数.md from the repository itself.

Every number quoted by the entry documents comes from here; do not hand-edit
counts in prose. Read-only with respect to data: it only writes 状态计数.md.
"""
from pathlib import Path
import csv, datetime, subprocess, sys

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '状态计数.md'


def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT), *args], text=True).strip()


def main():
    rows = list(csv.DictReader((ROOT / '文件清单.csv').open(encoding='utf-8-sig', newline='')))
    n_src = len(rows)
    total_bytes = sum(int(r['字节数']) for r in rows)
    missing = [r['本文件夹路径'] for r in rows if not (ROOT / r['本文件夹路径']).is_file()]

    runs = list(csv.DictReader((ROOT / '03_数据/00_数据索引/52项运行_当前位置.csv').open(encoding='utf-8-sig')))
    n_runs = len(runs)
    n_pass = sum(1 for r in runs if str(r.get('PASS', '')).strip().lower() == 'true')

    pts = list(csv.DictReader((ROOT / '03_数据/00_数据索引/36项主方向数据_模型对照.csv').open(encoding='utf-8-sig')))
    geoms = {(r['h_nm'], r['d_nm']) for r in pts}

    md = [p for p in ROOT.rglob('*.md')
          if p != OUT and '.git' not in p.parts
          and not set(p.relative_to(ROOT).parts) & {'_workspace', 'work'}]
    md_lines = sum(len(p.read_text(encoding='utf-8', errors='replace').splitlines()) for p in md)
    tracked = len(git('ls-files').splitlines())
    branch = git('rev-parse', '--abbrev-ref', 'HEAD')
    stamp = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S +08:00')

    lines = [
        '# 状态计数（自动生成）',
        '',
        f'生成时间：{stamp}；分支 `{branch}`；数量取自当前工作树与索引。',
        '',
        '本文件由 `python tools/status_counts.py` 生成。入口文档引用本文件，不手写数量。',
        '新增说明文档由 Git 跟踪，不进入来源清单；来源清单只收录带原项目路径的来源副本。',
        '',
        '| 量 | 值 |',
        '|---|---:|',
        f'| 来源清单记录 | {n_src} |',
        f'| 清单总字节 | {total_bytes} |',
        f'| 清单文件本地缺失 | {len(missing)} |',
        f'| Git 跟踪文件 | {tracked} |',
        f'| 52 项运行索引 | {n_runs} |',
        f'| 其中 PASS | {n_pass} |',
        f'| 主地图几何 | {len(geoms)} |',
        f'| 主地图方向样点 | {len(pts)} |',
        f'| Markdown 文件 | {len(md)} |',
        f'| Markdown 行数 | {md_lines} |',
        '',
    ]
    if missing:
        lines += [
            '## 本地缺失的清单文件',
            '',
            '以下路径在本机工作树中不存在或不可访问。Windows 的 260 字符路径上限是已知原因之一；',
            '这不等于仓库缺文件，Linux 工作树与 Git 对象仍完整。',
            '',
        ] + [f'- `{m}`' for m in missing[:10]]
        if len(missing) > 10:
            lines.append(f'- ……其余 {len(missing) - 10} 项略')
        lines.append('')
    OUT.write_text('\n'.join(lines), encoding='utf-8')
    print(f'wrote {OUT.name}: sources={n_src} runs={n_runs} pass={n_pass} geoms={len(geoms)} points={len(pts)}')
    if missing:
        print('missing files:', len(missing), file=sys.stderr)


if __name__ == '__main__':
    main()

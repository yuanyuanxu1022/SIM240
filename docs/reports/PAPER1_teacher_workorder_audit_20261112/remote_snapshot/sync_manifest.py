#!/usr/bin/env python3
"""Refresh SHA256 and byte counts in 文件清单.csv for files edited in the worktree.

Only existing rows are updated; new repository documents are not added. Text files
are hashed and measured after CRLF -> LF normalization so that the recorded values
match the LF blobs stored by Git on Windows with core.autocrlf=true.
"""
from pathlib import Path
import argparse, csv, hashlib, json, sys

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / '文件清单.csv'
RECORD = ROOT / '检查记录' / '清单同步.json'


def canonical(data):
    try:
        text = data.decode('utf-8')
    except UnicodeDecodeError:
        return data
    if '\r\n' not in text:
        return data
    return text.replace('\r\n', '\n').encode('utf-8')


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='report changes without writing')
    args = parser.parse_args()

    with MANIFEST.open(encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames
        rows = list(reader)

    updated, missing, unchanged = [], [], 0
    for row in rows:
        path = ROOT / row['本文件夹路径']
        if not path.is_file():
            missing.append(row['本文件夹路径'])
            continue
        raw = path.read_bytes()
        if sha256(raw) == row['SHA256'] and str(len(raw)) == row['字节数']:
            unchanged += 1
            continue
        data = canonical(raw)
        digest, size = sha256(data), len(data)
        if digest == row['SHA256'] and str(size) == row['字节数']:
            unchanged += 1
            continue
        updated.append({
            'path': row['本文件夹路径'],
            'old_sha256': row['SHA256'],
            'new_sha256': digest,
            'old_bytes': row['字节数'],
            'new_bytes': str(size),
        })
        row['SHA256'] = digest
        row['字节数'] = str(size)

    if updated and not args.check:
        newline = '\r\n' if b'\r\n' in MANIFEST.read_bytes()[:4096] else '\n'
        with MANIFEST.open('w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fields, lineterminator=newline)
            writer.writeheader()
            writer.writerows(rows)

    report = {
        'manifest_rows': len(rows),
        'unchanged': unchanged,
        'updated': updated,
        'missing_files': len(missing),
        'missing_examples': missing[:10],
        'dry_run': args.check,
        'new_documents_not_added': True,
        'physical_validation': False,
    }
    if not args.check:
        RECORD.parent.mkdir(exist_ok=True)
        RECORD.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    print(json.dumps({
        'manifest_rows': report['manifest_rows'],
        'unchanged': unchanged,
        'updated': len(updated),
        'missing': len(missing),
        'dry_run': args.check,
    }, ensure_ascii=False))
    for item in updated[:20]:
        print('  updated:', item['path'])
    return 0


if __name__ == '__main__':
    sys.exit(main())

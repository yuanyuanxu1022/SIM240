"""Check numeric citation usage in the two current integrated drafts, locally.

This checks bracket syntax and bibliography membership only. It does not verify
reference metadata, source content, or whether a citation supports a claim.
"""
from pathlib import Path
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[3]
REPORTS = ROOT / 'docs' / 'reports'
FILES = [
    REPORTS / 'SIM240_EJMB_英文整合工作稿_20261019.md',
    REPORTS / 'SIM240_EJMB_中文整合工作稿_20261019.md',
]
GROUP = re.compile(r'\[(\d+(?:\s*[-–—]\s*\d+)?(?:\s*[,，;]\s*\d+(?:\s*[-–—]\s*\d+)?)*)\]')


def audit(path):
    raw = path.read_bytes()
    lines = raw.decode('utf-8').splitlines()
    boundary = next(i for i, line in enumerate(lines)
                    if line.startswith('## REFERENCES') or line.startswith('## 参考文献'))
    entries = {}
    for line_number, line in enumerate(lines[boundary + 1:], start=boundary + 2):
        match = re.match(r'^\[(\d+)\]\s+', line)
        if match:
            entries.setdefault(int(match[1]), []).append(line_number)
    citations = {}
    for line_number, line in enumerate(lines[:boundary], start=1):
        for match in GROUP.finditer(line):
            for part in re.split(r'[,，;]', match[1]):
                bounds = [int(value) for value in re.split(r'[-–—]', part)]
                numbers = range(bounds[0], bounds[1] + 1) if len(bounds) == 2 else bounds
                for number in numbers:
                    citations.setdefault(number, []).append(line_number)
    assert hashlib.sha256(path.read_bytes()).hexdigest() == hashlib.sha256(raw).hexdigest()
    return {
        'path': str(path.relative_to(ROOT)),
        'sha256': hashlib.sha256(raw).hexdigest(),
        'references_heading_line': boundary + 1,
        'bibliography_count': len(entries),
        'cited_unique_count': len(citations),
        'uncited_bibliography_numbers': sorted(entries.keys() - citations.keys()),
        'citations_missing_bibliography': sorted(citations.keys() - entries.keys()),
        'duplicate_bibliography_numbers': {key: value for key, value in entries.items() if len(value) > 1},
        'bibliography_lines': entries,
        'citation_lines': citations,
        'input_unchanged': True,
    }


if __name__ == '__main__':
    results = {
        'date': '2026-10-19',
        'scope': 'numeric bracket citation usage only; no DOI, metadata, or claim-support verification',
        'bibtex_required_for_this_check': False,
        'drafts': [audit(path) for path in FILES],
    }
    output = Path(__file__).with_name('citation_usage.json')
    output.write_text(json.dumps(results, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps([{
        key: value for key, value in row.items()
        if key not in ('bibliography_lines', 'citation_lines')
    } for row in results['drafts']], ensure_ascii=False, indent=2))

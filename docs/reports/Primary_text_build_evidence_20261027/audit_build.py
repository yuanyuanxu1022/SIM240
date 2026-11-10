"""Read saved build artefacts; never compile, link or execute a solver."""
from pathlib import Path
import collections
import csv
import hashlib
import json
import re
import subprocess

ROOT = Path('/home/dell/yuanyuanxu/SIM240')
OUT = Path(__file__).resolve().parent
protected = json.loads((OUT / 'protected_inputs.json').read_text())

def read(path):
    path = Path(path).resolve()
    data = path.read_bytes()
    protected.setdefault(str(path), hashlib.sha256(data).hexdigest())
    return data

commands = []
def command(args, name):
    result = subprocess.run(args, capture_output=True, text=True, check=False)
    (OUT / 'evidence' / name).write_text(result.stdout + result.stderr)
    commands.append({'argv': args, 'exit': result.returncode, 'output': 'evidence/' + name})
    return result.stdout

inventory_path = ROOT / 'docs/reports/SIM240_Supplementary_Methods_20261024/Table_S1_run_inventory.csv'
runs = list(csv.DictReader(read(inventory_path).decode().splitlines()))
groups = collections.defaultdict(list)
for row in runs:
    groups[row['binary_sha256']].append(row['run_id'])

candidates = (OUT / 'evidence/local_build_candidates.txt').read_text().splitlines()
artifacts = []
for name in candidates:
    path = Path(name)
    data = read(path)
    item = {'path': name, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
    if data.startswith(b'\x7fELF'):
        label = 'artifact_' + str(len(artifacts))
        comment = command(['readelf', '-p', '.comment', name], label + '_comment.txt')
        notes = command(['readelf', '-n', name], label + '_notes.txt')
        sections = command(['readelf', '-SW', name], label + '_sections.txt')
        bid = re.search(r'Build ID: ([0-9a-f]+)', notes)
        item.update(elf=True, compiler_comment=comment.strip(),
                    build_id=bid.group(1) if bid else None,
                    debug_sections_present='.debug_info' in sections,
                    command_line_section_present='.GCC.command.line' in sections,
                    matching_run_ids=groups.get(item['sha256'], []))
    else:
        item['elf'] = False
    if path.suffix == '.d':
        deps = re.findall(r'/home/dell/openlb/[^\s\\]+', data.decode())
        item['openlb_dependency_paths'] = sorted(set(deps))
        item['historical_dependency_content_hashes_recorded'] = False
    artifacts.append(item)

entries = json.loads((OUT / 'evidence/share_build_entries.json').read_text())
clone = Path('/home/dell/yuanyuanxu/SIM240_code_figures_data_review_20261026')
share_head = command(['git', '-C', str(clone), 'rev-parse', 'HEAD'], 'share_head.txt').strip()
source_comparisons = []
for entry in entries:
    if '/src/' not in entry['原项目路径']:
        continue
    original = ROOT / entry['原项目路径']
    current_sha = hashlib.sha256(read(original)).hexdigest()
    package = Path('/home/dell/yuanyuanxu/SIM240_代码图片数据_20261022') / entry['本文件夹路径']
    package_sha = hashlib.sha256(read(package)).hexdigest() if package.exists() else None
    # Fixed Git tree blob ID, independent of sparse checkout expansion.
    blob = command(['git', '-C', str(clone), 'rev-parse', share_head + ':' + entry['本文件夹路径']],
                   'share_blob_' + str(len(source_comparisons)) + '.txt').strip()
    raw = read(original)
    git_id = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
    source_comparisons.append({'source': str(original), 'package_path': str(package),
        'current_sha256': current_sha, 'package_sha256': package_sha,
        'recorded_package_sha256': entry['SHA256'], 'fixed_git_blob': blob,
        'current_git_blob': git_id, 'matches_package_and_fixed_git':
        current_sha == package_sha == entry['SHA256'] and git_id == blob})
    command(['git', '-C', str(clone), 'log', '--all', '--format=%H %aI %s', '--', entry['本文件夹路径']],
            'share_history_' + str(len(source_comparisons)) + '.txt')

tracked = command(['git', '-C', str(ROOT), 'ls-files', '--',
    'CASE/D_series/D2_groove_error_map', 'CASE/D_series/D3_oblique_groove_tensor_check'], 'main_tracked.txt')
command(['git', '-C', str(ROOT), 'log', '--all', '--format=%H %aI %s', '--',
    'CASE/D_series/D2_groove_error_map', 'CASE/D_series/D3_oblique_groove_tensor_check'], 'main_history.txt')
openlb_head = command(['git', '-C', '/home/dell/openlb', 'rev-parse', 'HEAD'], 'current_openlb_head.txt').strip()
elfs = [a for a in artifacts if a['elf']]
summary = {
    'scope': 'Named D2/D3 artefacts under /home/dell/yuanyuanxu including ignored build directories; local document-name search; specified shared snapshot; not whole-machine or unnamed ELF search',
    'run_count': len(runs), 'hash_groups': [dict(sha256=h, count=len(v), run_ids=v,
       matching_elf_paths=[a['path'] for a in elfs if a['sha256'] == h]) for h,v in groups.items()],
    'artifacts': artifacts, 'shared_snapshot': share_head, 'source_comparisons': source_comparisons,
    'main_d2_d3_tracked_files': tracked.splitlines(), 'current_openlb_head': openlb_head,
    'linked_runs_with_retained_elf': sum(len(v) for h,v in groups.items() if any(a['sha256']==h for a in elfs)),
    'historical_source_build_binding_complete': False,
    'limits': ['ELF .comment is an embedded compiler marker, not a complete toolchain or all translation units record',
               'Build ID identifies linked bytes, not a source revision or a timestamp',
               '.d lists dependency paths, not historical contents',
               'Later source/package/Git snapshot identity does not bind historical binary compilation',
               'No solver or compiler executed; no historical manifest rewritten'],
    'commands': commands,
}
(OUT / 'build_evidence.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2)+'\n')
(OUT / 'protected_inputs.json').write_text(json.dumps(protected, indent=2)+'\n')
print(json.dumps({'runs': len(runs), 'candidates':len(artifacts),'elf_files':len(elfs),
   'linked_runs':summary['linked_runs_with_retained_elf'],
   'source_matches':[a['matches_package_and_fixed_git'] for a in source_comparisons],
   'protected_files':len(protected)},ensure_ascii=False))

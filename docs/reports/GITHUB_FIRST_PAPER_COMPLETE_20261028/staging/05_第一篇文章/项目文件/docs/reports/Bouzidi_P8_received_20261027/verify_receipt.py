"""Verify document scope, source identity and receipt records; never run a solver."""
from pathlib import Path
import datetime
import difflib
import hashlib
import json
import re

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    protected = json.loads((OUT / 'protected_inputs.json').read_text())
    intake = json.loads((OUT / 'intake.json').read_text())
    receipt = json.loads((OUT / 'contract_receipt.json').read_text())
    impl = json.loads((OUT / 'current_implementation.json').read_text())
    changes = json.loads((OUT / 'applied_changes.json').read_text())
    before = json.loads((OUT / 'editable_before.json').read_text())
    crossref = json.loads((OUT / 'evidence/crossref.json').read_text())['message']
    commands = json.loads((OUT / 'evidence/pdf_commands.json').read_text())
    failed_inputs = [p for p, r in protected.items()
                     if not Path(p).is_file() or digest(p) != r['sha256']]
    checks = {
        'all_80_protected_inputs_unchanged': len(protected) == 80 and not failed_inputs,
        'pdf_identity_size_sha': Path(intake['local_source']).stat().st_size == 413724
            and digest(intake['local_source']) == intake['sha256']
            == '751511dd8df61e373a0f94c86da350642ab38fe5c3602ac20bcff979ba4d10d7',
        'pdf_is_pdf': Path(intake['local_source']).read_bytes().startswith(b'%PDF-'),
        'nine_pages_with_eight_contiguous_article_pages': intake['pdf_pages'] == 9
            and intake['publisher_cover_pages'] == 1 and intake['article_pages'] == 8
            and [r['printed_page'] for r in intake['pages'][1:]] == list(range(3452, 3460)),
        'all_nine_pages_rendered_and_visual_review_recorded':
            all((OUT / f'pages/original-{n}.png').is_file() for n in range(1, 10))
            and all(p['visually_inspected'] for p in intake['pages']),
        'pdf_extract_and_render_commands_succeeded': all(r['exit_code'] == 0 for r in commands),
        'crossref_matches_identity': crossref['DOI'] == intake['doi']
            and crossref['title'][0] == intake['title']
            and crossref['page'] == '3452-3459' and crossref['volume'] == '13'
            and crossref['issue'] == '11'
            and crossref['published-print']['date-parts'][0][0] == 2001
            and [a['given'] + ' ' + a['family'] for a in crossref['author']] == intake['authors'],
        'six_specified_checks_have_original_locators':
            len(receipt['checks']) == 6
            and {c['id'] for c in receipt['checks']} == {'P8-Q', 'P8-L', 'P8-H', 'P8-T', 'P8-S', 'P8-M'}
            and all(c['original_printed_pages'] and c['original_locator']
                    and c['source_locators'] and c['status'] == 'CORRESPONDS_IN_REVIEWED_SCOPE'
                    for c in receipt['checks']),
        'thirteen_source_snapshots_match': len(impl['files']) == 13
            and all(digest(r['path']) == r['sha256'] for r in impl['files']),
        'source_fragment_locators_match': all(
            '\n'.join(f'{n}: {Path(r["path"]).read_text().splitlines()[n-1]}'
                      for n in range(f['start_line'], f['end_line'] + 1)) == f['text']
            for r in impl['files'] for f in r['fragments']),
        'no_compile_solver_fixture_real_extraction': all(receipt[k] is False for k in
            ['compile_executed', 'solver_executed', 'numerical_fixture_executed', 'real_N8_extraction_executed'])
            and receipt['new_run_id'] is None,
        'no_material_conflict_or_astra_claim': receipt['material_theoretical_conflict_found'] is False
            and receipt['astra_review_triggered'] is False,
        'scientific_states_preserved': receipt['NUMERICAL_GATE'] == 'NOT_EVALUATED'
            and receipt['RESULT_PASS'] is False and receipt['geometry_PASS'] is None
            and receipt['reference_qualified'] is False
            and receipt['strict_error_bound_established'] is False
            and receipt['submission_ready'] is False and receipt['prediction'] == 'HOLD'
            and receipt['historical_build_binding'] == 'OPEN'
            and receipt['reference_6_fulltext_applicability'] == 'OPEN',
    }
    document_diff = ''
    for path, record in before.items():
        source = Path(path)
        snap = OUT / 'before' / source.name
        checks['before_snapshot_' + source.name] = digest(snap) == record['sha256']
        expected = snap.read_text()
        for change in changes:
            if ROOT / change['path'] == source:
                if expected.count(change['old']) != 1:
                    raise ValueError('Unexpected replacement scope: ' + str(source))
                expected = expected.replace(change['old'], change['new'], 1)
        checks['only_declared_edits_' + source.name] = expected == source.read_text()
        document_diff += ''.join(difflib.unified_diff(
            snap.read_text().splitlines(True), source.read_text().splitlines(True),
            fromfile='before/' + source.name, tofile=str(source.relative_to(ROOT))))
    (OUT / 'document_changes.diff').write_text(document_diff)
    state_diff = ''
    for name in ['SIM240_AI_CONTEXT.md', 'AI_HANDOFF_20261015.md']:
        source = ROOT / 'docs/reports' / name
        old = (OUT / 'before' / name).read_text()
        new = source.read_text()
        # Require the old task section to be replaced, with other sections intact,
        # except the one explicit science-entry pointer in the GitHub section.
        old_start = old.index('## 第一篇：Bouzidi P8 仍缺完整原文')
        old_end = old.index('\n## ', old_start + 3)
        new_start = new.index('## 第一篇：Bouzidi原文已收到')
        new_end = new.index('\n## ', new_start + 3)
        old_remainder = old[:old_start] + old[old_end + 1:]
        new_remainder = new[:new_start] + new[new_end + 1:]
        new_remainder = new_remainder.replace(
            '科研最新状态见顶部Bouzidi原文接收入口；', '科研状态沿用下方原文接收入口；', 1)
        checks['state_scope_' + name] = old_remainder == new_remainder
        checks['state_points_to_new_receipt_' + name] = 'Bouzidi_P8_received_20261027/REPORT.md' in new
        state_diff += ''.join(difflib.unified_diff(
            old.splitlines(True), new.splitlines(True),
            fromfile='before/' + name, tofile=str(source.relative_to(ROOT))))
    (OUT / 'state_changes.diff').write_text(state_diff)
    # Write the verification target before checking report links to it.
    verification_path = OUT / 'verification.json'
    if not verification_path.exists():
        verification_path.write_text('{}\n')
    broken = []
    link_count = 0
    for doc in [OUT / 'REPORT.md', ROOT / 'docs/reports/SIM240_中文稿_导师审阅版_20261022.md',
                ROOT / 'docs/reports/SIM240_Supplementary_Methods_20261024/SUPPLEMENTARY_METHODS.md']:
        for target in re.findall(r'\]\(([^)]+)\)', doc.read_text()):
            if target.startswith(('https://', 'http://', '#')):
                continue
            path = re.sub(r':\d+(?::\d+)?$', '', target.split('#')[0])
            link_count += 1
            resolved = Path(path) if path.startswith('/') else doc.parent / path
            if not resolved.exists():
                broken.append({'document': str(doc), 'target': target})
    checks['report_and_formal_document_local_links_resolve'] = not broken
    result = {'checked_at': datetime.datetime.now().astimezone().isoformat(),
              'scope': 'DOCUMENT_AND_SOURCE_RECEIPT_INTEGRITY_ONLY_NOT_NUMERICAL_GATE',
              'all_checks_pass': all(checks.values()), 'checks': checks,
              'protected_inputs': len(protected), 'changed_protected_inputs': failed_inputs,
              'declared_document_replacements': len(changes), 'local_links': link_count,
              'broken_local_links': broken, 'human_author_adoption': 'NOT_RECORDED'}
    verification_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['all_checks_pass'] else 1


if __name__ == '__main__':
    raise SystemExit(main())

"""Exact isolated S1/A1 source adoption; never grants execution authority."""
from pathlib import Path
import difflib
import json
from evidence import need, sha

CASES = {'URV1_SMOOTH_H30_P_dx1p25_a100000', 'URV1_SMOOTH_H30_T_dx1p25_a100000'}


def verify_s1_revision(bound, observed, checker_case):
    from contracts import covered
    inputs = bound['inputs_sha256']
    path = checker_case / 's1_revision/anchor.json'
    covered(str(path), inputs)
    anchor = json.loads(path.read_text())
    need(anchor['revision_id'] == 'URV-S1-A1-v1' and anchor['simulation_authorized'] is False,
         'S1 source anchor is not launch authority')
    need(anchor['instruction_audit_status'] == 'PASS', 'S1 scoped machine audit not passed')
    need(bound.get('source_revision') == dict(id='URV-S1-A1-v1', anchor=str(path), sha256=sha(path)),
         'S1 source anchor not independently bound')
    need(bound.get('stage') == 'S1_SMOOTH_THIN', 'S1 source limited to S1 smooth controls')
    records = bound.get('approved_runs') or bound.get('prepared_runs')
    need(isinstance(records, list) and len(records) == 2 and
         {r.get('planned_case_id') for r in records} == CASES, 'exact S1 pair required')
    need(observed == anchor['native_source_sha256'], 'S1 exact source mismatch')
    sources = bound['provenance']['native_sources']
    by_name = {Path(p).name: Path(p) for p in sources}
    need(len(by_name) == len(sources) and set(by_name) == set(anchor['diffs']), 'S1 source map incomplete')
    for name, record in anchor['diffs'].items():
        base = covered(record['baseline_path'], inputs)
        delta = covered(record['path'], inputs)
        need(sha(base) == record['baseline_sha256'] and sha(delta) == record['sha256'], 'S1 reviewed baseline/diff changed')
        reconstructed = ''.join(difflib.unified_diff(base.read_text().splitlines(True),
            by_name[name].read_text().splitlines(True), fromfile='baseline/' + name, tofile='revision/' + name))
        need(reconstructed == delta.read_text(), 'S1 diff does not reconstruct exact source')
    for item in anchor['frozen_inputs']:
        covered(item['path'], inputs)
        need(sha(item['path']) == item['sha256'], 'S1 frozen scope/predecessor changed')
    predecessor = json.loads(Path(anchor['S0_acceptance_file']).read_text())
    need(predecessor['S0_RESULT_PASS'] is True and
         predecessor['S0_REVISION_DISPOSITION'] == 'ACCEPTED_NEW_A1_PAIR', 'accepted A1 S0 prerequisite missing')

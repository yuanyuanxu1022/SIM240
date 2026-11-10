"""Exact S1 source/ELF reuse for six S2 cases; no execution authority."""
from pathlib import Path
import difflib
import json
from evidence import need, sha

REVISION = 'URV-S2-S1-ELF-REUSE-v1'
ELF_SHA = '5c3836e97c99feab88cd8e41773237f6ff642a10558f151b11e112563382b07b'


def verify_s2_reuse(bound, observed, checker_case):
    from contracts import covered
    from stage_s2 import validate_records, validate_formal_authority
    path = checker_case / 's2_revision/anchor.json'
    covered(str(path), bound['inputs_sha256'])
    anchor = json.loads(path.read_text())
    need(anchor['revision_id'] == REVISION and anchor['simulation_authorized'] is False,
         'S2 source adoption is not execution authority')
    need(bound.get('source_revision') == dict(id=REVISION, anchor=str(path), sha256=sha(path)),
         'S2 source adoption binding mismatch')
    need(bound.get('stage') == 'S2_REG_GRID', 'exact S2 stage required')
    validate_records(bound, checker_case)
    need(observed == anchor['native_source_sha256'], 'S2 exact reused source mismatch')
    binary = covered(bound['provenance']['native_binary'], bound['inputs_sha256'])
    need(str(binary) == anchor['native_binary_path'] and sha(binary) == anchor['native_binary_sha256'] == ELF_SHA,
         'S2 requires the original byte-identical S1 ELF')
    sources = bound['provenance']['native_sources']
    by_name = {Path(p).name: Path(p) for p in sources}
    need(len(by_name) == len(sources) and set(by_name) == set(anchor['diffs']), 'S2 source map incomplete')
    for name, record in anchor['diffs'].items():
        base = covered(record['baseline_path'], bound['inputs_sha256'])
        delta = covered(record['path'], bound['inputs_sha256'])
        need(sha(base) == record['baseline_sha256'] and sha(delta) == record['sha256'], 'S2 baseline/diff drift')
        actual = ''.join(difflib.unified_diff(base.read_text().splitlines(True),
            by_name[name].read_text().splitlines(True), fromfile='baseline/' + name, tofile='revision/' + name))
        need(actual == delta.read_text(), 'S2 source/diff reconstruction mismatch')
    for item in anchor['frozen_inputs']:
        path = covered(item['path'], bound['inputs_sha256'])
        need(sha(path) == item['sha256'], 'S2 frozen protocol or predecessor drift')
    audit = json.loads(Path(anchor['machine_audit_path']).read_text())
    need(anchor['instruction_audit_status'] == 'REUSED_EXACT_ELF_SCOPED_PASS', 'S2 scoped audit missing')
    need(audit.get('SOURCE_REVISION_AUDIT') == 'PASS' and audit.get('binary_sha256') == ELF_SHA,
         'historical scoped audit failed or bound a different ELF')
    predecessor = json.loads(Path(anchor['S0_acceptance_file']).read_text())
    need(predecessor['S0_RESULT_PASS'] is True and predecessor['S0_REVISION_DISPOSITION'] == 'ACCEPTED_NEW_A1_PAIR',
         'accepted A1 S0 prerequisite missing')
    need([p.get('run_id') for p in anchor['S1_predecessors']] ==
         ['URV_S1_P_A1_v1_20261102_01', 'URV_S1_T_A1_v1_20261102_01'], 'exact accepted S1 pair required')
    for item in anchor['S1_predecessors']:
        accepted = json.loads(Path(item['acceptance']).read_text())
        completion = json.loads(Path(item['completion']).read_text())
        need(accepted['RESULT_PASS'] is True and accepted['NUMERICAL_GATE'] == 'PASS' and
             accepted['geometry_PASS'] is True and accepted['smooth'] is not None,
             'accepted S1 prerequisite missing')
        need(accepted['run_id'] == completion['run_id'] == item['run_id'] and
             completion['release_sha256'] == anchor['S1_release_sha256'] and
             completion['independent_process_exit_code'] == 0 and completion['inputs_unchanged'] is True,
             'S1 completion identity/exit mismatch')
        need(accepted['completion_sha256'] == sha(item['completion']), 'S1 acceptance/completion mismatch')
        run = Path(item['completion']).parent
        for relative, digest in completion['output_sha256'].items():
            raw = (run / relative).resolve()
            need(raw.is_relative_to(run) and sha(raw) == digest, 'S1 predecessor raw output drift')
    if bound.get('simulation_authorized') is True:
        validate_formal_authority(bound)

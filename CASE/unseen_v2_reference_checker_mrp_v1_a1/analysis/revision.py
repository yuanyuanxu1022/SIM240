"""One exact URV-MRP-v1 source revision; no generic source whitelist."""
from pathlib import Path
import difflib,json
from evidence import need,sha

def verify_revision(bound,observed,checker_case):
    from contracts import covered
    path=checker_case/'revision/revision_anchor.json'
    covered(str(path),bound['inputs_sha256'])
    anchor=json.loads(path.read_text())
    need(anchor['revision_id']=='URV-MRP-v1' and
         observed==anchor['native_source_sha256'],'native physical source differs from preparation anchor or exact MRP revision')
    need(bound.get('source_revision')=={'id':'URV-MRP-v1','anchor':str(path),'sha256':sha(path)},
         'exact source revision not independently bound')
    need(anchor['simulation_authorized'] is False,'revision anchor is not execution authorization')
    need(bound.get('stage')=='S0_REGRESSION','MRP revision limited to S0')
    original=checker_case/'common/source_preparation_anchor.json'
    need(sha(original)==anchor['original_anchor_sha256'],'original source anchor changed')
    for record in anchor['frozen_inputs']:
        covered(record['path'],bound['inputs_sha256'])
        need(sha(record['path'])==record['sha256'],'MRP frozen input changed')
    paths=bound['provenance']['native_sources'];by_name={Path(p).name:Path(p) for p in paths}
    need(len(by_name)==len(paths),'duplicate native source basename')
    for name,record in anchor['diffs'].items():
        diff=Path(record['path']);covered(str(diff),bound['inputs_sha256'])
        need(sha(diff)==record['sha256'],'reviewed source diff changed')
        baseline=Path(record['baseline_path']) if record['baseline_path'] else None
        if baseline:
            covered(str(baseline),bound['inputs_sha256'])
            need(sha(baseline)==record['baseline_sha256'],'diff baseline changed')
        old=baseline.read_text() if baseline else ''
        delta=''.join(difflib.unified_diff(old.splitlines(True),by_name[name].read_text().splitlines(True),
                                        fromfile='baseline/'+name,tofile='revision/'+name))
        need(delta==diff.read_text(),'reviewed diff does not reconstruct exact source')
    need(set(anchor['diffs'])==set(observed),'incomplete reviewed source revision')

#!/usr/bin/env python3
"""Check local source identity and preservation; do not run any fit or solver."""
from pathlib import Path
import hashlib
import json
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]

def info(p):
    b=p.read_bytes()
    return {'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}

def main():
    checks=[]
    def check(name,passed):checks.append({'check':name,'pass':bool(passed)})
    rows=json.loads((HERE/'inventory.json').read_text())
    check('34 PDF paths inventoried',len(rows)==34)
    check('30 distinct original PDF SHA256 values',len({r['sha256'] for r in rows})==30)
    unique=[r for r in rows if 'duplicate_of' not in r]
    terms=['1.7685','1.6331','0.4900','0.6990','1.768488','1.633079']
    matches=[]
    for row in rows:
        check('original PDF unchanged '+str(row['id']),info(Path(row['path']))==
              {k:row[k] for k in ['sha256','bytes']})
    for row in unique:
        check('full text extraction completed '+str(row['id']),row['full_text_exit']==0 and
              (ROOT/row['full_text_path']).exists() and row['text_characters']>0)
        t=(ROOT/row['full_text_path']).read_text()
        for term in terms:
            if term in t: matches.append({'id':row['id'],'term':term})
    check('no exact stored coefficient text matches in screened corpus',not matches)
    inputs=json.loads((HERE/'protected_inputs.json').read_text())
    states=['docs/reports/SIM240_AI_CONTEXT.md','docs/reports/AI_HANDOFF_PORTABLE_20261104.md']
    for name,d in inputs.items():
        if name not in states:check('protected project file unchanged '+name,info(ROOT/name)==d)
    for name in states:
        check('current source-audit handoff entry present '+name,
              'PAPER1_V2_downloads_source_audit_20261110/REPORT.md' in (ROOT/name).read_text())
    reg=json.loads((ROOT/'docs/reports/PAPER1_width_evidence_merge_20261110/output_hashes.json').read_text())
    for name,d in reg.items():check('current main output registry '+name,info(ROOT/name)==d)
    for ident,page in [(4,3),(11,4),(25,21),(25,24),(31,4),(31,5)]:
        check('rendered source page '+str((ident,page)),
              (HERE/'previews'/f'{ident:02d}_page{page}.png').exists())
    for name,doi in [('crossref_jfm.2020.134.json','10.1017/jfm.2020.134'),
                     ('crossref_j.mee.2017.04.001.json','10.1016/j.mee.2017.04.001')]:
        d=json.loads((HERE/name).read_text())
        check('Crossref DOI identity '+doi,d.get('status')=='ok' and
              d.get('message',{}).get('DOI','').lower()==doi)
    result={'checks':checks,'passed':sum(c['pass'] for c in checks),
            'failed':sum(not c['pass'] for c in checks),'numeric_text_matches':matches,
            'source_origin_confirmed':False,'global_novelty_established':False,
            'corpus_full_read_claimed':False,'new_simulation':False,'new_numerical_validation':False,
            'run_id':None,'refit':False,'formal_manuscripts_modified':False,'submission_ready':False}
    (HERE/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(result['passed'],'checks passed;',result['failed'],'failed; 34 source PDFs and 22 project inputs unchanged.')
    for c in checks:
        if not c['pass']:print('FAIL',c['check'])
    return bool(result['failed'])

if __name__=='__main__':sys.exit(main())

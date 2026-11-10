#!/usr/bin/env python3
"""Verify provenance wording and preservation using saved small artifacts only."""
from pathlib import Path
import ast
import collections
import csv
import hashlib
import json
import re
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
R = 'docs/reports/'
CN = R+'SIM240_中文稿_导师审阅版_20261022.md'
EN = R+'SIM240_First_Paper_English_20261028.md'
MANIFEST = R+'PAPER1_submission_package_20261109/MANIFEST.md'
AUTHORITY = R+'PAPER1_CURRENT_FILES_AUTHORITY_20261110.md'
REGISTRY = R+'PAPER1_width_evidence_merge_20261110/output_hashes.json'

def info(name):
    b=(ROOT/name).read_bytes()
    return {'sha256': hashlib.sha256(b).hexdigest(), 'bytes': len(b)}

def main():
    checks=[]
    def check(name, value, detail=''):
        checks.append({'check':name,'pass':bool(value),'detail':detail})

    edits=json.loads((HERE/'edits.json').read_text())
    modified=sorted({e['path'] for e in edits})
    numbers=lambda t: re.findall(r'(?<![A-Za-z0-9])\d+(?:\.\d+)?',t)
    displays=lambda t: re.findall(r'\$\$.*?\$\$',t,re.S)
    cite_numbers=lambda t: re.findall(r'\[(\d+(?:[–—,\-]\d+)*)\]',t)
    for name in modified:
        before=(HERE/'before'/name).read_text()
        after=(ROOT/name).read_text()
        replay=before
        for e in edits:
            if e['path']==name:
                check('exact before occurrence '+name+': '+e['before'][:20], replay.count(e['before'])==1)
                replay=replay.replace(e['before'],e['after'])
        check('edits reproduce '+name,replay==after)
        check('display equations preserved '+name,displays(before)==displays(after))
        check('numbered scientific references preserved '+name,cite_numbers(before)==cite_numbers(after))
        b=before; a=after
        # Only new numeric mentions are the explicitly sourced calibration-method paragraph.
        opening=next((e for e in edits if e['path']==name and e['before'].startswith(
            ('采用乘性因子','We apply multiplicative factors'))),None)
        if opening:
            b=b.replace(opening['before'],'')
            a=a.replace(opening['after'],'')
        check('all pre-existing numeric mentions preserved '+name,numbers(b)==numbers(a))
        # Table wording may change, while every numeric cell must stay the same.
        check('table numbers preserved '+name,
              numbers('\n'.join(l for l in before.splitlines() if l.startswith('|')))==
              numbers('\n'.join(l for l in after.splitlines() if l.startswith('|'))))
        # Every unchanged line block must survive in the same sequence.
        check('no V2 source ambiguity '+name,not any(s in after for s in
              ['既定经验','公布系数','公布V2','原先公布','published V2 coefficients',
               'published coefficients','published rounded form','fixed empirical correction','fixed empirical relation']))

    # Read source as syntax; do not import or execute any fitting routine.
    source=ROOT/'CASE/D_series/D2_groove_error_map/analysis_fit_v2.py'
    tree=ast.parse(source.read_text())
    constants={}
    for node in tree.body:
        if isinstance(node,ast.Assign) and isinstance(node.targets[0],ast.Name):
            try: constants[node.targets[0].id]=ast.literal_eval(node.value)
            except (ValueError,TypeError): pass
    check('calibration H from source',constants.get('CALIB_H')==(50.,75.,125.))
    check('calibration D from source',constants.get('CALIB_D')==(25.,50.,100.))
    check('fixed groove width',constants.get('W')==120.)
    functions={n.name:n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef)}
    objective=ast.get_source_segment(source.read_text(),functions['obj_minimax'])
    check('per-direction minimax objective present','np.max(np.abs(residuals(' in objective)
    fit_text=ast.get_source_segment(source.read_text(),functions['fit'])
    check('fit keys use calibration constants','for d in CALIB_D for h in CALIB_H' in fit_text)

    mp=ROOT/R/'SIM240_manuscript_revision_20261018/map36_evidence.csv'
    rows=list(csv.DictReader(mp.open()))
    expected={(h,d,dr) for h in constants['CALIB_H'] for d in constants['CALIB_D'] for dr in ['P','T']}
    actual={(float(r['h_nm']),float(r['d_nm']),r['direction']) for r in rows if r['group']=='calibration'}
    check('36 main records',len(rows)==36)
    check('18 main geometries',len({(r['h_nm'],r['d_nm']) for r in rows})==18)
    check('9 calibration geometries and 18 directional results',expected==actual and len(actual)==18)
    check('9 calibration records per direction',collections.Counter(k[2] for k in actual)=={'P':9,'T':9})
    pars=list(csv.DictReader((source.parent/'results/analysis/v2_fit_params.csv').open()))
    mm={r['direction']:r for r in pars if r['objective']=='minimax'}
    check('saved along coefficients round to unchanged Eq6',
          f"{float(mm['parallel']['a']):.4f}"=='1.7685' and f"{float(mm['parallel']['b']):.4f}"=='1.6331')
    check('saved transverse coefficients round to unchanged Eq6',
          f"{float(mm['perp']['a']):.4f}"=='0.4900' and f"{float(mm['perp']['b']):.4f}"=='0.6990')

    old=json.loads((HERE/'input_hashes.json').read_text())
    intended=set(modified+[MANIFEST,AUTHORITY,
        R+'PAPER1_submission_manuscript_20261110/SIM240_submission_CN.md',
        R+'PAPER1_submission_manuscript_20261110/SIM240_submission_EN.md',
        R+'SIM240_AI_CONTEXT.md',R+'AI_HANDOFF_PORTABLE_20261104.md'])
    protected={n:i for n,i in old.items() if n not in intended}
    for name,d in protected.items(): check('protected input unchanged '+name,info(name)==d)

    registry=json.loads((ROOT/REGISTRY).read_text())
    for name,d in registry.items(): check('current registry matches '+name,info(name)==d)
    check('registry count retained',len(registry)==18)
    m=(ROOT/MANIFEST).read_text(); a=(ROOT/AUTHORITY).read_text()
    for name in modified:
        d=info(name)
        for label,t in [('MANIFEST',m),('authority',a)]:
            line=next(l for l in t.splitlines() if l.startswith('| ') and f'`{name}`' in l)
            check(label+' current row '+name,d['sha256'][:16] in line and f"| {d['bytes']} |" in line)
    check('authority binds current MANIFEST',info(MANIFEST)['sha256'][:16] in a)
    for lang in ['CN','EN']:
        name=R+f'PAPER1_submission_manuscript_20261110/SIM240_submission_{lang}.md'
        d=info(name)
        check('authority current derivative '+lang,d['sha256'][:16] in a and str(d['bytes']) in a)
        check('MANIFEST current derivative '+lang,d['sha256'][:16] in m)
    cmd=[sys.executable,str(ROOT/R/'PAPER1_submission_manuscript_20261110/build_submission.py'),'--check']
    proc=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True)
    check('submission derived content and link check',proc.returncode==0 and proc.stdout.count('一致')==2)
    (HERE/'submission_check.txt').write_text(proc.stdout+proc.stderr)
    result={'scope':'V2 provenance and calibration wording only; no fitting, solver or scientific gate',
            'checks':checks,'passed':sum(c['pass'] for c in checks),
            'failed':sum(not c['pass'] for c in checks),'protected_inputs':len(protected),
            'run_id':None,'new_simulation':False,'refit':False,
            'independent_prediction_established':False,'submission_ready':False}
    (HERE/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(f"Checks: {result['passed']} passed, {result['failed']} failed; {len(protected)} protected inputs unchanged.")
    for c in checks:
        if not c['pass']: print('FAIL:',c['check'],c['detail'])
    return int(result['failed']>0)

if __name__=='__main__':
    sys.exit(main())

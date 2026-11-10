"""Record and correct three draft/reference remnants found during merge inspection."""
from pathlib import Path
import difflib
import hashlib
import json
import re

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[2]
edits=json.loads((OUT/'edits.json').read_text())
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def change(rel,old,new,reason):
    p=ROOT/rel;s=p.read_text();assert s.count(old)==1,(rel,old)
    p.write_text(s.replace(old,new));edits.append(dict(path=rel,operation='replace',before=old,after=new,reason=reason))
cn='docs/reports/SIM240_中文稿_导师审阅版_20261022.md'
en='docs/reports/SIM240_First_Paper_English_20261028.md'
change(cn,'共同倍率的最小剩余偏差另见补充候选及表S11。','共同倍率的最小剩余偏差另见补充S14.4及表S11。','replace draft wording with adopted supplementary section')
change(en,'given in the supplementary candidate and Table S11.','given in Supplement S14.4 and Table S11.','replace draft wording with adopted supplementary section')
change(en,'Figures S1c and W1d','Figures S1c and S1d','complete subpanel reference renumbering')
for name,old,new in [
    ('adopted_CN_4p3.md','补充候选及表S11','补充S14.4及表S11'),
    ('adopted_EN_4p3.md','the supplementary candidate and Table S11','Supplement S14.4 and Table S11'),
    ('adopted_EN_5p1.md','Figures S1c and W1d','Figures S1c and S1d')]:
    p=OUT/name;s=p.read_text();assert s.count(old)==1;p.write_text(s.replace(old,new))
manifest='docs/reports/PAPER1_submission_package_20261109/MANIFEST.md'
for n in (1,2):
    s=(ROOT/manifest).read_text();line=next(x for x in s.splitlines() if x.startswith(f'| {n} |'))
    rel=re.search(r'`([^`]+)`',line).group(1);p=ROOT/rel
    new=re.sub(r'`[a-f0-9]{16}` \| \d+ \|',f'`{sha(p)[:16]}` | {p.stat().st_size} |',line)
    change(manifest,line,new,'rebind after reference cleanup')
(OUT/'edits.json').write_text(json.dumps(edits,ensure_ascii=False,indent=2)+'\n')
before=json.loads((OUT/'before_hashes.json').read_text())
for rel in before:
    old=(OUT/'before'/rel).read_text();new=(ROOT/rel).read_text()
    (OUT/(Path(rel).name+'.diff')).write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile=rel+' before',tofile=rel+' after')))
outputs=json.loads((OUT/'output_hashes.json').read_text())
for rel in outputs: outputs[rel]={'sha256':sha(ROOT/rel),'bytes':(ROOT/rel).stat().st_size}
(OUT/'output_hashes.json').write_text(json.dumps(outputs,ensure_ascii=False,indent=2)+'\n')
print('Three reference/draft remnants corrected; manuscript hashes rebound.')

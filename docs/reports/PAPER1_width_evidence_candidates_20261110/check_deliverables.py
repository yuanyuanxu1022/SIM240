"""Consistency and export checks for the unmerged paired-width presentation."""
from pathlib import Path
from collections import Counter
import csv
import hashlib
import json
import math
import re
import subprocess
from PIL import Image

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[2]
SRC=ROOT/'docs/reports/PAPER1_scientific_question_decision_20261110'

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

protected=json.loads((OUT/'protected_inputs.json').read_text())
for rel,digest in protected.items(): assert sha(ROOT/rel)==digest,rel
old_verification=json.loads((SRC/'verification.json').read_text())
for rel,digest in old_verification['bound_raw_inputs'].items(): assert sha(ROOT/rel)==digest,rel
for name in ('paired_evidence.csv','selected_records.csv','mechanism_link.csv'):
    assert (OUT/name).read_bytes()==(SRC/name).read_bytes(),name
cn=(OUT/'CANDIDATE_CN.md').read_text(); en=(OUT/'CANDIDATE_EN.md').read_text()
assert re.findall(r'\\\[(.*?)\\\]',cn,re.S)==re.findall(r'\\\[(.*?)\\\]',en,re.S)
numeric=lambda s: Counter(re.findall(r'[−+\-]?\d+\.\d+',s))
assert numeric(cn)==numeric(en)
for text in (cn,en):
    assert all(f'CW{i}' in text for i in range(1,4))
    assert 'V2' in text and 'S14' in text
    for v in ('0.19101','0.58994','0.57915','0.77365','208.85','33.58','51.08','14.38'):
        assert v in text,v
tables={lang:(OUT/f'TABLES_{lang}.md').read_text() for lang in ('CN','EN')}
extract_tables=lambda s: [[line for line in block.splitlines() if line.startswith('|')][2:]
                        for block in re.split(r'\n## ',s)[1:]]
assert extract_tables(tables['CN'])==extract_tables(tables['EN'])
pairs=list(csv.DictReader((OUT/'paired_evidence.csv').open()))
for r in pairs:
    ap=1/float(r['F_P']);at=1/float(r['F_T'])
    assert math.isclose(ap/at,float(r['B']),rel_tol=1e-12)
    assert math.isclose(abs(ap-at)/(ap+at)*100,float(r['scalar_floor_percent']),rel_tol=1e-12)

manifest=json.loads((OUT/'figure_manifest.json').read_text())
assert not manifest['warnings']
assert manifest['scale']=='all linear; common 0 to 4.7 scale for both gradient panels'
for name,info in manifest['outputs'].items(): assert sha(OUT/name)==info['sha256'],name
lang_values=lambda lang:[{k:v for k,v in r.items() if k!='language'} for r in manifest['plotted_values'] if r['language']==lang]
assert lang_values('CN')==lang_values('EN')
metadata={}
for lang in ('CN','EN'):
    png=OUT/f'width_evidence_{lang}.png'
    with Image.open(png) as im:
        assert im.size==(2125,1771),im.size
        assert min(im.info['dpi'])>=299
        if im.mode=='RGBA': assert im.getextrema()[3]==(255,255)
    pdf=OUT/f'width_evidence_{lang}.pdf'
    info=subprocess.run(['pdfinfo',str(pdf)],check=True,text=True,capture_output=True).stdout
    assert re.search(r'^Pages:\s+1$',info,re.M)
    sizes=re.search(r'Page size:\s+([\d.]+) x ([\d.]+) pts',info)
    assert sizes
    mm=[float(x)*25.4/72 for x in sizes.groups()]
    assert all(abs(a-b)<.01 for a,b in zip(mm,[180,150]))
    fonts=subprocess.run(['pdffonts',str(pdf)],check=True,text=True,capture_output=True).stdout
    lines=fonts.splitlines()[2:]
    assert lines and all(re.search(r'\byes\s+yes\s+yes\b',line) for line in lines)
    svg=(OUT/f'width_evidence_{lang}.svg').read_text()
    assert '<image' not in svg and '<svg' in svg
    metadata[lang]={'pdfinfo':info,'pdffonts':fonts,'dimensions_mm':mm,'svg_embedded_images':False}

palette={'parallel':'00689D','transverse':'A94E00','profile':'666666','vertical':'8E559D'}
def luminance(hexcolor):
    v=[int(hexcolor[i:i+2],16)/255 for i in (0,2,4)]
    x=[t/12.92 if t<=.04045 else ((t+.055)/1.055)**2.4 for t in v]
    return sum(a*b for a,b in zip(x,[.2126,.7152,.0722]))
contrasts={k:1.05/(luminance(v)+.05) for k,v in palette.items()}
assert min(contrasts.values())>=3
out={'scope':'presentation consistency and file/export checks; not numerical or physical acceptance',
     'protected_inputs_unchanged':True,'protected_count':len(protected),'raw_small_files_unchanged':32,
     'copied_tables_match':True,'bilingual_display_equations_identical':True,
     'bilingual_decimal_tokens_identical':True,'bilingual_table_data_identical':True,
     'bilingual_plotted_data_identical':True,'export_metadata':metadata,
     'palette_contrast_against_white':contrasts,'color_only_encoding':False,
     'visual_review':'Both PNGs and both PDF raster previews inspected by assistant; no clipping or overlapping data labels observed after legend adjustment. This is not author sign-off.',
     'new_simulations':0,'new_fits':0,'new_field_processing':False,'formal_manuscripts_edited':False,
     'reference_qualified':False,'submission_ready':False,'script_sha256':sha(Path(__file__))}
(OUT/'verification.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:out[k] for k in ['protected_inputs_unchanged','bilingual_display_equations_identical',
    'bilingual_decimal_tokens_identical','bilingual_table_data_identical','bilingual_plotted_data_identical',
    'formal_manuscripts_edited','new_simulations']},ensure_ascii=False))

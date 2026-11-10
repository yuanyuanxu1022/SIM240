from pathlib import Path
import subprocess
import json
import hashlib

root = Path('/home/dell/yuanyuanxu/SIM240')
work = root / 'docs/reports/Formula_conclusions_summary_20261029'
tmp = root / 'tmp/pdfs/formula_conclusions_20261029'
tmp.mkdir(parents=True, exist_ok=True)
out = root / 'output/pdf/SIM240_公式与结论说明_20261029.pdf'
out.parent.mkdir(exist_ok=True)
cmd = ['/opt/quarto/bin/tools/x86_64/pandoc', str(work/'说明稿.md'), '-f', 'markdown', '-t', 'typst', '--standalone', '--template', str(work/'template.typ'), '-o', str(tmp/'summary.typ')]
p = subprocess.run(cmd, capture_output=True, text=True)
(work/'pandoc.log').write_text(p.stderr)
assert p.returncode == 0 and 'Could not convert TeX' not in p.stderr, p.stderr
p = subprocess.run(['/opt/quarto/bin/tools/x86_64/typst', 'compile', '--root', str(root), str(tmp/'summary.typ'), str(out)], capture_output=True, text=True)
(work/'typst.log').write_text(p.stderr)
assert p.returncode == 0, p.stderr
subprocess.run(['pdftotext', '-layout', str(out), str(tmp/'text.txt')], check=True)
text = (tmp/'text.txt').read_text()
required = ['1.7685', '1.6331', '0.4900', '0.6990', '204.85%', '54.19%', '10.5%', '18.7%', '6.9%', '16.36%', '18.71%', '9.20', '3.55', '1.034']
for item in required:
    assert item in text, item
excluded = ['如果向老师汇报', '当前最需要补强', '本轮只是解释现有成果', '下一步模型', '无需切换']
for item in excluded:
    assert item not in text, item
assert '�' not in text
info = subprocess.run(['pdfinfo', str(out)], capture_output=True, text=True, check=True).stdout
(work/'verification.json').write_text(json.dumps({'pdf':str(out.relative_to(root)), 'sha256':hashlib.sha256(out.read_bytes()).hexdigest(), 'required_values_checked':required, 'removed_passage_absent':True, 'pdfinfo':info, 'scientific_recalculation':False, 'visual_review':'PENDING'},ensure_ascii=False,indent=2)+'\n')
print(info)
print(out)

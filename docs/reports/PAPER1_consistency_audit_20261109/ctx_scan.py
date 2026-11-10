import re
import os

CN = '/home/dell/yuanyuanxu/SIM240/docs/reports/SIM240_中文稿_导师审阅版_20261022.md'
EN = '/home/dell/yuanyuanxu/SIM240/docs/reports/SIM240_First_Paper_English_20261028.md'

KEYS = ['10.30', '204.85', '8.11', '54.19', '88.85', '6.40', '30.63',
        '4.42', '4.43', '1.328', '126.62', '49.43', '2.21', '3.70', '67', '9.20']


def ctx(path, key, width=110):
    out = []
    for i, line in enumerate(open(path, encoding='utf-8'), 1):
        if key in line:
            s = line.strip()
            for m in re.finditer(re.escape(key), s):
                a = max(0, m.start() - width // 2)
                b = min(len(s), m.end() + width // 2)
                out.append((i, s[a:b].replace('\n', ' ')))
    return out


for k in KEYS:
    print('=' * 100)
    print('KEY', k)
    for tag, path in [('CN', CN), ('EN', EN)]:
        for ln, snippet in ctx(path, k):
            print('  [%s L%d] %s' % (tag, ln, snippet))

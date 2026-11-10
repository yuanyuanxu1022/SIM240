import re
import os

FILES = {
    'CN': 'docs/reports/SIM240_中文稿_导师审阅版_20261022.md',
    'EN': 'docs/reports/SIM240_First_Paper_English_20261028.md',
    'SM_CN': 'docs/reports/SIM240_Supplementary_Methods_20261024/SUPPLEMENTARY_METHODS.md',
    'SM_EN': 'docs/reports/SIM240_Supplementary_Methods_20261024/SUPPLEMENTARY_METHODS_EN_20261028.md',
}

# 基准：结论定稿文件里的关键数字（字符串形式，允许 %/％ 与空格差异）
BASELINE = [
    ('沿槽下界', '10.30'),
    ('沿槽上界', '204.85'),
    ('横槽下界', '8.11'),
    ('横槽上界', '54.19'),
    ('V2 沿槽前', '88.85'),
    ('V2 沿槽后', '6.40'),
    ('V2 横槽前', '30.63'),
    ('V2 横槽后', '4.42'),
    ('V2 沿槽最坏', '10.5'),
    ('V2 横槽最坏', '18.7'),
    ('薄隙加密', '4.43'),
    ('S4 控制', '1.328'),
    ('h100 沿槽', '126.62'),
    ('h100 横槽', '49.43'),
]

texts = {}
for k, p in FILES.items():
    full = os.path.join('/home/dell/yuanyuanxu/SIM240', p)
    if os.path.exists(full):
        texts[k] = open(full, encoding='utf-8').read()
    else:
        texts[k] = None
        print('MISSING', k, p)

print('%-14s %-8s %s' % ('项', '数值', 'CN / EN / SM_CN / SM_EN 出现次数'))
print('-' * 78)
for label, num in BASELINE:
    counts = []
    for k in ['CN', 'EN', 'SM_CN', 'SM_EN']:
        t = texts[k]
        counts.append(str(t.count(num)) if t else '-')
    print('%-14s %-8s %s' % (label, num, ' / '.join(counts)))

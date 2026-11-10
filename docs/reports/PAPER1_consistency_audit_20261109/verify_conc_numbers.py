import re

CONC = '/home/dell/yuanyuanxu/SIM240/docs/reports/PAPER1_conclusions_current_20261109.md'
CN = '/home/dell/yuanyuanxu/SIM240/docs/reports/SIM240_中文稿_导师审阅版_20261022.md'
CSV = '/home/dell/yuanyuanxu/SIM240/docs/reports/SIM240_manuscript_revision_20261018/map36_evidence.csv'
B44 = '/home/dell/yuanyuanxu/SIM240/docs/reports/PAPER1_闭环方案_20261105/bound_check_44_points.csv'

conc = open(CONC, encoding='utf-8').read()
cn = open(CN, encoding='utf-8').read()
csvt = open(CSV, encoding='utf-8-sig').read()
b44 = open(B44, encoding='utf-8').read()

nums = sorted(set(re.findall(r'\d+\.\d+', conc)))
print('结论定稿中出现的所有小数：')
miss = []
for n in nums:
    where = []
    if n in cn:
        where.append('CN')
    if n in csvt:
        where.append('CSV')
    if n in b44:
        where.append('B44')
    tag = '/'.join(where) if where else '!!未找到'
    if not where:
        miss.append(n)
    print('  %-12s %s' % (n, tag))

print()
if miss:
    print('需人工确认（不在任何源文件中）:', miss)
else:
    print('全部小数均可在正文或原始数据中找到出处。')

import os

CN = '/home/dell/yuanyuanxu/SIM240/docs/reports/SIM240_中文稿_导师审阅版_20261022.md'
EN = '/home/dell/yuanyuanxu/SIM240/docs/reports/SIM240_First_Paper_English_20261028.md'
SMC = '/home/dell/yuanyuanxu/SIM240/docs/reports/SIM240_Supplementary_Methods_20261024/SUPPLEMENTARY_METHODS.md'
SME = '/home/dell/yuanyuanxu/SIM240/docs/reports/SIM240_Supplementary_Methods_20261024/SUPPLEMENTARY_METHODS_EN_20261028.md'

cn = open(CN, encoding='utf-8').read()
en = open(EN, encoding='utf-8').read()
smc = open(SMC, encoding='utf-8').read()
sme = open(SME, encoding='utf-8').read()

PAIRS = [
    ('不推广/不 generalize', ['不推广', 'not generaliz', 'not be generaliz', 'no generalization']),
    ('非百分点', ['百分点', 'percentage point', 'not percentage points']),
    ('回顾性/retrospective', ['回顾性', 'retrospective']),
    ('非独立预测/not independent prediction', ['独立预测', 'independent prediction', 'not an independent']),
    ('不称盲测/not blind', ['盲测', 'blind']),
    ('5 格/5 cells', ['5 格', '5 cells', 'five cells', 'only 5']),
    ('不是误差界/not an error bound', ['误差界', 'error bound']),
    ('46 次验证/46 validations', ['46 次', '46 validations', 'not 46', '46 independent']),
    ('FAIL', ['FAIL', 'fail']),
    ('不构成/does not constitute', ['不构成', 'does not constitute', 'not a']),
]

print('%-38s %5s %5s %5s %5s' % ('限定语', 'CN', 'EN', 'SMC', 'SME'))
print('-' * 66)
for label, keys in PAIRS:
    def c(t):
        return sum(t.count(k) for k in keys)
    print('%-38s %5d %5d %5d %5d' % (label, c(cn), c(en), c(smc), c(sme)))

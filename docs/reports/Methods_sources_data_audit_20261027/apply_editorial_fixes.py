#!/usr/bin/env python3
"""Apply only verified bibliographic, provenance and availability wording fixes."""
from pathlib import Path
import json,hashlib,difflib,subprocess

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
MAIN=ROOT/'docs/reports/SIM240_中文稿_导师审阅版_20261022.md'
SUP=ROOT/'docs/reports/SIM240_Supplementary_Methods_20261024/SUPPLEMENTARY_METHODS.md'
before=HERE/'before';before.mkdir(exist_ok=False)
for p in [MAIN,SUP,ROOT/'docs/reports/SIM240_AI_CONTEXT.md',ROOT/'docs/reports/AI_HANDOFF_20261015.md']:
    (before/p.name).write_bytes(p.read_bytes())
protected=json.loads((ROOT/'docs/reports/Paper_formal_sync_20261027/protected_inputs.json').read_text())['sha256']
for p in [MAIN,SUP]:protected.pop(str(p.relative_to(ROOT)),None)
for p in (ROOT/'docs/reports/Paper_formal_sync_20261027').rglob('*'):
    if p.is_file():protected[str(p.relative_to(ROOT))]=hashlib.sha256(p.read_bytes()).hexdigest()
read=json.loads((HERE/'read_inputs.json').read_text())['sha256']
for p,h in read.items():
    path=Path(p)
    if path not in [MAIN,SUP]:protected[p]=h
(HERE/'protected_inputs.json').write_text(json.dumps({'sha256':protected,'scope':'selected current inputs and prior formal-sync artifacts, excluding this round authorized manuscript and supplement changes'},ensure_ascii=False,indent=2)+'\n')
(HERE/'git_status_before.txt').write_text(subprocess.run(['git','status','--short'],capture_output=True,text=True,check=True).stdout)
all_changes=[]
def change(text,id_,old,new):
    assert text.count(old)==1,(id_,text.count(old))
    all_changes.append({'id':id_,'old':old,'new':new})
    return text.replace(old,new,1)
text=MAIN.read_text()
text=change(text,'M01_REF6_TITLE_DOI',
 '[6] Dewangan M.K., Datta S. Semi-analytical solution for flow in a sinusoidal grooved channel. *Eur. J. Mech. B/Fluids*, 2018, **70**: 73–84.',
 '[6] Dewangan M.K., Datta S. Flow through microchannels with topographically patterned wall: A spectral theory for arbitrary groove depths. *Eur. J. Mech. B/Fluids*, 2018, **70**: 73–84. DOI: 10.1016/j.euromechflu.2018.02.004')
text=change(text,'M02_REF6_CONTENT_SCOPE',
 '同一作者对正弦沟槽给出了不限制幅度的半解析谱解 [6]。',
 '同一作者还对带图案化壁面的微通道流动进行了槽深相关的谱理论研究 [6]。')
text=change(text,'M03_REF6_VERIFICATION_NOTE',
 '> **注**：[6] 的卷期页码沿用项目台账，其题名与完整书目需在投稿前按原文核对。原文对正弦沟槽采用半解析谱方法、不限制幅度，与 [5] 的小参数渐近解适用条件不同，正文未将二者合并表述。',
 '> **注**：[6]的正式题名、作者、年份、卷号、页码与DOI已对照Crossref登记及作者所在机构出版目录核对。本轮未取得其全文，书目核验不等于完整适用条件核验；正文不再据此给出未经本轮原文确认的幅度范围。方法引文的核验层次与剩余缺口见补充材料S11。')
text=change(text,'M04_AVAILABILITY_CHECKLIST',
 '| 数据可用性声明 | 需按实际文件与访问记录核对公开范围、仓库版本和访问条件；是否需要 DOI 按目标期刊要求确认 |',
 '| 数据可用性声明 | 已核私有共享快照及其覆盖范围，见本附录下方说明；最终公开范围、访问方式和持久标识仍待作者确认 |')
text=change(text,'M05_REFERENCE_CHECKLIST',
 '| 参考文献终校 | [6] 的题名与卷期待按原文核对 |',
 '| 参考文献终校 | [6]书目信息已核；[8]、[9]全文公式及[10]期刊发表版的完整核对仍有缺口，范围见补充材料S11 |')
availability='''截至2026-10-27，部分代码、图片和原始数据已保存于私有仓库[SIM240_code_figures_data](https://github.com/yuanyuanxu1022/SIM240_code_figures_data)，本轮核对版本为提交[f11c0f20f6aaadf6920b95390855ec418cf8ae42](https://github.com/yuanyuanxu1022/SIM240_code_figures_data/commit/f11c0f20f6aaadf6920b95390855ec418cf8ae42)。该版本仅对有权限的人员开放，不是公众可下载的数据发布。本轮已核对其所选D2/D3运行记录及主要绘图输入；当前正文、方法补充材料和当日更新的部分图件/脚本尚未纳入该固定快照。共享包不等于本文全部材料和历史构建环境的完整复现档案。最终公开范围、访问方式及是否采用DOI等持久标识，仍需作者按实际文件和目标期刊要求确认。逐项覆盖与核验范围见 `Methods_sources_data_audit_20261027/REPORT.md`。

'''
text=change(text,'M06_ACTUAL_DATA_ACCESS_STATEMENT',
 '---\n\n## 附录 D　本版相对上一版（v2）的改动',
 availability+'---\n\n## 附录 D　本版相对上一版（v2）的改动')
note='''### D.9 方法引文、来源说明及数据访问范围核对（2026-10-27）

核对[4]、[6]—[10]的方法身份、已取得原文和当前实现证据，订正[6]题名并补DOI；在未取得全文的情况下，将其研究内容收窄到已核书目支持的描述。附录C记实际私有仓库版本、受限访问、选定数据覆盖及未同步内容；补充材料S10/S11区分当前二进制/源码、历史构建绑定和文献原文核验层次。原数值表、公式、系数、结果与结论不变。详细证据、访问失败和未闭合项见 `Methods_sources_data_audit_20261027/REPORT.md`。本轮不改变理论假设、数值判据、历史FAIL或投稿状态，没有新计算或发布。

'''
text=change(text,'M07_REVISION_HISTORY','---\n\n## 附录 E',note+'---\n\n## 附录 E')
MAIN.write_text(text)
sup=SUP.read_text()
para='''2026-10-27复核：上述52份指定运行清单仍缺少这些源码/构建绑定字段，二进制哈希仍分为22/22/6/2四组。本机当前可定位的D2与D3两个二进制分别匹配其中22项与6项运行的记录哈希；这只确认现存二进制的身份，不能证明其历史源码、编译器或依赖版本。当前OpenLB源码快照和Makefile可检查实现，但不能用固定注入的版本字符串补成历史来源证据。核对范围见[本轮来源报告](../Methods_sources_data_audit_20261027/REPORT.md)及`provenance.json`。

'''
sup=change(sup,'S01_CURRENT_PROVENANCE_RECHECK','<a id="sm-s11"></a>',para+'<a id="sm-s11"></a>')
old=sup.split('## S11 方法引文核实边界',1)[1]
new='''

2026-10-27更新；文献编号沿用配套正文。以下是来源核对范围，不是对本项目精度的统一放行：

- **[4] Patir–Cheng**：现有合法本地全文的印刷第15页式（23）（24）已再次目视核对，支持一维Reynolds模型内的调和/算术平均关系。不能据此将局部模型视为显式台阶域精确解或唯一耗散机制。
- **[6] Dewangan–Datta 2018**：正式题名为 *Flow through microchannels with topographically patterned wall: A spectral theory for arbitrary groove depths*，European Journal of Mechanics–B/Fluids 70，73–84，DOI 10.1016/j.euromechflu.2018.02.004。Crossref及[作者机构出版目录](https://web.iitd.ac.in/~subhra.datta/publications1.html)一致；本轮未取得全文，书目问题已订正，具体幅度条件不标为已完成全文核验。
- **[7] OpenLB**：Crossref核得2021年、81卷258–288页，[软件官方目录](https://www.openlb.net/articles/)可定位同一DOI；官网旧目录使用2020年条目，按最终卷页采用2021年。软件论文身份不证明各历史运行使用了哪个OpenLB版本。
- **[8] Bouzidi**：Crossref的出版社登记元数据/摘要支持反弹结合空间插值的方案身份，题名、作者、2001年、13(11)卷3452–3459页与DOI相符。AIP全文请求被拒绝，本轮未逐式比较原文与项目实现；q=.5等项目事实由保存记录和当前实现另核，不以摘要保证任意壁距的精度。
- **[9] Guo**：Crossref核对PRE65(4)、046308、2002年及DOI。当前OpenLB的`ForcedBGKdynamics`明确使用`forcing::PlainGuo`，`ForcedMomentum::computeU`加入`FORCE/2`，支持当前实现描述；APS全文接口返回401，本轮未逐式核原文，当前源码也不自动绑定所有历史二进制。
- **[10] GCI**：已取得[ASME官网方法文稿](https://www.asme.org/wwwasmeorg/media/resourcefiles/shop/journals/jfenumaccuracy.pdf)，实际查看PDF第6—7页（文稿页4—5）的步骤3—5及式（3）—（7），支持三格、观测阶、外推值和GCI的定义。该文稿列四位作者，与2008年期刊发表版的书目信息并非同一版，不能冒称逐页核对了期刊发表版。正文保留发表版引文；完整版本对应尚未闭合。方法有依据不使历史质量FAIL转为通过，也不建立全图严格误差界。

全文、元数据、当前源码、保存输出、历史构建与科学验收分别记录；未取得全文不等于文献不存在。完整访问记录、原始页预览及逐项裁定见[本轮核对报告](../Methods_sources_data_audit_20261027/REPORT.md)。本地原始支持记录[旧审计报告](../Methods_support_audit_20261022/REPORT.md)保留当时范围，不覆盖旧证书。第三方文献及本轮证据没有发布到共享仓库。
'''
sup=change(sup,'S02_CURRENT_CITATION_BOUNDARIES',old,new)
SUP.write_text(sup)
(HERE/'editorial_changes.json').write_text(json.dumps(all_changes,ensure_ascii=False,indent=2)+'\n')
diff=[]
for p in [MAIN,SUP]:diff.extend(difflib.unified_diff((before/p.name).read_text().splitlines(True),p.read_text().splitlines(True),fromfile=str(p.relative_to(ROOT))+'.before',tofile=str(p.relative_to(ROOT))))
(HERE/'editorial_changes.diff').write_text(''.join(diff))
print('Applied 7 manuscript and 2 supplement edits; scientific result sections and formulas retained.')

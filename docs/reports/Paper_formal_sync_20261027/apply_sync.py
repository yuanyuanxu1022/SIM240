#!/usr/bin/env python3
"""Apply the reviewed document candidate to the current manuscript only."""
from pathlib import Path
import csv
import difflib
import hashlib
import io
import json
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = ROOT/'docs/reports/SIM240_中文稿_导师审阅版_20261022.md'
CANDIDATE = ROOT/'docs/reports/SIM240_中文稿_限定措辞与理论附录候选_20261027.md'
PACKAGE = ROOT/'docs/reports/Paper_bounded_candidate_20261027'
verification = json.loads((PACKAGE/'verification.json').read_text())
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(BASE) == verification['base_sha256'], 'Base changed since candidate preparation; do not overwrite.'
assert sha(CANDIDATE) == verification['candidate_sha256'], 'Candidate changed since verification.'
assert verification['all_checks_pass']
snapshot = HERE/'before'
snapshot.mkdir(exist_ok=False)
for path in [BASE, ROOT/'docs/reports/SIM240_AI_CONTEXT.md', ROOT/'docs/reports/AI_HANDOFF_20261015.md']:
    (snapshot/path.name).write_bytes(path.read_bytes())
(HERE/'git_status_before.txt').write_text(subprocess.run(['git','status','--short'],capture_output=True,text=True,check=True).stdout)
protected = json.loads((PACKAGE/'protected_inputs.json').read_text())['sha256']
assert protected.pop(str(BASE.relative_to(ROOT))) == sha(BASE)
for path in PACKAGE.iterdir():
    if path.is_file(): protected[str(path.relative_to(ROOT))] = sha(path)
protected[str(CANDIDATE.relative_to(ROOT))] = sha(CANDIDATE)
assert all(sha(ROOT/p)==h for p,h in protected.items()), 'A selected protected input changed.'
(HERE/'protected_inputs.json').write_text(json.dumps({'sha256':protected,
    'scope':'selected prior inputs/reviews and candidate package; current manuscript intentionally excluded and preserved as before snapshot'},ensure_ascii=False,indent=2)+'\n')

text = CANDIDATE.read_text()
operations = []
def replace(id_,old,new):
    global text
    assert text.count(old)==1,(id_,text.count(old))
    text=text.replace(old,new,1)
    operations.append({'id':id_,'old':old,'new':new,'type':'document_status_or_history_only'})

replace('S01','**中文稿·限定措辞与理论短附录候选·作者采用待确认**',
 '**中文稿·正式工作稿（限定修订已同步，作者终审待完成）**')
metadata=next(x['new'] for x in json.loads((PACKAGE/'changes.json').read_text()) if x['id']=='R03')
replace('S02',metadata,
 '同步日期：2026-10-27。本稿按用户同步指令写入已交付候选的24项定点修订及理论短附录；同步前版本与差异保存在 `Paper_formal_sync_20261027/`。沿用既有原始 `result.txt` 与汇总 CSV 的独立复算结果，本轮未重新求解或拟合。文中图表编号沿用既有稿件，与英文稿旧编号的对应关系见文末附录。图件尚未嵌入正文，仅给出文件位置与图注。本文仍待作者最终科学审定；本次文字同步不改变数值参考、历史FAIL或投稿状态。')
replace('S03','### D.7 限定措辞与理论附录候选（2026-10-27）',
 '### D.7 限定措辞与理论附录候选准备（2026-10-27，历史记录）')
replace('S04','原导师审阅稿保留，作者科学采用待确认，无新求解、拟合、真实N8提取或Gate放行。',
 '候选准备时原导师审阅稿保留、作者采用待确认；本轮正式同步见D.8。该准备阶段无新求解、拟合、真实N8提取或Gate放行。')
replace('S05','## 附录 E　理想Stokes模型下局部立方律的上界性质（候选）',
 '## 附录 E　理想Stokes模型下局部立方律的上界性质')
replace('S06','本附录承接既有终审推导，作者采用待确认。结论只针对以下连续模型，不对本文离散数值参考的误差作保证。',
 '本附录沿用既有终审推导，已随本次文字修订同步至正式工作稿；最终科学审定仍待完成。结论只针对以下连续模型，不对本文离散数值参考的误差作保证。')
insert='''### D.8 限定修订同步至正式工作稿（2026-10-27）

按用户本轮同步指令，将已交付候选的24项定点修订及附录E写入本稿；本轮未收到排除项，按整体同步执行，未另行记录逐项人工科学核验。候选文件和原准备证据保留，同步前本稿保存在 `Paper_formal_sync_20261027/before/`。标题、摘要、结论与图注均沿用限定稿的参考口径；主式（1）—（7）、V2系数、原数值表和参考文献保持，附录E的假设、推导和式（E1）—（E6）不变。只调整候选/历史记录标识以反映本次同步，没有理论实质变更或严格数值误差界审定。最终作者科学审定、引文与来源缺口、数据声明及图件嵌入仍待完成。验证与改动记录见 `Paper_formal_sync_20261027/REVISION_NOTE.md` 和 `verification.json`；无新求解、编译、拟合、真实N8提取或数值/物理Gate放行。

'''
replace('S07','---\n\n## 附录 E',insert+'---\n\n## 附录 E')
BASE.write_text(text)
(HERE/'status_adaptations.json').write_text(json.dumps(operations,ensure_ascii=False,indent=2)+'\n')
(HERE/'manuscript_changes.diff').write_text(''.join(difflib.unified_diff((snapshot/BASE.name).read_text().splitlines(True),text.splitlines(True),fromfile=BASE.name+'.before',tofile=BASE.name)))
applied=[]
for item in json.loads((PACKAGE/'changes.json').read_text()):
    applied.append({'revision_id':item['id'],'location':item['location'],
        'status':'APPLIED_ON_USER_SYNC_INSTRUCTION','selection_basis':'ALL_DELIVERED_ITEMS_NO_EXCLUSIONS_SPECIFIED',
        'separate_itemwise_human_scientific_verification':'NOT_RECORDED'})
applied.append({'revision_id':'D7_AND_APPENDIX_E','location':'附录D.7及E',
    'status':'APPLIED_ON_USER_SYNC_INSTRUCTION','selection_basis':'ALL_DELIVERED_ITEMS_NO_EXCLUSIONS_SPECIFIED',
    'separate_itemwise_human_scientific_verification':'NOT_RECORDED'})
buf=io.StringIO(); writer=csv.DictWriter(buf,fieldnames=list(applied[0]));writer.writeheader();writer.writerows(applied)
(HERE/'applied_items.csv').write_text(buf.getvalue())
(HERE/'sync_status.json').write_text(json.dumps({
 'id':'PAPER_FORMAL_SYNC_20261027','status':'REVIEWED_CANDIDATE_SYNCED_TO_CURRENT_WORKING_MANUSCRIPT',
 'user_instruction':'按作者选定条目同步正式稿。若涉及假设改变、理论实质推广或严格数值误差界，使用GPT-6 Astra｜High复核。',
 'scope_interpretation':'No exclusions or alternative per-item selections found; all 24 delivered edits and appendix synchronized, as announced before editing.',
 'separate_itemwise_human_scientific_verification':'NOT_RECORDED','final_author_scientific_approval':'PENDING',
 'current_manuscript':str(BASE.relative_to(ROOT)),'candidate':str(CANDIDATE.relative_to(ROOT)),
 'before_sha256':verification['base_sha256'],'candidate_sha256':sha(CANDIDATE),'after_sha256':sha(BASE),
 'theoretical_substantive_change':False,'actual_model_switch_performed':False,
 'new_solver_run_id':None,'historical_N8_run_id':'D4_N8_diag_v3_1_20261026_v1',
 'solver_started':False,'real_N8_extraction':False,'refit_or_prediction_scoring':False,
 'NUMERICAL_GATE':'NOT_EVALUATED','RESULT_PASS':False,'geometry_PASS':None,
 'reference_qualified':False,'strict_error_bound_established':False,'submission_ready':False,
 'prediction_permission':'HOLD','git_commit_or_push':False},ensure_ascii=False,indent=2)+'\n')
print(f'Synchronized 24 edits and Appendix E; {len(protected)} selected existing files protected; original snapshot retained.')

"""Check saved abstract candidates and count text consistently; no solver or fitting."""
from pathlib import Path
import csv,json,re,hashlib

OUT=Path(__file__).resolve().parent
ROOT=OUT.parent
cn=(OUT/'ABSTRACT_CN_CANDIDATE.md').read_text().split('\n',1)[1].strip()
en=(OUT/'ABSTRACT_EN_CANDIDATE.md').read_text().split('\n',1)[1].strip()
main_cn=(ROOT/'SIM240_中文稿_导师审阅版_20261022.md').read_text()
main_en=(ROOT/'SIM240_First_Paper_English_20261028.md').read_text()
oldcn=main_cn.split('## 摘要',1)[1].split('**关键词',1)[0].strip()
olden=main_en.split('## Abstract',1)[1].split('**Keywords',1)[0].strip()

def quote_after(path,marker):
    s=path.read_text().split(marker,1)[1]
    return re.search(r'(?m)^> (.*)$',s)[1]
first=quote_after(ROOT/'PAPER1_title_data_abstract_step1_20261107/REPORT.md','候选：')
pieces=[first]
for n in range(2,6):
    pieces.append(quote_after(ROOT/f'PAPER1_abstract_sentence{n}_review_20261107/REPORT.md',f'## 推荐第{dict(zip(range(2,6),"二三四五"))[n]}句'))
pieces.append(quote_after(ROOT/'PAPER1_abstract_sentence6_review_20261107/REPORT.md','## 推荐改写为两句'))
pieces.append(quote_after(ROOT/'PAPER1_abstract_bound_sentence_review_20261107/REPORT.md','## 推荐句'))
pieces.append('上述定量结果限于采样几何与指定离散参考，尚未建立连续参数范围或实际压印过程的精度保证；结果提示，评价此类降阶模型时，应同时考察两主导度、其比值和参考敏感性。')
stitched='\n\n'.join(pieces)
(OUT/'STITCHED_SENTENCE_CANDIDATES_CN.md').write_text('# 逐句候选拼接稿（用于对比，不是推荐定稿）\n\n'+stitched+'\n')

def numbers(s):
    return re.findall(r'(?<![A-Za-z0-9.])[+−-]?\d+(?:\.\d+)?',s)
def metrics(s,english=False):
    ns=numbers(s)
    return {'Han_characters':len(re.findall(r'[\u4e00-\u9fff]',s)),
            'English_word_tokens':len(re.findall(r"[A-Za-z]+(?:[-’'][A-Za-z]+)*|[+−-]?\d+(?:\.\d+)?",s)) if english else None,
            'numeric_occurrences':len(ns),'numeric_tokens':ns}
checks=[]
def check(label,ok,details=None):checks.append({'check':label,'pass':bool(ok),'detail':details})
normalized_en=re.sub(r'\bfour\b','4',en)
check('bilingual_quantitative_sequence_normalized_four',numbers(cn)==numbers(normalized_en),{'cn':numbers(cn),'en_with_four_as_4':numbers(normalized_en),'normalization':'English four equals Chinese 4; metrics still count Arabic numerals only'})
check('candidate_shorter_than_stitched',len(cn)<len(stitched))
check('candidate_fewer_numbers_than_stitched',len(numbers(cn))<len(numbers(stitched)))
check('main_counts_and_refinement',all(x in cn for x in ['18种几何','36个主方向导度结果','5 nm','4种几何','2.5 nm']))
stats={x['component']:x for x in csv.DictReader((ROOT/'PAPER1_claim_final_review_20261105/recomputed_direction_stats.csv').open())}
for component in ['Kyy','Kxx']:
    for field in ['LC_max','V2_max_abs']:
        value=f"{float(stats[component][field]):.2f}"
        check('maximum_matches_'+component+'_'+field,value+'%' in cn and value+'%' in en,value)
check('no_new_independent_accuracy_claim',all(x in cn for x in ['回顾性','参考网格改变','保持V2系数不变','离散参考','连续导度的上界','不确定偏差幅度或V2准确度','尚未建立']))
check('retains_tensor_reconstruction',all(x in cn for x in ['同一线性张量关系','重建','45°','9.20°']))
manifest=json.loads((OUT/'source_manifest.json').read_text())
changed=[x['path'] for x in manifest if hashlib.sha256(Path(x['path']).read_bytes()).hexdigest()!=x['sha256']]
check('all_bound_inputs_preserved',not changed,changed)
result={'metrics':{'current_formal_CN':metrics(oldcn),'stitched_CN':metrics(stitched),'recommended_CN':metrics(cn),'current_formal_EN':metrics(olden,True),'recommended_EN':metrics(en,True)},'checks':checks,'passed':sum(x['pass'] for x in checks),'failed':sum(not x['pass'] for x in checks),'scope':'editorial and selected-source consistency, not scientific requalification','formal_abstract_edited':False,'new_solver_runs':0,'new_fit':False,'submission_ready':False}
(OUT/'check_results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'passed':result['passed'],'failed':result['failed'],'metrics':{k:{f:v for f,v in row.items() if f!='numeric_tokens'} for k,row in result['metrics'].items()}},ensure_ascii=False))
if result['failed']:raise SystemExit(1)

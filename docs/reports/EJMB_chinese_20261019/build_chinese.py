"""Assemble an author-review Chinese manuscript without changing source chapters."""
from pathlib import Path
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[3]
REPORTS = ROOT / "docs/reports"
NAMES = [
    "第一篇论文_第1章引言草稿_20261017.md",
    "第一篇论文_第2章方法草稿_20261017.md",
    "第一篇论文_第3章验证草稿_20261017.md",
    "第一篇论文_第4章结果I草稿_20261018.md",
    "第一篇论文_第5章_对比对象选择草稿_20261018.md",
    "SIM240_EJMB_英文整合工作稿_20261019.md",
]
paths = [REPORTS / n for n in NAMES] + [Path(__file__).with_name("新增中文段落.md")]
raw = {p: p.read_bytes() for p in paths}
hashes = {str(p.relative_to(ROOT)): hashlib.sha256(v).hexdigest() for p, v in raw.items()}
texts = {p.name: v.decode("utf-8") for p, v in raw.items()}


def between(s, start, end):
    return s.split(start, 1)[1].split(end, 1)[0].strip()


def chinese_sections(s, start, end):
    s = between(s, start, end)
    out = []
    mode = None
    for line in s.splitlines():
        if re.fullmatch(r"#{2,4} EN", line):
            mode = "en"
        elif re.fullmatch(r"#{2,4} 中文", line):
            mode = "zh"
        elif line.startswith("#"):
            if "／" in line:
                left, right = line.split("／", 1)
                m = re.match(r"(#{2,4}\s+(?:[A-Z]|\d+)\.)", left)
                assert m, line
                out.append(m.group(1) + " " + right.strip())
            else:
                out.append(line)
            mode = None
        elif mode == "zh":
            out.append(line)
    return "\n".join(out).strip()


new = texts["新增中文段落.md"]
abstract = between(new, "## 摘要", "## 引言")
intro = between(new, "## 引言", "## 结论")
conclusion = new.split("## 结论", 1)[1].strip()
methods = chinese_sections(texts[NAMES[1]], "## II. PROBLEM STATEMENT AND METHODS", "## 本章新增参考文献")
verification = chinese_sections(texts[NAMES[2]], "## III. VERIFICATION", "## 本章新增参考文献")
refinement = texts[NAMES[2]].split("## G2.", 1)[1].split("### 中文", 1)[1].strip()
refinement = refinement.replace("均通过本轮复算的数值门槛", "在2026-10-19既有核查记录中通过数值门槛")
verification += "\n\n### G2. 新增加密网格敏感性（既有结果）\n\n" + refinement
resolved = between(texts[NAMES[3]], "## 中文", "## 数据溯源表")
comparison = between(texts[NAMES[4]], "## 中文", "## 写作说明")

# Match the two evidence-bounded wording corrections already in the English candidate.
old = "式 (3) 的稳态流动在**显式几何**中直接用格点 Boltzmann 方法（LBM）求解"
assert old in methods
methods = methods.replace(old, "用于确定式(3)中输运系数的固定间隙单胞流动，在**显式几何**中采用格点 Boltzmann 方法（LBM）求解", 1)
old = "也是稳态 Stokes 流动的标准取值——此类问题中精度受边界处理而非碰撞模型限制。"
assert old in methods
methods = methods.replace(old, "本文尚未独立分解体相与边界处理对数值误差的贡献。", 1)
methods = methods.replace("稳定边界，本文", "稳定边界。本文")

refs = texts[NAMES[5]].split("## REFERENCES", 1)[1].strip()
header = """# 受限矩形沟槽的方向性输运：局部立方律闭合的误差及经验修正

**中文整合工作稿｜2026-10-19｜供作者与导师审阅，尚未达到投稿状态。**

本稿沿已推荐的EJMB流体力学主线组织，便于先用中文检查论证。第2—5章取自现有中文对照，新增中文摘要、引言和结论；不是英文全文逐句对译，也不是已经压缩完毕的最终稿。保留数字、公式、引用编号及证据限定，不修改原章、英文稿、V2或原始结果。

**阅读提示**：先看摘要与第6章结论，再看第4章结果和第5章比较；第2—3章用于核查方法与可信范围。图件尚未嵌入，第5章C节涉及图9/10的数据链仍待独立检查，相关传播数字未进入摘要。文中沿用的历史数值核查不是本次重新验收；当前没有新计算或Gate升级。作者署名、单位、基金及投稿声明尚未补齐。

---

## 摘要

"""
draft = (header + abstract + "\n\n## 1 引言\n\n" + intro
         + "\n\n## 2 问题与数值方法\n\n" + methods
         + "\n\n## 3 数值核查与可信范围\n\n" + verification
         + "\n\n## 4 显式几何中的方向性输运\n\n" + resolved
         + "\n\n## 5 闭合差异、经验修正与模型含义\n\n" + comparison
         + "\n\n## 6 结论\n\n" + conclusion
         + "\n\n## 参考文献（沿用英文稿的书目编号，待作者终核）\n\n" + refs + "\n")
draft = re.sub(r"\bTABLE\s+", "表 ", draft)
draft = re.sub(r"\bFIG\.\s*", "图 ", draft)
roman = {"I": "1", "II": "2", "III": "3", "IV": "4", "V": "5", "VI": "6"}
def section_ref(m):
    return "第" + roman[m.group(1)] + "章" + (m.group(2) + "节" if m.group(2) else "")
draft = re.sub(r"Sec\. (III|II|IV|VI|I|V)(?: ([A-H](?:\d+)?))?", section_ref, draft)
draft = re.sub(r"\n(?:---\n\n)+(?=## )", "\n\n", draft)
main = draft.split("## 参考文献", 1)[0]
formulas = re.findall(r"\\tag\{([^}]+)\}", main)
assert len(formulas) == len(set(formulas)), formulas
cited = {int(n) for g in re.findall(r"\[([\d, ]+)\]", main) for n in g.replace(" ", "").split(",")}
reference_numbers = {int(n) for n in re.findall(r"^\[(\d+)\]", refs, re.M)}
assert cited <= reference_numbers, cited - reference_numbers
assert all(hashlib.sha256(p.read_bytes()).hexdigest() == h for p, h in ((ROOT / k, v) for k, v in hashes.items()))
assert "### EN" not in draft and "### 中文" not in draft
for value in ["204.85", "54.19", "10.505", "6.921", "18.705", "14.936", "0.960996", "1.004658"]:
    assert value in draft, value
out = REPORTS / "SIM240_EJMB_中文整合工作稿_20261019.md"
assert not out.exists(), "Refusing to overwrite an existing Chinese draft"
out.write_text(draft, encoding="utf-8")
record = {
    "date": "2026-10-19", "scope": "Chinese manuscript integration and limited consistency checks",
    "source_hashes": hashes, "source_files_unchanged": True,
    "output": str(out.relative_to(ROOT)), "output_sha256": hashlib.sha256(out.read_bytes()).hexdigest(),
    "chinese_character_count": len(re.findall(r"[\u4e00-\u9fff]", draft)),
    "formula_tags": formulas, "reference_records": len(reference_numbers),
    "missing_cited_references": sorted(cited - reference_numbers),
    "human_author_approval": False, "submission_ready": False,
    "new_simulation": False, "new_numerical_validation": False,
    "limits": ["Figures not embedded or revalidated", "Propagation chain and figures 9/10 pending",
               "Not a sentence-by-sentence translation", "Full claim and source review not repeated"],
}
Path(__file__).with_name("integration_record.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({k: v for k, v in record.items() if k != "source_hashes"}, ensure_ascii=False, indent=2))

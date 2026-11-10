"""Build an author-review English draft from the existing reviewed chapter texts.

This script does not run a solver or optimizer, and never writes its source chapters.
The output is an integration draft, not a submission or numerical release.
"""
from pathlib import Path
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[3]
REPORTS = ROOT / "docs/reports"
OUT = REPORTS / "SIM240_EJMB_英文整合工作稿_20261019.md"
RECORD = Path(__file__).with_name("integration_record.json")
NAMES = [
    "第一篇论文_第1章引言草稿_20261017.md",
    "第一篇论文_第2章方法草稿_20261017.md",
    "第一篇论文_第3章验证草稿_20261017.md",
    "第一篇论文_第4章结果I草稿_20261018.md",
    "第一篇论文_第5章_对比对象选择草稿_20261018.md",
    "SIM240_PoF定向写作工作稿_20261019.md",
]
sources = {name: (REPORTS / name).read_bytes() for name in NAMES}
texts = {name: raw.decode("utf-8") for name, raw in sources.items()}
hashes = {name: hashlib.sha256(raw).hexdigest() for name, raw in sources.items()}


def between(text, start, end):
    return text.split(start, 1)[1].split(end, 1)[0].strip()


def english_sections(text, heading, stop):
    """Preserve structural headings and only the explicitly marked EN blocks."""
    text = text.split(heading, 1)[1].split(stop, 1)[0]
    lines = []
    mode = None
    for line in text.splitlines():
        if re.fullmatch(r"#{2,4} EN", line):
            mode = "en"
            continue
        if re.fullmatch(r"#{2,4} 中文", line):
            mode = "zh"
            continue
        if line.startswith("#"):
            lines.append(line.split("／", 1)[0].rstrip())
            mode = None
        elif mode == "en":
            lines.append(line)
    return "\n".join(lines).strip()


intro = between(texts[NAMES[0]], "## I. INTRODUCTION", "## 参考文献")
intro = re.sub(r"^### ¶.*\n", "", intro, flags=re.M)
intro = "\n".join(line for line in intro.splitlines() if not line.startswith("> **【图 1 已就位】**"))
methods = english_sections(texts[NAMES[1]], "## II. PROBLEM STATEMENT AND METHODS", "## 本章新增参考文献")
verification = english_sections(texts[NAMES[2]], "## III. VERIFICATION", "## 本章新增参考文献")
refinement = between(texts[NAMES[2]].split("## G2.", 1)[1], "### EN", "### 中文")
verification += "\n\n### G2. Added geometry-specific refinement checks\n\n" + refinement
resolved = between(texts[NAMES[3]], "### EN", "## 中文")
resolved = re.sub(r"^#### ", "### ", resolved, flags=re.M)
comparison = between(texts[NAMES[4]], "## EN", "## 中文")
abstract = between(texts[NAMES[5]], "## Abstract\n\n", "## 摘要中文释义")
conclusion = between(texts[NAMES[5]], "## 结论段英文候选\n\n", "## 章节与图件写作任务")
conclusion = conclusion.replace(" [draft:JC05]", "")

# Two wording corrections in this derived candidate only; no numerical alteration.
old1 = "The steady flow in Eq. (3) is solved directly in the resolved geometry"
new1 = "The fixed-gap cell flow used to determine the coefficients in Eq. (3) is solved in the resolved geometry"
assert old1 in methods
methods = methods.replace(old1, new1, 1)
old2 = "and it is a standard choice for steady Stokes flow, where accuracy is limited by the boundary treatment rather than by the collision model."
assert old2 in methods
methods = methods.replace(old2, "The present work does not separately quantify the bulk and boundary contributions to the numerical error.", 1)
# Repair the preceding conjunction left after shortening the original compound sentence.
methods = methods.replace(
    "it places the solution away from the stability boundary at $\\tau\\to\\tfrac12$, The present work",
    "it places the solution away from the stability boundary at $\\tau\\to\\tfrac12$. The present work",
)

references = {}
for name in NAMES[:3]:
    for line in texts[name].splitlines():
        match = re.match(r"\| \[(\d+)\] \| (.*?) \| (.*?) \|", line)
        if match:
            number, entry, doi = match.groups()
            # Chapter 1 also describes the associated thesis in its working ledger.
            # Retain only the cited journal record in this candidate bibliography.
            entry = entry.split("；", 1)[0]
            references[int(number)] = entry + (". DOI: " + doi if doi.startswith("10.") else ".")
assert sorted(references) == list(range(1, 23))
bibliography = "\n\n".join(f"[{n}] {references[n]}" for n in sorted(references))

banner = """# EJMB 英文整合工作稿（2026-10-19）

**作者与导师审阅稿；submission_ready=false。** 当前按用户授权的推荐，以European Journal of Mechanics – B/Fluids为写作主目标，常规Research Article。2025公开资料列工程技术大类三区，校方最终口径待核。选择依据见同日选刊报告顶部更新。

本文件把现有五章的英文正文整合为一份连续工作稿，补摘要与结论；原章、原始结果、V2和证据台账保持。沿用已有科学结论，不将整合操作当重新数值验收。正文的罗马章节、方程/表号及参考文献编号沿用原章，尚未声称符合EJMB现行格式；该刊作者指南本轮访问受403限制。文献元数据沿用原台账，作者仍需核准。

**当前待完成**：图件尚未嵌入并逐一核准；第V.C节的图9/10数据链与主链/敏感性标签仍待独立检查，不纳入本版摘要的定量承诺；历史构建来源绑定、全域数值不确定度及经验关系的独立预测检验仍有已披露限制。作者、单位、基金、贡献、利益冲突、数据可用性及AI使用声明须据实补齐。未投稿或联系期刊。

以下英文为候选主稿；本页中文说明、来源记录和验证待办不进入投稿正文。

---

# Directional transport in confined rectangular grooves: errors and empirical correction of a local cubic-law closure

## Abstract

"""

draft = (
    banner + abstract + "\n\n"
    + "## I. INTRODUCTION\n\n" + intro + "\n\n"
    + "## II. PROBLEM STATEMENT AND METHODS\n\n" + methods + "\n\n"
    + "## III. NUMERICAL VERIFICATION AND LIMITATIONS\n\n" + verification + "\n\n"
    + "## IV. DIRECTIONAL TRANSPORT IN THE RESOLVED GEOMETRY\n\n" + resolved + "\n\n"
    + "## V. CLOSURE DISCREPANCIES, EMPIRICAL CORRECTION AND MODEL IMPLICATIONS\n\n" + comparison + "\n\n"
    + "## VI. CONCLUSIONS\n\n" + conclusion + "\n\n"
    + "## REFERENCES\n\n" + bibliography + "\n"
)
draft = re.sub(r"\n(?:---\n\n)+(?=## )", "\n\n", draft)
for name, original_hash in hashes.items():
    assert hashlib.sha256((REPORTS / name).read_bytes()).hexdigest() == original_hash, name

body = draft.split("# Directional transport", 1)[1]
assert not re.search(r"[\u4e00-\u9fff]", body), "Unexpected Chinese text in English manuscript body"
cited = {int(n) for group in re.findall(r"\[([\d, ]+)\]", body.split("## REFERENCES", 1)[0]) for n in group.replace(" ", "").split(",")}
assert cited <= set(references), sorted(cited - set(references))
assert len(abstract.split()) <= 250
OUT.write_text(draft, encoding="utf-8")
record = {
    "date": "2026-10-19",
    "target_journal": "European Journal of Mechanics - B/Fluids",
    "article_type": "Research Article working draft",
    "submission_ready": False,
    "human_author_approval": False,
    "new_simulation": False,
    "new_numerical_gate": False,
    "source_hashes": hashes,
    "source_files_unchanged": True,
    "bibliography_records": len(references),
    "cited_reference_numbers": sorted(cited),
    "missing_cited_references": sorted(cited - set(references)),
    "abstract_words": len(abstract.split()),
    "main_text_whitespace_words": len(body.split()),
    "output": str(OUT.relative_to(ROOT)),
    "output_sha256": hashlib.sha256(OUT.read_bytes()).hexdigest(),
    "local_wording_changes": [
        "Distinguish the fixed-gap cell flow solved by LBM from the macroscopic Reynolds equation.",
        "Remove an unsupported universal attribution of numerical accuracy to boundary treatment; retain the missing bulk/boundary error decomposition.",
    ],
    "unresolved": [
        "Figures are not embedded or revalidated in this integration.",
        "Section V.C propagation chain and figures 9/10 require independent checking.",
        "Full methods and historical source/build provenance acceptance remain incomplete.",
        "Journal-specific guide unavailable (403); final format and submission declarations pending.",
        "Human review of scientific claims, sources, authorship and declarations pending.",
    ],
}
RECORD.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({k: v for k, v in record.items() if k != "source_hashes"}, ensure_ascii=False, indent=2))

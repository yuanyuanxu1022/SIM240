#!/usr/bin/env python3
"""Verify the lower-bound presentation fix (2026-11-09).

Scope: text-only presentation corrections. No new theory, no numerical acceptance.
Checks: changed-line accounting, titles, precision convention, equation numbering,
reference count, anchors, protected-input hashes, MANIFEST row binding, output hashes.
"""
import hashlib
import io
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
FIX = os.path.dirname(os.path.abspath(__file__))

CN = "docs/reports/SIM240_中文稿_导师审阅版_20261022.md"
EN = "docs/reports/SIM240_First_Paper_English_20261028.md"
MANIFEST = "docs/reports/PAPER1_submission_package_20261109/MANIFEST.md"

PROTECTED = "docs/reports/PAPER1_lower_bound_merge_20261109/protected_inputs.json"

checks = []


def add(name, ok, detail=None):
    checks.append({"check": name, "passed": bool(ok), "detail": detail})


def read(p):
    return io.open(os.path.join(ROOT, p), encoding="utf-8").read()


def sha(p):
    h = hashlib.sha256()
    with open(os.path.join(ROOT, p), "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def before(p):
    return os.path.join(FIX, os.path.basename(p) + ".before")


def changed_lines(p):
    """Return (removed, added) line lists between .before and current."""
    old = io.open(before(p), encoding="utf-8").read().splitlines()
    new = read(p).splitlines()
    import difflib
    rem, add = [], []
    for line in difflib.unified_diff(old, new, n=0, lineterm=""):
        if line.startswith("---") or line.startswith("+++"):
            continue
        if line.startswith("-"):
            rem.append(line[1:])
        elif line.startswith("+"):
            add.append(line[1:])
    return rem, add


# 1. changed-line accounting: exactly one title + one statistics paragraph per file
for p, label in ((CN, "CN"), (EN, "EN")):
    rem, added = changed_lines(p)
    add(f"{label} exactly 2 lines removed", len(rem) == 2, {"removed": len(rem)})
    add(f"{label} exactly 2 lines added", len(added) == 2, {"added": len(added)})
    add(f"{label} total line count unchanged", 
        len(io.open(before(p), encoding="utf-8").read().splitlines()) == len(read(p).splitlines()))

# 2. titles
cn = read(CN)
en = read(EN)
add("CN appendix title states both bounds",
    "## 附录 E　理想Stokes模型中局部立方律的上下界性质" in cn)
add("EN appendix title states both bounds",
    "## Appendix E. Upper- and lower-bound properties of the local cubic law" in en)
add("CN old title absent", "上界性质" not in cn)
add("EN old title absent", "Upper-bound property" not in en)

# 3. precision convention (Table 8 note requires two decimals)
for val in ("58.17%", "23.84%", "88.85%", "30.63%"):
    add(f"CN two-decimal {val}", val in cn)
    add(f"EN two-decimal {val}", val in en)
for bad in ("58.2%", "23.8%", "88.8%", "30.6%"):
    add(f"CN one-decimal {bad} removed", bad not in cn)
    add(f"EN one-decimal {bad} removed", bad not in en)
add("CN states same statistic as Table 8", "与表8的原始平均绝对偏差为同一统计量" in cn)
add("EN states same statistic as Table 8", "same quantities as the original-law mean absolute discrepancies in Table 8" in en)
add("CN table-8 two-decimal rule intact",
    "本表及正文的百分比统一保留两位小数" in cn)
add("EN table-8 two-decimal rule intact",
    "are reported to two decimal places" in en)

# 4. equation numbering intact and sequential
for p, label in ((CN, "CN"), (EN, "EN")):
    tags = re.findall(r"\\tag\{(E\d+)\}", read(p))
    add(f"{label} equation tags E1-E8 sequential",
        tags == [f"E{i}" for i in range(1, 9)], tags)

# 5. appendix structure and cross-reference
add("CN E.1 anchor present", '<a id="appendix-e-lower"></a>' in cn)
add("EN E.1 anchor present", '<a id="appendix-e-lower"></a>' in en)
add("CN E.1 heading present", "### E.1 基础下界及其适用范围" in cn)
add("EN E.1 heading present", "### E.1 Elementary lower bound and its scope" in en)
add("CN discussion cross-reference", "[E.1](#appendix-e-lower)" in cn and "式（E8）" in cn)
add("EN discussion cross-reference", "[Appendix E.1](#appendix-e-lower)" in en and "Eq. (E8)" in en)

# 6. key quantities retained
for token in ("63", "1.984", "46"):
    add(f"CN retains {token}", token in cn)
    add(f"EN retains {token}", token in en)

# 7. reference count unchanged
def nrefs(text):
    return len(re.findall(r"^\[\d+\]", text, flags=re.M))
add("CN reference count 11", nrefs(cn) == 11, nrefs(cn))
add("EN reference count 11", nrefs(en) == 11, nrefs(en))

# 8. abstract and five conclusions untouched (spot anchors)
add("CN abstract line unchanged",
    read(CN).splitlines()[14] == io.open(before(CN), encoding="utf-8").read().splitlines()[14])
add("EN conclusions block unchanged",
    [l for l in en.splitlines() if l.startswith("**1.**")] ==
    [l for l in io.open(before(EN), encoding="utf-8").read().splitlines() if l.startswith("**1.**")])

# 9. protected inputs unchanged
prot = json.load(open(os.path.join(ROOT, PROTECTED), encoding="utf-8"))
items = prot.get("files", prot) if isinstance(prot, dict) else prot
bad = []
if isinstance(items, dict):
    it = items.items()
else:
    it = [(x["path"], x["sha256"]) for x in items]
count = 0
for k, v in it:
    count += 1
    if not isinstance(v, str):
        continue
    if not os.path.exists(os.path.join(ROOT, k)) or sha(k) != v:
        bad.append(k)
add("23 protected inputs unchanged", count == 23 and not bad, {"count": count, "bad": bad})

# 10. MANIFEST rows bind to current files
man = read(MANIFEST)
rows = re.findall(r"^\| (\d) \| `([^`]+)` \| [^|]+ \| [^|]+ \| `([0-9a-f]{16})` \| (\d+) \|", man, flags=re.M)
rows = rows + re.findall(r"^\| (\d) \| `([^`]+)` \| `([0-9a-f]{16})` \| (\d+) \|", man, flags=re.M)
seen = {}
for num, path, h16, nbytes in rows:
    seen[num] = (path, h16, int(nbytes))
missing, mismatch = [], []
for num, (path, h16, nbytes) in seen.items():
    if not os.path.exists(os.path.join(ROOT, path)):
        missing.append(path)
        continue
    if not sha(path).startswith(h16) or os.path.getsize(os.path.join(ROOT, path)) != nbytes:
        mismatch.append({"row": num, "path": path, "manifest": h16, "actual": sha(path)[:16]})
add("MANIFEST 8 rows all bind", len(seen) == 8 and not missing and not mismatch,
    {"rows": len(seen), "missing": missing, "mismatch": mismatch})

# 11. corrective note present in MANIFEST
add("MANIFEST carries 1.1.1 correction note", "1.1.1 复核后修正" in man)

# 12. no stale superseded hash presented as current
add("MANIFEST no longer lists superseded CN hash as current row", "| `7ce3ac6b6e9a87ac` |" not in man)
add("MANIFEST no longer lists superseded EN hash as current row", "| `0554657c43e85df2` |" not in man)

passed = sum(1 for c in checks if c["passed"])
failed = [c for c in checks if not c["passed"]]
out = {
    "task": "Lower-bound presentation fix: two-decimal convention and appendix title",
    "scope": "Text-only presentation. No new theory, no numerical acceptance, no threshold change.",
    "checks_passed": passed,
    "checks_failed": len(failed),
    "checks": checks,
    "human_final_scientific_approval": "not asserted",
    "submission_ready": False,
}
with io.open(os.path.join(FIX, "verification.json"), "w", encoding="utf-8") as fh:
    json.dump(out, fh, ensure_ascii=False, indent=2)
with io.open(os.path.join(FIX, "output_hashes.json"), "w", encoding="utf-8") as fh:
    json.dump({p: sha(p) for p in (CN, EN, MANIFEST)}, fh, ensure_ascii=False, indent=2)

print(f"passed {passed}, failed {len(failed)}")
for c in failed:
    print("  FAIL:", c["check"], c.get("detail"))
sys.exit(0 if not failed else 1)

"""Read-only numerical reconciliation; writes only this revision's audit artifacts.

Does not run OpenLB or either fitting program. Does not claim optimization
reproduction, human approval, full manuscript verification or Gate release.
"""
from pathlib import Path
import csv
import difflib
import hashlib
import json
import math
import re
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
AUDIT = ROOT / "docs/reports/SIM240_single_phase_audit_20261018/evidence.json"
SKILL = Path("/home/dell/.codex/skills/scientific-writing/scripts")
SOURCE_PATHS = {
    "E001": "docs/reports/SIM240_single_phase_audit_20261018/evidence.json",
    "E002": "docs/reports/SIM240_single_phase_audit_20261018/REPORT.md",
    "E003": "CASE/D_series/D2_groove_error_map/scripts/fit_correction.py",
    "E004": "docs/reports/修正公式重拟合_又稳又好听_20261017.md",
    "E006": "CASE/D_series/D2_groove_error_map/analysis_fit_v2.py",
    "E007": "CASE/D_series/D2_groove_error_map/results/analysis/V2_FIT_REPORT.md",
}

def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def save_json(name, value):
    (HERE / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")

def read_k(p):
    values = {}
    for line in p.read_text().splitlines():
        key, sep, value = line.partition("=")
        if sep:
            values[key.strip()] = value.strip()
    return float(values["Keff_m3"])

def csv_out(name, rows):
    with (HERE / name).open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

e = json.loads(AUDIT.read_text())
rows = []
for r in e["records"]:
    if r["group"] != "map":
        continue
    h, d, direction = r["h"], r["d"], r["direction"]
    result_path = ROOT / r["path"] / "steady/result.txt"
    kd = read_k(result_path)
    assert kd == r["K"], str(result_path)
    km = ((h**3 + (h+d)**3) / 24 if direction == "P"
          else (h+d)**3 * h**3 / (6*((h+d)**3+h**3))) * 1e-27
    f1 = (1/(1+1.7207*(d/(h+d/2))**1.8046) if direction == "P"
          else 1/(1+0.5276*(d/120)**0.8259))
    f2 = (1/(1+1.7685*(d/120)**1.6331) if direction == "P"
          else 1/(1+0.4900*(d/120)**0.6990))
    raw, old, new = [(km*f/kd-1)*100 for f in (1, f1, f2)]
    for actual, key in ((raw,"E_pct"), (old,"old_residual_pct"),
                        (new,"proposed_residual_pct")):
        assert math.isclose(actual, r[key], abs_tol=1e-9), (h,d,direction,key)
    group = ("h25" if h == 25 else "d75" if d == 75 else
             "d120" if d == 120 else "calibration")
    rows.append(dict(h_nm=h, d_nm=d, direction=direction, group=group,
                     K_DNS_m3=kd, K_model_m3=km, E_pct=raw,
                     V1_rounded_residual_pct=old, V2_rounded_residual_pct=new,
                     result_path=str(result_path.relative_to(ROOT)),
                     result_sha256=digest(result_path)))
assert len(rows) == 36 and len({(r["h_nm"],r["d_nm"]) for r in rows}) == 18
csv_out("map36_evidence.csv", rows)
groups = []
for group in ("calibration","d75","d120","h25"):
    for direction in ("P","T"):
        part = [r for r in rows if r["group"] == group and r["direction"] == direction]
        groups.append(dict(group=group, direction=direction, geometries=len(part),
            V1_max_abs_pct=max(abs(r["V1_rounded_residual_pct"]) for r in part),
            V2_max_abs_pct=max(abs(r["V2_rounded_residual_pct"]) for r in part)))
csv_out("correction_groups.csv", groups)

# Only evaluate exported coefficients. The optimization itself is NOT run.
params_path = ROOT/"CASE/D_series/D2_groove_error_map/results/analysis/v2_fit_params.csv"
reported_residuals = ROOT/"CASE/D_series/D2_groove_error_map/results/analysis/v2_residuals.csv"
params = list(csv.DictReader(params_path.open()))
fit_checks = []
for p in params:
    direction = "P" if p["direction"] == "parallel" else "T"
    evaluated = []
    for r in rows:
        if r["direction"] != direction:
            continue
        factor = 1/(1+float(p["a"])*(r["d_nm"]/120)**float(p["b"]))
        residual = (r["K_model_m3"]*factor/r["K_DNS_m3"]-1)*100
        evaluated.append((r,residual))
    for field, predicate in (
        ("max_abs_resid_calib_pct", lambda r:r["group"]=="calibration"),
        ("max_abs_resid_domain_pct",lambda r:r["h_nm"]>=float(p["h_min_nm"])),
        ("max_abs_resid_all_pct",lambda r:True)):
        value = max(abs(v) for r,v in evaluated if predicate(r))
        # Exported a,b have six decimal places; report metrics four places.
        delta = abs(value-float(p[field]))
        assert delta < .001, (p["direction"], p["objective"], field, delta)
        fit_checks.append(dict(direction=direction, objective=p["objective"],
                              field=field, recomputed=value, difference=delta))
    if p["objective"] == "minimax":
        stored = {(int(r["h_nm"]),int(r["d_nm"])):r
                  for r in csv.DictReader(reported_residuals.open())}
        for r,value in evaluated:
            assert abs(value-float(stored[(r["h_nm"],r["d_nm"])][f"E1_{direction}_pct"])) < .001

raw_checked = []
changes = []
for name, previous in e["input_sha256"].items():
    p = ROOT/name
    current = digest(p) if p.is_file() else None
    if current != previous:
        changes.append(dict(path=name, previous=previous, current=current))
    # Protect numerical raw inputs, not concurrently edited derived reports.
    if "/steady/" in name or "/precheck/" in name:
        assert current == previous, "RAW INPUT CHANGED: "+name
        raw_checked.append(name)

sources = []
locators = {
    "E001":"counts, records[group=map], grid, viscosity, angles, conditional_coarse_GCI",
    "E002":"Sections 1-4; limitations A-I; evidence interpretation",
    "E003":"m4/t2; curve_fit calls; original d75 predictions; read only",
    "E004":"Sections 2.1-2.4; rounded proposal coefficients, not validation endorsement",
    "E006":"fit/best_of/load_runs/main; static inspection, not optimization execution",
    "E007":"Fitted coefficients and per-geometry residual tables; evaluated against raw K",
}
for eid, path in SOURCE_PATHS.items():
    sources.append(dict(evidence_id=eid, source_type="software" if path.endswith(".py") else "report",
        title=Path(path).name, authors=[], year=2026, identifiers={},
        locator=path+" :: "+locators[eid], confidentiality="restricted",
        verification=dict(status="unverified", source_opened=True,
                          verified_by=None, verified_on=None)))
sources.append(dict(evidence_id="E005", source_type="preprint",
    title="Scientific Agent Skills: A Library of Procedural Knowledge for Research Agents",
    authors=["Timothy Kassis","Vinayak Agarwal","Yuhuan He","Darshil Patel","Aubrey M. Brueckner"],
    year=2026, identifiers={"doi":"10.48550/arXiv.2609.00065",
                           "url":"https://arxiv.org/abs/2609.00065"},
    locator="arXiv v2 metadata, revised 2026-09-02; agent opened 2026-10-18; workflow only",
    confidentiality="public", verification=dict(status="unverified",source_opened=True,
                                                verified_by=None,verified_on=None)))
save_json("source_manifest.json",dict(schema_version="1.0", sources=sources))

claim_rows = []
section = ""
for line in (HERE/"CORE_CLAIMS.md").read_text().splitlines():
    if line.startswith("#"):
        section = line.lstrip("# ")
    ids = re.findall(r"\[claim:(C\d+)\]",line)
    if not ids:
        continue
    assert len(ids)==1, line
    ev = re.search(r"\[evidence:([E\d,]+)\]",line)
    assert ev, ids
    clean = re.sub(r"\[(?:claim:[^]]+|evidence:[^]]+|@E\d+)\]","",line)
    claim_rows.append(dict(claim_id=ids[0],section=section,claim_kind="interpretive",
        claim_text_sha256=hashlib.sha256(" ".join(clean.split()).encode()).hexdigest(),
        evidence_ids=ev[1].replace(",",";"), verification_status="unverified",
        uncertainty="not_estimated",analysis_intent="descriptive"))
assert len({r["claim_id"] for r in claim_rows})==len(claim_rows)
csv_out("claims.csv",claim_rows)

tool_reports = {}
for name, args in (
    ("source_schema",["validate_manifest.py",str(HERE/"source_manifest.json"),"--kind","source"]),
    ("claim_audit",["audit_claims.py",str(HERE/"CORE_CLAIMS.md"),
                    str(HERE/"claims.csv"),str(HERE/"source_manifest.json")]),
    ("reference_syntax",["check_references.py",str(HERE/"source_manifest.json")])):
    out = subprocess.run([sys.executable,str(SKILL/args[0]),*args[1:]],
                         capture_output=True,text=True)
    tool_reports[name] = dict(exit_code=out.returncode,stdout=out.stdout,stderr=out.stderr)
save_json("skill_checks.json",tool_reports)
assert tool_reports["source_schema"]["exit_code"] == 0
assert tool_reports["reference_syntax"]["exit_code"] == 0
claim_issues = json.loads(tool_reports["claim_audit"]["stdout"])["issues"]
expected_pending = {"CLAIM_NOT_VERIFIED", "UNVERIFIED_CITATION_MARKER",
                    "UNVERIFIED_CLAIM_EVIDENCE"}
assert {x["code"] for x in claim_issues} <= expected_pending
# Pending human checks remain errors in the original skill output.
core = (HERE/"CORE_CLAIMS.md").read_text()
for g in groups:
    assert f'{g["V1_max_abs_pct"]:.3f}' in core
    assert f'{g["V2_max_abs_pct"]:.3f}' in core
front = (ROOT/"docs/reports/PoF投稿包_前置材料与格式对照_20261017.md").read_text()
abstract = front.split("### 2.3 Abstract",1)[1].split("### 2.4 Keywords",1)[0]
abstract_line = next(x[2:] for x in abstract.splitlines() if x.startswith("> "))
assert len(abstract_line.split()) <= 250
assert f'{len(abstract_line.split())}个空白分隔词' in abstract
assert all(x in abstract_line for x in ("10.505%","6.921%","−18.705%","retrospective"))

files = list(ROOT.glob("docs/reports/第一篇论文_第[123]章*20261017.md"))
files += [ROOT/"docs/reports/PoF投稿包_前置材料与格式对照_20261017.md",
          ROOT/"CASE/plans/SIM240_第一篇范围重定位_纯液体单相_20261016.md"]
diffs = []
for p in files:
    before = HERE/"before"/p.name
    if before.exists():
        diffs.extend(difflib.unified_diff(before.read_text().splitlines(True),
                     p.read_text().splitlines(True),fromfile="before/"+p.name,
                     tofile=str(p.relative_to(ROOT))))
(HERE/"manuscript_changes.diff").write_text("".join(diffs))
report = dict(scope="arithmetic, raw-input stability and core-claim metadata only",
    map_rows=len(rows), groups=groups, coefficient_checks=fit_checks,
    raw_inputs_unchanged=len(raw_checked), changed_since_prior_audit=changes,
    source_sha256={eid:digest(ROOT/path) for eid,path in SOURCE_PATHS.items()},
    additional_fit_output_sha256={str(p.relative_to(ROOT)):digest(p)
                                 for p in (params_path,reported_residuals)},
    manuscript_sha256={str(p.relative_to(ROOT)):digest(p) for p in files},
    core_claims_sha256=digest(HERE/"CORE_CLAIMS.md"), claims_registered=len(claim_rows),
    abstract_word_count=len(abstract_line.split()),
    skill_claim_audit_human_review_pending=True, core_hash_mapping_errors=0,
    optimizer_rerun=False, solver_rerun=False, formal_gate_release=False,
    human_verified=False, submission_ready=False,
    note="V2 adopted by explicit user reply; data-informed, not independent final validation.")
save_json("validation.json",report)
print(json.dumps({k:report[k] for k in ("map_rows","raw_inputs_unchanged",
    "claims_registered","optimizer_rerun","solver_rerun","submission_ready")},indent=2))

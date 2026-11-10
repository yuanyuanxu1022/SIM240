#!/usr/bin/env python3
"""Bind caption drafts to machine-checked sources without inventing human approval."""
import csv
import hashlib
import json
from pathlib import Path
import sys
import argparse

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, "/home/dell/.codex/skills/scientific-writing/scripts")
from audit_claims import claim_text_hash

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--regenerate-generated-registry", action="store_true")
args = parser.parse_args()

entries = [
    ("E001", ROOT / "figures/paraview/D2_h75_d100_dx5_PT_publication_20261017_v1/rendered_v4/render_manifest.json",
     "Existing P/T fields and source-backed speed rendering", "inputs, geometry_nm, color, panels, sampling_note"),
    ("E002", HERE / "rendered/render_manifest.json", "T dissipation sample-footprint rendering", "range, liquid_samples, method, sampling, original_inputs_and_evidence"),
    ("E003", HERE / "profile_validation.json", "User CSV selection and reprobe against original P field", "profiles: positions, counts, exclusions, velocity differences"),
    ("E004", HERE / "figures_v2/layout_manifest.json", "Final four-figure layout and export record", "figures: source references, units, axes and text; final PNG/PDF/SVG"),
    ("E005", ROOT / "docs/reports/paraview_dissipation_state_audit_20261017/draft_v1_review.json",
     "User GUI draft pipeline review", "threshold, clip, coordinate bounds, preservation, remaining"),
]
sources = []
for evidence_id, path, title, locator in entries:
    sources.append({
        "evidence_id": evidence_id, "source_type": "other", "title": title,
        "authors": [], "year": None, "confidentiality": "confidential",
        "identifiers": {"doi": "", "url": "", "isbn": "", "pmid": "", "pmcid": ""},
        "locator": locator, "local_path": str(path),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "verification": {"source_opened": False, "status": "unverified", "verified_by": "", "verified_on": ""},
        "machine_check": {"checked_by": "Codex assistant and local scripts", "date": "2026-10-17",
                          "opened_and_checked_locally": True,
                          "note": "Machine/AI checks do not constitute the human verification required for manuscript approval."},
    })
sources.append({
    "evidence_id": "E006", "source_type": "other",
    "title": "Scientific Agent Skills: A Library of Procedural Knowledge for Research Agents",
    "authors": ["Timothy Kassis", "Vinayak Agarwal", "Yuhuan He", "Darshil Patel", "Aubrey M. Brueckner"],
    "year": 2026, "confidentiality": "public",
    "identifiers": {"doi": "10.48550/arXiv.2609.00065", "url": "https://arxiv.org/abs/2609.00065", "isbn": "", "pmid": "", "pmcid": ""},
    "locator": "arXiv abstract page; record revised 2026-09-02; no journal reference listed on checked page",
    "verification": {"source_opened": False, "status": "unverified", "verified_by": "", "verified_on": ""},
    "machine_check": {"checked_by": "Codex assistant via public arXiv page", "date": "2026-10-17", "opened_and_checked_locally": False},
})
caption = (HERE / "CAPTIONS.md").read_text()
annotated, claims, section = [], [], ""
for line in caption.splitlines():
    if line.startswith("## "):
        section = line[3:]
    if line.startswith(("ZH:", "EN:", "ALT:", "ZH_COMMON:", "EN_COMMON:")):
        if section.startswith("Figure 1") or section.startswith("Figure 2"):
            ids = "E001;E004"
        elif section.startswith("Figure 3"):
            ids = "E003;E004"
        elif section.startswith("Figure 4"):
            ids = "E002;E004"
        else:
            ids = "E001;E002;E003;E004"
        claim_id = "C" + str(len(claims) + 1).zfill(3)
        tagged = line + " [claim:" + claim_id + "] [evidence:" + ids.replace(";", ",") + "]"
        claims.append({"claim_id": claim_id, "section": section, "claim_kind": "factual",
                       "claim_text_sha256": claim_text_hash(tagged), "evidence_ids": ids,
                       "verification_status": "unverified", "uncertainty": "not_estimated",
                       "analysis_intent": "descriptive"})
        annotated.append(tagged)
    else:
        annotated.append(line)

for name in ("source_manifest.json", "claims.csv", "CAPTIONS_AUDIT.md", "source_locations.json"):
    if (HERE / name).exists() and not args.regenerate_generated_registry:
        raise RuntimeError("Refusing to overwrite existing caption provenance: " + name)
locations = {s["evidence_id"]: {k: v for k, v in s.items()
             if k in ("local_path", "sha256", "machine_check")} for s in sources}
allowed = {"evidence_id", "source_type", "title", "authors", "year", "confidentiality",
           "identifiers", "locator", "verification"}
schema_sources = [{k: v for k, v in s.items() if k in allowed} for s in sources]
for s in schema_sources:
    if s["confidentiality"] == "confidential":
        s["confidentiality"] = "restricted"  # Local unpublished sources, no external transfer.
(HERE / "source_manifest.json").write_text(json.dumps({"schema_version": "1.0", "sources": schema_sources}, indent=2, ensure_ascii=False) + "\n")
(HERE / "source_locations.json").write_text(json.dumps({"sources": locations,
    "human_verification_pending": True, "submission_ready": False,
    "schema_fix": "Machine hashes/paths are in this separate local sidecar, not in the controlled source schema. Earlier schema check reported 23 format errors; no scientific values were changed."}, indent=2, ensure_ascii=False) + "\n")
with (HERE / "claims.csv").open("w", newline="") as stream:
    writer = csv.DictWriter(stream, fieldnames=list(claims[0]))
    writer.writeheader()
    writer.writerows(claims)
(HERE / "CAPTIONS_AUDIT.md").write_text("\n".join(annotated) + "\n")
assert len(claims) == 14
assert all(claim_text_hash(line) == next(c["claim_text_sha256"] for c in claims if "[claim:" + c["claim_id"] + "]" in line)
           for line in annotated if "[claim:" in line)
print(json.dumps({"sources": len(sources), "caption_claims": len(claims),
                  "hash_bindings_checked": True, "human_verification": "pending", "submission_ready": False}))

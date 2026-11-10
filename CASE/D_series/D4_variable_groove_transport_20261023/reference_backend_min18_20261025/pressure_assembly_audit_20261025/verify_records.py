"""Independent standard-library audit of nine recorded assemblies; no backend import."""

import csv
import hashlib
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
REPO = ROOT.parents[3]
RECORD = HERE / "evidence/assembly_all9.json"


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1048576), b""):
            h.update(block)
    return h.hexdigest()


def verify():
    data = json.loads(RECORD.read_text())
    rows = list(csv.DictReader((ROOT / "protocol/benchmarks18.csv").open(
        encoding="utf-8-sig", newline="")))
    wanted = [r["planned_id"] for r in rows if r["direction_or_field"] in {"T", "mixed"}]
    assert len(wanted) == 9 and data["status"] == "COMPLETE"
    assert data["planned_ids"] == wanted
    assert len(data["records"]) == 9
    for relative, expected in data["input_sha256"].items():
        assert sha256(ROOT / relative) == expected, relative
    by_id = {}
    for record in data["records"]:
        assert record["exit_code"] == 0 and not record["stderr"], record["planned_id"]
        x = record["result"]
        ident = record["planned_id"]
        assert ident in wanted and ident not in by_id and x["planned_id"] == ident
        by_id[ident] = x
        assert x["matrix_shape"][0] == x["matrix_shape"][1] > 0
        assert x["matrix_nnz"] > x["matrix_shape"][0]
        assert x["matrix_values_finite"] and x["rhs_values_finite"]
        assert x["matrix_symmetric_1e-11"] and x["petsc_nullspace_test_reduced"]
        assert x["rhs_L2"] > 0 and math.isfinite(x["rhs_L2"])
        assert x["pressure_slave_dofs"] > 0
        assert x["original_full_pressure_candidate"]["An_over_A_Frobenius"] > 1e-10
        assert x["reduced_pressure_candidate"]["An_over_A_Frobenius"] < 1e-10
        assert x["reduced_pressure_candidate"]["n_dot_b_over_b_L2"] < 1e-10
        assert x["pressure_rhs_max_abs"] == 0 and x["rhs_projection_change_L2"] == 0
        assert x["solver_called"] is False and x["field_computed"] is False
    for a, b in (("B0MIN_FLAT_T_d1p25", "B0MIN_FLAT_T_d1p25_ALG"),
                 ("B0MIN_MMS_mixed_N32", "B0MIN_MMS_mixed_N32_ALG")):
        for key in ("mesh_sha256", "periodic_mapping_sha256", "matrix_csr_sha256",
                    "rhs_sha256_before_projection"):
            assert by_id[a][key] == by_id[b][key], (a, b, key)
    protected = json.loads((REPO / "docs/reports/G4_derivation_source_audit_20261025/"
                            "protected_inputs.json").read_text())
    altered = [p for p, expected in protected.items() if not Path(p).is_file() or sha256(p) != expected]
    prior = ROOT / "mesh_periodic_pressure_20261025"
    prior_hashes = json.loads((prior / "evidence/artifact_hashes.json").read_text())
    prior_altered = [p for p, expected in prior_hashes.items()
                     if not (prior / p).is_file() or sha256(prior / p) != expected]
    verdict = {"status": "PASS" if not altered and not prior_altered else "FAIL",
               "nine_mixed_assemblies_checked": len(by_id),
               "full_candidate_fails": 9,
               "reduced_candidate_passes": 9,
               "rhs_compatible": 9,
               "repeat_matrix_rhs_exact": 2,
               "protected_paths_checked": len(protected), "protected_altered": altered,
               "prior_package_files_checked": len(prior_hashes), "prior_package_altered": prior_altered,
               "solver_called": False}
    target = HERE / "evidence/independent_record_review.json"
    target.write_text(json.dumps(verdict, indent=2, ensure_ascii=False) + "\n")
    if verdict["status"] != "PASS":
        raise RuntimeError("INDEPENDENT_RECORD_REVIEW_FAILED")
    return verdict


if __name__ == "__main__":
    print(json.dumps(verify(), ensure_ascii=False))

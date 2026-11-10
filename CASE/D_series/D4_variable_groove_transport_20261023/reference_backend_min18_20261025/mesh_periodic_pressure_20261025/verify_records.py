#!/usr/bin/env python3
"""Independent arithmetic review of saved actual-interface records; no backend import."""

import csv
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
AUDIT = HERE / "evidence/actual_interface_all18.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check():
    data = json.loads(AUDIT.read_text())
    with (ROOT / "protocol/benchmarks18.csv").open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    planned = {r["planned_id"]: r for r in rows}
    assert len(rows) == len(planned) == 18
    assert data["planned_count"] == data["accepted_count"] == 18
    assert {c["planned_id"] for c in data["cases"]} == set(planned)
    for relative, expected in data["input_sha256"].items():
        assert sha(ROOT / relative) == expected, relative
    assert not data["matrix_assembled"] and not data["rhs_assembled"]
    assert not data["solver_called"] and data["actual_run_id"] is None
    assert data["NUMERICAL_GATE"] == "NOT_EVALUATED" and not data["RESULT_PASS"]
    assert data["geometry_PASS"] is None and data["prediction_permission"] == "HOLD"
    distinct_meshes = {}
    total_pairs = 0
    for case in data["cases"]:
        r = planned[case["planned_id"]]
        nx, nz = int(r["nx"]), int(r["nz"])
        mixed = r["direction_or_field"] in {"T", "mixed"}
        period = 3.2 if r["problem"] == "flat75" else 2.0
        assert case["actual_triangles"] == 2*nx*nz
        assert case["actual_vertices"] == (nx+1)*(nz+1)
        assert case["actual_right_facets"] == case["actual_left_facets"] == nz
        assert case["actual_raw_dofs"] == (2 if mixed else 1)*(2*nx+1)*(2*nz+1) + (nx+1)*(nz+1)*(1 if mixed else 0)
        assert case["period_hat"] == period and case["height_hat"] == 1
        pairs = case["periodic_link_audit"]["pairs"]
        expected_count = 2*(2*nz-1)+(nz+1) if mixed else 2*nz-1
        assert len(pairs) == case["periodic_link_audit"]["slave_count"] == expected_count
        assert case["periodic_link_audit"]["max_pair_coordinate_error"] < 1e-11
        assert case["periodic_link_audit"]["max_coefficient_error"] < 1e-11
        digest = hashlib.sha256(json.dumps(pairs, sort_keys=True,
                                           separators=(",", ":")).encode()).hexdigest()
        assert digest == case["periodic_link_audit"]["mapping_sha256"]
        expected_trace = ({(component, k) for component in ((0, 1) if mixed else (0,))
                           for k in range(1, 2*nz)}
                          | ({(-1, 2*k) for k in range(nz+1)} if mixed else set()))
        actual_trace = set()
        slave_ids, master_ids = set(), set()
        for pair in pairs:
            s, m = pair["slave_xz"], pair["master_xz"]
            component = pair["component"]
            assert abs(s[0]-period) < 1e-11 and abs(m[0]) < 1e-11
            assert abs(s[1]-m[1]) < 1e-11 and abs(pair["coefficient"]-1) < 1e-11
            k = round(s[1]*2*nz)
            assert abs(s[1]-k/(2*nz)) < 1e-11
            assert component in (-1, 0, 1)
            if component == -1:
                assert mixed and k % 2 == 0
            else:
                assert 0 < k < 2*nz
            actual_trace.add((component, k))
            slave_ids.add(pair["slave_dof"])
            master_ids.add(pair["master_dof"])
        assert actual_trace == expected_trace
        assert len(slave_ids) == len(master_ids) == expected_count
        if mixed:
            pg = case["pressure_gauge"]
            assert pg["candidate_nullspace_dimension"] == 1
            assert pg["P1_dofs"] == (nx+1)*(nz+1)
            assert abs(pg["nodal_area_weights_sum"]-period) < 1e-11
            assert not pg["matrix_kernel_checked"] and not pg["rhs_compatibility_checked"]
            assert not pg["matrix_nullspace_attached"]
        else:
            assert case["pressure_gauge"] is None
        assert not case["matrix_assembled"] and not case["rhs_assembled"]
        assert not case["solver_called"] and case["actual_run_id"] is None
        key = (period, nx, nz)
        previous = distinct_meshes.setdefault(key, case["actual_mesh_sha256"])
        assert previous == case["actual_mesh_sha256"]
        total_pairs += len(pairs)
    return {"kind": "INDEPENDENT_STATIC_RECORD_REVIEW",
            "all_record_checks_pass": True, "checked_cases": 18,
            "checked_periodic_pairs": total_pairs,
            "unique_geometry_mesh_hashes": len(distinct_meshes),
            "actual_PDE_operator_checked": False,
            "actual_pressure_rhs_checked": False,
            "solver_called": False, "NUMERICAL_GATE": "NOT_EVALUATED"}


if __name__ == "__main__":
    result = check()
    (HERE / "evidence/independent_record_review.json").write_text(
        json.dumps(result, indent=2)+"\n")
    print(json.dumps(result, indent=2))

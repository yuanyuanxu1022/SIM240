"""Actual geometry + artificial fields only; no matrix or solver is created."""
import ast
import hashlib
import importlib.util
import inspect  # Preload stdlib inspect before project inspect.py can shadow it.
import json
from pathlib import Path
import sys
import tempfile

import numpy as np

from bridge import BridgeRejected, build_raw_bundle

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "raw_capture_review_20261025"))
from raw_writer import REQUIRED, write_raw_arrays, sha256  # noqa: E402


def load_interface():
    path = ROOT / "mesh_periodic_pressure_20261025/interface.py"
    spec = importlib.util.spec_from_file_location("d4_adapter_interface_review", path)
    module = importlib.util.module_from_spec(spec)
    mesh_dir = str(path.parent)
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path[:] = [p for p in sys.path if p != mesh_dir]
    if mesh_dir in str(Path(inspect.__file__).resolve()):
        raise RuntimeError("STDLIB_INSPECT_SHADOWED")
    return module


def fail_for(action, reason):
    try:
        action()
    except BridgeRejected as exc:
        if reason not in str(exc):
            raise
        return
    raise AssertionError("not rejected: " + reason)


def main():
    interface = load_interface()
    preflight = json.loads((ROOT / "solve_entry_review_20261025/evidence/preflight_all9.json").read_text())
    rows = preflight["records"]
    assert len(rows) == 9
    probe = []
    with tempfile.TemporaryDirectory(prefix="d4_actual_mesh_synthetic_field_") as temp:
        for row in rows:
            ident = row["planned_id"]
            item = interface.build_interface(ident)  # Real mesh/MPC; no assembly or solve.
            n = item["mpc"].function_space.dofmap.index_map.size_local
            W = item["mpc"].function_space
            Q, qmap = W.sub(1).collapse()
            rec = np.arange(n, dtype=np.float64) / max(1, n)
            for link in item["stats"]["periodic_link_audit"]["pairs"]:
                rec[link["slave_dof"]] = rec[link["master_dof"]]
            rec[item["wall_bc"].dof_indices()[0]] = 0
            algebraic = rec.copy()
            algebraic[item["mpc"].slaves] = 0
            pressure_raw = rec[np.asarray(qmap[0], dtype=np.int64)].copy()
            weights = item["pressure"]["nodal_area_weights"]
            mean = float(np.dot(weights, pressure_raw) / weights.sum())
            result = {"status": "SYNTHETIC_ADAPTER_TEST_NOT_RESULT",
                      "algebraic_solution_before_backsubstitution": algebraic,
                      "periodic_reconstructed_solution": rec,
                      "pressure_raw_P1": pressure_raw,
                      "pressure_zero_area_mean_P1": pressure_raw - mean}
            bundle = build_raw_bundle(item, result)
            assert set(bundle) == set(REQUIRED)
            dest = write_raw_arrays(Path(temp), ident, bundle,
                                    {"kind": "SYNTHETIC_WRITER_TEST_NOT_RESULT"})
            record = json.loads((dest / "raw_manifest.json").read_text())
            for name, original in bundle.items():
                path = dest / (name + ".npy")
                with path.open("rb") as f:
                    actual = np.load(f, allow_pickle=False)
                assert np.array_equal(actual, original)
                assert sha256(path) == record["files"][path.name]["sha256"]
            if ident == "B0MIN_MMS_mixed_N8":
                fake = dict(result, pressure_raw_P1=pressure_raw + 1)
                fail_for(lambda: build_raw_bundle(item, fake), "PRESSURE_RESULT_MAP_MISMATCH")
                fake = dict(result, status="CLAIMED_PASS")
                fail_for(lambda: build_raw_bundle(item, fake), "UNVERIFIED_RESULT_STATUS_REQUIRED")
            probe.append({"planned_id": ident, "mixed_dofs": n,
                          "velocity_scalar_dofs": len(bundle["velocity_reconstructed_dof_indices"]),
                          "velocity_nodes": len(bundle["velocity_reconstructed_dof_indices"]) // 2,
                          "pressure_dofs": len(bundle["pressure_raw_P1"]),
                          "periodic_pairs": len(bundle["periodic_slave_dofs"]),
                          "raw_files_readback": len(record["files"]),
                          "raw_file_bytes": sum((dest / name).stat().st_size
                                                for name in record["files"]),
                          "artificial_field_only": True})
    for name in ("bridge.py", "audit_no_solve.py"):
        tree = ast.parse((HERE / name).read_text())
        if any(isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
               and node.func.attr == "solve" for node in ast.walk(tree)):
            raise RuntimeError("SOLVE_CALL_IN_BRIDGE_REVIEW")
    source_files = [ROOT / "mesh_periodic_pressure_20261025/interface.py",
                    ROOT / "solver_result_review_20261025/candidate_solver.py",
                    ROOT / "raw_capture_review_20261025/raw_writer.py",
                    ROOT / "protocol/benchmarks18.csv"]
    sources = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
               for p in source_files}
    record = {"status": "PASS_REAL_MESH_SYNTHETIC_FIELD_ONLY", "cases": probe,
              "candidate_result_adapter_structurally_compatible": True,
              "real_solver_output_tested": False, "ksp_created": False,
              "solver_called": False, "formal_run_id": None,
              "source_sha256": sources, "NUMERICAL_GATE": "NOT_EVALUATED",
              "RESULT_PASS": False, "geometry_PASS": None}
    (HERE / "evidence").mkdir(exist_ok=True)
    (HERE / "evidence/bridge_audit.json").write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps({"status": record["status"], "case_count": len(probe),
                      "max_mixed_dofs": max(x["mixed_dofs"] for x in probe),
                      "solver_called": False}))


if __name__ == "__main__":
    main()

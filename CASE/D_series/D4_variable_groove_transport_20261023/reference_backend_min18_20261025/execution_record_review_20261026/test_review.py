"""Synthetic-only record tests; the frozen solver path is denial-tested."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

import numpy as np

from child_record import ChildRejected, capture_reviewed_case, capture_synthetic_fixture
from failure_archive import ArchiveRejected, save_failure
from recorded_solver import (CandidateRejected, DiagnosticGMRES, check_release,
                             solve_prepared_mixed_system)

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def rejected(action, typ, word):
    try:
        action()
    except typ as exc:
        assert word in str(exc), (word, exc)
        return
    raise AssertionError("expected rejection: " + word)


def main():
    checks = []
    with tempfile.TemporaryDirectory(prefix="d4_record_synthetic_") as temp:
        root = Path(temp)
        vector = np.array([1.0, -0.0, np.nan, np.inf], dtype="<f8")
        archive = save_failure(root / "failures", "synthetic_failure", "KSP_SOLVE",
                               RuntimeError("synthetic stopped"), vector,
                               {"history": [1.0, float("nan")], "reason": -3},
                               {"source_sha256": "synthetic-only"})
        saved = np.load(archive / "partial_algebraic_solution_before_backsub.npy",
                        allow_pickle=False)
        assert saved.tobytes() == vector.tobytes()
        failure = json.loads((archive / "failure_manifest.json").read_text())
        assert failure["files"]["partial_algebraic_solution_before_backsub.npy"]["nonfinite_count"] == 2
        assert failure["diagnostics"]["history"][1] == "nan"
        assert failure["NUMERICAL_GATE"] == "NOT_EVALUATED"
        rejected(lambda: save_failure(root / "failures", "synthetic_failure", "KSP_SOLVE",
                 RuntimeError("again"), vector, {}, {}), ArchiveRejected,
                 "FAILURE_ALREADY_ARCHIVED")
        checks.append("PARTIAL_FLOAT64_BITS_DIAGNOSTICS_HASH_AND_NO_OVERWRITE")
        no_vector = save_failure(root / "failures", "before_vector", "KSP_CONFIGURATION",
                                 RuntimeError("before vector"), None, {}, {})
        assert json.loads((no_vector / "failure_manifest.json").read_text())["algebraic_vector_available"] is False
        checks.append("FAILURE_BEFORE_VECTOR_RECORDED_HONESTLY")
        fixture = HERE / "synthetic_child.py"
        run = capture_synthetic_fixture(root / "runs", "synthetic_exit7", fixture)
        record = json.loads((run / "capture_manifest.json").read_text())
        assert record["independent_exit_code"] == 7
        assert record["per_direct_child_rusage"]["direct_child_peak_RSS_KiB"] > 0
        assert record["inputs_unchanged"] is True
        assert (run / "independent_exit_code.txt").read_text() == "7\n"
        assert (run / "stdout.log").read_text() == "synthetic stdout complete\n"
        assert (run / "stderr.log").read_text() == "synthetic stderr complete\n"
        assert (run / "partial_synthetic.bin").read_bytes() == b"partial fixture retained\n"
        assert record["all_output_files_before_manifest"]["partial_synthetic.bin"]["sha256"] == sha(run / "partial_synthetic.bin")
        for name, entry in record["files"].items():
            assert sha(run / name) == entry["sha256"]
        assert record["output_dir_bytes_before_manifest"] >= (run / "partial_synthetic.bin").stat().st_size
        checks.append("PER_DIRECT_CHILD_WAIT4_RSS_EXIT7_LOGS_AND_PARTIAL_OUTPUT")
        run_two = capture_synthetic_fixture(root / "runs", "synthetic_exit7_second", fixture)
        record_two = json.loads((run_two / "capture_manifest.json").read_text())
        assert record_two["independent_exit_code"] == 7
        assert record_two["per_direct_child_rusage"]["direct_child_peak_RSS_KiB"] > 0
        assert record_two["run_id"] != record["run_id"]
        checks.append("TWO_DISTINCT_DIRECT_CHILD_RESOURCE_RECORDS")
        rejected(lambda: capture_synthetic_fixture(root / "runs", "synthetic_exit7", fixture),
                 ChildRejected, "RUN_ID_ALREADY_EXISTS")
        checks.append("PROCESS_NO_OVERWRITE")
        planned = "B0MIN_MMS_mixed_N8"
        denied_dir = root / "denied_real"
        rejected(lambda: capture_reviewed_case(denied_dir, "real_denied", planned,
                 ["/usr/bin/false"], {str(fixture): sha(fixture)},
                 {"status": "APPROVED_FOR_RECTANGLE_SOLVE"}),
                 ChildRejected, "FROZEN_PLAN_DENIES_EXECUTION")
        assert not denied_dir.exists()
        rejected(lambda: check_release({"item": {"plan": {"execution_authorized": False}}},
                 DiagnosticGMRES(1e-10, 1e-10, 100, 20), None),
                 CandidateRejected, "FROZEN_WHITELIST_DENIES_SOLVE")
        rejected(lambda: solve_prepared_mixed_system(
                 {"item": {"plan": {"execution_authorized": False}}},
                 DiagnosticGMRES(1e-10, 1e-10, 100, 20), None,
                 lambda *_: None), CandidateRejected, "FROZEN_WHITELIST_DENIES_SOLVE")
        checks.append("REAL_PROCESS_AND_KSP_GATES_DENY_BEFORE_OUTPUT_OR_SOLVER")
        worker = HERE / "reviewed_worker.py"
        response = subprocess.run([sys.executable, "-B", str(worker), "--planned-id", planned],
                                  capture_output=True, text=True, check=False)
        assert response.returncode == 2 and "FROZEN_PLAN_DENIES_EXECUTION" in response.stderr
        checks.append("WORKER_CLI_DENIES_FROZEN_PLAN_BEFORE_BACKEND_ASSEMBLY")
    report = {"status": "PASS_SYNTHETIC_AND_DENIAL_ONLY", "checks": checks,
              "real_solver_called": False, "formal_run_id": None,
              "NUMERICAL_GATE": "NOT_EVALUATED", "RESULT_PASS": False,
              "geometry_PASS": None}
    (HERE / "evidence/synthetic_tests.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()

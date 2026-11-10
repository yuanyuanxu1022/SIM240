"""Synthetic-only roundtrip and negative controls. Never imports a solver."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile

import numpy as np

from process_capture import CaptureRejected, capture_child
from raw_writer import RecordRejected, sha256, write_raw_arrays


HERE = Path(__file__).resolve().parent


def fixture():
    f = lambda x: np.asarray(x, dtype="<f8")
    i = lambda x: np.asarray(x, dtype="<i8")
    return {
        "mesh_coordinates_hat": f([[0, 0], [1, 0], [1, 1], [0, 1]]),
        "mesh_triangles": i([[0, 1, 2], [0, 2, 3]]),
        "algebraic_solution_before_backsub": f([1, 2, 3, 0, 1, 2, 3, 4]),
        "reconstructed_solution": f([1, 2, 3, 1, 1, 2, 3, 4]),
        "pressure_coordinates_hat": f([[0, 0], [1, 0], [1, 1], [0, 1]]),
        "velocity_dof_coordinates_hat": f([[0, 0], [1, 0], [1, 1], [0, 1]]),
        "velocity_dof_components": i([0, 1, 0, 1]),
        "velocity_reconstructed_dof_indices": i([0, 1, 2, 3]),
        "velocity_reconstructed_values": f([1, 2, 3, 1]),
        "pressure_reconstructed_dof_indices": i([4, 5, 6, 7]),
        "wall_velocity_dof_indices": i([0, 1]),
        "pressure_area_weights_hat2": f([0.125, 0.125, 0.125, 0.125]),
        "pressure_raw_P1": f([1, 2, 3, 4]),
        "pressure_zero_mean_P1": f([-1.5, -0.5, 0.5, 1.5]),
        "periodic_slave_dofs": i([3]),
        "periodic_master_dofs": i([0]),
    }


def expect_reject(fn, reason):
    try:
        fn()
    except (RecordRejected, CaptureRejected) as exc:
        assert reason in str(exc), (reason, exc)
        return
    raise AssertionError("expected rejection: " + reason)


def main():
    checks = []
    with tempfile.TemporaryDirectory(prefix="sim240_synthetic_capture_") as temp:
        parent = Path(temp)
        arrays = fixture()
        provenance = {"kind": "SYNTHETIC_WRITER_TEST_NOT_RESULT"}
        raw = write_raw_arrays(parent / "raw", "fixture", arrays, provenance)
        manifest = json.loads((raw / "raw_manifest.json").read_text())
        for name, expected in arrays.items():
            path = raw / (name + ".npy")
            observed = np.load(path, allow_pickle=False)
            assert observed.dtype == expected.dtype and np.array_equal(observed, expected)
            assert sha256(path) == manifest["files"][path.name]["sha256"]
        checks.append("16_RAW_ARRAYS_EXACT_READBACK_AND_HASH")
        expect_reject(lambda: write_raw_arrays(parent / "raw", "fixture", arrays, provenance),
                      "OUTPUT_ALREADY_EXISTS")
        checks.append("NO_OVERWRITE")
        bad = fixture()
        bad["pressure_zero_mean_P1"][0] += 1
        expect_reject(lambda: write_raw_arrays(parent / "raw", "badshift", bad, provenance),
                      "PRESSURE_SHIFT_MISMATCH")
        bad = fixture()
        bad["pressure_raw_P1"][0] = np.nan
        expect_reject(lambda: write_raw_arrays(parent / "raw", "badnan", bad, provenance),
                      "EMPTY_OR_NONFINITE_ARRAY")
        checks.append("PRESSURE_AND_FINITE_NEGATIVE_CONTROLS")
        (parent / "link").symlink_to(parent / "raw", target_is_directory=True)
        expect_reject(lambda: write_raw_arrays(parent / "link", "x", arrays, provenance),
                      "INVALID_OUTPUT_PARENT")
        checks.append("SYMLINK_REJECTED")
        child = parent / "synthetic_child.py"
        child.write_text("import sys\nprint('synthetic stdout')\n"
                         "print('synthetic stderr', file=sys.stderr)\nsys.exit(7)\n")
        before = hashlib.sha256(child.read_bytes()).hexdigest()
        argv = [sys.executable, "-B", str(child)]
        expect_reject(lambda: capture_child(parent / "run", "real", argv,
                      {str(child): before}, kind="FUTURE_UNVERIFIED_SOLVER_PROCESS"),
                      "REVIEWED_RELEASE_REQUIRED")
        expect_reject(lambda: capture_child(parent / "run", "real", argv,
                      {str(child): before}, kind="FUTURE_UNVERIFIED_SOLVER_PROCESS",
                      approved_release={"status": "APPROVED_FOR_RECTANGLE_SOLVE"}),
                      "REAL_PROCESS_ADAPTER_NOT_IMPLEMENTED")
        checks.append("REAL_PROCESS_GATE_CLOSED")
        run = capture_child(parent / "run", "synthetic_exit7", argv,
                            {str(child): before}, kind="SYNTHETIC_CAPTURE_TEST_NOT_RESULT")
        capture = json.loads((run / "capture_manifest.json").read_text())
        assert capture["independent_exit_code"] == 7
        assert (run / "independent_exit_code.txt").read_text() == "7\n"
        assert (run / "stdout.log").read_text() == "synthetic stdout\n"
        assert (run / "stderr.log").read_text() == "synthetic stderr\n"
        assert capture["inputs_unchanged"] is True
        for name, entry in capture["files"].items():
            assert sha256(run / name) == entry["sha256"]
        checks.append("INDEPENDENT_EXIT7_FULL_LOGS_AND_INPUT_HASHES")
        expect_reject(lambda: capture_child(parent / "run", "synthetic_exit7", argv,
                      {str(child): before}, kind="SYNTHETIC_CAPTURE_TEST_NOT_RESULT"),
                      "OUTPUT_ALREADY_EXISTS")
        expect_reject(lambda: capture_child(parent / "run", "wronghash", argv,
                      {str(child): "0" * 64}, kind="SYNTHETIC_CAPTURE_TEST_NOT_RESULT"),
                      "INPUT_HASH_MISMATCH_BEFORE_CHILD")
        checks.append("CAPTURE_NO_OVERWRITE_AND_INPUT_TAMPER_REJECTED")
    result = {"status": "PASS_SYNTHETIC_ONLY", "solver_called": False,
              "checks": checks, "formal_run_id": None,
              "NUMERICAL_GATE": "NOT_EVALUATED"}
    evidence = HERE / "evidence"
    evidence.mkdir(exist_ok=True)
    (evidence / "synthetic_checks.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

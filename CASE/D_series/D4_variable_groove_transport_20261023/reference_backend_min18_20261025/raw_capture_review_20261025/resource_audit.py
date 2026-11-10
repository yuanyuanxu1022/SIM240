"""One assembly-only resource measurement; explicitly no solve."""
import hashlib
import json
import os
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
EVIDENCE = HERE / "evidence"


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def mem_available():
    for row in Path("/proc/meminfo").read_text().splitlines():
        if row.startswith("MemAvailable:"):
            return int(row.split()[1]) * 1024
    raise RuntimeError("MemAvailable not found")


def main():
    target = "B0MIN_FLAT_T_d1p25"
    preflight = json.loads((ROOT / "solve_entry_review_20261025/evidence/preflight_all9.json").read_text())
    prior = next(r for r in preflight["records"] if r["planned_id"] == target)
    assert prior["exit_code"] == 0 and prior["preflight"]["solver_called"] is False
    assembly = json.loads((ROOT / "pressure_assembly_audit_20261025/evidence/assembly_all9.json").read_text())
    expected = next(r["result"] for r in assembly["records"] if r["planned_id"] == target)
    source = ROOT / "solve_entry_review_20261025/entry.py"
    plan = ROOT / "protocol/benchmarks18.csv"
    before = {str(path.relative_to(ROOT)): digest(path) for path in (source, plan)}
    available = mem_available()
    stat = os.statvfs(ROOT)
    disk_available = stat.f_bavail * stat.f_frsize
    command = ["/usr/bin/time", "-f", "PEAK_RSS_KiB=%M;WALL_SECONDS=%e;EXIT=%x",
               str(ROOT / ".backend/bin/python"), "-B", str(source),
               "--mode", "preflight", "--planned-id", target]
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    after = {str(path.relative_to(ROOT)): digest(path) for path in (source, plan)}
    actual = json.loads(completed.stdout) if completed.returncode == 0 else None
    assert before == after
    assert actual and actual["solver_called"] is False
    assert actual["matrix_csr_sha256"] == expected["matrix_csr_sha256"]
    assert actual["rhs_sha256_before_projection"] == expected["rhs_sha256_before_projection"]
    measures = dict(part.split("=", 1) for part in completed.stderr.strip().split(";")
                    if "=" in part)
    peak = int(measures["PEAK_RSS_KiB"])
    wall = float(measures["WALL_SECONDS"])
    shape = actual["matrix_shape"]
    nnz = expected["matrix_nnz"]
    # Illustrative CSR storage and GMRES basis only; PETSc allocation is broader.
    csr_bytes_32bit_indices = nnz * (8 + 4) + (shape[0] + 1) * 4
    gmres_50_vector_bytes = 51 * shape[0] * 8
    verdict = {
        "status": "ASSEMBLY_ONLY_RESOURCE_MEASURED_SOLVER_BUDGET_UNVALIDATED",
        "planned_id": target, "solver_called": False, "exit_code": completed.returncode,
        "assembly_preflight_peak_RSS_KiB": peak, "assembly_preflight_wall_seconds": wall,
        "measured_matrix_shape": shape, "matrix_nnz_from_prior_audit": nnz,
        "illustrative_CSR_32bit_index_bytes": csr_bytes_32bit_indices,
        "illustrative_GMRES_restart50_basis_bytes": gmres_50_vector_bytes,
        "current_MemAvailable_bytes": available, "current_disk_available_bytes": disk_available,
        "proposed_available_RAM_GiB": 4, "proposed_result_disk_GiB": 4,
        "proposed_total_solve_wall_hours": 2,
        "proposal_validation": "NOT_VALIDATED_BY_ASSEMBLY_ONLY",
        "unpreconditioned_GMRES_convergence_and_runtime": "UNTESTED",
        "parallel_cases": "ONE_AT_A_TIME_PROPOSAL_NOT_RELEASE",
        "input_sha256_before": before, "input_sha256_after": after,
        "matrix_csr_sha256": actual["matrix_csr_sha256"],
        "rhs_sha256_before_projection": actual["rhs_sha256_before_projection"],
        "NUMERICAL_GATE": "NOT_EVALUATED", "RESULT_PASS": False,
        "geometry_PASS": None
    }
    EVIDENCE.mkdir(exist_ok=True)
    (EVIDENCE / "assembly_only_stdout.json").write_text(completed.stdout)
    (EVIDENCE / "assembly_only_stderr.log").write_text(completed.stderr)
    (EVIDENCE / "resource_review.json").write_text(json.dumps(verdict, indent=2) + "\n")
    print(json.dumps(verdict, indent=2))


if __name__ == "__main__":
    main()

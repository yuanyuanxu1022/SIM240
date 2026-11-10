"""Nine isolated preflights. Every child only assembles and checks; none solves."""

import csv
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
ROWS = list(csv.DictReader((ROOT / "protocol/benchmarks18.csv").open(
    encoding="utf-8-sig", newline="")))
IDS = [r["planned_id"] for r in ROWS if r["direction_or_field"] in {"T", "mixed"}]


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    if len(IDS) != 9:
        raise RuntimeError("EXPECTED_NINE_PRESSURE_CASES")
    backend = ROOT / ".backend"
    python = backend / "bin/python"
    if Path(sys.prefix).resolve() != backend.resolve():
        raise RuntimeError("ISOLATED_BACKEND_REQUIRED")
    env = dict(os.environ, PYTHONPATH=str(ROOT), LD_LIBRARY_PATH=str(backend / "lib"))
    target = HERE / "evidence/preflight_all9.json"
    target.parent.mkdir(exist_ok=True)
    files = [ROOT / "protocol/benchmarks18.csv", ROOT / "protocol/method_contract.json",
             ROOT / "environment/conda-linux-64.explicit.txt",
             ROOT / "mesh_periodic_pressure_20261025/interface.py",
             ROOT / "src/symbolic_forms.py", ROOT / "src/contract.py",
             ROOT / "pressure_assembly_audit_20261025/evidence/assembly_all9.json",
             HERE / "entry.py", HERE / "run_preflight.py", HERE / "test_entry.py",
             HERE / "verify_preflight.py"]
    records = []
    for ident in IDS:
        command = [str(python), "-B", str(HERE / "entry.py"),
                   "--mode", "preflight", "--planned-id", ident]
        start = time.monotonic()
        try:
            proc = subprocess.run(command, env=env, capture_output=True, text=True,
                                  check=False, timeout=180)
            record = {"planned_id": ident, "command": command,
                      "exit_code": proc.returncode, "elapsed_s": time.monotonic()-start,
                      "stderr": proc.stderr}
            if proc.returncode == 0:
                record["preflight"] = json.loads(proc.stdout)
            else:
                record["stdout"] = proc.stdout
        except subprocess.TimeoutExpired as exc:
            record = {"planned_id": ident, "command": command,
                      "exit_code": None, "elapsed_s": time.monotonic()-start,
                      "error": "TIMEOUT_180_S", "stdout": str(exc.stdout),
                      "stderr": str(exc.stderr)}
        records.append(record)
        payload = {"schema": "D4_MIXED_SOLVE_ENTRY_PREFLIGHT_v1",
                   "status": "PARTIAL", "planned_ids": IDS, "records": records,
                   "source_sha256": {str(p.relative_to(ROOT)): sha256(p) for p in files},
                   "solver_called": False, "formal_run_id": None}
        target.write_text(json.dumps(payload, indent=2, ensure_ascii=False,
                                     allow_nan=False) + "\n")
        print(ident, record["exit_code"], f'{record["elapsed_s"]:.2f}s', flush=True)
        if record["exit_code"] != 0:
            break
    payload["status"] = ("PREFLIGHT_COMPLETE" if len(records) == len(IDS)
                         and all(r["exit_code"] == 0 for r in records)
                         else "PREFLIGHT_INCOMPLETE_OR_FAILED")
    target.write_text(json.dumps(payload, indent=2, ensure_ascii=False,
                                 allow_nan=False) + "\n")
    return 0 if payload["status"] == "PREFLIGHT_COMPLETE" else 1


if __name__ == "__main__":
    raise SystemExit(main())

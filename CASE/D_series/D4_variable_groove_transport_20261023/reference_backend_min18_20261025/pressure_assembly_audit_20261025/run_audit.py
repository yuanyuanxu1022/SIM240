"""Run each of nine bound mixed assembly audits in a fresh process, with no solve."""

import csv
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
HERE = Path(__file__).resolve().parent
ROWS = list(csv.DictReader((ROOT / "protocol/benchmarks18.csv").open(
    encoding="utf-8-sig", newline="")))
IDS = [r["planned_id"] for r in ROWS if r["direction_or_field"] in {"T", "mixed"}]
if len(IDS) != 9:
    raise RuntimeError("EXPECTED_NINE_MIXED_CASES")


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    backend = ROOT / ".backend"
    python = backend / "bin/python"
    if Path(sys.prefix).resolve() != backend.resolve():
        raise RuntimeError("ISOLATED_BACKEND_REQUIRED")
    target = HERE / "evidence"
    target.mkdir(exist_ok=True)
    env = dict(os.environ)
    env["PYTHONPATH"] = str(ROOT)
    env["LD_LIBRARY_PATH"] = str(backend / "lib")
    results = []
    for ident in IDS:
        command = [str(python), "-B", str(HERE / "probe.py"), ident]
        begin = time.monotonic()
        try:
            proc = subprocess.run(command, env=env, capture_output=True, text=True,
                                  timeout=180, check=False)
            record = {"planned_id": ident, "command": command,
                      "exit_code": proc.returncode, "elapsed_s": time.monotonic()-begin,
                      "stderr": proc.stderr}
            if proc.returncode == 0:
                record["result"] = json.loads(proc.stdout)
            else:
                record["stdout"] = proc.stdout
        except subprocess.TimeoutExpired as exc:
            record = {"planned_id": ident, "command": command, "exit_code": None,
                      "elapsed_s": time.monotonic()-begin, "error": "TIMEOUT_180_S",
                      "stdout": str(exc.stdout), "stderr": str(exc.stderr)}
        results.append(record)
        (target / "assembly_all9.json").write_text(json.dumps({
            "schema": "D4_MIXED_ASSEMBLY_AUDIT_v1", "status": "PARTIAL",
            "planned_ids": IDS, "records": results, "solver_called": False,
            "input_sha256": {str(p.relative_to(ROOT)): sha256(p) for p in [
                ROOT / "protocol/benchmarks18.csv", ROOT / "protocol/method_contract.json",
                ROOT / "src/symbolic_forms.py", ROOT / "src/contract.py",
                ROOT / "mesh_periodic_pressure_20261025/interface.py",
                HERE / "probe.py", HERE / "run_audit.py"]}
        }, indent=2, ensure_ascii=False, allow_nan=False) + "\n")
        print(ident, record["exit_code"], f'{record["elapsed_s"]:.2f}s', flush=True)
        if record["exit_code"] != 0:
            break
    payload = json.loads((target / "assembly_all9.json").read_text())
    payload["status"] = "COMPLETE" if len(results) == len(IDS) and all(
        r["exit_code"] == 0 for r in results) else "PARTIAL_OR_FAILED"
    (target / "assembly_all9.json").write_text(json.dumps(payload, indent=2,
                                                           ensure_ascii=False,
                                                           allow_nan=False) + "\n")
    return 0 if payload["status"] == "COMPLETE" else 1


if __name__ == "__main__":
    raise SystemExit(main())

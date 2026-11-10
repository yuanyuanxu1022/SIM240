"""Strict whitelist and preparation contracts. Standard-library only."""
import csv
import hashlib
import json
from pathlib import Path

from physics import flat_exact, topology_counts

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[3]
SOURCE = REPO / "docs/reports/D4_reference_protocol_review_20261025/minimal_benchmark18.csv"
SOURCE_SHA256 = "fb784710590acdbdc1ac5abdc33cdc542d3643bd4df28d49a85cb12902e85aee"
PREPARATION_VERSION = "D4_REFERENCE_MIN18_STATIC_PREPARATION_v1"


class Rejected(ValueError):
    pass


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1048576), b""):
            h.update(block)
    return h.hexdigest()


def load_plan():
    bindings = json.loads((ROOT / "protocol/review_input_hashes.json").read_text())
    for relative, expected in bindings.items():
        p = (REPO / relative).resolve()
        if not p.is_relative_to(REPO) or not p.is_file() or sha256(p) != expected:
            raise Rejected("REVIEW_INPUT_HASH_MISMATCH: " + relative)
    paths = [SOURCE, ROOT / "protocol/benchmarks18.csv"]
    if any(not p.is_file() or sha256(p) != SOURCE_SHA256 for p in paths):
        raise Rejected("WHITELIST_SOURCE_HASH_MISMATCH")
    with paths[1].open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    if len(rows) != 18 or len({r["planned_id"] for r in rows}) != 18:
        raise Rejected("WHITELIST_COUNT_OR_DUPLICATE_ID")
    plans = {}
    for r in rows:
        if r["authorized_to_execute"] != "False" or r["actual_run_id"]:
            raise Rejected("WHITELIST_IS_NOT_PREPARATION_ONLY")
        p = r["problem"]
        field = r["direction_or_field"]
        if (p, field) not in {("flat75", "P"), ("flat75", "T"), ("MMS", "scalar"), ("MMS", "mixed")}:
            raise Rejected("UNSUPPORTED_PROBLEM")
        mixed = field in {"T", "mixed"}
        nx, nz = int(r["nx"]), int(r["nz"])
        geometry = ({"kind": "rectangle", "h_nm": 75, "P_nm": 240, "d_nm": 0,
                     "P_hat": 3.2, "H_hat": 1, "units": "SI_recovery_from_h"}
                    if p == "flat75" else
                    {"kind": "rectangle", "P_hat": 2, "H_hat": 1, "units": "dimensionless_MMS"})
        plans[r["planned_id"]] = {
            "schema_version": 1, "preparation_version": PREPARATION_VERSION,
            "planned_id": r["planned_id"], "problem": p, "field": field,
            "role": r["role"], "geometry": geometry,
            "mesh": {"nx": nx, "nz": nz, "cell": "triangle", "diagonal": "right",
                     "label": r["mesh_label"], "constructed": False},
            "element": "P2_vector_P1_pressure" if mixed else "P2_scalar",
            "forcing": "unit_uniform_body_acceleration" if p == "flat75" else "prescribed_MMS_source",
            "explicit_body_force_and_pressure_drop_together": False,
            "pressure_sign": "minus_laplacian_u_plus_grad_pi" if mixed else None,
            "pressure_gauge": "one_constant_nullspace_then_integral_mean_removal" if mixed else None,
            "periodic": {"axis": "x", "slave": "x=P", "master": "x=0", "z_interval": [0, 1],
                         "velocity_wall_endpoints": "Dirichlet_priority_exclude_from_periodic_slaves",
                         "pressure_endpoints": "include" if mixed else None,
                         "trace_normalization": "max(1,left_amplitude,right_amplitude)",
                         "actual_pairing_verified": False},
            "quadrature_degree": int(r["quadrature_degree"]),
            "true_relative_residual_target": float(r["true_relative_residual_target"]),
            "target_status": "DRAFT_NOT_ACTIVATED",
            "candidate_resources": {"available_RAM_GiB": 4, "disk_GiB": 4,
                                    "whole_batch_wall_time_allowance_hours": 2,
                                    "measured_or_guaranteed": False},
            "analytic_topology_counts": topology_counts(nx, nz, mixed),
            "physical_constants": {"rho_kg_m3": 1000, "nu_m2_s": 1e-6, "a_m_s2": 1e5} if p == "flat75" else None,
            "analytic_expectation": flat_exact() if p == "flat75" else {"J_hat_exact": 1 / 6, "physical_K": "NOT_APPLICABLE"},
            "actual_run_id": None, "execution_authorized": False,
            "solve_implementation_present": False,
        }
    return plans


def canonical(plan):
    return json.dumps(plan, sort_keys=True, separators=(",", ":"), allow_nan=False)


def select(planned_id=None, supplied=None):
    plans = load_plan()
    if supplied is not None:
        if not isinstance(supplied, dict) or supplied.get("planned_id") not in plans:
            raise Rejected("UNKNOWN_OR_INVALID_CONFIG")
        key = supplied["planned_id"]
        if planned_id is not None and planned_id != key:
            raise Rejected("ID_CONFIG_MISMATCH")
        # JSON canonical equality is strict about extra fields, changed geometry,
        # altered tolerances, bool-vs-int substitution, NaN and execution flags.
        try:
            equal = canonical(supplied) == canonical(plans[key])
        except (ValueError, TypeError):
            equal = False
        if not equal:
            raise Rejected("CONFIG_DIFFERS_FROM_BOUND_WHITELIST")
        return [plans[key]]
    if planned_id is None:
        return list(plans.values())
    if planned_id not in plans:
        raise Rejected("UNKNOWN_PLANNED_ID")
    return [plans[planned_id]]


def bound_inputs():
    files = [SOURCE]
    bindings = json.loads((ROOT / "protocol/review_input_hashes.json").read_text())
    files.extend(REPO / relative for relative in bindings)
    for sub in ("src", "protocol", "schemas", "environment", "tests"):
        files.extend(p for p in (ROOT / sub).rglob("*") if p.is_file() and "__pycache__" not in p.parts)
    files.append(ROOT / "prepare.py")
    if (ROOT / "verify_preparation.py").is_file():
        files.append(ROOT / "verify_preparation.py")
    if (ROOT / "README.md").is_file():
        files.append(ROOT / "README.md")
    return {str(p.relative_to(REPO)): sha256(p) for p in sorted(set(files))}

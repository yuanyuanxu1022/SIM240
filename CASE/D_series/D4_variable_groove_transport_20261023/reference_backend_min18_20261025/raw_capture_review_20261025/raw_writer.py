"""Draft lossless array writer; no PDE solver import or execution path."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import numpy as np


class RecordRejected(ValueError):
    pass


REQUIRED = {
    "mesh_coordinates_hat": ("<f8", 2),
    "mesh_triangles": ("<i8", 2),
    "algebraic_solution_before_backsub": ("<f8", 1),
    "reconstructed_solution": ("<f8", 1),
    "pressure_coordinates_hat": ("<f8", 2),
    "velocity_dof_coordinates_hat": ("<f8", 2),
    "velocity_dof_components": ("<i8", 1),
    "velocity_reconstructed_dof_indices": ("<i8", 1),
    "velocity_reconstructed_values": ("<f8", 1),
    "pressure_reconstructed_dof_indices": ("<i8", 1),
    "wall_velocity_dof_indices": ("<i8", 1),
    "pressure_area_weights_hat2": ("<f8", 1),
    "pressure_raw_P1": ("<f8", 1),
    "pressure_zero_mean_P1": ("<f8", 1),
    "periodic_slave_dofs": ("<i8", 1),
    "periodic_master_dofs": ("<i8", 1),
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def write_raw_arrays(parent: Path, record_id: str, arrays: dict, provenance: dict) -> Path:
    """Write prevalidated arrays into a fresh directory; never label as accepted.

    Caller must explicitly mark synthetic fixtures. A future numerical adapter
    must supply real mesh, mixed DOF arrays, periodic map, and source binding.
    """
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,79}", record_id):
        raise RecordRejected("INVALID_RECORD_ID")
    parent = Path(parent)
    if parent.is_symlink() or (parent.exists() and not parent.is_dir()):
        raise RecordRejected("INVALID_OUTPUT_PARENT")
    dest = parent / record_id
    if dest.exists() or dest.is_symlink():
        raise RecordRejected("OUTPUT_ALREADY_EXISTS")
    if set(arrays) != set(REQUIRED):
        raise RecordRejected("RAW_ARRAY_SET_MISMATCH")
    if not isinstance(provenance, dict) or provenance.get("kind") not in {
        "SYNTHETIC_WRITER_TEST_NOT_RESULT", "FUTURE_UNVERIFIED_SOLVER_RAW"
    }:
        raise RecordRejected("EXPLICIT_PROVENANCE_KIND_REQUIRED")
    if provenance["kind"] == "FUTURE_UNVERIFIED_SOLVER_RAW" and not (
        provenance.get("planned_id") and provenance.get("source_sha256")
        and provenance.get("mesh_sha256") and provenance.get("matrix_csr_sha256")
    ):
        raise RecordRejected("REAL_PROVENANCE_BINDING_REQUIRED")
    validated = {}
    for name, (dtype, ndim) in REQUIRED.items():
        obj = arrays[name]
        if not isinstance(obj, np.ndarray) or obj.dtype.str != dtype or obj.ndim != ndim:
            raise RecordRejected("ARRAY_DTYPE_OR_RANK_MISMATCH:" + name)
        if not obj.size or not np.all(np.isfinite(obj)):
            raise RecordRejected("EMPTY_OR_NONFINITE_ARRAY:" + name)
        validated[name] = obj
    xyz = validated["mesh_coordinates_hat"]
    tri = validated["mesh_triangles"]
    pxyz = validated["pressure_coordinates_hat"]
    vxyz = validated["velocity_dof_coordinates_hat"]
    vcomponents = validated["velocity_dof_components"]
    vmap = validated["velocity_reconstructed_dof_indices"]
    vvalues = validated["velocity_reconstructed_values"]
    pmap = validated["pressure_reconstructed_dof_indices"]
    wall = validated["wall_velocity_dof_indices"]
    weights = validated["pressure_area_weights_hat2"]
    raw = validated["pressure_raw_P1"]
    shifted = validated["pressure_zero_mean_P1"]
    slaves = validated["periodic_slave_dofs"]
    masters = validated["periodic_master_dofs"]
    if (xyz.shape[1] != 2 or pxyz.shape[1] != 2 or vxyz.shape[1] != 2
            or tri.shape[1] != 3
            or tri.min() < 0 or tri.max() >= len(xyz)
            or len(validated["algebraic_solution_before_backsub"]) != len(validated["reconstructed_solution"])
            or len(pxyz) != len(weights) or len(raw) != len(weights)
            or len(vxyz) != len(vmap) or len(vcomponents) != len(vmap)
            or len(vvalues) != len(vmap) or len(pxyz) != len(pmap)
            or np.any((vcomponents != 0) & (vcomponents != 1))
            or len(shifted) != len(weights) or not np.all(weights > 0)
            or vmap.min() < 0 or pmap.min() < 0 or wall.min() < 0
            or max(vmap.max(), pmap.max(), wall.max()) >= len(validated["reconstructed_solution"])
            or len(slaves) != len(masters) or slaves.min() < 0 or masters.min() < 0
            or slaves.max() >= len(validated["reconstructed_solution"])
            or masters.max() >= len(validated["reconstructed_solution"])):
        raise RecordRejected("RAW_ARRAY_GEOMETRY_OR_MAP_MISMATCH")
    if not np.array_equal(raw, validated["reconstructed_solution"][pmap]):
        raise RecordRejected("PRESSURE_RECONSTRUCTION_MISMATCH")
    if not np.array_equal(vvalues, validated["reconstructed_solution"][vmap]):
        raise RecordRejected("VELOCITY_RECONSTRUCTION_MISMATCH")
    mean = float(np.dot(weights, raw) / weights.sum())
    if not np.allclose(shifted, raw - mean, rtol=1e-13, atol=1e-13):
        raise RecordRejected("PRESSURE_SHIFT_MISMATCH")
    try:
        json.dumps(provenance, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise RecordRejected("INVALID_PROVENANCE_JSON") from exc
    parent.mkdir(parents=True, exist_ok=True)
    dest.mkdir(exist_ok=False)
    files = {}
    try:
        for name, obj in validated.items():
            path = dest / (name + ".npy")
            with path.open("xb") as stream:
                np.save(stream, obj, allow_pickle=False)
            files[path.name] = {"sha256": sha256(path), "dtype": obj.dtype.str,
                                "shape": list(obj.shape), "nbytes": int(obj.nbytes)}
        manifest = {"record_status": "UNVERIFIED_RAW_NOT_A_GATE", "record_id": record_id,
                    "provenance": provenance, "files": files,
                    "pressure_removed_area_mean": mean,
                    "NUMERICAL_GATE": "NOT_EVALUATED", "RESULT_PASS": False,
                    "geometry_PASS": None}
        (dest / "raw_manifest.json").write_text(
            json.dumps(manifest, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    except Exception:
        (dest / "WRITE_INCOMPLETE.txt").write_text("Raw write failed; inspect partial files.\n")
        raise
    return dest

"""Preserve partial algebraic state from a failed future solve."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import re

import numpy as np


class ArchiveRejected(ValueError):
    pass


def _safe(value):
    if isinstance(value, np.generic):
        return _safe(value.item())
    if isinstance(value, float):
        return value if math.isfinite(value) else repr(value)
    if isinstance(value, dict):
        return {str(k): _safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_safe(v) for v in value]
    if value is None or isinstance(value, (str, int, bool)):
        return value
    return str(value)


def _hash(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def save_failure(root: Path, run_id: str, stage: str, error: BaseException,
                 algebraic_vector, diagnostics: dict, source_binding: dict) -> Path:
    """Create one immutable failure directory. Nonfinite vector bits are retained.

    `algebraic_vector` must be copied before MPC backsubstitution. This is a
    failure artifact, not an accepted physical field or formal run result.
    """
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,79}", run_id):
        raise ArchiveRejected("INVALID_RUN_ID")
    if not isinstance(stage, str) or not re.fullmatch(r"[A-Z][A-Z0-9_]{1,79}", stage):
        raise ArchiveRejected("INVALID_FAILURE_STAGE")
    if not isinstance(diagnostics, dict) or not isinstance(source_binding, dict):
        raise ArchiveRejected("DIAGNOSTICS_AND_BINDING_REQUIRED")
    vector = None if algebraic_vector is None else np.asarray(algebraic_vector)
    if vector is not None and (vector.ndim != 1 or vector.dtype != np.dtype("float64")):
        raise ArchiveRejected("FLOAT64_ALGEBRAIC_VECTOR_REQUIRED")
    root = Path(root)
    if root.is_symlink() or (root.exists() and not root.is_dir()):
        raise ArchiveRejected("INVALID_ARCHIVE_ROOT")
    dest = root / run_id
    if dest.exists() or dest.is_symlink():
        raise ArchiveRejected("FAILURE_ALREADY_ARCHIVED")
    root.mkdir(parents=True, exist_ok=True)
    dest.mkdir(exist_ok=False)
    files = {}
    if vector is not None:
        path = dest / "partial_algebraic_solution_before_backsub.npy"
        with path.open("xb") as out:
            np.save(out, vector.copy(), allow_pickle=False)
        files[path.name] = {"sha256": _hash(path), "shape": list(vector.shape),
                            "dtype": vector.dtype.str,
                            "finite_count": int(np.count_nonzero(np.isfinite(vector))),
                            "nonfinite_count": int(np.count_nonzero(~np.isfinite(vector)))}
    manifest = {"record_kind": "FAILED_UNVERIFIED_PARTIAL_NOT_A_RESULT",
                "run_id": run_id, "failure_stage": stage,
                "exception_type": type(error).__name__, "exception_message": str(error),
                "diagnostics": _safe(diagnostics), "source_binding": _safe(source_binding),
                "files": files, "algebraic_vector_available": vector is not None,
                "NUMERICAL_GATE": "NOT_EVALUATED", "RESULT_PASS": False,
                "geometry_PASS": None}
    (dest / "failure_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False, allow_nan=False) + "\n")
    return dest

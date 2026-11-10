"""Durable stage records and lossless arrays; no solver import."""
import json
from pathlib import Path
import re
import numpy as np
from common import sha, write_json


def arrays(directory, values, metadata):
    directory = Path(directory)
    directory.mkdir(exist_ok=False)
    (directory / "INCOMPLETE").write_text("Do not accept until manifest exists.\n")
    files = {}
    for name, value in values.items():
        if not re.fullmatch(r"[a-zA-Z][a-zA-Z0-9_]*", name):
            raise ValueError("INVALID_ARRAY_NAME")
        a = np.asarray(value)
        if a.dtype.kind not in "fi" or a.dtype.itemsize not in (4, 8):
            raise ValueError("NUMERIC_ARRAY_REQUIRED")
        path = directory/(name+".npy")
        with path.open("xb") as f:
            np.save(f, a, allow_pickle=False)
        files[path.name] = dict(sha256=sha(path), dtype=a.dtype.str, shape=list(a.shape))
    write_json(directory/"manifest.json", dict(metadata=metadata, files=files,
               NUMERICAL_GATE="NOT_EVALUATED", RESULT_PASS=False, geometry_PASS=None))
    (directory/"INCOMPLETE").unlink()


def read_arrays(directory):
    directory = Path(directory)
    if (directory/"INCOMPLETE").exists():
        raise ValueError("INCOMPLETE_ARRAY_RECORD")
    m = json.loads((directory/"manifest.json").read_text())
    result = {}
    for name, spec in m["files"].items():
        if Path(name).name != name or not name.endswith(".npy"):
            raise ValueError("INVALID_ARRAY_PATH")
        path = directory/name
        if path.is_symlink() or sha(path) != spec["sha256"]:
            raise ValueError("ARRAY_HASH_MISMATCH:"+name)
        a = np.load(path, allow_pickle=False)
        if a.dtype.str != spec["dtype"] or list(a.shape) != spec["shape"]:
            raise ValueError("ARRAY_LAYOUT_MISMATCH")
        result[name[:-4]] = a
    return result, m["metadata"]


def inventory(root):
    return {str(p.relative_to(root)):dict(sha256=sha(p), bytes=p.stat().st_size)
            for p in sorted(Path(root).rglob("*")) if p.is_file() and not p.is_symlink()}

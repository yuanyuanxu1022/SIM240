#!/usr/bin/env python3
"""Import/API check only: no mesh, assembly, Mat/Vec/KSP object or solve."""
import hashlib
import importlib
import importlib.metadata
import inspect
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]


def probe():
    prefix = ROOT / ".backend"
    if Path(sys.prefix).resolve() != prefix.resolve():
        raise RuntimeError("Run with this package's isolated Python, not base/system Python")
    modules = {}
    for name in ("numpy", "dolfinx", "basix", "ufl", "ffcx", "mpi4py", "petsc4py", "dolfinx_mpc"):
        m = importlib.import_module(name)
        origin = Path(m.__file__).resolve()
        if not origin.is_relative_to(prefix.resolve()):
            raise RuntimeError("Module outside isolated prefix: " + name)
        version = getattr(m, "__version__", None)
        if version is None:
            version = importlib.metadata.version(name)
        modules[name] = {"version": version, "path": str(origin),
                         "file_sha256": hashlib.sha256(origin.read_bytes()).hexdigest()}
    from mpi4py import MPI
    from petsc4py import PETSc
    import dolfinx
    import dolfinx_mpc
    import numpy as np
    extensions = {}
    for name in ("dolfinx.cpp", "dolfinx_mpc.cpp", "basix._basixcpp", "petsc4py.PETSc", "mpi4py.MPI"):
        origin = Path(importlib.import_module(name).__file__).resolve()
        if not origin.is_relative_to(prefix.resolve()):
            raise RuntimeError("Extension outside isolated prefix: " + name)
        extensions[name] = {"path": str(origin), "sha256": hashlib.sha256(origin.read_bytes()).hexdigest()}
    periodic = dolfinx_mpc.MultiPointConstraint.create_periodic_constraint_geometrical
    # Record libraries actually loaded by this interpreter, since standalone
    # ldd without the isolated library path does not reproduce Python's dlopen.
    core_names = ("libdolfinx", "libbasix", "libpetsc", "libmpi")
    loaded = sorted({line.split()[-1] for line in Path("/proc/self/maps").read_text().splitlines()
                     if len(line.split()) >= 6 and line.split()[-1].startswith("/")
                     and Path(line.split()[-1]).name.startswith(core_names)})
    if not loaded or any(not Path(p).resolve().is_relative_to(prefix.resolve()) for p in loaded):
        raise RuntimeError("Core numerical library missing or loaded outside isolated prefix")
    shared = {p: hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in loaded}
    real = np.dtype(PETSc.ScalarType) == np.dtype("float64")
    if not real or MPI.COMM_WORLD.size != 1:
        raise RuntimeError("Expected real float64 and one process")
    return {"kind": "BACKEND_IMPORT_API_CHECK_ONLY", "prefix": str(prefix),
            "python": sys.version, "modules": modules, "extension_binaries": extensions,
            "actual_loaded_core_shared_libraries": shared,
            "PETSc_version": PETSc.Sys.getVersion(), "PETSc_real_float64": real,
            "MPI_version": MPI.Get_library_version(), "MPI_size": MPI.COMM_WORLD.size,
            "dolfinx_default_scalar_type": str(dolfinx.default_scalar_type),
            "periodic_API_signature": str(inspect.signature(periodic)),
            "nullspace_API_available": hasattr(PETSc.NullSpace, "create"),
            "solver_called": False, "actual_mesh_or_matrix_created": False,
            "periodic_constraint_or_pressure_nullspace_tested": False,
            "numerical_acceptance": "NOT_EVALUATED", "ok": True}


if __name__ == "__main__":
    try:
        print(json.dumps(probe(), indent=2))
    except Exception as exc:
        print(json.dumps({"kind": "BACKEND_IMPORT_CHECK_FAILED", "error": repr(exc),
                          "solver_called": False, "ok": False}), file=sys.stderr)
        sys.exit(1)

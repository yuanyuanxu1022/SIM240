"""Symbolic UFL shape/source check, without a computational mesh or assembly.

ufl.Mesh below is an abstract coordinate-domain declaration. It has no cell
connectivity, coordinates, FEM matrix or numerical field. No JIT is called.
"""
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def check():
    import basix.ufl
    import ufl
    from ufl.algorithms import expand_derivatives
    from ufl.utils.stacks import StackDict
    from physics import scalar_mms, mixed_mms
    from symbolic_forms import manufactured_fields, poisson_forms, stokes_forms

    domain = ufl.Mesh(basix.ufl.element("Lagrange", "triangle", 1, shape=(2,)))
    x = ufl.SpatialCoordinate(domain)
    scalar_space = ufl.FunctionSpace(domain, basix.ufl.element("Lagrange", "triangle", 2))
    mixed_space = ufl.FunctionSpace(domain, basix.ufl.mixed_element([
        basix.ufl.element("Lagrange", "triangle", 2, shape=(2,)),
        basix.ufl.element("Lagrange", "triangle", 1)]))
    exact = manufactured_fields(x)
    dx = ufl.Measure("dx", domain=domain, metadata={"quadrature_degree": 8})
    v, eta = ufl.TrialFunction(scalar_space), ufl.TestFunction(scalar_space)
    u, pressure = ufl.TrialFunctions(mixed_space)
    w, q = ufl.TestFunctions(mixed_space)
    lhs_s, rhs_s = poisson_forms(v, eta, exact["scalar_forcing"], dx)
    lhs_m, rhs_m = stokes_forms(u, pressure, w, q, exact["mixed_forcing"], dx)
    # UFL validates tensor ranks while constructing these forms.
    assert all(len(f.integrals()) > 0 for f in [lhs_s, rhs_s, lhs_m, rhs_m])
    forcing_s = expand_derivatives(exact["scalar_forcing"])
    forcing_m = expand_derivatives(exact["mixed_forcing"])
    divergence = expand_derivatives(ufl.div(exact["velocity"]))
    errors = []
    for point in [(0.17, .21), (.83, .61), (1.73, .81)]:
        s = scalar_mms(*point); m = mixed_mms(*point)
        errors.append(abs(forcing_s.evaluate(point, {}, (), StackDict()) - s["forcing"]))
        for i in range(2):
            errors.append(abs(forcing_m.evaluate(point, {}, (i,), StackDict()) - m["forcing"][i]))
        errors.append(abs(divergence.evaluate(point, {}, (), StackDict())))
    assert max(errors) < 1e-12, errors
    return {"kind": "SYMBOLIC_UFL_ONLY", "ok": True,
            "source_and_divergence_max_absolute_difference": max(errors),
            "computational_mesh_created": False, "matrix_assembled": False,
            "JIT_called": False, "solver_called": False,
            "periodic_and_nullspace_backend_validation": "NOT_EVALUATED"}


if __name__ == "__main__":
    print(json.dumps(check(), indent=2))

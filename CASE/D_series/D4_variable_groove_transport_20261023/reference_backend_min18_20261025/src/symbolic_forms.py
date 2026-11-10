"""Lazy UFL recipes for later review; never compiles, assembles or solves.

All arguments must be supplied by a future reviewed implementation. This
module cannot create a domain, periodic map, nullspace or a PETSc problem.
The negative continuity sign gives the symmetric physical-pressure block.
"""


def poisson_forms(v, test, forcing, dx):
    import ufl
    return ufl.inner(ufl.grad(v), ufl.grad(test)) * dx, forcing * test * dx


def stokes_forms(u, pressure, w, q, forcing, dx):
    import ufl
    lhs = (ufl.inner(ufl.grad(u), ufl.grad(w))
           - pressure * ufl.div(w) - q * ufl.div(u)) * dx
    rhs = ufl.inner(forcing, w) * dx
    return lhs, rhs


def manufactured_fields(x):
    """Symbolic definitions; forcing is differentiated independently of physics.py."""
    import ufl
    z = x[1]
    scalar = z * (1 - z) * (1 + 0.1 * ufl.cos(ufl.pi * x[0]))
    psi = z**2 / 2 - z**3 / 3 + 0.1 * ufl.sin(ufl.pi * x[0]) * z**2 * (1 - z)**2
    u = ufl.as_vector((psi.dx(1), -psi.dx(0)))
    pressure = 0.1 * ufl.cos(ufl.pi * x[0]) * ufl.cos(ufl.pi * z)
    return {"scalar": scalar, "scalar_forcing": -ufl.div(ufl.grad(scalar)),
            "velocity": u, "pressure": pressure,
            "mixed_forcing": -ufl.div(ufl.grad(u)) + ufl.grad(pressure)}

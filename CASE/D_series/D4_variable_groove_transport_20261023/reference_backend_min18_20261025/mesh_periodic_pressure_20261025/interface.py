"""Single-process, no-solve interfaces for the bound 18 rectangular cases.

Coordinates are nondimensional: flat75 uses h=1 and P=3.2; MMS uses
H=1 and P=2. Physical SI recovery remains in the bound v1 contract.
"""

import hashlib
import json
from pathlib import Path
import sys

import numpy as np

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT / "src"))
from contract import Rejected, select  # noqa: E402


def _backend():
    if Path(sys.prefix).resolve() != (PACKAGE_ROOT / ".backend").resolve():
        raise Rejected("ISOLATED_BACKEND_REQUIRED")
    from mpi4py import MPI
    from petsc4py import PETSc
    from dolfinx import fem, mesh
    from dolfinx_mpc import MultiPointConstraint
    import basix.ufl
    if MPI.COMM_WORLD.size != 1 or np.dtype(PETSc.ScalarType) != np.dtype("float64"):
        raise Rejected("SINGLE_PROCESS_REAL_FLOAT64_ONLY")
    return MPI, fem, mesh, MultiPointConstraint, basix.ufl


def _coordinate_index(space, parent_map, components):
    """Map parent mixed DOF numbers to geometric (x,z,component) labels."""
    coords = space.tabulate_dof_coordinates()[:, :2]
    indices = np.asarray(parent_map, dtype=np.int64)
    if len(indices) != len(coords) * components:
        raise Rejected("COLLAPSED_MAP_BLOCK_COUNT_MISMATCH")
    return {int(parent): (coords[i // components], i % components)
            for i, parent in enumerate(indices)}


def _pressure_weights(domain, Q):
    """Exact integral weights of continuous P1 nodal values on linear triangles."""
    qcoords = Q.tabulate_dof_coordinates()[:, :2]
    keys = lambda xy: tuple(np.rint(np.asarray(xy) / 1e-11).astype(np.int64))
    lookup = {keys(x): i for i, x in enumerate(qcoords)}
    if len(lookup) != len(qcoords):
        raise Rejected("PRESSURE_VERTEX_KEY_COLLISION")
    weights = np.zeros(len(qcoords), dtype=np.float64)
    points = domain.geometry.x[:, :2]
    triangles = domain.geometry.dofmaps[0]
    for tri in triangles:
        a, b, c = points[tri]
        area = abs(np.linalg.det(np.stack((b-a, c-a), axis=1))) / 2
        if not np.isfinite(area) or area <= 0:
            raise Rejected("INVALID_TRIANGLE_AREA")
        for vertex in (a, b, c):
            try:
                weights[lookup[keys(vertex)]] += area / 3
            except KeyError as exc:
                raise Rejected("PRESSURE_DOF_NOT_ON_VERTEX") from exc
    if np.any(weights <= 0):
        raise Rejected("PRESSURE_WEIGHT_NONPOSITIVE")
    return weights


def remove_pressure_area_mean(values, weights):
    """Postprocessing interface for P1 pressure values, without a point pin.

    The caller must supply a field from a later completed calculation.
    This function itself only subtracts the mesh-integral mean.
    """
    v = np.asarray(values, dtype=np.float64)
    w = np.asarray(weights, dtype=np.float64)
    if v.ndim != 1 or w.ndim != 1 or v.shape != w.shape:
        raise Rejected("PRESSURE_VECTOR_SHAPE_MISMATCH")
    if not np.all(np.isfinite(v)) or not np.all(np.isfinite(w)) or np.any(w <= 0):
        raise Rejected("INVALID_PRESSURE_OR_WEIGHTS")
    area = float(np.sum(w))
    if not np.isfinite(area) or area <= 0:
        raise Rejected("INVALID_PRESSURE_AREA")
    mean = float(np.dot(w, v) / area)
    return v - mean, mean


def attach_checked_pressure_nullspace(matrix, rhs, candidate, relative_tol=1e-10):
    """Later assembly hook: check A*n and n·b before attaching one PETSc nullspace.

    No matrix is built here. The current preparation does not call this hook
    on a physical FEM system. A later caller must retain the returned PETSc
    vector/nullspace objects until the solve has completed.
    """
    from petsc4py import PETSc
    if not (np.isfinite(relative_tol) and 0 < relative_tol < 1):
        raise Rejected("INVALID_PRESSURE_NULLSPACE_TOLERANCE")
    ndata = np.asarray(candidate, dtype=np.float64)
    if ndata.ndim != 1 or not np.all(np.isfinite(ndata)) or np.linalg.norm(ndata) <= 0:
        raise Rejected("INVALID_PRESSURE_NULLSPACE_CANDIDATE")
    nrows, ncols = matrix.getSize()
    if nrows != ncols or nrows != rhs.getSize() or ncols != len(ndata):
        raise Rejected("PRESSURE_NULLSPACE_DIMENSION_MISMATCH")
    vector = matrix.createVecRight()
    if vector.getLocalSize() != len(ndata):
        raise Rejected("PRESSURE_NULLSPACE_LOCAL_SIZE_MISMATCH")
    vector.array[:] = ndata
    vector.normalize()
    image = matrix.createVecLeft()
    matrix.mult(vector, image)
    matrix_norm = matrix.norm()
    if matrix_norm <= 0:
        raise Rejected("ZERO_OPERATOR_NOT_A_PRESSURE_CHECK")
    kernel_relative = image.norm()/matrix_norm
    rhs_norm = rhs.norm()
    compatibility_relative = abs(rhs.dot(vector))/rhs_norm if rhs_norm > 0 else 0.0
    if kernel_relative > relative_tol or compatibility_relative > relative_tol:
        raise Rejected("PRESSURE_NULLSPACE_OR_RHS_COMPATIBILITY_FAILED")
    nullspace = PETSc.NullSpace().create(vectors=[vector], comm=PETSc.COMM_SELF)
    matrix.setNullSpace(nullspace)
    nullspace.remove(rhs)
    return {"nullspace": nullspace, "vector": vector,
            "kernel_relative": kernel_relative,
            "rhs_compatibility_relative_before_projection": compatibility_relative,
            "rhs_dot_null_after_projection": abs(rhs.dot(vector)),
            "only_one_constant_pressure_mode": True}


def _audit_links(mpc, coordinate_index, expected_slaves, period):
    slaves = np.asarray(mpc.slaves, dtype=np.int64)
    if len(slaves) != len(expected_slaves) or set(slaves) != set(expected_slaves):
        raise Rejected("PERIODIC_SLAVE_SET_MISMATCH")
    coefficients, offsets = mpc.coefficients()
    max_pair_error = 0.0
    max_coefficient_error = 0.0
    records = []
    for slave in slaves:
        master_links = mpc.masters.links(int(slave))
        if len(master_links) != 1:
            raise Rejected("PERIODIC_MASTER_MULTIPLICITY")
        master = int(master_links[0])
        if int(slave) not in coordinate_index or master not in coordinate_index:
            raise Rejected("PERIODIC_DOF_COORDINATE_MISSING")
        a, ac = coordinate_index[int(slave)]
        b, bc = coordinate_index[master]
        if ac != bc:
            raise Rejected("PERIODIC_COMPONENT_MISMATCH")
        error = float(np.max(np.abs(a-b-np.array((period, 0.0)))))
        max_pair_error = max(max_pair_error, error)
        weight = coefficients[offsets[int(slave)]:offsets[int(slave)+1]]
        if len(weight) != 1:
            raise Rejected("PERIODIC_COEFFICIENT_MULTIPLICITY")
        max_coefficient_error = max(max_coefficient_error, abs(float(weight[0])-1))
        records.append({"slave_dof": int(slave), "master_dof": master,
                        "slave_xz": [float(a[0]), float(a[1])],
                        "master_xz": [float(b[0]), float(b[1])],
                        "component": ac, "coefficient": float(weight[0])})
    if max_pair_error > 1e-11 or max_coefficient_error > 1e-11:
        raise Rejected("PERIODIC_LINK_OR_COEFFICIENT_ERROR")
    records.sort(key=lambda r: r["slave_dof"])
    mapping_digest = hashlib.sha256(json.dumps(records, sort_keys=True,
                                                separators=(",", ":")).encode()).hexdigest()
    return {"slave_count": len(slaves), "max_pair_coordinate_error": max_pair_error,
            "max_coefficient_error": max_coefficient_error,
            "all_masters_on_left_and_components_match": True,
            "mapping_sha256": mapping_digest, "pairs": records}


def _exact_periodic_mpc(space, MultiPointConstraint, coordinate_index, slaves, period):
    """Tie the enumerated right trace to the left trace, one DOF at a time.

    The installed automatic facet search omitted some P2 slaves on a 3.2 x 1
    rectangle during preparation. Exact DOF enumeration makes missing pairs a
    hard error; it still uses the backend's actual MPC elimination object.
    """
    def label(z, component):
        return (int(np.rint(z / 1e-11)), component)

    left = {}
    for dof, (xy, component) in coordinate_index.items():
        if abs(xy[0]) <= 1e-11:
            key = label(xy[1], component)
            if key in left:
                raise Rejected("DUPLICATE_LEFT_TRACE_DOF")
            left[key] = dof
    slave_ids = np.array(sorted(slaves), dtype=np.int32)
    master_ids = []
    for slave in slave_ids:
        if int(slave) not in coordinate_index:
            raise Rejected("RIGHT_TRACE_DOF_COORDINATE_MISSING")
        xy, component = coordinate_index[int(slave)]
        if abs(xy[0]-period) > 1e-11:
            raise Rejected("RIGHT_TRACE_DOF_NOT_ON_RIGHT")
        master = left.get(label(xy[1], component))
        if master is None:
            raise Rejected("PERIODIC_MASTER_MISSING")
        master_xy, master_component = coordinate_index[master]
        if master_component != component or np.max(abs(xy-master_xy-(period, 0))) > 1e-11:
            raise Rejected("PERIODIC_MASTER_GEOMETRY_MISMATCH")
        master_ids.append(master)
    if len(set(master_ids)) != len(master_ids):
        raise Rejected("PERIODIC_MASTER_REUSED")
    index_map = space.dofmap.index_map
    bs = space.dofmap.index_map_bs
    masters_local = np.asarray(master_ids, dtype=np.int32)
    master_global = (index_map.local_to_global(masters_local // bs)*bs
                     + masters_local % bs).astype(np.int64)
    mpc = MultiPointConstraint(space)
    mpc.add_constraint(space, slave_ids, master_global,
                       np.ones(len(slave_ids), dtype=np.float64),
                       np.zeros(len(slave_ids), dtype=np.int32),
                       np.arange(len(slave_ids)+1, dtype=np.int32))
    mpc.finalize()
    return mpc


def build_interface(planned_id):
    """Build real mesh, spaces, wall BC, finalized MPC and gauge *candidate*.

    This returns live objects for later separately reviewed assembly. It does
    not create a matrix, RHS, KSP, field result, or formal run_id.
    """
    plan = select(planned_id=planned_id)[0]
    MPI, fem, mesh, MultiPointConstraint, basix_ufl = _backend()
    nx, nz = plan["mesh"]["nx"], plan["mesh"]["nz"]
    period, height = float(plan["geometry"]["P_hat"]), float(plan["geometry"]["H_hat"])
    domain = mesh.create_rectangle(MPI.COMM_SELF, [[0., 0.], [period, height]],
                                   [nx, nz], cell_type=mesh.CellType.triangle,
                                   diagonal=mesh.DiagonalType.right)
    cells = domain.topology.index_map(2).size_local
    vertices = domain.topology.index_map(0).size_local
    if cells != 2*nx*nz or vertices != (nx+1)*(nz+1):
        raise Rejected("ACTUAL_MESH_TOPOLOGY_MISMATCH")
    points = domain.geometry.x[:, :2]
    if not np.allclose(points.min(axis=0), [0, 0], atol=1e-12, rtol=0) or not np.allclose(
            points.max(axis=0), [period, height], atol=1e-12, rtol=0):
        raise Rejected("ACTUAL_MESH_EXTENT_MISMATCH")

    right = lambda x: np.abs(x[0]-period) <= 1e-11
    wall = lambda x: (np.abs(x[1]) <= 1e-11) | (np.abs(x[1]-height) <= 1e-11)
    right_facets = mesh.locate_entities_boundary(domain, 1, right)
    if len(right_facets) != nz:
        raise Rejected("RIGHT_FACET_COUNT_MISMATCH")
    left_facets = mesh.locate_entities_boundary(domain, 1,
                                                lambda x: np.abs(x[0]) <= 1e-11)
    if len(left_facets) != nz:
        raise Rejected("LEFT_FACET_COUNT_MISMATCH")
    mixed = plan["field"] in {"T", "mixed"}
    pressure = None
    if mixed:
        Ve = basix_ufl.element("Lagrange", domain.basix_cell(), 2, shape=(2,))
        Qe = basix_ufl.element("Lagrange", domain.basix_cell(), 1)
        W = fem.functionspace(domain, basix_ufl.mixed_element([Ve, Qe]))
        velocity_sub, pressure_sub = W.sub(0), W.sub(1)
        V, vmap = velocity_sub.collapse()
        Q, qmap = pressure_sub.collapse()
        wall_dofs = fem.locate_dofs_geometrical((velocity_sub, V), wall)
        zero_velocity = fem.Function(V)
        bc = fem.dirichletbc(zero_velocity, wall_dofs, velocity_sub)
        expected_velocity = (set(fem.locate_dofs_geometrical((velocity_sub, V), right)[0])
                             - set(wall_dofs[0]))
        expected_pressure = set(fem.locate_dofs_geometrical((pressure_sub, Q), right)[0])
        expected = expected_velocity | expected_pressure
        coords = _coordinate_index(V, vmap[0], 2)
        coords.update({dof: (xy, -1) for dof, (xy, _) in
                       _coordinate_index(Q, qmap[0], 1).items()})
        if len(expected_velocity) != 2*(2*nz-1) or len(expected_pressure) != nz+1:
            raise Rejected("MIXED_TRACE_DOF_COUNT_MISMATCH")
        if len(expected & set(wall_dofs[0])):
            raise Rejected("VELOCITY_WALL_PERIODIC_OVERLAP")
        mpc = _exact_periodic_mpc(W, MultiPointConstraint, coords, expected, period)
        link_audit = _audit_links(mpc, coords, expected, period)
        weights = _pressure_weights(domain, Q)
        area = float(np.sum(weights))
        if abs(area-period*height) > 1e-11:
            raise Rejected("PRESSURE_AREA_MISMATCH")
        # Candidate constant-pressure vector in the actual constrained space.
        # A*n=0 and n^T*b=0 cannot be checked until later matrix/RHS assembly.
        gauge_space = mpc.function_space
        Qg, qmap_g = gauge_space.sub(1).collapse()
        pressure_indices = np.asarray(qmap_g[0], dtype=np.int64)
        gauge = np.zeros(gauge_space.dofmap.index_map.size_local, dtype=np.float64)
        gauge[pressure_indices] = 1
        if len(pressure_indices) != len(weights) or len(set(pressure_indices)) != len(weights):
            raise Rejected("PRESSURE_GAUGE_DOF_MISMATCH")
        if np.count_nonzero(gauge) != len(weights):
            raise Rejected("PRESSURE_GAUGE_VELOCITY_CONTAMINATION")
        gauge /= np.linalg.norm(gauge)
        probe = np.array([7 + 0.1*np.cos(np.pi*x)*np.cos(np.pi*z)
                          for x, z in Q.tabulate_dof_coordinates()[:, :2]])
        shifted, removed = remove_pressure_area_mean(probe, weights)
        if abs(np.dot(weights, shifted)) > 1e-11*area:
            raise Rejected("PRESSURE_MEAN_REMOVAL_CHECK_FAILED")
        pressure = {"space": Qg, "constant_vector": gauge,
                    "nodal_area_weights": weights, "area": area,
                    "candidate_nullspace_dimension": 1,
                    "sample_removed_mean": removed,
                    "constant_vector_velocity_entries_zero": True,
                    "matrix_kernel_checked": False,
                    "rhs_compatibility_checked": False,
                    "matrix_nullspace_attached": False}
        dof_total = W.dofmap.index_map.size_local
        trace = {"free_P2_velocity_slaves": len(expected_velocity),
                 "P1_pressure_slaves_including_endpoints": len(expected_pressure),
                 "velocity_wall_dofs": len(wall_dofs[0])}
    else:
        W = fem.functionspace(domain, ("Lagrange", 2))
        wall_dofs = fem.locate_dofs_geometrical(W, wall)
        bc = fem.dirichletbc(0., wall_dofs, W)
        expected = set(fem.locate_dofs_geometrical(W, right)) - set(wall_dofs)
        if len(expected) != 2*nz-1:
            raise Rejected("SCALAR_TRACE_DOF_COUNT_MISMATCH")
        coords = {i: (x[:2], 0) for i, x in enumerate(W.tabulate_dof_coordinates())}
        mpc = _exact_periodic_mpc(W, MultiPointConstraint, coords, expected, period)
        link_audit = _audit_links(mpc, coords, expected, period)
        dof_total = W.dofmap.index_map.size_local
        trace = {"free_P2_scalar_slaves": len(expected),
                 "scalar_wall_dofs": len(wall_dofs)}

    if dof_total != plan["analytic_topology_counts"]["raw_dofs"]:
        raise Rejected("ACTUAL_DOF_COUNT_DIFFERS_FROM_PLAN")
    mesh_digest = hashlib.sha256(points.astype("<f8").tobytes()
                                 + domain.geometry.dofmaps[0].astype("<i4").tobytes()).hexdigest()
    stats = {"planned_id": planned_id, "problem": plan["problem"], "field": plan["field"],
             "role": plan["role"], "mesh_coordinates": "dimensionless",
             "period_hat": period, "height_hat": height,
             "nx": nx, "nz": nz, "actual_triangles": cells, "actual_vertices": vertices,
             "actual_raw_dofs": dof_total, "actual_right_facets": len(right_facets),
             "actual_left_facets": len(left_facets),
             "actual_mesh_sha256": mesh_digest,
             "trace": trace, "periodic_link_audit": link_audit,
             "pressure_gauge": None if pressure is None else {
                 "candidate_nullspace_dimension": 1,
                 "P1_dofs": len(pressure["nodal_area_weights"]),
                 "nodal_area_weights_sum": pressure["area"],
                 "sample_removed_mean": pressure["sample_removed_mean"],
                 "matrix_kernel_checked": False, "rhs_compatibility_checked": False,
                 "matrix_nullspace_attached": False},
             "matrix_assembled": False, "rhs_assembled": False,
             "solver_called": False, "actual_run_id": None,
             "numerical_acceptance": "NOT_EVALUATED"}
    return {"domain": domain, "space": W, "wall_bc": bc, "mpc": mpc,
            "pressure": pressure, "stats": stats, "plan": plan}

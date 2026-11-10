"""Map a future in-memory mixed result to the raw writer; no solver call."""
from __future__ import annotations

import numpy as np


class BridgeRejected(ValueError):
    pass


def _vector_values(value, label):
    data = np.asarray(getattr(value, "array", value))
    if data.ndim != 1 or data.dtype != np.dtype("float64") or not np.all(np.isfinite(data)):
        raise BridgeRejected("INVALID_FLOAT64_VECTOR:" + label)
    return np.array(data, dtype="<f8", copy=True)


def build_raw_bundle(item: dict, result: dict) -> dict[str, np.ndarray]:
    """Adapt live mesh/DOF objects and completed in-memory vectors only.

    The caller must save diagnostics and hashes separately. This function does
    not create a KSP object, solve a system, or decide numerical acceptance.
    """
    if not isinstance(item, dict) or item.get("pressure") is None:
        raise BridgeRejected("MIXED_ITEM_REQUIRED")
    if not isinstance(result, dict) or result.get("status") not in {
        "SYNTHETIC_ADAPTER_TEST_NOT_RESULT", "CANDIDATE_SOLUTION_NOT_INDEPENDENTLY_ACCEPTED"
    }:
        raise BridgeRejected("UNVERIFIED_RESULT_STATUS_REQUIRED")
    algebraic = _vector_values(result["algebraic_solution_before_backsubstitution"], "algebraic")
    reconstructed = _vector_values(result["periodic_reconstructed_solution"], "reconstructed")
    W = item["mpc"].function_space
    if len(algebraic) != len(reconstructed) or len(reconstructed) != W.dofmap.index_map.size_local:
        raise BridgeRejected("MIXED_VECTOR_SIZE_MISMATCH")
    V, vmaps = W.sub(0).collapse()
    Q, qmaps = W.sub(1).collapse()
    if len(vmaps) != 1 or len(qmaps) != 1:
        raise BridgeRejected("COLLAPSED_MAP_FORMAT_CHANGED")
    vmap = np.asarray(vmaps[0], dtype="<i8")
    pmap = np.asarray(qmaps[0], dtype="<i8")
    vcoordinates = np.asarray(V.tabulate_dof_coordinates()[:, :2], dtype="<f8")
    pcoordinates = np.asarray(Q.tabulate_dof_coordinates()[:, :2], dtype="<f8")
    if (V.dofmap.index_map_bs != 2 or Q.dofmap.index_map_bs != 1
            or len(vmap) != 2 * len(vcoordinates)
            or len(pmap) != len(pcoordinates)
            or vmap.min() < 0 or pmap.min() < 0
            or max(vmap.max(), pmap.max()) >= len(reconstructed)
            or len(set(vmap)) != len(vmap) or len(set(pmap)) != len(pmap)
            or set(vmap) & set(pmap)):
        raise BridgeRejected("DOF_MAP_ORDER_OR_BLOCK_MISMATCH")
    original_Q, _ = item["space"].sub(1).collapse()
    original_pcoords = original_Q.tabulate_dof_coordinates()[:, :2]
    if not np.array_equal(original_pcoords, pcoordinates):
        raise BridgeRejected("PRESSURE_WEIGHT_DOF_ORDER_MISMATCH")
    pressure_raw = _vector_values(result["pressure_raw_P1"], "pressure_raw")
    pressure_shifted = _vector_values(result["pressure_zero_area_mean_P1"], "pressure_shifted")
    if len(pressure_raw) != len(pmap) or not np.array_equal(pressure_raw, reconstructed[pmap]):
        raise BridgeRejected("PRESSURE_RESULT_MAP_MISMATCH")
    weights = np.asarray(item["pressure"]["nodal_area_weights"], dtype="<f8").copy()
    if len(weights) != len(pmap) or np.any(weights <= 0):
        raise BridgeRejected("PRESSURE_WEIGHT_MISMATCH")
    mean = float(np.dot(weights, pressure_raw) / weights.sum())
    if not np.allclose(pressure_shifted, pressure_raw - mean, rtol=1e-13, atol=1e-13):
        raise BridgeRejected("PRESSURE_SHIFT_MISMATCH")
    links = item["stats"]["periodic_link_audit"]["pairs"]
    slaves = np.asarray([x["slave_dof"] for x in links], dtype="<i8")
    masters = np.asarray([x["master_dof"] for x in links], dtype="<i8")
    if not np.array_equal(np.sort(slaves), np.sort(np.asarray(item["mpc"].slaves))):
        raise BridgeRejected("PERIODIC_MAP_DIFFERS_FROM_MPC")
    domain = item["domain"]
    return {
        "mesh_coordinates_hat": np.asarray(domain.geometry.x[:, :2], dtype="<f8").copy(),
        "mesh_triangles": np.asarray(domain.geometry.dofmaps[0], dtype="<i8").copy(),
        "algebraic_solution_before_backsub": algebraic,
        "reconstructed_solution": reconstructed,
        "velocity_dof_coordinates_hat": np.repeat(vcoordinates, 2, axis=0),
        "velocity_dof_components": np.tile(np.asarray([0, 1], dtype="<i8"), len(vcoordinates)),
        "velocity_reconstructed_dof_indices": vmap,
        "velocity_reconstructed_values": reconstructed[vmap].copy(),
        "pressure_coordinates_hat": pcoordinates.copy(),
        "pressure_reconstructed_dof_indices": pmap,
        "wall_velocity_dof_indices": np.asarray(item["wall_bc"].dof_indices()[0], dtype="<i8").copy(),
        "pressure_area_weights_hat2": weights,
        "pressure_raw_P1": pressure_raw,
        "pressure_zero_mean_P1": pressure_shifted,
        "periodic_slave_dofs": slaves,
        "periodic_master_dofs": masters,
    }

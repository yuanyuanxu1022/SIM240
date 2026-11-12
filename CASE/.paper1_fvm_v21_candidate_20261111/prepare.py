#!/usr/bin/env python3
"""Generate fixed input dictionaries only. Never runs OpenFOAM or overwrites cases.

v2 changes relative to v1 (the v1 tree stays frozen as the record of the
h75_d0_T_flat REFERENCE_CHECK_FAIL):
  * per-level steady-iteration caps and matching wall-clock caps;
  * grid-continuation seeding: mid<-coarse, fine<-mid, tight<-fine, written by
    mapFields into the target's startTime directory 0.5, so the frozen 0/
    dictionaries are never rewritten;
  * the residualControl threshold is an early-exit trigger, not the acceptance
    rule; acceptance is decided post hoc by the numeric stopping criterion.
"""
from __future__ import annotations
from acceptance import RULE
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SELECTED = ((75, 100, "P"), (75, 100, "T"), (25, 100, "T"),
            (50, 120, "P"), (125, 120, "P"), (125, 120, "T"))
GRIDS_NM = (1.25, 0.625, 0.3125)
REPO = ROOT.parents[1]

# Steady-iteration cap per level. Measured on h75_d0_T_flat (Nz=120): the zero
# initial field needs about 4.0e4 steps to reach the production residual, so the
# caps below are safety ceilings, not planned workloads. simple.loop exits early
# when residualControl trips; a case that reaches its cap is recorded as a
# cap-stopped run; complete frozen post-hoc criteria may still accept it.
CAPS = {
    "coarse": dict(end_time=60000, wall_seconds=1800),
    "mid": dict(end_time=120000, wall_seconds=14400),
    "fine": dict(end_time=200000, wall_seconds=43200),
    "tight": dict(end_time=250000, wall_seconds=43200),
    "flat": dict(end_time=60000, wall_seconds=3600),
}
# Grid continuation: each level starts from its lower-resolution solution.
SEED_SOURCE = {"coarse": None, "mid": "coarse", "fine": "mid", "tight": "fine",
               "flat": None}
SEED_TIME = 0.5
# Early-exit trigger only. Acceptance is decided by the stopping criterion in
# run_one.py / postprocess.py. The tight level keeps the v1 tenfold tightening.
EXIT_TRIGGER = dict(p=("1e-11", "1e-10"), U=("1e-11", "1e-10"), v=("1e-11", "1e-10"))


def trigger(tight: bool) -> dict:
    slot = 0 if tight else 1
    return {key: value[slot] for key, value in EXIT_TRIGGER.items()}


def header(kind: str, name: str) -> str:
    return f"FoamFile\n{{ format ascii; class {kind}; object {name}; }}\n"


def mesh_dict(h: float, d: float, spacing: float) -> tuple[str, int]:
    # Coordinates are nanometres; blockMesh converts exactly once to metres.
    # A groove occupies x=[0,120], z=[0,d]. The whole gap is z=[d,d+h].
    # At x=0 below d is the solid ridge of the preceding period, hence a WALL.
    regions = [(0, 240, 0, h)] if d == 0 else [
        (0, 120, 0, d), (0, 120, d, d+h), (120, 240, d, d+h)]
    vertices: list[tuple[float, float, float]] = []
    blocks = []
    face_uses: dict[tuple[int, ...], list[tuple[int, ...]]] = {}
    count = 0
    for x0, x1, z0, z1 in regions:
        xyz = [(x0, 0, z0), (x1, 0, z0), (x1, 1, z0), (x0, 1, z0),
               (x0, 0, z1), (x1, 0, z1), (x1, 1, z1), (x0, 1, z1)]
        ids = []
        for point in xyz:
            if point not in vertices:
                vertices.append(point)
            ids.append(vertices.index(point))
        nx, nz = round((x1-x0)/spacing), round((z1-z0)/spacing)
        assert nx > 0 and nz > 0
        assert abs(nx*spacing-(x1-x0)) < 1e-10
        assert abs(nz*spacing-(z1-z0)) < 1e-10
        count += nx*nz
        blocks.append(f"hex ({' '.join(map(str, ids))}) ({nx} 1 {nz}) simpleGrading (1 1 1)")
        for loc in ((0,4,7,3), (1,2,6,5), (0,3,2,1),
                    (4,5,6,7), (0,1,5,4), (3,7,6,2)):
            f = tuple(ids[i] for i in loc)
            face_uses.setdefault(tuple(sorted(f)), []).append(f)
    patches: dict[str, list[tuple[int, ...]]] = {k: [] for k in
                                                ("xMinus", "xPlus", "walls", "frontBack")}
    for uses in face_uses.values():
        assert len(uses) in (1, 2)
        if len(uses) == 2:
            continue
        f = uses[0]
        ps = [vertices[v] for v in f]
        if len({v[1] for v in ps}) == 1:
            name = "frontBack"
        elif all(v[0] == 0 for v in ps) and min(v[2] for v in ps) >= d:
            name = "xMinus"
        elif all(v[0] == 240 for v in ps):
            name = "xPlus"
        else:
            name = "walls"
        patches[name].append(f)
    assert len(patches["xMinus"]) == len(patches["xPlus"]) == 1
    parts = [header("dictionary", "blockMeshDict"), "convertToMeters 1e-9;",
             "vertices\n(\n" + "\n".join("("+" ".join(f"{v:g}" for v in p)+")" for p in vertices) + "\n);",
             "blocks\n(\n"+"\n".join(blocks)+"\n);", "edges ();", "boundary\n("]
    for name, fs in patches.items():
        kind = "cyclic" if name.startswith("x") else ("empty" if name == "frontBack" else "wall")
        neighbour = ("neighbourPatch xPlus;" if name == "xMinus" else
                     "neighbourPatch xMinus;" if name == "xPlus" else "")
        faces = " ".join("("+" ".join(map(str, f))+")" for f in fs)
        parts.append(f"{name} {{ type {kind}; {neighbour} faces ({faces}); }}")
    parts.append(");\nmergePatchPairs ();\n")
    return "\n".join(parts), count


def field(name: str, direction: str) -> str:
    scalar = name in ("p", "v")
    dims = "[0 2 -2 0 0 0 0]" if name == "p" else "[0 1 -1 0 0 0 0]"
    zero = "0" if scalar else "(0 0 0)"
    wall = ("type fixedFluxPressure; value uniform 0;" if name == "p" else
            "type fixedValue; value uniform 0;" if name == "v" else "type noSlip;")
    return header("volScalarField" if scalar else "volVectorField", name) + f"""
dimensions {dims};
internalField uniform {zero};
boundaryField
{{
    xMinus {{ type cyclic; }}
    xPlus {{ type cyclic; }}
    walls {{ {wall} }}
    frontBack {{ type empty; }}
}}
"""


def frozen_anchors() -> list[dict]:
    """comparison_inputs.json is carried over byte-identically from v1."""
    frozen = ROOT / "comparison_inputs.json"
    if not frozen.exists():
        raise SystemExit("comparison_inputs.json is missing; copy it from the v1 release")
    anchors = json.loads(frozen.read_text())
    rows = list(csv.DictReader((REPO / "docs/reports/SIM240_manuscript_revision_20261018/map36_evidence.csv").open()))
    for anchor in anchors:
        row = next(r for r in rows if (int(r['h_nm']), int(r['d_nm']), r['direction'])
                   == (anchor['h_nm'], anchor['d_nm'], anchor['direction']))
        for key, column in (("K5_m3", "K_DNS_m3"), ("result_path", "result_path"),
                            ("result_sha256", "result_sha256")):
            if key == "K5_m3":
                if abs(anchor[key]-float(row[column])) > 0:
                    raise SystemExit("frozen anchor drifted: "+str(anchor))
            elif anchor[key] != row[column]:
                raise SystemExit("frozen anchor drifted: "+str(anchor))
    return anchors


def generate() -> None:
    output = ROOT / "prepared"
    if output.exists():
        raise SystemExit("Refusing to overwrite prepared/. Preserve its provenance or choose a new version.")
    frozen_anchors()
    plans = []
    entries = [(h, d, di, lev, dx, False) for h, d, di in SELECTED
               for lev, dx in zip(("coarse", "mid", "fine"), GRIDS_NM)]
    entries += [(h, d, di, "tight", GRIDS_NM[-1], True) for h, d, di in SELECTED]
    entries += [(75, 0, di, "flat", 0.625, False) for di in ("P", "T")]
    for h, d, di, level, dx, tight in entries:
        case_id = f"h{h}_d{d}_{di}_{level}"
        case = output/case_id
        for folder in ("0", "constant", "system"):
            (case/folder).mkdir(parents=True, exist_ok=False)
        text, ncells = mesh_dict(h, d, dx)
        (case/"system/blockMeshDict").write_text(text)
        (case/"constant/referenceProperties").write_text(header("dictionary", "referenceProperties")+f"""
direction {di};
nu [0 2 -1 0 0 0 0] 1e-6;
acceleration [0 1 -2 0 0 0 0] 1e5;
""")
        for name in (("v",) if di == "P" else ("U", "p")):
            (case/"0"/name).write_text(field(name, di))
        (case/"system/fvSchemes").write_text(header("dictionary", "fvSchemes")+"""
ddtSchemes { default steadyState; }
gradSchemes { default Gauss linear; }
divSchemes { default none; }
laplacianSchemes { default Gauss linear corrected; }
interpolationSchemes { default linear; }
snGradSchemes { default corrected; }
fluxRequired { default no; p; }
""")
        tol = "1e-13" if tight else "1e-12"
        limits = trigger(tight)
        if di == "P":
            residual = f"v {limits['v']};"
        else:
            residual = f"p {limits['p']}; U {limits['U']};"
        (case/"system/fvSolution").write_text(header("dictionary", "fvSolution")+f"""
solvers
{{
    v {{ solver PCG; preconditioner DIC; tolerance {tol}; relTol 0; }}
    U {{ solver smoothSolver; smoother symGaussSeidel; tolerance {tol}; relTol 0; }}
    p {{ solver GAMG; smoother DICGaussSeidel; tolerance {tol}; relTol 0; }}
}}
SIMPLE
{{
    nNonOrthogonalCorrectors 0;
    pRefCell 0;
    pRefValue 0;
    residualControl {{ {residual} }}
}}
relaxationFactors
{{
    fields {{ p 0.3; }}
    equations {{ U 0.7; }}
}}
""")
        seed_level = SEED_SOURCE[level]
        seed_from = f"h{h}_d{d}_{di}_{seed_level}" if seed_level else None
        start_time = SEED_TIME if seed_from else 0
        cap = CAPS[level]
        (case/"system/controlDict").write_text(header("dictionary", "controlDict")+f"""
application paper1StokesReference;
startFrom startTime;
startTime {start_time:g};
stopAt endTime;
endTime {cap['end_time']};
deltaT 1;
writeControl timeStep;
writeInterval 100;
purgeWrite 1;
writeFormat ascii;
writePrecision 17;
writeCompression off;
runTimeModifiable false;
""")
        metadata = dict(case_id=case_id, h_nm=h, d_nm=d, w_nm=120, P_nm=240,
                        Ly_nm=1, dx_nm=dx, direction=di, level=level,
                        nu_m2_s=1e-6, rho_kg_m3=1000, acceleration_m_s2=1e5,
                        expected_cells=ncells, expected_V_m3=240*(h+d/2)*1e-27,
                        Aplan_m2=240e-18, equation="scalar_Poisson" if di == "P" else "vector_Stokes",
                        transient=False, advection=False, tolerance_tightened=tight,
                        seed_from=seed_from, seed_time=SEED_TIME if seed_from else None,
                        seed_method="mapFields -consistent -mapMethod interpolate" if seed_from else None,
                        start_time=start_time, end_time_cap=cap["end_time"],
                        wall_clock_seconds=cap["wall_seconds"],
                        exit_trigger=limits,
                        flat_zero_component_exception=(d == 0 and di == "T"),
                        execution_authorized=False, solver_executed=False)
        (case/"case.json").write_text(json.dumps(metadata, indent=2)+"\n")
        plans.append(metadata)
    files = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in sorted(output.rglob('*')) if p.is_file()}
    files['comparison_inputs.json'] = hashlib.sha256((ROOT/'comparison_inputs.json').read_bytes()).hexdigest()
    manifest = dict(status="PREPARED_NOT_RUN", revision="v2.1_stopping_fix", cases=plans, sha256=files,
                    thresholds=dict(K_difference_percent=2.0, A_difference_percent=2.0,
                                    beta_difference_deg=0.40, flat_K_percent=0.1, flat_profile_percent=0.1,
                                    grid_mid_coarse_percent=1.0, grid_fine_mid_percent=0.5,
                                    algebraic_change_percent=0.05, section_spread_percent=0.1,
                                    power_balance_percent=0.1),
                    acceptance_rule=RULE,
                    resource_caps=CAPS,
                    output_criteria="Scheme A; preparation target, not a retrospective Gate change")
    (ROOT/"prepared_manifest.json").write_text(json.dumps(manifest, indent=2)+"\n")
    print(f"Prepared {len(plans)} inputs: 18 grid, 6 algebraic-tightening, 2 flat. No solver launched.")


if __name__ == "__main__":
    generate()

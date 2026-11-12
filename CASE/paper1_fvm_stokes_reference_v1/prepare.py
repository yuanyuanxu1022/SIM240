#!/usr/bin/env python3
"""Generate fixed input dictionaries only. Never runs OpenFOAM or overwrites cases."""
from __future__ import annotations
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SELECTED = ((75, 100, "P"), (75, 100, "T"), (25, 100, "T"),
            (50, 120, "P"), (125, 120, "P"), (125, 120, "T"))
GRIDS_NM = (1.25, 0.625, 0.3125)
REPO = ROOT.parents[1]


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


def generate() -> None:
    output = ROOT / "prepared"
    if output.exists():
        raise SystemExit("Refusing to overwrite prepared/. Preserve its provenance or choose a new version.")
    frozen = ROOT / "comparison_inputs.json"
    rows = list(csv.DictReader((REPO / "docs/reports/SIM240_manuscript_revision_20261018/map36_evidence.csv").open()))
    anchors = []
    for h, d, direction in SELECTED:
        row = next(r for r in rows if (int(r['h_nm']), int(r['d_nm']), r['direction']) == (h,d,direction))
        anchors.append({"h_nm": h, "d_nm": d, "direction": direction,
                        "K5_m3": float(row["K_DNS_m3"]),
                        "result_path": row["result_path"], "result_sha256": row["result_sha256"]})
    if frozen.exists():
        raise SystemExit("Refusing to overwrite frozen comparison_inputs.json")
    frozen.write_text(json.dumps(anchors, indent=2)+"\n")
    plans = []
    entries = [(h,d,di,lev,dx,False) for h,d,di in SELECTED
               for lev,dx in zip(("coarse","mid","fine"),GRIDS_NM)]
    entries += [(h,d,di,"tight",GRIDS_NM[-1],True) for h,d,di in SELECTED]
    entries += [(75,0,di,"flat",0.625,False) for di in ("P","T")]
    for h,d,di,level,dx,tight in entries:
        case_id=f"h{h}_d{d}_{di}_{level}"
        case=output/case_id
        for folder in ("0","constant","system"):
            (case/folder).mkdir(parents=True,exist_ok=False)
        text,ncells=mesh_dict(h,d,dx)
        (case/"system/blockMeshDict").write_text(text)
        (case/"constant/referenceProperties").write_text(header("dictionary","referenceProperties")+f"""
direction {di};
nu [0 2 -1 0 0 0 0] 1e-6;
acceleration [0 1 -2 0 0 0 0] 1e5;
""")
        for name in (("v",) if di == "P" else ("U","p")):
            (case/"0"/name).write_text(field(name,di))
        (case/"system/fvSchemes").write_text(header("dictionary","fvSchemes")+"""
ddtSchemes { default steadyState; }
gradSchemes { default Gauss linear; }
divSchemes { default none; }
laplacianSchemes { default Gauss linear corrected; }
interpolationSchemes { default linear; }
snGradSchemes { default corrected; }
fluxRequired { default no; p; }
""")
        tol="1e-13" if tight else "1e-12"
        outer="1e-11" if tight else "1e-10"
        residual=f"v {outer};" if di=="P" else f"p {outer}; U {outer};"
        (case/"system/fvSolution").write_text(header("dictionary","fvSolution")+f"""
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
        (case/"system/controlDict").write_text(header("dictionary","controlDict")+"""
application paper1StokesReference;
startFrom startTime;
startTime 0;
stopAt endTime;
endTime 6000;
deltaT 1;
writeControl timeStep;
writeInterval 100;
purgeWrite 1;
writeFormat ascii;
writePrecision 17;
writeCompression off;
runTimeModifiable false;
""")
        metadata=dict(case_id=case_id,h_nm=h,d_nm=d,w_nm=120,P_nm=240,
                      Ly_nm=1,dx_nm=dx,direction=di,level=level,
                      nu_m2_s=1e-6,rho_kg_m3=1000,acceleration_m_s2=1e5,
                      expected_cells=ncells,expected_V_m3=240*(h+d/2)*1e-27,
                      Aplan_m2=240e-18,equation="scalar_Poisson" if di=="P" else "vector_Stokes",
                      transient=False,advection=False,tolerance_tightened=tight,
                      execution_authorized=False,solver_executed=False)
        (case/"case.json").write_text(json.dumps(metadata,indent=2)+"\n")
        plans.append(metadata)
    files={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
           for p in sorted(output.rglob('*')) if p.is_file()}
    files['comparison_inputs.json']=hashlib.sha256(frozen.read_bytes()).hexdigest()
    manifest=dict(status="PREPARED_NOT_RUN",cases=plans,sha256=files,
                  thresholds=dict(K_difference_percent=2.0,A_difference_percent=2.0,
                      beta_difference_deg=0.40,flat_K_percent=0.1,flat_profile_percent=0.1,
                      grid_mid_coarse_percent=1.0,grid_fine_mid_percent=0.5,
                      algebraic_change_percent=0.05,section_spread_percent=0.1,
                      power_balance_percent=0.1),
                  output_criteria="Scheme A; preparation target, not a retrospective Gate change")
    (ROOT/"prepared_manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
    print(f"Prepared {len(plans)} inputs: 18 grid, 6 algebraic-tightening, 2 flat. No solver launched.")


if __name__ == "__main__":
    generate()

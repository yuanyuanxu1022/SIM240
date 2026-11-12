#!/usr/bin/env python3
"""Prepare REFINED-mesh FVM reference cases.  Writes inputs only, runs nothing.

WHY THIS TREE EXISTS
    In the frozen v2 release the case `h25_d100_T_fine` ended with
    `power_balance_percent = 0.146371`, above the internal 0.1 % ceiling, so
    its status is REFERENCE_CHECK_FAIL and `h25_d100_T_tight` was refused a
    seed.  Crucially, `tight` shares the *identical* mesh with `fine`
    (184320 cells, dx = 0.3125 nm); it only tightens residualControl.  Since
    power_balance measures the *spatial discretisation* mismatch between
    drive power and integrated viscous dissipation, tightening the iterative
    tolerance cannot improve it.  The only legitimate remedy is a finer mesh.

    This directory therefore adds a `refined` level at dx = 0.15625 nm
    (twice the resolution, four times the cells) for the geometries whose
    fine level failed.  It is a NEW study, not a modification of v2:

      * nothing under paper1_fvm_stokes_reference_v2/ is written, moved or
        re-hashed; its receipts and its FAIL verdict stand as the record;
      * the mesh generator, field dictionaries, schemes and solver settings
        are imported verbatim from the frozen v2 prepare.py so that ONLY the
        spacing changes -- same geometry, same boundary conditions, same
        discretisation, same physical parameters;
      * the acceptance ceiling is NOT relaxed: power_balance_percent must
        still be <= 0.1 % at the refined level;
      * by default the converged v2 fine solution is mapped onto the finer
        mesh as an INITIAL FIELD (mapFields -consistent -mapMethod
        interpolate).  Steady Stokes has a unique solution, so this changes
        the iteration count only, never the converged answer.  The v2 fine
        case was rejected for its *coarse-mesh* power balance; every
        acceptance metric here is recomputed from the refined field, so no
        coarse-mesh deficiency is inherited.  Pass --zero-init to start from
        a zero field instead.

USAGE
    /usr/bin/python3 prepare.py                 # h25_d100_T only (default)
    /usr/bin/python3 prepare.py --also-h125     # add the h125_d120_T case
    /usr/bin/python3 prepare.py --zero-init     # no mapped initial field
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
V2 = ROOT.parent / 'paper1_fvm_stokes_reference_v2'

# Import the frozen generators so that geometry, patches, fields, schemes and
# physical constants are literally the same code path as the v2 release.
sys.path.insert(0, str(V2))
from prepare import header, mesh_dict, field  # noqa: E402
from acceptance import RULE  # noqa: E402  - the frozen v2.1 stopping rule, reused as-is

# Fine level of v2 used 0.3125 nm.  Halving the spacing is the standard
# one-step refinement; it multiplies the 2-D cell count by four.
REFINED_DX_NM = 0.15625

# Geometries whose v2 fine level failed the power-balance ceiling.
# h25_d100_T_fine : 0.146371 %  -> confirmed FAIL
# h125_d120_T_fine: still running as of 2026-11-12; offered behind a flag so
#                   that it can be prepared only once its outcome is known.
DEFAULT_CASES = [(25, 100, 'T')]
OPTIONAL_CASES = [(125, 120, 'T')]

# The refined level is seeded from NOTHING (zero initial field), so it needs a
# generous iteration cap and wall clock.  h25_d100_T_fine took 2653 s on
# 184320 cells; the refined mesh has 4x the cells and, starting from zero,
# needs more iterations than a seeded run.  24 h is a ceiling, not a plan.
REFINED_CAP = dict(end_time=400000, wall_seconds=86400)


def generate(cases: list[tuple[int, int, str]], seeded: bool = True) -> None:
    output = ROOT / 'prepared'
    if output.exists():
        raise SystemExit('Refusing to overwrite prepared/.  '
                         'Archive it first if you intend to regenerate.')
    plans = []
    for h, d, di in cases:
        case_id = f'h{h}_d{d}_{di}_refined'
        case = output / case_id
        for folder in ('0', 'constant', 'system'):
            (case / folder).mkdir(parents=True, exist_ok=False)

        # Initial field: map the converged v2 fine-level solution onto this
        # finer mesh.  Steady Stokes has a unique solution, so the initial
        # field changes only the iteration count, never the converged answer.
        # The v2 fine case was flagged for its *coarse-mesh* power balance;
        # the refined power balance is recomputed here from the refined field.
        if seeded:
            source = (V2 / 'prepared' / f'h{h}_d{d}_{di}_fine').resolve()
            src_receipt = json.loads((source / 'runtime/receipt.json').read_text())
            times = {str(Path(p).parent) for p in src_receipt['native_field_sha256']}
            if len(times) != 1:
                raise SystemExit('seed source has no unique final time: ' + str(times))
            seed_time = next(iter(times))
            start_time = 0.5
            seed_from = str(source)
            seed_receipt_sha = hashlib.sha256(
                (source / 'runtime/receipt.json').read_bytes()).hexdigest()
        else:
            seed_time = None
            start_time = 0
            seed_from = None
            seed_receipt_sha = None

        text, ncells = mesh_dict(h, d, REFINED_DX_NM)
        (case / 'system/blockMeshDict').write_text(text)

        # Physical constants are copied verbatim from the v2 prepare.py.
        (case / 'constant/referenceProperties').write_text(
            header('dictionary', 'referenceProperties') + f"""
direction {di};
nu [0 2 -1 0 0 0 0] 1e-6;
acceleration [0 1 -2 0 0 0 0] 1e5;
""")
        for name in (('v',) if di == 'P' else ('U', 'p')):
            (case / '0' / name).write_text(field(name, di))

        (case / 'system/fvSchemes').write_text(header('dictionary', 'fvSchemes') + """
ddtSchemes { default steadyState; }
gradSchemes { default Gauss linear; }
divSchemes { default none; }
laplacianSchemes { default Gauss linear corrected; }
interpolationSchemes { default linear; }
snGradSchemes { default corrected; }
fluxRequired { default no; p; }
""")

        # Identical linear-solver settings and residualControl as the v2
        # non-tight levels.  Nothing is loosened; only the mesh is finer.
        residual = f"v 1e-10;" if di == 'P' else "p 1e-10; U 1e-10;"
        (case / 'system/fvSolution').write_text(header('dictionary', 'fvSolution') + f"""
solvers
{{
    v {{ solver PCG; preconditioner DIC; tolerance 1e-12; relTol 0; }}
    U {{ solver smoothSolver; smoother symGaussSeidel; tolerance 1e-12; relTol 0; }}
    p {{ solver GAMG; smoother DICGaussSeidel; tolerance 1e-12; relTol 0; }}
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

        (case / 'system/controlDict').write_text(header('dictionary', 'controlDict') + f"""
application paper1StokesReference;
startFrom startTime;
startTime {start_time:g};
stopAt endTime;
endTime {REFINED_CAP['end_time']};
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
                        Ly_nm=1, dx_nm=REFINED_DX_NM, direction=di, level='refined',
                        nu_m2_s=1e-6, rho_kg_m3=1000, acceleration_m_s2=1e5,
                        expected_cells=ncells, expected_V_m3=240 * (h + d / 2) * 1e-27,
                        Aplan_m2=240e-18,
                        equation='scalar_Poisson' if di == 'P' else 'vector_Stokes',
                        transient=False, advection=False, tolerance_tightened=False,
                        seed_from=seed_from, seed_time=seed_time,
                        seed_method='mapFields -consistent -mapMethod interpolate' if seeded else None,
                        seed_source_receipt_sha256=seed_receipt_sha,
                        seed_note='Initial field only.  Steady Stokes has a unique '
                                  'solution; the initial field sets the iteration count, '
                                  'not the answer.  All acceptance metrics are recomputed '
                                  'from the refined-mesh field.' if seeded else None,
                        start_time=start_time, end_time_cap=REFINED_CAP['end_time'],
                        wall_clock_seconds=REFINED_CAP['wall_seconds'],
                        exit_trigger=dict(p='1e-10', U='1e-10', v='1e-10'),
                        flat_zero_component_exception=False,
                        execution_authorized=False, solver_executed=False,
                        purpose='mesh remedy for the v2 fine-level power-balance failure',
                        supersedes=f'h{h}_d{d}_{di}_fine')
        (case / 'case.json').write_text(json.dumps(metadata, indent=2) + '\n')
        plans.append(metadata)
        print(f'  {case_id}: {ncells} cells at dx={REFINED_DX_NM} nm')

    files = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in sorted(output.rglob('*')) if p.is_file()}
    solver = V2 / 'bin/paper1StokesReference'
    manifest = dict(
        status='PREPARED_NOT_RUN',
        revision='v3_refined_mesh_remedy',
        derived_from='paper1_fvm_stokes_reference_v2 (untouched)',
        refined_dx_nm=REFINED_DX_NM,
        cases=plans,
        sha256=files,
        solver_path=str(solver),
        solver_sha256=hashlib.sha256(solver.read_bytes()).hexdigest(),
        acceptance_rule=RULE,
        thresholds=dict(power_balance_percent=0.1,
                        section_spread_percent=0.1,
                        section_vs_volume_percent=0.1,
                        grid_refined_fine_percent=0.5),
        note='Acceptance ceilings are inherited from v2 unchanged.  '
             'A refined case is accepted only if power_balance_percent <= 0.1 %, '
             'the same ceiling that h25_d100_T_fine failed.')
    (ROOT / 'prepared_manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(f'Prepared {len(plans)} refined case(s).  No solver launched.')


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--also-h125', action='store_true',
                    help='also prepare h125_d120_T_refined')
    ap.add_argument('--zero-init', action='store_true',
                    help='start from a zero field instead of mapping the v2 fine solution')
    args = ap.parse_args()
    generate(DEFAULT_CASES + (OPTIONAL_CASES if args.also_h125 else []),
             seeded=not args.zero_init)

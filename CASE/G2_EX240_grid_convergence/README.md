# G2 EX240 grid convergence

This isolated case implements SIM240 G2 Step 3 for the fixed single-phase,
fixed-geometry EX240 RVE. It runs Smooth75, EX240 parallel, and EX240
perpendicular transport at `dx = 5.0, 2.5, 1.25 nm`.

The case does not modify the frozen G1/G2 sources. `src/generate_step3_sources.py`
creates auditable diagnostic variants under `build/generated/`; the formal batch
records both frozen-base and generated-source hashes.

Workflow:

1. `scripts/preflight_grid.py --write` checks exact geometry representation and
   physical similarity.
2. `make -C src -j2` generates and compiles the four executables.
3. `scripts/run_grid_matrix.sh` performs all zero-step boundary prechecks before
   starting any steady run, then runs the nine formal points and post-processes
   the batch.

Large runs belong in `tmux`. The runner writes each log and exit code into its
own run directory and never overwrites an existing batch.

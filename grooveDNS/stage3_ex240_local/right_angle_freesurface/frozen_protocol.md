# SIM-EC1XT240 STEP 6-E frozen protocol

- Geometry: one `240 nm × 240 nm` orthogonal cross-junction cell, `h=65 nm`, recess depth `100 nm`, `dx=5 nm`.
- Initial state: the full 65 nm gap is liquid; one half-filled interface layer is placed at the groove mouth; the remaining recess is gas.
- Boundary conditions: x/y periodic, fixed no-slip substrate and grooved head in z, zero body force.
- FreeSurface: OpenLB D3Q27 fields and staged post-processors, `sigma=0.0309 N/m`, `dt=1e-12 s`, `tau=0.62`.
- Wetting: solid `EPSILON=1`, the qualitative wetting-wall setting documented by this OpenLB version. No numerical contact angle is prescribed or calibrated.
- Gas: FreeSurface gas state at reference pressure; gas momentum and trapped-gas pressure are not solved.
- Formal duration: 8000 steps unless a frozen stability check stops the run.
- Checks: finite fields, Mach `<=0.05`, rho in `[0.8,1.2]`, unchanged material, liquid-mass drift `<=5e-3`, maximum one-step fill change `<=0.02`, and `EPSILON` within the FreeSurface transition band `[-0.00100001,1.00100001]`.
- A formal filling PASS additionally requires the groove fill fraction to increase by at least `0.01` from its initial value.

The protocol is a functional capillary-filling baseline, not a confirmed material/contact-angle case.

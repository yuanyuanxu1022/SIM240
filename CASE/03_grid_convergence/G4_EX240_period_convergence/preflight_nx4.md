# G4 preflight (static)

- frozen G2 source SHA-256 pinned OK (4acd63db67e2...)
- nx=1: period 96 / groove 48 / mesa 24 / gap 30 / depth 40 cells (integer, independent of nx)
- nx=2: period 96 / groove 48 / mesa 24 / gap 30 / depth 40 cells (integer, independent of nx)
- nx=4: period 96 / groove 48 / mesa 24 / gap 30 / depth 40 cells (integer, independent of nx)
- nx=8: period 96 / groove 48 / mesa 24 / gap 30 / depth 40 cells (integer, independent of nx)
- binary OK: g4_nx4_serial_a5e4 sha256=987c02595606b650...
- binary OK: g4_nx4_serial_a1e5 sha256=732a4c226bdf2c72...
- binary OK: g4_nx4_serial_a2e5 sha256=e7bccd59229b208e...
- binary OK: g4_nx4_mpi_a5e4 sha256=e8f0e89314d73e29...
- binary OK: g4_nx4_mpi_a1e5 sha256=256aa921b52afb77...
- binary OK: g4_nx4_mpi_a2e5 sha256=0073d1b0a5193315...
- nx=1: fluid_nodes=460800 candidate_links=130176 maximum_steps=60000
- nx=1: referenceHeight=125.0 nm (expect 125)
- nx=2: fluid_nodes=921600 candidate_links=260352 maximum_steps=240000
- nx=2: referenceHeight=125.0 nm (expect 125)
- nx=4: fluid_nodes=1843200 candidate_links=520704 maximum_steps=960000
- nx=4: referenceHeight=125.0 nm (expect 125)
- nx=8: fluid_nodes=3686400 candidate_links=1041408 maximum_steps=3840000
- nx=8: referenceHeight=125.0 nm (expect 125)
- level nx=4: production ranks=16 (G4_EXPECTED_RANKS), per-rank cells 115200

preflight_PASS=true

# G4 preflight (static)

- frozen G2 source SHA-256 pinned OK (4acd63db67e2...)
- nx=1: period 96 / groove 48 / mesa 24 / gap 30 / depth 40 cells (integer, independent of nx)
- nx=2: period 96 / groove 48 / mesa 24 / gap 30 / depth 40 cells (integer, independent of nx)
- nx=4: period 96 / groove 48 / mesa 24 / gap 30 / depth 40 cells (integer, independent of nx)
- nx=8: period 96 / groove 48 / mesa 24 / gap 30 / depth 40 cells (integer, independent of nx)
- binary OK: g4_nx2_serial_a5e4 sha256=9ae472b0c6007141...
- binary OK: g4_nx2_serial_a1e5 sha256=d9f79a07b4881bee...
- binary OK: g4_nx2_serial_a2e5 sha256=a98e52505ead76eb...
- binary OK: g4_nx2_mpi_a5e4 sha256=e573643a78050f17...
- binary OK: g4_nx2_mpi_a1e5 sha256=6dbf46203dc0771d...
- binary OK: g4_nx2_mpi_a2e5 sha256=c9f3f3156a281568...
- nx=1: fluid_nodes=460800 candidate_links=130176 maximum_steps=60000
- nx=1: referenceHeight=125.0 nm (expect 125)
- nx=2: fluid_nodes=921600 candidate_links=260352 maximum_steps=240000
- nx=2: referenceHeight=125.0 nm (expect 125)
- nx=4: fluid_nodes=1843200 candidate_links=520704 maximum_steps=960000
- nx=4: referenceHeight=125.0 nm (expect 125)
- nx=8: fluid_nodes=3686400 candidate_links=1041408 maximum_steps=3840000
- nx=8: referenceHeight=125.0 nm (expect 125)
- level nx=2: production ranks=8 (G4_EXPECTED_RANKS), per-rank cells 115200

preflight_PASS=true

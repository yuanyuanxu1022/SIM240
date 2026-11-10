# Preparation-only development record

No formal spatial calculation occurred.

- The first static reference generator attempted eigvals on a 19x1 array and the tool returned `numpy.linalg.LinAlgError: Last 2 dimensions of the array must be square`. It was corrected to a 19x19 matrix before generating the accepted references; no solver was involved. This entry transcribes the tool result, not a newly captured raw log.
- Local build v1 failed on ambiguous D2/D3 names; `build_local_v1.log`, its exit code and `alpha_collision_v1_failed.cpp` preserve the compiler evidence. v2 succeeded.
- C build v1 failed on ambiguous statistics name; `build_c_v1.log`, its exit code and `coupled_v1_failed.cpp` preserve it. v2 succeeded without warnings.
- Verification v1 failed because another task updated the shared first-paper prefix while this task had not edited the shared files. v2/final record concurrent snapshot hashes instead of restoring a stale prefix. Physics limits were not changed.
- Formal alpha and C batch directories do not exist. Only local CellD and explicit zero-step preparations were executed.

#!/usr/bin/env bash
set -u -o pipefail

# First-stage G3-h runner: only h=50/125 nm, P/T, completing the
# documented 50/75/125 nm subset.  The protocol's h=25/100 nm points are
# intentionally outside this runner.
case_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
repo_root=$(cd "$case_root/../../.." && pwd)
openlb_root=/home/dell/openlb
results_root="$case_root/results"
status=0

for height_nm in 50 125; do
  binary="$case_root/build/g3_ex240_h${height_nm}"
  source="$case_root/build/generated/g3_ex240_h${height_nm}.cpp"
  if [[ ! -x "$binary" ]]; then
    echo "missing executable: $binary" >&2
    status=2
    continue
  fi
  if [[ ! -f "$source" ]]; then
    echo "missing generated source: $source" >&2
    status=2
    continue
  fi
  for direction in P T; do
    run_id="g3h_formal_h${height_nm}_${direction}_$(date +%Y%m%dT%H%M%S%z)"
    output_dir="$results_root/$run_id"
    if ! mkdir "$output_dir"; then
      echo "refusing existing or uncreatable output directory: $output_dir" >&2
      status=2
      continue
    fi
    {
      printf 'run_id=%s\n' "$run_id"
      printf 'formal_simulation=true\n'
      printf 'case=G3_EX240_height_sweep\nheight_nm=%s\ndirection=%s\n' "$height_nm" "$direction"
      printf 'rho_kg_m3=1000\nnu_m2_s=1e-6\nmu_Pa_s=1e-3\n'
      printf 'dx_nm=2.5\ndt_s=1.0416666666666667e-12\ntau=1.0\n'
      printf 'acceleration_m_s2=1e5\nperiodicity=x_y\nmpi_ranks=1\n'
      printf 'descriptor=D3Q19_FORCE\ncollision=ForcedBGK\nwall_boundary=Bouzidi_zero_velocity_exact_EX240\n'
      printf 'sim240_repository_commit=%s\n' "$(git -C "$repo_root" rev-parse HEAD)"
      printf 'openlb_version=1.8r1\nopenlb_commit=%s\n' "$(git -C "$openlb_root" rev-parse HEAD)"
      if [[ -n "$(git -C "$openlb_root" status --short --untracked-files=no)" ]]; then
        printf 'openlb_tracked_worktree=dirty\n'
      else
        printf 'openlb_tracked_worktree=clean\n'
      fi
      printf 'frozen_g2_source_sha256=4acd63db67e273f87fed487fa7d1866f18dc82c018aaba1151f44882bd021002\n'
      printf 'generated_source_sha256=%s\n' "$(sha256sum "$source" | awk '{print $1}')"
      printf 'binary_sha256=%s\n' "$(sha256sum "$binary" | awk '{print $1}')"
    } > "$output_dir/run_manifest.txt"
    echo "starting height=$height_nm direction=$direction output=$output_dir"
    "$binary" steady "$direction" "$output_dir" > "$output_dir/run.log" 2>&1
    code=$?
    printf '%s\n' "$code" > "$output_dir/exit_code.txt"
    echo "finished height=$height_nm direction=$direction exit_code=$code output=$output_dir"
    if [[ "$code" -ne 0 ]]; then
      status=1
    fi
  done
done

exit "$status"

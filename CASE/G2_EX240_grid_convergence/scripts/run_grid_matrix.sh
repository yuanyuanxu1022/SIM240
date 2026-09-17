#!/usr/bin/env bash
set -u -o pipefail

case_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
repo_root=$(cd "$case_root/../.." && pwd)
protocol="$case_root/STEP3_PROTOCOL.md"
preflight="$case_root/scripts/preflight_grid.py"
postprocess="$case_root/scripts/postprocess_grid.py"
build_dir="$case_root/build"
generated_dir="$build_dir/generated"
smooth_binary="$build_dir/g2_smooth75_step3"

python3 "$preflight" || exit $?

for binary in \
  "$smooth_binary" \
  "$build_dir/g2_ex240_dx5" \
  "$build_dir/g2_ex240_dx2p5" \
  "$build_dir/g2_ex240_dx1p25"; do
  if [[ ! -x "$binary" ]]; then
    echo "missing executable: $binary" >&2
    exit 2
  fi
done

batch_id="g2_grid_$(date +%Y%m%dT%H%M%S%z)"
batch_dir="$case_root/results/$batch_id"
if [[ -e "$batch_dir" ]]; then
  echo "refusing to overwrite $batch_dir" >&2
  exit 2
fi
mkdir -p "$batch_dir/runs"
printf '%s\n' "$batch_dir" > "$case_root/latest_batch.txt"

{
  printf '# SIM240 G2 Step 3 source manifest\n\n'
  printf -- '- batch_id: `%s`\n' "$batch_id"
  printf -- '- repository_commit: `%s`\n' "$(git -C "$repo_root" rev-parse HEAD)"
  printf -- '- generated_at: `%s`\n' "$(date --iso-8601=seconds)"
  printf -- '- compiler: `%s`\n' "$(mpic++ --version | head -1)"
  printf -- '- OpenLB build tag: `5953d8a-dirty`\n'
  printf '\n## SHA-256\n\n```text\n'
  sha256sum \
    "$repo_root/CASE/G2_EX240_single_period_transport/src/g2_ex240_single_period_transport.cpp" \
    "$repo_root/CASE/G1_Poiseuille_Bouzidi_Validation/src/g1_poiseuille_bouzidi_validation.cpp" \
    "$protocol" \
    "$case_root/REUSE_AUDIT.md" \
    "$case_root/grid_similarity_audit.csv" \
    "$case_root/src/generate_step3_sources.py" \
    "$generated_dir/g2_smooth75_step3.cpp" \
    "$generated_dir/g2_ex240_dx5.cpp" \
    "$generated_dir/g2_ex240_dx2p5.cpp" \
    "$generated_dir/g2_ex240_dx1p25.cpp" \
    "$smooth_binary" \
    "$build_dir/g2_ex240_dx5" \
    "$build_dir/g2_ex240_dx2p5" \
    "$build_dir/g2_ex240_dx1p25"
  printf '```\n\n## Repository status at launch\n\n```text\n'
  git -C "$repo_root" status --short
  printf '```\n'
} > "$batch_dir/SOURCE_MANIFEST.md"

write_manifest() {
  local output_dir=$1
  local run_id=$2
  local dx_nm=$3
  local case_name=$4
  local direction=$5
  local binary=$6
  local generated_source=$7
  {
    printf 'run_id=%s\n' "$run_id"
    printf 'case=%s\n' "$case_name"
    printf 'direction=%s\n' "$direction"
    printf 'dx_nm=%s\n' "$dx_nm"
    printf 'tau=1.0\n'
    printf 'rho_phys_kg_m3=1000\n'
    printf 'nu_phys_m2_s=1.0e-6\n'
    printf 'acceleration_m_s2=1.0e5\n'
    printf 'period_nm=240\nmesa_nm=60\ngroove_nm=120\ngroove_depth_nm=100\nmesa_gap_nm=75\n'
    printf 'descriptor=D3Q19_FORCE\ncollision=ForcedBGK\nwall_boundary=Bouzidi\nperiodicity=x_y\n'
    printf 'protocol=%s\n' "$protocol"
    printf 'binary=%s\n' "$binary"
    printf 'generated_source=%s\n' "$generated_source"
    sha256sum "$protocol" "$binary" "$generated_source"
  } > "$output_dir/run_manifest.txt"
}

binary_for() {
  local tag=$1
  local case_name=$2
  if [[ "$case_name" == "Smooth75" ]]; then
    printf '%s\n' "$smooth_binary"
  else
    printf '%s\n' "$build_dir/g2_ex240_dx${tag}"
  fi
}

source_for() {
  local tag=$1
  local case_name=$2
  if [[ "$case_name" == "Smooth75" ]]; then
    printf '%s\n' "$generated_dir/g2_smooth75_step3.cpp"
  else
    printf '%s\n' "$generated_dir/g2_ex240_dx${tag}.cpp"
  fi
}

direction_for() {
  local case_name=$1
  case "$case_name" in
    Smooth75) printf 'smooth\n' ;;
    EX240_parallel) printf 'parallel\n' ;;
    EX240_perpendicular) printf 'perpendicular\n' ;;
    *) return 2 ;;
  esac
}

run_precheck() {
  local tag=$1
  local dx_nm=$2
  local case_name=$3
  local run_id="dx${tag}_${case_name}"
  local run_root="$batch_dir/runs/dx${tag}/${case_name}"
  local precheck_dir="$run_root/precheck"
  local steady_dir="$run_root/steady"
  local binary
  local generated_source
  local direction
  binary=$(binary_for "$tag" "$case_name")
  generated_source=$(source_for "$tag" "$case_name")
  direction=$(direction_for "$case_name")
  mkdir -p "$precheck_dir" "$steady_dir"
  write_manifest "$precheck_dir" "$run_id" "$dx_nm" "$case_name" "$direction" "$binary" "$generated_source"
  write_manifest "$steady_dir" "$run_id" "$dx_nm" "$case_name" "$direction" "$binary" "$generated_source"

  if [[ "$case_name" == "Smooth75" ]]; then
    "$binary" precheck "$precheck_dir" "$dx_nm" 1.0 100000 \
      > "$precheck_dir/run.log" 2>&1
  elif [[ "$case_name" == "EX240_parallel" ]]; then
    "$binary" precheck P "$precheck_dir" > "$precheck_dir/run.log" 2>&1
  else
    "$binary" precheck T "$precheck_dir" > "$precheck_dir/run.log" 2>&1
  fi
  local code=$?
  printf '%s\n' "$code" > "$precheck_dir/exit_code.txt"
  echo "precheck run=$run_id exit=$code"
  return "$code"
}

run_steady() {
  local tag=$1
  local dx_nm=$2
  local case_name=$3
  local run_id="dx${tag}_${case_name}"
  local steady_dir="$batch_dir/runs/dx${tag}/${case_name}/steady"
  local binary
  binary=$(binary_for "$tag" "$case_name")
  if [[ "$case_name" == "Smooth75" ]]; then
    "$binary" steady "$steady_dir" "$dx_nm" 1.0 100000 \
      > "$steady_dir/run.log" 2>&1
  elif [[ "$case_name" == "EX240_parallel" ]]; then
    "$binary" steady P "$steady_dir" > "$steady_dir/run.log" 2>&1
  else
    "$binary" steady T "$steady_dir" > "$steady_dir/run.log" 2>&1
  fi
  local code=$?
  printf '%s\n' "$code" > "$steady_dir/exit_code.txt"
  echo "steady run=$run_id exit=$code"
  return "$code"
}

grid_tags=(5 2p5 1p25)
grid_dx=(5.0 2.5 1.25)
case_names=(Smooth75 EX240_parallel EX240_perpendicular)

precheck_failure=0
for index in 0 1 2; do
  for case_name in "${case_names[@]}"; do
    run_precheck "${grid_tags[$index]}" "${grid_dx[$index]}" "$case_name" || precheck_failure=1
  done
done
if [[ $precheck_failure -ne 0 ]]; then
  printf 'PRECHECK_MATRIX=FAIL\n' > "$batch_dir/batch_status.txt"
  exit 3
fi

steady_failure=0
for index in 0 1 2; do
  for case_name in "${case_names[@]}"; do
    run_steady "${grid_tags[$index]}" "${grid_dx[$index]}" "$case_name" || steady_failure=1
  done
done

python3 "$postprocess" "$batch_dir"
post_code=$?
printf '%s\n' "$post_code" > "$batch_dir/postprocess_exit_code.txt"
{
  printf 'PRECHECK_MATRIX=PASS\n'
  printf 'STEADY_MATRIX=%s\n' "$([[ $steady_failure -eq 0 ]] && printf PASS || printf FAIL)"
  printf 'POSTPROCESS_EXIT=%s\n' "$post_code"
} > "$batch_dir/batch_status.txt"

if [[ $steady_failure -ne 0 ]]; then
  exit 3
fi
exit "$post_code"

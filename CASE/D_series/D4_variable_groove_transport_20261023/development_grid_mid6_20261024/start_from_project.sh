#!/bin/bash
# Invocation wrapper only: preserve the frozen runner, permit and scientific inputs.
set -euo pipefail
mode="${1:---check}"
if [[ "$#" -gt 1 || ( "$mode" != "--check" && "$mode" != "--execute" ) ]]; then
  echo 'Usage: start_from_project.sh [--check|--execute]' >&2
  exit 2
fi
stage_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
project_dir="$(cd -- "$stage_dir/../../../.." && pwd -P)"
cd -- "$project_dir"
if [[ "$mode" == "--execute" ]]; then
  # The log survives an early exit before the formal batch directory is created.
  exec /usr/bin/python3 "$stage_dir/run_mid6.py" \
    --batch-id development_grid_mid6_20261024_v1 --execute \
    >> "$stage_dir/evidence/startup_console.log" 2>&1
else
  /usr/bin/python3 "$stage_dir/run_mid6.py" \
    --batch-id development_grid_mid6_20261024_v1 \
    | /usr/bin/tee "$stage_dir/evidence/startup_check.log"
fi

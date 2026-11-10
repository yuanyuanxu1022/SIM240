#!/bin/bash
# D2 决定性加密算例（4 个正式算例：h25/d100 与 h125/d120，P/T 两方向，dx=2.5nm）
# 目的：检验 V2 残差随 h 的漂移是网格假象还是模型缺陷（见 REPORT_ROUND1.md P1/P3）
# 流程遵循历史冻结口径：先写 run_manifest.txt（来源记录）→ precheck（几何/q 审计）→ 通过后才跑 steady
# 程序自带保护：无 manifest 拒绝运行；已有 result.txt 拒绝覆盖。脚本可安全重复执行（不会覆盖旧结果）。
set -u
cd /home/dell/yuanyuanxu/SIM240/CASE/D_series/D2_groove_error_map || exit 1

BIN="/home/dell/yuanyuanxu/SIM240/CASE/D_series/D2_groove_error_map/build/d2_groove_error_map"
HASH=$(sha256sum "$BIN" | cut -d' ' -f1)
LOG="results/dx25_refine4_run_20261018.log"
echo "=== dx25_refine4 启动 $(date -Is) binary_sha256=$HASH ===" >> "$LOG"

run_case() {
  local dir_letter=$1 h=$2 d=$3
  local base="results/h${h}_d${d}_dx2.5_${dir_letter}"
  local cid="D2-${dir_letter}-h${h}-d${d}-dx2.5"

  for mode in precheck steady; do
    mkdir -p "$base/$mode"
    cat > "$base/$mode/run_manifest.txt" <<EOF2
case_id=${cid}
direction=${dir_letter}
dx_nm=2.5
tau=1.0
acceleration_m_s2=1e5
mesa_gap_nm=${h}
groove_depth_nm=${d}
binary=${BIN}
binary_sha256=${HASH}
EOF2
  done

  ./build/d2_groove_error_map precheck "$dir_letter" "$base/precheck" 2.5 "$h" "$d" >> "$LOG" 2>&1
  echo $? > "$base/precheck/exit_code.txt"
  echo "--- ${cid} precheck exit=$(cat "$base/precheck/exit_code.txt") $(date -Is)" >> "$LOG"

  if [ "$(cat "$base/precheck/exit_code.txt")" != "0" ]; then
    echo "--- ${cid} precheck 未通过，跳过 steady" >> "$LOG"
    return 1
  fi

  ./build/d2_groove_error_map steady "$dir_letter" "$base/steady" 2.5 "$h" "$d" >> "$LOG" 2>&1
  echo $? > "$base/steady/exit_code.txt"
  echo "--- ${cid} steady exit=$(cat "$base/steady/exit_code.txt") $(date -Is)" >> "$LOG"
}

run_case P 25 100
run_case T 25 100
run_case P 125 120
run_case T 125 120

echo "=== dx25_refine4 全部结束 $(date -Is) ===" >> "$LOG"

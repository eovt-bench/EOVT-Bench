#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
VARIANT="${1:?Usage: run_all_tasks.sh oracle_pid|rgb_tracker_pid [GPU]}"
GPU="${2:-0}"
if [[ "${3:-}" != "--legacy-online-metrics" ]]; then
 echo "OR/IC online logging is historical. For an explicitly historical three-task run, use:" >&2
 echo "  bash baselines/scripts/run_all_tasks.sh $VARIANT $GPU --legacy-online-metrics" >&2
 echo "For current v0.2 scoring, see evaluation/PROTOCOL.md." >&2
 exit 2
fi
cd "$ROOT"
for TASK in stt or ic; do
 EXTRA=()
 if [[ "$TASK" != "stt" ]]; then EXTRA+=(--legacy-online-metrics); fi
 python run_baseline.py --variant "$VARIANT" --task "$TASK" --gpu "$GPU" --resume "${EXTRA[@]}"
done

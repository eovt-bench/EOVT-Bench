#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
VARIANT="${1:?Usage: run_all_tasks.sh oracle_pid|rgb_tracker_pid [GPU]}"
GPU="${2:-0}"
cd "$ROOT"
for TASK in stt or ic; do
 python run_baseline.py --variant "$VARIANT" --task "$TASK" --gpu "$GPU" --resume
done

#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
export PYTHONPATH="$ROOT/baselines${PYTHONPATH:+:$PYTHONPATH}"
export PYTHONDONTWRITEBYTECODE=1
python -m unittest discover -s baselines/tests -v
python -m unittest discover -s evaluation/tests -v
python run_baseline.py --variant oracle_pid --task stt --help >/dev/null
python evaluation/aggregate_results.py --help >/dev/null
python evaluation/validate_package.py

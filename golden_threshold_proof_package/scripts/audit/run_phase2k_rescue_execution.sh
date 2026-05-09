#!/usr/bin/env bash
set -euo pipefail
export PYTHONPATH="$(pwd):${PYTHONPATH:-}"

# Phase-2K full rescue execution/merge controller.
# Use --site so the command can see theorem-grade numerical dependencies
# installed in the normal Python environment. Remove --strict while diagnosing.
python scripts/audit/run_lower_anchor_phase2k_rescue_execution.py \
  --execute \
  --site \
  --timeout-seconds 7200 \
  --strict

#!/usr/bin/env python3
from __future__ import annotations

"""Endpoint probe alias for the Phase-2N single-N runner.

Use this when testing the alternative Theorem III route: an independent final
lower-anchor certificate at K > the challenger upper ceiling, rather than a full
microsegment collar continuation.  Arguments are identical to
run_lower_anchor_phase2n_single_N_probe.py.
"""

from pathlib import Path
import importlib.util
import sys

ROOT = Path(__file__).resolve().parents[2]
SINGLE = ROOT / "scripts" / "audit" / "run_lower_anchor_phase2n_single_N_probe.py"

spec = importlib.util.spec_from_file_location("phase2n_single_runner", SINGLE)
if spec is None or spec.loader is None:
    raise SystemExit("could not load Phase-2N single-N runner")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

if __name__ == "__main__":
    raise SystemExit(module.main())

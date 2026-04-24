from __future__ import annotations

from pathlib import Path
import sys
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import math

from kam_theorem_suite.proof_driver import build_torus_continuation_report

golden = (math.sqrt(5.0) - 1.0) / 2.0
report = build_torus_continuation_report(golden, [0.5, 0.7, 0.9, 1.0], N=64)
print("validated_fraction:", report["validated_fraction"])
for step in report["steps"]:
    print(step["K"], step["success"], step["bridge_quality"], step["oversampled_residual_inf"])

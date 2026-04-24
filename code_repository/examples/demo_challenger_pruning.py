from __future__ import annotations

from pathlib import Path
import sys
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import json

from kam_theorem_suite.challenger_pruning import ChallengerSpec
from kam_theorem_suite.proof_driver import build_challenger_pruning_report_driver

def main() -> None:
    challengers = [
        ChallengerSpec(preperiod=(), period=(2,), threshold_upper_bound=0.96, label="silver"),
        ChallengerSpec(preperiod=(), period=(3,), threshold_upper_bound=None, label="bronze"),
        ChallengerSpec(preperiod=(), period=(1, 2), threshold_upper_bound=0.9725, label="mixed"),
    ]
    report = build_challenger_pruning_report_driver(challengers, golden_lower_bound=0.9712)
    outdir = Path(__file__).resolve().parents[1] / "outputs"
    outdir.mkdir(exist_ok=True)
    outpath = outdir / "demo_challenger_pruning.json"
    outpath.write_text(json.dumps(report, indent=2))
    print(json.dumps({
        "status": report["status"],
        "dominated_count": report["dominated_count"],
        "overlapping_count": report["overlapping_count"],
        "arithmetic_only_count": report["arithmetic_only_count"],
        "output": str(outpath),
    }, indent=2))

if __name__ == "__main__":
    main()

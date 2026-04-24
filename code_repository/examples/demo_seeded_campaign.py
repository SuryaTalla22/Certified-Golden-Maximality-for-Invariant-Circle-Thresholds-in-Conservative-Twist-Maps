from __future__ import annotations

from pathlib import Path
import sys
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import json

from kam_theorem_suite import ArithmeticClassSpec
from kam_theorem_suite.proof_driver import build_seeded_class_campaign_report

def main() -> None:
    silver = ArithmeticClassSpec(preperiod=(), period=(2,), label='silver')
    rep = build_seeded_class_campaign_report(
        silver,
        reference_crossing_center=0.9713,
        reference_lower_bound=0.97122,
        max_q=20,
        keep_last=2,
        q_min=2,
        auto_localize_crossing=True,
        min_width=1e-3,
    )
    print(json.dumps(rep, indent=2)[:4000])

if __name__ == '__main__':
    main()

from __future__ import annotations

from pathlib import Path
import sys
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import json

from kam_theorem_suite import ArithmeticClassSpec
from kam_theorem_suite.proof_driver import build_seeded_multi_class_campaign_report

def main() -> None:
    classes = [
        ArithmeticClassSpec(preperiod=(), period=(2,), label='silver'),
        ArithmeticClassSpec(preperiod=(), period=(3,), label='bronze'),
    ]
    rep = build_seeded_multi_class_campaign_report(
        classes,
        reference_crossing_center=0.9713,
        reference_lower_bound=0.97122,
        max_q=12,
        keep_last=1,
        q_min=2,
        auto_localize_crossing=True,
        min_width=1e-3,
    )
    print(json.dumps(rep, indent=2)[:4000])

if __name__ == '__main__':
    main()

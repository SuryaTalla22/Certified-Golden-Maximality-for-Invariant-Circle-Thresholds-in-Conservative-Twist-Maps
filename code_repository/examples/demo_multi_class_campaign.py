from __future__ import annotations

from pathlib import Path
import sys
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from kam_theorem_suite.class_campaigns import ArithmeticClassSpec
from kam_theorem_suite.proof_driver import build_multi_class_campaign_report

def main() -> None:
    classes = [
        ArithmeticClassSpec(preperiod=(), period=(2,), label="silver"),
        ArithmeticClassSpec(preperiod=(), period=(3,), label="bronze"),
    ]
    rep = build_multi_class_campaign_report(
        classes,
        reference_label="golden",
        reference_lower_bound=0.97122,
        reference_crossing_center=0.9713,
        max_q=20,
        keep_last=2,
        q_min=2,
        auto_localize_crossing=True,
    )
    print({
        "dominated": rep["dominated_classes"],
        "overlapping": rep["overlapping_classes"],
        "undecided": rep["undecided_classes"],
    })

if __name__ == "__main__":
    main()

from __future__ import annotations

from pathlib import Path
import sys
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from kam_theorem_suite import ArithmeticClassSpec
from kam_theorem_suite.proof_driver import build_adaptive_class_campaign_report

silver = ArithmeticClassSpec(preperiod=(), period=(2,), label='silver')
report = build_adaptive_class_campaign_report(
    silver,
    reference_lower_bound=0.97122,
    reference_crossing_center=0.97130,
    max_q=30,
    keep_last=3,
    q_min=2,
    auto_localize_crossing=True,
    min_width=1e-3,
)
print({
    'class_label': report['class_label'],
    'status': report['status'],
    'certified_crossing_count': report['certified_crossing_count'],
    'failed_entry_count': report['failed_entry_count'],
})

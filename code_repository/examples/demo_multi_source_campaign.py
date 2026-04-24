from __future__ import annotations

from pathlib import Path
import sys
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from kam_theorem_suite import ArithmeticClassSpec
from kam_theorem_suite.proof_driver import build_multi_source_class_campaign_report

if __name__ == '__main__':
    rep = build_multi_source_class_campaign_report(
        ArithmeticClassSpec(preperiod=(), period=(2,), label='silver'),
        reference_crossing_center=0.97130,
        reference_lower_bound=0.97122,
        max_q=20,
        keep_last=2,
        q_min=2,
        auto_localize_crossing=True,
        min_width=1e-3,
        max_attempts_per_approximant=2,
        max_sources=3,
    )
    print({
        'class_label': rep['class_label'],
        'atlas_use_count': rep['atlas_use_count'],
        'atlas_blend_use_count': rep['atlas_blend_use_count'],
        'certified_crossing_count': rep['certified_crossing_count'],
    })

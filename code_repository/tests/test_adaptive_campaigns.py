
from __future__ import annotations

from kam_theorem_suite import ArithmeticClassSpec
from kam_theorem_suite.proof_driver import (
    build_adaptive_class_campaign_report,
    build_adaptive_multi_class_campaign_report,
)


def test_adaptive_class_campaign_smoke_and_schema():
    spec = ArithmeticClassSpec(preperiod=(), period=(2,), label='silver')
    rep = build_adaptive_class_campaign_report(
        spec,
        reference_lower_bound=0.97122,
        reference_crossing_center=0.97130,
        max_q=20,
        keep_last=2,
        q_min=2,
        auto_localize_crossing=True,
        min_width=1e-3,
        max_attempts_per_approximant=2,
    )
    assert rep['class_label'] == 'silver'
    assert 'entries' in rep and len(rep['entries']) > 0
    first = rep['entries'][0]
    assert 'attempts' in first and len(first['attempts']) > 0
    att = first['attempts'][0]
    assert 'predictor_method' in att
    assert 'crossing_window_lo' in att and att['crossing_window_lo'] < att['crossing_window_hi']
    assert rep['status'] in {
        'fully-adaptive-certified-campaign',
        'partially-adaptive-certified-campaign',
        'adaptive-campaign-needs-manual-followup',
    }


def test_adaptive_multi_class_campaign_smoke():
    classes = [
        ArithmeticClassSpec(preperiod=(), period=(2,), label='silver'),
        ArithmeticClassSpec(preperiod=(), period=(3,), label='bronze'),
    ]
    rep = build_adaptive_multi_class_campaign_report(
        classes,
        reference_label='golden',
        reference_lower_bound=0.97122,
        reference_crossing_center=0.97130,
        max_q=12,
        keep_last=1,
        q_min=2,
        auto_localize_crossing=True,
        min_width=1e-3,
        max_attempts_per_approximant=2,
    )
    assert rep['reference_label'] == 'golden'
    assert len(rep['class_campaigns']) == 2
    assert 'predictor_mode' in rep

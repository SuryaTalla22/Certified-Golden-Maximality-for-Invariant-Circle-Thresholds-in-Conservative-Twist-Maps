from __future__ import annotations

import numpy as np

from kam_theorem_suite import ArithmeticClassSpec
from kam_theorem_suite.proof_driver import (
    build_seed_transfer_report_driver,
    build_seeded_class_campaign_report,
    build_seeded_multi_class_campaign_report,
)
from kam_theorem_suite.standard_map import HarmonicFamily, solve_periodic_orbit


def test_seed_transfer_driver_smoke():
    family = HarmonicFamily()
    src = solve_periodic_orbit(3, 5, 0.9710, family)
    assert src['success']
    rep = build_seed_transfer_report_driver(
        src['x'],
        source_p=3,
        source_q=5,
        source_K=0.9710,
        target_p=5,
        target_q=8,
        target_K=0.9711,
        family=family,
        label='3/5',
    )
    assert rep['source_label'] == '3/5'
    assert rep['target_label'] == '5/8'
    assert rep['candidate_scores']
    assert rep['selected_method'] in {'lift-shape', 'graph-step'}
    assert rep['selected_x_guess'] is not None


def test_seed_transfer_seed_residual_is_finite():
    family = HarmonicFamily()
    src = solve_periodic_orbit(3, 5, 0.9710, family)
    rep = build_seed_transfer_report_driver(
        src['x'],
        source_p=3,
        source_q=5,
        source_K=0.9710,
        target_p=5,
        target_q=8,
        target_K=0.9711,
        family=family,
        label='3/5',
    )
    best = min(rep['candidate_scores'], key=lambda row: row['residual_inf'])
    assert np.isfinite(best['residual_inf'])
    assert best['residual_inf'] >= 0.0


def test_seeded_class_campaign_smoke_and_schema():
    spec = ArithmeticClassSpec(preperiod=(), period=(2,), label='silver')
    rep = build_seeded_class_campaign_report(
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
    assert 'seed_bank' in rep
    assert 'entries' in rep and rep['entries']
    first = rep['entries'][0]
    assert 'attempts' in first and first['attempts']
    att = first['attempts'][0]
    assert 'seed_source_label' in att
    assert 'seed_transfer' in att
    assert rep['status'] == 'seeded-campaign-complete'


def test_seeded_multi_class_campaign_smoke():
    classes = [
        ArithmeticClassSpec(preperiod=(), period=(2,), label='silver'),
        ArithmeticClassSpec(preperiod=(), period=(3,), label='bronze'),
    ]
    rep = build_seeded_multi_class_campaign_report(
        classes,
        reference_crossing_center=0.97130,
        reference_lower_bound=0.97122,
        max_q=12,
        keep_last=1,
        q_min=2,
        auto_localize_crossing=True,
        min_width=1e-3,
        max_attempts_per_approximant=2,
    )
    assert len(rep['class_campaigns']) == 2
    assert 'total_seed_reuse_count' in rep

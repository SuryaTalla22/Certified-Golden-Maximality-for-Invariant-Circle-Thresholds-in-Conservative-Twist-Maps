from __future__ import annotations

from kam_theorem_suite import ArithmeticClassSpec
from kam_theorem_suite.proof_driver import (
    build_multi_source_seed_atlas_report_driver,
    build_multi_source_class_campaign_report,
    build_multi_source_campaign_comparison_report,
    build_multi_source_multi_class_campaign_report,
)
from kam_theorem_suite.seed_transfer import build_seed_profile_from_orbit
from kam_theorem_suite.seeded_campaigns import SeedBankEntry
from kam_theorem_suite.standard_map import HarmonicFamily, solve_periodic_orbit


def _build_seed_bank():
    family = HarmonicFamily()
    bank = []
    for (p, q, K) in [(3, 5, 0.9710), (5, 8, 0.9711), (8, 13, 0.9712)]:
        sol = solve_periodic_orbit(p, q, K, family)
        assert sol['success']
        profile = build_seed_profile_from_orbit(sol['x'], p=p, q=q, K=K, family=family, label=f'{p}/{q}')
        bank.append(SeedBankEntry(label=f'{p}/{q}', p=p, q=q, rho=p / q, K_center=K, source_method='test', seed_profile=profile.to_dict()))
    return family, bank


def test_multi_source_seed_atlas_driver_smoke():
    family, bank = _build_seed_bank()
    rep = build_multi_source_seed_atlas_report_driver(
        bank,
        target_p=13,
        target_q=21,
        target_K=0.97125,
        family=family,
        max_sources=3,
    )
    assert rep['selected_sources']
    assert rep['single_source_transfers']
    assert rep['atlas_candidates']
    assert rep['selected_method'] is not None
    assert rep['selected_x_guess'] is not None


def test_multi_source_campaign_smoke_and_schema():
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
    assert rep['class_label'] == 'silver'
    assert 'entries' in rep and rep['entries']
    first = rep['entries'][0]
    assert 'attempts' in first and first['attempts']
    attempt = first['attempts'][0]
    assert 'atlas_used' in attempt
    assert 'atlas_report' in attempt
    assert 'atlas_selected_method' in attempt


def test_multi_source_campaign_comparison_smoke():
    rep = build_multi_source_campaign_comparison_report(
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
    assert rep['class_label'] == 'silver'
    assert 'seeded_campaign' in rep
    assert 'atlas_campaign' in rep
    assert rep['atlas_use_count'] >= 0


def test_multi_source_multi_class_campaign_smoke():
    rep = build_multi_source_multi_class_campaign_report(
        [
            ArithmeticClassSpec(preperiod=(), period=(2,), label='silver'),
            ArithmeticClassSpec(preperiod=(), period=(3,), label='bronze'),
        ],
        reference_crossing_center=0.97130,
        reference_lower_bound=0.97122,
        max_q=12,
        keep_last=1,
        q_min=2,
        auto_localize_crossing=True,
        min_width=1e-3,
        max_attempts_per_approximant=2,
        max_sources=3,
    )
    assert len(rep['class_campaigns']) == 2
    assert 'total_atlas_use_count' in rep

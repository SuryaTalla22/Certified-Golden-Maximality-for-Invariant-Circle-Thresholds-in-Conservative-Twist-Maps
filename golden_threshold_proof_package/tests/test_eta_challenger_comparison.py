from __future__ import annotations

from kam_theorem_suite.class_campaigns import ArithmeticClassSpec
from kam_theorem_suite.eta_challenger_comparison import (
    EtaChallengerSpec,
    build_campaign_driven_eta_challenger_comparison_certificate,
    build_eta_challenger_record_from_campaign,
    build_near_top_eta_challenger_comparison_certificate,
)
from kam_theorem_suite.proof_driver import (
    build_campaign_driven_eta_challenger_comparison_report,
    build_multi_class_campaign_report,
    build_near_top_eta_challenger_comparison_report,
)
from kam_theorem_suite.standard_map import HarmonicFamily


def _golden_anchor() -> dict:
    return {
        'family_label': 'nearby',
        'rho': 0.6180339887,
        'eta_interval': [1 / (5 ** 0.5), 1 / (5 ** 0.5)],
        'eta_center': 1 / (5 ** 0.5),
        'eta_radius': 0.0,
        'threshold_interval': [0.97113, 0.97116],
        'threshold_center': 0.971145,
        'threshold_radius': 1.5e-5,
        'local_envelope_anchor': {
            'eta_interval_lo': 1 / (5 ** 0.5),
            'eta_interval_hi': 1 / (5 ** 0.5),
            'eta_center': 1 / (5 ** 0.5),
            'threshold_lower': 0.97113,
            'threshold_upper': 0.97116,
            'threshold_center': 0.971145,
            'threshold_gap': 3.0e-5,
            'threshold_width': 3.0e-5,
        },
        'theorem_status': 'eta-threshold-comparison-strong',
    }


def test_near_top_eta_challenger_comparison_classifies_dominated_vs_overlapping() -> None:
    cert = build_near_top_eta_challenger_comparison_certificate(
        [
            EtaChallengerSpec(preperiod=(), period=(2,), label='silver', threshold_lower_bound=0.97080, threshold_upper_bound=0.97095),
            EtaChallengerSpec(preperiod=(), period=(3,), label='bronze', threshold_lower_bound=0.97090, threshold_upper_bound=0.97114),
            EtaChallengerSpec(preperiod=(), period=(1, 2), label='mixed'),
        ],
        golden_eta_threshold_certificate=_golden_anchor(),
        family_label='nearby',
    )
    d = cert.to_dict()
    assert d['theorem_status'].startswith('near-top-eta-challenger-comparison-')
    labels = {rec['label']: rec for rec in d['challenger_records']}
    assert labels['silver']['status'] == 'dominated-by-golden-threshold-anchor'
    assert labels['bronze']['status'] == 'overlaps-golden-threshold-anchor'
    assert labels['mixed']['status'] in {'arithmetic-weaker-only', 'undecided'}
    assert d['near_top_relation']['most_dangerous_threshold_label'] == 'bronze'
    assert d['theorem_flags']['golden_anchor_available'] is True
    assert d['theorem_flags']['challenger_records_available'] is True


def test_campaign_record_lifts_eta_and_threshold_summary() -> None:
    fake_campaign = {
        'class_label': 'silver',
        'ladder': {
            'preperiod': (),
            'period': (2,),
            'rho': 0.41421356,
            'eta_lo': 1 / (8 ** 0.5),
            'eta_hi': 1 / (8 ** 0.5),
            'eta_center': 1 / (8 ** 0.5),
            'arithmetic_method': 'periodic-cycle',
        },
        'pruning_against_reference': {
            'status': 'partially-pruned',
            'records': [
                {'label': 'silver 5/12', 'threshold_lower_bound': 0.97085, 'threshold_upper_bound': 0.97095},
                {'label': 'silver 12/29', 'threshold_lower_bound': 0.97088, 'threshold_upper_bound': 0.97098},
            ],
            'dominated_count': 2,
            'overlapping_count': 0,
            'arithmetic_only_count': 0,
            'undecided_count': 0,
        },
        'notes': 'fake campaign',
    }
    rec = build_eta_challenger_record_from_campaign(
        fake_campaign,
        golden_lower_bound=0.97113,
        golden_eta_lo=1 / (5 ** 0.5),
        golden_eta_hi=1 / (5 ** 0.5),
    ).to_dict()
    assert rec['label'] == 'silver'
    assert rec['threshold_upper_bound'] == 0.97098
    assert rec['threshold_source'] == 'campaign-atlas-supremum'
    assert rec['status'] == 'dominated-by-golden-threshold-anchor'
    assert rec['provenance']['most_dangerous_approximant'] == 'silver 12/29'


def test_campaign_driven_near_top_report_smoke() -> None:
    family = HarmonicFamily(harmonics=[(1.0, 1, 0.0)])
    classes = [
        ArithmeticClassSpec(preperiod=(), period=(2,), label='silver'),
        ArithmeticClassSpec(preperiod=(), period=(3,), label='bronze'),
    ]
    multi = build_multi_class_campaign_report(
        classes,
        reference_label='golden',
        reference_lower_bound=0.97113,
        reference_crossing_center=0.97110,
        family=family,
        max_q=8,
        keep_last=1,
        q_min=2,
        auto_localize_crossing=True,
        min_width=1e-3,
    )
    cert = build_campaign_driven_eta_challenger_comparison_certificate(
        multi,
        golden_eta_threshold_certificate=_golden_anchor(),
        family_label='standard-sine',
    )
    d = cert.to_dict()
    assert d['theorem_status'].startswith('campaign-driven-eta-challenger-comparison-')
    near = d['near_top_certificate']
    assert near['theorem_status'].startswith('near-top-eta-challenger-comparison-')
    assert len(near['challenger_records']) == 2


def test_driver_reports_expose_new_eta_challenger_surface() -> None:
    report = build_near_top_eta_challenger_comparison_report(
        [EtaChallengerSpec(preperiod=(), period=(2,), label='silver', threshold_upper_bound=0.97095)],
        golden_eta_threshold_certificate=_golden_anchor(),
        family_label='nearby',
    )
    campaign = {
        'reference_label': 'golden',
        'reference_lower_bound': 0.97113,
        'class_campaigns': [
            {
                'class_label': 'silver',
                'ladder': {'preperiod': (), 'period': (2,), 'rho': 0.4142, 'eta_lo': 1 / (8 ** 0.5), 'eta_hi': 1 / (8 ** 0.5), 'eta_center': 1 / (8 ** 0.5), 'arithmetic_method': 'periodic-cycle'},
                'pruning_against_reference': {'status': 'partially-pruned', 'records': [{'label': 'silver 5/12', 'threshold_lower_bound': 0.97085, 'threshold_upper_bound': 0.97095}], 'dominated_count': 1, 'overlapping_count': 0, 'arithmetic_only_count': 0, 'undecided_count': 0},
                'notes': 'fake',
            }
        ],
        'dominated_classes': ['silver'],
        'overlapping_classes': [],
        'undecided_classes': [],
    }
    campaign_report = build_campaign_driven_eta_challenger_comparison_report(
        campaign,
        golden_eta_threshold_certificate=_golden_anchor(),
        family_label='nearby',
    )
    assert report['theorem_status'].startswith('near-top-eta-challenger-comparison-')
    assert campaign_report['theorem_status'].startswith('campaign-driven-eta-challenger-comparison-')


def test_near_top_eta_challenger_surface_can_support_two_variable_mode() -> None:
    eta_payload = {'eta_lo': 0.40, 'eta_hi': 0.40, 'eta_center': 0.40}
    cert = build_near_top_eta_challenger_comparison_certificate(
        [
            EtaChallengerSpec(label='silver-a', eta_certificate=eta_payload, threshold_lower_bound=0.97080, threshold_upper_bound=0.97090),
            EtaChallengerSpec(label='silver-b', eta_certificate=eta_payload, threshold_lower_bound=0.97098, threshold_upper_bound=0.97108),
            EtaChallengerSpec(label='bronze', eta_certificate={'eta_lo': 0.35, 'eta_hi': 0.35, 'eta_center': 0.35}, threshold_lower_bound=0.97070, threshold_upper_bound=0.97075),
        ],
        golden_eta_threshold_certificate=_golden_anchor(),
        family_label='nearby',
    )
    d = cert.to_dict()
    assert d['statement_mode_certificate']['candidate_mode'] == 'two-variable'
    assert d['statement_mode_certificate']['mode_lock_status'] == 'two-variable-supported'

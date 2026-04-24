from __future__ import annotations

from kam_theorem_suite.eta_challenger_comparison import (
    EtaChallengerSpec,
    build_near_top_eta_challenger_comparison_certificate,
)


golden_anchor = {
    'family_label': 'standard-sine',
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

cert = build_near_top_eta_challenger_comparison_certificate(
    [
        EtaChallengerSpec(preperiod=(), period=(2,), label='silver', threshold_lower_bound=0.97080, threshold_upper_bound=0.97095),
        EtaChallengerSpec(preperiod=(), period=(3,), label='bronze', threshold_lower_bound=0.97090, threshold_upper_bound=0.97114),
        EtaChallengerSpec(preperiod=(), period=(1, 2), label='mixed'),
    ],
    golden_eta_threshold_certificate=golden_anchor,
    family_label='standard-sine',
)

print('status:', cert.theorem_status)
for rec in cert.challenger_records:
    print(rec['label'], rec['status'], rec['comparison_to_golden'].get('threshold_gap_to_golden_lower'))
print('near-top relation:', cert.near_top_relation)

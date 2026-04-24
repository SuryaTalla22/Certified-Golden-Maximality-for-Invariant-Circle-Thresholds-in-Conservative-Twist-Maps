from __future__ import annotations

from kam_theorem_suite import (
    EtaChallengerSpec,
    build_golden_theorem_vi_envelope_lift_certificate,
)


if __name__ == '__main__':
    cert = build_golden_theorem_vi_envelope_lift_certificate(
        base_K_values=[0.9710, 0.9711, 0.9712],
        challenger_specs=[
            EtaChallengerSpec(period=(1, 2), label='silver-like-demo', threshold_upper_bound=0.9708),
            EtaChallengerSpec(period=(2, 1, 1), label='bronze-like-demo', threshold_upper_bound=0.9706),
        ],
    ).to_dict()
    print('status:', cert['theorem_status'])
    print('statement mode:', cert['statement_mode'])
    print('open hypotheses:', cert['open_hypotheses'])
    print('active assumptions:', cert['active_assumptions'])

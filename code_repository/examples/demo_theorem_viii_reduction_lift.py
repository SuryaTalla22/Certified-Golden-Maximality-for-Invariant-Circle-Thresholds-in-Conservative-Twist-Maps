from __future__ import annotations

from pprint import pprint

from kam_theorem_suite.theorem_viii_reduction_lift import (
    build_golden_theorem_viii_reduction_lift_certificate,
)


if __name__ == '__main__':
    cert = build_golden_theorem_viii_reduction_lift_certificate(
        base_K_values=[0.3, 0.31],
        sample_count=2,
        min_q=5,
        max_q=8,
    ).to_dict()
    pprint({
        'theorem_status': cert['theorem_status'],
        'statement_mode': cert['statement_mode'],
        'open_hypotheses': cert['open_hypotheses'],
        'active_assumptions': cert['active_assumptions'],
    })

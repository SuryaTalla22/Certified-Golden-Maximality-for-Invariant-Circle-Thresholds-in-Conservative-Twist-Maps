from __future__ import annotations

from pprint import pprint

from kam_theorem_suite.class_campaigns import ArithmeticClassSpec
from kam_theorem_suite.theorem_vii_exhaustion_lift import (
    build_golden_theorem_vii_exhaustion_lift_certificate,
)


if __name__ == '__main__':
    specs = [
        ArithmeticClassSpec(preperiod=(), period=(2,), label='silver'),
        ArithmeticClassSpec(preperiod=(), period=(3,), label='bronze'),
    ]
    cert = build_golden_theorem_vii_exhaustion_lift_certificate(
        base_K_values=[0.97108, 0.97112],
        challenger_specs=specs,
        initial_max_q=21,
        rounds=1,
        per_round_budget=1,
        termination_rounds=1,
    ).to_dict()
    pprint({
        'theorem_status': cert['theorem_status'],
        'open_hypotheses': cert['open_hypotheses'],
        'active_assumptions': cert['active_assumptions'],
    })

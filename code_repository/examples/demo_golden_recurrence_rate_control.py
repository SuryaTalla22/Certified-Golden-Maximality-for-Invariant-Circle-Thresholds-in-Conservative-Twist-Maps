from __future__ import annotations

from kam_theorem_suite.proof_driver import build_golden_recurrence_rate_report
from tests.test_certified_tail_modulus_control import _synthetic_ladder


if __name__ == '__main__':
    report = build_golden_recurrence_rate_report(_synthetic_ladder(), min_chain_length=5)
    print(report['theorem_status'])
    print(report['chosen_step_exponent'])
    print(report['rate_golden_intersection_lo'], report['rate_golden_intersection_hi'])

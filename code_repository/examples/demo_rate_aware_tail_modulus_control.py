from __future__ import annotations

from pprint import pprint

from kam_theorem_suite.proof_driver import build_rate_aware_tail_modulus_report
from tests.test_certified_tail_modulus_control import _synthetic_ladder


if __name__ == "__main__":
    report = build_rate_aware_tail_modulus_report(_synthetic_ladder(), min_chain_length=5)
    pprint({
        'theorem_status': report['theorem_status'],
        'chosen_rate_exponent': report['chosen_rate_exponent'],
        'selected_rate_interval_width': report['selected_rate_interval_width'],
        'modulus_rate_intersection_width': report['modulus_rate_intersection_width'],
        'first_rate_tail_radius': report['first_rate_tail_radius'],
        'last_rate_tail_radius': report['last_rate_tail_radius'],
    })

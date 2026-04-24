from __future__ import annotations

from pprint import pprint

from kam_theorem_suite.proof_driver import build_edge_class_weighted_golden_rate_report
from tests.test_certified_tail_modulus_control import _synthetic_ladder


if __name__ == '__main__':
    report = build_edge_class_weighted_golden_rate_report(_synthetic_ladder(), min_chain_length=5)
    pprint({
        'theorem_status': report['theorem_status'],
        'chosen_edge_class_step_exponent': report['chosen_edge_class_step_exponent'],
        'edge_class_transport_intersection': (
            report['edge_class_transport_intersection_lo'],
            report['edge_class_transport_intersection_hi'],
        ),
        'derivative_share_mean': report['derivative_share_mean'],
        'tangent_share_mean': report['tangent_share_mean'],
        'fallback_share_mean': report['fallback_share_mean'],
    })

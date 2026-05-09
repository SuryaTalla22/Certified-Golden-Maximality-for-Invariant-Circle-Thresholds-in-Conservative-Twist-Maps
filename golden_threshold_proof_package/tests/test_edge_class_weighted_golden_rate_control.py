from __future__ import annotations

from kam_theorem_suite.edge_class_weighted_golden_rate_control import build_edge_class_weighted_golden_rate_certificate
from kam_theorem_suite.proof_driver import build_edge_class_weighted_golden_rate_report
from tests.test_certified_tail_modulus_control import _synthetic_ladder


def test_edge_class_weighted_golden_rate_builds_classwise_phi_budget() -> None:
    cert = build_edge_class_weighted_golden_rate_certificate(_synthetic_ladder(), min_chain_length=5)
    d = cert.to_dict()
    assert d['theorem_status'].startswith('edge-class-weighted-golden-rate-')
    assert d['chain_length'] >= 5
    assert d['chosen_edge_class_step_exponent'] is not None
    assert d['chosen_edge_class_step_exponent'] > 0.0
    assert d['edge_class_weighted_golden_tail_constant'] is not None
    assert d['actual_tail_dominated_by_edge_class_rate'] is True
    assert d['edge_class_tail_nonincreasing'] is True
    assert d['classwise_tail_nonincreasing'] is True
    assert d['selected_edge_class_interval_lo'] is not None
    assert d['selected_edge_class_interval_hi'] is not None
    assert d['edge_class_transport_intersection_lo'] is not None
    assert d['edge_class_transport_intersection_hi'] is not None
    nodes = d['nodes']
    assert nodes[0]['edge_class_weighted_tail_radius'] >= nodes[-1]['edge_class_weighted_tail_radius']
    for node in nodes:
        total = node['derivative_tail_radius'] + node['tangent_tail_radius'] + node['fallback_tail_radius']
        assert abs(total - node['edge_class_weighted_tail_radius']) < 1e-12
        assert 0.0 <= node['derivative_share'] <= 1.0
        assert 0.0 <= node['tangent_share'] <= 1.0
        assert 0.0 <= node['fallback_share'] <= 1.0
        assert abs(node['derivative_share'] + node['tangent_share'] + node['fallback_share'] - 1.0) < 1e-12


def test_driver_exposes_edge_class_weighted_golden_rate_layer() -> None:
    report = build_edge_class_weighted_golden_rate_report(_synthetic_ladder(), min_chain_length=5)
    assert report['chain_length'] >= 5
    assert report['theorem_status'].startswith('edge-class-weighted-golden-rate-')

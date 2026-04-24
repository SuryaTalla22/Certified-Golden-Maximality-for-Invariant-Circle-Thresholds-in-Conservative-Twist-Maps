from __future__ import annotations

from kam_theorem_suite.proof_driver import build_theorem_v_explicit_error_report
from kam_theorem_suite.theorem_v_error_control import build_theorem_v_explicit_error_certificate
from tests.test_certified_tail_modulus_control import _synthetic_ladder


def test_theorem_v_explicit_error_builds_compatible_interval_and_monotone_error_law() -> None:
    cert = build_theorem_v_explicit_error_certificate(_synthetic_ladder(), min_chain_length=5)
    d = cert.to_dict()
    assert d['theorem_status'].startswith('theorem-v-explicit-error-law-')
    assert d['compatible_interval_nonempty'] is True
    assert d['compatible_limit_interval_lo'] is not None
    assert d['compatible_limit_interval_hi'] is not None
    assert d['compatible_layer_count'] >= 5
    assert d['chosen_q_power_exponent'] is not None
    assert d['q_power_anchor_q'] == 8
    assert d['q_power_tail_dominates_certificate_tail'] is True
    assert d['monotone_error_law_nonincreasing'] is True
    assert d['active_bounds_dominate_compatible_errors'] is True
    assert d['active_bounds_dominate_certificate_totals'] is True
    nodes = d['nodes']
    assert len(nodes) >= 5
    assert nodes[0]['q'] == 8
    assert nodes[-1]['q'] == 55
    assert nodes[0]['monotone_total_error_radius'] >= nodes[-1]['monotone_total_error_radius']
    assert nodes[0]['q_power_tail_radius'] >= nodes[-1]['q_power_tail_radius']
    assert d['late_coherent_suffix_length'] >= 3
    assert d['late_coherent_suffix_start_q'] == 21
    assert d['late_coherent_suffix_interval_width'] is not None
    assert d['late_coherent_suffix_contracting'] is True
    assert d['late_coherent_suffix_status'] == 'late-coherent-suffix-strong'
    for node in nodes:
        assert node['monotone_interval_lo'] <= node['transport_center'] <= node['monotone_interval_hi']
        assert node['monotone_total_error_radius'] + 1e-15 >= node['raw_total_error_radius']


def test_driver_exposes_theorem_v_explicit_error_layer() -> None:
    report = build_theorem_v_explicit_error_report(_synthetic_ladder(), min_chain_length=5)
    assert report['chain_length'] >= 5
    assert report['theorem_status'].startswith('theorem-v-explicit-error-law-')
    assert report['compatible_limit_interval_width'] is not None

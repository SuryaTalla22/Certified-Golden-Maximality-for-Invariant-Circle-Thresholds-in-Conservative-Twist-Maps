from __future__ import annotations

from kam_theorem_suite.eta_comparison import (
    build_eta_threshold_comparison_certificate,
    build_proto_envelope_eta_bridge_certificate,
)
from kam_theorem_suite.standard_map import HarmonicFamily


family = HarmonicFamily(harmonics=[(1.0, 1, 0.0), (0.06, 2, 0.02)])

eta_anchor = build_eta_threshold_comparison_certificate(family=family)
print('eta-threshold status:', eta_anchor.theorem_status)
print('eta interval:', eta_anchor.eta_interval)
print('threshold interval:', eta_anchor.threshold_interval)

panel_records = [
    {'eta_approx': 1 / (5 ** 0.5), 'threshold_lo': 0.97113, 'threshold_hi': 0.97116, 'is_golden': True},
    {'eta_approx': 1 / (8 ** 0.5), 'threshold_lo': 0.97080, 'threshold_hi': 0.97095, 'is_golden': False},
]
bridge = build_proto_envelope_eta_bridge_certificate(family=family, panel_records=panel_records)
print('proto-envelope status:', bridge.theorem_status)
print('panel relation:', bridge.proto_envelope_relation)

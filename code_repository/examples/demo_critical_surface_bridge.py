from __future__ import annotations

from pprint import pprint

from kam_theorem_suite.standard_map import HarmonicFamily
from kam_theorem_suite.critical_surface import (
    build_family_transversality_certificate,
    build_critical_surface_bridge_certificate,
)


family = HarmonicFamily(harmonics=[(1.05, 1, 0.04), (0.08, 2, 0.01), (0.03, 3, -0.02)])

trans = build_family_transversality_certificate(family, family_label='demo')
bridge = build_critical_surface_bridge_certificate(family, family_label='demo')

print('Family transversality status:', trans.theorem_status)
print('Selected crossing interval:', trans.selected_crossing_interval)
print('Critical parameter estimate:', trans.critical_parameter_estimate)
print('Derivative / margin:', trans.unstable_coordinate_derivative, trans.transversality_margin)
print()
print('Critical-surface bridge status:', bridge.theorem_status)
pprint(bridge.theorem_flags)

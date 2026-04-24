from __future__ import annotations

from pprint import pprint

from kam_theorem_suite.standard_map import HarmonicFamily
from kam_theorem_suite.proof_driver import (
    build_transversality_window_report,
    build_validated_critical_surface_bridge_report,
)


family = HarmonicFamily(harmonics=[(1.05, 1, 0.04), (0.08, 2, 0.01), (0.03, 3, -0.02)])

window = build_transversality_window_report(family=family, family_label='demo_family')
bridge = build_validated_critical_surface_bridge_report(family=family, family_label='demo_family')

print('window status:', window['theorem_status'])
print('localized window:', window['localized_window'])
print('derivative floor proxy:', window['derivative_floor_proxy'])
print('transversality margin:', window['transversality_margin'])
print('bridge status:', bridge['theorem_status'])
pprint(bridge['theorem_flags'])

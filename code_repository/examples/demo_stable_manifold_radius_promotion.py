from __future__ import annotations

from pprint import pprint

from kam_theorem_suite.standard_map import HarmonicFamily
from kam_theorem_suite.stable_manifold import build_stable_manifold_chart_certificate
from kam_theorem_suite.theorem_i_ii_workstream_lift import build_golden_theorem_i_ii_workstream_lift_certificate

stable = build_stable_manifold_chart_certificate(HarmonicFamily())
print('Stable-manifold theorem status:', stable.theorem_status)
print('Stable chart radius:', stable.stable_chart_radius)
print('Radius source:', stable.radius_source)
pprint(stable.radius_components)

workstream = build_golden_theorem_i_ii_workstream_lift_certificate(HarmonicFamily()).to_dict()
print('Workstream theorem status:', workstream['theorem_status'])
print('Workstream residual status:', workstream['residual_burden_summary']['status'])
print('Renormalization package status:', workstream['validated_renormalization_package_promotion']['theorem_status'])
print('Critical-surface theorem status:', workstream['validated_critical_surface_theorem_promotion']['theorem_status'])
print('Threshold promotion status:', workstream['critical_surface_threshold_identification_promotion']['theorem_status'])

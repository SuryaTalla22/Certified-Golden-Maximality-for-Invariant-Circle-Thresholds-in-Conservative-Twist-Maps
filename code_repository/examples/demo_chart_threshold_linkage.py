from __future__ import annotations

from pprint import pprint

from kam_theorem_suite.chart_threshold_linkage import build_chart_threshold_linkage_certificate
from kam_theorem_suite.standard_map import HarmonicFamily


family = HarmonicFamily(harmonics=[(1.05, 1, 0.04), (0.08, 2, 0.01), (0.03, 3, -0.02)])

lower = {
    'stable_lower_bound': 0.97100,
    'stable_window_lo': 0.97100,
    'stable_window_hi': 0.97108,
    'theorem_status': 'golden-lower-neighborhood-stability-strong',
}
upper = {
    'selected_upper_lo': 0.97117,
    'selected_upper_hi': 0.97122,
    'selected_barrier_lo': 1.020,
    'selected_barrier_hi': 1.030,
    'theorem_status': 'golden-irrational-incompatibility-strong',
}
theorem_v = {
    'compatible_limit_interval_lo': 0.97110,
    'compatible_limit_interval_hi': 0.97120,
    'theorem_status': 'theorem-v-explicit-error-law-strong',
}

cert = build_chart_threshold_linkage_certificate(
    family=family,
    family_label='nearby',
    threshold_center=0.97115,
    threshold_scale=2.0e-4,
    lower_certificate=lower,
    upper_certificate=upper,
    theorem_v_certificate=theorem_v,
)

pprint(cert.to_dict())

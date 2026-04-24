from __future__ import annotations

from pprint import pprint

from kam_theorem_suite import (
    HarmonicFamily,
    build_renormalization_operator_report,
    build_renormalization_fixed_point_report,
    build_linearization_bounds_report,
)

family = HarmonicFamily(harmonics=[(1.05, 1, 0.04), (0.08, 2, 0.01), (0.03, 3, -0.02)])

print('=== Proxy renormalization operator ===')
pprint(build_renormalization_operator_report(family=family, family_label='demo'))

print('\n=== Fixed-point scaffold ===')
pprint(build_renormalization_fixed_point_report(family=family, family_label='demo', iterations=5))

print('\n=== Linearization bounds ===')
pprint(build_linearization_bounds_report(family=family, family_label='demo'))

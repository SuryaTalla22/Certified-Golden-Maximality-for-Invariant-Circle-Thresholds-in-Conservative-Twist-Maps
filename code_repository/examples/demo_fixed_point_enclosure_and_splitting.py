from __future__ import annotations

from pprint import pprint

from kam_theorem_suite.standard_map import HarmonicFamily
from kam_theorem_suite.fixed_point_enclosure import build_fixed_point_enclosure_certificate
from kam_theorem_suite.spectral_splitting import build_spectral_splitting_certificate

family = HarmonicFamily(harmonics=[(1.05, 1, 0.04), (0.08, 2, 0.01), (0.03, 3, -0.02)])

enclosure = build_fixed_point_enclosure_certificate(family, family_label='demo')
splitting = build_spectral_splitting_certificate(family, family_label='demo')

print('enclosure status:', enclosure.theorem_status)
print('enclosure radius:', enclosure.enclosure_radius)
print('invariance margin:', enclosure.invariance_margin)
print('splitting status:', splitting.theorem_status)
print('stable dimension:', splitting.stable_dimension)
print('unstable dimension:', splitting.unstable_dimension)
print('spectral gap ratio:', splitting.spectral_gap_ratio)
pprint(splitting.splitting_flags)

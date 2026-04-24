from __future__ import annotations

from kam_theorem_suite.theorem_vii_exhaustion_discharge import (
    build_golden_theorem_vii_exhaustion_discharge_lift_certificate,
)

cert = build_golden_theorem_vii_exhaustion_discharge_lift_certificate(base_K_values=[0.9711, 0.97111])
report = cert.to_dict()
print('status:', report['theorem_status'])
print('upstream active assumptions:', report['upstream_active_assumptions'])
print('local active assumptions:', report['local_active_assumptions'])

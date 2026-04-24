from __future__ import annotations

from kam_theorem_suite import build_golden_theorem_vi_envelope_discharge_lift_certificate


if __name__ == '__main__':
    cert = build_golden_theorem_vi_envelope_discharge_lift_certificate(
        base_K_values=[0.92, 0.94, 0.96],
        min_q=5,
        max_q=13,
    )
    data = cert.to_dict()
    print('status:', data['theorem_status'])
    print('statement_mode:', data['statement_mode'])
    print('upstream_active_assumptions:', data['upstream_active_assumptions'])
    print('local_active_assumptions:', data['local_active_assumptions'])

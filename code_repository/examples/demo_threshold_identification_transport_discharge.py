from __future__ import annotations

from kam_theorem_suite.threshold_identification_transport_discharge import (
    build_golden_threshold_identification_transport_discharge_certificate,
)


if __name__ == '__main__':
    cert = build_golden_threshold_identification_transport_discharge_certificate(
        base_K_values=[0.97108, 0.97110, 0.97112],
        assume_unique_true_threshold_branch_inside_transport_locked_window=False,
    ).to_dict()
    print('status:', cert['theorem_status'])
    print('transport interval:', cert['transport_interval'])
    print('identified window:', cert['identified_window'])
    print('locked window:', cert['locked_window'])
    print('upstream actives:', cert['upstream_active_assumptions'])
    print('local actives:', cert['local_active_assumptions'])

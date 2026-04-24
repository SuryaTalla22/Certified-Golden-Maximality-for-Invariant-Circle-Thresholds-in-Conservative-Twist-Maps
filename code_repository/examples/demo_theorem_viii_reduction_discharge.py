from __future__ import annotations

from pprint import pprint

from kam_theorem_suite.theorem_viii_reduction_discharge import (
    build_golden_theorem_viii_reduction_discharge_lift_certificate,
)


if __name__ == '__main__':
    cert = build_golden_theorem_viii_reduction_discharge_lift_certificate(
        base_K_values=[0.95, 0.971, 0.989],
    ).to_dict()
    print('status:', cert['theorem_status'])
    print('statement_mode:', cert['statement_mode'])
    print('residual_global_active_assumptions:')
    pprint(cert['residual_global_active_assumptions'])
    print('residual_non_global_hinges:')
    pprint(cert['residual_non_global_hinges'])

from __future__ import annotations

from pprint import pprint

from kam_theorem_suite.threshold_identification_lift import (
    build_golden_threshold_identification_lift_certificate,
)


if __name__ == '__main__':
    cert = build_golden_threshold_identification_lift_certificate(
        base_K_values=[0.97105, 0.97110, 0.97115],
        n_terms=8,
        min_q=5,
        max_q=13,
    )
    pprint({
        'theorem_status': cert.theorem_status,
        'identified_window': cert.identified_window,
        'open_hypotheses': cert.open_hypotheses,
        'upstream_active_assumptions': cert.upstream_active_assumptions,
        'local_active_assumptions': cert.local_active_assumptions,
    })

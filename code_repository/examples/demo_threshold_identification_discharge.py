from __future__ import annotations

from pprint import pprint

from kam_theorem_suite.threshold_identification_discharge import (
    build_golden_threshold_identification_discharge_certificate,
)


if __name__ == '__main__':
    cert = build_golden_threshold_identification_discharge_certificate(base_K_values=[0.3]).to_dict()
    pprint({
        'theorem_status': cert['theorem_status'],
        'workstream_window': cert['workstream_window'],
        'identified_window': cert['identified_window'],
        'overlap_window': cert['overlap_window'],
        'overlap_width': cert['overlap_width'],
        'center_gap': cert['center_gap'],
        'upstream_active_assumptions': cert['upstream_active_assumptions'],
        'local_active_assumptions': cert['local_active_assumptions'],
    })

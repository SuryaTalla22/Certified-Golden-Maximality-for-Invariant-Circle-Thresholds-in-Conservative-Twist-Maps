from __future__ import annotations

import math

from kam_theorem_suite.audit.lower_anchor_phase2p_modewise_tail import (
    _GOLDEN_RHO,
    build_modewise_geometric_tail_ledger,
    parse_float_list,
    parse_int_list,
)


def test_parse_helpers_are_unique_and_positive():
    assert parse_float_list("1,2,2,0,-3,4") == (1.0, 2.0, 4.0)
    assert parse_int_list("1,2,2,0,-3,4") == (1, 2, 4)


def test_modewise_tail_reproduces_l1_and_improves_global_bound():
    # Values from the Phase-2O best strict sigma override.  The old scalar
    # bound used max inverse * l1; the modewise ledger should be much smaller.
    tail_sup = 4.1355513260843267e-10
    ratio = 0.9357881805779968
    start = 513
    global_inv = 134.1677387880765
    source_tail_l1 = 1.2880966038060018e-08
    ledger = build_modewise_geometric_tail_ledger(
        rho=_GOLDEN_RHO,
        sigma=1.0e-6,
        tail_start_mode=start,
        finite_cutoff=1024,
        tail_sup=tail_sup,
        geometric_ratio=ratio,
        global_inverse_bound=global_inv,
    )
    assert ledger.theorem_usable
    assert not ledger.failure_reasons
    assert math.isclose(ledger.tail_l1_bound, source_tail_l1, rel_tol=1e-8, abs_tol=1e-18)
    assert ledger.global_inverse_tail_response is not None
    assert ledger.modewise_tail_response < 0.05 * ledger.global_inverse_tail_response
    assert ledger.modewise_tail_response < 1.0e-7


def test_modewise_tail_fails_closed_for_bad_ratio():
    ledger = build_modewise_geometric_tail_ledger(
        rho=_GOLDEN_RHO,
        sigma=1.0e-6,
        tail_start_mode=513,
        finite_cutoff=1024,
        tail_sup=1.0e-10,
        geometric_ratio=1.0,
        global_inverse_bound=10.0,
    )
    assert not ledger.theorem_usable
    assert "geometric_ratio_not_in_unit_interval" in ledger.failure_reasons


def test_phase2p_expands_phase2o_scan_rows():
    from kam_theorem_suite.audit.lower_anchor_phase2p_modewise_tail import _extract_selected_rows

    scan = {
        "schema": "phase2o_tail_radius_scan_report_v1",
        "rows": [
            {"model_name": "diagnostic", "theorem_eligible": False, "radius_r": 1.0},
            {"model_name": "strict_source_tail_radius_x3", "theorem_eligible": True, "radius_r": 3.0},
            {"model_name": "strict_source_tail_radius_x6", "theorem_eligible": True, "radius_r": 6.0},
        ],
    }
    rows = _extract_selected_rows(scan, "phase2o_scan", None)
    assert [r["model_name"] for r in rows] == [
        "strict_source_tail_radius_x3",
        "strict_source_tail_radius_x6",
    ]

from __future__ import annotations

from kam_theorem_suite.golden_aposteriori import (
    build_golden_aposteriori_certificate,
    build_golden_small_divisor_table,
    continue_golden_aposteriori_certificates,
    golden_inverse,
)


def test_golden_small_divisor_table_is_certified_on_short_cutoff() -> None:
    table = build_golden_small_divisor_table(8, rho=golden_inverse())
    assert len(table) == 8
    assert all(row.certified_against_lower_bound for row in table)
    assert min(row.ratio_to_lower_bound for row in table) >= 1.0


def test_golden_aposteriori_certificate_smoke() -> None:
    cert = build_golden_aposteriori_certificate(0.3, N_values=(32, 48, 64), sigma_cap=0.02)
    d = cert.to_dict()
    assert d["golden_small_divisor_pass"] is True
    assert d["finite_dimensional_success"] is True
    assert d["selected_N"] in {32, 48, 64}
    assert d["theorem_status"] in {
        "golden-aposteriori-bridge-strong",
        "golden-aposteriori-bridge-moderate",
        "golden-aposteriori-bridge-weak",
    }
    assert d["cohomological_inverse_bound"] > 0.0
    assert d["weighted_graph_l1"] > 0.0
    assert d["analytic_theorem_status"] in {
        "analytic-torus-bridge-strong",
        "analytic-torus-bridge-moderate",
        "analytic-torus-bridge-weak",
    }


def test_golden_aposteriori_continuation_report_smoke() -> None:
    report = continue_golden_aposteriori_certificates([0.2, 0.3], N_values=(32, 48), sigma_cap=0.02)
    d = report.to_dict()
    assert d["source"] == "multiresolution"
    assert len(d["steps"]) == 2
    assert d["success_prefix_len"] >= 1

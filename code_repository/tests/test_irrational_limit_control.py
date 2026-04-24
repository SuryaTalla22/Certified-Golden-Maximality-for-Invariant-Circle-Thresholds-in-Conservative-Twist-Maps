from __future__ import annotations

from kam_theorem_suite.irrational_limit_control import build_rational_irrational_convergence_certificate
from kam_theorem_suite.proof_driver import build_rational_irrational_convergence_report


def _synthetic_ladder(limit: float = 0.9716, slope: float = 0.12) -> dict:
    qs = [8, 13, 21, 34]
    approximants = []
    for i, q in enumerate(qs, start=1):
        center = limit + slope / (q * q)
        width = 4e-4 / i
        approximants.append(
            {
                "p": q - 1,
                "q": q,
                "label": f"a-{q-1}/{q}",
                "crossing_root_window_lo": center - 0.5 * width,
                "crossing_root_window_hi": center + 0.5 * width,
                "crossing_root_window_width": width,
                "crossing_center": center,
            }
        )
    return {"approximants": approximants}


def test_limit_control_builds_nonempty_interval_for_clean_tail() -> None:
    cert = build_rational_irrational_convergence_certificate(_synthetic_ladder(), min_members=3)
    d = cert.to_dict()
    assert d["theorem_status"] in {
        "irrational-limit-control-strong",
        "irrational-limit-control-moderate",
        "irrational-limit-control-weak",
    }
    assert d["selected_tail_member_count"] >= 3
    assert d["limit_interval_lo"] is not None
    assert d["limit_interval_hi"] is not None
    assert d["limit_interval_lo"] <= 0.9716 <= d["limit_interval_hi"]


def test_limit_control_respects_audit_seed_threshold() -> None:
    ladder = _synthetic_ladder()
    cert = build_rational_irrational_convergence_certificate(
        ladder,
        asymptotic_audit={"audited_upper_source_threshold": 21},
        min_members=2,
    )
    d = cert.to_dict()
    assert d["selected_q_threshold"] in {8, 13, 21}
    assert len(d["entries"]) == 4


def test_driver_layer_exposes_limit_control_report() -> None:
    report = build_rational_irrational_convergence_report(_synthetic_ladder(), min_members=2)
    assert report["usable_entry_count"] == 4
    assert report["theorem_status"].startswith("irrational-limit-control-")

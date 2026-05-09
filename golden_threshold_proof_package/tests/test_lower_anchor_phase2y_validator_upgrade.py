from pathlib import Path
import importlib.util
import json
import sys

MOD_PATH = Path("kam_theorem_suite/audit/lower_anchor_phase2y_validator_upgrade.py")


def load_mod():
    spec = importlib.util.spec_from_file_location("phase2y_validator_upgrade", MOD_PATH)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def failed_record(q=0.886, margin=-1.3e-8, guard=1.18e-7, tail=3.46e-7, allowable=4.51e-7):
    m = load_mod()
    return m.FailedPieceRecord(
        index=5,
        label="p0005",
        segment_id="seg",
        path="x.json",
        K_lo=0.0,
        K_hi=1.0,
        K_mid=0.5,
        theorem_ready=False,
        theorem_facing=False,
        promotion_allowed=False,
        model_name="row",
        sigma=1e-7,
        radius_r=9.0e-7,
        radius_multiplier=None,
        finite_contraction_q=q,
        tail_cutoff=1536,
        radii_margin=margin,
        tail_T=tail + guard,
        allowable_tail_max=allowable,
        tail_response_bound=tail,
        nonlinear_guard=guard,
        failure_reasons=("analytic_radii_margin_not_safely_positive",),
        source_kind="test",
    )


def test_required_improvement_safe_q_guard_fraction():
    m = load_mod()
    row = m.build_required_improvement_row(failed_record())
    assert row.bucket == "safe_q_small_gap"
    assert row.needs_finite_q_upgrade is False
    assert row.guard_reduction_frac_needed is not None
    assert 0.09 < row.guard_reduction_frac_needed < 0.13
    assert row.closeable_by_guard_only_at_15pct is True


def test_required_improvement_q_over_one_needs_finite_upgrade():
    m = load_mod()
    row = m.build_required_improvement_row(failed_record(q=1.006))
    assert row.bucket == "q_over_one"
    assert row.needs_finite_q_upgrade is True
    assert row.q_reduction_needed_to_target > 0.0
    assert row.recommended_upgrade in {"combined_diagonal_q_plus_profiled_guard", "diagonal_or_weighted_finite_krawczyk"}


def test_sensitivity_trial_closes_with_guard_factor():
    m = load_mod()
    row = m.build_required_improvement_row(failed_record())
    t = m.sensitivity_trial(row, guard_factor=0.85, tail_response_factor=1.0, q_factor=1.0)
    assert t.margin_passes is True
    assert t.q_passes is True
    assert t.sensitivity_closes is True
    assert t.diagnostic_only is True


def test_build_phase2y_report_from_summary(tmp_path):
    m = load_mod()
    summary = tmp_path / "summary.json"
    summary.write_text(json.dumps({
        "best_failed_rows": [
            {
                "index": 5,
                "K_lo": 0.1,
                "K_hi": 0.2,
                "radii_margin": -1.0e-8,
                "finite_contraction_q": 0.88,
                "tail_T": 4.6e-7,
                "allowable_tail_max": 4.5e-7,
                "tail_response_bound": 3.4e-7,
                "nonlinear_guard": 1.2e-7,
                "failure_reasons": ["analytic_radii_margin_not_safely_positive"],
            }
        ]
    }))
    report = m.build_phase2y_report(summaries=[summary], top_k_trials=1, guard_factors=(1.0, 0.85), tail_response_factors=(1.0,), q_factors=(1.0,))
    assert report["status"] == "phase2y-diagnostic-complete"
    assert report["diagnostic_only"] is True
    assert report["summary"]["row_count"] == 1
    assert report["summary"]["minimal_closing_trial_record_count"] == 1

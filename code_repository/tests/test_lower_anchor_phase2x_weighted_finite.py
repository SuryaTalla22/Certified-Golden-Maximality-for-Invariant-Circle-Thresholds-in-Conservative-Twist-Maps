from pathlib import Path
import importlib.util
import json
import sys

MOD_PATH = Path("kam_theorem_suite/audit/lower_anchor_phase2x_weighted_finite.py")


def load_mod():
    spec = importlib.util.spec_from_file_location("phase2x_weighted", MOD_PATH)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_autopsy_safe_q_small_gap():
    m = load_mod()
    rec = m.FailedPieceRecord(
        index=5, label="p0005", segment_id="seg", path="x.json", K_lo=0.0, K_hi=1.0, K_mid=0.5,
        theorem_ready=False, theorem_facing=False, promotion_allowed=False, model_name="row", sigma=1e-7,
        radius_r=1.0, radius_multiplier=None, finite_contraction_q=0.88, tail_cutoff=1536,
        radii_margin=-1.0e-8, tail_T=4.6e-7, allowable_tail_max=4.5e-7,
        tail_response_bound=3.4e-7, nonlinear_guard=1.2e-7,
        failure_reasons=("analytic_radii_margin_not_safely_positive",), source_kind="test")
    a = m.autopsy_record(rec)
    assert a.bucket == "safe_q_small_gap"
    assert a.gap_to_close == 1.0e-8
    assert a.recommended_rescue == "radius_shell_plus_weighted_nonlinear_guard"


def test_autopsy_q_boundary():
    m = load_mod()
    rec = m.FailedPieceRecord(
        index=15, label="p0015", segment_id="seg", path="x.json", K_lo=0.0, K_hi=1.0, K_mid=0.5,
        theorem_ready=False, theorem_facing=False, promotion_allowed=False, model_name="row", sigma=1e-7,
        radius_r=1.0, radius_multiplier=None, finite_contraction_q=0.9996, tail_cutoff=1536,
        radii_margin=-2.0e-8, tail_T=4.7e-7, allowable_tail_max=4.5e-7,
        tail_response_bound=3.5e-7, nonlinear_guard=1.2e-7,
        failure_reasons=("analytic_radii_margin_not_safely_positive",), source_kind="test")
    a = m.autopsy_record(rec)
    assert a.bucket == "q_boundary_near_miss"
    assert a.recommended_rescue == "weighted_norm_or_targeted_n_lift"


def test_anchor_generation():
    m = load_mod()
    anchors = m.generate_anchor_windows("0.0", "1.0", 3, "0.1", "g")
    assert len(anchors) == 3
    assert anchors[0]["K_lo"] == "0"
    assert anchors[-1]["K_hi"] == "1"
    assert anchors[1]["K_mid"] == "0.5"


def test_records_from_summary(tmp_path):
    m = load_mod()
    p = tmp_path / "summary.json"
    p.write_text(json.dumps({"best_failed_rows": [{"index": 1, "K_lo": 0.1, "K_hi": 0.2, "radii_margin": -1e-8, "finite_contraction_q": 0.9, "tail_T": 2.0, "allowable_tail_max": 1.9}]}))
    recs = m.records_from_summary(p)
    assert len(recs) == 1
    assert recs[0].index == 1
    assert recs[0].K_mid == 0.15000000000000002


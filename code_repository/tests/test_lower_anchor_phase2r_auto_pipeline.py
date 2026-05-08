from decimal import Decimal
import importlib.util
import sys
from pathlib import Path

SCRIPT = Path("scripts/audit/run_lower_anchor_phase2r_auto_collar_pipeline.py")


def load_module():
    spec = importlib.util.spec_from_file_location("phase2r_auto", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_segment_formula_basic():
    m = load_module()
    s0 = m.segment_for_index(0)
    assert m.fmt_dec(s0.lo) == "0.9600001"
    assert m.fmt_dec(s0.hi) == "0.9605002"
    s2 = m.segment_for_index(2)
    assert m.fmt_dec(s2.lo) == "0.9610001"
    assert m.fmt_dec(s2.hi) == "0.9615002"


def test_partial_final_segment():
    m = load_module()
    s = m.segment_for_index(23, Decimal("0.971636"))
    assert s.partial_final is True
    assert m.fmt_dec(s.lo) == "0.9715001"
    assert m.fmt_dec(s.hi) == "0.971636"
    assert s.hi > s.lo


def test_stop_index_for_target():
    m = load_module()
    assert m.stop_index_for_target(Decimal("0.9605002")) == 0
    assert m.stop_index_for_target(Decimal("0.9610002")) == 1
    assert m.stop_index_for_target(Decimal("0.971636")) == 23


def test_sigma_slug():
    m = load_module()
    assert m.sigma_slug("0.0001") == "0p0001"


def test_final_anchor_only_on_final_chain():
    m = load_module()
    assert m.should_pass_final_anchor(Decimal("0.9620002"), "0.971636", "1e-10") is False
    assert m.should_pass_final_anchor(Decimal("0.971636"), "0.971636", "1e-10") is True
    assert m.should_pass_final_anchor(Decimal("0.97163599995"), "0.971636", "1e-10") is True


def test_phase2o_radius_coverage_detection(tmp_path):
    m = load_module()
    cand = tmp_path / "candidate.json"
    scan = tmp_path / "scan.json"
    scan.write_text('{"config": {"radius_multipliers": [1.0, 2.0, 6.0]}, "rows": []}')
    cand.write_text('{"anchor_segments": [{"source_artifact": "scan.json"}]}')
    assert m.phase2o_has_requested_radius_coverage(cand, "1.0,2.0,6.0") is True
    assert m.phase2o_has_requested_radius_coverage(cand, "1.0,3.0") is False

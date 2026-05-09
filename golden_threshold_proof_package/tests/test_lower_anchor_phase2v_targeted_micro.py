import importlib.util
import sys
from pathlib import Path

SCRIPT = Path("scripts/audit/run_lower_anchor_phase2v_targeted_micro_rescue.py")


def load_module():
    spec = importlib.util.spec_from_file_location("phase2v_targeted", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_generate_pieces_count_and_bounds():
    m = load_module()
    pieces = m.generate_pieces("0.0", "1.0", 4, "0.0", "x")
    assert len(pieces) == 4
    assert pieces[0]["K_lo"] == "0"
    assert pieces[-1]["K_hi"] == "1"
    assert pieces[2]["piece_label"] == "x_p0002"


def test_generate_pieces_overlap_clamped():
    m = load_module()
    pieces = m.generate_pieces("0.0", "1.0", 2, "0.2", "x")
    assert pieces[0]["K_lo"] == "0"
    assert pieces[0]["K_hi"] == "0.6"
    assert pieces[1]["K_lo"] == "0.4"
    assert pieces[1]["K_hi"] == "1"


def test_profiles_present():
    m = load_module()
    assert "needle" in m.PROFILES
    assert "needle1536" in m.PROFILES
    assert "rescue" in m.PROFILES
    assert "1536" in m.PROFILES["needle1536"]["tail_cutoffs"]


def test_ready_false_for_missing(tmp_path):
    m = load_module()
    assert m.is_ready_candidate(tmp_path / "missing.json") is False

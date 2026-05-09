import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "audit" / "run_lower_anchor_phase2u_fast_micro_closer.py"


def load_module():
    spec = importlib.util.spec_from_file_location("phase2u_fast", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_generate_pieces_coverage_and_order():
    m = load_module()
    pieces = m.generate_pieces("0.0", "1.0", 4, "0.02", "gap")
    assert pieces[0]["K_lo"] == "0"
    assert pieces[-1]["K_hi"] == "1"
    assert len(pieces) == 4
    assert float(pieces[0]["K_hi"]) > float(pieces[1]["K_lo"])
    assert pieces[2]["segment_id"] == "phase2u_gap_p0002"


def test_profiles_exist():
    m = load_module()
    assert "fast" in m.PROFILES
    assert "standard" in m.PROFILES
    assert "aggressive" in m.PROFILES
    assert "2048" in m.PROFILES["fast"]["tail_cutoffs"]


def test_ready_candidate_detection(tmp_path):
    m = load_module()
    p = tmp_path / "candidate.json"
    p.write_text(json.dumps({
        "theorem_facing": True,
        "promotion_allowed": True,
        "failure_fields": [],
        "selected_phase2p_row": {"theorem_ready": True, "failure_reasons": []},
    }))
    assert m.is_ready_candidate(p)
    p.write_text(json.dumps({
        "theorem_facing": True,
        "promotion_allowed": False,
        "failure_fields": [],
        "selected_phase2p_row": {"theorem_ready": True, "failure_reasons": []},
    }))
    assert not m.is_ready_candidate(p)


def test_parse_args_dry_run_defaults():
    m = load_module()
    args = m.parse_args([
        "--label", "x", "--K-lo", "0.1", "--K-hi", "0.2", "--dry-run"
    ])
    assert args.label == "x"
    assert args.pieces == 64
    assert args.profile == "fast"

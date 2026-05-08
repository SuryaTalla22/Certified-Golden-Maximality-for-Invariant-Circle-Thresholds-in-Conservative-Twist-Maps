import importlib.util
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "audit" / "run_lower_anchor_phase2t_parallel_gap_closer.py"


def load_module():
    spec = importlib.util.spec_from_file_location("phase2t_parallel", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_interval_pieces_cover_and_overlap():
    m = load_module()
    pieces = m.interval_pieces(0.0, 1.0, 4, overlap=0.01, label_prefix="x", depth=0)
    assert len(pieces) == 4
    assert pieces[0]["K_lo"] == 0.0
    assert pieces[-1]["K_hi"] == 1.0
    for a, b in zip(pieces, pieces[1:]):
        assert a["K_hi"] > b["K_lo"]


def test_split_failed_piece():
    m = load_module()
    p = m.interval_pieces(0.0, 1.0, 1, overlap=0.0, label_prefix="x", depth=0)[0]
    children = m.split_failed_piece(p, 2, 0.01)
    assert len(children) == 2
    assert children[0]["depth"] == 1
    assert children[0]["K_hi"] > children[1]["K_lo"]


def test_safe_label():
    m = load_module()
    assert m.safe_label("collar-012b1/a") == "collar_012b1_a"


def test_piece_paths_contain_label():
    m = load_module()
    paths = m.piece_paths("collar_012b1_d00_p0000")
    assert "collar_012b1_d00_p0000" in paths["phase2p_candidate"]
    assert paths["ready_candidate"].endswith("THEOREM_READY_candidate.json")

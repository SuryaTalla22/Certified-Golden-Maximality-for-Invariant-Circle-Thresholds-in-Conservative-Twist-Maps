from pathlib import Path
import importlib.util
import sys


def load_module():
    p = Path("scripts/audit/run_lower_anchor_phase2w_radius_shell_rescue.py")
    spec = importlib.util.spec_from_file_location("phase2w_radius_shell", p)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_slug():
    m = load_module()
    assert m.slug_float(1e-7) == "1.000e-07".replace(".", "p")


def test_piece_formula():
    m = load_module()
    pieces = m.make_pieces("gap", 0.0, 1.0, 4, overlap=0.1)
    assert len(pieces) == 4
    assert pieces[0].base_K_lo == "0"
    assert pieces[0].K_lo == "0"
    assert pieces[1].K_lo == "0.15"
    assert pieces[-1].K_hi == "1"


def test_parse_indices():
    m = load_module()
    assert m.parse_indices("1,3,5") == [1, 3, 5]
    assert m.parse_indices("2-4") == [2, 3, 4]
    assert m.parse_indices("1,3-5") == [1, 3, 4, 5]


def test_profile_exists():
    m = load_module()
    prof = m.profile_config("shell")
    assert "1.3" in prof.radius_multipliers
    assert "0.0000001" in prof.sigma_values

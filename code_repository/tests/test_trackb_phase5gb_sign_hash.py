from __future__ import annotations
import json
import hashlib
from pathlib import Path
import numpy as np

from kam_theorem_suite.lower_param.phase5g_formal_components import canonical_file_sha256, residual_proof_object


def test_phase5gb_hash_is_raw_file_hash(tmp_path: Path):
    p = tmp_path / "cert.json"
    p.write_text('{\n  "b": 2,\n  "a": 1\n}\n', encoding="utf-8")
    expected = hashlib.sha256(p.read_bytes()).hexdigest()
    assert canonical_file_sha256(p) == expected


def test_phase5gb_residual_force_sign_minus_one(tmp_path: Path):
    M = 32
    u = np.zeros(M)
    npz = tmp_path / "seed.npz"
    np.savez(npz, u=u, K=0.1, omega=(5**0.5 - 1)/2)
    obj = residual_proof_object(npz, nu=1.001, grid_factor=1, residual_slack=1e-13, require_sign=-1)
    assert obj["selected_sign"] == -1
    assert obj["scalar_residual_linf_upper"] > 0

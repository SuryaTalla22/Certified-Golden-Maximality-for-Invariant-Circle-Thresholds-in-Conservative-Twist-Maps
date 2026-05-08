from __future__ import annotations

from pathlib import Path

import numpy as np

from kam_theorem_suite.lower_param.small_divisor_audit import (
    GOLDEN_OMEGA,
    audit_npz_small_divisor,
    small_divisor_table,
    SmallDivisorAuditConfig,
)


def test_small_divisor_table_basic():
    tab = small_divisor_table(64, GOLDEN_OMEGA)
    assert tab["max_mode"] == 64
    assert tab["min_denominator"] > 0.0
    assert tab["max_inverse"] > 1.0
    assert len(tab["worst_modes_by_denominator"]) > 0


def test_phase3_npz_audit_smoke(tmp_path: Path):
    M = 128
    t = np.arange(M) / M
    omega = GOLDEN_OMEGA
    u = 1e-3 * np.sin(2 * np.pi * t) + 2e-4 * np.cos(4 * np.pi * t)
    residual = 1e-12 * np.sin(2 * np.pi * t)
    freq = np.fft.fftfreq(M, d=1.0 / M)
    npz = tmp_path / "seed.npz"
    np.savez(
        npz,
        schema="test_trackb_phase3_seed",
        K=0.1,
        M=M,
        omega=omega,
        u=u,
        residual=residual,
        freq=freq,
        diagnostic_only=True,
        theorem_facing=False,
    )
    rec = audit_npz_small_divisor(SmallDivisorAuditConfig(
        npz_path=str(npz),
        out_dir=str(tmp_path / "out"),
        nu_grid=(1.002, 1.003),
        force=True,
    ))
    assert rec["diagnostic_only"] is True
    assert rec["theorem_facing"] is False
    assert rec["small_divisor_diagnostics"]["max_mode"] == 64
    assert rec["weighted_cohomology_norms"]["nu_1.003000"]["cohomology_correction_l1_nu"] > 0.0

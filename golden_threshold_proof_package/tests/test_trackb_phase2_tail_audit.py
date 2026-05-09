from __future__ import annotations

from pathlib import Path
import numpy as np

from kam_theorem_suite.lower_param.fourier_tail_audit import TailAuditConfig, audit_npz, run_phase2_tail_audit


def test_phase2_tail_audit_synthetic_npz(tmp_path: Path):
    M = 128
    theta = np.arange(M) / M
    omega = (5 ** 0.5 - 1) / 2
    u = 1e-3 * np.sin(2 * np.pi * theta) + 2e-5 * np.cos(4 * np.pi * theta)
    residual = 1e-12 * np.sin(2 * np.pi * theta)
    freq = np.fft.fftfreq(M, d=1.0 / M)
    npz = tmp_path / "seed.npz"
    np.savez_compressed(
        npz,
        schema="theorem_iii_trackb_phase1_embedding_npz_v1",
        diagnostic_only=True,
        theorem_facing=False,
        K=0.1,
        M=M,
        omega=omega,
        theta=theta,
        u=u,
        residual=residual,
        u_coeff=np.fft.fft(u) / M,
        residual_coeff=np.fft.fft(residual) / M,
        freq=freq,
    )
    rec = audit_npz(TailAuditConfig(npz_path=str(npz), out_dir=str(tmp_path / "audit"), nu_grid=(1.002, 1.005), force=True))
    assert rec["diagnostic_only"] is True
    assert rec["theorem_facing"] is False
    assert rec["M"] == M
    assert rec["weighted_norms"]["nu_1.002000"]["u_l1_nu"] > 0
    assert rec["coefficient_checks"]["u_coeff_recomputed_vs_saved_linf"] < 1e-16

    summary = run_phase2_tail_audit(npz_paths=[str(npz)], out_dir=tmp_path / "grid", workers=1, nu_grid=(1.002,), force=True)
    assert summary["counts"]["completed_records"] == 1
    assert (tmp_path / "grid" / "phase2_tail_audit_summary.json").exists()

from pathlib import Path
import numpy as np

from kam_theorem_suite.lower_param.automatic_reducibility_audit import (
    audit_npz_auto_reducibility,
    AutoReducibilityAuditConfig,
)


def test_phase4_auto_reducibility_smoke(tmp_path: Path):
    M = 128
    theta = np.arange(M, dtype=float) / M
    omega = (np.sqrt(5.0) - 1.0) / 2.0
    K = 0.05
    u = 0.002 * np.sin(2*np.pi*theta)
    freq = np.fft.fftfreq(M, d=1.0/M)
    # Construct residual with same scalar equation used by the audit.
    def shift(v, sign=1):
        c = np.fft.fft(v)/M
        return np.fft.ifft(c*np.exp(1j*2*np.pi*freq*omega*sign)*M).real
    residual = shift(u,1)-2*u+shift(u,-1)-(K/(2*np.pi))*np.sin(2*np.pi*(theta+u))
    npz = tmp_path / "toy.npz"
    np.savez_compressed(npz, schema="toy", K=K, M=M, omega=omega, u=u, freq=freq, residual=residual)
    rec = audit_npz_auto_reducibility(AutoReducibilityAuditConfig(npz_path=str(npz), out_dir=str(tmp_path), force=True))
    assert rec["schema"] == "theorem_iii_trackb_phase4_auto_reducibility_audit_v1"
    assert rec["diagnostic_only"] is True
    assert rec["scalar_metrics"]["twist_abs_average"] > 0.0
    assert "nu_1.003000" in rec["weighted_auto_reducibility_norms"]

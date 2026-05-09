"""Common numerical utilities for Theorem III Track B Phase 4i.

Diagnostic-only utilities.  These routines intentionally do not provide
interval or theorem-facing bounds.  They are used to prepare and inspect
candidate seeds for a later rigorous validator.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple
import json
import math
import os
import re

import numpy as np

GOLDEN_ROTATION = (math.sqrt(5.0) - 1.0) / 2.0
TWOPI = 2.0 * math.pi


def ensure_dir(path: str | Path) -> None:
    Path(path).mkdir(parents=True, exist_ok=True)


def write_json(path: str | Path, payload: Dict[str, Any]) -> None:
    path = Path(path)
    ensure_dir(path.parent)
    tmp = path.with_suffix(path.suffix + f".tmp.{os.getpid()}")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, sort_keys=True)
        f.write("\n")
    os.replace(tmp, path)


def read_json(path: str | Path) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def csv_write(path: str | Path, rows: Sequence[Dict[str, Any]]) -> None:
    import csv
    path = Path(path)
    ensure_dir(path.parent)
    if not rows:
        with open(path, "w", encoding="utf-8") as f:
            f.write("")
        return
    keys: List[str] = []
    seen = set()
    for r in rows:
        for k in r.keys():
            if k not in seen:
                keys.append(k)
                seen.add(k)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in keys})


def sanitize_float_tag(x: float, ndigits: int = 10) -> str:
    s = f"{x:.{ndigits}f}"
    return s.replace("-", "m").replace(".", "p")


def parse_K_from_path(path: str | Path) -> Optional[float]:
    name = Path(path).name
    m = re.search(r"K([0-9]+p[0-9]+)", name)
    if not m:
        return None
    try:
        return float(m.group(1).replace("p", "."))
    except Exception:
        return None


def parse_M_from_path(path: str | Path) -> Optional[int]:
    name = Path(path).name
    m = re.search(r"_M(\d+)", name)
    if not m:
        return None
    try:
        return int(m.group(1))
    except Exception:
        return None


def _first_numeric_array(z: np.lib.npyio.NpzFile, names: Sequence[str]) -> Optional[np.ndarray]:
    for nm in names:
        if nm in z.files:
            arr = np.asarray(z[nm])
            if arr.size > 0 and np.issubdtype(arr.dtype, np.number):
                return np.array(arr, dtype=float).reshape(-1)
    return None


def _first_scalar(z: np.lib.npyio.NpzFile, names: Sequence[str]) -> Optional[float]:
    for nm in names:
        if nm in z.files:
            arr = np.asarray(z[nm])
            if arr.size:
                try:
                    return float(arr.reshape(-1)[0])
                except Exception:
                    pass
    return None


@dataclass
class SeedData:
    path: str
    u: np.ndarray
    K: float
    omega: float
    M: int
    keys: List[str]


def load_seed(npz_path: str | Path, omega_override: Optional[float] = None) -> SeedData:
    npz_path = str(npz_path)
    with np.load(npz_path, allow_pickle=False) as z:
        keys = list(z.files)
        u = _first_numeric_array(
            z,
            [
                "u", "u_grid", "u_values", "embedding_u", "phase_u", "graph_u",
                "solution_u", "u_real", "u_samples",
            ],
        )
        if u is None:
            # Fall back to x/theta if both are present.
            x = _first_numeric_array(z, ["x", "x_grid", "embedding_x", "x_values"])
            th = _first_numeric_array(z, ["theta", "theta_grid", "t", "grid"])
            if x is not None:
                if th is None or th.size != x.size:
                    th = np.arange(x.size, dtype=float) / float(x.size)
                u = np.mod(x - th + 0.5, 1.0) - 0.5
        if u is None:
            raise KeyError(
                f"Could not locate a periodic u-array in {npz_path}. Available keys: {keys}"
            )
        K = _first_scalar(z, ["K", "k", "parameter_K", "K_value"])
        omega = _first_scalar(z, ["omega", "rho", "rotation", "rotation_number"])
    if K is None:
        K = parse_K_from_path(npz_path)
    if K is None:
        raise KeyError(f"Could not determine K from {npz_path}")
    if omega_override is not None:
        omega = float(omega_override)
    if omega is None:
        omega = GOLDEN_ROTATION
    u = np.asarray(u, dtype=float).reshape(-1)
    return SeedData(path=npz_path, u=u, K=float(K), omega=float(omega), M=int(u.size), keys=keys)


def modes(n: int) -> np.ndarray:
    return np.fft.fftfreq(n, d=1.0 / n).astype(int)


def fft_coeff(v: np.ndarray) -> np.ndarray:
    v = np.asarray(v)
    return np.fft.fft(v) / v.size


def values_from_coeff(c: np.ndarray) -> np.ndarray:
    return np.fft.ifft(c * c.size)


def spectral_shift(v: np.ndarray, omega: float) -> np.ndarray:
    n = v.size
    k = modes(n)
    c = np.fft.fft(v)
    return np.fft.ifft(c * np.exp(1j * TWOPI * k * omega)).real


def spectral_derivative(v: np.ndarray) -> np.ndarray:
    n = v.size
    k = modes(n)
    c = np.fft.fft(v)
    return np.fft.ifft(c * (1j * TWOPI * k)).real


def lowpass_values(v: np.ndarray, cutoff_mode: Optional[int]) -> np.ndarray:
    if cutoff_mode is None:
        return np.asarray(v, dtype=float).copy()
    n = v.size
    cutoff = int(cutoff_mode)
    k = modes(n)
    c = np.fft.fft(v)
    c[np.abs(k) > cutoff] = 0.0
    return np.fft.ifft(c).real


def highpass_values(v: np.ndarray, cutoff_mode: Optional[int]) -> np.ndarray:
    if cutoff_mode is None:
        return np.zeros_like(v, dtype=float)
    n = v.size
    cutoff = int(cutoff_mode)
    k = modes(n)
    c = np.fft.fft(v)
    c[np.abs(k) <= cutoff] = 0.0
    return np.fft.ifft(c).real


def interpolation_coeff_from_values(v: np.ndarray, L: int) -> np.ndarray:
    """Embed Fourier coefficients of an M-grid signal into an L-grid coefficient array."""
    v = np.asarray(v, dtype=float)
    M = v.size
    if L == M:
        return fft_coeff(v)
    if L < M:
        raise ValueError(f"Cannot interpolate from M={M} to smaller L={L}")
    cM = fft_coeff(v)
    cL = np.zeros(L, dtype=complex)
    kM = modes(M)
    kL_to_index = {int(k): i for i, k in enumerate(modes(L))}
    for i, k in enumerate(kM):
        j = kL_to_index.get(int(k))
        if j is not None:
            cL[j] = cM[i]
    return cL


def interp_values(v: np.ndarray, L: int) -> np.ndarray:
    cL = interpolation_coeff_from_values(v, L)
    return values_from_coeff(cL).real


def interp_adjoint_values(y: np.ndarray, M: int) -> np.ndarray:
    """Adjoint of interp_values(v, L) under Euclidean dot products."""
    y = np.asarray(y, dtype=float)
    L = y.size
    if L == M:
        return y.copy()
    Y = np.fft.fft(y)
    kM = modes(M)
    kL_to_index = {int(k): i for i, k in enumerate(modes(L))}
    B = np.zeros(M, dtype=complex)
    for i, k in enumerate(kM):
        j = kL_to_index.get(int(k))
        if j is not None:
            B[i] = Y[j]
    return np.fft.ifft(B).real


def scalar_residual(u: np.ndarray, K: float, omega: float, sign: int = 1) -> np.ndarray:
    """Scalar hull-function residual on the native grid.

    Convention sign=1 corresponds to
        u(theta+w)-2u(theta)+u(theta-w) - K/(2pi) sin(2pi(theta+u(theta))).
    """
    M = u.size
    theta = np.arange(M, dtype=float) / float(M)
    return (
        spectral_shift(u, omega)
        - 2.0 * u
        + spectral_shift(u, -omega)
        - sign * (K / TWOPI) * np.sin(TWOPI * (theta + u))
    )


def scalar_residual_on_grid_from_core(
    u_core: np.ndarray, K: float, omega: float, L: int, sign: int = 1
) -> np.ndarray:
    uL = interp_values(u_core, L)
    theta = np.arange(L, dtype=float) / float(L)
    return (
        spectral_shift(uL, omega)
        - 2.0 * uL
        + spectral_shift(uL, -omega)
        - sign * (K / TWOPI) * np.sin(TWOPI * (theta + uL))
    )


def linearized_residual_apply_on_grid(
    deltaL: np.ndarray, uL: np.ndarray, K: float, omega: float, sign: int = 1
) -> np.ndarray:
    theta = np.arange(deltaL.size, dtype=float) / float(deltaL.size)
    c = sign * K * np.cos(TWOPI * (theta + uL))
    return spectral_shift(deltaL, omega) - 2.0 * deltaL + spectral_shift(deltaL, -omega) - c * deltaL


def linearized_residual_adjoint_on_grid(
    yL: np.ndarray, uL: np.ndarray, K: float, omega: float, sign: int = 1
) -> np.ndarray:
    # Shift adjoints are opposite shifts; the symmetric second-difference operator
    # remains the same because both +/- shifts are present.
    theta = np.arange(yL.size, dtype=float) / float(yL.size)
    c = sign * K * np.cos(TWOPI * (theta + uL))
    return spectral_shift(yL, -omega) - 2.0 * yL + spectral_shift(yL, omega) - c * yL


def l1_nu(v: np.ndarray, nu: float) -> float:
    c = fft_coeff(np.asarray(v, dtype=float))
    k = np.abs(modes(v.size))
    return float(np.sum(np.abs(c) * (float(nu) ** k)))


def derivative_l1_nu(v: np.ndarray, nu: float) -> float:
    c = fft_coeff(np.asarray(v, dtype=float))
    k = np.abs(modes(v.size))
    return float(np.sum(np.abs(c) * (TWOPI * k) * (float(nu) ** k)))


def shell_summaries(coeff_abs: np.ndarray, shell_fracs: Sequence[float] = (0, .25, .5, .75, .9, 1.0)) -> List[Dict[str, Any]]:
    n = coeff_abs.size
    k_abs = np.abs(modes(n))
    kmax = int(np.max(k_abs))
    out: List[Dict[str, Any]] = []
    for a, b in zip(shell_fracs[:-1], shell_fracs[1:]):
        lo = int(math.floor(a * kmax))
        hi = int(math.floor(b * kmax))
        mask = (k_abs >= lo) & (k_abs <= hi)
        vals = coeff_abs[mask]
        out.append({
            "frac_lo": float(a),
            "frac_hi": float(b),
            "mode_lo": int(lo),
            "mode_hi": int(hi),
            "sum_abs": float(np.sum(vals)),
            "max_abs": float(np.max(vals)) if vals.size else 0.0,
            "count": int(vals.size),
        })
    return out


def top_modes(v: np.ndarray, count: int = 30, derivative_weight: bool = False) -> List[Dict[str, Any]]:
    c = fft_coeff(np.asarray(v, dtype=float))
    k = modes(v.size)
    score = np.abs(c)
    if derivative_weight:
        score = score * (TWOPI * np.abs(k))
    idx = np.argsort(score)[::-1][:count]
    out = []
    for i in idx:
        out.append({
            "mode": int(k[i]),
            "abs_coeff": float(abs(c[i])),
            "score": float(score[i]),
            "real": float(c[i].real),
            "imag": float(c[i].imag),
        })
    return out


def save_seed_npz(
    path: str | Path,
    u: np.ndarray,
    K: float,
    omega: float,
    source_path: str,
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    path = Path(path)
    ensure_dir(path.parent)
    M = len(u)
    theta = np.arange(M, dtype=float) / float(M)
    x = theta + u
    r = x - (theta - omega + spectral_shift(u, -omega))
    md = json.dumps(metadata or {}, sort_keys=True)
    np.savez_compressed(
        path,
        u=np.asarray(u, dtype=float),
        K=float(K),
        omega=float(omega),
        M=int(M),
        theta=theta,
        x=x,
        r=r,
        source_path=str(source_path),
        metadata_json=np.array(md),
    )

from __future__ import annotations

"""Phase 2N lower-anchor rescue tools.

Phase 2N is a deliberately conservative replacement for the failed Phase-2M
brute-force collar sweep.  The utilities here have three design goals:

1. run one numerical resolution at a time, so an expensive/high-N attempt cannot
   destroy the diagnostics from cheaper attempts;
2. score attempts by the actual Phase-2E theorem gate ``Y + Z r + T < r`` rather
   than by the older compact analytic margin; and
3. support seeded continuation and endpoint probes without requiring the entire
   near-critical collar to be proved in one monolithic process.

The module is fail-closed.  The standard strict ledger is the only ledger marked
``theorem_eligible`` by default.  Experimental tail variants are written for
brainstorming and diagnostics but are not promoted unless an explicit caller
chooses to treat them as research leads.
"""

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence
import json
import math
import time

import numpy as np

from .lower_anchor_regeneration import GOLDEN_INVERSE
from ..analytic_lower_krawczyk import (
    AnalyticLowerRadiiLedger,
    build_analytic_lower_radii_ledger,
    build_modewise_divisor_ledger,
    exact_small_divisor_gap,
)
from ..analytic_norms import analytic_weights, spectral_coefficients_from_samples, spectral_wavenumbers
from ..invariance_defect import residual_samples
from ..standard_map import HarmonicFamily
from ..torus_validator import (
    AnalyticInvariantCircleCertificate,
    build_analytic_invariant_circle_certificate,
)


@dataclass(frozen=True)
class Phase2NAttemptConfig:
    segment_id: str
    K_lo: float
    K_hi: float
    K_mid: float
    N: int
    oversample_factor: int = 64
    sigma_cap: float = 1.0e-4
    outward_rounding_tolerance: float = 1.0e-12
    theorem_margin_safety_factor: float = 10.0
    phase2e_nonlinear_margin_fraction: float = 0.25
    seed_path: str | None = None
    seed_policy: str = "none"
    tail_variant_mode: str = "diagnostic"
    created_by: str = "phase2n-single-N-probe"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Phase2NScore:
    theorem_ready: bool
    radii_margin: float
    residual_Y: float
    linear_Z: float
    radius_r: float
    tail_T: float
    finite_radii_margin: float | None
    source_theorem_margin: float | None
    selected_N: int
    sigma: float
    failure_reasons: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["failure_reasons"] = list(self.failure_reasons)
        return d


@dataclass(frozen=True)
class Phase2NTailVariant:
    name: str
    theorem_eligible: bool
    residual_Y: float
    linear_Z: float
    radius_r: float
    tail_T: float
    radii_lhs: float
    radii_margin: float
    components: dict[str, float]
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "theorem_eligible": bool(self.theorem_eligible),
            "residual_Y": float(self.residual_Y),
            "linear_Z": float(self.linear_Z),
            "radius_r": float(self.radius_r),
            "tail_T": float(self.tail_T),
            "radii_lhs": float(self.radii_lhs),
            "radii_margin": float(self.radii_margin),
            "components": {k: float(v) for k, v in self.components.items()},
            "notes": self.notes,
        }


@dataclass(frozen=True)
class Phase2NAttemptResult:
    schema: str
    status: str
    config: Phase2NAttemptConfig
    elapsed_seconds: float
    certificate_summary: dict[str, Any]
    strict_ledger: dict[str, Any]
    score: Phase2NScore
    tail_variants: tuple[Phase2NTailVariant, ...]
    seed_summary: dict[str, Any]
    raw_certificate: dict[str, Any] | None = None

    @property
    def theorem_ready(self) -> bool:
        return bool(self.score.theorem_ready)

    def to_dict(self, *, include_raw_certificate: bool = True) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "status": self.status,
            "theorem_ready": bool(self.theorem_ready),
            "config": self.config.to_dict(),
            "elapsed_seconds": float(self.elapsed_seconds),
            "certificate_summary": self.certificate_summary,
            "strict_ledger": self.strict_ledger,
            "score": self.score.to_dict(),
            "tail_variants": [v.to_dict() for v in self.tail_variants],
            "seed_summary": self.seed_summary,
            "raw_certificate": self.raw_certificate if include_raw_certificate else None,
        }


def atomic_write_json(path: str | Path, payload: Mapping[str, Any]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    tmp.replace(path)


def parse_int_list(raw: str | Sequence[int]) -> tuple[int, ...]:
    if isinstance(raw, str):
        vals = [int(x.strip()) for x in raw.split(",") if x.strip()]
    else:
        vals = [int(x) for x in raw]
    return tuple(sorted({x for x in vals if x > 0}))


def parse_float_list(raw: str | Sequence[float]) -> tuple[float, ...]:
    if isinstance(raw, str):
        vals = [float(x.strip()) for x in raw.split(",") if x.strip()]
    else:
        vals = [float(x) for x in raw]
    return tuple(vals)


def _as_dict(obj: Any) -> dict[str, Any]:
    if isinstance(obj, Mapping):
        return dict(obj)
    if hasattr(obj, "to_dict"):
        return dict(obj.to_dict())
    return dict(getattr(obj, "__dict__", {}) or {})


def _finite_float(value: Any, default: float | None = None) -> float | None:
    try:
        x = float(value)
    except Exception:
        return default
    return x if math.isfinite(x) else default


def _first_mapping_with_source_validation(payload: Any) -> Mapping[str, Any] | None:
    """Find a certificate-like mapping containing source_validation/u/z samples."""
    if isinstance(payload, Mapping):
        if isinstance(payload.get("source_validation"), Mapping):
            return payload
        if isinstance(payload.get("raw_certificate"), Mapping):
            found = _first_mapping_with_source_validation(payload["raw_certificate"])
            if found is not None:
                return found
        for key in ("raw_validation_records", "records", "anchor_segments", "attempts", "results"):
            val = payload.get(key)
            if isinstance(val, Sequence) and not isinstance(val, (str, bytes)):
                # Search from the end first: continuation seeds usually want the
                # most recent/highest-K record.
                for item in reversed(list(val)):
                    found = _first_mapping_with_source_validation(item)
                    if found is not None:
                        return found
        if isinstance(payload.get("phase2n_result"), Mapping):
            return _first_mapping_with_source_validation(payload["phase2n_result"])
    return None


def load_seed_from_json(path: str | Path) -> tuple[np.ndarray | None, np.ndarray | None, float | None, dict[str, Any]]:
    path = Path(path)
    data = json.loads(path.read_text())
    cert = _first_mapping_with_source_validation(data)
    summary: dict[str, Any] = {"seed_path": str(path), "found": False}
    if cert is None:
        summary["reason"] = "no_source_validation_mapping_found"
        return None, None, None, summary
    src = cert.get("source_validation") if isinstance(cert, Mapping) else None
    if not isinstance(src, Mapping):
        summary["reason"] = "source_validation_missing"
        return None, None, None, summary
    u_raw = src.get("u")
    z_raw = src.get("z")
    lam_raw = src.get("lambda_value")
    try:
        u = np.asarray(u_raw, dtype=float)
    except Exception:
        u = None
    try:
        z = np.asarray(z_raw, dtype=float)
    except Exception:
        z = None
    lam = _finite_float(lam_raw)
    if u is None or u.size == 0:
        summary["reason"] = "seed_u_missing_or_empty"
        return None, None, lam, summary
    summary.update({
        "found": True,
        "seed_N": int(u.size),
        "has_z": bool(z is not None and z.size == u.size + 1),
        "lambda_value": lam,
    })
    return u, z, lam, summary


def resample_periodic_samples(samples: np.ndarray, target_N: int) -> np.ndarray:
    """Fourier zero-pad/truncate real periodic samples to a new grid length."""
    arr = np.asarray(samples, dtype=float)
    target_N = int(target_N)
    if arr.size == target_N:
        out = arr.copy()
        out -= np.mean(out)
        return out
    if arr.size <= 0 or target_N <= 0:
        raise ValueError("positive source and target lengths are required")
    coeffs_shift = np.fft.fftshift(np.fft.fft(arr) / arr.size)
    old_N = arr.size
    if target_N >= old_N:
        pad = target_N - old_N
        left = pad // 2
        right = pad - left
        new_shift = np.pad(coeffs_shift, (left, right), mode="constant")
    else:
        drop = old_N - target_N
        left = drop // 2
        right = drop - left
        new_shift = coeffs_shift[left:old_N - right]
    new_coeffs = np.fft.ifftshift(new_shift)
    out = np.fft.ifft(new_coeffs * target_N).real
    out -= np.mean(out)
    return np.asarray(out, dtype=float)


def build_seed_for_N(seed_path: str | Path | None, N: int) -> tuple[np.ndarray | None, np.ndarray | None, dict[str, Any]]:
    if seed_path is None:
        return None, None, {"seed_path": None, "found": False, "policy": "none"}
    u, z, lam, summary = load_seed_from_json(seed_path)
    summary["target_N"] = int(N)
    if u is None:
        return None, None, summary
    try:
        uN = resample_periodic_samples(u, int(N))
        if lam is None and z is not None and z.size >= 1:
            lam = _finite_float(z[-1], 0.0)
        zN = np.concatenate([uN, np.array([0.0 if lam is None else float(lam)])])
        summary.update({"resampled": True, "resampled_N": int(N), "lambda_used": float(zN[-1])})
        return uN, zN, summary
    except Exception as exc:
        summary.update({"resampled": False, "reason": repr(exc)})
        return None, None, summary


def phase2e_score_from_ledger(ledger: AnalyticLowerRadiiLedger | Mapping[str, Any]) -> Phase2NScore:
    d = ledger.to_dict() if hasattr(ledger, "to_dict") else dict(ledger)
    return Phase2NScore(
        theorem_ready=bool(d.get("theorem_ready", False)),
        radii_margin=float(d.get("radii_margin", -float("inf"))),
        residual_Y=float(d.get("residual_Y", float("inf"))),
        linear_Z=float(d.get("linear_defect_Z", float("inf"))),
        radius_r=float(d.get("radius_r", 0.0)),
        tail_T=float(d.get("tail_bound_T", float("inf"))),
        finite_radii_margin=_finite_float(d.get("finite_radii_margin")),
        source_theorem_margin=_finite_float(d.get("source_theorem_margin")),
        selected_N=int(d.get("N", 0) or 0),
        sigma=float(d.get("sigma", 0.0) or 0.0),
        failure_reasons=tuple(str(x) for x in d.get("failure_reasons", []) or []),
    )


def score_key(score: Phase2NScore) -> tuple[float, float, float, float, int]:
    """Ordering key: theorem closure first, then Phase-2E margin."""
    margin = score.radii_margin if math.isfinite(score.radii_margin) else -float("inf")
    source = score.source_theorem_margin if score.source_theorem_margin is not None and math.isfinite(score.source_theorem_margin) else -float("inf")
    finite = score.finite_radii_margin if score.finite_radii_margin is not None and math.isfinite(score.finite_radii_margin) else -float("inf")
    return (1.0 if score.theorem_ready else 0.0, margin, finite, source, int(score.selected_N))


def _extract_u_lambda_from_certificate(certificate: AnalyticInvariantCircleCertificate | Mapping[str, Any]) -> tuple[np.ndarray | None, float | None]:
    d = _as_dict(certificate)
    src = d.get("source_validation") if isinstance(d.get("source_validation"), Mapping) else {}
    try:
        u = np.asarray(src.get("u", d.get("u")), dtype=float)
    except Exception:
        u = None
    if u is not None and u.size == 0:
        u = None
    lam = _finite_float(src.get("lambda_value", d.get("lambda_value")))
    return u, lam


def _strict_ledger_to_tail_variant(ledger: AnalyticLowerRadiiLedger) -> Phase2NTailVariant:
    d = ledger.to_dict()
    return Phase2NTailVariant(
        name="strict_phase2e_source_tail",
        theorem_eligible=True,
        residual_Y=float(d["residual_Y"]),
        linear_Z=float(d["linear_defect_Z"]),
        radius_r=float(d["radius_r"]),
        tail_T=float(d["tail_bound_T"]),
        radii_lhs=float(d["radii_lhs"]),
        radii_margin=float(d["radii_margin"]),
        components={
            "tail_response_bound": float(d.get("tail_response_bound", 0.0)),
            "nonlinear_response_bound": float(d.get("nonlinear_response_bound", 0.0)),
        },
        notes="This is the standard strict Phase-2E ledger; it is the only theorem-eligible variant by default.",
    )


def _coefficient_tail_envelope(coeffs: np.ndarray, *, sigma: float, band_fraction: float = 0.65, safety: float = 8.0) -> tuple[float, dict[str, float]]:
    """Diagnostic geometric tail envelope from the last resolved band.

    This is intentionally marked diagnostic.  It is useful for determining
    whether the present tail model is too pessimistic, but it is not a theorem
    replacement unless the paper later adds the corresponding proof.
    """
    coeffs = np.asarray(coeffs, dtype=complex)
    N = len(coeffs)
    if N <= 4:
        return float("inf"), {"reason_code": 1.0}
    k = np.abs(spectral_wavenumbers(N)).astype(float)
    mags = np.abs(coeffs)
    max_mode = np.max(k)
    if max_mode <= 0:
        return 0.0, {"max_mode": 0.0}
    band = (k >= float(band_fraction) * max_mode) & (k > 0)
    if not np.any(band):
        band = k > 0
    weighted_band = mags[band] * np.exp(2.0 * math.pi * float(sigma) * k[band])
    envelope = float(np.max(weighted_band)) * float(safety)
    # A conservative geometric denominator for one full mode step in the chosen
    # analytic weight.  If sigma is tiny, this intentionally becomes large.
    ratio = float(math.exp(-2.0 * math.pi * max(float(sigma), 1.0e-12)))
    denom = max(1.0e-15, 1.0 - ratio)
    tail_l1 = float(envelope * ratio / denom)
    return tail_l1, {
        "band_fraction": float(band_fraction),
        "safety": float(safety),
        "envelope": float(envelope),
        "ratio": float(ratio),
        "denominator": float(denom),
        "band_count": float(np.count_nonzero(band)),
    }


def build_tail_variants(
    certificate: AnalyticInvariantCircleCertificate,
    strict_ledger: AnalyticLowerRadiiLedger,
    *,
    oversample_factor: int,
    outward_rounding_tolerance: float,
) -> tuple[Phase2NTailVariant, ...]:
    variants: list[Phase2NTailVariant] = [_strict_ledger_to_tail_variant(strict_ledger)]
    u, lam = _extract_u_lambda_from_certificate(certificate)
    data = certificate.to_dict()
    inv_bound = _finite_float(data.get("cohomological_inverse_bound"), 0.0) or 0.0
    if u is None or lam is None:
        return tuple(variants)
    try:
        coeffs = spectral_coefficients_from_samples(np.asarray(u, dtype=float))
        sigma = float(strict_ledger.sigma)
        tail_l1, comp = _coefficient_tail_envelope(coeffs, sigma=sigma)
        diagnostic_tail_response = float(tail_l1 * inv_bound) if math.isfinite(tail_l1) else float("inf")
        # Keep the strict nonlinear response term, but swap in a high-mode-band
        # diagnostic tail.  This shows whether the standard tail bound is the
        # active obstruction.
        nonlinear = float(strict_ledger.nonlinear_response_bound)
        tail_T = float(diagnostic_tail_response + nonlinear)
        lhs = float(strict_ledger.residual_Y + strict_ledger.linear_defect_Z * strict_ledger.radius_r + tail_T)
        margin = float(strict_ledger.radius_r - lhs - abs(outward_rounding_tolerance))
        variants.append(Phase2NTailVariant(
            name="diagnostic_high_mode_envelope_tail",
            theorem_eligible=False,
            residual_Y=float(strict_ledger.residual_Y),
            linear_Z=float(strict_ledger.linear_defect_Z),
            radius_r=float(strict_ledger.radius_r),
            tail_T=float(tail_T),
            radii_lhs=float(lhs),
            radii_margin=float(margin),
            components={**comp, "tail_l1": float(tail_l1), "tail_response_bound": float(diagnostic_tail_response), "nonlinear_response_bound": nonlinear},
            notes="Diagnostic only: high-mode coefficient-envelope tail.  Use to decide whether a rigorous sharper tail lemma is worth implementing.",
        ))
    except Exception as exc:
        variants.append(Phase2NTailVariant(
            name="diagnostic_high_mode_envelope_tail_failed",
            theorem_eligible=False,
            residual_Y=float(strict_ledger.residual_Y),
            linear_Z=float(strict_ledger.linear_defect_Z),
            radius_r=float(strict_ledger.radius_r),
            tail_T=float("inf"),
            radii_lhs=float("inf"),
            radii_margin=-float("inf"),
            components={"exception_present": 1.0},
            notes=f"Diagnostic tail variant failed: {exc!r}",
        ))
    return tuple(variants)


def certificate_summary(certificate: AnalyticInvariantCircleCertificate) -> dict[str, Any]:
    d = certificate.to_dict()
    src = d.get("source_validation") if isinstance(d.get("source_validation"), Mapping) else {}
    return {
        "rho": float(d.get("rho", GOLDEN_INVERSE)),
        "K": float(d.get("K", 0.0)),
        "N": int(d.get("N", 0)),
        "theorem_status": d.get("theorem_status"),
        "finite_dimensional_success": bool(d.get("finite_dimensional_success", False)),
        "bridge_quality": d.get("bridge_quality"),
        "sigma_used": _finite_float(d.get("sigma_used")),
        "sigma_cap": _finite_float(d.get("sigma_cap")),
        "finite_radius": _finite_float(d.get("finite_radius")),
        "finite_radii_margin": _finite_float(d.get("finite_radii_margin")),
        "cohomological_correction_bound": _finite_float(d.get("cohomological_correction_bound")),
        "theorem_margin": _finite_float(d.get("theorem_margin")),
        "solver_iterations": int(src.get("solver_iterations", 0) or 0),
        "solver_history_tail": list(src.get("solver_history", []) or [])[-5:],
        "oversampled_residual_inf": _finite_float(src.get("oversampled_residual_inf")),
    }


def run_single_N_attempt(config: Phase2NAttemptConfig, *, include_raw_certificate: bool = True) -> Phase2NAttemptResult:
    t0 = time.time()
    u0, z0, seed_summary = build_seed_for_N(config.seed_path, int(config.N))
    if u0 is not None:
        seed_summary["policy"] = config.seed_policy or "json-resampled"
    try:
        cert = build_analytic_invariant_circle_certificate(
            rho=float(GOLDEN_INVERSE),
            K=float(config.K_mid),
            family=HarmonicFamily(),
            N=int(config.N),
            sigma_cap=float(config.sigma_cap),
            oversample_factor=int(config.oversample_factor),
            u0=u0,
            z0=z0,
        )
        strict = build_analytic_lower_radii_ledger(
            cert,
            oversample_factor=int(config.oversample_factor),
            outward_rounding_tolerance=float(config.outward_rounding_tolerance),
            safety_factor=float(config.theorem_margin_safety_factor),
            nonlinear_fraction_of_finite_margin=float(config.phase2e_nonlinear_margin_fraction),
        )
        score = phase2e_score_from_ledger(strict)
        variants = build_tail_variants(cert, strict, oversample_factor=int(config.oversample_factor), outward_rounding_tolerance=float(config.outward_rounding_tolerance))
        status = "phase2n-theorem-ready-single-N" if score.theorem_ready else "phase2n-diagnostic-single-N"
        return Phase2NAttemptResult(
            schema="phase2n_single_N_attempt_v1",
            status=status,
            config=config,
            elapsed_seconds=time.time() - t0,
            certificate_summary=certificate_summary(cert),
            strict_ledger=strict.to_dict(),
            score=score,
            tail_variants=variants,
            seed_summary=seed_summary,
            raw_certificate=cert.to_dict() if include_raw_certificate else None,
        )
    except Exception as exc:
        elapsed = time.time() - t0
        fail_score = Phase2NScore(
            theorem_ready=False,
            radii_margin=-float("inf"),
            residual_Y=float("inf"),
            linear_Z=float("inf"),
            radius_r=0.0,
            tail_T=float("inf"),
            finite_radii_margin=None,
            source_theorem_margin=None,
            selected_N=int(config.N),
            sigma=float(config.sigma_cap),
            failure_reasons=("phase2n_single_N_exception", repr(exc)),
        )
        return Phase2NAttemptResult(
            schema="phase2n_single_N_attempt_v1",
            status="phase2n-exception-single-N",
            config=config,
            elapsed_seconds=elapsed,
            certificate_summary={"exception": repr(exc)},
            strict_ledger={"exception": repr(exc), "theorem_ready": False, "radii_margin": -float("inf")},
            score=fail_score,
            tail_variants=tuple(),
            seed_summary=seed_summary,
            raw_certificate=None,
        )


def write_single_N_attempt(result: Phase2NAttemptResult, path: str | Path, *, include_raw_certificate: bool = True) -> None:
    atomic_write_json(path, result.to_dict(include_raw_certificate=include_raw_certificate))


def collect_attempts(paths: Iterable[str | Path]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for p in paths:
        try:
            data = json.loads(Path(p).read_text())
            if isinstance(data, Mapping):
                out.append(dict(data))
        except Exception:
            continue
    return out


def score_from_attempt_dict(data: Mapping[str, Any]) -> Phase2NScore:
    score = data.get("score") if isinstance(data.get("score"), Mapping) else {}
    return Phase2NScore(
        theorem_ready=bool(score.get("theorem_ready", False)),
        radii_margin=float(score.get("radii_margin", -float("inf"))),
        residual_Y=float(score.get("residual_Y", float("inf"))),
        linear_Z=float(score.get("linear_Z", float("inf"))),
        radius_r=float(score.get("radius_r", 0.0)),
        tail_T=float(score.get("tail_T", float("inf"))),
        finite_radii_margin=_finite_float(score.get("finite_radii_margin")),
        source_theorem_margin=_finite_float(score.get("source_theorem_margin")),
        selected_N=int(score.get("selected_N", 0) or 0),
        sigma=float(score.get("sigma", 0.0) or 0.0),
        failure_reasons=tuple(str(x) for x in score.get("failure_reasons", []) or []),
    )


def summarize_attempts(attempts: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for item in attempts:
        score = score_from_attempt_dict(item)
        cfg = item.get("config") if isinstance(item.get("config"), Mapping) else {}
        rows.append({
            "path": item.get("_path"),
            "status": item.get("status"),
            "segment_id": cfg.get("segment_id"),
            "K_mid": cfg.get("K_mid"),
            "N": score.selected_N,
            "oversample_factor": cfg.get("oversample_factor"),
            "sigma_cap": cfg.get("sigma_cap"),
            "sigma_used": score.sigma,
            "theorem_ready": score.theorem_ready,
            "radii_margin": score.radii_margin,
            "residual_Y": score.residual_Y,
            "linear_Z": score.linear_Z,
            "radius_r": score.radius_r,
            "tail_T": score.tail_T,
            "finite_radii_margin": score.finite_radii_margin,
            "source_theorem_margin": score.source_theorem_margin,
            "failure_reasons": list(score.failure_reasons),
            "elapsed_seconds": item.get("elapsed_seconds"),
        })
    rows.sort(key=lambda r: score_key(Phase2NScore(
        theorem_ready=bool(r["theorem_ready"]),
        radii_margin=float(r["radii_margin"]),
        residual_Y=float(r["residual_Y"]),
        linear_Z=float(r["linear_Z"]),
        radius_r=float(r["radius_r"]),
        tail_T=float(r["tail_T"]),
        finite_radii_margin=_finite_float(r["finite_radii_margin"]),
        source_theorem_margin=_finite_float(r["source_theorem_margin"]),
        selected_N=int(r["N"]),
        sigma=float(r["sigma_used"]),
        failure_reasons=tuple(r["failure_reasons"]),
    )), reverse=True)
    best = rows[0] if rows else None
    return {
        "schema": "phase2n_attempt_summary_v1",
        "attempt_count": len(rows),
        "theorem_ready_count": sum(1 for r in rows if r["theorem_ready"]),
        "best": best,
        "rows": rows,
    }


def build_phase2e_candidate_from_best_attempt(best_attempt: Mapping[str, Any], *, source_artifact: str) -> dict[str, Any]:
    """Create a Phase-2E-shaped candidate row from the best single-N result.

    This is intentionally a one-segment candidate.  It is useful for strict
    ingestion tests or manual merge into a collar bundle, but is not itself a
    proof of the full collar unless the caller merges a contiguous segment list.
    """
    cfg = best_attempt.get("config") if isinstance(best_attempt.get("config"), Mapping) else {}
    strict = best_attempt.get("strict_ledger") if isinstance(best_attempt.get("strict_ledger"), Mapping) else {}
    score = score_from_attempt_dict(best_attempt)
    row = {
        "segment_id": cfg.get("segment_id"),
        "K_lo": float(cfg.get("K_lo", cfg.get("K_mid", 0.0))),
        "K_hi": float(cfg.get("K_hi", cfg.get("K_mid", 0.0))),
        "K_mid": float(cfg.get("K_mid", 0.0)),
        "rho": float(GOLDEN_INVERSE),
        "N": int(score.selected_N),
        "sigma": float(score.sigma),
        "oversample_factor": int(cfg.get("oversample_factor", 0) or 0),
        "norm_name": strict.get("norm_name", "phase2n-strict-ledger"),
        "residual_Y": float(score.residual_Y),
        "linear_defect_Z": float(score.linear_Z),
        "tail_bound_T": float(score.tail_T),
        "radius_r": float(score.radius_r),
        "radii_margin": float(score.radii_margin),
        "small_divisor_min": float((strict.get("divisor_ledger") or {}).get("min_gap", 0.0) if isinstance(strict.get("divisor_ledger"), Mapping) else 0.0),
        "small_divisor_inverse_bound": float((strict.get("divisor_ledger") or {}).get("max_inverse_multiplier", 0.0) if isinstance(strict.get("divisor_ledger"), Mapping) else 0.0),
        "small_divisor_source": "phase2n-strict-phase2e-ledger",
        "source_module": "kam_theorem_suite.audit.lower_anchor_phase2n.run_single_N_attempt",
        "source_artifact": str(source_artifact),
        "certified": bool(score.theorem_ready),
        "finite_dimensional_only": bool(not score.theorem_ready),
        "closure_level": strict.get("closure_level", "phase2n_diagnostic"),
        "theorem_ready": bool(score.theorem_ready),
        "analytic_probe_attempted": True,
        "analytic_theorem_status": (best_attempt.get("certificate_summary") or {}).get("theorem_status") if isinstance(best_attempt.get("certificate_summary"), Mapping) else None,
        "analytic_theorem_margin": score.source_theorem_margin,
        "failure_reasons": list(score.failure_reasons),
        "phase2e_ledger": strict,
    }
    return {
        "schema": "phase2n_single_segment_candidate_v1",
        "theorem_facing": bool(score.theorem_ready),
        "diagnostic_only": bool(not score.theorem_ready),
        "promotion_allowed": False,
        "closure_level": "analytic_theorem_closure" if score.theorem_ready else "phase2n_single_segment_not_closed",
        "source": "Phase-2N single-segment margin-optimized candidate",
        "failure_fields": [] if score.theorem_ready else ["single_segment_not_theorem_ready"],
        "notes": "One-segment candidate. Merge into a contiguous collar only after neighboring segment overlaps are verified.",
        "anchor_segments": [row],
        "raw_phase2n_attempt": best_attempt,
    }


__all__ = [
    "Phase2NAttemptConfig",
    "Phase2NAttemptResult",
    "Phase2NScore",
    "Phase2NTailVariant",
    "atomic_write_json",
    "build_phase2e_candidate_from_best_attempt",
    "build_seed_for_N",
    "collect_attempts",
    "parse_float_list",
    "parse_int_list",
    "phase2e_score_from_ledger",
    "resample_periodic_samples",
    "run_single_N_attempt",
    "score_from_attempt_dict",
    "score_key",
    "summarize_attempts",
    "write_single_N_attempt",
]

from __future__ import annotations

"""Phase 2O tail/radius closure tools for the Theorem-III lower anchor.

Phase 2N made the near-critical lower-anchor obstruction precise: the residual
term can be driven to about 1e-9, while the strict Phase-2E ledger remains
negative because the source tail term is too large for the finite-dimensional
proof radius.  Phase 2O is a targeted, fail-closed scanner for that exact
obstruction.

The scanner consumes a Phase-2N single-N attempt JSON (or a Phase-2N summary
whose ``best.path`` points at one).  It does not rerun Newton.  Instead it uses
raw certificate samples already stored in the Phase-2N attempt to recompute
proof budgets under:

* strict source-tail radius multiplier scans;
* true working-sigma overrides below/above the historical 1e-4 floor; and
* explicitly diagnostic high-mode coefficient-envelope tail models.

Only rows with ``theorem_eligible=True`` may be promoted.  Diagnostic tail rows
are deliberately never theorem-facing unless a future manuscript adds the
corresponding lemma and the promotion logic is changed explicitly.
"""

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence
import csv
import json
import math

import numpy as np

from ..analytic_norms import analytic_weights, spectral_coefficients_from_samples, spectral_wavenumbers
from ..fourier_bounds import certify_fourier_tail_bound_from_coeffs
from ..invariance_defect import residual_samples
from ..standard_map import HarmonicFamily
from ..torus_validator import second_derivative_bound_on_ball
from ..analytic_lower_krawczyk import build_modewise_divisor_ledger, exact_small_divisor_gap
try:  # Phase 2N bundle supplies this helper; keep a local fallback for robustness.
    from .lower_anchor_phase2n import atomic_write_json
except Exception:  # pragma: no cover - fallback only
    def atomic_write_json(path: str | Path, payload: Mapping[str, Any]) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        tmp.replace(path)

_GOLDEN_RHO = (math.sqrt(5.0) - 1.0) / 2.0

try:
    from .lower_anchor_phase2aa_raw_payload_export import attach_raw_validation_payload_to_candidate
except Exception:  # pragma: no cover - stage-1B overlay not installed
    attach_raw_validation_payload_to_candidate = None  # type: ignore[assignment]


@dataclass(frozen=True)
class Phase2OScanConfig:
    input_path: str
    radius_multipliers: tuple[float, ...] = (1.0, 1.05, 1.1, 1.2, 1.5, 2.0, 2.5, 3.0, 3.25, 3.5, 4.0)
    sigma_values: tuple[float, ...] = (1.0e-4, 7.5e-5, 5.0e-5, 2.5e-5, 1.0e-5, 5.0e-6, 2.5e-6, 1.0e-6)
    tail_band_fractions: tuple[float, ...] = (0.50, 0.65, 0.75, 0.85)
    tail_safety_factors: tuple[float, ...] = (2.0, 4.0, 8.0, 16.0)
    nonlinear_margin_fraction: float = 0.25
    outward_rounding_tolerance: float = 1.0e-12
    theorem_margin_safety_factor: float = 10.0
    min_theorem_sigma: float = 1.0e-8
    allow_experimental_candidate: bool = False

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["radius_multipliers"] = list(self.radius_multipliers)
        d["sigma_values"] = list(self.sigma_values)
        d["tail_band_fractions"] = list(self.tail_band_fractions)
        d["tail_safety_factors"] = list(self.tail_safety_factors)
        return d


@dataclass(frozen=True)
class Phase2OInputSummary:
    resolved_input_path: str
    original_input_path: str
    segment_id: str | None
    K_lo: float | None
    K_hi: float | None
    K_mid: float
    N: int
    oversample_factor: int
    source_sigma: float
    source_radius: float
    source_margin: float
    source_tail_T: float
    source_residual_Y: float
    source_linear_Z: float
    has_raw_certificate: bool
    has_source_samples: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Phase2ORow:
    model_name: str
    tail_model: str
    theorem_eligible: bool
    theorem_ready: bool
    radius_multiplier: float
    radius_r: float
    sigma: float
    residual_Y: float
    finite_nonlinear_term: float
    linear_Z: float
    finite_eta: float
    finite_B_norm: float
    finite_lipschitz_bound: float
    finite_contraction_q: float
    finite_poly_margin: float
    tail_l1: float | None
    tail_response_bound: float
    nonlinear_guard: float
    tail_T: float
    radii_lhs: float
    radii_margin: float
    allowable_tail_max: float
    needed_tail_factor: float | None
    needed_radius_if_Z_fixed: float | None
    tail_theorem_usable: bool
    strip_width_proxy: float | None
    tail_start_mode: int
    oversample_factor: int
    sigma_source: str
    failure_reasons: tuple[str, ...] = field(default_factory=tuple)
    components: dict[str, Any] = field(default_factory=dict)
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["failure_reasons"] = list(self.failure_reasons)
        return d


@dataclass(frozen=True)
class Phase2OReport:
    schema: str
    status: str
    config: Phase2OScanConfig
    input_summary: Phase2OInputSummary
    strict_source_row: Phase2ORow
    theorem_ready_count: int
    theorem_eligible_count: int
    diagnostic_ready_count: int
    best_theorem_eligible: dict[str, Any] | None
    best_diagnostic: dict[str, Any] | None
    conclusion: dict[str, Any]
    rows: tuple[Phase2ORow, ...]
    raw_input_attempt: dict[str, Any] | None = None

    def to_dict(self, *, include_raw_input: bool = False) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "status": self.status,
            "config": self.config.to_dict(),
            "input_summary": self.input_summary.to_dict(),
            "strict_source_row": self.strict_source_row.to_dict(),
            "theorem_ready_count": int(self.theorem_ready_count),
            "theorem_eligible_count": int(self.theorem_eligible_count),
            "diagnostic_ready_count": int(self.diagnostic_ready_count),
            "best_theorem_eligible": self.best_theorem_eligible,
            "best_diagnostic": self.best_diagnostic,
            "conclusion": dict(self.conclusion),
            "rows": [r.to_dict() for r in self.rows],
            "raw_input_attempt": self.raw_input_attempt if include_raw_input else None,
        }


def _finite_float(value: Any, default: float | None = None) -> float | None:
    try:
        out = float(value)
    except Exception:
        return default
    return out if math.isfinite(out) else default


def _as_mapping(obj: Any) -> Mapping[str, Any]:
    return obj if isinstance(obj, Mapping) else {}


def parse_float_list(raw: str | Sequence[float]) -> tuple[float, ...]:
    if isinstance(raw, str):
        vals = [float(x.strip()) for x in raw.split(",") if x.strip()]
    else:
        vals = [float(x) for x in raw]
    out: list[float] = []
    for x in vals:
        if math.isfinite(x) and x > 0.0 and x not in out:
            out.append(float(x))
    return tuple(out)


def load_json(path: str | Path) -> dict[str, Any]:
    data = json.loads(Path(path).read_text())
    if not isinstance(data, Mapping):
        raise ValueError(f"expected JSON object in {path}")
    return dict(data)


def resolve_phase2n_attempt(input_path: str | Path) -> tuple[dict[str, Any], str]:
    """Resolve a Phase-2N summary/candidate/attempt into a single attempt object."""
    input_path = Path(input_path)
    data = load_json(input_path)

    # Phase-2N batch summary: follow best.path.
    best = data.get("best") if isinstance(data.get("best"), Mapping) else None
    if best and best.get("path"):
        best_path = Path(str(best["path"]))
        if not best_path.is_absolute():
            # Interpret relative to current repo root first; if missing, relative
            # to the summary file's directory as a fallback.
            if not best_path.exists():
                alt = input_path.parent / best_path.name
                if alt.exists():
                    best_path = alt
        return resolve_phase2n_attempt(best_path)

    # Phase-2N candidate generated by summarize_lower_anchor_phase2n_probes.py.
    if isinstance(data.get("raw_phase2n_attempt"), Mapping):
        return dict(data["raw_phase2n_attempt"]), str(input_path)

    # Phase-2N direct single-N attempt.
    if str(data.get("schema", "")).startswith("phase2n_single_N_attempt"):
        return data, str(input_path)

    # Some rows may nest the attempt inside a generic key.
    for key in ("phase2n_result", "attempt", "raw_attempt"):
        if isinstance(data.get(key), Mapping):
            nested = dict(data[key])
            if str(nested.get("schema", "")).startswith("phase2n_single_N_attempt"):
                return nested, str(input_path)

    raise ValueError(
        f"Could not resolve {input_path} to a Phase-2N attempt. "
        "Pass either a *_phase2n_batch_summary.json with best.path, "
        "a Phase-2N *_candidate.json, or a Phase-2N single-N JSON."
    )


def _extract_source_samples(raw_certificate: Mapping[str, Any]) -> tuple[np.ndarray | None, float | None, dict[str, Any]]:
    src = _as_mapping(raw_certificate.get("source_validation"))
    u_raw = src.get("u", raw_certificate.get("u"))
    lam_raw = src.get("lambda_value", raw_certificate.get("lambda_value"))
    summary: dict[str, Any] = {"source_validation_present": bool(src)}
    try:
        u = np.asarray(u_raw, dtype=float)
    except Exception:
        u = None
    if u is not None and u.size == 0:
        u = None
    lam = _finite_float(lam_raw)
    summary.update({"has_u": bool(u is not None), "N_from_u": None if u is None else int(u.size), "lambda_value": lam})
    return u, lam, summary


def _source_strict_row(attempt: Mapping[str, Any], input_summary: Phase2OInputSummary, cfg: Phase2OScanConfig) -> Phase2ORow:
    strict = _as_mapping(attempt.get("strict_ledger"))
    score = _as_mapping(attempt.get("score"))
    r = _finite_float(strict.get("radius_r"), _finite_float(score.get("radius_r"), 0.0)) or 0.0
    Z = _finite_float(strict.get("linear_defect_Z"), _finite_float(score.get("linear_Z"), float("inf"))) or float("inf")
    Y = _finite_float(strict.get("residual_Y"), _finite_float(score.get("residual_Y"), float("inf"))) or float("inf")
    T = _finite_float(strict.get("tail_bound_T"), _finite_float(score.get("tail_T"), float("inf"))) or float("inf")
    lhs = _finite_float(strict.get("radii_lhs"), Y + Z * r + T) or (Y + Z * r + T)
    margin = _finite_float(strict.get("radii_margin"), r - lhs - abs(cfg.outward_rounding_tolerance)) or -float("inf")
    tail_response = _finite_float(strict.get("tail_response_bound"), T) or T
    nonlinear_guard = _finite_float(strict.get("nonlinear_response_bound"), max(0.0, T - tail_response)) or 0.0
    allowable_tail = (1.0 - Z) * r - Y
    needed_tail_factor = None if T <= 0.0 or not math.isfinite(T) else allowable_tail / T
    needed_radius = None if (1.0 - Z) <= 0.0 else (T + Y) / (1.0 - Z)
    failures = tuple(str(x) for x in strict.get("failure_reasons", []) or [])
    return Phase2ORow(
        model_name="source_phase2e_strict",
        tail_model="source_phase2e_tail",
        theorem_eligible=True,
        theorem_ready=bool(strict.get("theorem_ready", score.get("theorem_ready", False))),
        radius_multiplier=1.0,
        radius_r=float(r),
        sigma=float(_finite_float(strict.get("sigma"), input_summary.source_sigma) or 0.0),
        residual_Y=float(Y),
        finite_nonlinear_term=float(Z * r),
        linear_Z=float(Z),
        finite_eta=0.0,
        finite_B_norm=0.0,
        finite_lipschitz_bound=0.0,
        finite_contraction_q=0.0,
        finite_poly_margin=0.0,
        tail_l1=None,
        tail_response_bound=float(tail_response),
        nonlinear_guard=float(nonlinear_guard),
        tail_T=float(T),
        radii_lhs=float(lhs),
        radii_margin=float(margin),
        allowable_tail_max=float(allowable_tail),
        needed_tail_factor=None if needed_tail_factor is None else float(needed_tail_factor),
        needed_radius_if_Z_fixed=None if needed_radius is None else float(needed_radius),
        tail_theorem_usable=True,
        strip_width_proxy=None,
        tail_start_mode=max(1, input_summary.N // 2 + 1),
        oversample_factor=int(input_summary.oversample_factor),
        sigma_source="phase2e_strict_ledger",
        failure_reasons=failures,
        components={"strict_ledger": strict},
        notes="Unmodified source Phase-2E ledger from the Phase-2N attempt.",
    )


def _modewise_inverse_applied_residual_from_samples(
    *,
    u: np.ndarray,
    rho: float,
    K: float,
    family: HarmonicFamily,
    lambda_value: float,
    sigma: float,
    oversample_factor: int,
) -> tuple[float, float, int]:
    resid = residual_samples(
        u,
        float(rho),
        float(K),
        family,
        lambda_value=float(lambda_value),
        oversample_factor=max(4, int(oversample_factor)),
    )
    coeffs = spectral_coefficients_from_samples(resid)
    k = spectral_wavenumbers(len(coeffs)).astype(int)
    weights = analytic_weights(len(coeffs), float(sigma))
    inverse_applied = 0.0
    weighted_l1 = 0.0
    for idx, kk in enumerate(k):
        mag = float(abs(coeffs[idx]))
        w = float(weights[idx])
        weighted_l1 += mag * w
        if int(kk) == 0:
            inv = 1.0
        else:
            gap = exact_small_divisor_gap(float(rho), int(kk))
            inv = float("inf") if gap <= 0.0 else 1.0 / gap
        inverse_applied += mag * w * inv
    return float(inverse_applied), float(weighted_l1), int(len(coeffs))


def _finite_radius_terms(
    *,
    u: np.ndarray | None,
    K: float,
    family: HarmonicFamily,
    radius: float,
    finite_eta: float,
    finite_B_norm: float,
    fallback_lipschitz: float,
) -> tuple[float, float, float, float, float]:
    """Return L(r), finite nonlinear term, Z, q, finite margin."""
    L = float(fallback_lipschitz)
    if u is not None and math.isfinite(radius) and radius > 0.0:
        try:
            L = float(second_derivative_bound_on_ball(u, float(K), float(radius), family))
        except Exception:
            L = float(fallback_lipschitz)
    finite_nl = float(0.5 * finite_B_norm * L * radius * radius)
    linear_Z = float(finite_nl / radius) if radius > 0.0 else float("inf")
    q = float(finite_B_norm * L * radius)
    finite_margin = float(radius - (finite_eta + finite_nl))
    return L, finite_nl, linear_Z, q, finite_margin


def _tail_response_from_strict(raw_certificate: Mapping[str, Any], strict: Mapping[str, Any]) -> tuple[float, float | None, dict[str, Any]]:
    tail_response = _finite_float(strict.get("tail_response_bound"))
    if tail_response is not None:
        return float(tail_response), None, {"source": "strict_ledger.tail_response_bound"}
    tail = _as_mapping(raw_certificate.get("tail_bound"))
    inv = _finite_float(raw_certificate.get("cohomological_inverse_bound"))
    tail_l1 = _finite_float(tail.get("tail_l1"))
    if inv is not None and tail_l1 is not None:
        return float(inv * tail_l1), float(tail_l1), {"source": "raw_certificate.tail_bound.tail_l1_times_inverse"}
    return float("inf"), tail_l1, {"source": "unavailable"}


def build_strict_radius_or_sigma_row(
    *,
    model_name: str,
    attempt: Mapping[str, Any],
    input_summary: Phase2OInputSummary,
    config: Phase2OScanConfig,
    radius_multiplier: float = 1.0,
    sigma: float | None = None,
    recompute_sigma_terms: bool = False,
    u: np.ndarray | None = None,
    lambda_value: float | None = None,
) -> Phase2ORow:
    raw = _as_mapping(attempt.get("raw_certificate"))
    strict = _as_mapping(attempt.get("strict_ledger"))
    family = HarmonicFamily()
    rho = _finite_float(raw.get("rho"), _GOLDEN_RHO) or _GOLDEN_RHO
    K = _finite_float(raw.get("K"), input_summary.K_mid) or input_summary.K_mid
    N = int(_finite_float(raw.get("N"), input_summary.N) or input_summary.N)
    oversample = int(_as_mapping(attempt.get("config")).get("oversample_factor") or input_summary.oversample_factor or 32)
    source_r = _finite_float(strict.get("radius_r"), input_summary.source_radius) or input_summary.source_radius
    radius = float(source_r) * float(radius_multiplier)
    sigma_val = float(input_summary.source_sigma if sigma is None else sigma)
    finite_eta = _finite_float(raw.get("finite_eta"), 0.0) or 0.0
    finite_B = _finite_float(raw.get("finite_B_norm"), float("inf")) or float("inf")
    fallback_L = _finite_float(raw.get("finite_lipschitz_bound"), float("inf")) or float("inf")
    inv_bound = _finite_float(raw.get("cohomological_inverse_bound"))
    strip_width = _finite_float(raw.get("strip_width_proxy"))
    tail_start = max(1, N // 2 + 1)

    L, finite_nl, linear_Z, q, finite_margin = _finite_radius_terms(
        u=u,
        K=float(K),
        family=family,
        radius=float(radius),
        finite_eta=float(finite_eta),
        finite_B_norm=float(finite_B),
        fallback_lipschitz=float(fallback_L),
    )

    if recompute_sigma_terms:
        if u is None or lambda_value is None:
            Y = float("inf")
            weighted_residual_l1 = float("inf")
            residual_truncation = 0
            tail_response = float("inf")
            tail_l1 = None
            tail_usable = False
            tail_components: dict[str, Any] = {"reason": "source_samples_or_lambda_missing"}
        else:
            Y, weighted_residual_l1, residual_truncation = _modewise_inverse_applied_residual_from_samples(
                u=u,
                rho=float(rho),
                K=float(K),
                family=family,
                lambda_value=float(lambda_value),
                sigma=float(sigma_val),
                oversample_factor=int(oversample),
            )
            coeffs = spectral_coefficients_from_samples(np.asarray(u, dtype=float))
            tail = certify_fourier_tail_bound_from_coeffs(
                coeffs,
                sigma_used=float(sigma_val),
                strip_width_proxy=strip_width,
                tail_start_mode=tail_start,
            )
            tail_l1 = None if tail.tail_l1 is None else float(tail.tail_l1)
            tail_usable = bool(tail.theorem_usable)
            inv = float(inv_bound) if inv_bound is not None else float(build_modewise_divisor_ledger(max(1, N // 2), rho=float(rho), sigma=0.0).max_inverse_multiplier)
            tail_response = float("inf") if tail_l1 is None else float(tail_l1 * inv)
            tail_components = tail.to_dict()
            tail_components.update({"weighted_residual_l1": float(weighted_residual_l1), "residual_truncation": int(residual_truncation), "inverse_bound_used": float(inv)})
        tail_model = "strict_cauchy_tail_sigma_override"
        sigma_source = "phase2o_true_working_sigma_override"
    else:
        Y = _finite_float(strict.get("residual_Y"), input_summary.source_residual_Y) or input_summary.source_residual_Y
        tail_response, tail_l1, tail_components = _tail_response_from_strict(raw, strict)
        tail_usable = math.isfinite(tail_response)
        tail_model = "source_phase2e_tail"
        sigma_source = "source_phase2e_sigma"

    nonlinear_guard = 0.0
    if math.isfinite(finite_margin) and finite_margin > 0.0:
        nonlinear_guard = max(0.0, float(config.nonlinear_margin_fraction) * float(finite_margin))
    tail_T = float(tail_response + nonlinear_guard)
    lhs = float(Y + finite_nl + tail_T)
    margin = float(radius - lhs - abs(config.outward_rounding_tolerance))
    required = abs(float(config.outward_rounding_tolerance)) * max(1.0, float(config.theorem_margin_safety_factor))
    allowable_tail = float(radius - finite_nl - Y)
    needed_tail_factor = None if tail_T <= 0.0 or not math.isfinite(tail_T) else float(allowable_tail / tail_T)
    needed_radius = None if (1.0 - linear_Z) <= 0.0 else float((tail_T + Y) / (1.0 - linear_Z))

    failures: list[str] = []
    if not (math.isfinite(radius) and radius > 0.0):
        failures.append("radius_missing_or_nonpositive")
    if not (math.isfinite(Y)):
        failures.append("residual_Y_not_finite")
    if not (math.isfinite(finite_nl) and math.isfinite(linear_Z)):
        failures.append("finite_nonlinear_term_not_finite")
    if not (math.isfinite(q) and q < 1.0):
        failures.append("finite_contraction_q_not_below_one")
    if not (math.isfinite(finite_margin) and finite_margin > 0.0):
        failures.append("finite_radius_polynomial_margin_nonpositive")
    if not (math.isfinite(tail_T)):
        failures.append("tail_bound_T_not_finite")
    if recompute_sigma_terms and not tail_usable:
        failures.append("sigma_override_tail_not_theorem_usable")
    if recompute_sigma_terms and sigma_val < float(config.min_theorem_sigma):
        failures.append("sigma_below_min_theorem_sigma")
    if margin <= required:
        failures.append("analytic_radii_margin_not_safely_positive")

    theorem_eligible = bool((not recompute_sigma_terms) or (sigma_val >= float(config.min_theorem_sigma) and tail_usable))
    theorem_ready = bool(theorem_eligible and not failures)
    return Phase2ORow(
        model_name=str(model_name),
        tail_model=tail_model,
        theorem_eligible=theorem_eligible,
        theorem_ready=theorem_ready,
        radius_multiplier=float(radius_multiplier),
        radius_r=float(radius),
        sigma=float(sigma_val),
        residual_Y=float(Y),
        finite_nonlinear_term=float(finite_nl),
        linear_Z=float(linear_Z),
        finite_eta=float(finite_eta),
        finite_B_norm=float(finite_B),
        finite_lipschitz_bound=float(L),
        finite_contraction_q=float(q),
        finite_poly_margin=float(finite_margin),
        tail_l1=tail_l1,
        tail_response_bound=float(tail_response),
        nonlinear_guard=float(nonlinear_guard),
        tail_T=float(tail_T),
        radii_lhs=float(lhs),
        radii_margin=float(margin),
        allowable_tail_max=float(allowable_tail),
        needed_tail_factor=needed_tail_factor,
        needed_radius_if_Z_fixed=needed_radius,
        tail_theorem_usable=bool(tail_usable),
        strip_width_proxy=strip_width,
        tail_start_mode=int(tail_start),
        oversample_factor=int(oversample),
        sigma_source=sigma_source,
        failure_reasons=tuple(failures),
        components={
            "tail_components": tail_components,
            "finite_terms": {
                "finite_eta": float(finite_eta),
                "finite_B_norm": float(finite_B),
                "finite_lipschitz_bound": float(L),
                "finite_contraction_q": float(q),
                "finite_poly_margin": float(finite_margin),
            },
        },
        notes=(
            "Strict theorem-eligible source-tail radius scan." if not recompute_sigma_terms
            else "Strict theorem-eligible true working-sigma override; no Newton rerun, same source samples."
        ),
    )


def _diagnostic_high_mode_tail_l1(
    coeffs: np.ndarray,
    *,
    sigma: float,
    tail_start_mode: int,
    band_fraction: float,
    safety_factor: float,
) -> tuple[float, dict[str, Any]]:
    coeffs = np.asarray(coeffs, dtype=complex)
    k = np.abs(spectral_wavenumbers(len(coeffs))).astype(float)
    mags = np.abs(coeffs)
    kmax = float(np.max(k, initial=0.0))
    if kmax <= 0.0:
        return 0.0, {"kmax": 0.0, "band_count": 0}
    band = (k >= float(band_fraction) * kmax) & (k > 0)
    if not np.any(band):
        band = k > 0
    weighted = mags[band] * np.exp(2.0 * math.pi * float(sigma) * k[band])
    envelope = float(np.max(weighted, initial=0.0)) * float(safety_factor)
    ratio = math.exp(-2.0 * math.pi * max(float(sigma), 1.0e-15))
    denom = max(1.0e-15, 1.0 - ratio)
    tail_sup = envelope * math.exp(-2.0 * math.pi * max(float(sigma), 1.0e-15) * int(tail_start_mode))
    tail_l1 = float(2.0 * tail_sup / denom)
    return tail_l1, {
        "band_fraction": float(band_fraction),
        "safety_factor": float(safety_factor),
        "kmax": float(kmax),
        "band_count": int(np.count_nonzero(band)),
        "envelope": float(envelope),
        "ratio": float(ratio),
        "denominator": float(denom),
        "tail_sup": float(tail_sup),
    }


def build_diagnostic_high_mode_row(
    *,
    model_name: str,
    attempt: Mapping[str, Any],
    input_summary: Phase2OInputSummary,
    config: Phase2OScanConfig,
    sigma: float,
    band_fraction: float,
    safety_factor: float,
    u: np.ndarray,
    lambda_value: float,
) -> Phase2ORow:
    base = build_strict_radius_or_sigma_row(
        model_name=model_name,
        attempt=attempt,
        input_summary=input_summary,
        config=config,
        radius_multiplier=1.0,
        sigma=float(sigma),
        recompute_sigma_terms=True,
        u=u,
        lambda_value=lambda_value,
    )
    raw = _as_mapping(attempt.get("raw_certificate"))
    inv_bound = _finite_float(raw.get("cohomological_inverse_bound"), 1.0) or 1.0
    coeffs = spectral_coefficients_from_samples(np.asarray(u, dtype=float))
    tail_l1, comp = _diagnostic_high_mode_tail_l1(
        coeffs,
        sigma=float(sigma),
        tail_start_mode=int(base.tail_start_mode),
        band_fraction=float(band_fraction),
        safety_factor=float(safety_factor),
    )
    tail_response = float(tail_l1 * inv_bound)
    tail_T = float(tail_response + base.nonlinear_guard)
    lhs = float(base.residual_Y + base.finite_nonlinear_term + tail_T)
    margin = float(base.radius_r - lhs - abs(config.outward_rounding_tolerance))
    allowable_tail = float(base.radius_r - base.finite_nonlinear_term - base.residual_Y)
    needed_tail_factor = None if tail_T <= 0.0 or not math.isfinite(tail_T) else float(allowable_tail / tail_T)
    needed_radius = None if (1.0 - base.linear_Z) <= 0.0 else float((tail_T + base.residual_Y) / (1.0 - base.linear_Z))
    failures = list(base.failure_reasons)
    # Replace tail usability/margin failures for diagnostic model.
    failures = [x for x in failures if x not in {"sigma_override_tail_not_theorem_usable", "analytic_radii_margin_not_safely_positive"}]
    if margin <= abs(config.outward_rounding_tolerance) * max(1.0, config.theorem_margin_safety_factor):
        failures.append("diagnostic_margin_not_positive")
    theorem_ready = bool(not failures and margin > 0.0)
    return Phase2ORow(
        model_name=str(model_name),
        tail_model="diagnostic_high_mode_envelope_tail",
        theorem_eligible=False,
        theorem_ready=False,
        radius_multiplier=1.0,
        radius_r=float(base.radius_r),
        sigma=float(sigma),
        residual_Y=float(base.residual_Y),
        finite_nonlinear_term=float(base.finite_nonlinear_term),
        linear_Z=float(base.linear_Z),
        finite_eta=float(base.finite_eta),
        finite_B_norm=float(base.finite_B_norm),
        finite_lipschitz_bound=float(base.finite_lipschitz_bound),
        finite_contraction_q=float(base.finite_contraction_q),
        finite_poly_margin=float(base.finite_poly_margin),
        tail_l1=float(tail_l1),
        tail_response_bound=float(tail_response),
        nonlinear_guard=float(base.nonlinear_guard),
        tail_T=float(tail_T),
        radii_lhs=float(lhs),
        radii_margin=float(margin),
        allowable_tail_max=float(allowable_tail),
        needed_tail_factor=needed_tail_factor,
        needed_radius_if_Z_fixed=needed_radius,
        tail_theorem_usable=False,
        strip_width_proxy=base.strip_width_proxy,
        tail_start_mode=int(base.tail_start_mode),
        oversample_factor=int(base.oversample_factor),
        sigma_source="phase2o_diagnostic_high_mode_envelope",
        failure_reasons=tuple(failures),
        components={"diagnostic_tail_components": comp, "inverse_bound_used": float(inv_bound), "base_sigma_override": base.to_dict()},
        notes="Diagnostic only. This row cannot be promoted without adding/proving the corresponding high-mode envelope lemma.",
    )


def _row_sort_key(row: Phase2ORow) -> tuple[float, float, float, float, float]:
    return (
        1.0 if row.theorem_ready else 0.0,
        1.0 if row.theorem_eligible else 0.0,
        float(row.radii_margin) if math.isfinite(row.radii_margin) else -float("inf"),
        -float(row.tail_T) if math.isfinite(row.tail_T) else -float("inf"),
        -float(row.finite_contraction_q) if math.isfinite(row.finite_contraction_q) else -float("inf"),
    )


def _build_input_summary(attempt: Mapping[str, Any], resolved_path: str, original_path: str) -> Phase2OInputSummary:
    cfg = _as_mapping(attempt.get("config"))
    strict = _as_mapping(attempt.get("strict_ledger"))
    score = _as_mapping(attempt.get("score"))
    raw = _as_mapping(attempt.get("raw_certificate"))
    u, _, src_summary = _extract_source_samples(raw)
    return Phase2OInputSummary(
        resolved_input_path=str(resolved_path),
        original_input_path=str(original_path),
        segment_id=cfg.get("segment_id"),
        K_lo=_finite_float(cfg.get("K_lo")),
        K_hi=_finite_float(cfg.get("K_hi")),
        K_mid=float(_finite_float(cfg.get("K_mid"), _finite_float(raw.get("K"), 0.0)) or 0.0),
        N=int(_finite_float(raw.get("N"), _finite_float(score.get("selected_N"), _finite_float(cfg.get("N"), 0))) or 0),
        oversample_factor=int(cfg.get("oversample_factor") or 0),
        source_sigma=float(_finite_float(strict.get("sigma"), _finite_float(score.get("sigma"), _finite_float(raw.get("sigma_used"), 0.0))) or 0.0),
        source_radius=float(_finite_float(strict.get("radius_r"), _finite_float(score.get("radius_r"), 0.0)) or 0.0),
        source_margin=float(_finite_float(strict.get("radii_margin"), _finite_float(score.get("radii_margin"), -float("inf"))) or -float("inf")),
        source_tail_T=float(_finite_float(strict.get("tail_bound_T"), _finite_float(score.get("tail_T"), float("inf"))) or float("inf")),
        source_residual_Y=float(_finite_float(strict.get("residual_Y"), _finite_float(score.get("residual_Y"), float("inf"))) or float("inf")),
        source_linear_Z=float(_finite_float(strict.get("linear_defect_Z"), _finite_float(score.get("linear_Z"), float("inf"))) or float("inf")),
        has_raw_certificate=bool(raw),
        has_source_samples=bool(src_summary.get("has_u")),
    )


def build_phase2o_report(input_path: str | Path, config: Phase2OScanConfig | None = None) -> Phase2OReport:
    original_path = str(input_path)
    attempt, resolved_path = resolve_phase2n_attempt(input_path)
    cfg = config or Phase2OScanConfig(input_path=original_path)
    input_summary = _build_input_summary(attempt, resolved_path, original_path)
    strict_source = _source_strict_row(attempt, input_summary, cfg)
    raw = _as_mapping(attempt.get("raw_certificate"))
    u, lam, seed_summary = _extract_source_samples(raw)

    rows: list[Phase2ORow] = [strict_source]

    # 1. Strict source-tail radius scan.  This is theorem-eligible, but usually
    # demonstrates that the finite contraction radius cannot be inflated enough.
    for mult in cfg.radius_multipliers:
        if abs(float(mult) - 1.0) < 1e-15:
            continue
        rows.append(build_strict_radius_or_sigma_row(
            model_name=f"strict_source_tail_radius_x{float(mult):g}",
            attempt=attempt,
            input_summary=input_summary,
            config=cfg,
            radius_multiplier=float(mult),
            sigma=input_summary.source_sigma,
            recompute_sigma_terms=False,
            u=u,
            lambda_value=lam,
        ))

    # 2. True working-sigma override at the source radius.  This is theorem-
    # eligible when sigma is positive and the Cauchy tail is usable.
    if u is not None and lam is not None:
        for sig in cfg.sigma_values:
            rows.append(build_strict_radius_or_sigma_row(
                model_name=f"strict_sigma_override_sg{float(sig):.3e}",
                attempt=attempt,
                input_summary=input_summary,
                config=cfg,
                radius_multiplier=1.0,
                sigma=float(sig),
                recompute_sigma_terms=True,
                u=u,
                lambda_value=lam,
            ))

        # 3. Diagnostic high-mode-envelope tail.  Never theorem-eligible.
        for sig in cfg.sigma_values:
            for band in cfg.tail_band_fractions:
                for safety in cfg.tail_safety_factors:
                    rows.append(build_diagnostic_high_mode_row(
                        model_name=f"diag_highmode_sg{float(sig):.3e}_b{float(band):.2f}_sf{float(safety):g}",
                        attempt=attempt,
                        input_summary=input_summary,
                        config=cfg,
                        sigma=float(sig),
                        band_fraction=float(band),
                        safety_factor=float(safety),
                        u=u,
                        lambda_value=lam,
                    ))

    rows.sort(key=_row_sort_key, reverse=True)
    theorem_eligible_rows = [r for r in rows if r.theorem_eligible]
    theorem_ready_rows = [r for r in theorem_eligible_rows if r.theorem_ready]
    diagnostic_ready_rows = [r for r in rows if (not r.theorem_eligible) and r.radii_margin > 0.0 and not r.failure_reasons]
    best_theorem = theorem_eligible_rows[0].to_dict() if theorem_eligible_rows else None
    best_diag = max((r for r in rows if not r.theorem_eligible), key=_row_sort_key).to_dict() if any(not r.theorem_eligible for r in rows) else None

    if theorem_ready_rows:
        status = "phase2o-theorem-ready-tail-radius-closure"
        conclusion = {
            "closed": True,
            "recommended_next_step": "export_phase2o_candidate_and_merge_this_segment_into_the_collar_chain",
            "message": "A theorem-eligible Phase-2O row has positive outward-rounded margin.",
        }
    else:
        status = "phase2o-diagnostic-tail-radius-not-closed"
        best_eligible = theorem_eligible_rows[0] if theorem_eligible_rows else strict_source
        radius_blocked = any("finite_contraction_q_not_below_one" in r.failure_reasons for r in rows if r.tail_model == "source_phase2e_tail")
        conclusion = {
            "closed": False,
            "recommended_next_step": "inspect_best_diagnostic_tail_rows_then_implement_a_sharper_tail_lemma_or_change_the_lower_norm",
            "message": "No theorem-eligible tail/radius row closed.  The report identifies whether radius inflation is blocked by finite contraction and whether diagnostic tail models would close.",
            "best_eligible_margin": float(best_eligible.radii_margin),
            "best_eligible_tail_T": float(best_eligible.tail_T),
            "best_eligible_allowable_tail_max": float(best_eligible.allowable_tail_max),
            "radius_inflation_blocked_by_finite_contraction": bool(radius_blocked),
            "source_samples": seed_summary,
        }

    return Phase2OReport(
        schema="phase2o_tail_radius_scan_report_v1",
        status=status,
        config=cfg,
        input_summary=input_summary,
        strict_source_row=strict_source,
        theorem_ready_count=len(theorem_ready_rows),
        theorem_eligible_count=len(theorem_eligible_rows),
        diagnostic_ready_count=len(diagnostic_ready_rows),
        best_theorem_eligible=best_theorem,
        best_diagnostic=best_diag,
        conclusion=conclusion,
        rows=tuple(rows),
        raw_input_attempt=dict(attempt),
    )


def write_phase2o_report(report: Phase2OReport, out_path: str | Path, *, include_raw_input: bool = False) -> None:
    atomic_write_json(out_path, report.to_dict(include_raw_input=include_raw_input))


def write_phase2o_csv(report: Phase2OReport, csv_path: str | Path) -> None:
    csv_path = Path(csv_path)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "model_name", "tail_model", "theorem_eligible", "theorem_ready", "radius_multiplier", "radius_r", "sigma",
        "radii_margin", "residual_Y", "finite_nonlinear_term", "linear_Z", "finite_contraction_q", "finite_poly_margin",
        "tail_l1", "tail_response_bound", "nonlinear_guard", "tail_T", "allowable_tail_max", "needed_tail_factor",
        "needed_radius_if_Z_fixed", "tail_theorem_usable", "strip_width_proxy", "tail_start_mode", "oversample_factor",
        "sigma_source", "failure_reasons", "notes",
    ]
    with csv_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in report.rows:
            d = row.to_dict()
            d["failure_reasons"] = ";".join(d.get("failure_reasons", []))
            writer.writerow({k: d.get(k) for k in fields})


def build_phase2o_candidate(report: Phase2OReport, *, source_artifact: str, allow_experimental: bool = False) -> dict[str, Any]:
    ready_rows = [r for r in report.rows if r.theorem_eligible and r.theorem_ready]
    selected: Phase2ORow | None = ready_rows[0] if ready_rows else None
    experimental = False
    if selected is None and allow_experimental:
        diagnostic_candidates = [r for r in report.rows if (not r.theorem_eligible) and r.radii_margin > 0.0]
        if diagnostic_candidates:
            selected = max(diagnostic_candidates, key=_row_sort_key)
            experimental = True
    if selected is None:
        selected = next((r for r in report.rows if r.theorem_eligible), report.strict_source_row)

    inp = report.input_summary
    theorem_facing = bool(selected.theorem_eligible and selected.theorem_ready and not experimental)
    row = {
        "segment_id": inp.segment_id,
        "K_lo": inp.K_lo,
        "K_hi": inp.K_hi,
        "K_mid": inp.K_mid,
        "rho": _GOLDEN_RHO,
        "N": inp.N,
        "sigma": selected.sigma,
        "oversample_factor": selected.oversample_factor,
        "norm_name": "phase2o-tail-radius-radii-polynomial",
        "residual_Y": selected.residual_Y,
        "linear_defect_Z": selected.linear_Z,
        "linear_Z": selected.linear_Z,
        "tail_bound_T": selected.tail_T,
        "tail_T": selected.tail_T,
        "tail_response_bound": selected.tail_response_bound,
        "nonlinear_guard": selected.nonlinear_guard,
        "finite_nonlinear_term": selected.finite_nonlinear_term,
        "finite_contraction_q": selected.finite_contraction_q,
        "finite_poly_margin": selected.finite_poly_margin,
        "allowable_tail_max": selected.allowable_tail_max,
        "radius_r": selected.radius_r,
        "radii_margin": selected.radii_margin,
        "small_divisor_source": "phase2o-recomputed-tail-radius-ledger",
        "source_module": "kam_theorem_suite.audit.lower_anchor_phase2o_tail_radius",
        "source_artifact": str(source_artifact),
        "certified": theorem_facing,
        "finite_dimensional_only": bool(not theorem_facing),
        "closure_level": "phase2o_tail_radius_closure" if theorem_facing else "phase2o_tail_radius_not_closed",
        "theorem_ready": theorem_facing,
        "analytic_probe_attempted": True,
        "analytic_theorem_status": "phase2o-tail-radius-closed" if theorem_facing else "phase2o-tail-radius-diagnostic",
        "analytic_theorem_margin": selected.radii_margin,
        "failure_reasons": list(selected.failure_reasons),
        "phase2o_ledger": selected.to_dict(),
        "strict_source_ledger": report.strict_source_row.to_dict(),
    }
    candidate_payload = {
        "schema": "phase2o_single_segment_candidate_v1",
        "theorem_facing": theorem_facing,
        "diagnostic_only": bool(not theorem_facing),
        "promotion_allowed": theorem_facing,
        "experimental_selected": bool(experimental),
        "closure_level": "phase2o_tail_radius_closure" if theorem_facing else "phase2o_tail_radius_not_closed",
        "source": "Phase-2O tail/radius closure candidate",
        "failure_fields": [] if theorem_facing else ["phase2o_tail_radius_not_theorem_ready"],
        "notes": (
            "One-segment theorem-facing candidate; merge into a contiguous collar only after neighboring overlaps are verified."
            if theorem_facing else
            "Diagnostic one-segment candidate. Do not promote unless a theorem-eligible row closes."
        ),
        "input_summary": report.input_summary.to_dict(),
        "selected_phase2o_row": selected.to_dict(),
        "rows": [selected.to_dict()],
        "anchor_segments": [row],
    }
    if attach_raw_validation_payload_to_candidate is not None:
        try:
            candidate_payload = attach_raw_validation_payload_to_candidate(
                candidate_payload,
                phase2n_attempt=report.raw_input_attempt,
                selected_row=selected.to_dict(),
                input_summary=report.input_summary.to_dict(),
                source_artifact=str(source_artifact),
                stage="phase2o",
            )
        except Exception as exc:  # fail-open for diagnostics, fail-closed for theorem status
            candidate_payload["phase2aa_stage1b_export"] = {
                "enabled": False,
                "error": repr(exc),
                "does_not_change_theorem_facing_status": True,
            }
    return candidate_payload


def print_compact_report(report: Phase2OReport) -> str:
    lines = []
    lines.append(json.dumps({
        "status": report.status,
        "theorem_ready_count": report.theorem_ready_count,
        "theorem_eligible_count": report.theorem_eligible_count,
        "diagnostic_ready_count": report.diagnostic_ready_count,
        "best_theorem_eligible": None if report.best_theorem_eligible is None else {
            k: report.best_theorem_eligible.get(k) for k in [
                "model_name", "tail_model", "radii_margin", "sigma", "radius_multiplier", "tail_T", "allowable_tail_max", "finite_contraction_q", "failure_reasons"
            ]
        },
        "best_diagnostic": None if report.best_diagnostic is None else {
            k: report.best_diagnostic.get(k) for k in [
                "model_name", "tail_model", "radii_margin", "sigma", "tail_T", "allowable_tail_max", "failure_reasons"
            ]
        },
        "conclusion": report.conclusion,
    }, indent=2))
    return "\n".join(lines)


__all__ = [
    "Phase2OScanConfig",
    "Phase2OInputSummary",
    "Phase2ORow",
    "Phase2OReport",
    "build_phase2o_candidate",
    "build_phase2o_report",
    "parse_float_list",
    "print_compact_report",
    "resolve_phase2n_attempt",
    "write_phase2o_csv",
    "write_phase2o_report",
]

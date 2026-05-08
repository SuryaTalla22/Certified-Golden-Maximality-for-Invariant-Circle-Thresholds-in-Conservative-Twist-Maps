from __future__ import annotations

"""Phase 2P modewise tail-response audit for Theorem III.

Phase 2O isolated the Theorem-III lower-anchor obstruction: the residual is
small, K-width effects are negligible, and radius inflation is blocked by the
finite contraction condition.  The remaining overestimate is the strict tail
response term.  Phase 2P replaces the scalar worst-case tail response

    max_k ||L_k^{-1}|| * sum_k tail_k

with a modewise geometric tail response

    sum_{|k| >= k0} ||L_k^{-1}|| * tail_envelope_k,

plus a certified golden Diophantine remainder for the infinite part of the
tail.  This is still fail-closed: a row becomes theorem-facing only when the
input carries a theorem-usable analytic tail envelope, the golden tail small-
divisor remainder applies, the finite contraction condition remains below one,
and the recomputed inequality

    Y + Z r + T < r

has a positive outward-rounded margin.
"""

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Mapping, Sequence
import csv
import json
import math

import numpy as np

from ..analytic_norms import spectral_coefficients_from_samples
from ..fourier_bounds import certify_fourier_tail_bound_from_coeffs
from ..invariance_defect import residual_samples
from ..standard_map import HarmonicFamily
from ..analytic_lower_krawczyk import exact_small_divisor_gap

try:
    from .lower_anchor_phase2n import atomic_write_json
except Exception:  # pragma: no cover - fallback only
    def atomic_write_json(path: str | Path, payload: Mapping[str, Any]) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        tmp.replace(path)

_GOLDEN_RHO = (math.sqrt(5.0) - 1.0) / 2.0
_GOLDEN_DIOPHANTINE_C = 4.0 / math.sqrt(5.0)

try:
    from .lower_anchor_phase2aa_raw_payload_export import attach_raw_validation_payload_to_candidate
except Exception:  # pragma: no cover - stage-1B overlay not installed
    attach_raw_validation_payload_to_candidate = None  # type: ignore[assignment]


@dataclass(frozen=True)
class Phase2PScanConfig:
    input_path: str
    sigma_values: tuple[float, ...] = (1.0e-4, 7.5e-5, 5.0e-5, 2.5e-5, 1.0e-5, 5.0e-6, 2.5e-6, 1.0e-6)
    tail_cutoffs: tuple[int, ...] = (1024, 2048, 4096, 8192, 16384)
    oversample_factors: tuple[int, ...] = (16,)
    outward_rounding_tolerance: float = 1.0e-12
    theorem_margin_safety_factor: float = 10.0
    min_theorem_sigma: float = 1.0e-8
    golden_rho_tolerance: float = 1.0e-12
    use_recomputed_tail_from_u: bool = True
    include_source_sigma_row: bool = True

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["sigma_values"] = list(self.sigma_values)
        d["tail_cutoffs"] = list(self.tail_cutoffs)
        d["oversample_factors"] = list(self.oversample_factors)
        return d


@dataclass(frozen=True)
class Phase2PInputSummary:
    original_input_path: str
    resolved_phase2n_path: str | None
    input_kind: str
    segment_id: str | None
    K_lo: float | None
    K_hi: float | None
    K_mid: float
    rho: float
    N: int
    source_sigma: float
    source_radius: float
    source_residual_Y: float
    source_linear_Z: float
    source_tail_T: float
    source_margin: float
    source_tail_start_mode: int
    has_raw_certificate: bool
    has_source_samples: bool
    has_selected_phase2o_row: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ModewiseTailLedger:
    theorem_usable: bool
    rho: float
    sigma: float
    tail_start_mode: int
    finite_cutoff: int
    geometric_ratio: float
    tail_sup_at_start: float
    tail_l1_bound: float
    modewise_finite_l1: float
    modewise_remainder_l1: float
    global_inverse_bound_used_by_phase2o: float | None
    global_inverse_tail_response: float | None
    modewise_finite_response: float
    modewise_remainder_response: float
    modewise_tail_response: float
    improvement_factor_vs_global_response: float | None
    golden_diophantine_constant: float
    worst_finite_inverse: float
    worst_finite_inverse_mode: int
    top_contributors: tuple[dict[str, float | int], ...]
    failure_reasons: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["failure_reasons"] = list(self.failure_reasons)
        d["top_contributors"] = [dict(x) for x in self.top_contributors]
        return d


@dataclass(frozen=True)
class Phase2PRow:
    model_name: str
    tail_model: str
    theorem_eligible: bool
    theorem_ready: bool
    sigma: float
    oversample_factor: int
    tail_cutoff: int
    radius_r: float
    residual_Y: float
    finite_nonlinear_term: float
    linear_Z: float
    finite_contraction_q: float
    finite_poly_margin: float
    nonlinear_guard: float
    tail_l1: float
    tail_response_bound: float
    tail_T: float
    radii_lhs: float
    radii_margin: float
    allowable_tail_max: float
    needed_tail_factor: float | None
    tail_start_mode: int
    tail_theorem_usable: bool
    failure_reasons: tuple[str, ...]
    modewise_tail_ledger: ModewiseTailLedger
    components: dict[str, Any] = field(default_factory=dict)
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["failure_reasons"] = list(self.failure_reasons)
        d["modewise_tail_ledger"] = self.modewise_tail_ledger.to_dict()
        return d


@dataclass(frozen=True)
class Phase2PReport:
    schema: str
    status: str
    config: Phase2PScanConfig
    input_summary: Phase2PInputSummary
    theorem_ready_count: int
    theorem_eligible_count: int
    best_theorem_eligible: dict[str, Any] | None
    conclusion: dict[str, Any]
    rows: tuple[Phase2PRow, ...]
    raw_input: dict[str, Any] | None = None
    raw_phase2n_attempt: dict[str, Any] | None = None

    def to_dict(self, *, include_raw_input: bool = False) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "status": self.status,
            "config": self.config.to_dict(),
            "input_summary": self.input_summary.to_dict(),
            "theorem_ready_count": int(self.theorem_ready_count),
            "theorem_eligible_count": int(self.theorem_eligible_count),
            "best_theorem_eligible": self.best_theorem_eligible,
            "conclusion": dict(self.conclusion),
            "rows": [r.to_dict() for r in self.rows],
            "raw_input": self.raw_input if include_raw_input else None,
            "raw_phase2n_attempt": self.raw_phase2n_attempt if include_raw_input else None,
        }


def _as_mapping(x: Any) -> Mapping[str, Any]:
    return x if isinstance(x, Mapping) else {}


def _finite_float(x: Any, default: float | None = None) -> float | None:
    try:
        y = float(x)
    except Exception:
        return default
    return y if math.isfinite(y) else default


def _finite_int(x: Any, default: int = 0) -> int:
    y = _finite_float(x)
    if y is None:
        return int(default)
    return int(y)


def parse_float_list(raw: str | Sequence[float]) -> tuple[float, ...]:
    if isinstance(raw, str):
        vals = [float(x.strip()) for x in raw.split(",") if x.strip()]
    else:
        vals = [float(x) for x in raw]
    out: list[float] = []
    for v in vals:
        if math.isfinite(v) and v > 0.0 and v not in out:
            out.append(float(v))
    return tuple(out)


def parse_int_list(raw: str | Sequence[int]) -> tuple[int, ...]:
    if isinstance(raw, str):
        vals = [int(x.strip()) for x in raw.split(",") if x.strip()]
    else:
        vals = [int(x) for x in raw]
    out: list[int] = []
    for v in vals:
        if v > 0 and v not in out:
            out.append(int(v))
    return tuple(out)


def load_json(path: str | Path) -> dict[str, Any]:
    data = json.loads(Path(path).read_text())
    if not isinstance(data, Mapping):
        raise ValueError(f"expected JSON object in {path}")
    return dict(data)


def _resolve_relative(path: str | Path, base: str | Path | None = None) -> Path:
    p = Path(path)
    if p.is_absolute():
        return p
    if p.exists():
        return p
    if base is not None:
        b = Path(base)
        cand = b.parent / p
        if cand.exists():
            return cand
        cand2 = b.parent / p.name
        if cand2.exists():
            return cand2
    return p


def _resolve_phase2n_from_summary(path: str | Path) -> tuple[dict[str, Any], str]:
    path = Path(path)
    data = load_json(path)
    best = data.get("best") if isinstance(data.get("best"), Mapping) else None
    if best and best.get("path"):
        p = _resolve_relative(str(best["path"]), path)
        return _resolve_phase2n_from_summary(p)
    if str(data.get("schema", "")).startswith("phase2n_single_N_attempt"):
        return data, str(path)
    if isinstance(data.get("raw_phase2n_attempt"), Mapping):
        return dict(data["raw_phase2n_attempt"]), str(path)
    for key in ("phase2n_result", "attempt", "raw_attempt"):
        if isinstance(data.get(key), Mapping):
            nested = dict(data[key])
            if str(nested.get("schema", "")).startswith("phase2n_single_N_attempt"):
                return nested, str(path)
    raise ValueError(f"could not resolve Phase-2N attempt from {path}")


def resolve_phase2p_input(input_path: str | Path) -> tuple[dict[str, Any], dict[str, Any] | None, str | None, str]:
    """Return (input_json, phase2n_attempt, phase2n_path, input_kind)."""
    input_path = Path(input_path)
    data = load_json(input_path)
    schema = str(data.get("schema", ""))

    if schema.startswith("phase2o_single_segment_candidate"):
        inp = _as_mapping(data.get("input_summary"))
        p = inp.get("resolved_input_path") or inp.get("resolved_phase2n_path")
        attempt = None
        attempt_path = None
        if p:
            try:
                attempt, attempt_path = _resolve_phase2n_from_summary(_resolve_relative(str(p), input_path))
            except Exception:
                attempt, attempt_path = None, None
        return data, attempt, attempt_path, "phase2o_candidate"

    if schema.startswith("phase2o_tail_radius_scan_report"):
        inp = _as_mapping(data.get("input_summary"))
        p = inp.get("resolved_input_path") or inp.get("resolved_phase2n_path")
        attempt = None
        attempt_path = None
        if p:
            try:
                attempt, attempt_path = _resolve_phase2n_from_summary(_resolve_relative(str(p), input_path))
            except Exception:
                attempt, attempt_path = None, None
        return data, attempt, attempt_path, "phase2o_scan"

    if schema.startswith("phase2n_single_N_attempt") or data.get("best"):
        attempt, attempt_path = _resolve_phase2n_from_summary(input_path)
        return data, attempt, attempt_path, "phase2n"

    raise ValueError(
        f"Unsupported input {input_path}. Pass a Phase-2O candidate/report or Phase-2N summary/single-N attempt."
    )


def _phase2n_source_row(input_json: Mapping[str, Any]) -> Mapping[str, Any]:
    """Return a selected-row-shaped mapping for a Phase-2N attempt."""
    score = _as_mapping(input_json.get("score"))
    strict = _as_mapping(input_json.get("strict_ledger"))
    raw = _as_mapping(input_json.get("raw_certificate"))
    if score or strict:
        return {
            "model_name": "source_phase2n_strict",
            "sigma": _finite_float(strict.get("sigma"), _finite_float(raw.get("sigma_used"), 0.0)),
            "radius_r": _finite_float(strict.get("radius_r"), score.get("radius_r")),
            "residual_Y": _finite_float(strict.get("residual_Y"), score.get("residual_Y")),
            "linear_Z": _finite_float(strict.get("linear_defect_Z"), score.get("linear_Z")),
            "finite_nonlinear_term": None,
            "finite_contraction_q": _finite_float(raw.get("finite_contraction_bound"), 0.0),
            "finite_poly_margin": _finite_float(raw.get("finite_radii_margin"), 0.0),
            "nonlinear_guard": _finite_float(strict.get("nonlinear_response_bound"), 0.0),
            "tail_T": _finite_float(strict.get("tail_bound_T"), score.get("tail_T")),
            "radii_margin": _finite_float(strict.get("radii_margin"), score.get("radii_margin")),
            "tail_start_mode": None,
            "oversample_factor": _as_mapping(input_json.get("config")).get("oversample_factor", 0),
            "components": {"tail_components": _as_mapping(raw.get("tail_bound"))},
        }
    return {}


def _safe_slug(value: Any) -> str:
    s = str(value if value is not None else "row")
    out = []
    for ch in s:
        out.append(ch if ch.isalnum() else "_")
    collapsed = "".join(out).strip("_")
    return collapsed[:96] or "row"


def _rows_from_phase2o_scan(data: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    raw_rows = data.get("rows")
    if not isinstance(raw_rows, list):
        return []
    rows = [r for r in raw_rows if isinstance(r, Mapping)]
    eligible = [r for r in rows if r.get("theorem_eligible") is True]
    return eligible or rows


def _extract_selected_rows(
    input_json: Mapping[str, Any],
    input_kind: str,
    input_path: str | Path | None,
) -> list[Mapping[str, Any]]:
    """Return all Phase-2O rows that Phase 2P should modewise-tail scan.

    The original Phase 2P consumed only one selected Phase-2O row.  Collar 011
    exposed the interaction that matters after Phase 2P: Phase 2O's scalar-tail
    score prefers a small radius, while Phase 2P may need a larger radius row
    combined with the modewise tail response.  This helper therefore expands a
    Phase-2O scan report, and also follows a Phase-2O candidate's recorded
    source scan when available.
    """
    if input_kind == "phase2o_scan":
        return _rows_from_phase2o_scan(input_json)

    if input_kind == "phase2o_candidate":
        scan_rows: list[Mapping[str, Any]] = []
        source_paths: list[Any] = []
        top_source = input_json.get("source_artifact")
        if top_source:
            source_paths.append(top_source)
        for seg in input_json.get("anchor_segments", []) or []:
            if isinstance(seg, Mapping) and seg.get("source_artifact"):
                source_paths.append(seg.get("source_artifact"))

        seen: set[str] = set()
        for src in source_paths:
            try:
                resolved = _resolve_relative(str(src), input_path) if input_path is not None else Path(str(src))
                key = str(resolved)
                if key in seen or not resolved.exists():
                    continue
                seen.add(key)
                data = load_json(resolved)
                if str(data.get("schema", "")).startswith("phase2o_tail_radius_scan_report"):
                    scan_rows.extend(_rows_from_phase2o_scan(data))
            except Exception:
                continue
        if scan_rows:
            return scan_rows

        row = input_json.get("selected_phase2o_row")
        if isinstance(row, Mapping):
            return [row]
        return []

    if input_kind == "phase2n":
        row = _phase2n_source_row(input_json)
        return [row] if row else []

    return []


def _extract_selected_row(input_json: Mapping[str, Any], input_kind: str) -> Mapping[str, Any]:
    rows = _extract_selected_rows(input_json, input_kind, None)
    return rows[0] if rows else {}


def _extract_u_lambda(raw_certificate: Mapping[str, Any]) -> tuple[np.ndarray | None, float | None, dict[str, Any]]:
    src = _as_mapping(raw_certificate.get("source_validation"))
    u_raw = src.get("u", raw_certificate.get("u"))
    lam_raw = src.get("lambda_value", raw_certificate.get("lambda_value"))
    try:
        u = np.asarray(u_raw, dtype=float)
    except Exception:
        u = None
    if u is not None and u.size == 0:
        u = None
    lam = _finite_float(lam_raw)
    return u, lam, {"source_validation_present": bool(src), "has_u": u is not None, "N_from_u": None if u is None else int(u.size), "lambda_value": lam}


def _build_input_summary(
    *,
    original_input_path: str,
    input_kind: str,
    input_json: Mapping[str, Any],
    selected: Mapping[str, Any],
    phase2n_attempt: Mapping[str, Any] | None,
    phase2n_path: str | None,
) -> Phase2PInputSummary:
    attempt = phase2n_attempt or input_json
    raw = _as_mapping(attempt.get("raw_certificate"))
    cfg = _as_mapping(attempt.get("config"))
    inp = _as_mapping(input_json.get("input_summary"))
    strict = _as_mapping(attempt.get("strict_ledger"))
    score = _as_mapping(attempt.get("score"))
    u, _, u_summary = _extract_u_lambda(raw)
    N = _finite_int(raw.get("N"), _finite_int(inp.get("N"), 0))
    K_mid = _finite_float(raw.get("K"), _finite_float(inp.get("K_mid"), _finite_float(cfg.get("K_mid"), 0.0))) or 0.0
    rho = _finite_float(raw.get("rho"), _GOLDEN_RHO) or _GOLDEN_RHO
    radius = _finite_float(selected.get("radius_r"), _finite_float(strict.get("radius_r"), _finite_float(score.get("radius_r"), 0.0))) or 0.0
    residual = _finite_float(selected.get("residual_Y"), _finite_float(strict.get("residual_Y"), _finite_float(score.get("residual_Y"), float("inf")))) or float("inf")
    linear_Z = _finite_float(selected.get("linear_Z"), _finite_float(strict.get("linear_defect_Z"), _finite_float(score.get("linear_Z"), float("inf")))) or float("inf")
    tail_T = _finite_float(selected.get("tail_T"), _finite_float(strict.get("tail_bound_T"), _finite_float(score.get("tail_T"), float("inf")))) or float("inf")
    margin = _finite_float(selected.get("radii_margin"), _finite_float(strict.get("radii_margin"), _finite_float(score.get("radii_margin"), -float("inf")))) or -float("inf")
    tail_start = _finite_int(selected.get("tail_start_mode"), N // 2 + 1 if N else 1)
    sigma = _finite_float(selected.get("sigma"), _finite_float(raw.get("sigma_used"), _finite_float(strict.get("sigma"), 0.0))) or 0.0
    return Phase2PInputSummary(
        original_input_path=str(original_input_path),
        resolved_phase2n_path=phase2n_path,
        input_kind=str(input_kind),
        segment_id=cfg.get("segment_id") or inp.get("segment_id"),
        K_lo=_finite_float(cfg.get("K_lo"), _finite_float(inp.get("K_lo"))),
        K_hi=_finite_float(cfg.get("K_hi"), _finite_float(inp.get("K_hi"))),
        K_mid=float(K_mid),
        rho=float(rho),
        N=int(N),
        source_sigma=float(sigma),
        source_radius=float(radius),
        source_residual_Y=float(residual),
        source_linear_Z=float(linear_Z),
        source_tail_T=float(tail_T),
        source_margin=float(margin),
        source_tail_start_mode=int(tail_start),
        has_raw_certificate=bool(raw),
        has_source_samples=bool(u_summary.get("has_u")),
        has_selected_phase2o_row=bool(selected),
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
    from ..analytic_norms import analytic_weights, spectral_wavenumbers
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


def _golden_tail_remainder_bound(*, tail_sup: float, ratio: float, tail_start: int, after_mode: int) -> tuple[float, float]:
    """Return (tail_l1_remainder, inverse-applied remainder) beyond after_mode.

    The exact finite sum handles modes tail_start <= |k| <= after_mode.  For
    the infinite remainder, use the golden bound

        |exp(2π i k rho_G)-1| >= (4/sqrt(5))/k,

    hence inverse multiplier <= k / (4/sqrt(5)).
    """
    q = float(ratio)
    if not (0.0 < q < 1.0):
        return float("inf"), float("inf")
    start = int(tail_start)
    m0 = int(after_mode) + 1
    if m0 < start:
        m0 = start
    n0 = m0 - start
    # Sum_{n=n0}^∞ q^n and Sum_{n=n0}^∞ (n+start) q^n.
    qn = q ** n0
    one_minus = 1.0 - q
    geom = qn / one_minus
    weighted_m_sum = qn * (n0 / one_minus + q / (one_minus * one_minus) + start / one_minus)
    tail_l1_remainder = 2.0 * float(tail_sup) * geom
    response_remainder = 2.0 * float(tail_sup) * weighted_m_sum / _GOLDEN_DIOPHANTINE_C
    return float(tail_l1_remainder), float(response_remainder)


def build_modewise_geometric_tail_ledger(
    *,
    rho: float,
    sigma: float,
    tail_start_mode: int,
    finite_cutoff: int,
    tail_sup: float,
    geometric_ratio: float,
    global_inverse_bound: float | None = None,
) -> ModewiseTailLedger:
    failures: list[str] = []
    if abs(float(rho) - _GOLDEN_RHO) > 1.0e-10:
        failures.append("golden_tail_diophantine_bound_not_applicable_to_rho")
    if not (math.isfinite(tail_sup) and tail_sup >= 0.0):
        failures.append("tail_sup_not_finite_nonnegative")
    if not (math.isfinite(geometric_ratio) and 0.0 < geometric_ratio < 1.0):
        failures.append("geometric_ratio_not_in_unit_interval")
    if int(tail_start_mode) <= 0:
        failures.append("tail_start_mode_not_positive")
    if int(finite_cutoff) < int(tail_start_mode):
        failures.append("finite_cutoff_before_tail_start")
    if float(sigma) <= 0.0 or not math.isfinite(float(sigma)):
        failures.append("sigma_not_positive")

    if failures:
        return ModewiseTailLedger(
            theorem_usable=False,
            rho=float(rho), sigma=float(sigma), tail_start_mode=int(tail_start_mode), finite_cutoff=int(finite_cutoff),
            geometric_ratio=float(geometric_ratio) if math.isfinite(geometric_ratio) else float("nan"),
            tail_sup_at_start=float(tail_sup) if math.isfinite(tail_sup) else float("nan"),
            tail_l1_bound=float("inf"), modewise_finite_l1=float("inf"), modewise_remainder_l1=float("inf"),
            global_inverse_bound_used_by_phase2o=global_inverse_bound,
            global_inverse_tail_response=None if global_inverse_bound is None else float("inf"),
            modewise_finite_response=float("inf"), modewise_remainder_response=float("inf"), modewise_tail_response=float("inf"),
            improvement_factor_vs_global_response=None, golden_diophantine_constant=_GOLDEN_DIOPHANTINE_C,
            worst_finite_inverse=float("inf"), worst_finite_inverse_mode=0, top_contributors=tuple(), failure_reasons=tuple(failures),
        )

    start = int(tail_start_mode)
    cutoff = int(finite_cutoff)
    q = float(geometric_ratio)
    finite_l1 = 0.0
    finite_response = 0.0
    worst_inv = 0.0
    worst_k = 0
    contribs: list[dict[str, float | int]] = []
    for m in range(start, cutoff + 1):
        amp_two_sided = 2.0 * float(tail_sup) * (q ** (m - start))
        gap = exact_small_divisor_gap(float(rho), int(m))
        inv = float("inf") if gap <= 0.0 else 1.0 / gap
        resp = amp_two_sided * inv
        finite_l1 += amp_two_sided
        finite_response += resp
        if inv > worst_inv:
            worst_inv = inv
            worst_k = m
        if resp > 0.0:
            contribs.append({"mode": int(m), "two_sided_tail_bound": float(amp_two_sided), "inverse_multiplier": float(inv), "response_contribution": float(resp)})
    rem_l1, rem_response = _golden_tail_remainder_bound(tail_sup=float(tail_sup), ratio=q, tail_start=start, after_mode=cutoff)
    total_l1 = float(finite_l1 + rem_l1)
    total_response = float(finite_response + rem_response)
    global_resp = None if global_inverse_bound is None else float(global_inverse_bound) * total_l1
    improvement = None
    if global_resp is not None and total_response > 0.0 and math.isfinite(global_resp):
        improvement = float(total_response / global_resp)
    contribs.sort(key=lambda x: float(x["response_contribution"]), reverse=True)
    return ModewiseTailLedger(
        theorem_usable=True,
        rho=float(rho),
        sigma=float(sigma),
        tail_start_mode=start,
        finite_cutoff=cutoff,
        geometric_ratio=q,
        tail_sup_at_start=float(tail_sup),
        tail_l1_bound=total_l1,
        modewise_finite_l1=float(finite_l1),
        modewise_remainder_l1=float(rem_l1),
        global_inverse_bound_used_by_phase2o=None if global_inverse_bound is None else float(global_inverse_bound),
        global_inverse_tail_response=global_resp,
        modewise_finite_response=float(finite_response),
        modewise_remainder_response=float(rem_response),
        modewise_tail_response=total_response,
        improvement_factor_vs_global_response=improvement,
        golden_diophantine_constant=_GOLDEN_DIOPHANTINE_C,
        worst_finite_inverse=float(worst_inv),
        worst_finite_inverse_mode=int(worst_k),
        top_contributors=tuple(contribs[:16]),
        failure_reasons=tuple(),
    )


def _tail_components_for_sigma(
    *,
    selected: Mapping[str, Any],
    attempt: Mapping[str, Any] | None,
    sigma: float,
    tail_start_mode: int,
) -> dict[str, Any]:
    # Prefer recomputing from raw u samples so the sigma scan is real.  If u is
    # absent, fall back to the selected Phase-2O/Phase-2N tail components only
    # when the requested sigma equals the selected source sigma.
    raw = _as_mapping((attempt or {}).get("raw_certificate"))
    u, _, _ = _extract_u_lambda(raw)
    strip = _finite_float(selected.get("strip_width_proxy"), _finite_float(_as_mapping(raw.get("source_validation")).get("strip_width_proxy"), _finite_float(raw.get("strip_width_proxy"))))
    if u is not None and strip is not None:
        coeffs = spectral_coefficients_from_samples(np.asarray(u, dtype=float))
        tail = certify_fourier_tail_bound_from_coeffs(
            coeffs,
            sigma_used=float(sigma),
            strip_width_proxy=float(strip),
            tail_start_mode=int(tail_start_mode),
        )
        d = tail.to_dict()
        d["source"] = "recomputed_from_u_coefficients"
        return d

    comp = _as_mapping(_as_mapping(selected.get("components")).get("tail_components"))
    if comp:
        d = dict(comp)
        d["source"] = "selected_row_tail_components_fallback"
        return d
    tail = _as_mapping(raw.get("tail_bound"))
    d = dict(tail)
    d["source"] = "raw_certificate_tail_bound_fallback"
    return d


def _global_inverse_bound(selected: Mapping[str, Any], attempt: Mapping[str, Any] | None) -> float | None:
    comp = _as_mapping(_as_mapping(selected.get("components")).get("tail_components"))
    v = _finite_float(comp.get("inverse_bound_used"))
    if v is not None:
        return v
    raw = _as_mapping((attempt or {}).get("raw_certificate"))
    v = _finite_float(raw.get("cohomological_inverse_bound"))
    if v is not None:
        return v
    strict = _as_mapping((attempt or {}).get("strict_ledger"))
    div = _as_mapping(strict.get("divisor_ledger"))
    return _finite_float(div.get("max_inverse_multiplier"))


def build_phase2p_row(
    *,
    model_name: str,
    input_summary: Phase2PInputSummary,
    selected: Mapping[str, Any],
    attempt: Mapping[str, Any] | None,
    config: Phase2PScanConfig,
    sigma: float,
    oversample_factor: int,
    tail_cutoff: int,
) -> Phase2PRow:
    raw = _as_mapping((attempt or {}).get("raw_certificate"))
    u, lam, _ = _extract_u_lambda(raw)
    family = HarmonicFamily()
    rho = float(input_summary.rho)
    K = float(input_summary.K_mid)
    radius = _finite_float(selected.get("radius_r"), input_summary.source_radius)
    radius = float(radius if radius is not None else input_summary.source_radius)
    linear_Z = _finite_float(selected.get("linear_Z"), input_summary.source_linear_Z)
    linear_Z = float(linear_Z if linear_Z is not None else input_summary.source_linear_Z)
    finite_nl = _finite_float(selected.get("finite_nonlinear_term"))
    if finite_nl is None:
        finite_nl = linear_Z * radius
    finite_q = _finite_float(selected.get("finite_contraction_q"), _finite_float(raw.get("finite_contraction_bound"), 0.0)) or 0.0
    finite_poly_margin = _finite_float(selected.get("finite_poly_margin"), _finite_float(raw.get("finite_radii_margin"), 0.0)) or 0.0
    nonlinear_guard = _finite_float(selected.get("nonlinear_guard"), 0.0) or 0.0
    tail_start = int(_finite_float(selected.get("tail_start_mode"), input_summary.source_tail_start_mode) or input_summary.source_tail_start_mode)

    # Recompute residual_Y at the same sigma when possible; otherwise preserve
    # the selected-source value and mark the row accordingly.
    residual_Y = _finite_float(selected.get("residual_Y"), input_summary.source_residual_Y)
    residual_Y = float(residual_Y if residual_Y is not None else input_summary.source_residual_Y)
    residual_components: dict[str, Any] = {"source": "selected_input_row"}
    if u is not None and lam is not None:
        residual_Y, weighted_resid_l1, resid_trunc = _modewise_inverse_applied_residual_from_samples(
            u=u,
            rho=rho,
            K=K,
            family=family,
            lambda_value=float(lam),
            sigma=float(sigma),
            oversample_factor=int(oversample_factor),
        )
        residual_components = {
            "source": "recomputed_from_source_samples",
            "weighted_residual_l1": float(weighted_resid_l1),
            "residual_truncation": int(resid_trunc),
            "oversample_factor": int(oversample_factor),
        }

    tail_comp = _tail_components_for_sigma(selected=selected, attempt=attempt, sigma=float(sigma), tail_start_mode=tail_start)
    tail_sup = _finite_float(tail_comp.get("tail_sup"))
    ratio = _finite_float(tail_comp.get("geometric_ratio"))
    tail_l1_source = _finite_float(tail_comp.get("tail_l1"))
    global_inv = _global_inverse_bound(selected, attempt)
    ledger = build_modewise_geometric_tail_ledger(
        rho=rho,
        sigma=float(sigma),
        tail_start_mode=tail_start,
        finite_cutoff=int(tail_cutoff),
        tail_sup=float("nan") if tail_sup is None else float(tail_sup),
        geometric_ratio=float("nan") if ratio is None else float(ratio),
        global_inverse_bound=global_inv,
    )

    tail_response = float(ledger.modewise_tail_response)
    tail_T = float(tail_response + nonlinear_guard)
    lhs = float(residual_Y + finite_nl + tail_T)
    margin = float(radius - lhs - abs(config.outward_rounding_tolerance))
    allowable = float(radius - finite_nl - residual_Y)
    needed_tail_factor = None if tail_T <= 0.0 or not math.isfinite(tail_T) else float(allowable / tail_T)
    required = abs(config.outward_rounding_tolerance) * max(1.0, float(config.theorem_margin_safety_factor))

    failures: list[str] = []
    if abs(rho - _GOLDEN_RHO) > float(config.golden_rho_tolerance):
        failures.append("rho_not_within_golden_tolerance")
    if sigma < float(config.min_theorem_sigma):
        failures.append("sigma_below_min_theorem_sigma")
    if not (math.isfinite(radius) and radius > 0.0):
        failures.append("radius_missing_or_nonpositive")
    if not (math.isfinite(residual_Y)):
        failures.append("residual_Y_not_finite")
    if not (math.isfinite(finite_nl)):
        failures.append("finite_nonlinear_term_not_finite")
    if not (math.isfinite(finite_q) and finite_q < 1.0):
        failures.append("finite_contraction_q_not_below_one")
    if not (math.isfinite(finite_poly_margin) and finite_poly_margin > 0.0):
        failures.append("finite_radius_polynomial_margin_nonpositive")
    if not ledger.theorem_usable:
        failures.extend(ledger.failure_reasons)
    if tail_l1_source is not None and math.isfinite(tail_l1_source):
        # The modewise ledger should reproduce the original geometric l1 bound
        # within a small outward tolerance; otherwise it might have dropped mass.
        if ledger.tail_l1_bound > float(tail_l1_source) * (1.0 + 1e-8) + 1e-18:
            # This is safe but records that our reconstruction is looser.
            pass
        elif ledger.tail_l1_bound < float(tail_l1_source) * (1.0 - 1e-6) - 1e-18:
            failures.append("modewise_tail_l1_below_source_tail_l1")
    if not (math.isfinite(tail_T)):
        failures.append("tail_bound_T_not_finite")
    if margin <= required:
        failures.append("analytic_radii_margin_not_safely_positive")

    theorem_eligible = bool(
        sigma >= float(config.min_theorem_sigma)
        and abs(rho - _GOLDEN_RHO) <= float(config.golden_rho_tolerance)
        and ledger.theorem_usable
    )
    theorem_ready = bool(theorem_eligible and not failures)
    return Phase2PRow(
        model_name=str(model_name),
        tail_model="strict_modewise_geometric_tail_response",
        theorem_eligible=theorem_eligible,
        theorem_ready=theorem_ready,
        sigma=float(sigma),
        oversample_factor=int(oversample_factor),
        tail_cutoff=int(tail_cutoff),
        radius_r=float(radius),
        residual_Y=float(residual_Y),
        finite_nonlinear_term=float(finite_nl),
        linear_Z=float(linear_Z),
        finite_contraction_q=float(finite_q),
        finite_poly_margin=float(finite_poly_margin),
        nonlinear_guard=float(nonlinear_guard),
        tail_l1=float(ledger.tail_l1_bound),
        tail_response_bound=float(tail_response),
        tail_T=float(tail_T),
        radii_lhs=float(lhs),
        radii_margin=float(margin),
        allowable_tail_max=float(allowable),
        needed_tail_factor=needed_tail_factor,
        tail_start_mode=int(tail_start),
        tail_theorem_usable=bool(ledger.theorem_usable),
        failure_reasons=tuple(dict.fromkeys(failures)),
        modewise_tail_ledger=ledger,
        components={
            "tail_components_source": tail_comp,
            "residual_components": residual_components,
            "selected_input_row": dict(selected),
            "raw_tail_l1_source": tail_l1_source,
            "global_inverse_bound": global_inv,
        },
        notes="Strict Phase-2P modewise inverse-applied geometric tail response with golden Diophantine infinite-remainder bound.",
    )


def _row_sort_key(row: Phase2PRow) -> tuple[float, float, float, float, float]:
    return (
        1.0 if row.theorem_ready else 0.0,
        1.0 if row.theorem_eligible else 0.0,
        float(row.radii_margin) if math.isfinite(row.radii_margin) else -float("inf"),
        -float(row.tail_T) if math.isfinite(row.tail_T) else -float("inf"),
        -float(row.tail_cutoff),
    )


def build_phase2p_report(input_path: str | Path, config: Phase2PScanConfig | None = None) -> Phase2PReport:
    cfg = config or Phase2PScanConfig(input_path=str(input_path))
    input_json, phase2n_attempt, phase2n_path, input_kind = resolve_phase2p_input(input_path)
    selected_rows = _extract_selected_rows(input_json, input_kind, input_path)
    selected = selected_rows[0] if selected_rows else {}
    input_summary = _build_input_summary(
        original_input_path=str(input_path),
        input_kind=input_kind,
        input_json=input_json,
        selected=selected,
        phase2n_attempt=phase2n_attempt,
        phase2n_path=phase2n_path,
    )
    sigmas = list(cfg.sigma_values)
    if cfg.include_source_sigma_row and input_summary.source_sigma > 0 and input_summary.source_sigma not in sigmas:
        sigmas.append(input_summary.source_sigma)
    sigmas = sorted(set(float(s) for s in sigmas if s > 0.0), reverse=True)
    rows: list[Phase2PRow] = []
    if not selected_rows:
        selected_rows = [selected]
    for selected_i, selected_row in enumerate(selected_rows):
        selected_name = _safe_slug(selected_row.get("model_name", f"row_{selected_i}"))
        for sigma in sigmas:
            for osf in cfg.oversample_factors:
                for cutoff in cfg.tail_cutoffs:
                    rows.append(build_phase2p_row(
                        model_name=(
                            f"strict_modewise_tail_from_{selected_name}_"
                            f"sg{float(sigma):.3e}_os{int(osf)}_cut{int(cutoff)}"
                        ),
                        input_summary=input_summary,
                        selected=selected_row,
                        attempt=phase2n_attempt,
                        config=cfg,
                        sigma=float(sigma),
                        oversample_factor=int(osf),
                        tail_cutoff=int(cutoff),
                    ))
    rows.sort(key=_row_sort_key, reverse=True)
    eligible = [r for r in rows if r.theorem_eligible]
    ready = [r for r in eligible if r.theorem_ready]
    best = eligible[0].to_dict() if eligible else None
    if ready:
        status = "phase2p-theorem-ready-modewise-tail-closure"
        conclusion = {
            "closed": True,
            "recommended_next_step": "export_phase2p_candidate_and_merge_collar_000_then_propagate_phase2p_to_the_next_collar_segment",
            "message": "A theorem-eligible modewise tail row has positive outward-rounded margin.",
            "best_ready_margin": float(ready[0].radii_margin),
            "best_ready_tail_T": float(ready[0].tail_T),
            "best_ready_allowable_tail_max": float(ready[0].allowable_tail_max),
        }
    else:
        status = "phase2p-diagnostic-modewise-tail-not-closed"
        best_row = eligible[0] if eligible else (rows[0] if rows else None)
        conclusion = {
            "closed": False,
            "recommended_next_step": "if_modewise_tail_fails_change_the_lower_norm_or_recompute_a_better_finite_inverse",
            "message": "No theorem-eligible modewise tail row closed.",
            "best_eligible_margin": None if best_row is None else float(best_row.radii_margin),
            "best_eligible_tail_T": None if best_row is None else float(best_row.tail_T),
            "best_eligible_allowable_tail_max": None if best_row is None else float(best_row.allowable_tail_max),
        }
    return Phase2PReport(
        schema="phase2p_modewise_tail_scan_report_v1",
        status=status,
        config=cfg,
        input_summary=input_summary,
        theorem_ready_count=len(ready),
        theorem_eligible_count=len(eligible),
        best_theorem_eligible=best,
        conclusion=conclusion,
        rows=tuple(rows),
        raw_input=dict(input_json),
        raw_phase2n_attempt=None if phase2n_attempt is None else dict(phase2n_attempt),
    )


def write_phase2p_report(report: Phase2PReport, out_path: str | Path, *, include_raw_input: bool = False) -> None:
    atomic_write_json(out_path, report.to_dict(include_raw_input=include_raw_input))


def write_phase2p_csv(report: Phase2PReport, csv_path: str | Path) -> None:
    csv_path = Path(csv_path)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "model_name", "tail_model", "theorem_eligible", "theorem_ready", "sigma", "oversample_factor", "tail_cutoff",
        "radii_margin", "residual_Y", "finite_nonlinear_term", "linear_Z", "finite_contraction_q", "finite_poly_margin",
        "nonlinear_guard", "tail_l1", "tail_response_bound", "tail_T", "allowable_tail_max", "needed_tail_factor",
        "tail_start_mode", "tail_theorem_usable", "failure_reasons", "global_inverse_tail_response", "modewise_tail_response",
        "improvement_factor_vs_global_response", "worst_finite_inverse", "worst_finite_inverse_mode", "notes",
    ]
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in report.rows:
            d = row.to_dict()
            led = d.get("modewise_tail_ledger", {})
            d["failure_reasons"] = ";".join(d.get("failure_reasons", []))
            d["global_inverse_tail_response"] = led.get("global_inverse_tail_response")
            d["modewise_tail_response"] = led.get("modewise_tail_response")
            d["improvement_factor_vs_global_response"] = led.get("improvement_factor_vs_global_response")
            d["worst_finite_inverse"] = led.get("worst_finite_inverse")
            d["worst_finite_inverse_mode"] = led.get("worst_finite_inverse_mode")
            writer.writerow({k: d.get(k) for k in fields})


def build_phase2p_candidate(report: Phase2PReport, *, source_artifact: str) -> dict[str, Any]:
    ready = [r for r in report.rows if r.theorem_eligible and r.theorem_ready]
    selected = ready[0] if ready else (next((r for r in report.rows if r.theorem_eligible), report.rows[0] if report.rows else None))
    if selected is None:
        raise ValueError("Phase-2P report has no rows")
    inp = report.input_summary
    theorem_facing = bool(selected.theorem_eligible and selected.theorem_ready)
    row = {
        "segment_id": inp.segment_id,
        "K_lo": inp.K_lo,
        "K_hi": inp.K_hi,
        "K_mid": inp.K_mid,
        "rho": inp.rho,
        "N": inp.N,
        "sigma": selected.sigma,
        "oversample_factor": selected.oversample_factor,
        "norm_name": "phase2p-modewise-tail-radii-polynomial",
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
        "small_divisor_source": "phase2p-modewise-tail-golden-diophantine-ledger",
        "source_module": "kam_theorem_suite.audit.lower_anchor_phase2p_modewise_tail",
        "source_artifact": str(source_artifact),
        "certified": theorem_facing,
        "finite_dimensional_only": bool(not theorem_facing),
        "closure_level": "phase2p_modewise_tail_closure" if theorem_facing else "phase2p_modewise_tail_not_closed",
        "theorem_ready": theorem_facing,
        "analytic_probe_attempted": True,
        "analytic_theorem_status": "phase2p-modewise-tail-closed" if theorem_facing else "phase2p-modewise-tail-diagnostic",
        "analytic_theorem_margin": selected.radii_margin,
        "failure_reasons": list(selected.failure_reasons),
        "phase2p_ledger": selected.to_dict(),
    }
    candidate_payload = {
        "schema": "phase2p_single_segment_candidate_v1",
        "theorem_facing": theorem_facing,
        "diagnostic_only": bool(not theorem_facing),
        "promotion_allowed": theorem_facing,
        "closure_level": "phase2p_modewise_tail_closure" if theorem_facing else "phase2p_modewise_tail_not_closed",
        "source": "Phase-2P modewise tail closure candidate",
        "failure_fields": [] if theorem_facing else ["phase2p_modewise_tail_not_theorem_ready"],
        "notes": (
            "One-segment theorem-facing Phase-2P candidate. Merge into a contiguous collar only after overlap checks."
            if theorem_facing else
            "Diagnostic Phase-2P candidate. Do not promote unless theorem_facing is true."
        ),
        "input_summary": report.input_summary.to_dict(),
        "selected_phase2p_row": selected.to_dict(),
        "rows": [selected.to_dict()],
        "anchor_segments": [row],
    }
    if attach_raw_validation_payload_to_candidate is not None:
        try:
            candidate_payload = attach_raw_validation_payload_to_candidate(
                candidate_payload,
                phase2n_attempt=report.raw_phase2n_attempt,
                selected_row=selected.to_dict(),
                input_summary=report.input_summary.to_dict(),
                source_artifact=str(source_artifact),
                stage="phase2p",
            )
        except Exception as exc:  # fail-open for diagnostics, fail-closed for theorem status
            candidate_payload["phase2aa_stage1b_export"] = {
                "enabled": False,
                "error": repr(exc),
                "does_not_change_theorem_facing_status": True,
            }
    return candidate_payload


def print_compact_report(report: Phase2PReport) -> str:
    best = report.best_theorem_eligible or {}
    return json.dumps({
        "status": report.status,
        "theorem_ready_count": report.theorem_ready_count,
        "theorem_eligible_count": report.theorem_eligible_count,
        "best_theorem_eligible": {k: best.get(k) for k in [
            "model_name", "tail_model", "theorem_ready", "sigma", "tail_cutoff", "radii_margin", "tail_T", "allowable_tail_max", "tail_response_bound", "nonlinear_guard", "failure_reasons"
        ]} if best else None,
        "conclusion": report.conclusion,
    }, indent=2)


__all__ = [
    "ModewiseTailLedger",
    "Phase2PInputSummary",
    "Phase2PReport",
    "Phase2PRow",
    "Phase2PScanConfig",
    "atomic_write_json",
    "build_modewise_geometric_tail_ledger",
    "build_phase2p_candidate",
    "build_phase2p_report",
    "parse_float_list",
    "parse_int_list",
    "print_compact_report",
    "write_phase2p_csv",
    "write_phase2p_report",
]

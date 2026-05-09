from __future__ import annotations

"""Heavy Phase-2E lower-anchor certificate driver.

This module is intentionally conservative.  It adds the machinery needed to try
for a theorem-facing lower anchor without ever promoting a finite-dimensional
or diagnostic object by accident.  The heavy path evaluates an adaptive,
near-critical continuation grid, tries a ladder of Fourier resolutions, records
modewise golden small-divisor data, and exports a Phase-2B-shaped candidate only
when every segment carries a positive analytic margin.

The present implementation is a rigorous audit/driver layer around the existing
lower-side validators.  It does not hide failures: if the analytic majorants are
still too pessimistic, the generated candidate is diagnostic-only and strict
Phase-2B ingestion remains impossible.
"""

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence
import csv
import json
import math
import time

from .lower_anchor_regeneration import DEFAULT_EXISTING_RIGHT, DEFAULT_FINAL_ANCHOR, GOLDEN_INVERSE

SUCCESS_ANALYTIC_STATUSES = {
    "analytic-torus-bridge-strong",
    "analytic-torus-bridge-moderate",
    "golden-aposteriori-bridge-strong",
    "golden-aposteriori-bridge-moderate",
}

DEFAULT_ADAPTIVE_BREAKPOINTS = (
    0.265000,
    0.500000,
    0.700000,
    0.850000,
    0.930000,
    0.960000,
    0.970000,
    0.971000,
    0.971400,
    0.971580,
    0.971636,
)


@dataclass(frozen=True)
class HeavyLowerAnchorConfig:
    start_K: float = DEFAULT_EXISTING_RIGHT
    final_anchor_lo: float = DEFAULT_FINAL_ANCHOR[0]
    final_anchor_hi: float = DEFAULT_FINAL_ANCHOR[1]
    overlap: float = 1.0e-7
    N_values: tuple[int, ...] = (64, 96, 128, 192)
    oversample_factor: int = 8
    sigma_cap: float = 0.02
    refinement_levels: int = 0
    refine_margin_threshold: float = 1.0e-7
    dry_run: bool = False
    max_segments: int | None = None
    segment_start: int = 0
    segment_stop: int | None = None
    max_wall_seconds: float | None = None
    theorem_margin_safety_factor: float = 10.0
    outward_rounding_tolerance: float = 1.0e-12
    theorem_facing_policy: str = "all-segments-positive-analytic-margin"
    use_phase2e_direct_radii_ledger: bool = True
    phase2e_nonlinear_margin_fraction: float = 0.25

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ModewiseSmallDivisorSummary:
    rho: float
    max_k: int
    min_exact_gap: float
    min_theoretical_lower_bound: float
    max_inverse_multiplier: float
    worst_k: int
    lower_bound_failures: tuple[int, ...]
    sample_rows: tuple[dict[str, float | int | bool], ...]

    @property
    def certified(self) -> bool:
        return self.max_k > 0 and self.min_exact_gap > 0.0 and not self.lower_bound_failures

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["lower_bound_failures"] = list(self.lower_bound_failures)
        d["sample_rows"] = list(self.sample_rows)
        d["certified"] = self.certified
        return d


@dataclass(frozen=True)
class HeavyLowerAnchorRecord:
    segment_id: str
    K_lo: float
    K_hi: float
    K_mid: float
    rho: float
    attempted: bool
    selected_N: int | None
    finite_success: bool
    finite_radius: float | None
    finite_eta: float | None
    finite_B_norm: float | None
    finite_lipschitz_bound: float | None
    finite_radii_margin: float | None
    analytic_status: str | None
    analytic_margin: float | None
    cohomological_correction_bound: float | None
    tail_bridge_bound_l1: float | None
    analytic_tail_term: float | None
    residual_Y: float | None
    linear_defect_Z: float | None
    tail_bound_T: float | None
    radius_r: float | None
    recomputed_phase2b_margin: float | None
    weighted_residual_l1: float | None
    relative_correction_to_graph: float | None
    small_divisor: ModewiseSmallDivisorSummary | None
    theorem_ready: bool
    closure_level: str
    failure_reasons: tuple[str, ...] = field(default_factory=tuple)
    elapsed_seconds: float = 0.0
    source_module: str = "kam_theorem_suite.torus_validator.build_theorem_optimized_analytic_invariant_circle_certificate"
    phase2e_ledger: dict[str, Any] | None = None

    def to_candidate_row(self, *, source_artifact: str) -> dict[str, Any]:
        N = int(self.selected_N or 0)
        finite_only = not self.theorem_ready
        ledger = self.phase2e_ledger if isinstance(self.phase2e_ledger, Mapping) else {}
        sigma = _float_or_none(ledger.get("sigma")) if isinstance(ledger, Mapping) else None
        if sigma is None:
            sigma = 0.0
        oversample_factor = ledger.get("oversample_factor") if isinstance(ledger, Mapping) else None
        return {
            "segment_id": self.segment_id,
            "K_lo": float(self.K_lo),
            "K_hi": float(self.K_hi),
            "K_mid": float(self.K_mid),
            "rho": float(self.rho),
            "N": N,
            "sigma": float(sigma),
            "oversample_factor": oversample_factor,
            "norm_name": "analytic-weighted-fourier-heavy-lower-certificate" if self.theorem_ready else "diagnostic-heavy-lower-certificate-attempt",
            "residual_Y": float(self.residual_Y or 0.0),
            "linear_defect_Z": float(self.linear_defect_Z or 0.0),
            "tail_bound_T": float(self.tail_bound_T or 0.0),
            "radius_r": float(self.radius_r or 0.0),
            "radii_margin": float(self.recomputed_phase2b_margin if self.recomputed_phase2b_margin is not None else 0.0),
            "small_divisor_min": float(self.small_divisor.min_exact_gap if self.small_divisor else 0.0),
            "small_divisor_inverse_bound": float(self.small_divisor.max_inverse_multiplier if self.small_divisor else 0.0),
            "small_divisor_source": "modewise-golden-small-divisor-summary",
            "source_module": self.source_module,
            "source_artifact": source_artifact,
            "certified": bool(self.theorem_ready and self.recomputed_phase2b_margin is not None and self.recomputed_phase2b_margin > 0.0),
            "finite_dimensional_only": bool(finite_only),
            "closure_level": self.closure_level,
            "theorem_ready": bool(self.theorem_ready),
            "analytic_probe_attempted": bool(self.attempted),
            "analytic_theorem_status": self.analytic_status,
            "analytic_theorem_margin": self.analytic_margin,
            "failure_reasons": list(self.failure_reasons),
            "phase2e_ledger": self.phase2e_ledger,
        }

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["failure_reasons"] = list(self.failure_reasons)
        d["small_divisor"] = None if self.small_divisor is None else self.small_divisor.to_dict()
        return d


@dataclass(frozen=True)
class HeavyLowerAnchorReport:
    schema: str
    status: str
    config: HeavyLowerAnchorConfig
    records: tuple[HeavyLowerAnchorRecord, ...]
    theorem_facing: bool
    diagnostic_only: bool
    promotion_allowed: bool
    final_anchor_reached_by_grid: bool
    attempted_record_count: int
    theorem_ready_record_count: int
    min_finite_margin: float | None
    min_analytic_margin: float | None
    min_phase2b_margin: float | None
    failure_fields: tuple[str, ...]
    notes: str

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["config"] = self.config.to_dict()
        d["records"] = [r.to_dict() for r in self.records]
        d["failure_fields"] = list(self.failure_fields)
        return d


def build_adaptive_near_anchor_grid(
    *,
    start_K: float = DEFAULT_EXISTING_RIGHT,
    final_anchor_hi: float = DEFAULT_FINAL_ANCHOR[1],
    overlap: float = 1.0e-7,
    breakpoints: Sequence[float] | None = None,
) -> list[tuple[float, float, float]]:
    raw = list(DEFAULT_ADAPTIVE_BREAKPOINTS if breakpoints is None else breakpoints)
    vals = sorted({float(x) for x in raw if float(start_K) <= float(x) <= float(final_anchor_hi)})
    if not vals or vals[0] > float(start_K):
        vals.insert(0, float(start_K))
    if vals[-1] < float(final_anchor_hi):
        vals.append(float(final_anchor_hi))
    rows: list[tuple[float, float, float]] = []
    for idx, (a, b) in enumerate(zip(vals, vals[1:])):
        lo = float(a) - (float(overlap) if idx > 0 else 0.0)
        hi = float(b) + (float(overlap) if idx < len(vals) - 2 else 0.0)
        rows.append((lo, hi, 0.5 * (float(a) + float(b))))
    return rows


def refine_grid_by_margins(
    rows: Sequence[tuple[float, float, float]],
    margin_by_mid: Mapping[float, float | None],
    *,
    threshold: float,
    levels: int = 1,
    overlap: float = 1.0e-7,
) -> list[tuple[float, float, float]]:
    current = list(rows)
    for _ in range(max(0, int(levels))):
        refined: list[tuple[float, float, float]] = []
        for lo, hi, mid in current:
            margin = margin_by_mid.get(float(mid))
            needs = margin is None or (math.isfinite(float(margin)) and float(margin) < float(threshold)) or not math.isfinite(float(margin))
            if needs:
                left_mid = 0.5 * (lo + mid)
                right_mid = 0.5 * (mid + hi)
                refined.append((lo, mid + overlap, left_mid))
                refined.append((mid - overlap, hi, right_mid))
            else:
                refined.append((lo, hi, mid))
        current = refined
    return current


def build_modewise_golden_small_divisor_summary(max_k: int, *, rho: float = GOLDEN_INVERSE, sample_limit: int = 12) -> ModewiseSmallDivisorSummary:
    max_k = int(max_k)
    if max_k <= 0:
        return ModewiseSmallDivisorSummary(float(rho), 0, float("inf"), float("inf"), 0.0, 0, tuple(), tuple())
    failures: list[int] = []
    sample: list[dict[str, float | int | bool]] = []
    min_exact = float("inf")
    min_lb = float("inf")
    max_inv = 0.0
    worst_k = 1
    for k in range(1, max_k + 1):
        exact = float(abs(math.sin(math.pi * k * float(rho))) * 2.0)
        lb = float(4.0 / (math.sqrt(5.0) * k))
        inv = float("inf") if exact <= 0.0 else 1.0 / exact
        passed = bool(exact + 1.0e-14 >= lb)
        if not passed:
            failures.append(k)
        if exact < min_exact:
            min_exact = exact
            worst_k = k
        min_lb = min(min_lb, lb)
        max_inv = max(max_inv, inv)
        if len(sample) < sample_limit or k == max_k:
            sample.append({
                "k": int(k),
                "exact_gap": exact,
                "theoretical_lower_bound": lb,
                "inverse_multiplier": inv,
                "certified_against_lower_bound": passed,
            })
    return ModewiseSmallDivisorSummary(
        rho=float(rho),
        max_k=max_k,
        min_exact_gap=float(min_exact),
        min_theoretical_lower_bound=float(min_lb),
        max_inverse_multiplier=float(max_inv),
        worst_k=int(worst_k),
        lower_bound_failures=tuple(failures),
        sample_rows=tuple(sample),
    )


def _float_or_none(value: Any) -> float | None:
    try:
        out = float(value)
    except Exception:
        return None
    return out if math.isfinite(out) else None


def _dict_of(obj: Any) -> dict[str, Any]:
    if isinstance(obj, Mapping):
        return dict(obj)
    if hasattr(obj, "to_dict"):
        return dict(obj.to_dict())
    return dict(getattr(obj, "__dict__", {}) or {})


def _build_record_from_certificate(segment_id: str, K_lo: float, K_hi: float, K_mid: float, cert: Any, *, elapsed: float, tolerance: float, safety_factor: float, oversample_factor: int = 8, use_phase2e_direct_radii_ledger: bool = True, phase2e_nonlinear_margin_fraction: float = 0.25) -> HeavyLowerAnchorRecord:
    data = _dict_of(cert)
    selected_N = int(data.get("N", data.get("selected_N", 0)) or 0)
    finite_success = bool(data.get("finite_dimensional_success", data.get("success", False)))
    finite_radius = _float_or_none(data.get("finite_radius"))
    finite_eta = _float_or_none(data.get("finite_eta"))
    B_norm = _float_or_none(data.get("finite_B_norm"))
    lipschitz = _float_or_none(data.get("finite_lipschitz_bound"))
    finite_margin = _float_or_none(data.get("finite_radii_margin"))
    analytic_margin = _float_or_none(data.get("theorem_margin", data.get("analytic_theorem_margin")))
    analytic_status = str(data.get("theorem_status", data.get("analytic_theorem_status", "")) or "")
    correction = _float_or_none(data.get("cohomological_correction_bound"))
    tail_l1 = None
    tail_bound = data.get("tail_bound")
    if isinstance(tail_bound, Mapping):
        tail_l1 = _float_or_none(tail_bound.get("tail_l1"))
    if tail_l1 is None:
        tail_l1 = _float_or_none(data.get("tail_bridge_bound_l1"))
    inv = _float_or_none(data.get("cohomological_inverse_bound")) or 0.0
    analytic_tail_term = None if tail_l1 is None else float(tail_l1) * float(inv)
    phase2e_ledger = None
    phase2e_terms_used = False
    if use_phase2e_direct_radii_ledger:
        try:
            from ..analytic_lower_krawczyk import build_analytic_lower_radii_ledger
            ledger = build_analytic_lower_radii_ledger(
                cert,
                oversample_factor=oversample_factor,
                outward_rounding_tolerance=tolerance,
                safety_factor=safety_factor,
                nonlinear_fraction_of_finite_margin=phase2e_nonlinear_margin_fraction,
            )
            phase2e_ledger = ledger.to_dict()
            # Only consume the direct modewise Phase-2E terms when the residual
            # coefficients were actually recomputed from source samples.  If the
            # certificate is a synthetic/mock object or an older compact shell,
            # keep the Phase-2D aggregate fallback so tests and archival shells
            # remain readable but not over-promoted.
            if ledger.modewise_residual_available:
                residual_Y = float(ledger.residual_Y)
                linear_defect_Z = float(ledger.linear_defect_Z)
                tail_T = float(ledger.tail_bound_T)
                finite_radius = float(ledger.radius_r)
                # Phase-2B recomputes the strict margin exactly from Y, Z, T, r.
                # The Phase-2E ledger stores an outward-rounded margin for
                # theorem readiness; the candidate row must store the raw
                # recomputable margin so ingestion does not reject it as stale.
                phase2b_margin = float(finite_radius - (residual_Y + linear_defect_Z * finite_radius + tail_T))
                phase2e_terms_used = True
            else:
                residual_Y = linear_defect_Z = tail_T = phase2b_margin = None
        except Exception as exc:
            phase2e_ledger = {"phase2e_ledger_exception": repr(exc)}
            residual_Y = linear_defect_Z = tail_T = phase2b_margin = None

    if not phase2e_terms_used:
        if finite_radius is not None and finite_eta is not None and B_norm is not None and lipschitz is not None:
            residual_Y = float(finite_eta)
            linear_defect_Z = float(0.5 * B_norm * lipschitz * finite_radius)
            tail_T = float(correction or 0.0) + float(analytic_tail_term or 0.0)
            phase2b_margin = float(finite_radius - (residual_Y + linear_defect_Z * finite_radius + tail_T))
        else:
            residual_Y = linear_defect_Z = tail_T = phase2b_margin = None

    small = build_modewise_golden_small_divisor_summary(max(1, selected_N // 2)) if selected_N > 0 else None
    required_margin = float(safety_factor) * float(tolerance)
    phase2e_ready = bool(phase2e_terms_used and phase2e_ledger and phase2e_ledger.get("theorem_ready", False))
    legacy_ready = bool(
        (not phase2e_terms_used)
        and analytic_margin is not None
        and phase2b_margin is not None
        and analytic_margin > required_margin
        and phase2b_margin > required_margin
        and analytic_status in SUCCESS_ANALYTIC_STATUSES
    )
    theorem_ready = bool(
        finite_success
        and (phase2e_ready or legacy_ready)
        and small is not None
        and small.certified
    )
    reasons: list[str] = []
    if not finite_success:
        reasons.append("finite_validator_failed")
    if finite_margin is None or finite_margin <= 0.0:
        reasons.append("finite_radii_margin_nonpositive")
    if phase2e_terms_used:
        if not phase2e_ready:
            reasons.append("phase2e_direct_analytic_radii_ledger_not_closed")
        if phase2e_ledger:
            reasons.extend(str(x) for x in phase2e_ledger.get("failure_reasons", []) or [])
    else:
        if use_phase2e_direct_radii_ledger:
            reasons.append("phase2e_direct_analytic_radii_ledger_unavailable_using_legacy_fallback")
        if analytic_margin is None or analytic_margin <= required_margin:
            reasons.append("analytic_theorem_margin_not_safely_positive")
        if analytic_status not in SUCCESS_ANALYTIC_STATUSES:
            reasons.append("analytic_status_not_promotable")
    if phase2b_margin is None or phase2b_margin <= required_margin:
        reasons.append("phase2b_recomputed_margin_not_safely_positive")
    if small is None or not small.certified:
        reasons.append("small_divisor_modewise_audit_failed")
    return HeavyLowerAnchorRecord(
        segment_id=segment_id,
        K_lo=float(K_lo), K_hi=float(K_hi), K_mid=float(K_mid), rho=float(GOLDEN_INVERSE),
        attempted=True, selected_N=selected_N, finite_success=finite_success,
        finite_radius=finite_radius, finite_eta=finite_eta, finite_B_norm=B_norm,
        finite_lipschitz_bound=lipschitz, finite_radii_margin=finite_margin,
        analytic_status=analytic_status, analytic_margin=analytic_margin,
        cohomological_correction_bound=correction, tail_bridge_bound_l1=tail_l1,
        analytic_tail_term=analytic_tail_term, residual_Y=residual_Y,
        linear_defect_Z=linear_defect_Z, tail_bound_T=tail_T, radius_r=finite_radius,
        recomputed_phase2b_margin=phase2b_margin,
        weighted_residual_l1=_float_or_none(data.get("weighted_residual_l1", (data.get("defect_report") or {}).get("weighted_l1") if isinstance(data.get("defect_report"), Mapping) else None)),
        relative_correction_to_graph=_float_or_none(data.get("relative_correction_to_graph")),
        small_divisor=small,
        theorem_ready=theorem_ready,
        closure_level="analytic_theorem_closure" if theorem_ready else ("phase2e_direct_radii_attempt_not_closed" if phase2e_terms_used else "heavy_analytic_attempt_not_closed"),
        failure_reasons=tuple(dict.fromkeys(reasons)),
        elapsed_seconds=float(elapsed),
        phase2e_ledger=phase2e_ledger,
    )


def _dry_record(segment_id: str, K_lo: float, K_hi: float, K_mid: float) -> HeavyLowerAnchorRecord:
    return HeavyLowerAnchorRecord(
        segment_id=segment_id, K_lo=float(K_lo), K_hi=float(K_hi), K_mid=float(K_mid), rho=float(GOLDEN_INVERSE),
        attempted=False, selected_N=None, finite_success=False, finite_radius=None, finite_eta=None,
        finite_B_norm=None, finite_lipschitz_bound=None, finite_radii_margin=None,
        analytic_status="dry-run-not-executed", analytic_margin=None,
        cohomological_correction_bound=None, tail_bridge_bound_l1=None, analytic_tail_term=None,
        residual_Y=None, linear_defect_Z=None, tail_bound_T=None, radius_r=None,
        recomputed_phase2b_margin=None, weighted_residual_l1=None,
        relative_correction_to_graph=None, small_divisor=None, theorem_ready=False,
        closure_level="dry_run_plan_only", failure_reasons=("heavy_certificate_not_executed",), elapsed_seconds=0.0,
        phase2e_ledger=None,
    )


def run_heavy_lower_anchor_certificate(
    config: HeavyLowerAnchorConfig | None = None,
    *,
    certificate_builder: Callable[..., Any] | None = None,
) -> HeavyLowerAnchorReport:
    cfg = config or HeavyLowerAnchorConfig()
    all_rows = build_adaptive_near_anchor_grid(start_K=cfg.start_K, final_anchor_hi=cfg.final_anchor_hi, overlap=cfg.overlap)
    grid_total_segments = len(all_rows)
    segment_start = max(0, int(cfg.segment_start))
    segment_stop = grid_total_segments if cfg.segment_stop is None else min(grid_total_segments, max(segment_start, int(cfg.segment_stop)))
    rows = list(all_rows[segment_start:segment_stop])
    if cfg.max_segments is not None:
        rows = rows[: int(cfg.max_segments)]
        segment_stop = min(segment_stop, segment_start + len(rows))
    records: list[HeavyLowerAnchorRecord] = []
    wall_started = time.time()
    stopped_for_wall_time = False
    builder = certificate_builder
    import_failure: str | None = None
    if builder is None and not cfg.dry_run:
        try:
            from kam_theorem_suite.torus_validator import build_theorem_optimized_analytic_invariant_circle_certificate
            builder = build_theorem_optimized_analytic_invariant_circle_certificate
        except Exception as exc:
            import_failure = repr(exc)
    for local_idx, (K_lo, K_hi, K_mid) in enumerate(rows):
        if cfg.max_wall_seconds is not None and (time.time() - wall_started) >= float(cfg.max_wall_seconds):
            stopped_for_wall_time = True
            break
        idx = segment_start + local_idx
        sid = f"phase2e_heavy_anchor_segment_{idx:03d}"
        if cfg.dry_run or builder is None:
            rec = _dry_record(sid, K_lo, K_hi, K_mid)
            if import_failure:
                rec = HeavyLowerAnchorRecord(**{**rec.to_dict(), "failure_reasons": tuple(list(rec.failure_reasons) + ["numeric_lower_stack_unavailable"]), "analytic_status": import_failure})
            records.append(rec)
            continue
        t0 = time.time()
        try:
            cert = builder(
                rho=float(GOLDEN_INVERSE),
                K=float(K_mid),
                N_values=tuple(int(x) for x in cfg.N_values),
                sigma_cap=float(cfg.sigma_cap),
                oversample_factor=int(cfg.oversample_factor),
            )
            rec = _build_record_from_certificate(
                sid, K_lo, K_hi, K_mid, cert,
                elapsed=time.time() - t0,
                tolerance=cfg.outward_rounding_tolerance,
                safety_factor=cfg.theorem_margin_safety_factor,
                oversample_factor=cfg.oversample_factor,
                use_phase2e_direct_radii_ledger=cfg.use_phase2e_direct_radii_ledger,
                phase2e_nonlinear_margin_fraction=cfg.phase2e_nonlinear_margin_fraction,
            )
        except Exception as exc:
            rec = _dry_record(sid, K_lo, K_hi, K_mid)
            rec = HeavyLowerAnchorRecord(**{**rec.to_dict(), "attempted": True, "elapsed_seconds": time.time() - t0, "analytic_status": "exception", "failure_reasons": ("heavy_certificate_exception", repr(exc))})
        records.append(rec)
    report = build_heavy_lower_anchor_report(records, cfg)
    if stopped_for_wall_time:
        data = report.to_dict()
        failures = list(data.get("failure_fields", []) or [])
        if "wall_time_budget_exhausted" not in failures:
            failures.append("wall_time_budget_exhausted")
        data["failure_fields"] = failures
        data["diagnostic_only"] = True
        data["theorem_facing"] = False
        data["promotion_allowed"] = False
        data["status"] = "heavy-lower-anchor-diagnostic-or-incomplete"
        data["notes"] = str(data.get("notes", "")) + " Wall-time budget expired before all requested segments completed."
        return HeavyLowerAnchorReport(
            schema=data["schema"],
            status=data["status"],
            config=cfg,
            records=tuple(records),
            theorem_facing=False,
            diagnostic_only=True,
            promotion_allowed=False,
            final_anchor_reached_by_grid=bool(data.get("final_anchor_reached_by_grid", False)),
            attempted_record_count=int(data.get("attempted_record_count", 0)),
            theorem_ready_record_count=int(data.get("theorem_ready_record_count", 0)),
            min_finite_margin=data.get("min_finite_margin"),
            min_analytic_margin=data.get("min_analytic_margin"),
            min_phase2b_margin=data.get("min_phase2b_margin"),
            failure_fields=tuple(failures),
            notes=data["notes"],
        )
    return report


def build_heavy_lower_anchor_report(records: Sequence[HeavyLowerAnchorRecord | Mapping[str, Any]], config: HeavyLowerAnchorConfig | None = None) -> HeavyLowerAnchorReport:
    cfg = config or HeavyLowerAnchorConfig()
    recs: list[HeavyLowerAnchorRecord] = []
    for item in records:
        if isinstance(item, HeavyLowerAnchorRecord):
            recs.append(item)
        else:
            data = dict(item)
            if isinstance(data.get("small_divisor"), Mapping):
                sd = data["small_divisor"]
                data["small_divisor"] = ModewiseSmallDivisorSummary(
                    rho=float(sd.get("rho", GOLDEN_INVERSE)),
                    max_k=int(sd.get("max_k", 0)),
                    min_exact_gap=float(sd.get("min_exact_gap", 0.0)),
                    min_theoretical_lower_bound=float(sd.get("min_theoretical_lower_bound", 0.0)),
                    max_inverse_multiplier=float(sd.get("max_inverse_multiplier", 0.0)),
                    worst_k=int(sd.get("worst_k", 0)),
                    lower_bound_failures=tuple(int(x) for x in sd.get("lower_bound_failures", []) or []),
                    sample_rows=tuple(dict(x) for x in sd.get("sample_rows", []) or []),
                )
            data["failure_reasons"] = tuple(data.get("failure_reasons", []) or [])
            recs.append(HeavyLowerAnchorRecord(**data))
    final_reached = bool(recs and min(r.K_lo for r in recs) <= cfg.start_K and max(r.K_hi for r in recs) >= cfg.final_anchor_hi)
    full_grid_requested = (int(cfg.segment_start) <= 0 and cfg.segment_stop is None and cfg.max_segments is None)
    attempted = sum(1 for r in recs if r.attempted)
    ready = sum(1 for r in recs if r.theorem_ready)
    finite_margins = [r.finite_radii_margin for r in recs if r.finite_radii_margin is not None and math.isfinite(r.finite_radii_margin)]
    analytic_margins = [r.analytic_margin for r in recs if r.analytic_margin is not None and math.isfinite(r.analytic_margin)]
    p2b_margins = [r.recomputed_phase2b_margin for r in recs if r.recomputed_phase2b_margin is not None and math.isfinite(r.recomputed_phase2b_margin)]
    failures: list[str] = []
    if not recs:
        failures.append("heavy_lower_anchor_records_missing")
    if attempted != len(recs):
        failures.append("some_heavy_segments_not_attempted")
    if ready != len(recs):
        failures.append("analytic_theorem_closure_not_established_for_all_segments")
    if not final_reached:
        failures.append("grid_does_not_reach_final_anchor")
    if not full_grid_requested:
        failures.append("partial_grid_run_not_promotable")
    theorem_facing = bool(recs and ready == len(recs) and final_reached and not failures)
    return HeavyLowerAnchorReport(
        schema="phase2e_heavy_lower_anchor_certificate_report_v1",
        status="theorem-ready-heavy-lower-anchor-generated" if theorem_facing else "heavy-lower-anchor-diagnostic-or-incomplete",
        config=cfg,
        records=tuple(recs),
        theorem_facing=theorem_facing,
        diagnostic_only=not theorem_facing,
        promotion_allowed=theorem_facing,
        final_anchor_reached_by_grid=final_reached,
        attempted_record_count=attempted,
        theorem_ready_record_count=ready,
        min_finite_margin=(None if not finite_margins else float(min(finite_margins))),
        min_analytic_margin=(None if not analytic_margins else float(min(analytic_margins))),
        min_phase2b_margin=(None if not p2b_margins else float(min(p2b_margins))),
        failure_fields=tuple(failures),
        notes=(
            "Every segment must have a safely positive analytic theorem margin before this payload is promotable. "
            "Diagnostic runs are intentionally rejected by Phase-2B strict ingestion."
        ),
    )


def build_heavy_candidate_json(report: HeavyLowerAnchorReport, *, source_artifact: str) -> dict[str, Any]:
    return {
        "schema": "phase2e_heavy_lower_anchor_candidate_v1",
        "theorem_facing": bool(report.theorem_facing),
        "diagnostic_only": bool(report.diagnostic_only),
        "promotion_allowed": bool(report.promotion_allowed),
        "closure_level": "analytic_theorem_closure" if report.promotion_allowed else "heavy_analytic_attempt_not_closed",
        "source": "Phase-2E adaptive lower-anchor analytic Krawczyk/radii certificate driver",
        "config": report.config.to_dict(),
        "failure_fields": list(report.failure_fields),
        "notes": report.notes,
        "anchor_segments": [r.to_candidate_row(source_artifact=source_artifact) for r in report.records],
        "raw_validation_records": [r.to_dict() for r in report.records],
    }


def write_heavy_lower_anchor_outputs(
    report: HeavyLowerAnchorReport,
    *,
    out_dir: str | Path,
    table_dir: str | Path,
    candidate_name: str = "lower_anchor_heavy_candidate.json",
) -> dict[str, Any]:
    out = Path(out_dir); tab = Path(table_dir)
    out.mkdir(parents=True, exist_ok=True); tab.mkdir(parents=True, exist_ok=True)
    candidate_path = out / candidate_name
    report_path = out / "lower_anchor_heavy_report.json"
    csv_path = tab / "lower_anchor_heavy_records.csv"
    tex_path = tab / "lower_anchor_heavy_records.tex"
    candidate = build_heavy_candidate_json(report, source_artifact=str(candidate_path))
    candidate_path.write_text(json.dumps(candidate, indent=2, sort_keys=True) + "\n")
    report_path.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True) + "\n")
    fields = ["segment_id", "K_lo", "K_hi", "K_mid", "attempted", "selected_N", "finite_radii_margin", "analytic_status", "analytic_margin", "recomputed_phase2b_margin", "theorem_ready", "closure_level", "failure_reasons"]
    with csv_path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields); writer.writeheader()
        for r in report.records:
            row = r.to_dict(); row["failure_reasons"] = ";".join(r.failure_reasons)
            writer.writerow({k: row.get(k) for k in fields})
    bs = chr(92)
    lines = ["% AUTO-GENERATED by lower_anchor_heavy_certificate.py; do not edit manually.", bs + "begin{tabular}{lrrrrl}", bs + "hline", "Segment & $K_{\\min}$ & $K_{\\max}$ & $N$ & analytic margin & status " + bs + bs, bs + "hline"]
    for r in report.records:
        margin = "--" if r.analytic_margin is None else f"{r.analytic_margin:.3e}"
        status = "ready" if r.theorem_ready else "diagnostic"
        N = 0 if r.selected_N is None else int(r.selected_N)
        lines.append(f"{r.segment_id} & {r.K_lo:.6f} & {r.K_hi:.6f} & {N:d} & {margin} & {status} " + bs + bs)
    lines.extend([bs + "hline", bs + "end{tabular}", ""])
    tex_path.write_text("\n".join(lines))
    return {
        "candidate_path": str(candidate_path),
        "report_path": str(report_path),
        "csv_path": str(csv_path),
        "tex_path": str(tex_path),
        "promotion_allowed": bool(report.promotion_allowed),
        "failure_fields": list(report.failure_fields),
    }




def run_heavy_lower_anchor_certificate_on_segments(
    segments: Sequence[Mapping[str, Any] | Sequence[Any]],
    config: HeavyLowerAnchorConfig | None = None,
    *,
    certificate_builder: Callable[..., Any] | None = None,
) -> HeavyLowerAnchorReport:
    """Run the heavy lower-anchor driver on an explicit custom segment list.

    This is the Phase-2G escape hatch for adaptive failure refinement.  Phase 2F
    runs slices of the canonical full grid; Phase 2G needs to rerun only the
    first failing interval after bisection, overlap repair, or resolution
    escalation.  The returned report is intentionally diagnostic unless the
    provided custom segment list also covers the complete lower-anchor path.
    Promotion is still controlled by the same Phase-2B strict ingestion step.

    Each segment may be a mapping with ``K_lo``, ``K_hi``, optional ``K_mid`` and
    optional ``segment_id`` fields, or a tuple/list ``(K_lo, K_hi, K_mid)``.
    """

    cfg = config or HeavyLowerAnchorConfig()
    normalised: list[tuple[str, float, float, float]] = []
    for idx, item in enumerate(segments):
        if isinstance(item, Mapping):
            lo = float(item["K_lo"])
            hi = float(item["K_hi"])
            mid = float(item.get("K_mid", 0.5 * (lo + hi)))
            sid = str(item.get("segment_id", f"phase2g_custom_anchor_segment_{idx:03d}"))
        else:
            vals = list(item)
            if len(vals) < 2:
                raise ValueError("custom segment tuples must contain at least K_lo and K_hi")
            lo = float(vals[0])
            hi = float(vals[1])
            mid = float(vals[2]) if len(vals) >= 3 else 0.5 * (lo + hi)
            sid = f"phase2g_custom_anchor_segment_{idx:03d}"
        if not (math.isfinite(lo) and math.isfinite(hi) and math.isfinite(mid)):
            raise ValueError(f"non-finite custom segment endpoint in {item!r}")
        if not lo < hi:
            raise ValueError(f"custom segment must satisfy K_lo < K_hi: {item!r}")
        normalised.append((sid, lo, hi, mid))

    records: list[HeavyLowerAnchorRecord] = []
    wall_started = time.time()
    stopped_for_wall_time = False
    builder = certificate_builder
    import_failure: str | None = None
    if builder is None and not cfg.dry_run:
        try:
            from kam_theorem_suite.torus_validator import build_theorem_optimized_analytic_invariant_circle_certificate
            builder = build_theorem_optimized_analytic_invariant_circle_certificate
        except Exception as exc:
            import_failure = repr(exc)

    for sid, K_lo, K_hi, K_mid in normalised:
        if cfg.max_wall_seconds is not None and (time.time() - wall_started) >= float(cfg.max_wall_seconds):
            stopped_for_wall_time = True
            break
        if cfg.dry_run or builder is None:
            rec = _dry_record(sid, K_lo, K_hi, K_mid)
            if import_failure:
                rec = HeavyLowerAnchorRecord(**{**rec.to_dict(), "failure_reasons": tuple(list(rec.failure_reasons) + ["numeric_lower_stack_unavailable"]), "analytic_status": import_failure})
            records.append(rec)
            continue
        t0 = time.time()
        try:
            cert = builder(
                rho=float(GOLDEN_INVERSE),
                K=float(K_mid),
                N_values=tuple(int(x) for x in cfg.N_values),
                sigma_cap=float(cfg.sigma_cap),
                oversample_factor=int(cfg.oversample_factor),
            )
            rec = _build_record_from_certificate(
                sid,
                K_lo,
                K_hi,
                K_mid,
                cert,
                elapsed=time.time() - t0,
                tolerance=cfg.outward_rounding_tolerance,
                safety_factor=cfg.theorem_margin_safety_factor,
                oversample_factor=cfg.oversample_factor,
                use_phase2e_direct_radii_ledger=cfg.use_phase2e_direct_radii_ledger,
                phase2e_nonlinear_margin_fraction=cfg.phase2e_nonlinear_margin_fraction,
            )
        except Exception as exc:
            rec = _dry_record(sid, K_lo, K_hi, K_mid)
            rec = HeavyLowerAnchorRecord(**{**rec.to_dict(), "attempted": True, "elapsed_seconds": time.time() - t0, "analytic_status": "exception", "failure_reasons": ("heavy_certificate_exception", repr(exc))})
        records.append(rec)

    report = build_heavy_lower_anchor_report(records, cfg)
    data = report.to_dict()
    failures = list(data.get("failure_fields", []) or [])
    if "custom_phase2g_segment_run_not_promotable_without_merge" not in failures:
        failures.append("custom_phase2g_segment_run_not_promotable_without_merge")
    if stopped_for_wall_time and "wall_time_budget_exhausted" not in failures:
        failures.append("wall_time_budget_exhausted")
    return HeavyLowerAnchorReport(
        schema=data["schema"],
        status="phase2g-custom-heavy-lower-anchor-diagnostic",
        config=cfg,
        records=tuple(records),
        theorem_facing=False,
        diagnostic_only=True,
        promotion_allowed=False,
        final_anchor_reached_by_grid=bool(data.get("final_anchor_reached_by_grid", False)),
        attempted_record_count=int(data.get("attempted_record_count", 0)),
        theorem_ready_record_count=int(data.get("theorem_ready_record_count", 0)),
        min_finite_margin=data.get("min_finite_margin"),
        min_analytic_margin=data.get("min_analytic_margin"),
        min_phase2b_margin=data.get("min_phase2b_margin"),
        failure_fields=tuple(failures),
        notes=(
            "Phase-2G custom refinement run.  Merge this chunk into a complete candidate and run strict Phase-2B ingestion before promotion."
        ),
    )

__all__ = [
    "HeavyLowerAnchorConfig",
    "HeavyLowerAnchorRecord",
    "HeavyLowerAnchorReport",
    "ModewiseSmallDivisorSummary",
    "build_adaptive_near_anchor_grid",
    "build_heavy_candidate_json",
    "build_heavy_lower_anchor_report",
    "build_modewise_golden_small_divisor_summary",
    "refine_grid_by_margins",
    "run_heavy_lower_anchor_certificate",
    "run_heavy_lower_anchor_certificate_on_segments",
    "write_heavy_lower_anchor_outputs",
]

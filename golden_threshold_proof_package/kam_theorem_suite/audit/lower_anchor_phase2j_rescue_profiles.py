from __future__ import annotations

"""Phase-2J rescue profiles for failing lower-anchor analytic segments.

The design mirrors the validated-solver methodology used elsewhere in this
project: difficult rows are not treated with a single global proof profile.
Instead, each failing K-segment receives a local profile containing a K-bisection
plan, Fourier-resolution ladder, oversampling ladder, sigma-cap sweep, radius
retry metadata, and predictive-center policy.  The profile is a *plan* for a
future theorem-grade rerun; it never changes any candidate row or marks a row as
certified.
"""

from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence
import math


@dataclass(frozen=True)
class Phase2JRescueProfile:
    name: str
    regime: str
    n_values: tuple[int, ...]
    oversample_factors: tuple[int, ...]
    sigma_caps: tuple[float, ...]
    split_count: int
    overlap: float
    max_wall_seconds: float
    predictive_center_policy: str
    high_precision_dps: int
    radius_ladder: tuple[float, ...]
    refinement_rounds: int
    notes: str

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["n_values"] = list(self.n_values)
        data["oversample_factors"] = list(self.oversample_factors)
        data["sigma_caps"] = list(self.sigma_caps)
        data["radius_ladder"] = list(self.radius_ladder)
        return data

    @property
    def n_values_csv(self) -> str:
        return ",".join(str(int(x)) for x in self.n_values)


def _finite_float(value: Any, default: float = 0.0) -> float:
    try:
        out = float(value)
    except Exception:
        return float(default)
    return out if math.isfinite(out) else float(default)


def infer_k_regime(K_mid: float) -> str:
    """Classify a lower-anchor segment by proximity to the final critical anchor."""

    k = float(K_mid)
    if k < 0.93:
        return "early"
    if k < 0.970:
        return "middle"
    if k < 0.97158:
        return "near_critical"
    return "endpoint"


def build_profile_for_failure(row: Mapping[str, Any], *, dominant_failure_term: str | None = None) -> Phase2JRescueProfile:
    """Return an old-solver-style rescue profile for one failed segment.

    The values are deliberately conservative and local.  Tail-dominated rows get
    higher resolution and a broader sigma sweep; overlap/localization failures
    get more K-splitting; residual-dominated rows get more predictive refinement
    and resolution escalation.  These choices are emitted as auditable metadata
    and command scripts rather than as theorem claims.
    """

    K_mid = _finite_float(row.get("K_mid", 0.5 * (_finite_float(row.get("K_lo")) + _finite_float(row.get("K_hi")))))
    K_lo = _finite_float(row.get("K_lo"))
    K_hi = _finite_float(row.get("K_hi"))
    width = max(0.0, K_hi - K_lo)
    regime = infer_k_regime(K_mid)
    dominant = str(dominant_failure_term or row.get("dominant_failure_term") or "unknown")

    if regime == "early":
        n_values = (128, 192, 256, 384)
        overs = (16, 24)
        sigmas = (0.02, 0.01, 0.005)
        split = 2
        dps = 160
        rounds = 2
        max_wall = 1200.0
    elif regime == "middle":
        n_values = (192, 256, 384, 512)
        overs = (16, 24, 32)
        sigmas = (0.02, 0.01, 0.005, 0.0025)
        split = 3
        dps = 180
        rounds = 3
        max_wall = 1800.0
    elif regime == "near_critical":
        n_values = (256, 384, 512, 768)
        overs = (24, 32)
        sigmas = (0.02, 0.01, 0.005, 0.0025, 0.001)
        split = 4
        dps = 220
        rounds = 4
        max_wall = 2400.0
    else:
        n_values = (384, 512, 768, 1024)
        overs = (24, 32, 40)
        sigmas = (0.02, 0.01, 0.005, 0.0025, 0.001, 0.0005)
        split = 6
        dps = 240
        rounds = 5
        max_wall = 3600.0

    if dominant in {"tail_bound_T", "tail_dominated", "tail"}:
        n_values = tuple(sorted(set(n_values + (max(n_values) * 2,))))
        sigmas = tuple(sorted(set(sigmas + (0.00025,))))
        notes = "Tail-dominated failure: increase resolution and sweep smaller analytic strip widths."
    elif dominant in {"residual_Y", "residual_dominated", "residual"}:
        n_values = tuple(sorted(set(n_values + (max(n_values) * 2,))))
        rounds += 1
        notes = "Residual-dominated failure: emphasize predictive refinement and higher resolved-mode accuracy."
    elif dominant in {"linear_defect_Zr", "linear_defect_Z", "linear"}:
        overs = tuple(sorted(set(overs + (48,))))
        notes = "Linear-defect-dominated failure: rerun with stronger oversampling and local radius profiling."
    elif dominant in {"overlap", "overlap_margin"}:
        split = max(split + 1, 4)
        notes = "Overlap failure: insert bridge subsegments before increasing global resolution."
    else:
        notes = "General analytic-margin failure: combine K-localization, sigma sweep, and resolution escalation."

    # Extremely wide intervals should be split even in early regimes; very small
    # endpoint intervals should still get multiple bridge attempts.
    if width > 0.10:
        split = max(split, 3)
    if K_hi >= 0.9715:
        split = max(split, 6)

    overlap = min(1.0e-7, max(1.0e-10, width * 1.0e-3))
    radius_ladder = (0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0)
    return Phase2JRescueProfile(
        name=f"phase2j_{regime}_{dominant}".replace(" ", "_"),
        regime=regime,
        n_values=tuple(int(x) for x in n_values),
        oversample_factors=tuple(int(x) for x in overs),
        sigma_caps=tuple(float(x) for x in sigmas),
        split_count=int(split),
        overlap=float(overlap),
        max_wall_seconds=float(max_wall),
        predictive_center_policy="previous-certified-segment-plus-local-continuation-extrapolation",
        high_precision_dps=int(dps),
        radius_ladder=radius_ladder,
        refinement_rounds=int(rounds),
        notes=notes,
    )


def subdivide_segment(row: Mapping[str, Any], profile: Phase2JRescueProfile) -> list[dict[str, Any]]:
    """Return overlapped rescue subsegments for a failed segment."""

    K_lo = _finite_float(row.get("K_lo"))
    K_hi = _finite_float(row.get("K_hi"))
    if not K_lo < K_hi:
        return []
    sid = str(row.get("segment_id", "phase2j_failed_segment"))
    split = max(1, int(profile.split_count))
    width = (K_hi - K_lo) / float(split)
    out: list[dict[str, Any]] = []
    for idx in range(split):
        base_lo = K_lo + idx * width
        base_hi = K_lo + (idx + 1) * width
        lo = base_lo - (profile.overlap if idx > 0 else 0.0)
        hi = base_hi + (profile.overlap if idx < split - 1 else 0.0)
        mid = 0.5 * (base_lo + base_hi)
        out.append({
            "parent_segment_id": sid,
            "segment_id": f"{sid}_phase2j_sub{idx:02d}",
            "K_lo": float(lo),
            "K_hi": float(hi),
            "K_mid": float(mid),
            "profile_name": profile.name,
            "regime": profile.regime,
            "overlap": float(profile.overlap),
        })
    return out


__all__ = [
    "Phase2JRescueProfile",
    "build_profile_for_failure",
    "infer_k_regime",
    "subdivide_segment",
]

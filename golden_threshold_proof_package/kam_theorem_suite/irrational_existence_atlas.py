from __future__ import annotations

"""Multi-resolution irrational-circle validation and continuation atlases."""

from dataclasses import asdict, dataclass, field
from typing import Any, Iterable, Sequence

import numpy as np

from .standard_map import HarmonicFamily
from .torus_validator import (
    InvariantCircleValidationResult,
    evaluate_trig_interpolant_from_coeffs,
    solve_invariant_circle_graph,
    spectral_coefficients_from_samples,
    validate_invariant_circle_graph,
)


@dataclass
class ResolutionValidationEntry:
    N: int
    success: bool
    bridge_quality: str
    radius: float
    residual_inf: float
    oversampled_residual_inf: float
    fourier_tail_l2: float
    strip_width_proxy: float | None
    contraction_bound: float
    lambda_value: float
    message: str
    solver_iterations: int
    u: np.ndarray = field(repr=False)
    z: np.ndarray = field(repr=False)

    @classmethod
    def from_validation(cls, val: InvariantCircleValidationResult) -> "ResolutionValidationEntry":
        return cls(
            N=int(val.N), success=bool(val.success), bridge_quality=str(val.bridge_quality),
            radius=float(val.radius), residual_inf=float(val.residual_inf),
            oversampled_residual_inf=float(val.oversampled_residual_inf),
            fourier_tail_l2=float(val.fourier_tail_l2),
            strip_width_proxy=(None if val.strip_width_proxy is None else float(val.strip_width_proxy)),
            contraction_bound=float(val.contraction_bound), lambda_value=float(val.lambda_value),
            message=str(val.message), solver_iterations=int(val.solver_iterations),
            u=np.asarray(val.u, dtype=float), z=np.asarray(val.z, dtype=float),
        )

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["u"] = np.asarray(self.u, dtype=float).tolist()
        d["z"] = np.asarray(self.z, dtype=float).tolist()
        return d


@dataclass
class ResolutionComparison:
    N_coarse: int
    N_fine: int
    coarse_to_fine_l2: float
    coarse_to_fine_inf: float
    fine_to_coarse_l2: float
    fine_to_coarse_inf: float
    oversampled_residual_ratio: float | None
    tail_ratio: float | None
    strip_ratio: float | None
    pair_stable: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class MultiResolutionValidationReport:
    rho: float
    K: float
    family_label: str
    resolutions: list[ResolutionValidationEntry]
    comparisons: list[ResolutionComparison]
    all_success: bool
    finest_success_N: int | None
    stable_success_prefix: int
    success_count: int
    atlas_quality: str
    recommended_quality_floor: str | None
    stability_summary: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["resolutions"] = [r.to_dict() for r in self.resolutions]
        d["comparisons"] = [c.to_dict() for c in self.comparisons]
        return d


@dataclass
class MultiResolutionContinuationStep:
    index: int
    K: float
    atlas_quality: str
    all_success: bool
    finest_success_N: int | None
    recommended_quality_floor: str | None
    stable_success_prefix: int
    success_count: int
    stability_summary: dict[str, Any]
    report: MultiResolutionValidationReport = field(repr=False)

    def to_dict(self) -> dict[str, Any]:
        return {
            "index": int(self.index), "K": float(self.K), "atlas_quality": str(self.atlas_quality),
            "all_success": bool(self.all_success), "finest_success_N": self.finest_success_N,
            "recommended_quality_floor": self.recommended_quality_floor,
            "stable_success_prefix": int(self.stable_success_prefix), "success_count": int(self.success_count),
            "stability_summary": dict(self.stability_summary), "report": self.report.to_dict(),
        }


@dataclass
class MultiResolutionContinuationReport:
    rho: float
    family_label: str
    N_values: list[int]
    K_values: list[float]
    steps: list[MultiResolutionContinuationStep]
    quality_floor: str
    stable_prefix_len: int
    stable_threshold_bracket: tuple[float, float] | None
    last_stable_K: float | None
    first_unstable_K: float | None
    all_stable: bool

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["steps"] = [s.to_dict() for s in self.steps]
        if self.stable_threshold_bracket is not None:
            d["stable_threshold_bracket"] = [float(self.stable_threshold_bracket[0]), float(self.stable_threshold_bracket[1])]
            d["last_stable_before_failure"] = float(self.stable_threshold_bracket[0])
            d["first_unstable_after_success"] = float(self.stable_threshold_bracket[1])
        else:
            d["last_stable_before_failure"] = self.last_stable_K
            d["first_unstable_after_success"] = self.first_unstable_K
        return d


@dataclass
class MultiResolutionExistenceCrossingBridge:
    multiresolution_continuation: dict[str, Any]
    crossing_window: dict[str, Any]
    relation: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "multiresolution_continuation": self.multiresolution_continuation,
            "crossing_window": self.crossing_window,
            "relation": self.relation,
        }


_DEF_STABLE_L2 = 5e-3
_DEF_STABLE_INF = 2e-2


def _family_label(family: HarmonicFamily) -> str:
    if len(family.harmonics) == 1 and family.harmonics[0][1] == 1:
        return "standard-sine"
    return "custom-harmonic"


def _normalize_resolutions(N_values: Iterable[int]) -> list[int]:
    out = sorted({int(N) for N in N_values if int(N) > 0})
    if not out:
        raise ValueError("N_values must contain at least one positive resolution")
    return out


def resample_graph_samples(u: np.ndarray, N_target: int) -> np.ndarray:
    u = np.asarray(u, dtype=float)
    N_target = int(N_target)
    theta = np.arange(N_target, dtype=float) / float(N_target)
    coeffs = spectral_coefficients_from_samples(u)
    vals = evaluate_trig_interpolant_from_coeffs(coeffs, theta)
    out = np.asarray(vals, dtype=float)
    out -= np.mean(out)
    return out


def build_seed_z_from_graph(u: np.ndarray, lambda_value: float, N_target: int) -> np.ndarray:
    up = resample_graph_samples(np.asarray(u, dtype=float), N_target)
    return np.concatenate([up, np.array([float(lambda_value)], dtype=float)])


def _compare_resolutions(coarse: ResolutionValidationEntry, fine: ResolutionValidationEntry, *, rel_radius_scale: float = 25.0) -> ResolutionComparison:
    coarse_on_fine = resample_graph_samples(coarse.u, fine.N)
    fine_on_coarse = resample_graph_samples(fine.u, coarse.N)
    ctf = fine.u - coarse_on_fine
    ftc = fine_on_coarse - coarse.u
    ctf_l2 = float(np.linalg.norm(ctf) / np.sqrt(len(ctf)))
    ctf_inf = float(np.linalg.norm(ctf, ord=np.inf))
    ftc_l2 = float(np.linalg.norm(ftc) / np.sqrt(len(ftc)))
    ftc_inf = float(np.linalg.norm(ftc, ord=np.inf))
    res_ratio = None
    if coarse.oversampled_residual_inf > 0.0 and fine.oversampled_residual_inf > 0.0:
        res_ratio = float(fine.oversampled_residual_inf / coarse.oversampled_residual_inf)
    tail_ratio = None
    if coarse.fourier_tail_l2 > 0.0 and fine.fourier_tail_l2 > 0.0:
        tail_ratio = float(fine.fourier_tail_l2 / coarse.fourier_tail_l2)
    strip_ratio = None
    if coarse.strip_width_proxy and fine.strip_width_proxy and coarse.strip_width_proxy > 0.0:
        strip_ratio = float(fine.strip_width_proxy / coarse.strip_width_proxy)
    l2_tol = max(_DEF_STABLE_L2, rel_radius_scale * max(fine.radius, 0.0))
    inf_tol = max(_DEF_STABLE_INF, 4.0 * rel_radius_scale * max(fine.radius, 0.0))
    pair_stable = coarse.success and fine.success and ctf_l2 <= l2_tol and ctf_inf <= inf_tol and ftc_l2 <= l2_tol and ftc_inf <= inf_tol
    return ResolutionComparison(int(coarse.N), int(fine.N), ctf_l2, ctf_inf, ftc_l2, ftc_inf, res_ratio, tail_ratio, strip_ratio, bool(pair_stable))


def classify_multiresolution_quality(resolutions: Sequence[ResolutionValidationEntry], comparisons: Sequence[ResolutionComparison]) -> tuple[str, str | None, dict[str, Any]]:
    success_count = sum(1 for r in resolutions if r.success)
    if success_count == 0:
        return "failed", None, {"success_count": 0, "stable_pair_count": 0, "finest_bridge_quality": None, "finest_pair_stable": False}
    finest_success = next((r for r in reversed(resolutions) if r.success), None)
    finest_bridge_quality = finest_success.bridge_quality if finest_success is not None else None
    stable_pair_count = sum(1 for c in comparisons if c.pair_stable)
    all_success = all(r.success for r in resolutions)
    all_pairs_stable = len(comparisons) == stable_pair_count
    finest_pair_stable = comparisons[-1].pair_stable if comparisons else bool(finest_success and finest_success.success)
    quality = "weak"
    recommended = None
    if all_success and all_pairs_stable and finest_bridge_quality in {"strong", "moderate"}:
        quality = "strong"
        recommended = finest_bridge_quality
        if finest_bridge_quality == "moderate" and finest_success is not None:
            if finest_success.oversampled_residual_inf > 1e-7 or finest_success.fourier_tail_l2 > 1e-7:
                quality = "moderate"
    elif success_count >= 2 and finest_pair_stable and finest_bridge_quality in {"strong", "moderate"}:
        quality = "moderate"
        recommended = "moderate"
    elif finest_success is not None and finest_success.success:
        quality = "weak"
        recommended = "weak"
    return quality, recommended, {
        "success_count": int(success_count), "stable_pair_count": int(stable_pair_count),
        "finest_bridge_quality": finest_bridge_quality, "finest_pair_stable": bool(finest_pair_stable),
        "all_success": bool(all_success), "all_pairs_stable": bool(all_pairs_stable),
    }


def validate_invariant_circle_multiresolution(rho: float, K: float, family: HarmonicFamily | None = None, *, N_values: Sequence[int] = (64, 96, 128), initial_u: np.ndarray | None = None, initial_z_by_N: dict[int, np.ndarray] | None = None, oversample_factor: int = 4) -> MultiResolutionValidationReport:
    family = family or HarmonicFamily()
    N_grid = _normalize_resolutions(N_values)
    initial_z_by_N = {int(k): np.asarray(v, dtype=float).copy() for k, v in (initial_z_by_N or {}).items()}
    entries: list[ResolutionValidationEntry] = []
    z_prev = None
    u_prev = None
    lam_prev = 0.0
    for N in N_grid:
        if N in initial_z_by_N:
            z0 = initial_z_by_N[N].copy()
        elif z_prev is not None and u_prev is not None:
            z0 = build_seed_z_from_graph(u_prev, lam_prev, N)
        elif initial_u is not None:
            z0 = build_seed_z_from_graph(np.asarray(initial_u, dtype=float), 0.0, N)
        else:
            z0 = None
        solve = solve_invariant_circle_graph(rho, K, family, N=N, z0=z0)
        val = validate_invariant_circle_graph(rho, K, family, N=N, solve_result=solve, oversample_factor=oversample_factor)
        entry = ResolutionValidationEntry.from_validation(val)
        entries.append(entry)
        if entry.success:
            z_prev = entry.z.copy(); u_prev = entry.u.copy(); lam_prev = float(entry.lambda_value)
    comparisons = [_compare_resolutions(c, f) for c, f in zip(entries[:-1], entries[1:])]
    quality, recommended, summary = classify_multiresolution_quality(entries, comparisons)
    stable_prefix = 0
    for ent in entries:
        if ent.success:
            stable_prefix += 1
        else:
            break
    finest_success = next((r.N for r in reversed(entries) if r.success), None)
    return MultiResolutionValidationReport(float(rho), float(K), _family_label(family), entries, comparisons, all(r.success for r in entries), finest_success, stable_prefix, sum(1 for r in entries if r.success), quality, recommended, summary)


def continue_invariant_circle_multiresolution(rho: float, K_values: Sequence[float], family: HarmonicFamily | None = None, *, N_values: Sequence[int] = (64, 96, 128), quality_floor: str = "moderate", initial_z_by_N: dict[int, np.ndarray] | None = None, oversample_factor: int = 4) -> MultiResolutionContinuationReport:
    family = family or HarmonicFamily()
    K_grid = [float(K) for K in K_values]
    if not K_grid:
        raise ValueError("K_values must be non-empty")
    N_grid = _normalize_resolutions(N_values)
    warm_by_N = {int(k): np.asarray(v, dtype=float).copy() for k, v in (initial_z_by_N or {}).items()}
    steps: list[MultiResolutionContinuationStep] = []
    quality_rank = {"failed": 0, "weak": 1, "moderate": 2, "strong": 3}
    floor_rank = quality_rank.get(str(quality_floor), 2)
    for idx, K in enumerate(K_grid):
        report = validate_invariant_circle_multiresolution(rho=rho, K=K, family=family, N_values=N_grid, initial_z_by_N=warm_by_N, oversample_factor=oversample_factor)
        step = MultiResolutionContinuationStep(int(idx), float(K), str(report.atlas_quality), bool(report.all_success), report.finest_success_N, report.recommended_quality_floor, int(report.stable_success_prefix), int(report.success_count), dict(report.stability_summary), report)
        steps.append(step)
        for entry in report.resolutions:
            if entry.success:
                warm_by_N[int(entry.N)] = np.asarray(entry.z, dtype=float).copy()
    stable_prefix_len = 0
    for step in steps:
        if quality_rank.get(step.atlas_quality, 0) >= floor_rank:
            stable_prefix_len += 1
        else:
            break
    stable_bracket = None
    if stable_prefix_len > 0 and stable_prefix_len < len(steps):
        stable_bracket = (steps[stable_prefix_len - 1].K, steps[stable_prefix_len].K)
    last_stable_K = steps[stable_prefix_len - 1].K if stable_prefix_len > 0 else None
    first_unstable_K = steps[stable_prefix_len].K if stable_prefix_len < len(steps) else None
    return MultiResolutionContinuationReport(float(rho), _family_label(family), [int(N) for N in N_grid], K_grid, steps, str(quality_floor), int(stable_prefix_len), stable_bracket, last_stable_K, first_unstable_K, stable_prefix_len == len(steps))


def build_multiresolution_existence_vs_crossing_bridge(*, rho: float, K_values: Sequence[float], N_values: Sequence[int], p: int, q: int, crossing_K_lo: float, crossing_K_hi: float, family: HarmonicFamily | None = None, quality_floor: str = "moderate", target_residue: float = 0.25) -> MultiResolutionExistenceCrossingBridge:
    family = family or HarmonicFamily()
    from .crossing_certificate import certify_unique_crossing_window
    cont = continue_invariant_circle_multiresolution(rho=rho, K_values=K_values, family=family, N_values=N_values, quality_floor=quality_floor)
    crossing = certify_unique_crossing_window(p=p, q=q, K_lo=crossing_K_lo, K_hi=crossing_K_hi, family=family, target_residue=target_residue).to_dict()
    relation = {
        "last_stable_K": cont.last_stable_K,
        "first_unstable_K": cont.first_unstable_K,
        "crossing_window_lo": float(crossing_K_lo),
        "crossing_window_hi": float(crossing_K_hi),
        "separated": bool(cont.last_stable_K is not None and cont.last_stable_K < float(crossing_K_lo)),
        "quality_floor": str(quality_floor),
        "atlas_all_stable": bool(cont.all_stable),
        "stable_prefix_len": int(cont.stable_prefix_len),
    }
    return MultiResolutionExistenceCrossingBridge(cont.to_dict(), crossing, relation)



@dataclass
class MultiResolutionLimitClosureCertificate:
    rho: float
    K: float
    family_label: str
    cross_resolution_consistency_certified: bool
    resolution_cauchy_control_certified: bool
    limit_profile_ready_for_closure: bool
    resolution_gap_margin: float | None
    multiresolution_closure_status: str
    source_report: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_multiresolution_limit_closure_certificate(report: MultiResolutionValidationReport, *, max_pair_inf: float = 2.0e-2) -> MultiResolutionLimitClosureCertificate:
    pair_infs = [float(c.coarse_to_fine_inf) for c in report.comparisons] + [float(c.fine_to_coarse_inf) for c in report.comparisons]
    worst_inf = max(pair_infs) if pair_infs else 0.0
    gap_margin = float(max_pair_inf - worst_inf)
    consistency = bool(report.success_count >= 2 and report.stability_summary.get('stable_pair_count', 0) >= max(1, len(report.comparisons)))
    cauchy = bool(report.success_count >= 2 and gap_margin > 0.0)
    ready = bool(consistency and cauchy and report.atlas_quality in {'strong', 'moderate'})
    if ready:
        status = 'multiresolution-limit-closure-strong'
    elif report.success_count >= 1:
        status = 'multiresolution-limit-closure-partial'
    else:
        status = 'multiresolution-limit-closure-failed'
    return MultiResolutionLimitClosureCertificate(
        rho=float(report.rho),
        K=float(report.K),
        family_label=str(report.family_label),
        cross_resolution_consistency_certified=bool(consistency),
        resolution_cauchy_control_certified=bool(cauchy),
        limit_profile_ready_for_closure=bool(ready),
        resolution_gap_margin=float(gap_margin),
        multiresolution_closure_status=str(status),
        source_report=report.to_dict(),
    )

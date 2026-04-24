from __future__ import annotations

"""Golden-class a-posteriori bridge certificates.

This module is the first serious pivot from the generic proof-bridge/search
machinery toward a theorem-facing *golden* validation package.

It does **not** claim a finished infinite-dimensional KAM theorem. What it does
provide is a more structured lower-side certificate for the golden irrational
class by combining:

1. a validated finite-dimensional collocation certificate for the invariant
   graph equation;
2. explicit golden small-divisor bounds up to the active Fourier cutoff;
3. weighted Fourier norms in an analyticity-strip proxy; and
4. strip-based force-derivative bounds that quantify how large a genuine
   a-posteriori Newton step would have to control.

The output is intentionally honest: it returns theorem-facing constants and a
"bridge status" showing how strong the current evidence is for a future fully
analytic proof.
"""

from dataclasses import asdict, dataclass, field
from typing import Any, Sequence
import math

import numpy as np

from .irrational_existence_atlas import (
    MultiResolutionValidationReport,
    build_multiresolution_limit_closure_certificate,
    validate_invariant_circle_multiresolution,
)
from .standard_map import HarmonicFamily
from .analytic_norms import choose_safe_sigma
from .small_divisors import build_golden_small_divisor_audit
from .torus_validator import (
    InvariantCircleValidationResult,
    build_analytic_invariant_circle_certificate,
    build_infinite_dimensional_closure_witness,
    build_theorem_optimized_analytic_invariant_circle_certificate,
    evaluate_trig_interpolant_from_coeffs,
    oversampled_residual_inf,
    spectral_coefficients_from_samples,
    validate_invariant_circle_graph,
)


_GOLDEN_RHO = (math.sqrt(5.0) - 1.0) / 2.0


@dataclass
class GoldenSmallDivisorEntry:
    k: int
    exact_gap: float
    theoretical_lower_bound: float
    ratio_to_lower_bound: float
    certified_against_lower_bound: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class GoldenAposterioriCertificate:
    rho: float
    K: float
    source: str
    family_label: str
    selected_N: int
    atlas_quality: str | None
    selected_bridge_quality: str
    finite_dimensional_success: bool
    theorem_status: str
    message: str
    sigma_used: float
    sigma_cap: float
    strip_width_proxy: float | None
    weighted_graph_l1: float
    weighted_graph_l2: float
    weighted_residual_l1: float
    weighted_residual_l2: float
    weighted_residual_inf_proxy: float
    tail_bridge_bound_l1: float | None
    tail_bridge_bound_l2: float | None
    finite_radius: float
    finite_eta: float
    finite_B_norm: float
    finite_lipschitz_bound: float
    finite_contraction_bound: float
    finite_radii_margin: float | None
    golden_small_divisor_cutoff: int
    golden_small_divisor_min_exact: float
    golden_small_divisor_min_lower_bound: float
    golden_small_divisor_pass: bool
    cohomological_inverse_bound: float
    strip_dforce_bound: float
    strip_ddforce_bound: float
    cohomological_correction_bound: float
    nonlinear_response_scale: float
    quadratic_remainder_scale: float
    relative_correction_to_graph: float
    analytic_theorem_status: str
    analytic_theorem_margin: float | None
    small_divisor_table: list[GoldenSmallDivisorEntry] = field(default_factory=list)
    source_report: dict[str, Any] | None = field(default=None, repr=False)
    analytic_certificate: dict[str, Any] | None = field(default=None, repr=False)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["small_divisor_table"] = [row.to_dict() for row in self.small_divisor_table]
        return d


@dataclass
class GoldenAposterioriContinuationStep:
    index: int
    K: float
    theorem_status: str
    finite_dimensional_success: bool
    selected_N: int
    selected_bridge_quality: str
    sigma_used: float
    weighted_residual_l1: float
    cohomological_correction_bound: float
    relative_correction_to_graph: float
    certificate: GoldenAposterioriCertificate = field(repr=False)

    def to_dict(self) -> dict[str, Any]:
        return {
            "index": int(self.index),
            "K": float(self.K),
            "theorem_status": str(self.theorem_status),
            "finite_dimensional_success": bool(self.finite_dimensional_success),
            "selected_N": int(self.selected_N),
            "selected_bridge_quality": str(self.selected_bridge_quality),
            "sigma_used": float(self.sigma_used),
            "weighted_residual_l1": float(self.weighted_residual_l1),
            "cohomological_correction_bound": float(self.cohomological_correction_bound),
            "relative_correction_to_graph": float(self.relative_correction_to_graph),
            "certificate": self.certificate.to_dict(),
        }


@dataclass
class GoldenAposterioriContinuationReport:
    rho: float
    family_label: str
    K_values: list[float]
    source: str
    steps: list[GoldenAposterioriContinuationStep]
    success_prefix_len: int
    last_success_K: float | None
    first_nonstrong_K: float | None
    all_success: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "rho": float(self.rho),
            "family_label": str(self.family_label),
            "K_values": [float(K) for K in self.K_values],
            "source": str(self.source),
            "steps": [s.to_dict() for s in self.steps],
            "success_prefix_len": int(self.success_prefix_len),
            "last_success_K": self.last_success_K,
            "first_nonstrong_K": self.first_nonstrong_K,
            "all_success": bool(self.all_success),
        }


def golden_inverse() -> float:
    return float(_GOLDEN_RHO)


def golden_small_divisor_lower_bound(k: int) -> float:
    kk = abs(int(k))
    if kk == 0:
        return float("inf")
    return 4.0 / (math.sqrt(5.0) * kk)


def exact_small_divisor_gap(rho: float, k: int) -> float:
    kk = int(k)
    if kk == 0:
        return float("inf")
    return float(abs(np.exp(2j * np.pi * kk * float(rho)) - 1.0))


def build_golden_small_divisor_table(max_k: int, *, rho: float | None = None) -> list[GoldenSmallDivisorEntry]:
    rho = float(golden_inverse() if rho is None else rho)
    out: list[GoldenSmallDivisorEntry] = []
    for k in range(1, int(max_k) + 1):
        exact = exact_small_divisor_gap(rho, k)
        lb = golden_small_divisor_lower_bound(k)
        ratio = float(exact / lb) if lb > 0.0 else float("inf")
        out.append(GoldenSmallDivisorEntry(
            k=int(k),
            exact_gap=float(exact),
            theoretical_lower_bound=float(lb),
            ratio_to_lower_bound=float(ratio),
            certified_against_lower_bound=bool(exact + 1e-14 >= lb),
        ))
    return out


def _family_label(family: HarmonicFamily) -> str:
    if len(family.harmonics) == 1 and family.harmonics[0][1] == 1:
        return "standard-sine"
    return "custom-harmonic"


def choose_safe_sigma(*, strip_width_proxy: float | None, sigma_cap: float = 0.04, fraction: float = 0.5, floor: float = 1e-4) -> float:
    if strip_width_proxy is None or not np.isfinite(strip_width_proxy) or strip_width_proxy <= 0.0:
        return float(min(max(floor, sigma_cap * 0.25), sigma_cap))
    return float(min(sigma_cap, max(floor, fraction * float(strip_width_proxy))))


def weighted_fourier_norms_from_coeffs(coeffs: np.ndarray, sigma: float) -> tuple[float, float]:
    coeffs = np.asarray(coeffs, dtype=complex)
    N = len(coeffs)
    k = np.fft.fftfreq(N, d=1.0 / N)
    weights = np.exp(2.0 * np.pi * float(sigma) * np.abs(k))
    absw = np.abs(coeffs) * weights
    l1 = float(np.sum(absw))
    l2 = float(np.sqrt(np.sum(absw**2)))
    return l1, l2


def _residual_samples(u: np.ndarray, rho: float, K: float, family: HarmonicFamily, *, lambda_value: float, oversample_factor: int = 8) -> np.ndarray:
    u = np.asarray(u, dtype=float)
    coeffs = spectral_coefficients_from_samples(u)
    M = max(int(oversample_factor) * len(u), len(u))
    theta = np.arange(M, dtype=float) / float(M)
    u_theta = evaluate_trig_interpolant_from_coeffs(coeffs, theta)
    u_plus = evaluate_trig_interpolant_from_coeffs(coeffs, (theta + float(rho)) % 1.0)
    u_minus = evaluate_trig_interpolant_from_coeffs(coeffs, (theta - float(rho)) % 1.0)
    resid = u_plus + u_minus - 2.0 * u_theta - float(K) * family.force(theta + u_theta) - float(lambda_value)
    return np.asarray(resid, dtype=float)


def weighted_residual_norms(u: np.ndarray, rho: float, K: float, family: HarmonicFamily, *, lambda_value: float, sigma: float, oversample_factor: int = 8) -> tuple[float, float, float]:
    resid = _residual_samples(u, rho, K, family, lambda_value=lambda_value, oversample_factor=oversample_factor)
    coeffs = spectral_coefficients_from_samples(resid)
    l1, l2 = weighted_fourier_norms_from_coeffs(coeffs, sigma)
    return l1, l2, float(np.linalg.norm(resid, ord=np.inf))


def strip_derivative_bound(family: HarmonicFamily, sigma: float, *, order: int = 1) -> float:
    sigma = float(max(0.0, sigma))
    total = 0.0
    for amp, mode, _phase in family.harmonics:
        mode = int(mode)
        base = abs(float(amp)) * math.exp(2.0 * math.pi * mode * sigma)
        if order == 1:
            total += base
        elif order == 2:
            total += base * (2.0 * math.pi * mode)
        else:
            raise ValueError("order must be 1 or 2")
    return float(total)


def tail_bridge_bound_from_proxy(coeffs: np.ndarray, *, sigma_used: float, strip_width_proxy: float | None) -> tuple[float | None, float | None]:
    coeffs = np.asarray(coeffs, dtype=complex)
    if strip_width_proxy is None or not np.isfinite(strip_width_proxy) or strip_width_proxy <= sigma_used:
        return None, None
    N = len(coeffs)
    half = max(1, N // 2)
    k = np.fft.fftfreq(N, d=1.0 / N)
    abs_k = np.abs(k)
    mags = np.abs(coeffs)
    safe = float(strip_width_proxy)
    C = float(np.max(mags * np.exp(2.0 * np.pi * safe * abs_k)))
    delta = safe - float(sigma_used)
    if delta <= 0.0:
        return None, None
    # Two-sided geometric tail for modes strictly beyond the represented band.
    rho = math.exp(-2.0 * math.pi * delta)
    start = half + 1
    if start <= 0 or rho >= 1.0:
        return None, None
    tail_l1 = 2.0 * C * math.exp(-2.0 * math.pi * delta * start) / (1.0 - rho)
    tail_l2 = math.sqrt(2.0) * C * math.exp(-2.0 * math.pi * delta * start) / math.sqrt(1.0 - rho * rho)
    return float(tail_l1), float(tail_l2)


def _select_validation_from_multiresolution(report: MultiResolutionValidationReport) -> InvariantCircleValidationResult:
    best = None
    for entry in report.resolutions:
        if entry.success:
            best = entry
    if best is None:
        best = report.resolutions[-1]
    return InvariantCircleValidationResult(
        rho=float(report.rho),
        K=float(report.K),
        N=int(best.N),
        success=bool(best.success),
        message=str(best.message),
        radius=float(best.radius),
        eta=float("nan") if not np.isfinite(best.radius) else float(best.radius),  # overwritten below when possible
        B_norm=float("nan"),
        lipschitz_bound=float("nan"),
        contraction_bound=float(best.contraction_bound),
        residual_inf=float(best.residual_inf),
        residual_l2=float(best.residual_inf),
        lambda_value=float(best.lambda_value),
        mean_u=float(np.mean(best.u)),
        oversampled_residual_inf=float(best.oversampled_residual_inf),
        fourier_tail_l1=float("nan"),
        fourier_tail_l2=float(best.fourier_tail_l2),
        strip_width_proxy=(None if best.strip_width_proxy is None else float(best.strip_width_proxy)),
        solver_iterations=int(best.solver_iterations),
        solver_history=[],
        bridge_quality=str(best.bridge_quality),
        u=np.asarray(best.u, dtype=float),
        z=np.asarray(best.z, dtype=float),
    )


def _choose_status(
    *,
    finite_success: bool,
    atlas_quality: str | None,
    bridge_quality: str,
    finite_margin: float | None,
    golden_small_divisor_pass: bool,
    weighted_residual_l1: float,
    tail_bridge_bound_l1: float | None,
    relative_correction_to_graph: float,
    analytic_theorem_status: str,
    analytic_theorem_margin: float | None,
) -> tuple[str, str]:
    if not finite_success:
        return "failed", "no validated finite-dimensional ball was available for the golden graph equation"
    if not golden_small_divisor_pass:
        return "golden-small-divisor-check-failed", "the explicit golden small-divisor audit failed at the active Fourier cutoff"

    tail = float("inf") if tail_bridge_bound_l1 is None else float(tail_bridge_bound_l1)
    margin_ok = finite_margin is not None and finite_margin > 0.0
    analytic_ok = analytic_theorem_margin is not None and analytic_theorem_margin > 0.0
    atlas_quality = atlas_quality or "single-resolution"
    strong_analytic = analytic_theorem_status == "analytic-torus-bridge-strong"
    moderate_analytic = analytic_theorem_status in {"analytic-torus-bridge-strong", "analytic-torus-bridge-moderate"}
    if atlas_quality in {"strong", "moderate"} and bridge_quality in {"strong", "moderate"} and margin_ok and analytic_ok and strong_analytic and weighted_residual_l1 <= 1e-6 and tail <= 1e-6 and relative_correction_to_graph <= 1e-3:
        return "golden-aposteriori-bridge-strong", "validated collocation ball plus golden small-divisor control and analytic-strip defect/tail diagnostics close in a strong theorem-facing regime"
    if bridge_quality in {"strong", "moderate"} and margin_ok and moderate_analytic and weighted_residual_l1 <= 1e-4 and relative_correction_to_graph <= 1e-2:
        return "golden-aposteriori-bridge-moderate", "validated collocation ball with explicit golden small-divisor control and analytic-strip theorem constants in a moderate regime"
    return "golden-aposteriori-bridge-weak", "validated finite-dimensional golden certificate available, but the strip/tail bridge to a full analytic theorem remains weak"


def build_golden_aposteriori_certificate(
    K: float,
    family: HarmonicFamily | None = None,
    *,
    rho: float | None = None,
    N: int = 128,
    N_values: Sequence[int] = (64, 96, 128),
    sigma_cap: float = 0.04,
    use_multiresolution: bool = True,
    oversample_factor: int = 8,
) -> GoldenAposterioriCertificate:
    family = family or HarmonicFamily()
    rho = float(golden_inverse() if rho is None else rho)

    atlas_report: MultiResolutionValidationReport | None = None
    atlas_quality: str | None = None
    if use_multiresolution:
        atlas_report = validate_invariant_circle_multiresolution(
            rho=rho,
            K=float(K),
            family=family,
            N_values=N_values,
            oversample_factor=max(4, int(oversample_factor // 2)),
        )
        atlas_quality = str(atlas_report.atlas_quality)
        selected = atlas_report.resolutions[-1]
        for entry in atlas_report.resolutions:
            if entry.success:
                selected = entry
        val = validate_invariant_circle_graph(
            rho=rho,
            K=float(K),
            family=family,
            N=int(selected.N),
            z0=np.asarray(selected.z, dtype=float),
            oversample_factor=oversample_factor,
        )
        source = "multiresolution"
    else:
        val = validate_invariant_circle_graph(
            rho=rho,
            K=float(K),
            family=family,
            N=int(N),
            oversample_factor=oversample_factor,
        )
        source = "single-resolution"

    analytic_cert = build_analytic_invariant_circle_certificate(
        rho=rho, K=float(K), family=family, N=int(val.N), sigma_cap=sigma_cap, oversample_factor=oversample_factor, z0=np.asarray(val.z, dtype=float),
    )
    sigma_used = float(analytic_cert.sigma_used)
    graph_l1 = float(analytic_cert.strip_profile.weighted_l1)
    graph_l2 = float(analytic_cert.strip_profile.weighted_l2)
    res_l1 = float(analytic_cert.defect_report.weighted_l1)
    res_l2 = float(analytic_cert.defect_report.weighted_l2)
    res_inf = float(analytic_cert.defect_report.residual_inf)
    tail_l1 = analytic_cert.tail_bound.tail_l1
    tail_l2 = analytic_cert.tail_bound.tail_l2

    cutoff = max(1, int(val.N // 2))
    small_divisor_audit = build_golden_small_divisor_audit(cutoff, rho=rho)
    small_divisors = build_golden_small_divisor_table(cutoff, rho=rho)
    min_exact = float(small_divisor_audit.min_exact_gap)
    min_lb = float(small_divisor_audit.min_lower_bound if small_divisor_audit.min_lower_bound is not None else 0.0)
    golden_pass = bool(small_divisor_audit.lower_bound_pass)
    cohomology_bound = float(small_divisor_audit.cohomological_inverse_bound)

    d1 = strip_derivative_bound(family, sigma_used, order=1)
    d2 = strip_derivative_bound(family, sigma_used, order=2)
    correction = cohomology_bound * res_l1
    nonlinear_response = cohomology_bound * abs(float(K)) * d1
    quadratic_scale = cohomology_bound * abs(float(K)) * d2
    rel_corr = float(correction / max(graph_l1, 1e-16))

    margin = analytic_cert.finite_radii_margin

    status, message = _choose_status(
        finite_success=bool(val.success),
        atlas_quality=atlas_quality,
        bridge_quality=str(val.bridge_quality),
        finite_margin=margin,
        golden_small_divisor_pass=golden_pass,
        weighted_residual_l1=float(res_l1),
        tail_bridge_bound_l1=tail_l1,
        relative_correction_to_graph=rel_corr,
        analytic_theorem_status=str(analytic_cert.theorem_status),
        analytic_theorem_margin=analytic_cert.theorem_margin,
    )

    return GoldenAposterioriCertificate(
        rho=float(rho),
        K=float(K),
        source=str(source),
        family_label=_family_label(family),
        selected_N=int(val.N),
        atlas_quality=atlas_quality,
        selected_bridge_quality=str(val.bridge_quality),
        finite_dimensional_success=bool(val.success),
        theorem_status=str(status),
        message=str(message),
        sigma_used=float(sigma_used),
        sigma_cap=float(sigma_cap),
        strip_width_proxy=(None if val.strip_width_proxy is None else float(val.strip_width_proxy)),
        weighted_graph_l1=float(graph_l1),
        weighted_graph_l2=float(graph_l2),
        weighted_residual_l1=float(res_l1),
        weighted_residual_l2=float(res_l2),
        weighted_residual_inf_proxy=float(res_inf),
        tail_bridge_bound_l1=(None if tail_l1 is None else float(tail_l1)),
        tail_bridge_bound_l2=(None if tail_l2 is None else float(tail_l2)),
        finite_radius=float(val.radius),
        finite_eta=float(val.eta),
        finite_B_norm=float(val.B_norm),
        finite_lipschitz_bound=float(val.lipschitz_bound),
        finite_contraction_bound=float(val.contraction_bound),
        finite_radii_margin=(None if margin is None else float(margin)),
        golden_small_divisor_cutoff=int(cutoff),
        golden_small_divisor_min_exact=float(min_exact),
        golden_small_divisor_min_lower_bound=float(min_lb),
        golden_small_divisor_pass=bool(golden_pass),
        cohomological_inverse_bound=float(cohomology_bound),
        strip_dforce_bound=float(d1),
        strip_ddforce_bound=float(d2),
        cohomological_correction_bound=float(correction),
        nonlinear_response_scale=float(nonlinear_response),
        quadratic_remainder_scale=float(quadratic_scale),
        relative_correction_to_graph=float(rel_corr),
        analytic_theorem_status=str(analytic_cert.theorem_status),
        analytic_theorem_margin=(None if analytic_cert.theorem_margin is None else float(analytic_cert.theorem_margin)),
        small_divisor_table=small_divisors,
        source_report=(None if atlas_report is None else atlas_report.to_dict()),
        analytic_certificate=analytic_cert.to_dict(),
    )


def continue_golden_aposteriori_certificates(
    K_values: Sequence[float],
    family: HarmonicFamily | None = None,
    *,
    rho: float | None = None,
    N_values: Sequence[int] = (64, 96, 128),
    sigma_cap: float = 0.04,
    use_multiresolution: bool = True,
    oversample_factor: int = 8,
) -> GoldenAposterioriContinuationReport:
    family = family or HarmonicFamily()
    rho = float(golden_inverse() if rho is None else rho)
    grid = [float(K) for K in K_values]
    if not grid:
        raise ValueError("K_values must be non-empty")
    steps: list[GoldenAposterioriContinuationStep] = []
    for idx, K in enumerate(grid):
        cert = build_golden_aposteriori_certificate(
            K=float(K), family=family, rho=rho, N_values=N_values,
            sigma_cap=sigma_cap, use_multiresolution=use_multiresolution,
            oversample_factor=oversample_factor,
        )
        steps.append(GoldenAposterioriContinuationStep(
            index=int(idx),
            K=float(K),
            theorem_status=str(cert.theorem_status),
            finite_dimensional_success=bool(cert.finite_dimensional_success),
            selected_N=int(cert.selected_N),
            selected_bridge_quality=str(cert.selected_bridge_quality),
            sigma_used=float(cert.sigma_used),
            weighted_residual_l1=float(cert.weighted_residual_l1),
            cohomological_correction_bound=float(cert.cohomological_correction_bound),
            relative_correction_to_graph=float(cert.relative_correction_to_graph),
            certificate=cert,
        ))
    success_prefix = 0
    for step in steps:
        if step.theorem_status in {
            "golden-aposteriori-bridge-strong",
            "golden-aposteriori-bridge-moderate",
            "golden-aposteriori-bridge-weak",
        }:
            success_prefix += 1
        else:
            break
    last_success = steps[success_prefix - 1].K if success_prefix > 0 else None
    first_nonstrong = steps[success_prefix].K if success_prefix < len(steps) else None
    return GoldenAposterioriContinuationReport(
        rho=float(rho),
        family_label=_family_label(family),
        K_values=grid,
        source=("multiresolution" if use_multiresolution else "single-resolution"),
        steps=steps,
        success_prefix_len=int(success_prefix),
        last_success_K=last_success,
        first_nonstrong_K=first_nonstrong,
        all_success=bool(success_prefix == len(steps)),
    )



@dataclass
class GoldenTheoremIIIFinalCertificate:
    rho: float
    family_label: str
    certified_below_threshold_interval: list[float] | None
    local_aposteriori_certificate: dict[str, Any]
    infinite_dimensional_closure_witness: dict[str, Any]
    multiresolution_limit_closure: dict[str, Any] | None
    continuation_closure: dict[str, Any]
    lower_neighborhood_closure: dict[str, Any]
    analytic_invariant_circle_exists: bool
    theorem_iii_final_status: str
    residual_theorem_iii_burden: list[str]
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_golden_theorem_iii_final_certificate(
    base_K_values: Sequence[float],
    family: HarmonicFamily | None = None,
    *,
    rho: float | None = None,
    N_values: Sequence[int] = (64, 96, 128),
    sigma_cap: float = 0.04,
    use_multiresolution: bool = True,
    oversample_factor: int = 8,
    golden_aposteriori_certificate: dict[str, Any] | None = None,
    infinite_dimensional_closure_witness: dict[str, Any] | None = None,
    continuation_closure_certificate: dict[str, Any] | None = None,
    lower_neighborhood_certificate: dict[str, Any] | None = None,
    multiresolution_limit_closure_certificate: dict[str, Any] | None = None,
) -> GoldenTheoremIIIFinalCertificate:
    family = family or HarmonicFamily()
    rho = float(golden_inverse() if rho is None else rho)
    grid = [float(K) for K in base_K_values]
    if not grid:
        raise ValueError('base_K_values must be non-empty')

    ap_cert = dict(golden_aposteriori_certificate) if golden_aposteriori_certificate is not None else build_golden_aposteriori_certificate(
        K=float(grid[0]), family=family, rho=rho, N_values=N_values, sigma_cap=sigma_cap,
        use_multiresolution=use_multiresolution, oversample_factor=oversample_factor,
    ).to_dict()

    if infinite_dimensional_closure_witness is not None:
        closure = dict(infinite_dimensional_closure_witness)
    else:
        analytic_source = build_theorem_optimized_analytic_invariant_circle_certificate(rho=rho, K=float(grid[0]), family=family, N_values=tuple(sorted({int(ap_cert.get('selected_N', max(N_values))), *[int(x) for x in N_values]})), sigma_cap=sigma_cap, oversample_factor=oversample_factor)
        closure = build_infinite_dimensional_closure_witness(analytic_source).to_dict()

    if continuation_closure_certificate is not None:
        cont = dict(continuation_closure_certificate)
    else:
        from .torus_continuation import continue_invariant_circle_validations, build_torus_continuation_closure_certificate
        cont_report = continue_invariant_circle_validations(rho=rho, K_values=grid, family=family, N=int(ap_cert.get('selected_N', max(N_values))))
        cont = build_torus_continuation_closure_certificate(cont_report).to_dict()

    if lower_neighborhood_certificate is not None:
        lower = dict(lower_neighborhood_certificate)
    else:
        from .golden_lower_neighborhood_stability import build_golden_lower_neighborhood_stability_certificate, build_golden_lower_theorem_neighborhood_certificate
        lower_base = build_golden_lower_neighborhood_stability_certificate(grid, family=family, rho=rho, resolution_sets=(tuple(int(x) for x in N_values),))
        lower = build_golden_lower_theorem_neighborhood_certificate(lower_base).to_dict()

    if multiresolution_limit_closure_certificate is not None:
        multires = dict(multiresolution_limit_closure_certificate)
    elif use_multiresolution:
        mr = validate_invariant_circle_multiresolution(rho=rho, K=float(grid[0]), family=family, N_values=N_values, oversample_factor=max(4, int(oversample_factor // 2)))
        multires = build_multiresolution_limit_closure_certificate(mr).to_dict()
    else:
        multires = None

    interval = None
    lower_interval = (lower.get('certified_existence_interval') or lower.get('stable_lower_interval')) if isinstance(lower, dict) else None
    cont_interval = cont.get('continuation_interval') if isinstance(cont, dict) else None
    if isinstance(lower_interval, Sequence) and len(lower_interval) == 2 and isinstance(cont_interval, Sequence) and len(cont_interval) == 2:
        lo = max(float(lower_interval[0]), float(cont_interval[0]))
        hi = min(float(lower_interval[1]), float(cont_interval[1]))
        if hi >= lo:
            interval = [float(lo), float(hi)]
    elif isinstance(lower_interval, Sequence) and len(lower_interval) == 2:
        interval = [float(lower_interval[0]), float(lower_interval[1])]
    elif isinstance(cont_interval, Sequence) and len(cont_interval) == 2:
        interval = [float(cont_interval[0]), float(cont_interval[1])]

    burdens = []
    if not closure.get('resolved_mode_validation_certified', False):
        burdens.append('resolved_mode_validation_certified')
    if not closure.get('tail_closure_certified', False):
        burdens.append('tail_closure_certified')
    if not closure.get('small_divisor_closure_certified', False):
        burdens.append('small_divisor_closure_certified')
    if not closure.get('invariance_defect_closure_certified', False):
        burdens.append('invariance_defect_closure_certified')
    if multires is not None and not multires.get('limit_profile_ready_for_closure', False):
        burdens.append('multiresolution_limit_closure')
    if not cont.get('all_steps_locally_closed', False):
        burdens.append('continuation_closure')
    if not lower.get('lower_interval_certified', False):
        burdens.append('lower_interval_certified')

    final = bool(not burdens and interval is not None)
    if final:
        status = 'golden-theorem-iii-final-strong'
        notes = 'The lower-side a-posteriori package, infinite-dimensional closure witness, continuation closure, and lower neighborhood all close in the final theorem-facing regime.'
    elif closure.get('resolved_mode_validation_certified', False):
        status = 'golden-theorem-iii-infinite-dimensional-closure-incomplete'
        notes = 'The lower-side front is strong, but at least one infinite-dimensional closure or interval-level witness remains incomplete.'
    else:
        status = 'golden-theorem-iii-front-only'
        notes = 'The lower-side front does not yet close beyond the finite validator / a-posteriori shell.'

    return GoldenTheoremIIIFinalCertificate(
        rho=float(rho),
        family_label=_family_label(family),
        certified_below_threshold_interval=interval,
        local_aposteriori_certificate=ap_cert,
        infinite_dimensional_closure_witness=closure,
        multiresolution_limit_closure=multires,
        continuation_closure=cont,
        lower_neighborhood_closure=lower,
        analytic_invariant_circle_exists=bool(final),
        theorem_iii_final_status=str(status),
        residual_theorem_iii_burden=[str(x) for x in burdens],
        notes=str(notes),
    )


def build_golden_theorem_iii_certificate(*args, **kwargs) -> GoldenTheoremIIIFinalCertificate:
    return build_golden_theorem_iii_final_certificate(*args, **kwargs)

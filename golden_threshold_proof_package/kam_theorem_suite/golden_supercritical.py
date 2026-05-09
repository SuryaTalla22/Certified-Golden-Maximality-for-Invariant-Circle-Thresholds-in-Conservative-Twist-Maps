from __future__ import annotations

from dataclasses import asdict, dataclass
from fractions import Fraction
from typing import Any, Sequence

from .arithmetic_exact import convergents_from_cf
from .asymptotic_upper_ladder_audit import audit_refined_upper_ladder_asymptotics
from .golden_aposteriori import continue_golden_aposteriori_certificates, golden_inverse
from .obstruction_atlas import ApproximantWindowSpec
from .standard_map import HarmonicFamily
from .two_sided_irrational_atlas import build_rational_upper_ladder
from .upper_ladder_refinement import refine_rational_upper_ladder

"""Golden-class supercritical obstruction sharpener.

This module is the upper-side counterpart to :mod:`golden_aposteriori`.
It packages the strongest *golden-specific* supercritical obstruction object the
current proof bridge can build honestly:

1. generate a ladder of genuine golden convergents,
2. certify crossing windows and later hyperbolic bands on that ladder,
3. refine the resulting upper object using crossing-cluster refinement, and
4. audit its stabilization on high-denominator tails.

The result is a theorem-facing golden supercritical obstruction certificate.
It is still not a finished irrational nonexistence theorem.
"""


@dataclass(frozen=True)
class GoldenConvergentSpec:
    p: int
    q: int
    label: str
    rho: float
    rho_error: float
    crossing_K_lo: float
    crossing_K_hi: float
    band_search_lo: float
    band_search_hi: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_approximant_window_spec(self) -> ApproximantWindowSpec:
        return ApproximantWindowSpec(
            p=int(self.p),
            q=int(self.q),
            crossing_K_lo=float(self.crossing_K_lo),
            crossing_K_hi=float(self.crossing_K_hi),
            band_search_lo=float(self.band_search_lo),
            band_search_hi=float(self.band_search_hi),
            label=str(self.label),
        )


@dataclass
class GoldenSupercriticalObstructionCertificate:
    rho: float
    family_label: str
    target_residue: float
    crossing_center: float
    crossing_half_width: float
    band_offset: float
    band_width: float
    generated_convergents: list[dict[str, Any]]
    ladder: dict[str, Any]
    refined: dict[str, Any]
    asymptotic_audit: dict[str, Any]
    selected_upper_source: str
    selected_upper_lo: float | None
    selected_upper_hi: float | None
    selected_upper_width: float | None
    earliest_hyperbolic_band_lo: float | None
    latest_hyperbolic_band_hi: float | None
    successful_crossing_count: int
    successful_band_count: int
    theorem_status: str
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class GoldenTwoSidedBridgeCertificate:
    rho: float
    family_label: str
    lower_side: dict[str, Any]
    upper_side: dict[str, Any]
    relation: dict[str, Any]
    theorem_status: str
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


_GOLDEN_CROSSING_CENTER = 0.971635406


def _family_label(family: HarmonicFamily) -> str:
    if len(family.harmonics) == 1 and family.harmonics[0][1] == 1:
        return "standard-sine"
    return "custom-harmonic"


def _golden_convergents(n_terms: int) -> list[Fraction]:
    if n_terms < 1:
        raise ValueError("n_terms must be >= 1")
    cf = [0] + [1] * (int(n_terms) + 2)
    convs = convergents_from_cf(cf)
    out: list[Fraction] = []
    seen: set[tuple[int, int]] = set()
    for frac in convs:
        key = (int(frac.numerator), int(frac.denominator))
        if frac.denominator <= 0 or key in seen:
            continue
        seen.add(key)
        out.append(frac)
    return out


def generate_golden_convergent_specs(
    *,
    rho: float | None = None,
    n_terms: int = 10,
    keep_last: int = 6,
    min_q: int = 5,
    max_q: int | None = None,
    crossing_center: float = _GOLDEN_CROSSING_CENTER,
    crossing_half_width: float = 2.5e-3,
    band_offset: float = 5.5e-2,
    band_width: float = 3.0e-2,
) -> list[GoldenConvergentSpec]:
    rho = float(golden_inverse() if rho is None else rho)
    convs = [f for f in _golden_convergents(n_terms) if int(f.denominator) >= int(min_q)]
    if max_q is not None:
        convs = [f for f in convs if int(f.denominator) <= int(max_q)]
    if keep_last > 0 and len(convs) > int(keep_last):
        convs = convs[-int(keep_last):]
    out: list[GoldenConvergentSpec] = []
    for frac in convs:
        p = int(frac.numerator)
        q = int(frac.denominator)
        out.append(
            GoldenConvergentSpec(
                p=p,
                q=q,
                label=f"gold-{p}/{q}",
                rho=float(frac),
                rho_error=float(abs(float(frac) - rho)),
                crossing_K_lo=float(crossing_center - crossing_half_width),
                crossing_K_hi=float(crossing_center + crossing_half_width),
                band_search_lo=float(crossing_center + band_offset),
                band_search_hi=float(crossing_center + band_offset + band_width),
            )
        )
    return out


def _pick_upper_object(ladder: dict[str, Any], refined: dict[str, Any], audit: dict[str, Any]) -> tuple[str, float | None, float | None, float | None]:
    if audit.get("audited_upper_lo") is not None and audit.get("audited_upper_hi") is not None:
        lo = float(audit["audited_upper_lo"])
        hi = float(audit["audited_upper_hi"])
        return "asymptotic-upper-ladder", lo, hi, float(hi - lo)
    if refined.get("best_refined_crossing_lower_bound") is not None and refined.get("best_refined_crossing_upper_bound") is not None:
        lo = float(refined["best_refined_crossing_lower_bound"])
        hi = float(refined["best_refined_crossing_upper_bound"])
        width = refined.get("best_refined_crossing_width")
        return "refined-upper-ladder", lo, hi, float(width if width is not None else hi - lo)
    if ladder.get("best_crossing_lower_bound") is not None and ladder.get("best_crossing_upper_bound") is not None:
        lo = float(ladder["best_crossing_lower_bound"])
        hi = float(ladder["best_crossing_upper_bound"])
        width = ladder.get("crossing_intersection_width")
        return "raw-upper-ladder", lo, hi, float(width if width is not None else hi - lo)
    return "no-upper-object", None, None, None


def _choose_theorem_status(*, source: str, successful_crossings: int, successful_bands: int, audit_status: str) -> tuple[str, str]:
    if source == "asymptotic-upper-ladder" and successful_crossings >= 3 and successful_bands >= 1 and audit_status in {"asymptotically-stable-upper-ladder", "asymptotically-audited-upper-ladder"}:
        return "golden-supercritical-obstruction-strong", "golden convergent ladder admits a stabilized asymptotic upper object together with at least one sustained hyperbolic band"
    if source in {"asymptotic-upper-ladder", "refined-upper-ladder"} and successful_crossings >= 2:
        return "golden-supercritical-obstruction-moderate", "golden convergent ladder admits a refined or asymptotically audited upper object, but the irrational nonexistence bridge is not yet sharp"
    if source != "no-upper-object" and successful_crossings >= 1:
        return "golden-supercritical-obstruction-weak", "golden convergent ladder supplies an upper-side obstruction object, but it remains local or only weakly coordinated across denominators"
    return "golden-supercritical-obstruction-failed", "golden convergent ladder did not yet close a usable upper-side obstruction object"


def build_golden_supercritical_obstruction_certificate(
    family: HarmonicFamily | None = None,
    *,
    rho: float | None = None,
    n_terms: int = 10,
    keep_last: int = 6,
    min_q: int = 5,
    max_q: int | None = None,
    crossing_center: float = _GOLDEN_CROSSING_CENTER,
    crossing_half_width: float = 2.5e-3,
    band_offset: float = 5.5e-2,
    band_width: float = 3.0e-2,
    target_residue: float = 0.25,
    auto_localize_crossing: bool = False,
    initial_subdivisions: int = 4,
    max_depth: int = 4,
    min_width: float = 5e-4,
    refine_upper_ladder: bool = True,
    asymptotic_min_members: int = 2,
) -> GoldenSupercriticalObstructionCertificate:
    family = family or HarmonicFamily()
    rho = float(golden_inverse() if rho is None else rho)
    specs = generate_golden_convergent_specs(
        rho=rho,
        n_terms=n_terms,
        keep_last=keep_last,
        min_q=min_q,
        max_q=max_q,
        crossing_center=crossing_center,
        crossing_half_width=crossing_half_width,
        band_offset=band_offset,
        band_width=band_width,
    )
    ladder = build_rational_upper_ladder(
        rho=rho,
        specs=[s.to_approximant_window_spec() for s in specs],
        family=family,
        target_residue=target_residue,
        auto_localize_crossing=auto_localize_crossing,
        initial_subdivisions=initial_subdivisions,
        max_depth=max_depth,
        min_width=min_width,
    ).to_dict()
    if refine_upper_ladder:
        refined = refine_rational_upper_ladder(ladder).to_dict()
        audit = audit_refined_upper_ladder_asymptotics(ladder, min_members=asymptotic_min_members).to_dict()
    else:
        refined = {
            "best_refined_crossing_lower_bound": None,
            "best_refined_crossing_upper_bound": None,
            "best_refined_crossing_width": None,
            "refinement_status": "skipped",
        }
        audit = {
            "audited_upper_lo": None,
            "audited_upper_hi": None,
            "audited_upper_width": None,
            "status": "skipped",
        }
    source, up_lo, up_hi, up_w = _pick_upper_object(ladder, refined, audit)
    status, note = _choose_theorem_status(
        source=source,
        successful_crossings=int(ladder.get("successful_crossing_count", 0)),
        successful_bands=int(ladder.get("successful_band_count", 0)),
        audit_status=str(audit.get("status", "failed")),
    )
    notes = f"Golden supercritical obstruction built from {len(specs)} convergents. {note}. This remains an upper-side bridge object for the golden irrational class, not yet a full irrational nonexistence theorem."
    return GoldenSupercriticalObstructionCertificate(
        rho=float(rho),
        family_label=_family_label(family),
        target_residue=float(target_residue),
        crossing_center=float(crossing_center),
        crossing_half_width=float(crossing_half_width),
        band_offset=float(band_offset),
        band_width=float(band_width),
        generated_convergents=[s.to_dict() for s in specs],
        ladder=ladder,
        refined=refined,
        asymptotic_audit=audit,
        selected_upper_source=str(source),
        selected_upper_lo=up_lo,
        selected_upper_hi=up_hi,
        selected_upper_width=up_w,
        earliest_hyperbolic_band_lo=(None if ladder.get("earliest_band_lo") is None else float(ladder["earliest_band_lo"])),
        latest_hyperbolic_band_hi=(None if ladder.get("latest_band_hi") is None else float(ladder["latest_band_hi"])),
        successful_crossing_count=int(ladder.get("successful_crossing_count", 0)),
        successful_band_count=int(ladder.get("successful_band_count", 0)),
        theorem_status=str(status),
        notes=notes,
    )


def build_golden_two_sided_bridge_certificate(
    K_values: Sequence[float],
    family: HarmonicFamily | None = None,
    *,
    rho: float | None = None,
    N_values: Sequence[int] = (64, 96, 128),
    sigma_cap: float = 0.04,
    use_multiresolution: bool = True,
    oversample_factor: int = 8,
    n_terms: int = 10,
    keep_last: int = 6,
    min_q: int = 5,
    max_q: int | None = None,
    crossing_center: float = _GOLDEN_CROSSING_CENTER,
    crossing_half_width: float = 2.5e-3,
    band_offset: float = 5.5e-2,
    band_width: float = 3.0e-2,
    target_residue: float = 0.25,
    auto_localize_crossing: bool = False,
    initial_subdivisions: int = 4,
    max_depth: int = 4,
    min_width: float = 5e-4,
    refine_upper_ladder: bool = True,
    asymptotic_min_members: int = 2,
) -> GoldenTwoSidedBridgeCertificate:
    family = family or HarmonicFamily()
    rho = float(golden_inverse() if rho is None else rho)
    lower = continue_golden_aposteriori_certificates(
        K_values=K_values,
        family=family,
        rho=rho,
        N_values=N_values,
        sigma_cap=sigma_cap,
        use_multiresolution=use_multiresolution,
        oversample_factor=oversample_factor,
    ).to_dict()
    upper = build_golden_supercritical_obstruction_certificate(
        family=family,
        rho=rho,
        n_terms=n_terms,
        keep_last=keep_last,
        min_q=min_q,
        max_q=max_q,
        crossing_center=crossing_center,
        crossing_half_width=crossing_half_width,
        band_offset=band_offset,
        band_width=band_width,
        target_residue=target_residue,
        auto_localize_crossing=auto_localize_crossing,
        initial_subdivisions=initial_subdivisions,
        max_depth=max_depth,
        min_width=min_width,
        refine_upper_ladder=refine_upper_ladder,
        asymptotic_min_members=asymptotic_min_members,
    ).to_dict()
    lower_bound = lower.get("last_success_K")
    upper_lo = upper.get("selected_upper_lo")
    upper_hi = upper.get("selected_upper_hi")
    earliest_band_lo = upper.get("earliest_hyperbolic_band_lo")
    band_gap = None if lower_bound is None or earliest_band_lo is None else float(earliest_band_lo) - float(lower_bound)
    corridor_gap = None if lower_bound is None or upper_lo is None else float(upper_lo) - float(lower_bound)
    if lower_bound is not None and upper_lo is not None and float(lower_bound) < float(upper_lo):
        if upper.get("theorem_status") == "golden-supercritical-obstruction-strong":
            status = "golden-two-sided-bridge-strong"
            msg = "golden lower-side a-posteriori continuation and upper-side golden obstruction produce a separated two-sided corridor"
        else:
            status = "golden-two-sided-bridge-moderate"
            msg = "golden lower-side and upper-side certificates produce a separated corridor, but the supercritical side is not yet strong enough for a sharp irrational theorem"
    elif lower_bound is not None and upper_lo is not None:
        status = "golden-two-sided-overlap"
        msg = "golden lower-side and upper-side objects overlap, so the present bridge remains non-sharp"
    elif lower_bound is not None:
        status = "golden-lower-only"
        msg = "only the golden lower-side a-posteriori continuation closed"
    elif upper_lo is not None:
        status = "golden-upper-only"
        msg = "only the golden upper-side obstruction object closed"
    else:
        status = "golden-incomplete"
        msg = "neither side closed enough to produce a usable golden bridge"
    relation = {
        "lower_bound_K": (None if lower_bound is None else float(lower_bound)),
        "upper_object_source": str(upper.get("selected_upper_source", "none")),
        "upper_crossing_lo": (None if upper_lo is None else float(upper_lo)),
        "upper_crossing_hi": (None if upper_hi is None else float(upper_hi)),
        "upper_crossing_width": (None if upper.get("selected_upper_width") is None else float(upper["selected_upper_width"])),
        "gap_to_upper_crossing": corridor_gap,
        "gap_to_earliest_hyperbolic_band": band_gap,
        "lower_success_prefix_len": int(lower.get("success_prefix_len", 0)),
        "upper_successful_crossings": int(upper.get("successful_crossing_count", 0)),
        "upper_successful_bands": int(upper.get("successful_band_count", 0)),
        "status": str(status),
    }
    notes = f"{msg}. This is the current best golden-specific two-sided bridge in the code: a lower a-posteriori continuation object paired with a golden convergent supercritical obstruction sharpener."
    return GoldenTwoSidedBridgeCertificate(
        rho=float(rho),
        family_label=_family_label(family),
        lower_side=lower,
        upper_side=upper,
        relation=relation,
        theorem_status=str(status),
        notes=notes,
    )


__all__ = [
    "GoldenConvergentSpec",
    "GoldenSupercriticalObstructionCertificate",
    "GoldenTwoSidedBridgeCertificate",
    "generate_golden_convergent_specs",
    "build_golden_supercritical_obstruction_certificate",
    "build_golden_two_sided_bridge_certificate",
]

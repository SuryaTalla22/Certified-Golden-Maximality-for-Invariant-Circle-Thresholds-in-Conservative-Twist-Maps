from __future__ import annotations

"""Adaptive supercritical-band certificates for rational periodic branches.

This module strengthens the obstruction side beyond a single local crossing window.
It does **not** claim a finished nonexistence theorem for irrational invariant
circles. Instead, it packages the strongest theorem-like statement that the
current proof bridge can make honestly on the supercritical side:

- a rational branch can be certified to remain hyperbolic on a parameter window;
- that window can be refined adaptively into a contiguous *band* of certified
  supercritical behavior; and
- a local crossing certificate can be connected to a later hyperbolic band to
  produce a more structured breakup narrative than a single barrier window.

The resulting reports are intended for notebooks, examples, and future proof
work. They make it easy to distinguish between

1. a merely local crossing certificate, and
2. a sustained supercritical band in which the chosen rational approximant is
   provably hyperbolic and stays away from the target residue level.
"""

from dataclasses import asdict, dataclass
from typing import Any

from .certification import get_residue_and_derivative_iv
from .crossing_certificate import certify_unique_crossing_window
from .interval_utils import iv_scalar
from .standard_map import HarmonicFamily
from .theorem_iv_band_methodology import get_theorem_iv_band_profile, methodology_localize_hyperbolic_band


@dataclass
class HyperbolicWindowCertificate:
    p: int
    q: int
    K_lo: float
    K_hi: float
    target_residue: float
    residue_interval_lo: float
    residue_interval_hi: float
    abs_residue_interval_lo: float
    abs_residue_interval_hi: float
    g_interval_lo: float
    g_interval_hi: float
    gprime_interval_lo: float
    gprime_interval_hi: float
    trace_interval_lo: float
    trace_interval_hi: float
    trace_abs_lower_bound: float
    hyperbolicity_margin: float
    regime: str
    certified_above_target: bool
    certified_hyperbolic: bool
    tangent_inclusion_success: bool
    branch_tube: dict[str, Any]
    message: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SupercriticalBandReport:
    p: int
    q: int
    K_lo: float
    K_hi: float
    target_residue: float
    initial_subdivisions: int
    max_depth: int
    min_width: float
    accepted_windows: list[dict[str, Any]]
    rejected_windows: list[dict[str, Any]]
    longest_band_lo: float | None
    longest_band_hi: float | None
    longest_band_width: float
    coverage_width: float
    coverage_fraction: float
    status: str
    notes: str

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["best_band"] = None if self.longest_band_lo is None else {
            "K_lo": self.longest_band_lo,
            "K_hi": self.longest_band_hi,
            "width": self.longest_band_width,
        }
        d["certified_band_count"] = len(self.accepted_windows)
        return d


@dataclass
class CrossingToHyperbolicBandBridge:
    p: int
    q: int
    crossing_window_input_lo: float
    crossing_window_input_hi: float
    band_search_lo: float
    band_search_hi: float
    target_residue: float
    crossing_certificate: dict[str, Any]
    band_report: dict[str, Any]
    first_supercritical_gap: float | None
    status: str
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _trace_interval_from_residue_interval(res_lo: float, res_hi: float) -> tuple[float, float]:
    lo = 2.0 - 4.0 * float(res_hi)
    hi = 2.0 - 4.0 * float(res_lo)
    return float(lo), float(hi)


def _trace_abs_lower_bound(tr_lo: float, tr_hi: float) -> float:
    if tr_lo <= 0.0 <= tr_hi:
        return 0.0
    return min(abs(tr_lo), abs(tr_hi))


def _classify_regime(res_lo: float, res_hi: float) -> tuple[str, bool]:
    if res_hi < 0.0:
        return "negative-hyperbolic", True
    if res_lo > 1.0:
        return "positive-hyperbolic", True
    if res_lo > 0.0 and res_hi < 1.0:
        return "elliptic", False
    return "mixed", False


def certify_hyperbolic_window(
    p: int,
    q: int,
    K_lo: float,
    K_hi: float,
    family: HarmonicFamily | None = None,
    *,
    x_guess=None,
    target_residue: float = 0.25,
) -> HyperbolicWindowCertificate:
    """Certify one supercritical parameter window on a rational branch.

    The certificate is intentionally modest: it records whether the chosen
    rational branch is rigorously enclosed on the window and whether the Greene
    residue interval lies entirely in a hyperbolic regime (``R<0`` or ``R>1``).
    This is stronger than the earlier barrier-band label because it records a
    sustained hyperbolic window, not only a local side classification.
    """
    family = family or HarmonicFamily()
    summary = get_residue_and_derivative_iv(
        p=p,
        q=q,
        K_iv=iv_scalar(K_lo, K_hi),
        family=family,
        x_guess=x_guess,
        target_residue=target_residue,
    )
    res_lo = float(summary["residue_interval_lo"])
    res_hi = float(summary["residue_interval_hi"])
    abs_lo = float(summary["abs_residue_interval_lo"])
    abs_hi = float(summary["abs_residue_interval_hi"])
    tr_lo, tr_hi = _trace_interval_from_residue_interval(res_lo, res_hi)
    tr_abs_lb = _trace_abs_lower_bound(tr_lo, tr_hi)
    regime, certified_hyp = _classify_regime(res_lo, res_hi)
    above_target = abs_lo > float(target_residue)
    return HyperbolicWindowCertificate(
        p=int(p),
        q=int(q),
        K_lo=float(K_lo),
        K_hi=float(K_hi),
        target_residue=float(target_residue),
        residue_interval_lo=res_lo,
        residue_interval_hi=res_hi,
        abs_residue_interval_lo=abs_lo,
        abs_residue_interval_hi=abs_hi,
        g_interval_lo=float(summary["g_interval_lo"]),
        g_interval_hi=float(summary["g_interval_hi"]),
        gprime_interval_lo=float(summary["gprime_interval_lo"]),
        gprime_interval_hi=float(summary["gprime_interval_hi"]),
        trace_interval_lo=tr_lo,
        trace_interval_hi=tr_hi,
        trace_abs_lower_bound=tr_abs_lb,
        hyperbolicity_margin=float(tr_abs_lb - 2.0),
        regime=regime,
        certified_above_target=bool(above_target),
        certified_hyperbolic=bool(certified_hyp),
        tangent_inclusion_success=bool(summary["tangent_inclusion_success"]),
        branch_tube=dict(summary["branch_tube"]),
        message=str(summary["message"]),
    )


def _merge_window_dicts(windows: list[dict[str, Any]], *, tol: float = 1e-12) -> list[dict[str, Any]]:
    if not windows:
        return []
    windows = sorted(windows, key=lambda w: (w["K_lo"], w["K_hi"]))
    merged: list[dict[str, Any]] = [dict(windows[0])]
    for w in windows[1:]:
        last = merged[-1]
        same_regime = w.get("regime") == last.get("regime")
        if same_regime and float(w["K_lo"]) <= float(last["K_hi"]) + tol:
            last["K_hi"] = max(float(last["K_hi"]), float(w["K_hi"]))
            last["residue_interval_lo"] = min(float(last["residue_interval_lo"]), float(w["residue_interval_lo"]))
            last["residue_interval_hi"] = max(float(last["residue_interval_hi"]), float(w["residue_interval_hi"]))
            last["abs_residue_interval_lo"] = min(float(last["abs_residue_interval_lo"]), float(w["abs_residue_interval_lo"]))
            last["abs_residue_interval_hi"] = max(float(last["abs_residue_interval_hi"]), float(w["abs_residue_interval_hi"]))
            last["trace_abs_lower_bound"] = min(float(last["trace_abs_lower_bound"]), float(w["trace_abs_lower_bound"]))
            last["hyperbolicity_margin"] = min(float(last["hyperbolicity_margin"]), float(w["hyperbolicity_margin"]))
            last.setdefault("merged_count", 1)
            last["merged_count"] += int(w.get("merged_count", 1))
        else:
            merged.append(dict(w))
    return merged


def build_supercritical_band_report(
    p: int,
    q: int,
    K_lo: float,
    K_hi: float,
    family: HarmonicFamily | None = None,
    *,
    x_guess=None,
    target_residue: float = 0.25,
    initial_subdivisions: int = 4,
    max_depth: int = 4,
    min_width: float = 5e-4,
    use_seed_propagation: bool = True,
    use_methodology_frontend: bool = True,
    crossing_root_hi: float | None = None,
    previous_entry_dicts: list[dict[str, Any]] | None = None,
    skip_recursive_scan_on_success: bool = True,
) -> SupercriticalBandReport:
    """Adaptively certify a sustained supercritical hyperbolic band.

    The input interval is split coarsely first. Any subwindow that is not yet
    certified hyperbolic is recursively bisected until it either certifies or
    reaches the stopping depth/width. Accepted windows are merged into
    contiguous bands of the same hyperbolic regime.
    """
    family = family or HarmonicFamily()
    K_lo = float(K_lo)
    K_hi = float(K_hi)
    if K_lo > K_hi:
        K_lo, K_hi = K_hi, K_lo
    if initial_subdivisions < 1:
        raise ValueError("initial_subdivisions must be >= 1")
    if max_depth < 0:
        raise ValueError("max_depth must be >= 0")

    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    window_cache: dict[tuple[float, float], dict[str, Any]] = {}
    methodology_frontend = None

    if use_methodology_frontend:
        spec = type('BandSpecProxy', (), {'p': int(p), 'q': int(q), 'band_search_lo': float(K_lo), 'band_search_hi': float(K_hi)})()
        methodology_frontend = methodology_localize_hyperbolic_band(spec, family=family, target_residue=target_residue, crossing_root_hi=crossing_root_hi, previous_entry_dicts=previous_entry_dicts, x_guess=x_guess, profile=get_theorem_iv_band_profile(p, q))
        if methodology_frontend.get('proof_ready', False):
            cert = dict(methodology_frontend.get('certificate') or {})
            cert['certification_source'] = 'methodology-local-band'
            accepted.append(cert)
            if skip_recursive_scan_on_success:
                merged = _merge_window_dicts(accepted)
                best = max(merged, key=lambda w: float(w['K_hi']) - float(w['K_lo'])) if merged else None
                longest_lo = None if best is None else float(best['K_lo'])
                longest_hi = None if best is None else float(best['K_hi'])
                longest_width = 0.0 if best is None else float(longest_hi - longest_lo)
                coverage_width = float(sum(float(w['K_hi']) - float(w['K_lo']) for w in merged))
                total_width = max(K_hi - K_lo, 1e-30)
                coverage_fraction = float(coverage_width / total_width)
                return SupercriticalBandReport(p=int(p), q=int(q), K_lo=K_lo, K_hi=K_hi, target_residue=float(target_residue), initial_subdivisions=int(initial_subdivisions), max_depth=int(max_depth), min_width=float(min_width), accepted_windows=merged, rejected_windows=[{'methodology_frontend': methodology_frontend}], longest_band_lo=longest_lo, longest_band_hi=longest_hi, longest_band_width=float(longest_width), coverage_width=float(coverage_width), coverage_fraction=float(coverage_fraction), status='certified-local-band', notes='Methodology front-end certified a theorem-mode local hyperbolic band; broad interval scan skipped to avoid redundant expensive wide-window residue enclosure.')
        elif methodology_frontend.get('fallback_window_lo') is not None and methodology_frontend.get('fallback_window_hi') is not None:
            K_lo = max(K_lo, float(methodology_frontend['fallback_window_lo']))
            K_hi = min(K_hi, float(methodology_frontend['fallback_window_hi']))

    def recurse(a: float, b: float, depth: int, local_guess=None) -> None:
        key = (round(float(a), 15), round(float(b), 15))
        if key in window_cache:
            cert = dict(window_cache[key])
        else:
            cert = certify_hyperbolic_window(
                p=p,
                q=q,
                K_lo=a,
                K_hi=b,
                family=family,
                x_guess=local_guess if local_guess is not None else x_guess,
                target_residue=target_residue,
            ).to_dict()
            window_cache[key] = dict(cert)
        cert["depth"] = int(depth)
        cert["width"] = float(b - a)
        if cert["certified_hyperbolic"] and cert["certified_above_target"]:
            accepted.append(cert)
            return
        if depth >= max_depth or (b - a) <= min_width:
            rejected.append(cert)
            return
        mid = 0.5 * (a + b)
        branch = cert.get("branch_tube", {}) or {}
        left_seed = branch.get("x_left")
        mid_seed = branch.get("x_mid")
        right_seed = branch.get("x_right")
        recurse(a, mid, depth + 1, left_seed if use_seed_propagation and left_seed is not None else (mid_seed if use_seed_propagation else None))
        recurse(mid, b, depth + 1, right_seed if use_seed_propagation and right_seed is not None else (mid_seed if use_seed_propagation else None))

    grid = [K_lo + (K_hi - K_lo) * i / initial_subdivisions for i in range(initial_subdivisions + 1)]
    prev_seed = x_guess
    for a, b in zip(grid[:-1], grid[1:]):
        recurse(float(a), float(b), 0, prev_seed)

    merged = _merge_window_dicts(accepted)
    longest_lo = None
    longest_hi = None
    longest_width = 0.0
    if merged:
        best = max(merged, key=lambda w: float(w["K_hi"]) - float(w["K_lo"]))
        longest_lo = float(best["K_lo"])
        longest_hi = float(best["K_hi"])
        longest_width = float(longest_hi - longest_lo)

    coverage_width = float(sum(float(w["K_hi"]) - float(w["K_lo"]) for w in merged))
    total_width = max(K_hi - K_lo, 1e-30)
    coverage_fraction = float(coverage_width / total_width)
    if merged and coverage_fraction > 0.999:
        status = "certified-full-band"
    elif merged:
        status = "certified-partial-band"
    else:
        status = "no-certified-band"

    notes = (
        "This is a rational supercritical-band certificate, not a finished irrational nonexistence theorem. "
        "Accepted windows are either wide-window interval certificates or theorem-mode local hyperbolic-band certificates built from a pointwise hyperbolic center plus local transport."
    )
    if methodology_frontend is not None and not accepted:
        rejected.append({'methodology_frontend': methodology_frontend})
    return SupercriticalBandReport(
        p=int(p),
        q=int(q),
        K_lo=K_lo,
        K_hi=K_hi,
        target_residue=float(target_residue),
        initial_subdivisions=int(initial_subdivisions),
        max_depth=int(max_depth),
        min_width=float(min_width),
        accepted_windows=merged,
        rejected_windows=rejected,
        longest_band_lo=longest_lo,
        longest_band_hi=longest_hi,
        longest_band_width=float(longest_width),
        coverage_width=float(coverage_width),
        coverage_fraction=float(coverage_fraction),
        status=status,
        notes=notes,
    )


def build_crossing_to_hyperbolic_band_bridge(
    p: int,
    q: int,
    crossing_K_lo: float,
    crossing_K_hi: float,
    band_search_lo: float,
    band_search_hi: float,
    family: HarmonicFamily | None = None,
    *,
    x_guess=None,
    target_residue: float = 0.25,
    auto_localize_crossing: bool = False,
    initial_subdivisions: int = 4,
    max_depth: int = 4,
    min_width: float = 5e-4,
) -> CrossingToHyperbolicBandBridge:
    """Connect a local crossing certificate to a later hyperbolic supercritical band."""
    family = family or HarmonicFamily()
    crossing = certify_unique_crossing_window(
        p=p,
        q=q,
        K_lo=float(crossing_K_lo),
        K_hi=float(crossing_K_hi),
        family=family,
        x_guess=x_guess,
        target_residue=target_residue,
        auto_localize=auto_localize_crossing,
    )
    crossing_dict = crossing.to_dict()
    effective_lo = max(float(band_search_lo), float(crossing.certified_root_window_hi or band_search_lo))
    band = build_supercritical_band_report(
        p=p,
        q=q,
        K_lo=effective_lo,
        K_hi=float(band_search_hi),
        family=family,
        x_guess=x_guess,
        target_residue=target_residue,
        initial_subdivisions=initial_subdivisions,
        max_depth=max_depth,
        min_width=min_width,
    )

    gap = None
    status = "incomplete"
    if crossing.certified_root_window_hi is not None and band.longest_band_lo is not None:
        gap = float(band.longest_band_lo - crossing.certified_root_window_hi)
        status = "crossing-plus-hyperbolic-band"
    elif crossing.certified_root_window_hi is not None:
        status = "crossing-only"
    elif band.longest_band_lo is not None:
        status = "hyperbolic-band-only"

    notes = (
        "This bridge combines a local unique-crossing theorem for g(K)=|R|-target with an adaptively certified hyperbolic band further into the supercritical regime. "
        "It is stronger than a single barrier window, but it still does not identify the exact irrational threshold."
    )
    return CrossingToHyperbolicBandBridge(
        p=int(p),
        q=int(q),
        crossing_window_input_lo=float(crossing_K_lo),
        crossing_window_input_hi=float(crossing_K_hi),
        band_search_lo=float(effective_lo),
        band_search_hi=float(band_search_hi),
        target_residue=float(target_residue),
        crossing_certificate=crossing_dict,
        band_report=band.to_dict(),
        first_supercritical_gap=gap,
        status=status,
        notes=notes,
    )

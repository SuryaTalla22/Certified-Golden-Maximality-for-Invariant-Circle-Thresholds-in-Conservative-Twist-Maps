from __future__ import annotations

"""Finite-panel tail replacement theorem for Theorem IV upper bands.

This module provides a rigor-preserving replacement for explicit high-q golden
rows in the current finite theorem panel.  The main idea is:

1. Build a coherent *anchor upper object* from a short ladder of explicit
   crossing-plus-band witnesses (typically through 55/89).
2. Predict candidate band centers for later golden convergents using only the
   certified anchor-band family.
3. Certify local hyperbolic bands for the later rows *without* rebuilding their
   expensive crossing-localization layers.
4. Package the resulting family as a theorem-facing certificate that can be
   consumed by the IV upper-tail coherence stack.

The result is not a universal asymptotic theorem.  It is a finite-panel tail
transport theorem: enough to replace explicit 89/144-and-beyond rows in the
current operational panel without silently weakening rigor.
"""

from dataclasses import asdict, dataclass
from typing import Any, Sequence
import math
import numpy as np

from .hyperbolicity_certifier import certify_sustained_hyperbolic_tail
from .obstruction_atlas import ApproximantWindowSpec
from .standard_map import HarmonicFamily
from .theorem_iv_band_methodology import (
    get_theorem_iv_band_profile,
    methodology_localize_hyperbolic_band,
)


def _nested_get(obj: dict[str, Any] | None, path: Sequence[str], default: Any = None) -> Any:
    cur: Any = obj
    for key in path:
        if not isinstance(cur, dict) or key not in cur:
            return default
        cur = cur[key]
    return cur


def _best_band_from_entry(entry: dict[str, Any]) -> dict[str, Any]:
    band = entry.get('band_report', {}) or {}
    best = band.get('best_band', {}) or {}
    return best if isinstance(best, dict) else {}


def _band_certificate_candidates(entry: dict[str, Any]) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    band = entry.get('band_report', {}) or {}

    accepted = band.get('accepted_windows', []) or []
    if isinstance(accepted, list):
        for cert in accepted:
            if isinstance(cert, dict):
                candidates.append(cert)

    methodology_cert = _nested_get(entry, ['methodology_band', 'certificate'])
    if isinstance(methodology_cert, dict):
        candidates.append(methodology_cert)

    frontend_cert = _nested_get(entry, ['band_report', 'methodology_frontend', 'certificate'])
    if isinstance(frontend_cert, dict):
        candidates.append(frontend_cert)

    best = _best_band_from_entry(entry)
    if best:
        candidates.append(best)

    return candidates


def _extract_band_center_halfwidth_margin(entry: dict[str, Any], *, target_residue: float = 0.25) -> tuple[float | None, float | None, float | None]:
    candidates: list[tuple[Any, Any, Any]] = []

    for cert in _band_certificate_candidates(entry):
        center = cert.get('chosen_center')
        if center is None:
            center = cert.get('center')
            if isinstance(center, dict):
                center = None
        half_width = cert.get('chosen_half_width')
        if half_width is None:
            half_width = cert.get('half_width')
        if center is None or half_width is None:
            lo = cert.get('K_lo')
            hi = cert.get('K_hi')
            if lo is not None and hi is not None:
                if center is None:
                    center = 0.5 * (float(lo) + float(hi))
                if half_width is None:
                    half_width = 0.5 * (float(hi) - float(lo))
        margin = cert.get('chosen_margin')
        if margin is None:
            margin = cert.get('margin')
        if margin is None:
            g_lo = cert.get('g_interval_lo')
            if g_lo is not None:
                margin = float(g_lo)
        if margin is None:
            margin = cert.get('hyperbolicity_margin')
        if margin is None:
            abs_lo = cert.get('abs_residue_interval_lo')
            if abs_lo is not None:
                margin = float(abs_lo) - float(target_residue)
        candidates.append((center, half_width, margin))

    for center, half_width, margin in candidates:
        if center is not None and half_width is not None and margin is not None:
            return float(center), float(half_width), float(margin)
    return None, None, None


def _band_center_from_entry(entry: dict[str, Any]) -> float | None:
    center, _, _ = _extract_band_center_halfwidth_margin(entry)
    return center


def _band_half_width_from_entry(entry: dict[str, Any]) -> float | None:
    _, half_width, _ = _extract_band_center_halfwidth_margin(entry)
    return half_width


def _band_margin_from_entry(entry: dict[str, Any], target_residue: float) -> float | None:
    _, _, margin = _extract_band_center_halfwidth_margin(entry, target_residue=target_residue)
    return margin


def _entry_has_explicit_crossing_band(entry: dict[str, Any]) -> bool:
    cross = entry.get('adaptive_crossing', {}) or {}
    cross_msg = str(cross.get('message', ''))
    cross_status = str(cross.get('status', ''))
    methodology_ok = bool(_nested_get(cross, ['methodology_frontend', 'proof_ready'], False))
    band = entry.get('band_report', {}) or {}
    certified_band_count = int(band.get('certified_band_count', 0))
    center, half_width, margin = _extract_band_center_halfwidth_margin(entry)
    crossing_ok = methodology_ok or cross_status in {'theorem_mode_local', 'interval_newton', 'monotone_window'} or ('proof-ready local crossing certificate' in cross_msg)
    return crossing_ok and certified_band_count > 0 and center is not None and half_width is not None and margin is not None


def _normalize_entry_for_tail(entry: dict[str, Any]) -> dict[str, Any]:
    out = dict(entry)
    if 'crossing_certificate' not in out:
        adaptive = out.get('adaptive_crossing', {}) or {}
        out['crossing_certificate'] = {
            'certification_tier': str(adaptive.get('status', 'incomplete')),
            'source': str(out.get('localized_crossing_source', adaptive.get('message', 'adaptive-crossing'))),
        }
    return out


@dataclass
class TailBandAnchor:
    p: int
    q: int
    label: str
    crossing_lo: float
    crossing_hi: float
    band_lo: float
    band_hi: float
    band_center: float
    band_half_width: float
    band_margin: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class PairwiseBandTransportCertificate:
    q_left: int
    q_right: int
    center_left: float
    center_right: float
    center_drift: float
    width_floor: float
    margin_floor: float
    normalized_center_drift: float
    transport_status: str
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class TailDerivedRowCertificate:
    p: int
    q: int
    label: str
    predictive_center: float
    prediction_source: str
    anchor_upper_lo: float
    anchor_upper_hi: float
    anchor_upper_width: float
    band_certificate: dict[str, Any]
    proof_ready: bool
    inherited_positive_gap: bool
    theorem_status: str
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class GoldenTheoremIVTailTransportCertificate:
    family_label: str
    rho: float | None
    target_residue: float
    anchor_qs: list[int]
    anchor_rows: list[dict[str, Any]]
    anchor_tail_summary: dict[str, Any]
    pairwise_transport: list[dict[str, Any]]
    explicit_tail_cutoff_q: int
    replacement_qs: list[int]
    derived_rows: list[dict[str, Any]]
    anchor_upper_lo: float | None
    anchor_upper_hi: float | None
    anchor_upper_width: float | None
    all_replacement_rows_proof_ready: bool
    all_replacement_rows_above_anchor_upper: bool
    theorem_status: str
    open_hypotheses: list[str]
    residual_burden: list[str]
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def extract_tail_band_anchor(entry: dict[str, Any], *, target_residue: float = 0.25) -> TailBandAnchor:
    if not _entry_has_explicit_crossing_band(entry):
        raise ValueError('entry does not contain an explicit crossing-plus-band anchor witness')
    center, half_width, margin = _extract_band_center_halfwidth_margin(entry, target_residue=target_residue)
    if center is None or half_width is None or margin is None:
        raise ValueError('entry is missing required band-center data')

    crossing_lo = entry.get('crossing_root_window_lo')
    crossing_hi = entry.get('crossing_root_window_hi')
    if crossing_lo is None or crossing_hi is None:
        adaptive = entry.get('adaptive_crossing', {}) or {}
        best = adaptive.get('best_window', {}) or {}
        crossing_lo = best.get('K_lo', crossing_lo)
        crossing_hi = best.get('K_hi', crossing_hi)
    if crossing_lo is None or crossing_hi is None:
        raise ValueError('entry is missing required crossing-window data')

    band_lo = entry.get('hyperbolic_band_lo')
    band_hi = entry.get('hyperbolic_band_hi')
    if band_lo is None or band_hi is None:
        best_band = _best_band_from_entry(entry)
        band_lo = best_band.get('K_lo', band_lo)
        band_hi = best_band.get('K_hi', band_hi)
    if band_lo is None or band_hi is None:
        band_lo = float(center) - float(half_width)
        band_hi = float(center) + float(half_width)

    return TailBandAnchor(
        p=int(entry['p']),
        q=int(entry['q']),
        label=str(entry.get('label', f"{entry['p']}/{entry['q']}")),
        crossing_lo=float(crossing_lo),
        crossing_hi=float(crossing_hi),
        band_lo=float(band_lo),
        band_hi=float(band_hi),
        band_center=float(center),
        band_half_width=float(half_width),
        band_margin=float(margin),
    )


def build_pairwise_band_transport_certificate(left: TailBandAnchor | dict[str, Any], right: TailBandAnchor | dict[str, Any]) -> PairwiseBandTransportCertificate:
    if not isinstance(left, TailBandAnchor):
        left = TailBandAnchor(**dict(left))
    if not isinstance(right, TailBandAnchor):
        right = TailBandAnchor(**dict(right))
    drift = abs(float(right.band_center) - float(left.band_center))
    width_floor = min(float(left.band_half_width), float(right.band_half_width))
    margin_floor = min(float(left.band_margin), float(right.band_margin))
    denom = max(width_floor, 1e-30)
    normalized = drift / denom
    strong = drift < 0.75 * width_floor and margin_floor > drift
    moderate = drift < width_floor and margin_floor > 0.5 * drift
    if strong:
        status = 'pairwise-band-transport-strong'
        notes = 'Center drift is smaller than the local certified half-width and below the available band margin.'
    elif moderate:
        status = 'pairwise-band-transport-moderate'
        notes = 'Center drift is controlled but not decisively dominated by the certified half-width.'
    else:
        status = 'pairwise-band-transport-weak'
        notes = 'Center drift is too large relative to the local certified band geometry.'
    return PairwiseBandTransportCertificate(
        q_left=int(left.q), q_right=int(right.q),
        center_left=float(left.band_center), center_right=float(right.band_center),
        center_drift=float(drift), width_floor=float(width_floor), margin_floor=float(margin_floor),
        normalized_center_drift=float(normalized), transport_status=status, notes=notes,
    )


def _fit_tail_center(q: int, anchors: Sequence[TailBandAnchor]) -> tuple[float, str]:
    pts = [(1.0 / (float(a.q) * float(a.q)), float(a.band_center)) for a in anchors]
    if len(pts) >= 2:
        xs = np.array([x for x, _ in pts], dtype=float)
        ys = np.array([y for _, y in pts], dtype=float)
        try:
            coeff = np.polyfit(xs, ys, deg=1)
            pred = float(np.polyval(coeff, 1.0 / (float(q) * float(q))))
            return pred, 'q^-2 anchor-center fit'
        except Exception:
            pass
    return float(anchors[-1].band_center), 'last-anchor-center'


def _make_band_report_from_certificate(cert: dict[str, Any], spec: ApproximantWindowSpec) -> dict[str, Any]:
    band_lo = float(cert['K_lo'])
    band_hi = float(cert['K_hi'])
    return {
        'p': int(spec.p),
        'q': int(spec.q),
        'K_lo': float(spec.band_search_lo),
        'K_hi': float(spec.band_search_hi),
        'target_residue': 0.25,
        'initial_subdivisions': 0,
        'max_depth': 0,
        'min_width': 0.0,
        'accepted_windows': [cert],
        'rejected_windows': [],
        'certified_band_count': 1,
        'best_band': {
            'K_lo': band_lo,
            'K_hi': band_hi,
            'width': float(band_hi - band_lo),
            'g_interval_lo': cert.get('g_interval_lo'),
            'g_interval_hi': cert.get('g_interval_hi'),
            'hyperbolicity_margin': cert.get('hyperbolicity_margin'),
        },
        'longest_band_lo': band_lo,
        'longest_band_hi': band_hi,
        'longest_band_width': float(band_hi - band_lo),
        'coverage_width': float(band_hi - band_lo),
        'coverage_fraction': max(0.0, min(1.0, float(band_hi - band_lo) / max(float(spec.band_search_hi - spec.band_search_lo), 1e-30))),
        'status': 'certified-local-band',
        'notes': 'tail-transport replacement theorem produced a certified local band without rebuilding the expensive crossing row.',
    }


def _make_tail_entry_from_cert(spec: ApproximantWindowSpec, cert: dict[str, Any], *, anchor_upper_lo: float, anchor_upper_hi: float, prediction_source: str, predictive_center: float) -> dict[str, Any]:
    band_lo = float(cert['K_lo'])
    band_hi = float(cert['K_hi'])
    gap = float(band_lo - float(anchor_upper_hi))
    adaptive_crossing = {
        'status': 'anchor_upper_object',
        'message': 'Crossing certificate inherited from the coherent anchor upper object in the finite tail-replacement theorem.',
        'anchor_upper_lo': float(anchor_upper_lo),
        'anchor_upper_hi': float(anchor_upper_hi),
        'prediction_source': str(prediction_source),
        'predictive_center': float(predictive_center),
    }
    return {
        'p': int(spec.p),
        'q': int(spec.q),
        'label': str(spec.normalized_label()),
        'crossing_window_input_lo': float(spec.crossing_K_lo),
        'crossing_window_input_hi': float(spec.crossing_K_hi),
        'band_search_lo': float(spec.band_search_lo),
        'band_search_hi': float(spec.band_search_hi),
        'adaptive_crossing': adaptive_crossing,
        'localized_crossing_source': 'tail-theorem-anchor-upper-object',
        'crossing_root_window_lo': float(anchor_upper_lo),
        'crossing_root_window_hi': float(anchor_upper_hi),
        'crossing_root_window_width': float(anchor_upper_hi - anchor_upper_lo),
        'band_report': _make_band_report_from_certificate(cert, spec),
        'hyperbolic_band_lo': band_lo,
        'hyperbolic_band_hi': band_hi,
        'hyperbolic_band_width': float(band_hi - band_lo),
        'gap_from_crossing_to_band': float(gap),
        'status': 'tail-transport-derived',
        'notes': 'Tail row derived from the finite anchor upper object plus a certified local transport band.',
    }


def _build_anchor_upper_envelope_summary(
    anchors: Sequence[TailBandAnchor],
    anchor_entries: Sequence[dict[str, Any]],
    *,
    min_anchor_count: int,
) -> dict[str, Any]:
    if not anchors:
        return {
            'generated_qs': [],
            'witness_qs': [],
            'tail_qs': [],
            'tail_start_q': None,
            'tail_is_suffix_of_generated': False,
            'tail_member_count': 0,
            'coherent_upper_lo': None,
            'coherent_upper_hi': None,
            'coherent_upper_width': None,
            'coherent_band_lo': None,
            'coherent_band_hi': None,
            'coherent_band_width': None,
            'incompatibility_gap': None,
            'gap_floor': None,
            'gap_ceiling': None,
            'pairwise_transport': [],
            'pairwise_strong_count': 0,
            'pairwise_moderate_or_better_count': 0,
            'pairwise_weak_count': 0,
            'maximum_normalized_center_drift': None,
            'legacy_tail_diagnostics': {},
            'theorem_status': 'anchor-upper-envelope-failed',
            'notes': 'No valid anchor witnesses were available.',
        }

    crossings_lo = [float(a.crossing_lo) for a in anchors]
    crossings_hi = [float(a.crossing_hi) for a in anchors]
    bands_lo = [float(a.band_lo) for a in anchors]
    bands_hi = [float(a.band_hi) for a in anchors]
    upper_lo = min(crossings_lo)
    upper_hi = max(crossings_hi)
    band_lo = min(bands_lo)
    band_hi = max(bands_hi)
    gap_floor = band_lo - upper_hi
    gap_ceiling = band_hi - upper_lo

    pairwise = [build_pairwise_band_transport_certificate(anchors[i], anchors[i + 1]).to_dict() for i in range(len(anchors) - 1)]
    strong_count = sum(1 for p in pairwise if p.get('transport_status') == 'pairwise-band-transport-strong')
    moderate_count = sum(1 for p in pairwise if p.get('transport_status') in {'pairwise-band-transport-strong', 'pairwise-band-transport-moderate'})
    weak_count = sum(1 for p in pairwise if p.get('transport_status') == 'pairwise-band-transport-weak')
    max_normalized_drift = None
    if pairwise:
        max_normalized_drift = max(float(p.get('normalized_center_drift', 0.0)) for p in pairwise)

    legacy_tail = certify_sustained_hyperbolic_tail(
        [_normalize_entry_for_tail(e) for e in anchor_entries],
        min_tail_members=max(2, min_anchor_count - 1),
    ).to_dict()

    if len(anchors) < int(min_anchor_count):
        theorem_status = 'anchor-upper-envelope-failed'
        notes = 'Too few anchor witnesses were available to build the finite-panel upper envelope.'
    elif gap_floor <= 0.0:
        theorem_status = 'anchor-upper-envelope-weak'
        notes = 'The explicit anchor family does not yet separate the global crossing cap from the global hyperbolic barrier floor.'
    else:
        theorem_status = 'anchor-upper-envelope-strong'
        notes = 'The explicit anchor family determines a rigorous upper crossing cap and a positive barrier floor; pairwise transport diagnostics are recorded but are not required to intersect in a common window.'

    return {
        'generated_qs': [int(a.q) for a in anchors],
        'witness_qs': [int(a.q) for a in anchors],
        'tail_qs': [int(a.q) for a in anchors],
        'tail_start_q': int(anchors[0].q),
        'tail_is_suffix_of_generated': True,
        'tail_member_count': int(len(anchors)),
        'coherent_upper_lo': float(upper_lo),
        'coherent_upper_hi': float(upper_hi),
        'coherent_upper_width': float(upper_hi - upper_lo),
        'coherent_band_lo': float(band_lo),
        'coherent_band_hi': float(band_hi),
        'coherent_band_width': float(band_hi - band_lo),
        'incompatibility_gap': float(gap_floor),
        'gap_floor': float(gap_floor),
        'gap_ceiling': float(gap_ceiling),
        'pairwise_transport': pairwise,
        'pairwise_strong_count': int(strong_count),
        'pairwise_moderate_or_better_count': int(moderate_count),
        'pairwise_weak_count': int(weak_count),
        'maximum_normalized_center_drift': (None if max_normalized_drift is None else float(max_normalized_drift)),
        'legacy_tail_diagnostics': legacy_tail,
        'theorem_status': theorem_status,
        'notes': notes,
    }


def build_golden_tail_band_transport_certificate(
    anchor_entries: Sequence[dict[str, Any]],
    replacement_specs: Sequence[ApproximantWindowSpec],
    *,
    family: HarmonicFamily | None = None,
    rho: float | None = None,
    target_residue: float = 0.25,
    explicit_tail_cutoff_q: int = 89,
    min_anchor_count: int = 3,
) -> GoldenTheoremIVTailTransportCertificate:
    family = family or HarmonicFamily()
    anchors: list[TailBandAnchor] = []
    failed_anchor_labels: list[str] = []
    for e in anchor_entries:
        if not _entry_has_explicit_crossing_band(e):
            continue
        try:
            anchors.append(extract_tail_band_anchor(e, target_residue=target_residue))
        except Exception as exc:
            label = str(e.get('label', f"{e.get('p', '?')}/{e.get('q', '?')}"))
            failed_anchor_labels.append(f"{label}: {exc}")
    anchors = sorted(anchors, key=lambda a: a.q)
    if len(anchors) < int(min_anchor_count):
        note = 'Not enough explicit crossing-plus-band anchors are available to build the finite-panel tail replacement theorem.'
        if failed_anchor_labels:
            note += ' Failed anchors: ' + '; '.join(failed_anchor_labels)
        return GoldenTheoremIVTailTransportCertificate(
            family_label='standard-sine' if len(family.harmonics) == 1 and family.harmonics[0][1] == 1 else 'custom-harmonic',
            rho=None if rho is None else float(rho),
            target_residue=float(target_residue),
            anchor_qs=[a.q for a in anchors],
            anchor_rows=[a.to_dict() for a in anchors],
            anchor_tail_summary={},
            pairwise_transport=[],
            explicit_tail_cutoff_q=int(explicit_tail_cutoff_q),
            replacement_qs=[int(s.q) for s in replacement_specs],
            derived_rows=[],
            anchor_upper_lo=None,
            anchor_upper_hi=None,
            anchor_upper_width=None,
            all_replacement_rows_proof_ready=False,
            all_replacement_rows_above_anchor_upper=False,
            theorem_status='golden-theorem-iv-tail-transport-failed',
            open_hypotheses=['insufficient_anchor_rows'],
            residual_burden=['insufficient_anchor_rows'],
            notes=note,
        )

    pairwise = [build_pairwise_band_transport_certificate(anchors[i], anchors[i + 1]) for i in range(len(anchors) - 1)]
    anchor_tail_summary = _build_anchor_upper_envelope_summary(
        anchors,
        anchor_entries,
        min_anchor_count=min_anchor_count,
    )
    upper_lo = anchor_tail_summary.get('coherent_upper_lo')
    upper_hi = anchor_tail_summary.get('coherent_upper_hi')
    if upper_lo is None or upper_hi is None:
        return GoldenTheoremIVTailTransportCertificate(
            family_label='standard-sine' if len(family.harmonics) == 1 and family.harmonics[0][1] == 1 else 'custom-harmonic',
            rho=None if rho is None else float(rho),
            target_residue=float(target_residue),
            anchor_qs=[a.q for a in anchors],
            anchor_rows=[a.to_dict() for a in anchors],
            anchor_tail_summary=anchor_tail_summary,
            pairwise_transport=[p.to_dict() for p in pairwise],
            explicit_tail_cutoff_q=int(explicit_tail_cutoff_q),
            replacement_qs=[int(s.q) for s in replacement_specs],
            derived_rows=[],
            anchor_upper_lo=None,
            anchor_upper_hi=None,
            anchor_upper_width=None,
            all_replacement_rows_proof_ready=False,
            all_replacement_rows_above_anchor_upper=False,
            theorem_status='golden-theorem-iv-tail-transport-failed',
            open_hypotheses=['coherent_anchor_upper_object_not_available'],
            residual_burden=['coherent_anchor_upper_object_not_available'],
            notes='The explicit anchors do not yet define a usable upper envelope object to be inherited by the tail rows.',
        )

    derived_rows: list[TailDerivedRowCertificate] = []
    current_anchor_family = list(anchors)
    for spec in replacement_specs:
        pred_center, pred_source = _fit_tail_center(int(spec.q), current_anchor_family)
        profile = get_theorem_iv_band_profile(spec.p, spec.q)
        methodology = methodology_localize_hyperbolic_band(
            spec,
            family=family,
            target_residue=target_residue,
            crossing_root_hi=float(upper_hi),
            predictive_hint_center=float(pred_center),
            previous_entry_dicts=[],
            profile=profile,
        )
        cert = methodology.get('certificate') or {}
        proof_ready = bool(methodology.get('proof_ready', False) and cert and cert.get('proof_ready', False))
        inherited_gap = bool(proof_ready and float(cert.get('K_lo', -math.inf)) > float(upper_hi))
        if proof_ready and inherited_gap:
            temp_entry = _make_tail_entry_from_cert(
                spec,
                cert,
                anchor_upper_lo=float(upper_lo),
                anchor_upper_hi=float(upper_hi),
                prediction_source=pred_source,
                predictive_center=pred_center,
            )
            try:
                current_anchor_family.append(extract_tail_band_anchor(temp_entry, target_residue=target_residue))
            except Exception:
                pass
            theorem_status = 'tail-row-certified'
            notes = 'Tail row certified by local hyperbolic-band transport from the anchor upper envelope.'
        elif proof_ready:
            theorem_status = 'tail-row-gap-failed'
            notes = 'A local hyperbolic band was certified, but it did not sit strictly above the anchor upper envelope.'
        else:
            theorem_status = 'tail-row-certification-failed'
            notes = methodology.get('message', 'Tail row could not be certified from the anchor upper envelope.')
        derived_rows.append(TailDerivedRowCertificate(
            p=int(spec.p),
            q=int(spec.q),
            label=str(spec.normalized_label()),
            predictive_center=float(pred_center),
            prediction_source=str(pred_source),
            anchor_upper_lo=float(upper_lo),
            anchor_upper_hi=float(upper_hi),
            anchor_upper_width=float(float(upper_hi) - float(upper_lo)),
            band_certificate=cert if isinstance(cert, dict) else {},
            proof_ready=proof_ready,
            inherited_positive_gap=inherited_gap,
            theorem_status=theorem_status,
            notes=str(notes),
        ))

    all_ready = all(r.proof_ready for r in derived_rows) if replacement_specs else True
    all_gap = all(r.inherited_positive_gap for r in derived_rows) if replacement_specs else True
    open_hypotheses = []
    residual = []
    if not all_ready:
        open_hypotheses.append('all_tail_rows_certified_from_anchor_upper_object')
        residual.append('uncertified_tail_rows')
    if not all_gap:
        open_hypotheses.append('all_tail_rows_above_anchor_upper_object')
        residual.append('nonpositive_anchor_gap_on_tail')
    if anchor_tail_summary.get('theorem_status') != 'anchor-upper-envelope-strong':
        open_hypotheses.append('anchor_upper_envelope_is_strong')
        residual.append('anchor_upper_envelope_not_strong')

    if all_ready and all_gap and anchor_tail_summary.get('theorem_status') == 'anchor-upper-envelope-strong':
        theorem_status = 'golden-theorem-iv-tail-transport-strong'
        notes = 'Explicit anchors through the cutoff row determine a rigorous upper envelope, and every later row in the finite panel inherits a certified local hyperbolic band above that envelope.'
    elif all_ready and all_gap:
        theorem_status = 'golden-theorem-iv-tail-transport-moderate'
        notes = 'Tail rows are certified above the anchor upper envelope, but the anchor envelope itself is not yet packaged as strong.'
    else:
        theorem_status = 'golden-theorem-iv-tail-transport-weak'
        notes = 'The anchor family predicts the tail successfully in places, but the full finite-panel tail replacement theorem is not yet closed.'

    return GoldenTheoremIVTailTransportCertificate(
        family_label='standard-sine' if len(family.harmonics) == 1 and family.harmonics[0][1] == 1 else 'custom-harmonic',
        rho=None if rho is None else float(rho),
        target_residue=float(target_residue),
        anchor_qs=[a.q for a in anchors],
        anchor_rows=[a.to_dict() for a in anchors],
        anchor_tail_summary=anchor_tail_summary,
        pairwise_transport=[p.to_dict() for p in pairwise],
        explicit_tail_cutoff_q=int(explicit_tail_cutoff_q),
        replacement_qs=[int(s.q) for s in replacement_specs],
        derived_rows=[r.to_dict() for r in derived_rows],
        anchor_upper_lo=float(upper_lo),
        anchor_upper_hi=float(upper_hi),
        anchor_upper_width=float(float(upper_hi) - float(upper_lo)),
        all_replacement_rows_proof_ready=bool(all_ready),
        all_replacement_rows_above_anchor_upper=bool(all_gap),
        theorem_status=theorem_status,
        open_hypotheses=open_hypotheses,
        residual_burden=residual,
        notes=notes,
    )


def _row_interval_from_band_data(row: dict[str, Any]) -> tuple[float | None, float | None]:
    # direct interval keys
    for lo_key, hi_key in (
        ("upper_lo", "upper_hi"),
        ("band_lo", "band_hi"),
        ("K_lo", "K_hi"),
    ):
        lo = row.get(lo_key)
        hi = row.get(hi_key)
        if lo is not None and hi is not None:
            return float(lo), float(hi)

    # center/half-width style keys
    center = (
        row.get("band_center")
        if row.get("band_center") is not None
        else row.get("center")
    )
    half_width = (
        row.get("band_half_width")
        if row.get("band_half_width") is not None
        else row.get("half_width")
    )

    if center is not None and half_width is not None:
        c = float(center)
        h = float(half_width)
        return c - h, c + h

    # nested derived certificate path if present
    band_certificate = row.get("band_certificate")
    if isinstance(band_certificate, dict):
        lo = band_certificate.get("K_lo")
        hi = band_certificate.get("K_hi")
        if lo is not None and hi is not None:
            return float(lo), float(hi)

    # nested best-band path if present
    best_band = row.get("best_band")
    if isinstance(best_band, dict):
        lo = best_band.get("K_lo")
        hi = best_band.get("K_hi")
        if lo is not None and hi is not None:
            return float(lo), float(hi)
        center = best_band.get("center")
        half_width = best_band.get("half_width")
        if center is not None and half_width is not None:
            c = float(center)
            h = float(half_width)
            return c - h, c + h

    return None, None


def make_tail_transport_entry_dicts(cert, replacement_specs):
    if hasattr(cert, "to_dict"):
        cert = cert.to_dict()

    rows_by_q = {int(r["q"]): r for r in cert.get("derived_rows", [])}
    global_upper_lo = cert.get("anchor_upper_lo")
    global_upper_hi = cert.get("anchor_upper_hi")
    if global_upper_lo is not None and global_upper_hi is not None:
        global_upper_lo = float(global_upper_lo)
        global_upper_hi = float(global_upper_hi)
    else:
        global_upper_lo = None
        global_upper_hi = None

    out = []
    for spec in replacement_specs:
        q = int(spec.q)
        row = rows_by_q.get(q)
        if row is None:
            raise ValueError(f"tail transport certificate is missing derived row for q={q}")

        band_certificate = dict(row.get("band_certificate") or {})
        if not band_certificate:
            raise ValueError(f"derived tail row q={q} is missing its certified local band")
        if global_upper_lo is None or global_upper_hi is None:
            raise ValueError(f"derived tail row q={q} is missing the inherited anchor upper object")

        entry = _make_tail_entry_from_cert(
            spec,
            band_certificate,
            anchor_upper_lo=float(global_upper_lo),
            anchor_upper_hi=float(global_upper_hi),
            prediction_source=str(row.get("prediction_source", "tail-transport-fit")),
            predictive_center=float(row.get("predictive_center", row.get("band_center", row.get("center", 0.5 * (float(global_upper_lo) + float(global_upper_hi)))))) ,
        )
        entry["tail_transport_certificate"] = {
            "anchor_tail_summary": dict(cert.get("anchor_tail_summary") or {}),
            "explicit_tail_cutoff_q": cert.get("explicit_tail_cutoff_q"),
            "raw_row": dict(row),
        }
        out.append(entry)

    return out

__all__ = [
    'TailBandAnchor', 'PairwiseBandTransportCertificate', 'TailDerivedRowCertificate', 'GoldenTheoremIVTailTransportCertificate',
    'extract_tail_band_anchor', 'build_pairwise_band_transport_certificate', 'build_golden_tail_band_transport_certificate', 'make_tail_transport_entry_dicts',
]

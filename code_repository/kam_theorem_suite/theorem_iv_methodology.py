from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Sequence

import numpy as np

from .certification import (
    branch_residue_value,
    certify_crossing_via_derivative,
    certify_crossing_via_newton_local,
    certified_unique_crossing_on_window,
    deep_refine_and_certify,
    propose_local_crossing_window,
    scan_branch_for_crossing,
    search_strict_endpoint_pair_targeted,
)
from .obstruction_atlas import ApproximantWindowSpec
from .standard_map import HarmonicFamily


@dataclass(frozen=True)
class TheoremIVMethodologyProfile:
    name: str
    dps: int
    h_list: tuple[float, ...]
    derivative_floor: float
    bracket_fractions: tuple[float, ...]
    targeted_points: int
    targeted_center_margin: float
    targeted_max_expand: int
    localization_grid: int
    pre_refine_rounds: int
    scan_margin: float
    max_iter: int = 26
    tol: float = 1e-8

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def get_theorem_iv_methodology_profile(p: int, q: int) -> TheoremIVMethodologyProfile:
    q = int(q)
    if q <= 21:
        return TheoremIVMethodologyProfile(
            name='low-q', dps=140,
            h_list=(5e-6, 1e-5, 2e-5, 5e-5, 1e-4),
            derivative_floor=5e-4,
            bracket_fractions=(0.125, 0.25, 0.5, 0.75),
            targeted_points=17, targeted_center_margin=2.0e-4,
            targeted_max_expand=8, localization_grid=121, pre_refine_rounds=3,
            scan_margin=1.5e-3,
        )
    if q <= 34:
        return TheoremIVMethodologyProfile(
            name='mid-q', dps=160,
            h_list=(5e-6, 1e-5, 2e-5, 5e-5, 1e-4),
            derivative_floor=5e-4,
            bracket_fractions=(0.125, 0.25, 0.5, 0.75),
            targeted_points=17, targeted_center_margin=1.75e-4,
            targeted_max_expand=8, localization_grid=161, pre_refine_rounds=4,
            scan_margin=1.25e-3,
        )
    if q <= 55:
        return TheoremIVMethodologyProfile(
            name='high-q', dps=180,
            h_list=(2e-6, 5e-6, 1e-5, 2e-5, 5e-5),
            derivative_floor=5e-4,
            bracket_fractions=(0.125, 0.25, 0.5, 0.75),
            targeted_points=21, targeted_center_margin=1.5e-4,
            targeted_max_expand=10, localization_grid=221, pre_refine_rounds=4,
            scan_margin=1.0e-3,
        )
    if q <= 89:
        return TheoremIVMethodologyProfile(
            name='very-high-q', dps=180,
            h_list=(2e-6, 5e-6, 1e-5, 2e-5, 5e-5, 1e-4),
            derivative_floor=4e-4,
            bracket_fractions=(0.0625, 0.125, 0.25, 0.5, 0.75),
            targeted_points=25, targeted_center_margin=1.0e-4,
            targeted_max_expand=12, localization_grid=241, pre_refine_rounds=4,
            scan_margin=8.0e-4,
        )
    if q <= 144:
        return TheoremIVMethodologyProfile(
            name='extreme-q', dps=200,
            h_list=(1e-6, 2e-6, 5e-6, 1e-5, 2e-5, 5e-5),
            derivative_floor=3e-4,
            bracket_fractions=(0.0625, 0.125, 0.25, 0.5),
            targeted_points=31, targeted_center_margin=8.0e-5,
            targeted_max_expand=14, localization_grid=281, pre_refine_rounds=5,
            scan_margin=6.0e-4,
        )
    return TheoremIVMethodologyProfile(
        name='ultra-q', dps=220,
        h_list=(5e-7, 1e-6, 2e-6, 5e-6, 1e-5, 2e-5),
        derivative_floor=2.5e-4,
        bracket_fractions=(0.0625, 0.125, 0.25, 0.5),
        targeted_points=35, targeted_center_margin=6.0e-5,
        targeted_max_expand=16, localization_grid=321, pre_refine_rounds=5,
        scan_margin=5.0e-4,
    )


def _entry_center_from_dict(entry: dict[str, Any]) -> float | None:
    if entry.get('crossing_root_window_lo') is not None and entry.get('crossing_root_window_hi') is not None:
        return 0.5 * (float(entry['crossing_root_window_lo']) + float(entry['crossing_root_window_hi']))
    adaptive = entry.get('adaptive_crossing') or {}
    best = adaptive.get('best_window') or {}
    if best.get('K_lo') is not None and best.get('K_hi') is not None:
        return 0.5 * (float(best['K_lo']) + float(best['K_hi']))
    meth = adaptive.get('methodology_frontend') or {}
    for key in ('refined_center', 'predictive_center'):
        if meth.get(key) is not None:
            return float(meth[key])
    return None


def _fit_center_from_previous_entries(q: int, previous_entry_dicts: Sequence[dict[str, Any]]) -> tuple[float | None, str]:
    pts: list[tuple[float, float]] = []
    for entry in previous_entry_dicts:
        try:
            qq = int(entry.get('q'))
        except Exception:
            continue
        center = _entry_center_from_dict(entry)
        if center is None:
            continue
        pts.append((float(1.0 / (qq * qq)), float(center)))
    if len(pts) >= 2:
        xs = np.array([x for x, _ in pts], dtype=float)
        ys = np.array([y for _, y in pts], dtype=float)
        try:
            coeff = np.polyfit(xs, ys, deg=1)
            pred = float(np.polyval(coeff, 1.0 / (int(q) * int(q))))
            return pred, 'q^-2 extrapolation from previous entries'
        except Exception:
            pass
    if pts:
        return float(pts[-1][1]), 'last completed entry center'
    return None, 'none'


def predict_theorem_iv_crossing_center(
    spec: ApproximantWindowSpec,
    *,
    previous_entry_dicts: Sequence[dict[str, Any]] | None = None,
    predictive_hint_center: float | None = None,
) -> dict[str, Any]:
    lo = float(spec.crossing_K_lo)
    hi = float(spec.crossing_K_hi)
    if predictive_hint_center is not None:
        center = float(predictive_hint_center)
        source = 'explicit predictive hint'
    else:
        center, source = _fit_center_from_previous_entries(int(spec.q), list(previous_entry_dicts or []))
        if center is None:
            center = 0.5 * (lo + hi)
            source = 'window midpoint fallback'
    center = min(max(float(center), lo), hi)
    return {
        'predictive_center': float(center),
        'source': str(source),
        'crossing_window_lo': lo,
        'crossing_window_hi': hi,
    }


def methodology_localize_theorem_iv_crossing(
    spec: ApproximantWindowSpec,
    family: HarmonicFamily | None = None,
    *,
    target_residue: float = 0.25,
    profile: TheoremIVMethodologyProfile | None = None,
    predictive_hint_center: float | None = None,
    previous_entry_dicts: Sequence[dict[str, Any]] | None = None,
    enable_high_precision: bool = True,
) -> dict[str, Any]:
    family = family or HarmonicFamily()
    profile = profile or get_theorem_iv_methodology_profile(spec.p, spec.q)
    prediction = predict_theorem_iv_crossing_center(
        spec,
        previous_entry_dicts=previous_entry_dicts,
        predictive_hint_center=predictive_hint_center,
    )
    predicted_center = float(prediction['predictive_center'])
    scan_half = max(float(profile.scan_margin), 2.0 * float(profile.targeted_center_margin))
    scan_lo = max(float(spec.crossing_K_lo), predicted_center - scan_half)
    scan_hi = min(float(spec.crossing_K_hi), predicted_center + scan_half)
    if scan_hi <= scan_lo:
        scan_lo = float(spec.crossing_K_lo)
        scan_hi = float(spec.crossing_K_hi)

    scan_rows = scan_branch_for_crossing(
        p=int(spec.p), q=int(spec.q), family=family, target_residue=target_residue,
        K_min=float(scan_lo), K_max=float(scan_hi), n_grid=int(profile.localization_grid), K_seed=0.0,
    )
    proposal = propose_local_crossing_window(scan_rows, target_residue=target_residue)
    if proposal is None:
        work_lo = scan_lo
        work_hi = scan_hi
        proposal_kind = 'scan-failed'
    else:
        work_lo = float(proposal['K_lo'])
        work_hi = float(proposal['K_hi'])
        proposal_kind = str(proposal.get('kind', 'proposed'))
    work_center = 0.5 * (work_lo + work_hi)

    deep_refine = None
    refined_center = work_center
    if enable_high_precision and int(profile.dps) > 0:
        try:
            deep_refine = deep_refine_and_certify(
                p=int(spec.p), q=int(spec.q), K_center=float(work_center),
                target_residue=target_residue, dps=int(profile.dps),
            )
            if deep_refine.get('success', False):
                refined_center = float(deep_refine.get('refined_center', work_center))
        except Exception as exc:
            deep_refine = {'success': False, 'message': f'deep refinement exception: {exc}'}
    refined_center = min(max(float(refined_center), float(spec.crossing_K_lo)), float(spec.crossing_K_hi))
    local_half = max(float(profile.targeted_center_margin), 0.5 * max(work_hi - work_lo, 1e-10))
    local_lo = max(float(spec.crossing_K_lo), refined_center - local_half)
    local_hi = min(float(spec.crossing_K_hi), refined_center + local_half)

    attempts: list[dict[str, Any]] = []
    best_success: dict[str, Any] | None = None
    def _record(name: str, payload: dict[str, Any]) -> None:
        attempts.append({'method': name, 'success': bool(payload.get('success', False)), 'proof_ready': bool(payload.get('proof_ready', False)), 'message': payload.get('message')})

    for name, builder in [
        ('newton_local', lambda: certify_crossing_via_newton_local(
            p=int(spec.p), q=int(spec.q), K_center=float(refined_center), family=family,
            target_residue=target_residue, h_list=tuple(profile.h_list),
            derivative_floor=float(profile.derivative_floor), bracket_fractions=tuple(profile.bracket_fractions),
        )),
        ('derivative_local', lambda: certify_crossing_via_derivative(
            p=int(spec.p), q=int(spec.q), K_center=float(refined_center), family=family,
            target_residue=target_residue, h_list=tuple(profile.h_list), derivative_floor=float(profile.derivative_floor),
        )),
        ('targeted_strict_pair', lambda: search_strict_endpoint_pair_targeted(
            p=int(spec.p), q=int(spec.q), K_center=float(refined_center),
            initial_half_width=max(0.5 * (local_hi - local_lo), float(profile.targeted_center_margin)),
            family=family, target_residue=target_residue,
            max_expand=int(profile.targeted_max_expand), per_side_points=int(profile.targeted_points),
            center_margin=float(profile.targeted_center_margin), require_strict_buffer=True,
        )),
        ('certified_unique_window', lambda: certified_unique_crossing_on_window(
            p=int(spec.p), q=int(spec.q), family=family, target_residue=target_residue,
            K_lo=float(local_lo), K_hi=float(local_hi), max_iter=int(profile.max_iter), tol=float(profile.tol),
            auto_localize=True, localization_grid=int(profile.localization_grid),
            derivative_h=float(profile.h_list[0]), derivative_floor=float(profile.derivative_floor),
            proof_mode=True, pre_refine_rounds=int(profile.pre_refine_rounds),
        )),
    ]:
        try:
            payload = builder()
        except Exception as exc:
            payload = {'success': False, 'proof_ready': False, 'message': f'{name} exception: {exc}'}
        _record(name, payload)
        if payload.get('proof_ready', False):
            best_success = dict(payload)
            best_success['method'] = name
            break

    seed_state = None
    seed_center = refined_center
    if best_success is not None and best_success.get('K_lo') is not None and best_success.get('K_hi') is not None:
        seed_center = 0.5 * (float(best_success['K_lo']) + float(best_success['K_hi']))
    try:
        seed_state = branch_residue_value(
            p=int(spec.p), q=int(spec.q), K=float(seed_center), family=family,
            target_residue=target_residue, x_guess=None, K_anchor=predicted_center,
        )
    except Exception as exc:
        seed_state = {'success': False, 'message': f'branch seed recovery exception: {exc}'}

    out: dict[str, Any] = {
        'predictive_center': float(predicted_center),
        'prediction_source': str(prediction['source']),
        'scan_window_lo': float(scan_lo),
        'scan_window_hi': float(scan_hi),
        'proposal_kind': proposal_kind,
        'proposed_window_lo': float(work_lo),
        'proposed_window_hi': float(work_hi),
        'refined_center': float(refined_center),
        'local_window_lo': float(local_lo),
        'local_window_hi': float(local_hi),
        'profile': profile.to_dict(),
        'deep_refine': deep_refine,
        'attempts': attempts,
        'scan_rows': scan_rows,
        'seed_state_message': seed_state.get('message') if isinstance(seed_state, dict) else None,
    }
    if best_success is not None:
        out.update({
            'success': True,
            'proof_ready': True,
            'status': 'theorem_mode_local',
            'K_lo': float(best_success['K_lo']),
            'K_hi': float(best_success['K_hi']),
            'width': float(best_success.get('width', float(best_success['K_hi']) - float(best_success['K_lo']))),
            'method': str(best_success.get('method', 'unknown')),
            'certificate': best_success,
        })
    else:
        out.update({
            'success': False,
            'proof_ready': False,
            'status': 'fallback-required',
            'K_lo': float(local_lo),
            'K_hi': float(local_hi),
            'width': float(local_hi - local_lo),
            'method': 'none',
            'certificate': None,
        })
    if isinstance(seed_state, dict) and seed_state.get('success', False) and seed_state.get('x') is not None:
        out['x_seed'] = np.asarray(seed_state['x'], dtype=float).tolist()
    else:
        out['x_seed'] = None
    return out


__all__ = [
    'TheoremIVMethodologyProfile',
    'get_theorem_iv_methodology_profile',
    'predict_theorem_iv_crossing_center',
    'methodology_localize_theorem_iv_crossing',
]

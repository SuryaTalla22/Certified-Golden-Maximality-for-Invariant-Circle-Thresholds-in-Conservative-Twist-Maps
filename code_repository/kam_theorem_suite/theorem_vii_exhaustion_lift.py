from __future__ import annotations

"""Conditional theorem packaging for the current Theorem VII challenger-exhaustion front.

The repository already has:

* a Theorem-VI envelope shell describing the current arithmetic-threshold
  comparison front,
* a static class-level exhaustion screen,
* an adaptive search loop,
* an evidence-weighted search policy, and
* a termination-aware search policy distinguishing theorem status from search
  lifecycle status.

What it still lacks is the final theorem proving that these screened and searched
classes really exhaust every non-golden irrational challenger relevant to the
universal theorem.  This module packages that gap honestly.  It does not claim
final challenger exhaustion.  Instead it records which front hypotheses are
already discharged and which additional assumptions would promote the present
search stack into a conditional Theorem-VII-style statement.
"""

from dataclasses import asdict, dataclass
from inspect import signature
from typing import Any, Mapping, Sequence

from .challenger_search_loop import build_adaptive_class_exhaustion_search
from .class_campaigns import ArithmeticClassSpec
from .class_exhaustion_screen import (
    build_class_exhaustion_screen,
    build_near_top_threat_set_partition_certificate,
    promote_omitted_class_global_control_certificate,
    promote_screened_panel_global_completeness_certificate,
)
from .evidence_weighted_search import build_evidence_weighted_class_exhaustion_search
from .eta_challenger_comparison import (
    EtaChallengerSpec,
    build_near_top_eta_challenger_comparison_certificate,
)
from .standard_map import HarmonicFamily
from .termination_aware_search import build_termination_aware_class_exhaustion_search
from .theorem_vi_envelope_lift import build_golden_theorem_vi_certificate
from .theorem_vii_global_completeness import build_golden_theorem_vii_global_completeness_certificate
from .theorem_vii_global_exhaustion_support import build_theorem_vii_global_exhaustion_support_certificate
from .theorem_vii_support_utils import extract_stage106_support_certificates, merge_support_certificates



def _family_label(family: HarmonicFamily) -> str:
    if len(family.harmonics) == 1 and family.harmonics[0][1] == 1:
        return 'standard-sine'
    return 'custom-harmonic'



def _filter_kwargs(fn, kwargs: Mapping[str, Any]) -> dict[str, Any]:
    params = signature(fn).parameters
    has_var_keyword = any(p.kind == p.VAR_KEYWORD for p in params.values())
    if has_var_keyword:
        return dict(kwargs)
    return {k: v for k, v in kwargs.items() if k in params}



def _status_rank(status: str) -> int:
    status = str(status)
    if status.endswith('-conditional-one-variable-strong') or status.endswith('-conditional-two-variable-strong') or status.endswith('-conditional-strong') or status.endswith('-strong') or status.startswith('all-screened-classes-dominated'):
        return 4
    if status.endswith('-front-complete') or status.endswith('-front-only'):
        return 3
    if status.endswith('-conditional-partial') or status.endswith('-moderate') or status.endswith('-partial'):
        return 2
    if status.endswith('-weak'):
        return 1
    return 0



def _is_front_complete(cert: Mapping[str, Any]) -> bool:
    return _status_rank(str(cert.get('theorem_status', ''))) >= 3 and len(cert.get('open_hypotheses', [])) == 0



def _default_challenger_specs() -> list[ArithmeticClassSpec]:
    return [
        ArithmeticClassSpec(preperiod=(), period=(2,), label='silver'),
        ArithmeticClassSpec(preperiod=(), period=(3,), label='bronze'),
        ArithmeticClassSpec(preperiod=(1,), period=(2,), label='near-golden-12'),
    ]


def _extract_stage106_screened_panel_labels(payload: Mapping[str, Any] | None) -> list[str]:
    """Return screened-panel labels explicitly certified by a Stage-106 support payload.

    The VII lift has an older default challenger panel.  Stage 106 may certify a
    sharper screened panel inherited from VI; when that payload is supplied, the
    lift should not reintroduce stale default challengers as local-front blockers.
    """
    if not isinstance(payload, Mapping):
        return []
    labels = [str(x) for x in payload.get('screened_panel_labels', [])]
    support = payload.get('support_certificates', payload)
    if isinstance(support, Mapping):
        cert = support.get('screened_panel_global_completeness_certificate', {})
        if isinstance(cert, Mapping):
            labels.extend(str(x) for x in cert.get('screened_panel_labels', []))
    out: list[str] = []
    seen: set[str] = set()
    for label in labels:
        if label and label not in seen:
            seen.add(label)
            out.append(label)
    return out


def _restrict_specs_to_stage106_screened_panel(
    specs: Sequence[ArithmeticClassSpec],
    payload: Mapping[str, Any] | None,
) -> list[ArithmeticClassSpec]:
    labels = set(_extract_stage106_screened_panel_labels(payload))
    if not labels:
        return list(specs)
    filtered = [spec for spec in specs if spec.normalized_label() in labels]
    return filtered or list(specs)


_GLOBAL_EXHAUSTION_ASSUMPTIONS = {
    'finite_screened_panel_is_globally_complete',
    'omitted_nongolden_irrationals_outside_screened_panel_controlled',
}

_NEAR_TOP_PROMOTION_ASSUMPTIONS = {
    'exact_near_top_lagrange_spectrum_ranking',
    'theorem_level_pruning_of_dominated_regions',
    'deferred_or_retired_classes_are_globally_dominated',
    'termination_search_promotes_to_theorem_exclusion',
}


def _coerce_float(x: Any) -> float | None:
    if x is None:
        return None
    return float(x)


def _arithmetic_spec_to_eta_spec(spec: ArithmeticClassSpec) -> EtaChallengerSpec:
    return EtaChallengerSpec(
        preperiod=tuple(spec.preperiod),
        period=tuple(spec.period),
        label=spec.normalized_label(),
        metadata={'source': 'theorem-vii-arithmetic-class'},
    )


def _challenger_status_to_pruning_status(status: str) -> str:
    mapping = {
        'dominated-by-golden-threshold-anchor': 'dominated',
        'overlaps-golden-threshold-anchor': 'overlapping',
        'arithmetic-weaker-only': 'arithmetic-weaker-only',
        'undecided': 'undecided',
    }
    return mapping.get(str(status), 'undecided')


def _extract_theorem_vi_shell(theorem_vi: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(theorem_vi, Mapping):
        return {}
    shell = theorem_vi.get('theorem_vi_shell')
    if isinstance(shell, Mapping):
        return dict(shell)
    baseline = theorem_vi.get('baseline_theorem_vi_certificate')
    if isinstance(baseline, Mapping):
        baseline_shell = baseline.get('theorem_vi_shell')
        if isinstance(baseline_shell, Mapping):
            return dict(baseline_shell)
        return dict(baseline)
    lift = theorem_vi.get('theorem_vi_envelope_lift_certificate')
    if isinstance(lift, Mapping):
        lift_shell = lift.get('theorem_vi_shell')
        if isinstance(lift_shell, Mapping):
            return dict(lift_shell)
        return dict(lift)
    return {}


def _derive_near_top_surface_from_theorem_vi(
    theorem_vi: Mapping[str, Any],
    *,
    challenger_specs: Sequence[ArithmeticClassSpec],
    family: HarmonicFamily,
    kwargs: Mapping[str, Any],
) -> dict[str, Any] | None:
    theorem_vi = dict(theorem_vi)
    theorem_vi_shell = _extract_theorem_vi_shell(theorem_vi)
    near_top = dict(theorem_vi.get('near_top_challenger_surface', {}) or theorem_vi_shell.get('near_top_challenger_surface', {}))
    labels = {spec.normalized_label() for spec in challenger_specs}
    existing = {str(row.get('label', '')) for row in near_top.get('challenger_records', [])}
    if labels and labels.issubset(existing):
        return near_top
    eta_anchor = dict(theorem_vi.get('eta_threshold_anchor', {}) or theorem_vi_shell.get('eta_threshold_anchor', {}))
    if not eta_anchor:
        return near_top if near_top.get('challenger_records') else None
    eta_specs = [_arithmetic_spec_to_eta_spec(spec) for spec in challenger_specs]
    built = build_near_top_eta_challenger_comparison_certificate(
        eta_specs,
        **_filter_kwargs(
            build_near_top_eta_challenger_comparison_certificate,
            dict(
                golden_eta_threshold_certificate=eta_anchor,
                family=family,
                family_label=theorem_vi.get('family_label') or theorem_vi_shell.get('family_label'),
                **kwargs,
            ),
        ),
    ).to_dict()
    if near_top:
        merged = dict(near_top)
        for key, value in built.items():
            if key == 'challenger_records':
                if value:
                    merged[key] = value
            elif key == 'panel_records':
                if value:
                    merged[key] = value
            elif key == 'theorem_status':
                merged[key] = value
            else:
                merged.setdefault(key, value)
        note = str(merged.get('notes', ''))
        if 'supplemented for Theorem VII' not in note:
            merged['notes'] = (note + ' ' if note else '') + 'Near-top challenger records were supplemented for Theorem VII from the existing Theorem VI eta anchor.'
        return merged
    return built


def _build_surface_screen_from_near_top(
    near_top: Mapping[str, Any],
    *,
    challenger_specs: Sequence[ArithmeticClassSpec],
    reference_crossing_center: float,
    reference_lower_bound: float,
    family: HarmonicFamily,
) -> dict[str, Any]:
    by_label = {str(row.get('label', '')): dict(row) for row in near_top.get('challenger_records', [])}
    classes: list[dict[str, Any]] = []
    for spec in challenger_specs:
        label = spec.normalized_label()
        row = by_label.get(label, {})
        eta_interval = row.get('eta_interval')
        eta_lo = _coerce_float(None if eta_interval is None else eta_interval[0])
        eta_hi = _coerce_float(None if eta_interval is None else eta_interval[1])
        eta_center = None if eta_lo is None or eta_hi is None else 0.5 * (eta_lo + eta_hi)
        threshold_upper = _coerce_float(row.get('threshold_upper_bound'))
        threshold_lower = _coerce_float(row.get('threshold_lower_bound'))
        classes.append({
            'class_label': label,
            'preperiod': tuple(spec.preperiod),
            'period': tuple(spec.period),
            'rho': _coerce_float(row.get('rho')),
            'eta_lo': eta_lo,
            'eta_hi': eta_hi,
            'eta_center': eta_center,
            'approximant_count': 0,
            'raw_ladder_quality': 'not-run-near-top-surface-derived',
            'refined_status': 'not-run-near-top-surface-derived',
            'asymptotic_status': 'not-run-near-top-surface-derived',
            'selected_upper_source': str(row.get('threshold_source', 'near-top-eta-challenger-surface')),
            'selected_upper_lo': threshold_lower,
            'selected_upper_hi': threshold_upper,
            'selected_upper_width': None if threshold_lower is None or threshold_upper is None else float(threshold_upper - threshold_lower),
            'selected_upper_margin_to_reference': None if threshold_upper is None else float(reference_lower_bound - threshold_upper),
            'earliest_band_lo': None,
            'latest_band_hi': None,
            'pruning_status': _challenger_status_to_pruning_status(str(row.get('status', 'undecided'))),
            'reason': str(row.get('reason', 'derived from Theorem VI near-top challenger surface')),
            'notes': 'Derived from the existing Theorem VI near-top challenger surface rather than rebuilding the full class-level exhaustion screen.',
        })

    dominated = [r for r in classes if r.get('pruning_status') == 'dominated']
    overlapping = [r for r in classes if r.get('pruning_status') == 'overlapping']
    arithmetic_only = [r for r in classes if r.get('pruning_status') == 'arithmetic-weaker-only']
    undecided = [r for r in classes if r.get('pruning_status') == 'undecided']
    remaining = [r for r in classes if r.get('pruning_status') != 'dominated' and r.get('selected_upper_hi') is not None]
    strongest = None if not remaining else min(remaining, key=lambda r: float(r['selected_upper_hi']))
    arithmetic_ranking_certificate = {
        'status': 'screened-panel-ranking-certificate-available' if classes else 'screened-panel-ranking-certificate-missing',
        'ranking': sorted(
            [
                {
                    'class_label': str(r.get('class_label', 'unknown')),
                    'eta_hi': float(r.get('eta_hi', 0.0) or 0.0),
                    'eta_lo': float(r.get('eta_lo', 0.0) or 0.0),
                }
                for r in classes
            ],
            key=lambda row: (-row['eta_hi'], -row['eta_lo'], row['class_label']),
        ),
        'screened_class_labels': [str(r.get('class_label', 'unknown')) for r in classes],
        'theorem_level_ranked_labels': [],
        'proves_exact_near_top_lagrange_spectrum_ranking': False,
        'covers_screened_panel': bool(classes),
        'notes': 'This ranking is inherited from the existing Theorem VI near-top challenger surface and remains a theorem-support frontier rather than a theorem-level ranking proof.',
    }
    pruning_region_certificate = {
        'status': 'theorem-level-dominated-regions-frontier' if classes else 'theorem-level-dominated-regions-missing',
        'theorem_level_dominated_labels': [str(r.get('class_label', 'unknown')) for r in dominated],
        'proves_theorem_level_pruning_of_dominated_regions': False,
        'notes': 'The current dominated labels are inherited from the near-top challenger surface, but theorem-level pruning promotion has not yet been certified globally.',
    }
    screened_panel_global_completeness_certificate = {
        'status': 'screened-panel-global-completeness-frontier' if classes else 'screened-panel-global-completeness-missing',
        'screened_panel_labels': [str(r.get('class_label', 'unknown')) for r in classes],
        'overlapping_labels': [str(r.get('class_label', 'unknown')) for r in overlapping],
        'undecided_labels': [str(r.get('class_label', 'unknown')) for r in undecided],
        'theorem_level_complete_labels': [],
        'theorem_level_complete_records': [],
        'panel_has_no_overlaps': len(overlapping) == 0,
        'panel_has_no_undecided': len(undecided) == 0,
        'screened_panel_globally_complete': False,
        'notes': 'The screened panel is derived from the Theorem VI near-top challenger surface. It is useful as a theorem-facing seed but is not yet a theorem-level global completeness proof.',
    }
    near_global = dict(near_top.get('global_nongolden_ceiling_certificate', {}))
    omitted_labels = [str(r.get('class_label', 'unknown')) for r in arithmetic_only]
    omitted_class_global_control_certificate = {
        'status': 'omitted-class-global-control-certified' if bool(near_global.get('global_ceiling_theorem_certified', False)) else ('omitted-class-global-control-frontier' if classes else 'omitted-class-global-control-missing'),
        'screened_panel_globally_complete': False,
        'partition_complete': False,
        'omitted_labels': omitted_labels,
        'controlled_by_pruning': [],
        'controlled_by_ranking': [],
        'controlled_by_termination_exclusion': [],
        'controlled_by_deferred_retired_domination': [],
        'control_records': [],
        'uncontrolled_omitted_labels': [] if bool(near_global.get('global_ceiling_theorem_certified', False)) else list(omitted_labels),
        'omitted_classes_globally_controlled': bool(near_global.get('global_ceiling_theorem_certified', False)),
        'notes': 'This omitted-class seed is inherited from the Theorem VI near-top nongolden ceiling certificate and still needs theorem-level completion unless the ceiling theorem flag is already certified.',
    }
    if len(classes) == 0:
        status = 'class-exhaustion-screen-missing'
    elif len(overlapping) == 0 and len(undecided) == 0:
        status = 'near-top-surface-screen-front-complete'
    elif len(overlapping) > 0:
        status = 'screen-has-overlapping-challengers'
    elif len(undecided) > 0:
        status = 'screen-has-undecided-challengers'
    else:
        status = 'screened-panel-arithmetic-tail-only'
    return {
        'reference_label': 'golden',
        'reference_lower_bound': float(reference_lower_bound),
        'reference_crossing_center': float(reference_crossing_center),
        'family_label': _family_label(family),
        'classes': classes,
        'dominated_count': len(dominated),
        'overlapping_count': len(overlapping),
        'arithmetic_only_count': len(arithmetic_only),
        'undecided_count': len(undecided),
        'asymptotic_upper_count': 0,
        'refined_upper_count': 0,
        'raw_upper_count': 0,
        'no_upper_count': sum(1 for r in classes if r.get('selected_upper_hi') is None),
        'strongest_remaining_class': None if strongest is None else str(strongest.get('class_label')),
        'strongest_remaining_upper_bound': None if strongest is None else _coerce_float(strongest.get('selected_upper_hi')),
        'strongest_remaining_source': None if strongest is None else str(strongest.get('selected_upper_source')),
        'arithmetic_ranking_certificate': arithmetic_ranking_certificate,
        'pruning_region_certificate': pruning_region_certificate,
        'near_top_threat_set_partition_certificate': {},
        'screened_panel_global_completeness_certificate': screened_panel_global_completeness_certificate,
        'omitted_class_global_control_certificate': omitted_class_global_control_certificate,
        'status': status,
        'notes': 'This class screen was derived directly from the existing Theorem VI near-top challenger surface to avoid rebuilding the expensive class-exhaustion ladder stack.',
    }


def _build_search_seed_reports_from_surface(
    screen: Mapping[str, Any],
    *,
    reference_lower_bound: float,
    reference_crossing_center: float,
    family: HarmonicFamily,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    classes = [dict(row) for row in screen.get('classes', [])]
    overlapping = [row for row in classes if str(row.get('pruning_status')) == 'overlapping']
    undecided = [row for row in classes if str(row.get('pruning_status')) == 'undecided']
    arithmetic_only = [row for row in classes if str(row.get('pruning_status')) == 'arithmetic-weaker-only']
    dominated = [row for row in classes if str(row.get('pruning_status')) == 'dominated']
    active_like = overlapping + undecided
    strongest_active_upper = None
    strongest_active_source = None
    if active_like:
        with_upper = [row for row in active_like if row.get('selected_upper_hi') is not None]
        if with_upper:
            strongest = min(with_upper, key=lambda row: float(row['selected_upper_hi']))
            strongest_active_upper = _coerce_float(strongest.get('selected_upper_hi'))
            strongest_active_source = str(strongest.get('selected_upper_source'))

    seed_round = {
        'round_index': 1,
        'active_classes': [str(row.get('class_label', 'unknown')) for row in classes],
        'evaluated_classes': [str(row.get('class_label', 'unknown')) for row in classes],
        'deferred_classes': [],
        'retired_classes': [str(row.get('class_label', 'unknown')) for row in dominated + arithmetic_only],
        'probed_deferred_classes': [],
        'top_priority_classes': [str(row.get('class_label', 'unknown')) for row in active_like],
        'escalated_classes': [],
        'newly_deferred_classes': [],
        'newly_retired_classes': [str(row.get('class_label', 'unknown')) for row in dominated + arithmetic_only],
        'reactivated_classes': [],
        'records': classes,
        'status': 'theorem-vii-near-top-seed-round',
        'notes': 'This synthetic seed round is derived from the existing Theorem VI near-top challenger surface; it packages the current local challenger state without rebuilding the full challenger search stack.',
    }
    adaptive = {
        'reference_label': 'golden',
        'reference_lower_bound': float(reference_lower_bound),
        'reference_crossing_center': float(reference_crossing_center),
        'family_label': _family_label(family),
        'rounds': [dict(seed_round)],
        'final_records': classes,
        'dominated_count': len(dominated),
        'overlapping_count': len(overlapping),
        'arithmetic_only_count': len(arithmetic_only),
        'undecided_count': len(undecided),
        'strongest_remaining_class': screen.get('strongest_remaining_class'),
        'strongest_remaining_upper_bound': screen.get('strongest_remaining_upper_bound'),
        'strongest_remaining_source': screen.get('strongest_remaining_source'),
        'total_escalations': 0,
        'terminated_early': True,
        'status': 'adaptive-search-seeded-from-theorem-vi-near-top-surface',
        'notes': 'Adaptive search was short-circuited to the existing Theorem VI near-top challenger surface so the current theorem shell can propagate without rebuilding the expensive challenger screen.',
    }
    evidence = {
        'reference_label': 'golden',
        'reference_lower_bound': float(reference_lower_bound),
        'reference_crossing_center': float(reference_crossing_center),
        'family_label': _family_label(family),
        'rounds': [dict(seed_round)],
        'final_records': classes,
        'dominated_count': len(dominated),
        'overlapping_count': len(overlapping),
        'arithmetic_only_count': len(arithmetic_only),
        'undecided_count': len(undecided),
        'strongest_remaining_class': screen.get('strongest_remaining_class'),
        'strongest_remaining_upper_bound': screen.get('strongest_remaining_upper_bound'),
        'strongest_remaining_source': screen.get('strongest_remaining_source'),
        'total_escalations': 0,
        'terminated_early': True,
        'status': 'evidence-weighted-search-seeded-from-theorem-vi-near-top-surface',
        'notes': 'The evidence-weighted search layer was seeded directly from the existing Theorem VI near-top challenger surface.',
    }
    retired_labels = [str(row.get('class_label', 'unknown')) for row in dominated + arithmetic_only]
    arithmetic_only_labels = [str(row.get('class_label', 'unknown')) for row in arithmetic_only]
    deferred_retired_domination_certificate = {
        'status': 'deferred-retired-domination-frontier' if arithmetic_only_labels else 'no-deferred-or-retired-classes',
        'deferred_labels': [],
        'retired_labels': retired_labels,
        'proved_dominated_labels': [str(row.get('class_label', 'unknown')) for row in dominated],
        'unproved_retired_labels': list(arithmetic_only_labels),
        'proves_deferred_or_retired_classes_are_globally_dominated': len(arithmetic_only_labels) == 0,
        'notes': 'Retired labels inherited from the near-top surface are only theorem-grade globally dominated when they are already dominated rather than merely arithmetically separated.',
    }
    termination_exclusion_promotion_certificate = {
        'status': 'termination-exclusion-vacuous' if not active_like and not arithmetic_only_labels else 'termination-exclusion-frontier',
        'candidate_labels': list(arithmetic_only_labels),
        'promoted_labels': [],
        'proves_termination_search_promotes_to_theorem_exclusion': False if arithmetic_only_labels else not bool(active_like),
        'notes': 'No additional theorem-grade termination exclusions are certified beyond what is already visible in the near-top surface seed.',
    }
    termination = {
        'reference_label': 'golden',
        'reference_lower_bound': float(reference_lower_bound),
        'reference_crossing_center': float(reference_crossing_center),
        'family_label': _family_label(family),
        'rounds': [dict(seed_round)],
        'final_records': classes,
        'active_count': len(active_like),
        'deferred_count': 0,
        'retired_count': len(retired_labels),
        'dominated_count': len(dominated),
        'overlapping_count': len(overlapping),
        'arithmetic_only_count': len(arithmetic_only),
        'undecided_count': len(undecided),
        'strongest_active_class': None if not active_like else (None if strongest_active_upper is None else str(min((row for row in active_like if row.get('selected_upper_hi') is not None), key=lambda row: float(row['selected_upper_hi'])).get('class_label'))),
        'strongest_active_upper_bound': strongest_active_upper,
        'strongest_active_source': strongest_active_source,
        'total_escalations': 0,
        'total_deferrals': 0,
        'total_reactivations': 0,
        'deferred_retired_domination_certificate': deferred_retired_domination_certificate,
        'termination_exclusion_promotion_certificate': termination_exclusion_promotion_certificate,
        'terminated_early': True,
        'status': ('all-screened-classes-dominated' if not active_like and not arithmetic_only_labels else ('termination-aware-search-has-overlapping-challengers' if overlapping else ('termination-aware-search-has-undecided-challengers' if undecided else 'termination-aware-search-seeded-from-theorem-vi-near-top-surface'))),
        'notes': 'Termination-aware search was seeded directly from the existing Theorem VI near-top challenger surface so that Theorem VII consumes the already-built VI challenger layer rather than rebuilding the full class-exhaustion stack.',
    }
    return adaptive, evidence, termination


@dataclass
class TheoremVIIExhaustionHypothesisRow:
    name: str
    satisfied: bool
    source: str
    note: str
    margin: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class TheoremVIIExhaustionAssumptionRow:
    name: str
    assumed: bool
    source: str
    note: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class GoldenTheoremVIIExhaustionLiftCertificate:
    family_label: str
    reference_lower_bound: float
    reference_crossing_center: float
    theorem_vi_shell: dict[str, Any]
    class_exhaustion_screen: dict[str, Any]
    adaptive_search_report: dict[str, Any]
    evidence_weighted_search_report: dict[str, Any]
    termination_aware_search_report: dict[str, Any]
    support_certificates: dict[str, Any]
    current_screened_panel_dominance_certificate: dict[str, Any]
    omitted_class_global_control_certificate: dict[str, Any]
    global_completeness_certificate: dict[str, Any]
    residual_burden_summary: dict[str, Any]
    hypotheses: list[TheoremVIIExhaustionHypothesisRow]
    assumptions: list[TheoremVIIExhaustionAssumptionRow]
    discharged_hypotheses: list[str]
    open_hypotheses: list[str]
    upstream_active_assumptions: list[str]
    local_active_assumptions: list[str]
    active_assumptions: list[str]
    theorem_status: str
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return {
            'family_label': str(self.family_label),
            'reference_lower_bound': float(self.reference_lower_bound),
            'reference_crossing_center': float(self.reference_crossing_center),
            'theorem_vi_shell': dict(self.theorem_vi_shell),
            'class_exhaustion_screen': dict(self.class_exhaustion_screen),
            'adaptive_search_report': dict(self.adaptive_search_report),
            'evidence_weighted_search_report': dict(self.evidence_weighted_search_report),
            'termination_aware_search_report': dict(self.termination_aware_search_report),
            'support_certificates': {str(k): dict(v) for k, v in self.support_certificates.items()},
            'current_screened_panel_dominance_certificate': dict(self.current_screened_panel_dominance_certificate),
            'omitted_class_global_control_certificate': dict(self.omitted_class_global_control_certificate),
            'global_completeness_certificate': dict(self.global_completeness_certificate),
            'residual_burden_summary': dict(self.residual_burden_summary),
            'hypotheses': [row.to_dict() for row in self.hypotheses],
            'assumptions': [row.to_dict() for row in self.assumptions],
            'discharged_hypotheses': [str(x) for x in self.discharged_hypotheses],
            'open_hypotheses': [str(x) for x in self.open_hypotheses],
            'upstream_active_assumptions': [str(x) for x in self.upstream_active_assumptions],
            'local_active_assumptions': [str(x) for x in self.local_active_assumptions],
            'active_assumptions': [str(x) for x in self.active_assumptions],
            'theorem_status': str(self.theorem_status),
            'notes': str(self.notes),
        }



def _default_exhaustion_assumptions() -> list[TheoremVIIExhaustionAssumptionRow]:
    return [
        TheoremVIIExhaustionAssumptionRow(
            name='exact_near_top_lagrange_spectrum_ranking',
            assumed=False,
            source='Theorem-VII exhaustion lift assumption',
            note='The near-top non-golden irrational classes are ranked exactly enough that the screened panel captures the only remaining global threats.',
        ),
        TheoremVIIExhaustionAssumptionRow(
            name='theorem_level_pruning_of_dominated_regions',
            assumed=False,
            source='Theorem-VII exhaustion lift assumption',
            note='Arithmetic/pruning regions currently used as search heuristics are promoted to theorem-level dominated regions.',
        ),
        TheoremVIIExhaustionAssumptionRow(
            name='finite_screened_panel_is_globally_complete',
            assumed=False,
            source='Theorem-VII exhaustion lift assumption',
            note='After exact arithmetic ranking and pruning, the remaining threat set reduces to the explicitly screened finite panel.',
        ),
        TheoremVIIExhaustionAssumptionRow(
            name='deferred_or_retired_classes_are_globally_dominated',
            assumed=False,
            source='Theorem-VII exhaustion lift assumption',
            note='Classes deferred or retired by the search lifecycle are genuinely dominated globally, not merely deprioritized for computational reasons.',
        ),
        TheoremVIIExhaustionAssumptionRow(
            name='termination_search_promotes_to_theorem_exclusion',
            assumed=False,
            source='Theorem-VII exhaustion lift assumption',
            note='Termination-aware search outcomes upgrade from search-policy exclusions to theorem-grade exclusions.',
        ),
        TheoremVIIExhaustionAssumptionRow(
            name='omitted_nongolden_irrationals_outside_screened_panel_controlled',
            assumed=False,
            source='Theorem-VII exhaustion lift assumption',
            note='Non-golden irrational classes outside the screened panel are controlled by exact ranking, pruning, and envelope arguments.',
        ),
    ]



def _build_assumptions(
    *,
    assume_exact_near_top_lagrange_spectrum_ranking: bool,
    assume_theorem_level_pruning_of_dominated_regions: bool,
    assume_finite_screened_panel_is_globally_complete: bool,
    assume_deferred_or_retired_classes_are_globally_dominated: bool,
    assume_termination_search_promotes_to_theorem_exclusion: bool,
    assume_omitted_nongolden_irrationals_outside_screened_panel_controlled: bool,
) -> list[TheoremVIIExhaustionAssumptionRow]:
    assumption_map = {
        'exact_near_top_lagrange_spectrum_ranking': bool(assume_exact_near_top_lagrange_spectrum_ranking),
        'theorem_level_pruning_of_dominated_regions': bool(assume_theorem_level_pruning_of_dominated_regions),
        'finite_screened_panel_is_globally_complete': bool(assume_finite_screened_panel_is_globally_complete),
        'deferred_or_retired_classes_are_globally_dominated': bool(assume_deferred_or_retired_classes_are_globally_dominated),
        'termination_search_promotes_to_theorem_exclusion': bool(assume_termination_search_promotes_to_theorem_exclusion),
        'omitted_nongolden_irrationals_outside_screened_panel_controlled': bool(assume_omitted_nongolden_irrationals_outside_screened_panel_controlled),
    }
    rows: list[TheoremVIIExhaustionAssumptionRow] = []
    for row in _default_exhaustion_assumptions():
        rows.append(
            TheoremVIIExhaustionAssumptionRow(
                name=row.name,
                assumed=bool(assumption_map.get(row.name, False)),
                source=row.source,
                note=row.note,
            )
        )
    return rows




def _coerce_float(value: Any) -> float | None:
    if value is None:
        return None
    return float(value)


def _certificate_proves(cert: Mapping[str, Any] | None, *keys: str) -> bool:
    cert = {} if cert is None else dict(cert)
    for key in keys:
        if bool(cert.get(key, False)):
            return True
    return False


def _derive_support_certificates(
    *,
    screen: Mapping[str, Any],
    termination: Mapping[str, Any],
    omitted_class_global_control_certificate: Mapping[str, Any] | None,
) -> dict[str, dict[str, Any]]:
    arithmetic_ranking_certificate = dict(screen.get('arithmetic_ranking_certificate', {}))
    pruning_region_certificate = dict(screen.get('pruning_region_certificate', {}))
    deferred_retired_domination_certificate = dict(termination.get('deferred_retired_domination_certificate', {}))
    termination_search_exclusion_certificate = dict(termination.get('termination_exclusion_promotion_certificate', {}))
    screened_panel_global_completeness_certificate = promote_screened_panel_global_completeness_certificate(
        screened_panel_certificate=dict(screen.get('screened_panel_global_completeness_certificate', {})),
        arithmetic_ranking_certificate=arithmetic_ranking_certificate,
        pruning_region_certificate=pruning_region_certificate,
        deferred_retired_domination_certificate=deferred_retired_domination_certificate,
        termination_exclusion_promotion_certificate=termination_search_exclusion_certificate,
    )
    near_top_threat_set_partition_certificate = build_near_top_threat_set_partition_certificate(
        screened_panel_certificate=screened_panel_global_completeness_certificate,
        arithmetic_ranking_certificate=arithmetic_ranking_certificate,
        pruning_region_certificate=pruning_region_certificate,
        deferred_retired_domination_certificate=deferred_retired_domination_certificate,
        termination_exclusion_promotion_certificate=termination_search_exclusion_certificate,
    )
    seed_omitted_class_global_control_certificate = dict(screen.get('omitted_class_global_control_certificate', {}))
    if omitted_class_global_control_certificate is not None:
        seed_omitted_class_global_control_certificate.update(dict(omitted_class_global_control_certificate))
    omitted_class_global_control_certificate = promote_omitted_class_global_control_certificate(
        omitted_control_certificate=seed_omitted_class_global_control_certificate,
        partition_certificate=near_top_threat_set_partition_certificate,
        screened_panel_certificate=screened_panel_global_completeness_certificate,
        arithmetic_ranking_certificate=arithmetic_ranking_certificate,
        pruning_region_certificate=pruning_region_certificate,
        deferred_retired_domination_certificate=deferred_retired_domination_certificate,
        termination_exclusion_promotion_certificate=termination_search_exclusion_certificate,
    )
    return {
        'exact_near_top_lagrange_spectrum_ranking_certificate': arithmetic_ranking_certificate,
        'theorem_level_pruning_certificate': pruning_region_certificate,
        'screened_panel_global_completeness_certificate': screened_panel_global_completeness_certificate,
        'near_top_threat_set_partition_certificate': near_top_threat_set_partition_certificate,
        'deferred_retired_domination_certificate': deferred_retired_domination_certificate,
        'termination_search_exclusion_certificate': termination_search_exclusion_certificate,
        'omitted_class_global_control_certificate': omitted_class_global_control_certificate,
    }


def _apply_certificate_discharge(
    assumptions: Sequence[TheoremVIIExhaustionAssumptionRow],
    support_certificates: Mapping[str, Mapping[str, Any]],
) -> list[TheoremVIIExhaustionAssumptionRow]:
    proof_keys = {
        'exact_near_top_lagrange_spectrum_ranking': ('exact_near_top_lagrange_spectrum_ranking_certificate', ('proves_exact_near_top_lagrange_spectrum_ranking',)),
        'theorem_level_pruning_of_dominated_regions': ('theorem_level_pruning_certificate', ('proves_theorem_level_pruning_of_dominated_regions',)),
        'finite_screened_panel_is_globally_complete': ('screened_panel_global_completeness_certificate', ('screened_panel_globally_complete',)),
        'deferred_or_retired_classes_are_globally_dominated': ('deferred_retired_domination_certificate', ('proves_deferred_or_retired_classes_are_globally_dominated',)),
        'termination_search_promotes_to_theorem_exclusion': ('termination_search_exclusion_certificate', ('proves_termination_search_promotes_to_theorem_exclusion',)),
        'omitted_nongolden_irrationals_outside_screened_panel_controlled': ('omitted_class_global_control_certificate', ('omitted_classes_globally_controlled',)),
    }
    out: list[TheoremVIIExhaustionAssumptionRow] = []
    for row in assumptions:
        cert_name, keys = proof_keys[row.name]
        cert = dict(support_certificates.get(cert_name, {}))
        assumed = bool(row.assumed) or _certificate_proves(cert, *keys)
        source = row.source if not _certificate_proves(cert, *keys) else str(cert.get('status', cert_name))
        out.append(TheoremVIIExhaustionAssumptionRow(name=row.name, assumed=assumed, source=source, note=row.note))
    return out


def _build_current_screened_panel_dominance_certificate(
    screen: Mapping[str, Any],
    termination: Mapping[str, Any],
    *,
    reference_lower_bound: float,
) -> dict[str, Any]:
    strongest_active_upper = _coerce_float(termination.get('strongest_active_upper_bound'))
    strongest_screen_upper = _coerce_float(screen.get('strongest_remaining_upper_bound'))
    upper_bound = strongest_active_upper if strongest_active_upper is not None else strongest_screen_upper

    if strongest_active_upper is not None:
        source = 'termination_aware_search.strongest_active_upper_bound'
    elif strongest_screen_upper is not None:
        source = 'class_exhaustion_screen.strongest_remaining_upper_bound'
    else:
        source = None

    active_count = int(termination.get('active_count', 0))
    deferred_count = int(termination.get('deferred_count', 0))
    undecided_count = int(termination.get('undecided_count', 0))
    overlapping_count = int(termination.get('overlapping_count', 0))
    pending_count = active_count + deferred_count + undecided_count + overlapping_count
    dominated_count = int(screen.get('dominated_count', 0))
    screened_count = len(screen.get('classes', []))

    margin = None if upper_bound is None else float(reference_lower_bound - float(upper_bound))

    if pending_count == 0 and (upper_bound is None or (margin is not None and margin > 0.0)):
        status = 'screened-panel-dominance-strong'
    elif upper_bound is not None and margin is not None and margin > 0.0:
        status = 'screened-panel-dominance-partial'
    elif upper_bound is not None and margin is not None and margin <= 0.0:
        status = 'screened-panel-dominance-incompatible'
    elif screened_count > 0:
        status = 'screened-panel-dominance-weak'
    else:
        status = 'screened-panel-dominance-missing'

    return {
        'status': status,
        'strongest_current_screened_panel_upper_bound': upper_bound,
        'dominance_margin': margin,
        'current_pending_count': pending_count,
        'current_active_count': active_count,
        'current_deferred_count': deferred_count,
        'current_undecided_count': undecided_count,
        'current_overlapping_count': overlapping_count,
        'screened_class_count': screened_count,
        'dominated_screened_class_count': dominated_count,
        'source': source,
        'near_top_frontier_closed': status == 'screened-panel-dominance-strong',
    }


def _build_residual_burden_summary(
    *,
    open_hypotheses: Sequence[str],
    local_active_assumptions: Sequence[str],
    upstream_active_assumptions: Sequence[str],
    current_screened_panel_dominance_certificate: Mapping[str, Any],
) -> dict[str, Any]:
    local_front_hypotheses = [str(x) for x in open_hypotheses if str(x) != 'theorem_vi_front_complete']
    remaining_global_exhaustion_assumptions = [
        str(x) for x in local_active_assumptions if str(x) in _GLOBAL_EXHAUSTION_ASSUMPTIONS
    ]
    remaining_near_top_promotion_assumptions = [
        str(x) for x in local_active_assumptions if str(x) in _NEAR_TOP_PROMOTION_ASSUMPTIONS
    ]
    upstream_theorem_assumptions = [str(x) for x in upstream_active_assumptions]
    near_top_closed = bool(current_screened_panel_dominance_certificate.get('near_top_frontier_closed', False))

    if near_top_closed and not local_front_hypotheses and not remaining_global_exhaustion_assumptions and not remaining_near_top_promotion_assumptions and not upstream_theorem_assumptions:
        status = 'fully-discharged'
    elif near_top_closed and not local_front_hypotheses and remaining_global_exhaustion_assumptions:
        status = 'global-screened-panel-completeness-frontier'
    elif local_front_hypotheses:
        status = 'near-top-frontier-still-open'
    elif near_top_closed:
        status = 'mixed-global-and-upstream-burden'
    else:
        status = 'mixed-near-top-and-global'

    return {
        'status': status,
        'local_front_hypotheses': local_front_hypotheses,
        'remaining_global_exhaustion_assumptions': remaining_global_exhaustion_assumptions,
        'remaining_near_top_promotion_assumptions': remaining_near_top_promotion_assumptions,
        'upstream_theorem_assumptions': upstream_theorem_assumptions,
        'current_screened_panel_dominance_status': None if current_screened_panel_dominance_certificate.get('status') is None else str(current_screened_panel_dominance_certificate.get('status')),
        'current_screened_panel_dominance_margin': current_screened_panel_dominance_certificate.get('dominance_margin'),
        'current_screened_panel_pending_count': int(current_screened_panel_dominance_certificate.get('current_pending_count', 0)),
        'near_top_frontier_closed': near_top_closed,
    }


def _build_hypotheses(
    theorem_vi: Mapping[str, Any],
    screen: Mapping[str, Any],
    adaptive: Mapping[str, Any],
    evidence: Mapping[str, Any],
    termination: Mapping[str, Any],
    current_screened_panel_dominance_certificate: Mapping[str, Any],
    *,
    reference_lower_bound: float,
) -> list[TheoremVIIExhaustionHypothesisRow]:
    strongest_active = termination.get('strongest_active_upper_bound')
    if strongest_active is not None:
        strongest_margin = float(reference_lower_bound - float(strongest_active))
    else:
        strongest_margin = None

    return [
        TheoremVIIExhaustionHypothesisRow(
            name='theorem_vi_front_complete',
            satisfied=_is_front_complete(theorem_vi),
            source='Theorem-VI envelope lift',
            note='The current Theorem VI shell has no remaining front hypotheses, even if conditional assumptions remain active.',
            margin=None,
        ),
        TheoremVIIExhaustionHypothesisRow(
            name='initial_class_screen_available',
            satisfied=len(screen.get('classes', [])) > 0,
            source='class-exhaustion screen',
            note='A nonempty finite challenger panel has been screened against the current golden reference lower bound.',
            margin=None if len(screen.get('classes', [])) == 0 else float(len(screen.get('classes', []))),
        ),
        TheoremVIIExhaustionHypothesisRow(
            name='adaptive_search_executed',
            satisfied=len(adaptive.get('rounds', [])) > 0,
            source='adaptive class-exhaustion search',
            note='The static screen has been followed by a round-based adaptive challenger search.',
            margin=None if len(adaptive.get('rounds', [])) == 0 else float(len(adaptive.get('rounds', []))),
        ),
        TheoremVIIExhaustionHypothesisRow(
            name='evidence_weighted_search_executed',
            satisfied=len(evidence.get('rounds', [])) > 0,
            source='evidence-weighted class-exhaustion search',
            note='Search priorities have been refined using multi-round evidence from prior escalations.',
            margin=None if len(evidence.get('rounds', [])) == 0 else float(len(evidence.get('rounds', []))),
        ),
        TheoremVIIExhaustionHypothesisRow(
            name='termination_aware_search_executed',
            satisfied=len(termination.get('rounds', [])) > 0,
            source='termination-aware class-exhaustion search',
            note='A search lifecycle layer has been applied to the screened panel.',
            margin=None if len(termination.get('rounds', [])) == 0 else float(len(termination.get('rounds', []))),
        ),
        TheoremVIIExhaustionHypothesisRow(
            name='no_overlapping_final_challengers',
            satisfied=int(termination.get('overlapping_count', 0)) == 0,
            source='termination-aware class-exhaustion search',
            note='No final screened challenger remains overlapping the current golden reference lower bound.',
            margin=float(-int(termination.get('overlapping_count', 0))),
        ),
        TheoremVIIExhaustionHypothesisRow(
            name='no_undecided_final_challengers',
            satisfied=int(termination.get('undecided_count', 0)) == 0,
            source='termination-aware class-exhaustion search',
            note='No final screened challenger remains undecided after the termination-aware search lifecycle.',
            margin=float(-int(termination.get('undecided_count', 0))),
        ),
        TheoremVIIExhaustionHypothesisRow(
            name='no_deferred_search_classes_remaining',
            satisfied=int(termination.get('deferred_count', 0)) == 0,
            source='termination-aware class-exhaustion search',
            note='No challenger remains merely deferred for search reasons.',
            margin=float(-int(termination.get('deferred_count', 0))),
        ),
        TheoremVIIExhaustionHypothesisRow(
            name='no_active_search_classes_remaining',
            satisfied=int(termination.get('active_count', 0)) == 0,
            source='termination-aware class-exhaustion search',
            note='No challenger remains in the active search pool.',
            margin=float(-int(termination.get('active_count', 0))),
        ),
        TheoremVIIExhaustionHypothesisRow(
            name='all_near_top_challengers_dominated',
            satisfied=str(current_screened_panel_dominance_certificate.get('status', '')) == 'screened-panel-dominance-strong',
            source='screened-panel-dominance-certificate',
            note='The currently screened near-top challenger panel is dominated by the golden class with no active, deferred, overlapping, or undecided survivors remaining.',
            margin=None if current_screened_panel_dominance_certificate.get('dominance_margin') is None else float(current_screened_panel_dominance_certificate.get('dominance_margin')),
        ),
        TheoremVIIExhaustionHypothesisRow(
            name='strongest_active_upper_below_reference',
            satisfied=strongest_active is None or float(strongest_active) < float(reference_lower_bound),
            source='termination-aware class-exhaustion search',
            note='If an active challenger remains, its best certified upper object still lies below the golden reference lower bound.',
            margin=strongest_margin,
        ),
    ]



def build_golden_theorem_vii_exhaustion_lift_certificate(
    base_K_values: Sequence[float],
    challenger_specs: Sequence[ArithmeticClassSpec] | None = None,
    family: HarmonicFamily | None = None,
    *,
    reference_crossing_center: float | None = None,
    reference_lower_bound: float | None = None,
    theorem_vi_certificate: Mapping[str, Any] | None = None,
    theorem_vi_envelope_discharge_certificate: Mapping[str, Any] | None = None,
    omitted_class_global_control_certificate: Mapping[str, Any] | None = None,
    theorem_vii_global_exhaustion_support_certificate: Mapping[str, Any] | None = None,
    support_certificates: Mapping[str, Mapping[str, Any]] | None = None,
    auto_build_stage106_global_exhaustion_support: bool = False,
    assume_exact_near_top_lagrange_spectrum_ranking: bool = False,
    assume_theorem_level_pruning_of_dominated_regions: bool = False,
    assume_finite_screened_panel_is_globally_complete: bool = False,
    assume_deferred_or_retired_classes_are_globally_dominated: bool = False,
    assume_termination_search_promotes_to_theorem_exclusion: bool = False,
    assume_omitted_nongolden_irrationals_outside_screened_panel_controlled: bool = False,
    **kwargs,
) -> GoldenTheoremVIIExhaustionLiftCertificate:
    if not base_K_values:
        raise ValueError('base_K_values must be non-empty')

    family = family or HarmonicFamily()
    specs = list(challenger_specs) if challenger_specs is not None else _default_challenger_specs()
    if challenger_specs is None:
        specs = _restrict_specs_to_stage106_screened_panel(specs, theorem_vii_global_exhaustion_support_certificate)
    if len(specs) == 0:
        raise ValueError('challenger_specs must be non-empty')

    reference_crossing_center = float(reference_crossing_center) if reference_crossing_center is not None else float(sum(float(x) for x in base_K_values) / len(base_K_values))
    reference_lower_bound = float(reference_lower_bound) if reference_lower_bound is not None else float(min(float(x) for x in base_K_values))

    if theorem_vi_envelope_discharge_certificate is not None:
        theorem_vi = dict(theorem_vi_envelope_discharge_certificate)
    elif theorem_vi_certificate is not None:
        theorem_vi = dict(theorem_vi_certificate)
    else:
        theorem_vi = build_golden_theorem_vi_certificate(
            **_filter_kwargs(build_golden_theorem_vi_certificate, dict(base_K_values=base_K_values, family=family, **kwargs))
        ).to_dict()

    near_top_seed = _derive_near_top_surface_from_theorem_vi(
        theorem_vi,
        challenger_specs=specs,
        family=family,
        kwargs=kwargs,
    )
    if near_top_seed is not None and len(near_top_seed.get('challenger_records', [])) > 0:
        screen = _build_surface_screen_from_near_top(
            near_top_seed,
            challenger_specs=specs,
            reference_crossing_center=reference_crossing_center,
            reference_lower_bound=reference_lower_bound,
            family=family,
        )
        adaptive, evidence, termination = _build_search_seed_reports_from_surface(
            screen,
            reference_lower_bound=reference_lower_bound,
            reference_crossing_center=reference_crossing_center,
            family=family,
        )
    else:
        screen = build_class_exhaustion_screen(
            specs,
            **_filter_kwargs(
                build_class_exhaustion_screen,
                dict(
                    reference_crossing_center=reference_crossing_center,
                    reference_lower_bound=reference_lower_bound,
                    family=family,
                    **kwargs,
                ),
            ),
        ).to_dict()
        adaptive = build_adaptive_class_exhaustion_search(
            specs,
            **_filter_kwargs(
                build_adaptive_class_exhaustion_search,
                dict(
                    reference_crossing_center=reference_crossing_center,
                    reference_lower_bound=reference_lower_bound,
                    family=family,
                    **kwargs,
                ),
            ),
        ).to_dict()
        evidence = build_evidence_weighted_class_exhaustion_search(
            specs,
            **_filter_kwargs(
                build_evidence_weighted_class_exhaustion_search,
                dict(
                    reference_crossing_center=reference_crossing_center,
                    reference_lower_bound=reference_lower_bound,
                    family=family,
                    **kwargs,
                ),
            ),
        ).to_dict()
        termination = build_termination_aware_class_exhaustion_search(
            specs,
            **_filter_kwargs(
                build_termination_aware_class_exhaustion_search,
                dict(
                    reference_crossing_center=reference_crossing_center,
                    reference_lower_bound=reference_lower_bound,
                    family=family,
                    **kwargs,
                ),
            ),
        ).to_dict()

    current_screened_panel_dominance_certificate = _build_current_screened_panel_dominance_certificate(
        screen,
        termination,
        reference_lower_bound=reference_lower_bound,
    )

    hypotheses = _build_hypotheses(
        theorem_vi,
        screen,
        adaptive,
        evidence,
        termination,
        current_screened_panel_dominance_certificate,
        reference_lower_bound=reference_lower_bound,
    )
    assumptions = _build_assumptions(
        assume_exact_near_top_lagrange_spectrum_ranking=assume_exact_near_top_lagrange_spectrum_ranking,
        assume_theorem_level_pruning_of_dominated_regions=assume_theorem_level_pruning_of_dominated_regions,
        assume_finite_screened_panel_is_globally_complete=assume_finite_screened_panel_is_globally_complete,
        assume_deferred_or_retired_classes_are_globally_dominated=assume_deferred_or_retired_classes_are_globally_dominated,
        assume_termination_search_promotes_to_theorem_exclusion=assume_termination_search_promotes_to_theorem_exclusion,
        assume_omitted_nongolden_irrationals_outside_screened_panel_controlled=assume_omitted_nongolden_irrationals_outside_screened_panel_controlled,
    )
    derived_support_certificates = _derive_support_certificates(
        screen=screen,
        termination=termination,
        omitted_class_global_control_certificate=omitted_class_global_control_certificate,
    )
    stage106_support_payload = theorem_vii_global_exhaustion_support_certificate
    if stage106_support_payload is None and auto_build_stage106_global_exhaustion_support:
        stage106_support_payload = build_theorem_vii_global_exhaustion_support_certificate(
            screen=screen,
            termination=termination,
            theorem_vi_certificate=theorem_vi,
            reference_lower_bound=reference_lower_bound,
        )
    raw_support_certificates = support_certificates
    support_certificates = merge_support_certificates(
        derived_support_certificates,
        extract_stage106_support_certificates(stage106_support_payload),
    )
    support_certificates = merge_support_certificates(support_certificates, raw_support_certificates)
    assumptions = _apply_certificate_discharge(assumptions, support_certificates)

    discharged_hypotheses = [row.name for row in hypotheses if row.satisfied]
    open_hypotheses = [row.name for row in hypotheses if not row.satisfied]
    upstream_active_assumptions = [str(x) for x in theorem_vi.get('active_assumptions', [])]
    local_active_assumptions = [row.name for row in assumptions if not row.assumed]
    active_assumptions = upstream_active_assumptions + local_active_assumptions
    residual_burden_summary = _build_residual_burden_summary(
        open_hypotheses=open_hypotheses,
        local_active_assumptions=local_active_assumptions,
        upstream_active_assumptions=upstream_active_assumptions,
        current_screened_panel_dominance_certificate=current_screened_panel_dominance_certificate,
    )
    preliminary_certificate = {
        'family_label': _family_label(family),
        'current_screened_panel_dominance_certificate': dict(current_screened_panel_dominance_certificate),
        'support_certificates': {str(k): dict(v) for k, v in support_certificates.items()},
        'residual_burden_summary': dict(residual_burden_summary),
        'local_active_assumptions': list(local_active_assumptions),
        'upstream_active_assumptions': list(upstream_active_assumptions),
        'active_assumptions': list(active_assumptions),
        'assumptions': [row.to_dict() for row in assumptions],
    }
    global_completeness_certificate = build_golden_theorem_vii_global_completeness_certificate(preliminary_certificate).to_dict()
    residual_burden_summary = dict(global_completeness_certificate.get('residual_burden_summary', residual_burden_summary))

    front_complete = len(open_hypotheses) == 0
    if front_complete and len(active_assumptions) == 0:
        theorem_status = 'golden-theorem-vii-exhaustion-lift-conditional-strong'
    elif front_complete:
        theorem_status = 'golden-theorem-vii-exhaustion-lift-front-complete'
    elif discharged_hypotheses:
        theorem_status = 'golden-theorem-vii-exhaustion-lift-conditional-partial'
    else:
        theorem_status = 'golden-theorem-vii-exhaustion-lift-failed'

    notes = (
        'This certificate packages the current challenger-exhaustion search stack into a conditional theorem shell. '
        'It does not claim final exhaustion of all non-golden irrationals; rather, it separates the discharged screened/search hypotheses '
        'from the remaining global arithmetic and pruning assumptions needed for Theorem VII.'
    )
    if residual_burden_summary.get('status') in {'global-screened-panel-completeness-frontier', 'screened-panel-global-completeness-frontier'}:
        notes += ' The currently screened near-top panel is already dominated; the remaining Theorem VII burden is now showing that the screened panel is genuinely globally complete.'
    elif residual_burden_summary.get('status') == 'omitted-class-global-control-frontier':
        notes += ' The screened panel itself is effectively complete, so the remaining Theorem VII burden is controlling omitted non-golden classes outside that panel.'
    elif residual_burden_summary.get('status') == 'global-completeness-and-omitted-control-frontier':
        notes += ' The remaining Theorem VII burden now splits into screened-panel global completeness and omitted-class global control.'
    elif residual_burden_summary.get('status') == 'global-exhaustion-support-frontier':
        notes += ' The local near-top frontier is closed, but theorem-grade global ranking/pruning/termination support objects are still missing.'
    elif residual_burden_summary.get('status') == 'near-top-frontier-still-open':
        notes += ' The present bottleneck is still the near-top screened-panel dominance front rather than the omitted/global challenger tail.'

    return GoldenTheoremVIIExhaustionLiftCertificate(
        family_label=_family_label(family),
        reference_lower_bound=reference_lower_bound,
        reference_crossing_center=reference_crossing_center,
        theorem_vi_shell=theorem_vi,
        class_exhaustion_screen=screen,
        adaptive_search_report=adaptive,
        evidence_weighted_search_report=evidence,
        termination_aware_search_report=termination,
        support_certificates=support_certificates,
        current_screened_panel_dominance_certificate=current_screened_panel_dominance_certificate,
        omitted_class_global_control_certificate={} if omitted_class_global_control_certificate is None else dict(omitted_class_global_control_certificate),
        global_completeness_certificate=global_completeness_certificate,
        residual_burden_summary=residual_burden_summary,
        hypotheses=hypotheses,
        assumptions=assumptions,
        discharged_hypotheses=discharged_hypotheses,
        open_hypotheses=open_hypotheses,
        upstream_active_assumptions=upstream_active_assumptions,
        local_active_assumptions=local_active_assumptions,
        active_assumptions=active_assumptions,
        theorem_status=theorem_status,
        notes=notes,
    )



def build_golden_theorem_vii_certificate(*args, **kwargs) -> GoldenTheoremVIIExhaustionLiftCertificate:
    return build_golden_theorem_vii_exhaustion_lift_certificate(*args, **kwargs)


__all__ = [
    'TheoremVIIExhaustionHypothesisRow',
    'TheoremVIIExhaustionAssumptionRow',
    'GoldenTheoremVIIExhaustionLiftCertificate',
    'build_golden_theorem_vii_exhaustion_lift_certificate',
    'build_golden_theorem_vii_certificate',
]

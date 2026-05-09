from __future__ import annotations

"""Discharge packaging propagating the sharper Theorem-VI shell into Theorem VII.

This stage tightens the challenger-exhaustion side of the theorem program. The
repository already has:

* a Theorem-VI envelope discharge shell that inherits the Workstream-fed
  threshold-identification discharge package, and
* a Theorem-VII challenger-exhaustion shell that can optionally consume that
  sharper Theorem-VI package.

What remains missing is a theorem-facing object that explicitly records how much
of Theorem VII's upstream burden is removed when the discharge-aware Theorem-VI
shell is used, and that propagates that sharper shell downstream to the final
reduction layer.
"""

from dataclasses import asdict, dataclass
from inspect import signature
from typing import Any, Mapping, Sequence

from .class_campaigns import ArithmeticClassSpec
from .standard_map import HarmonicFamily
from .theorem_vi_envelope_discharge import (
    RESIDUAL_LOCAL_IDENTIFICATION_ASSUMPTION,
    build_golden_theorem_vi_discharge_certificate,
)
from .theorem_vii_exhaustion_lift import build_golden_theorem_vii_certificate
from .theorem_vii_global_completeness import build_golden_theorem_vii_global_completeness_certificate
from .theorem_vii_support_utils import merge_support_certificates


def _coerce_float(value: Any) -> float | None:
    if value is None:
        return None
    return float(value)


def _filter_kwargs(fn, kwargs: Mapping[str, Any]) -> dict[str, Any]:
    params = signature(fn).parameters
    has_var_keyword = any(p.kind == p.VAR_KEYWORD for p in params.values())
    if has_var_keyword:
        return dict(kwargs)
    return {k: v for k, v in kwargs.items() if k in params}


def _status_rank(status: str) -> int:
    status = str(status)
    if 'conditional-one-variable-strong' in status or 'conditional-two-variable-strong' in status or status.endswith('-conditional-strong') or status.endswith('-strong'):
        return 4
    if status.endswith('-front-complete') or status.endswith('-front-only'):
        return 3
    if status.endswith('-conditional-partial') or status.endswith('-partial') or status.endswith('-moderate'):
        return 2
    if status.endswith('-weak') or status.endswith('-fragile'):
        return 1
    return 0


def _is_front_complete(cert: Mapping[str, Any]) -> bool:
    return _status_rank(str(cert.get('theorem_status', ''))) >= 3 and len(cert.get('open_hypotheses', [])) == 0


_GLOBAL_EXHAUSTION_ASSUMPTIONS = {
    'finite_screened_panel_is_globally_complete',
    'omitted_nongolden_irrationals_outside_screened_panel_controlled',
}


@dataclass
class TheoremVIIExhaustionDischargeHypothesisRow:
    name: str
    satisfied: bool
    source: str
    note: str
    margin: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class TheoremVIIExhaustionDischargeAssumptionRow:
    name: str
    assumed: bool
    source: str
    note: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class GoldenTheoremVIIExhaustionDischargeLiftCertificate:
    family_label: str
    reference_lower_bound: float
    reference_crossing_center: float
    theorem_vii_shell: dict[str, Any]
    theorem_vi_discharge_shell: dict[str, Any]
    current_screened_panel_dominance_certificate: dict[str, Any]
    global_completeness_certificate: dict[str, Any]
    residual_burden_summary: dict[str, Any]
    current_near_top_exhaustion_upper_bound: float | None
    current_near_top_exhaustion_margin: float | None
    current_near_top_exhaustion_active_count: int
    current_near_top_exhaustion_deferred_count: int
    current_near_top_exhaustion_undecided_count: int
    current_near_top_exhaustion_overlapping_count: int
    current_near_top_exhaustion_pending_count: int
    current_near_top_exhaustion_source: str | None
    current_near_top_exhaustion_status: str | None
    theorem_vii_codepath_final: bool
    theorem_vii_papergrade_final: bool
    theorem_vii_residual_citation_burden: list[str]
    hypotheses: list[TheoremVIIExhaustionDischargeHypothesisRow]
    assumptions: list[TheoremVIIExhaustionDischargeAssumptionRow]
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
            'theorem_vii_shell': dict(self.theorem_vii_shell),
            'theorem_vi_discharge_shell': dict(self.theorem_vi_discharge_shell),
            'current_screened_panel_dominance_certificate': dict(self.current_screened_panel_dominance_certificate),
            'global_completeness_certificate': dict(self.global_completeness_certificate),
            'residual_burden_summary': dict(self.residual_burden_summary),
            'current_near_top_exhaustion_upper_bound': None if self.current_near_top_exhaustion_upper_bound is None else float(self.current_near_top_exhaustion_upper_bound),
            'current_near_top_exhaustion_margin': None if self.current_near_top_exhaustion_margin is None else float(self.current_near_top_exhaustion_margin),
            'current_near_top_exhaustion_active_count': int(self.current_near_top_exhaustion_active_count),
            'current_near_top_exhaustion_deferred_count': int(self.current_near_top_exhaustion_deferred_count),
            'current_near_top_exhaustion_undecided_count': int(self.current_near_top_exhaustion_undecided_count),
            'current_near_top_exhaustion_overlapping_count': int(self.current_near_top_exhaustion_overlapping_count),
            'current_near_top_exhaustion_pending_count': int(self.current_near_top_exhaustion_pending_count),
            'current_near_top_exhaustion_source': None if self.current_near_top_exhaustion_source is None else str(self.current_near_top_exhaustion_source),
            'current_near_top_exhaustion_status': None if self.current_near_top_exhaustion_status is None else str(self.current_near_top_exhaustion_status),
            'theorem_vii_codepath_final': bool(self.theorem_vii_codepath_final),
            'theorem_vii_papergrade_final': bool(self.theorem_vii_papergrade_final),
            'theorem_vii_residual_citation_burden': [str(x) for x in self.theorem_vii_residual_citation_burden],
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



def _summarize_papergrade_exhaustion_status(
    *,
    theorem_status: str,
    global_completeness_certificate: Mapping[str, Any],
    open_hypotheses: Sequence[str],
    active_assumptions: Sequence[str],
    residual_burden_summary: Mapping[str, Any],
) -> tuple[bool, bool, list[str]]:
    codepath_final = _status_rank(theorem_status) >= 3 and len(list(open_hypotheses)) == 0
    completeness_status = str(global_completeness_certificate.get('theorem_status', ''))
    residual_status = str(residual_burden_summary.get('status', ''))
    papergrade_final = (
        codepath_final
        and _status_rank(completeness_status) >= 4
        and len(list(active_assumptions)) == 0
        and residual_status not in {
            'global-screened-panel-completeness-frontier',
            'screened-panel-global-completeness-frontier',
            'global-completeness-and-omitted-control-frontier',
            'omitted-class-global-control-frontier',
            'global-exhaustion-support-frontier',
            'global-completeness-not-ready',
        }
    )
    residual_citation_burden: list[str] = []
    if not papergrade_final:
        if residual_status:
            residual_citation_burden.append(residual_status)
        completeness_residual = str((global_completeness_certificate.get('residual_burden_summary') or {}).get('status', ''))
        if completeness_residual and completeness_residual not in residual_citation_burden:
            residual_citation_burden.append(completeness_residual)
        if len(list(active_assumptions)) > 0 and 'theorem-vii-papergrade-cleanup-active-assumptions' not in residual_citation_burden:
            residual_citation_burden.append('theorem-vii-papergrade-cleanup-active-assumptions')
        if len(list(open_hypotheses)) > 0 and 'theorem-vii-open-hypotheses' not in residual_citation_burden:
            residual_citation_burden.append('theorem-vii-open-hypotheses')
    return codepath_final, papergrade_final, residual_citation_burden


def _coerce_assumption_rows(rows: Sequence[Mapping[str, Any]]) -> list[TheoremVIIExhaustionDischargeAssumptionRow]:
    out: list[TheoremVIIExhaustionDischargeAssumptionRow] = []
    for row in rows:
        out.append(
            TheoremVIIExhaustionDischargeAssumptionRow(
                name=str(row.get('name', 'unknown-assumption')),
                assumed=bool(row.get('assumed', False)),
                source=str(row.get('source', 'Theorem-VII exhaustion lift assumption')),
                note=str(row.get('note', '')),
            )
        )
    return out


def _extract_vi_current_challenger_upper(discharge: Mapping[str, Any]) -> tuple[float | None, str | None]:
    direct = _coerce_float(discharge.get('current_most_dangerous_challenger_upper'))
    if direct is not None:
        return direct, 'theorem_vi_discharge.current_most_dangerous_challenger_upper'
    theorem_vi_shell = dict(discharge.get('theorem_vi_shell', {}))
    near_relation = dict((theorem_vi_shell.get('near_top_challenger_surface') or {}).get('near_top_relation', {}))
    direct = _coerce_float(near_relation.get('most_dangerous_threshold_upper'))
    if direct is not None:
        return direct, 'theorem_vi_shell.near_top_challenger_surface.near_top_relation.most_dangerous_threshold_upper'
    proto_relation = dict((theorem_vi_shell.get('proto_envelope_bridge') or {}).get('proto_envelope_relation', {}))
    direct = _coerce_float(proto_relation.get('panel_nongolden_max_upper_bound'))
    if direct is not None:
        return direct, 'theorem_vi_shell.proto_envelope_bridge.proto_envelope_relation.panel_nongolden_max_upper_bound'
    return None, None


def _extract_near_top_exhaustion_summary(
    theorem_vii: Mapping[str, Any],
    discharge: Mapping[str, Any],
    *,
    reference_lower_bound: float,
) -> tuple[float | None, float | None, int, int, int, int, int, str | None, str | None]:
    direct_upper = _coerce_float(theorem_vii.get('current_near_top_exhaustion_upper_bound'))
    direct_margin = _coerce_float(theorem_vii.get('current_near_top_exhaustion_margin'))
    direct_active = int(theorem_vii.get('current_near_top_exhaustion_active_count', 0))
    direct_deferred = int(theorem_vii.get('current_near_top_exhaustion_deferred_count', 0))
    direct_undecided = int(theorem_vii.get('current_near_top_exhaustion_undecided_count', 0))
    direct_overlap = int(theorem_vii.get('current_near_top_exhaustion_overlapping_count', 0))
    direct_pending = int(theorem_vii.get('current_near_top_exhaustion_pending_count', direct_active + direct_deferred + direct_undecided + direct_overlap))
    direct_source = theorem_vii.get('current_near_top_exhaustion_source')
    direct_status = theorem_vii.get('current_near_top_exhaustion_status')
    if any(x is not None for x in (direct_upper, direct_margin, direct_source, direct_status)):
        return (
            direct_upper,
            direct_margin,
            direct_active,
            direct_deferred,
            direct_undecided,
            direct_overlap,
            direct_pending,
            None if direct_source is None else str(direct_source),
            None if direct_status is None else str(direct_status),
        )

    inherited_dominance = theorem_vii.get('current_screened_panel_dominance_certificate')
    if isinstance(inherited_dominance, Mapping):
        inherited = dict(inherited_dominance)
        inherited_status = str(inherited.get('status', ''))
        status_map = {
            'screened-panel-dominance-strong': 'near-top-exhaustion-strong',
            'screened-panel-dominance-partial': 'near-top-exhaustion-partial',
            'screened-panel-dominance-weak': 'near-top-exhaustion-weak',
            'screened-panel-dominance-incompatible': 'near-top-exhaustion-incompatible',
        }
        if inherited_status in status_map:
            return (
                _coerce_float(inherited.get('strongest_current_screened_panel_upper_bound')),
                _coerce_float(inherited.get('dominance_margin')),
                int(inherited.get('current_active_count', 0)),
                int(inherited.get('current_deferred_count', 0)),
                int(inherited.get('current_undecided_count', 0)),
                int(inherited.get('current_overlapping_count', 0)),
                int(inherited.get('current_pending_count', 0)),
                str(inherited.get('source', 'theorem_vii.current_screened_panel_dominance_certificate')),
                status_map[inherited_status],
            )

    vi_global = dict(discharge.get('global_nongolden_ceiling_certificate', {}))
    vi_global_upper = _coerce_float(vi_global.get('global_nongolden_upper_ceiling'))
    vi_global_margin = _coerce_float(vi_global.get('global_gap_margin'))
    vi_global_status = vi_global.get('global_ceiling_status')
    if any(x is not None for x in (vi_global_upper, vi_global_margin, vi_global_status)):
        return (
            vi_global_upper,
            vi_global_margin,
            0,
            0,
            0,
            0,
            0,
            'theorem_vi_discharge.global_nongolden_ceiling_certificate',
            None if vi_global_status is None else str(vi_global_status),
        )

    termination = dict(theorem_vii.get('termination_aware_search_report', {}))
    active_count = int(termination.get('active_count', 0))
    deferred_count = int(termination.get('deferred_count', 0))
    undecided_count = int(termination.get('undecided_count', 0))
    overlapping_count = int(termination.get('overlapping_count', 0))
    pending_count = active_count + deferred_count + undecided_count + overlapping_count

    upper_bound, upper_source = _extract_vi_current_challenger_upper(discharge)
    margin = None if upper_bound is None else float(reference_lower_bound - float(upper_bound))

    if upper_bound is None:
        status = 'near-top-exhaustion-summary-missing'
    elif margin is not None and margin > 0.0 and pending_count == 0:
        status = 'near-top-exhaustion-strong'
    elif margin is not None and margin > 0.0 and overlapping_count == 0 and undecided_count == 0:
        status = 'near-top-exhaustion-partial'
    elif margin is not None and margin > 0.0:
        status = 'near-top-exhaustion-weak'
    else:
        status = 'near-top-exhaustion-incompatible'

    source_parts = []
    if upper_source is not None:
        source_parts.append(upper_source)
    if termination:
        source_parts.append('theorem_vii_shell.termination_aware_search_report')
    source = ' + '.join(source_parts) if source_parts else None
    return upper_bound, margin, active_count, deferred_count, undecided_count, overlapping_count, pending_count, source, status



def _build_current_screened_panel_dominance_certificate(
    *,
    theorem_vii: Mapping[str, Any],
    current_near_top_exhaustion_upper_bound: float | None,
    current_near_top_exhaustion_margin: float | None,
    current_near_top_exhaustion_active_count: int,
    current_near_top_exhaustion_deferred_count: int,
    current_near_top_exhaustion_undecided_count: int,
    current_near_top_exhaustion_overlapping_count: int,
    current_near_top_exhaustion_pending_count: int,
    current_near_top_exhaustion_source: str | None,
    current_near_top_exhaustion_status: str | None,
) -> dict[str, Any]:
    inherited = theorem_vii.get('current_screened_panel_dominance_certificate')
    if isinstance(inherited, Mapping):
        data = dict(inherited)
    else:
        data = {}
    data.update({
        'status': (
            'screened-panel-dominance-strong' if current_near_top_exhaustion_status == 'near-top-exhaustion-strong'
            else 'screened-panel-dominance-partial' if current_near_top_exhaustion_status == 'near-top-exhaustion-partial'
            else 'screened-panel-dominance-weak' if current_near_top_exhaustion_status == 'near-top-exhaustion-weak'
            else 'screened-panel-dominance-incompatible' if current_near_top_exhaustion_status == 'near-top-exhaustion-incompatible'
            else 'screened-panel-dominance-missing'
        ),
        'strongest_current_screened_panel_upper_bound': current_near_top_exhaustion_upper_bound,
        'dominance_margin': current_near_top_exhaustion_margin,
        'current_active_count': int(current_near_top_exhaustion_active_count),
        'current_deferred_count': int(current_near_top_exhaustion_deferred_count),
        'current_undecided_count': int(current_near_top_exhaustion_undecided_count),
        'current_overlapping_count': int(current_near_top_exhaustion_overlapping_count),
        'current_pending_count': int(current_near_top_exhaustion_pending_count),
        'source': None if current_near_top_exhaustion_source is None else str(current_near_top_exhaustion_source),
        'near_top_frontier_closed': current_near_top_exhaustion_status == 'near-top-exhaustion-strong',
    })
    return data


def _build_residual_burden_summary(
    *,
    open_hypotheses: Sequence[str],
    local_active_assumptions: Sequence[str],
    upstream_active_assumptions: Sequence[str],
    current_screened_panel_dominance_certificate: Mapping[str, Any],
) -> dict[str, Any]:
    local_front_hypotheses = [str(x) for x in open_hypotheses if str(x) not in {'theorem_vii_front_complete', 'theorem_vi_discharge_front_complete', 'theorem_vii_upstream_burden_reduced_by_discharge', 'theorem_vi_statement_mode_explicit', 'theorem_vi_discharge_residual_hinge_isolated'}]
    remaining_global_exhaustion_assumptions = [
        str(x) for x in local_active_assumptions if str(x) in _GLOBAL_EXHAUSTION_ASSUMPTIONS
    ]
    upstream_theorem_assumptions = [str(x) for x in upstream_active_assumptions]
    near_top_closed = bool(current_screened_panel_dominance_certificate.get('near_top_frontier_closed', False))

    if near_top_closed and not local_front_hypotheses and not remaining_global_exhaustion_assumptions and not upstream_theorem_assumptions:
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
        'upstream_theorem_assumptions': upstream_theorem_assumptions,
        'current_screened_panel_dominance_status': None if current_screened_panel_dominance_certificate.get('status') is None else str(current_screened_panel_dominance_certificate.get('status')),
        'current_screened_panel_dominance_margin': current_screened_panel_dominance_certificate.get('dominance_margin'),
        'current_screened_panel_pending_count': int(current_screened_panel_dominance_certificate.get('current_pending_count', 0)),
        'near_top_frontier_closed': near_top_closed,
    }


def _build_hypotheses(
    theorem_vii: Mapping[str, Any],
    discharge: Mapping[str, Any],
    current_screened_panel_dominance_certificate: Mapping[str, Any],
) -> list[TheoremVIIExhaustionDischargeHypothesisRow]:
    old_upstream = [str(x) for x in theorem_vii.get('upstream_active_assumptions', [])]
    new_upstream = [str(x) for x in discharge.get('active_assumptions', [])]
    old_count = len(old_upstream)
    new_count = len(new_upstream)
    reduction = float(old_count - new_count)
    residual_local = {str(x) for x in discharge.get('local_active_assumptions', [])}
    statement_mode = str(discharge.get('statement_mode', 'unresolved'))
    return [
        TheoremVIIExhaustionDischargeHypothesisRow(
            name='theorem_vii_front_complete',
            satisfied=_is_front_complete(theorem_vii),
            source='Theorem-VII exhaustion lift',
            note='The current challenger-exhaustion shell has no remaining open front hypotheses before discharge propagation.',
            margin=None,
        ),
        TheoremVIIExhaustionDischargeHypothesisRow(
            name='theorem_vi_discharge_front_complete',
            satisfied=_is_front_complete(discharge),
            source='Theorem-VI envelope discharge lift',
            note='The discharge-aware Theorem VI shell has no remaining open front hypotheses.',
            margin=None,
        ),
        TheoremVIIExhaustionDischargeHypothesisRow(
            name='theorem_vi_discharge_residual_hinge_isolated',
            satisfied=residual_local.issubset({RESIDUAL_LOCAL_IDENTIFICATION_ASSUMPTION}),
            source='Theorem-VI envelope discharge lift',
            note='After propagation into Theorem VII, the only residual local upstream hinge from identification remains the localized compatibility-window identification assumption.',
            margin=None if not residual_local else float(len(residual_local)),
        ),
        TheoremVIIExhaustionDischargeHypothesisRow(
            name='all_near_top_challengers_dominated',
            satisfied=bool(current_screened_panel_dominance_certificate.get('near_top_frontier_closed', False)),
            source='screened-panel-dominance-certificate',
            note='The screened near-top challenger panel is dominated after feeding the discharge-aware Theorem VI shell into Theorem VII.',
            margin=None if current_screened_panel_dominance_certificate.get('dominance_margin') is None else float(current_screened_panel_dominance_certificate.get('dominance_margin')),
        ),
        TheoremVIIExhaustionDischargeHypothesisRow(
            name='theorem_vii_upstream_burden_reduced_by_discharge',
            satisfied=new_count <= old_count,
            source='comparison of Theorem-VII upstream assumptions before/after discharge',
            note='Replacing the older Theorem VI shell with the discharge-aware shell should weakly reduce the number of upstream active assumptions carried by Theorem VII.',
            margin=reduction,
        ),
        TheoremVIIExhaustionDischargeHypothesisRow(
            name='theorem_vi_statement_mode_explicit',
            satisfied=statement_mode in {'one-variable', 'two-variable', 'unresolved'},
            source='Theorem-VI envelope discharge lift',
            note='The discharge-aware Theorem VI shell exposes an explicit arithmetic-threshold statement mode.',
            margin=None,
        ),
    ]


def build_golden_theorem_vii_exhaustion_discharge_lift_certificate(
    base_K_values: Sequence[float],
    challenger_specs: Sequence[ArithmeticClassSpec] | None = None,
    family: HarmonicFamily | None = None,
    *,
    reference_crossing_center: float | None = None,
    reference_lower_bound: float | None = None,
    theorem_vii_certificate: Mapping[str, Any] | None = None,
    theorem_vi_certificate: Mapping[str, Any] | None = None,
    theorem_vi_envelope_discharge_certificate: Mapping[str, Any] | None = None,
    theorem_vii_global_exhaustion_support_certificate: Mapping[str, Any] | None = None,
    support_certificates: Mapping[str, Mapping[str, Any]] | None = None,
    **kwargs: Any,
) -> GoldenTheoremVIIExhaustionDischargeLiftCertificate:
    if not base_K_values:
        raise ValueError('base_K_values must be non-empty')

    family = family or HarmonicFamily()
    reference_crossing_center = float(reference_crossing_center) if reference_crossing_center is not None else float(sum(float(x) for x in base_K_values) / len(base_K_values))
    reference_lower_bound = float(reference_lower_bound) if reference_lower_bound is not None else float(min(float(x) for x in base_K_values))

    if theorem_vii_certificate is not None:
        theorem_vii = dict(theorem_vii_certificate)
    else:
        theorem_vii = build_golden_theorem_vii_certificate(
            base_K_values=base_K_values,
            challenger_specs=challenger_specs,
            family=family,
            reference_crossing_center=reference_crossing_center,
            reference_lower_bound=reference_lower_bound,
            theorem_vii_global_exhaustion_support_certificate=theorem_vii_global_exhaustion_support_certificate,
            support_certificates=support_certificates,
            **_filter_kwargs(build_golden_theorem_vii_certificate, kwargs),
        ).to_dict()

    if theorem_vi_envelope_discharge_certificate is not None:
        discharge = dict(theorem_vi_envelope_discharge_certificate)
    else:
        inherited_theorem_vi = theorem_vi_certificate
        if inherited_theorem_vi is None and theorem_vii_certificate is not None:
            inherited_theorem_vi = dict(theorem_vii.get('theorem_vi_shell', {}))
        if inherited_theorem_vi is not None:
            discharge = dict(inherited_theorem_vi)
            if discharge.get('current_most_dangerous_challenger_upper') is None:
                current_local = dict(discharge.get('current_local_top_gap_certificate', {}))
                if current_local.get('current_most_dangerous_challenger_upper') is not None:
                    discharge['current_most_dangerous_challenger_upper'] = current_local.get('current_most_dangerous_challenger_upper')
            note = str(discharge.get('notes', ''))
            if 'proxy for Theorem VII discharge propagation' not in note:
                discharge['notes'] = (note + ' ' if note else '') + 'This shell is being reused as a proxy for Theorem VII discharge propagation because no dedicated Theorem VI discharge certificate was supplied.'
        else:
            discharge = build_golden_theorem_vi_discharge_certificate(
                base_K_values=base_K_values,
                family=family,
                **_filter_kwargs(build_golden_theorem_vi_discharge_certificate, kwargs),
            ).to_dict()

    inherited_support_certificates = {}
    if isinstance(theorem_vii.get('support_certificates'), Mapping):
        inherited_support_certificates = dict(theorem_vii.get('support_certificates', {}))
    if isinstance(theorem_vii.get('global_completeness_certificate'), Mapping):
        inherited_support_certificates = merge_support_certificates(
            inherited_support_certificates,
            theorem_vii.get('global_completeness_certificate', {}).get('support_certificates', {}),
        )
    inherited_support_certificates = merge_support_certificates(inherited_support_certificates, support_certificates)
    if isinstance(theorem_vii_global_exhaustion_support_certificate, Mapping):
        inherited_support_certificates = merge_support_certificates(
            inherited_support_certificates,
            theorem_vii_global_exhaustion_support_certificate.get('support_certificates', theorem_vii_global_exhaustion_support_certificate),
        )

    assumptions = _coerce_assumption_rows(theorem_vii.get('assumptions', []))
    local_active_assumptions = [str(x) for x in theorem_vii.get('local_active_assumptions', [])]
    upstream_active_assumptions = [str(x) for x in discharge.get('active_assumptions', [])]
    active_assumptions = upstream_active_assumptions + [x for x in local_active_assumptions if x not in upstream_active_assumptions]

    near_top_reference_lower_bound = _coerce_float(theorem_vii.get('reference_lower_bound'))
    if near_top_reference_lower_bound is None:
        near_top_reference_lower_bound = float(reference_lower_bound)
    current_near_top_exhaustion_upper_bound, current_near_top_exhaustion_margin, current_near_top_exhaustion_active_count, current_near_top_exhaustion_deferred_count, current_near_top_exhaustion_undecided_count, current_near_top_exhaustion_overlapping_count, current_near_top_exhaustion_pending_count, current_near_top_exhaustion_source, current_near_top_exhaustion_status = _extract_near_top_exhaustion_summary(
        theorem_vii,
        discharge,
        reference_lower_bound=float(near_top_reference_lower_bound),
    )

    current_screened_panel_dominance_certificate = _build_current_screened_panel_dominance_certificate(
        theorem_vii=theorem_vii,
        current_near_top_exhaustion_upper_bound=current_near_top_exhaustion_upper_bound,
        current_near_top_exhaustion_margin=current_near_top_exhaustion_margin,
        current_near_top_exhaustion_active_count=current_near_top_exhaustion_active_count,
        current_near_top_exhaustion_deferred_count=current_near_top_exhaustion_deferred_count,
        current_near_top_exhaustion_undecided_count=current_near_top_exhaustion_undecided_count,
        current_near_top_exhaustion_overlapping_count=current_near_top_exhaustion_overlapping_count,
        current_near_top_exhaustion_pending_count=current_near_top_exhaustion_pending_count,
        current_near_top_exhaustion_source=current_near_top_exhaustion_source,
        current_near_top_exhaustion_status=current_near_top_exhaustion_status,
    )

    family_label = str(theorem_vii.get('family_label', 'standard-sine'))
    hypotheses = _build_hypotheses(theorem_vii, discharge, current_screened_panel_dominance_certificate)
    discharged_hypotheses = [row.name for row in hypotheses if row.satisfied]
    open_hypotheses = [row.name for row in hypotheses if not row.satisfied]
    residual_burden_summary = _build_residual_burden_summary(
        open_hypotheses=open_hypotheses,
        local_active_assumptions=local_active_assumptions,
        upstream_active_assumptions=upstream_active_assumptions,
        current_screened_panel_dominance_certificate=current_screened_panel_dominance_certificate,
    )
    preliminary_certificate = {
        'family_label': family_label,
        'current_screened_panel_dominance_certificate': dict(current_screened_panel_dominance_certificate),
        'support_certificates': {str(k): dict(v) for k, v in inherited_support_certificates.items()},
        'residual_burden_summary': dict(residual_burden_summary),
        'local_active_assumptions': list(local_active_assumptions),
        'upstream_active_assumptions': list(upstream_active_assumptions),
        'active_assumptions': list(active_assumptions),
        'assumptions': [row.to_dict() for row in assumptions],
    }
    global_completeness_certificate = build_golden_theorem_vii_global_completeness_certificate(preliminary_certificate).to_dict()
    residual_burden_summary = dict(global_completeness_certificate.get('residual_burden_summary', residual_burden_summary))
    local_active_assumptions = [str(x) for x in global_completeness_certificate.get('local_active_assumptions', local_active_assumptions)]
    upstream_active_assumptions = [str(x) for x in global_completeness_certificate.get('upstream_active_assumptions', upstream_active_assumptions)]
    active_assumptions = upstream_active_assumptions + [x for x in local_active_assumptions if x not in upstream_active_assumptions]
    assumptions = _coerce_assumption_rows(global_completeness_certificate.get('assumptions', [row.to_dict() for row in assumptions]))

    if not open_hypotheses and not active_assumptions:
        theorem_status = 'golden-theorem-vii-exhaustion-discharge-lift-conditional-strong'
        notes = (
            'The challenger-exhaustion front is closed, the discharge-aware Theorem VI front is closed, and no active upstream or local assumptions remain. '
            'This is the strongest current conditional Theorem-VII statement supported by the repository after discharge propagation.'
        )
    elif not open_hypotheses:
        theorem_status = 'golden-theorem-vii-exhaustion-discharge-lift-front-complete'
        notes = (
            'The Theorem VII front and the discharge-aware Theorem VI front are both assembled. '
            'The remaining burden is now split cleanly between the reduced upstream identification/envelope burden and the local challenger-exhaustion assumptions.'
        )
    elif any(row.satisfied for row in hypotheses):
        theorem_status = 'golden-theorem-vii-exhaustion-discharge-lift-conditional-partial'
        notes = (
            'The discharge-aware Theorem VII shell exists, but one or more front hypotheses remain open. '
            'The current stage is still useful because it exposes the reduced upstream burden carried by Theorem VII.'
        )
    else:
        theorem_status = 'golden-theorem-vii-exhaustion-discharge-lift-failed'
        notes = 'The present data do not assemble into a usable discharge-aware Theorem-VII challenger-exhaustion shell.'

    theorem_vii_codepath_final, theorem_vii_papergrade_final, theorem_vii_residual_citation_burden = _summarize_papergrade_exhaustion_status(
        theorem_status=theorem_status,
        global_completeness_certificate=global_completeness_certificate,
        open_hypotheses=open_hypotheses,
        active_assumptions=active_assumptions,
        residual_burden_summary=residual_burden_summary,
    )

    if current_near_top_exhaustion_status is not None and theorem_status != 'golden-theorem-vii-exhaustion-discharge-lift-failed':
        notes += f" Current near-top exhaustion status: {str(current_near_top_exhaustion_status)}."
        if current_near_top_exhaustion_margin is not None:
            notes += f" Near-top dominance margin relative to the current golden reference lower bound: {float(current_near_top_exhaustion_margin):.6g}."
        notes += f" Pending near-top challenger count: {int(current_near_top_exhaustion_pending_count)}."
    if residual_burden_summary.get('status') in {'global-screened-panel-completeness-frontier', 'screened-panel-global-completeness-frontier'}:
        notes += ' The near-top screened panel is already dominated after discharge propagation, so the remaining Theorem VII burden is now theorem-grade global screened-panel completeness.'
    elif residual_burden_summary.get('status') == 'omitted-class-global-control-frontier':
        notes += ' The screened panel is effectively complete after discharge propagation, so the remaining Theorem VII burden is controlling omitted non-golden classes outside that panel.'
    elif residual_burden_summary.get('status') == 'global-completeness-and-omitted-control-frontier':
        notes += ' Both sides of the remaining global Theorem VII burden are still active after discharge propagation: screened-panel completeness and omitted-class control.'
    elif residual_burden_summary.get('status') == 'global-exhaustion-support-frontier':
        notes += ' The local near-top frontier is closed after discharge propagation, but theorem-grade global ranking/pruning/termination support objects are still missing.'

    return GoldenTheoremVIIExhaustionDischargeLiftCertificate(
        family_label=family_label,
        reference_lower_bound=float(reference_lower_bound),
        reference_crossing_center=float(reference_crossing_center),
        theorem_vii_shell=theorem_vii,
        theorem_vi_discharge_shell=discharge,
        current_screened_panel_dominance_certificate=current_screened_panel_dominance_certificate,
        global_completeness_certificate=global_completeness_certificate,
        residual_burden_summary=residual_burden_summary,
        current_near_top_exhaustion_upper_bound=current_near_top_exhaustion_upper_bound,
        current_near_top_exhaustion_margin=current_near_top_exhaustion_margin,
        current_near_top_exhaustion_active_count=current_near_top_exhaustion_active_count,
        current_near_top_exhaustion_deferred_count=current_near_top_exhaustion_deferred_count,
        current_near_top_exhaustion_undecided_count=current_near_top_exhaustion_undecided_count,
        current_near_top_exhaustion_overlapping_count=current_near_top_exhaustion_overlapping_count,
        current_near_top_exhaustion_pending_count=current_near_top_exhaustion_pending_count,
        current_near_top_exhaustion_source=current_near_top_exhaustion_source,
        current_near_top_exhaustion_status=current_near_top_exhaustion_status,
        theorem_vii_codepath_final=bool(theorem_vii_codepath_final),
        theorem_vii_papergrade_final=bool(theorem_vii_papergrade_final),
        theorem_vii_residual_citation_burden=[str(x) for x in theorem_vii_residual_citation_burden],
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


build_golden_theorem_vii_discharge_certificate = build_golden_theorem_vii_exhaustion_discharge_lift_certificate

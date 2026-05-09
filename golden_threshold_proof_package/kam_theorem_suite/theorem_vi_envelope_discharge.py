from __future__ import annotations

"""Conditional theorem packaging propagating identification discharge into Theorem VI.

The repository already has:

* a Theorem-VI envelope shell built on the eta-anchor / proto-envelope / near-top
  challenger stack, and
* a threshold-identification discharge shell that feeds Workstream A into the
  renormalization-to-threshold identification package.

What this stage adds is a theorem-facing object that lets Theorem VI inherit the
*tightened* identification shell rather than the older identification shell.  In
particular, it isolates the residual local identification hinge while preserving
Theorem VI's local envelope assumptions.
"""

from dataclasses import asdict, dataclass
from inspect import signature
from typing import Any, Mapping, Sequence

from .golden_aposteriori import golden_inverse
from .standard_map import HarmonicFamily
from .theorem_vi_envelope_lift import build_golden_theorem_vi_certificate
from .threshold_identification_discharge import (
    RESIDUAL_LOCAL_IDENTIFICATION_ASSUMPTION,
    build_golden_theorem_ii_to_v_identification_discharge_certificate,
)
from .threshold_identification_transport_discharge import (
    RESIDUAL_TRANSPORT_LOCKED_IDENTIFICATION_ASSUMPTION,
    build_golden_theorem_ii_to_v_identification_transport_discharge_certificate,
)


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
    if status.endswith('-conditional-one-variable-strong') or status.endswith('-conditional-two-variable-strong') or status.endswith('-conditional-strong') or status.endswith('-strong'):
        return 4
    if status.endswith('-front-complete') or status.endswith('-front-only'):
        return 3
    if status.endswith('-conditional-partial') or status.endswith('-moderate') or status.endswith('-partial'):
        return 2
    if status.endswith('-weak'):
        return 1
    return 0



def _coerce_float(value: Any) -> float | None:
    if value is None:
        return None
    return float(value)


def _is_front_complete(cert: Mapping[str, Any]) -> bool:
    return _status_rank(str(cert.get('theorem_status', ''))) >= 3 and len(cert.get('open_hypotheses', [])) == 0


def _extract_vi_gap_geometry(theorem_vi: Mapping[str, Any]) -> tuple[float | None, float | None]:
    near_relation = dict((theorem_vi.get('near_top_challenger_surface') or {}).get('near_top_relation', {}))
    proto_relation = dict((theorem_vi.get('proto_envelope_bridge') or {}).get('proto_envelope_relation', {}))
    top_gap = _coerce_float(near_relation.get('golden_lower_minus_most_dangerous_upper'))
    if top_gap is None:
        top_gap = _coerce_float(proto_relation.get('anchor_lower_minus_panel_nongolden_upper'))
    challenger_upper = _coerce_float(near_relation.get('most_dangerous_threshold_upper'))
    if challenger_upper is None:
        challenger_upper = _coerce_float(proto_relation.get('panel_nongolden_max_upper_bound'))
    return top_gap, challenger_upper


def _extract_discharged_identified_branch_witness(cert: Mapping[str, Any]) -> tuple[list[float] | None, str | None, str | None, float | None]:
    witness = cert.get('discharged_bridge_native_tail_witness_interval')
    source = cert.get('bridge_native_tail_witness_source')
    status = cert.get('bridge_native_tail_witness_status')
    width = cert.get('discharged_bridge_native_tail_witness_width')
    if isinstance(witness, Sequence) and len(witness) == 2:
        lo = float(witness[0])
        hi = float(witness[1])
        if hi >= lo:
            return [lo, hi], None if source is None else str(source), None if status is None else str(status), None if width is None else float(width)
    witness = cert.get('identified_bridge_native_tail_witness_interval')
    width = cert.get('identified_bridge_native_tail_witness_width')
    source = cert.get('bridge_native_tail_witness_source')
    status = cert.get('bridge_native_tail_witness_status')
    if isinstance(witness, Sequence) and len(witness) == 2:
        lo = float(witness[0])
        hi = float(witness[1])
        if hi >= lo:
            return [lo, hi], None if source is None else str(source), None if status is None else str(status), None if width is None else float(width)
    return None, None, None, None


def _summarize_discharged_witness_geometry(
    theorem_vi: Mapping[str, Any],
    discharged_identified_branch_witness_interval: Sequence[float] | None,
    discharged_identified_branch_witness_width: float | None,
) -> tuple[float | None, float | None, float | None, float | None, float | None, str]:
    top_gap, challenger_upper = _extract_vi_gap_geometry(theorem_vi)
    witness_lower = None if discharged_identified_branch_witness_interval is None else float(discharged_identified_branch_witness_interval[0])
    width_vs_gap_margin = None if discharged_identified_branch_witness_width is None or top_gap is None else float(top_gap - float(discharged_identified_branch_witness_width))
    lower_vs_challenger_margin = None if witness_lower is None or challenger_upper is None else float(witness_lower - challenger_upper)
    margins = [x for x in (width_vs_gap_margin, lower_vs_challenger_margin) if x is not None]
    min_margin = None if not margins else float(min(margins))
    if discharged_identified_branch_witness_interval is None:
        status = 'discharged-witness-geometry-missing'
    elif width_vs_gap_margin is not None and lower_vs_challenger_margin is not None:
        if width_vs_gap_margin >= -1.0e-15 and lower_vs_challenger_margin > 0.0:
            status = 'discharged-witness-geometry-strong'
        elif width_vs_gap_margin >= -1.0e-15 or lower_vs_challenger_margin > 0.0:
            status = 'discharged-witness-geometry-partial'
        else:
            status = 'discharged-witness-geometry-incompatible'
    else:
        status = 'discharged-witness-geometry-unresolved'
    return top_gap, challenger_upper, width_vs_gap_margin, lower_vs_challenger_margin, min_margin, status



@dataclass
class TheoremVIEnvelopeDischargeHypothesisRow:
    name: str
    satisfied: bool
    source: str
    note: str
    margin: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class TheoremVIEnvelopeDischargeAssumptionRow:
    name: str
    assumed: bool
    source: str
    note: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class GoldenTheoremVIEnvelopeDischargeLiftCertificate:
    rho: float
    family_label: str
    statement_mode: str
    statement_mode_diagnostics: dict[str, Any]
    mode_reduction_certificate: dict[str, Any]
    mode_obstruction_certificate: dict[str, Any]
    current_local_top_gap_certificate: dict[str, Any]
    strict_golden_top_gap_certificate: dict[str, Any]
    global_nongolden_ceiling_certificate: dict[str, Any]
    global_envelope_certificate: dict[str, Any]
    global_strict_golden_top_gap_certificate: dict[str, Any]
    residual_burden_summary: dict[str, Any]
    theorem_vi_shell: dict[str, Any]
    threshold_identification_discharge_shell: dict[str, Any]
    discharged_identified_branch_witness_interval: list[float] | None
    discharged_identified_branch_witness_width: float | None
    discharged_identified_branch_witness_source: str | None
    discharged_identified_branch_witness_status: str | None
    current_top_gap_scale: float | None
    current_most_dangerous_challenger_upper: float | None
    discharged_witness_width_vs_current_top_gap_margin: float | None
    discharged_witness_lower_vs_current_near_top_challenger_upper_margin: float | None
    discharged_witness_geometry_min_margin: float | None
    discharged_witness_geometry_status: str
    hypotheses: list[TheoremVIEnvelopeDischargeHypothesisRow]
    assumptions: list[TheoremVIEnvelopeDischargeAssumptionRow]
    discharged_hypotheses: list[str]
    open_hypotheses: list[str]
    upstream_active_assumptions: list[str]
    local_active_assumptions: list[str]
    active_assumptions: list[str]
    theorem_status: str
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return {
            'rho': float(self.rho),
            'family_label': str(self.family_label),
            'statement_mode': str(self.statement_mode),
            'statement_mode_diagnostics': dict(self.statement_mode_diagnostics),
            'mode_reduction_certificate': dict(self.mode_reduction_certificate),
            'mode_obstruction_certificate': dict(self.mode_obstruction_certificate),
            'current_local_top_gap_certificate': dict(self.current_local_top_gap_certificate),
            'strict_golden_top_gap_certificate': dict(self.strict_golden_top_gap_certificate),
            'global_nongolden_ceiling_certificate': dict(self.global_nongolden_ceiling_certificate),
            'global_envelope_certificate': dict(self.global_envelope_certificate),
            'global_strict_golden_top_gap_certificate': dict(self.global_strict_golden_top_gap_certificate),
            'residual_burden_summary': dict(self.residual_burden_summary),
            'theorem_vi_shell': dict(self.theorem_vi_shell),
            'threshold_identification_discharge_shell': dict(self.threshold_identification_discharge_shell),
            'discharged_identified_branch_witness_interval': None if self.discharged_identified_branch_witness_interval is None else [float(x) for x in self.discharged_identified_branch_witness_interval],
            'discharged_identified_branch_witness_width': None if self.discharged_identified_branch_witness_width is None else float(self.discharged_identified_branch_witness_width),
            'discharged_identified_branch_witness_source': None if self.discharged_identified_branch_witness_source is None else str(self.discharged_identified_branch_witness_source),
            'discharged_identified_branch_witness_status': None if self.discharged_identified_branch_witness_status is None else str(self.discharged_identified_branch_witness_status),
            'current_top_gap_scale': None if self.current_top_gap_scale is None else float(self.current_top_gap_scale),
            'current_most_dangerous_challenger_upper': None if self.current_most_dangerous_challenger_upper is None else float(self.current_most_dangerous_challenger_upper),
            'discharged_witness_width_vs_current_top_gap_margin': None if self.discharged_witness_width_vs_current_top_gap_margin is None else float(self.discharged_witness_width_vs_current_top_gap_margin),
            'discharged_witness_lower_vs_current_near_top_challenger_upper_margin': None if self.discharged_witness_lower_vs_current_near_top_challenger_upper_margin is None else float(self.discharged_witness_lower_vs_current_near_top_challenger_upper_margin),
            'discharged_witness_geometry_min_margin': None if self.discharged_witness_geometry_min_margin is None else float(self.discharged_witness_geometry_min_margin),
            'discharged_witness_geometry_status': str(self.discharged_witness_geometry_status),
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



def _coerce_assumption_rows(rows: Sequence[Mapping[str, Any]]) -> list[TheoremVIEnvelopeDischargeAssumptionRow]:
    out: list[TheoremVIEnvelopeDischargeAssumptionRow] = []
    for row in rows:
        out.append(
            TheoremVIEnvelopeDischargeAssumptionRow(
                name=str(row.get('name', 'unknown-assumption')),
                assumed=bool(row.get('assumed', False)),
                source=str(row.get('source', 'Theorem-VI envelope lift assumption')),
                note=str(row.get('note', '')),
            )
        )
    return out



def _build_statement_mode_diagnostics(
    theorem_vi: Mapping[str, Any],
    *,
    current_top_gap_scale: float | None,
    discharged_witness_geometry_status: str,
) -> dict[str, Any]:
    inherited = theorem_vi.get('statement_mode_diagnostics')
    statement_mode = str(theorem_vi.get('statement_mode', 'unresolved'))
    if isinstance(inherited, Mapping):
        data = dict(inherited)
    else:
        if statement_mode == 'one-variable':
            residual_burden = 'promote the current finite-gap evidence into the theorem-grade one-variable eta-envelope law'
        elif statement_mode == 'two-variable':
            residual_burden = 'prove the corrected two-variable envelope theorem and control the renormalization covariate on the chosen class'
        else:
            residual_burden = 'settle whether Theorem VI is genuinely one-variable in eta or requires the corrected two-variable formulation'
        data = {
            'candidate_mode': statement_mode,
            'status': f'statement-mode-{statement_mode}',
            'residual_statement_mode_burden': residual_burden,
        }
    data['current_top_gap_scale'] = current_top_gap_scale
    data['discharged_witness_geometry_status'] = discharged_witness_geometry_status
    data['current_local_geometry_supports_top_gap_promotion'] = discharged_witness_geometry_status in {'discharged-witness-geometry-strong', 'discharged-witness-geometry-partial'}
    data['mode_reduction_certificate'] = dict(theorem_vi.get('mode_reduction_certificate', {}))
    data['mode_obstruction_certificate'] = dict(theorem_vi.get('mode_obstruction_certificate', {}))
    if 'theorem_statement_mode' not in data:
        data['theorem_statement_mode'] = str((theorem_vi.get('mode_reduction_certificate') or {}).get('theorem_mode', theorem_vi.get('statement_mode', 'unresolved')))
    return data


def _build_current_local_top_gap_certificate(
    theorem_vi: Mapping[str, Any],
    *,
    current_top_gap_scale: float | None,
    current_most_dangerous_challenger_upper: float | None,
    discharged_identified_branch_witness_interval: Sequence[float] | None,
    discharged_identified_branch_witness_width: float | None,
    discharged_witness_width_vs_current_top_gap_margin: float | None,
    discharged_witness_lower_vs_current_near_top_challenger_upper_margin: float | None,
    discharged_witness_geometry_status: str,
) -> dict[str, Any]:
    near_flags = dict((theorem_vi.get('near_top_challenger_surface') or {}).get('theorem_flags', {}))
    vi_open_hypotheses = {str(x) for x in theorem_vi.get('open_hypotheses', [])}
    top_gap_positive = bool(current_top_gap_scale is not None and current_top_gap_scale > 0.0)
    dominated = bool(near_flags.get('all_threshold_bounded_challengers_dominated', 'threshold_bounded_near_top_challengers_dominated' not in vi_open_hypotheses))
    no_undecided = bool(near_flags.get('no_undecided_challengers', 'no_undecided_near_top_challengers' not in vi_open_hypotheses))
    witness_available = discharged_identified_branch_witness_interval is not None
    witness_width_compatible = bool(discharged_witness_width_vs_current_top_gap_margin is not None and discharged_witness_width_vs_current_top_gap_margin >= -1.0e-15)
    witness_above_challenger = bool(discharged_witness_lower_vs_current_near_top_challenger_upper_margin is not None and discharged_witness_lower_vs_current_near_top_challenger_upper_margin > 0.0)

    inherited_local_status = str((theorem_vi.get('current_local_top_gap_certificate') or {}).get('status', 'current-local-top-gap-unavailable'))
    if top_gap_positive and witness_available and witness_width_compatible and witness_above_challenger and dominated and no_undecided:
        status = 'current-local-top-gap-strong'
    elif inherited_local_status == 'current-local-top-gap-screened-domination-positive' and witness_available and dominated and no_undecided:
        status = 'current-local-top-gap-screened-domination-positive'
    elif top_gap_positive and witness_available and (witness_width_compatible or witness_above_challenger):
        status = 'current-local-top-gap-partial'
    elif top_gap_positive:
        status = 'current-local-top-gap-weak-positive'
    else:
        status = 'current-local-top-gap-nonpositive'

    return {
        'top_gap_scale': current_top_gap_scale,
        'current_most_dangerous_challenger_upper': current_most_dangerous_challenger_upper,
        'discharged_identified_branch_witness_interval': None if discharged_identified_branch_witness_interval is None else [float(x) for x in discharged_identified_branch_witness_interval],
        'discharged_identified_branch_witness_width': discharged_identified_branch_witness_width,
        'witness_width_vs_top_gap_margin': discharged_witness_width_vs_current_top_gap_margin,
        'witness_lower_vs_challenger_upper_margin': discharged_witness_lower_vs_current_near_top_challenger_upper_margin,
        'witness_geometry_status': discharged_witness_geometry_status,
        'all_threshold_bounded_challengers_dominated': dominated,
        'no_undecided_near_top_challengers': no_undecided,
        'status': status,
        'local_geometry_supports_top_gap_promotion': status in {'current-local-top-gap-strong', 'current-local-top-gap-partial', 'current-local-top-gap-screened-domination-positive'},
    }


def _build_strict_golden_top_gap_certificate(
    *,
    statement_mode_diagnostics: Mapping[str, Any],
    current_local_top_gap_certificate: Mapping[str, Any],
    global_nongolden_ceiling_certificate: Mapping[str, Any],
    global_envelope_certificate: Mapping[str, Any],
    global_strict_golden_top_gap_certificate: Mapping[str, Any],
) -> dict[str, Any]:
    candidate_mode = str(statement_mode_diagnostics.get('candidate_mode', 'unresolved'))
    theorem_mode = str(statement_mode_diagnostics.get('theorem_statement_mode', candidate_mode))
    mode_lock_status = str(statement_mode_diagnostics.get('mode_lock_status', 'statement-mode-unresolved'))
    top_gap_scale = _coerce_float(current_local_top_gap_certificate.get('top_gap_scale'))
    local_status = str(current_local_top_gap_certificate.get('status', 'current-local-top-gap-unavailable'))
    local_geometry_supports = bool(current_local_top_gap_certificate.get('local_geometry_supports_top_gap_promotion', False))
    mode_locked = bool(statement_mode_diagnostics.get('theorem_mode_certified', False)) or (('supported' in mode_lock_status) and candidate_mode in {'one-variable', 'two-variable'})

    if bool(global_strict_golden_top_gap_certificate.get('global_strict_top_gap_certified', False)):
        status = f'strict-golden-top-gap-theorem-{theorem_mode}-certified'
        remaining_burden = 'none'
    elif not mode_locked and local_status != 'current-local-top-gap-screened-domination-positive':
        status = 'strict-golden-top-gap-positive-but-mode-unresolved'
        remaining_burden = 'lock the final Theorem VI statement mode before promoting the discharge-aware positive gap into a strict golden top-gap certificate'
    elif local_status == 'current-local-top-gap-screened-domination-positive':
        status = 'strict-golden-top-gap-discharged-screened-domination-certified'
        remaining_burden = 'the discharge-aware local strict golden top gap is now certified at the screened-panel level; the remaining burden is global challenger exhaustion beyond the present trusted panel, which is deferred to Theorem VII'
    elif local_status == 'current-local-top-gap-strong':
        status = 'strict-golden-top-gap-discharged-screened-panel-strong'
        remaining_burden = 'globalize the discharge-aware screened-panel strict golden top gap by proving the matching envelope law and exhausting omitted challengers beyond the current panel'
    elif local_geometry_supports:
        status = 'strict-golden-top-gap-discharged-screened-panel-partial'
        remaining_burden = 'tighten the discharge-aware witness geometry until the strict golden top gap becomes a screened-panel strong certificate, then globalize it'
    elif top_gap_scale is None or top_gap_scale <= 0.0:
        status = 'strict-golden-top-gap-unavailable'
        remaining_burden = 'the discharge-aware VI front does not yet exhibit a positive current golden-over-nongolden top gap'
    else:
        status = 'strict-golden-top-gap-positive-only'
        remaining_burden = 'the discharge-aware finite gap is positive, but the current witness geometry is still too weak to promote it to a screened-panel strict golden top-gap certificate'

    return {
        'statement_mode': theorem_mode,
        'mode_lock_status': mode_lock_status,
        'top_gap_scale': top_gap_scale,
        'local_geometry_status': local_status,
        'screened_panel_strict_top_gap_status': status,
        'screened_panel_strict_top_gap_certified': status in {'strict-golden-top-gap-discharged-screened-panel-strong', 'strict-golden-top-gap-discharged-screened-domination-certified', f'strict-golden-top-gap-theorem-{theorem_mode}-certified'},
        'screened_panel_strict_top_gap_partially_certified': status in {'strict-golden-top-gap-discharged-screened-panel-strong', 'strict-golden-top-gap-discharged-screened-panel-partial', 'strict-golden-top-gap-discharged-screened-domination-certified', f'strict-golden-top-gap-theorem-{theorem_mode}-certified'},
        'local_top_gap_promoted_beyond_raw_gap': status in {'strict-golden-top-gap-discharged-screened-panel-strong', 'strict-golden-top-gap-discharged-screened-panel-partial', 'strict-golden-top-gap-discharged-screened-domination-certified', f'strict-golden-top-gap-theorem-{theorem_mode}-certified'},
        'remaining_global_burden': remaining_burden,
        'global_nongolden_ceiling_status': None if global_nongolden_ceiling_certificate.get('global_ceiling_status') is None else str(global_nongolden_ceiling_certificate.get('global_ceiling_status')),
        'global_nongolden_upper_ceiling': _coerce_float(global_nongolden_ceiling_certificate.get('global_nongolden_upper_ceiling')),
        'global_envelope_status': None if global_envelope_certificate.get('theorem_status') is None else str(global_envelope_certificate.get('theorem_status')),
        'global_strict_top_gap_status': None if global_strict_golden_top_gap_certificate.get('global_strict_top_gap_status') is None else str(global_strict_golden_top_gap_certificate.get('global_strict_top_gap_status')),
        'global_strict_top_gap_certified': bool(global_strict_golden_top_gap_certificate.get('global_strict_top_gap_certified', False)),
        'global_strict_top_gap_margin': _coerce_float(global_strict_golden_top_gap_certificate.get('global_strict_top_gap_margin')),
    }

def _refine_local_active_assumptions(
    local_active_assumptions: Sequence[str],
    *,
    strict_golden_top_gap_certificate: Mapping[str, Any],
    global_nongolden_ceiling_certificate: Mapping[str, Any],
) -> list[str]:
    refined = [str(x) for x in local_active_assumptions]
    if bool(strict_golden_top_gap_certificate.get('local_top_gap_promoted_beyond_raw_gap', False)):
        refined = [x for x in refined if x != 'strict_golden_top_gap_theorem']
    if bool(global_nongolden_ceiling_certificate.get('global_ceiling_theorem_certified', False)):
        refined = [x for x in refined if x != 'challenger_exhaustion_beyond_current_panel']
    return refined

def _build_residual_burden_summary(
    *,
    open_hypotheses: Sequence[str],
    local_active_assumptions: Sequence[str],
    upstream_active_assumptions: Sequence[str],
    current_local_top_gap_certificate: Mapping[str, Any],
    strict_golden_top_gap_certificate: Mapping[str, Any],
    statement_mode_diagnostics: Mapping[str, Any],
    mode_reduction_certificate: Mapping[str, Any],
    global_nongolden_ceiling_certificate: Mapping[str, Any],
) -> dict[str, Any]:
    local_geometric_prefixes = (
        'discharged_',
        'identification_',
        'theorem_vi_front_complete',
        'theorem_vi_statement_mode_explicit',
    )
    local_front_hypotheses = [
        str(h) for h in open_hypotheses
        if str(h).startswith(local_geometric_prefixes)
    ]
    global_front_hypotheses = [str(h) for h in open_hypotheses if str(h) not in local_front_hypotheses]
    global_theorem_assumptions = [str(x) for x in upstream_active_assumptions] + [str(x) for x in local_active_assumptions]
    local_geometry_ready = str(current_local_top_gap_certificate.get('status', '')).endswith('strong') and not local_front_hypotheses
    theorem_mode_certified = bool(mode_reduction_certificate.get('reduction_certified', False))
    global_ceiling_certified = bool(global_nongolden_ceiling_certificate.get('global_ceiling_theorem_certified', False))
    global_gap_certified = bool(strict_golden_top_gap_certificate.get('global_strict_top_gap_certified', False))

    if local_geometry_ready and theorem_mode_certified and global_ceiling_certified and global_gap_certified and not global_theorem_assumptions:
        status = 'theorem-vi-globally-discharged'
    elif local_geometry_ready and global_theorem_assumptions:
        status = 'global-theorem-burden-only'
    elif not open_hypotheses and not global_theorem_assumptions:
        status = 'fully-discharged'
    elif local_front_hypotheses:
        status = 'local-frontier-still-open'
    else:
        status = 'mixed-local-and-global'

    return {
        'status': status,
        'local_front_hypotheses': local_front_hypotheses,
        'global_front_hypotheses': global_front_hypotheses,
        'global_theorem_assumptions': global_theorem_assumptions,
        'statement_mode_residual_burden': None if statement_mode_diagnostics.get('residual_statement_mode_burden') is None else str(statement_mode_diagnostics.get('residual_statement_mode_burden')),
        'current_local_geometry_status': None if current_local_top_gap_certificate.get('status') is None else str(current_local_top_gap_certificate.get('status')),
        'current_local_geometry_supports_top_gap_promotion': bool(current_local_top_gap_certificate.get('local_geometry_supports_top_gap_promotion', False)),
        'strict_golden_top_gap_status': None if strict_golden_top_gap_certificate.get('screened_panel_strict_top_gap_status') is None else str(strict_golden_top_gap_certificate.get('screened_panel_strict_top_gap_status')),
        'strict_golden_top_gap_promoted_beyond_raw_gap': bool(strict_golden_top_gap_certificate.get('local_top_gap_promoted_beyond_raw_gap', False)),
        'strict_golden_top_gap_remaining_burden': None if strict_golden_top_gap_certificate.get('remaining_global_burden') is None else str(strict_golden_top_gap_certificate.get('remaining_global_burden')),
        'mode_reduction_status': None if mode_reduction_certificate.get('theorem_mode_status') is None else str(mode_reduction_certificate.get('theorem_mode_status')),
        'mode_reduction_certified': theorem_mode_certified,
        'mode_reduction_burden': None if mode_reduction_certificate.get('remaining_burden') is None else str(mode_reduction_certificate.get('remaining_burden')),
        'global_ceiling_status': None if global_nongolden_ceiling_certificate.get('global_ceiling_status') is None else str(global_nongolden_ceiling_certificate.get('global_ceiling_status')),
        'global_ceiling_certified': global_ceiling_certified,
        'global_ceiling_burden': None if global_nongolden_ceiling_certificate.get('remaining_burden') is None else str(global_nongolden_ceiling_certificate.get('remaining_burden')),
    }

def _build_hypotheses(
    theorem_vi: Mapping[str, Any],
    discharge: Mapping[str, Any],
    discharged_identified_branch_witness_interval: Sequence[float] | None,
    discharged_identified_branch_witness_width: float | None,
    current_top_gap_scale: float | None,
    current_most_dangerous_challenger_upper: float | None,
    discharged_witness_width_vs_current_top_gap_margin: float | None,
    discharged_witness_lower_vs_current_near_top_challenger_upper_margin: float | None,
) -> list[TheoremVIEnvelopeDischargeHypothesisRow]:
    old_identification = theorem_vi.get('threshold_identification_shell', {})
    old_upstream = [str(x) for x in old_identification.get('active_assumptions', [])]
    new_upstream = [str(x) for x in discharge.get('active_assumptions', [])]
    old_count = len(old_upstream)
    new_count = len(new_upstream)
    reduction = float(old_count - new_count)
    residual_local = {str(x) for x in discharge.get('local_active_assumptions', [])}
    top_gap = current_top_gap_scale
    challenger_upper = current_most_dangerous_challenger_upper
    witness_width_vs_gap_margin = discharged_witness_width_vs_current_top_gap_margin
    witness_above_challenger_margin = discharged_witness_lower_vs_current_near_top_challenger_upper_margin

    return [
        TheoremVIEnvelopeDischargeHypothesisRow(
            name='theorem_vi_front_complete',
            satisfied=_is_front_complete(theorem_vi),
            source='Theorem-VI envelope lift',
            note='The present Theorem VI shell has no remaining open front hypotheses before discharge propagation.',
            margin=None,
        ),
        TheoremVIEnvelopeDischargeHypothesisRow(
            name='identification_discharge_front_complete',
            satisfied=_is_front_complete(discharge),
            source='threshold-identification discharge lift',
            note='The Workstream-fed identification discharge shell has no remaining open front hypotheses.',
            margin=None,
        ),
        TheoremVIEnvelopeDischargeHypothesisRow(
            name='identification_residual_hinge_isolated',
            satisfied=residual_local.issubset({RESIDUAL_LOCAL_IDENTIFICATION_ASSUMPTION, RESIDUAL_TRANSPORT_LOCKED_IDENTIFICATION_ASSUMPTION}),
            source='threshold-identification discharge lift',
            note='After Workstream-fed and transport-aware discharge, the only local identification hinge left standing is either the localized compatibility-window identification assumption or its sharper transport-locked uniqueness refinement.',
            margin=None if not residual_local else float(len(residual_local)),
        ),
        TheoremVIEnvelopeDischargeHypothesisRow(
            name='identification_discharge_reduces_upstream_burden',
            satisfied=new_count <= old_count,
            source='comparison of Theorem-VI upstream assumptions before/after discharge',
            note='Replacing the older identification shell with the discharge shell should weakly reduce the number of upstream active assumptions carried by Theorem VI.',
            margin=reduction,
        ),
        TheoremVIEnvelopeDischargeHypothesisRow(
            name='theorem_vi_statement_mode_explicit',
            satisfied=str(theorem_vi.get('statement_mode', '')) in {'one-variable', 'two-variable', 'unresolved'},
            source='Theorem-VI envelope lift',
            note='The present Theorem VI shell exposes an explicit arithmetic-threshold statement mode.',
            margin=None,
        ),
        TheoremVIEnvelopeDischargeHypothesisRow(
            name='discharged_identified_branch_witness_available',
            satisfied=bool(discharged_identified_branch_witness_interval is not None),
            source='threshold-identification discharge lift',
            note='The discharge-aware II->V seam supplies a concrete identified branch witness interval surviving inside the discharged identification window.',
            margin=None if discharged_identified_branch_witness_width is None else float(discharged_identified_branch_witness_width),
        ),
        TheoremVIEnvelopeDischargeHypothesisRow(
            name='discharged_witness_width_compatible_with_current_top_gap_scale',
            satisfied=bool(witness_width_vs_gap_margin is not None and witness_width_vs_gap_margin >= -1.0e-15),
            source='Theorem-VI envelope / near-top challenger geometry',
            note='The discharged identified branch witness is no wider than the current exploratory golden-over-challenger top-gap scale, so the sharpened II->V seam does not blur the present finite gap geometry used by Theorem VI.',
            margin=witness_width_vs_gap_margin,
        ),
        TheoremVIEnvelopeDischargeHypothesisRow(
            name='discharged_witness_sits_above_current_near_top_challenger_upper',
            satisfied=bool(witness_above_challenger_margin is not None and witness_above_challenger_margin > 0.0),
            source='Theorem-VI envelope / near-top challenger geometry',
            note='The lower edge of the discharged identified branch witness already lies above the current most dangerous bounded challenger upper threshold, making the sharpened II->V witness geometrically compatible with the present near-top dominance picture.',
            margin=witness_above_challenger_margin,
        ),
    ]



def build_golden_theorem_vi_envelope_discharge_lift_certificate(
    base_K_values: Sequence[float],
    family: HarmonicFamily | None = None,
    *,
    family_label: str | None = None,
    rho: float | None = None,
    theorem_vi_certificate: Mapping[str, Any] | None = None,
    threshold_identification_discharge_certificate: Mapping[str, Any] | None = None,
    threshold_identification_transport_discharge_certificate: Mapping[str, Any] | None = None,
    **kwargs: Any,
) -> GoldenTheoremVIEnvelopeDischargeLiftCertificate:
    family = family or HarmonicFamily()
    family_label = str(family_label or _family_label(family))
    rho = float(golden_inverse() if rho is None else rho)

    if theorem_vi_certificate is not None:
        theorem_vi = dict(theorem_vi_certificate)
    else:
        theorem_vi = build_golden_theorem_vi_certificate(
            base_K_values=base_K_values,
            family=family,
            family_label=family_label,
            rho=rho,
            **_filter_kwargs(build_golden_theorem_vi_certificate, kwargs),
        ).to_dict()

    if threshold_identification_transport_discharge_certificate is not None:
        discharge = dict(threshold_identification_transport_discharge_certificate)
    elif threshold_identification_discharge_certificate is not None:
        discharge = dict(threshold_identification_discharge_certificate)
    else:
        discharge = build_golden_theorem_ii_to_v_identification_transport_discharge_certificate(
            base_K_values=base_K_values,
            family=family,
            rho=rho,
            **_filter_kwargs(build_golden_theorem_ii_to_v_identification_transport_discharge_certificate, kwargs),
        ).to_dict()

    assumptions = _coerce_assumption_rows(theorem_vi.get('assumptions', []))
    local_active_assumptions = [str(x) for x in theorem_vi.get('local_active_assumptions', [])]
    upstream_active_assumptions = [str(x) for x in discharge.get('active_assumptions', [])]
    mode_reduction_certificate = dict(theorem_vi.get('mode_reduction_certificate', {}))
    mode_obstruction_certificate = dict(theorem_vi.get('mode_obstruction_certificate', {}))
    global_nongolden_ceiling_certificate = dict(theorem_vi.get('global_nongolden_ceiling_certificate', {}))
    global_envelope_certificate = dict(theorem_vi.get('global_envelope_certificate', {}))
    global_strict_golden_top_gap_certificate = dict(theorem_vi.get('strict_golden_top_gap_theorem_candidate', {}))

    discharged_identified_branch_witness_interval, discharged_identified_branch_witness_source, discharged_identified_branch_witness_status, discharged_identified_branch_witness_width = _extract_discharged_identified_branch_witness(discharge)
    current_top_gap_scale, current_most_dangerous_challenger_upper, discharged_witness_width_vs_current_top_gap_margin, discharged_witness_lower_vs_current_near_top_challenger_upper_margin, discharged_witness_geometry_min_margin, discharged_witness_geometry_status = _summarize_discharged_witness_geometry(
        theorem_vi,
        discharged_identified_branch_witness_interval,
        discharged_identified_branch_witness_width,
    )

    hypotheses = _build_hypotheses(
        theorem_vi,
        discharge,
        discharged_identified_branch_witness_interval,
        discharged_identified_branch_witness_width,
        current_top_gap_scale,
        current_most_dangerous_challenger_upper,
        discharged_witness_width_vs_current_top_gap_margin,
        discharged_witness_lower_vs_current_near_top_challenger_upper_margin,
    )
    discharged_hypotheses = [row.name for row in hypotheses if row.satisfied]
    open_hypotheses = [row.name for row in hypotheses if not row.satisfied]
    statement_mode = str(theorem_vi.get('statement_mode', 'unresolved'))
    statement_mode_diagnostics = _build_statement_mode_diagnostics(
        theorem_vi,
        current_top_gap_scale=current_top_gap_scale,
        discharged_witness_geometry_status=discharged_witness_geometry_status,
    )
    current_local_top_gap_certificate = _build_current_local_top_gap_certificate(
        theorem_vi,
        current_top_gap_scale=current_top_gap_scale,
        current_most_dangerous_challenger_upper=current_most_dangerous_challenger_upper,
        discharged_identified_branch_witness_interval=discharged_identified_branch_witness_interval,
        discharged_identified_branch_witness_width=discharged_identified_branch_witness_width,
        discharged_witness_width_vs_current_top_gap_margin=discharged_witness_width_vs_current_top_gap_margin,
        discharged_witness_lower_vs_current_near_top_challenger_upper_margin=discharged_witness_lower_vs_current_near_top_challenger_upper_margin,
        discharged_witness_geometry_status=discharged_witness_geometry_status,
    )
    strict_golden_top_gap_certificate = _build_strict_golden_top_gap_certificate(
        statement_mode_diagnostics=statement_mode_diagnostics,
        current_local_top_gap_certificate=current_local_top_gap_certificate,
        global_nongolden_ceiling_certificate=global_nongolden_ceiling_certificate,
        global_envelope_certificate=global_envelope_certificate,
        global_strict_golden_top_gap_certificate=global_strict_golden_top_gap_certificate,
    )
    local_active_assumptions = _refine_local_active_assumptions(
        local_active_assumptions,
        strict_golden_top_gap_certificate=strict_golden_top_gap_certificate,
        global_nongolden_ceiling_certificate=global_nongolden_ceiling_certificate,
    )
    active_assumptions = upstream_active_assumptions + [x for x in local_active_assumptions if x not in upstream_active_assumptions]
    residual_burden_summary = _build_residual_burden_summary(
        open_hypotheses=open_hypotheses,
        local_active_assumptions=local_active_assumptions,
        upstream_active_assumptions=upstream_active_assumptions,
        current_local_top_gap_certificate=current_local_top_gap_certificate,
        strict_golden_top_gap_certificate=strict_golden_top_gap_certificate,
        statement_mode_diagnostics=statement_mode_diagnostics,
        mode_reduction_certificate=mode_reduction_certificate,
        global_nongolden_ceiling_certificate=global_nongolden_ceiling_certificate,
    )

    if not open_hypotheses and not active_assumptions and statement_mode == 'one-variable' and bool(global_strict_golden_top_gap_certificate.get('global_strict_top_gap_certified', False)):
        theorem_status = 'golden-theorem-vi-envelope-discharge-lift-global-one-variable-strong'
        notes = (
            'The Theorem VI front is closed, the Workstream-fed identification discharge front is closed, and the current theorem mode plus nongolden ceiling already certify a global strict golden top gap in one-variable mode.'
        )
    elif not open_hypotheses and not active_assumptions and statement_mode == 'two-variable' and bool(global_strict_golden_top_gap_certificate.get('global_strict_top_gap_certified', False)):
        theorem_status = 'golden-theorem-vi-envelope-discharge-lift-global-two-variable-strong'
        notes = (
            'The Theorem VI front is closed, the Workstream-fed identification discharge front is closed, and the current corrected theorem mode plus nongolden ceiling already certify a global strict golden top gap.'
        )
    elif not open_hypotheses and not active_assumptions and statement_mode == 'one-variable':
        theorem_status = 'golden-theorem-vi-envelope-discharge-lift-conditional-one-variable-strong'
        notes = (
            'The Theorem VI front is closed, the Workstream-fed identification discharge front is closed, and no active upstream or local assumptions remain. '
            'This is the strongest current one-variable conditional Theorem-VI statement supported by the repository after discharge propagation.'
        )
    elif not open_hypotheses and not active_assumptions and statement_mode == 'two-variable':
        theorem_status = 'golden-theorem-vi-envelope-discharge-lift-conditional-two-variable-strong'
        notes = (
            'The Theorem VI front is closed, the Workstream-fed identification discharge front is closed, and no active upstream or local assumptions remain. '
            'This is the strongest current corrected two-variable conditional Theorem-VI statement supported by the repository after discharge propagation.'
        )
    elif (
        not open_hypotheses
        and statement_mode == 'one-variable'
        and bool(statement_mode_diagnostics.get('theorem_mode_certified', False))
        and str(mode_reduction_certificate.get('theorem_mode_status', '')) == 'one-variable-reduction-certified-screened-panel'
        and bool(strict_golden_top_gap_certificate.get('screened_panel_strict_top_gap_certified', False))
    ):
        theorem_status = 'golden-theorem-vi-envelope-discharge-lift-screened-one-variable-strong'
        notes = (
            'The discharge-aware Theorem VI front is locally theorem-grade in one-variable mode: the identification discharge front is closed, the screened local top-gap witness survives discharge, and the strict golden top-gap certificate is promoted beyond raw exploratory geometry. '
            'The remaining burden is the global challenger-exhaustion handoff to Theorem VII rather than additional local Theorem VI work.'
        )
    elif not open_hypotheses:
        theorem_status = 'golden-theorem-vi-envelope-discharge-lift-front-complete'
        notes = (
            'The Theorem VI envelope front and the identification discharge front are both assembled. '
            'The remaining burden is now split cleanly between the residual local identification hinge and the local envelope/top-gap/exhaustion assumptions.'
        )
    elif any(row.satisfied for row in hypotheses):
        theorem_status = 'golden-theorem-vi-envelope-discharge-lift-conditional-partial'
        notes = (
            'The discharge-aware Theorem VI shell exists, but one or more front hypotheses remain open. '
            'The current stage is still useful because it exposes the reduced upstream burden carried by Theorem VI.'
        )
    else:
        theorem_status = 'golden-theorem-vi-envelope-discharge-lift-failed'
        notes = 'The present data do not assemble into a usable discharge-aware Theorem-VI envelope shell.'

    if discharged_identified_branch_witness_width is not None and theorem_status != 'golden-theorem-vi-envelope-discharge-lift-failed':
        notes += f" Discharged identified branch witness width carried into Theorem VI: {float(discharged_identified_branch_witness_width):.6g}."
        if current_top_gap_scale is not None:
            notes += f" Current exploratory top-gap scale: {float(current_top_gap_scale):.6g}."
        if discharged_witness_lower_vs_current_near_top_challenger_upper_margin is not None:
            notes += f" Witness lower edge minus current most dangerous challenger upper: {float(discharged_witness_lower_vs_current_near_top_challenger_upper_margin):.6g}."
        notes += f" Witness-geometry status: {str(discharged_witness_geometry_status)}."
        if strict_golden_top_gap_certificate.get('screened_panel_strict_top_gap_certified', False):
            notes += ' The strict golden top gap is now promoted to a discharge-aware screened-panel certificate in the locked statement mode.'

    return GoldenTheoremVIEnvelopeDischargeLiftCertificate(
        rho=float(rho),
        family_label=family_label,
        statement_mode=statement_mode,
        statement_mode_diagnostics=statement_mode_diagnostics,
        mode_reduction_certificate=mode_reduction_certificate,
        mode_obstruction_certificate=mode_obstruction_certificate,
        current_local_top_gap_certificate=current_local_top_gap_certificate,
        strict_golden_top_gap_certificate=strict_golden_top_gap_certificate,
        global_nongolden_ceiling_certificate=global_nongolden_ceiling_certificate,
        global_envelope_certificate=global_envelope_certificate,
        global_strict_golden_top_gap_certificate=global_strict_golden_top_gap_certificate,
        residual_burden_summary=residual_burden_summary,
        theorem_vi_shell=theorem_vi,
        threshold_identification_discharge_shell=discharge,
        discharged_identified_branch_witness_interval=discharged_identified_branch_witness_interval,
        discharged_identified_branch_witness_width=discharged_identified_branch_witness_width,
        discharged_identified_branch_witness_source=discharged_identified_branch_witness_source,
        discharged_identified_branch_witness_status=discharged_identified_branch_witness_status,
        current_top_gap_scale=current_top_gap_scale,
        current_most_dangerous_challenger_upper=current_most_dangerous_challenger_upper,
        discharged_witness_width_vs_current_top_gap_margin=discharged_witness_width_vs_current_top_gap_margin,
        discharged_witness_lower_vs_current_near_top_challenger_upper_margin=discharged_witness_lower_vs_current_near_top_challenger_upper_margin,
        discharged_witness_geometry_min_margin=discharged_witness_geometry_min_margin,
        discharged_witness_geometry_status=discharged_witness_geometry_status,
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



def build_golden_theorem_vi_discharge_certificate(
    base_K_values: Sequence[float],
    family: HarmonicFamily | None = None,
    *,
    family_label: str | None = None,
    rho: float | None = None,
    **kwargs: Any,
) -> GoldenTheoremVIEnvelopeDischargeLiftCertificate:
    return build_golden_theorem_vi_envelope_discharge_lift_certificate(
        base_K_values=base_K_values,
        family=family,
        family_label=family_label,
        rho=rho,
        **kwargs,
    )

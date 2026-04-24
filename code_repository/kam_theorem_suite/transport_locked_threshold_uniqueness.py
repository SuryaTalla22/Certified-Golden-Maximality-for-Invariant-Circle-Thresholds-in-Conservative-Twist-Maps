from __future__ import annotations

"""Transport-locked threshold-branch uniqueness certification.

This module sharpens the transport-aware identification seam.

The repository already knows how to:

* build a transport-compatible irrational interval from the Theorem-V stack,
* build an identified threshold window from the II->V identification shell, and
* lock those two windows together.

What the transport-aware discharge shell still needs is a theorem-facing check
that the locked window contains only one admissible threshold branch.  The
present module packages the strongest local evidence already available in the
codebase:

* transport-certified tail windows,
* pairwise and triple transport-chain coherence,
* explicit compatible-interval/error-control data,
* late-tail contraction of the witness chain, and
* lower/upper anchor compatibility.

The resulting object is still local.  It does not claim the final threshold
identification theorem.  It does certify whether the late transport chain has
collapsed strongly enough to support the local uniqueness statement that the
transport-aware discharge shell otherwise leaves open as an assumption.
"""

from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from .theorem_v_downstream_utils import extract_theorem_v_target_interval, unwrap_theorem_v_shell


CORE_INTERVAL_SOURCES = (
    'transport_certified_control',
    'pairwise_transport_control',
    'triple_transport_cocycle_control',
    'global_transport_potential_control',
    'tail_cauchy_potential_control',
    'certified_tail_modulus_control',
    'rate_aware_tail_modulus_control',
    'theorem_v_explicit_error_control',
)


@dataclass
class TransportLockedThresholdUniquenessHypothesisRow:
    name: str
    satisfied: bool
    source: str
    note: str
    margin: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class TransportLockedThresholdUniquenessCertificate:
    family_label: str
    theorem_v_shell: dict[str, Any]
    transport_interval: list[float] | None
    identified_window: list[float] | None
    locked_window: list[float] | None
    witness_source_names: list[str]
    contraction_source_names: list[str]
    contraction_profile: list[float]
    contraction_ratio: float | None
    late_tail_contracting: bool
    transport_chain_qs: list[int]
    pairwise_chain_qs: list[int]
    triple_chain_qs: list[int]
    pair_chain_intersection: list[float] | None
    triple_chain_intersection: list[float] | None
    branch_witness_interval: list[float] | None
    branch_witness_width: float | None
    threshold_identification_interval: list[float] | None
    threshold_identification_ready: bool
    threshold_identification_margin: float | None
    residual_identification_obstruction: str | None
    residual_tail_budget: float | None
    explicit_tail_budget: float | None
    transport_tail_budget: float | None
    pairwise_tail_budget: float | None
    triple_tail_budget: float | None
    unique_local_crossings_fraction: float | None
    eventual_nesting: bool
    pairwise_coherent: bool
    triple_coherent: bool
    lower_anchor_compatible: bool
    upper_anchor_compatible: bool
    eventual_branch_coherence: bool
    uniqueness_margin: float | None
    hypotheses: list[TransportLockedThresholdUniquenessHypothesisRow]
    discharged_hypotheses: list[str]
    open_hypotheses: list[str]
    theorem_status: str
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return {
            'family_label': str(self.family_label),
            'theorem_v_shell': dict(self.theorem_v_shell),
            'transport_interval': None if self.transport_interval is None else [float(x) for x in self.transport_interval],
            'identified_window': None if self.identified_window is None else [float(x) for x in self.identified_window],
            'locked_window': None if self.locked_window is None else [float(x) for x in self.locked_window],
            'witness_source_names': [str(x) for x in self.witness_source_names],
            'contraction_source_names': [str(x) for x in self.contraction_source_names],
            'contraction_profile': [float(x) for x in self.contraction_profile],
            'contraction_ratio': None if self.contraction_ratio is None else float(self.contraction_ratio),
            'late_tail_contracting': bool(self.late_tail_contracting),
            'transport_chain_qs': [int(x) for x in self.transport_chain_qs],
            'pairwise_chain_qs': [int(x) for x in self.pairwise_chain_qs],
            'triple_chain_qs': [int(x) for x in self.triple_chain_qs],
            'pair_chain_intersection': None if self.pair_chain_intersection is None else [float(x) for x in self.pair_chain_intersection],
            'triple_chain_intersection': None if self.triple_chain_intersection is None else [float(x) for x in self.triple_chain_intersection],
            'branch_witness_interval': None if self.branch_witness_interval is None else [float(x) for x in self.branch_witness_interval],
            'branch_witness_width': None if self.branch_witness_width is None else float(self.branch_witness_width),
            'threshold_identification_interval': None if self.threshold_identification_interval is None else [float(x) for x in self.threshold_identification_interval],
            'threshold_identification_ready': bool(self.threshold_identification_ready),
            'threshold_identification_margin': None if self.threshold_identification_margin is None else float(self.threshold_identification_margin),
            'residual_identification_obstruction': None if self.residual_identification_obstruction is None else str(self.residual_identification_obstruction),
            'residual_tail_budget': None if self.residual_tail_budget is None else float(self.residual_tail_budget),
            'explicit_tail_budget': None if self.explicit_tail_budget is None else float(self.explicit_tail_budget),
            'transport_tail_budget': None if self.transport_tail_budget is None else float(self.transport_tail_budget),
            'pairwise_tail_budget': None if self.pairwise_tail_budget is None else float(self.pairwise_tail_budget),
            'triple_tail_budget': None if self.triple_tail_budget is None else float(self.triple_tail_budget),
            'unique_local_crossings_fraction': None if self.unique_local_crossings_fraction is None else float(self.unique_local_crossings_fraction),
            'eventual_nesting': bool(self.eventual_nesting),
            'pairwise_coherent': bool(self.pairwise_coherent),
            'triple_coherent': bool(self.triple_coherent),
            'lower_anchor_compatible': bool(self.lower_anchor_compatible),
            'upper_anchor_compatible': bool(self.upper_anchor_compatible),
            'eventual_branch_coherence': bool(self.eventual_branch_coherence),
            'uniqueness_margin': None if self.uniqueness_margin is None else float(self.uniqueness_margin),
            'hypotheses': [row.to_dict() for row in self.hypotheses],
            'discharged_hypotheses': [str(x) for x in self.discharged_hypotheses],
            'open_hypotheses': [str(x) for x in self.open_hypotheses],
            'theorem_status': str(self.theorem_status),
            'notes': str(self.notes),
        }


def _status_rank(status: str) -> int:
    status = str(status)
    if status.endswith('-conditional-strong') or status.endswith('-strong'):
        return 4
    if status.endswith('-front-complete') or status.endswith('-front-only'):
        return 3
    if status.endswith('-partial') or status.endswith('-moderate'):
        return 2
    if status.endswith('-weak') or status.endswith('-fragile'):
        return 1
    return 0


def _is_closed_status(status: Any) -> bool:
    return _status_rank(str(status)) >= 3


def _interval_from_payload(payload: Mapping[str, Any], *pairs: tuple[str, str]) -> list[float] | None:
    for lo_key, hi_key in pairs:
        lo = payload.get(lo_key)
        hi = payload.get(hi_key)
        if lo is None or hi is None:
            continue
        lo_f = float(lo)
        hi_f = float(hi)
        if hi_f >= lo_f:
            return [lo_f, hi_f]
    return None


def _interval_width(interval: Sequence[float] | None) -> float | None:
    if interval is None:
        return None
    return float(interval[1] - interval[0])


def _intersect_intervals(intervals: Sequence[Sequence[float] | None]) -> list[float] | None:
    usable = [(float(iv[0]), float(iv[1])) for iv in intervals if iv is not None]
    if not usable:
        return None
    lo = max(lo for lo, _ in usable)
    hi = min(hi for _, hi in usable)
    if hi < lo:
        return None
    return [float(lo), float(hi)]


def _is_subset(a: Sequence[float] | None, b: Sequence[float] | None, tol: float = 1e-15) -> bool:
    if a is None or b is None:
        return False
    return float(a[0]) >= float(b[0]) - tol and float(a[1]) <= float(b[1]) + tol


def _safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _max_optional(values: Sequence[Any]) -> float | None:
    usable = [_safe_float(v) for v in values]
    usable = [float(v) for v in usable if v is not None]
    if not usable:
        return None
    return float(max(usable))


def _min_optional(values: Sequence[Any]) -> float | None:
    usable = [_safe_float(v) for v in values]
    usable = [float(v) for v in usable if v is not None]
    if not usable:
        return None
    return float(min(usable))


def _monotone_nonincreasing(values: Sequence[float], tol: float = 1e-15) -> bool:
    return all(float(values[i + 1]) <= float(values[i]) + tol for i in range(len(values) - 1))


def _eventual_monotone_nonincreasing(values: Sequence[float], min_suffix_len: int = 3, tol: float = 1e-15) -> bool:
    if len(values) < 2:
        return False
    min_suffix_len = max(2, int(min_suffix_len))
    for start in range(max(0, len(values) - min_suffix_len + 1)):
        suffix = values[start:]
        if len(suffix) >= min_suffix_len and _monotone_nonincreasing(suffix, tol=tol):
            return True
    return False


def _extract_transport_interval(theorem_v_shell: Mapping[str, Any]) -> list[float] | None:
    return extract_theorem_v_target_interval(theorem_v_shell)



def _extract_explicit_late_suffix_interval(front: Mapping[str, Any]) -> tuple[list[float] | None, list[str], bool | None, float | None, str]:
    relation = dict(front.get('relation', {}))
    interval = _interval_from_payload(
        relation,
        ('native_late_coherent_suffix_witness_lo', 'native_late_coherent_suffix_witness_hi'),
    )
    labels = [str(x) for x in relation.get('native_late_coherent_suffix_labels', [])]
    contracting = relation.get('native_late_coherent_suffix_contracting')
    ratio = _safe_float(relation.get('native_late_coherent_suffix_contraction_ratio'))
    source_name = str(relation.get('native_late_coherent_suffix_source', 'golden_limit_bridge.native_late_coherent_suffix_witness'))
    if interval is not None:
        return interval, labels, None if contracting is None else bool(contracting), ratio, source_name

    explicit = dict(front.get('theorem_v_explicit_error_control', {}))
    interval = _interval_from_payload(
        explicit,
        ('late_coherent_suffix_interval_lo', 'late_coherent_suffix_interval_hi'),
    )
    labels = [str(x) for x in explicit.get('late_coherent_suffix_labels', [])]
    contracting = explicit.get('late_coherent_suffix_contracting')
    ratio = _safe_float(explicit.get('late_coherent_suffix_contraction_ratio'))
    return interval, labels, None if contracting is None else bool(contracting), ratio, 'theorem_v_explicit_error_late_coherent_suffix'


def _extract_core_intervals(front: Mapping[str, Any]) -> tuple[dict[str, list[float]], list[str]]:
    payload_specs: dict[str, tuple[str, tuple[tuple[str, str], ...]]] = {
        'transport_certified_control': ('transport_certified_control', (('limit_interval_lo', 'limit_interval_hi'),)),
        'pairwise_transport_control': ('pairwise_transport_control', (('pair_chain_intersection_lo', 'pair_chain_intersection_hi'), ('limit_interval_lo', 'limit_interval_hi'))),
        'triple_transport_cocycle_control': ('triple_transport_cocycle_control', (('triple_chain_intersection_lo', 'triple_chain_intersection_hi'), ('limit_interval_lo', 'limit_interval_hi'))),
        'global_transport_potential_control': ('global_transport_potential_control', (('selected_limit_interval_lo', 'selected_limit_interval_hi'), ('limit_interval_lo', 'limit_interval_hi'))),
        'tail_cauchy_potential_control': ('tail_cauchy_potential_control', (('selected_limit_interval_lo', 'selected_limit_interval_hi'), ('limit_interval_lo', 'limit_interval_hi'))),
        'certified_tail_modulus_control': ('certified_tail_modulus_control', (('selected_limit_interval_lo', 'selected_limit_interval_hi'), ('limit_interval_lo', 'limit_interval_hi'))),
        'rate_aware_tail_modulus_control': ('rate_aware_tail_modulus_control', (('modulus_rate_intersection_lo', 'modulus_rate_intersection_hi'), ('selected_limit_interval_lo', 'selected_limit_interval_hi'), ('limit_interval_lo', 'limit_interval_hi'))),
        'theorem_v_explicit_error_control': ('theorem_v_explicit_error_control', (('compatible_limit_interval_lo', 'compatible_limit_interval_hi'),)),
    }
    intervals: dict[str, list[float]] = {}
    source_names: list[str] = []
    for public_name in CORE_INTERVAL_SOURCES:
        front_key, pairs = payload_specs[public_name]
        payload = dict(front.get(front_key, {}))
        interval = _interval_from_payload(payload, *pairs)
        if interval is not None:
            intervals[public_name] = interval
            source_names.append(public_name)
    return intervals, source_names


def _best_width_from_payload(name: str, payload: Mapping[str, Any], interval: Sequence[float] | None) -> float | None:
    interval_width = _interval_width(interval)
    candidates: list[Any]
    if name == 'transport_certified_control':
        candidates = [interval_width, payload.get('limit_interval_width')]
    elif name == 'pairwise_transport_control':
        candidates = [interval_width, payload.get('pair_chain_intersection_width'), payload.get('last_pair_interval_width'), payload.get('limit_interval_width')]
    elif name == 'triple_transport_cocycle_control':
        candidates = [interval_width, payload.get('triple_chain_intersection_width'), payload.get('last_triple_interval_width'), payload.get('limit_interval_width')]
    elif name == 'global_transport_potential_control':
        candidates = [interval_width, payload.get('selected_limit_interval_width'), payload.get('last_node_interval_width')]
    elif name == 'tail_cauchy_potential_control':
        candidates = [interval_width, payload.get('selected_limit_interval_width'), payload.get('last_node_interval_width')]
    elif name == 'certified_tail_modulus_control':
        candidates = [interval_width, payload.get('selected_limit_interval_width')]
    elif name == 'rate_aware_tail_modulus_control':
        candidates = [interval_width, payload.get('modulus_rate_intersection_width'), payload.get('selected_rate_interval_width')]
    elif name == 'theorem_v_explicit_error_control':
        candidates = [interval_width, payload.get('compatible_limit_interval_width')]
    else:
        candidates = [interval_width]
    return _min_optional(candidates)


def _extract_width_profile(front: Mapping[str, Any], core_intervals: Mapping[str, Sequence[float]]) -> tuple[list[str], list[float]]:
    source_names: list[str] = []
    widths: list[float] = []
    payload_names = {
        'transport_certified_control': 'transport_certified_control',
        'pairwise_transport_control': 'pairwise_transport_control',
        'triple_transport_cocycle_control': 'triple_transport_cocycle_control',
        'global_transport_potential_control': 'global_transport_potential_control',
        'tail_cauchy_potential_control': 'tail_cauchy_potential_control',
        'certified_tail_modulus_control': 'certified_tail_modulus_control',
        'rate_aware_tail_modulus_control': 'rate_aware_tail_modulus_control',
        'theorem_v_explicit_error_control': 'theorem_v_explicit_error_control',
    }
    for name in CORE_INTERVAL_SOURCES:
        if name == 'theorem_v_explicit_error_control':
            # The explicit-error interval is a compatible outer corridor.  It can be
            # slightly wider than the deepest witness layers without indicating a
            # second branch, so we do not force it into the contraction test.
            continue
        interval = core_intervals.get(name)
        payload = dict(front.get(payload_names[name], {}))
        width = _best_width_from_payload(name, payload, interval)
        if width is not None:
            source_names.append(name)
            widths.append(float(width))
    return source_names, widths


def _select_late_branch_witness(
    *,
    locked_window: Sequence[float] | None,
    ordered_intervals: Sequence[tuple[str, Sequence[float]]],
) -> tuple[list[float] | None, list[str]]:
    usable = [(str(name), [float(interval[0]), float(interval[1])]) for name, interval in ordered_intervals]
    if not usable:
        empty_witness = None if locked_window is None else [float(locked_window[0]), float(locked_window[1])]
        empty_names = [] if locked_window is None else ['locked_window']
        return empty_witness, empty_names

    candidates: list[tuple[float, int, int, list[float], list[str]]] = []
    for start in range(len(usable)):
        suffix = usable[start:]
        names = [name for name, _ in suffix]
        intervals = [interval for _, interval in suffix]
        if locked_window is not None:
            names = ['locked_window'] + names
            intervals = [[float(locked_window[0]), float(locked_window[1])]] + intervals
        witness = _intersect_intervals(intervals)
        if witness is None:
            continue
        width = float(_interval_width(witness) or 0.0)
        candidates.append((width, start, -len(names), witness, names))

    if not candidates:
        return (None, [] if locked_window is None else ['locked_window'])

    candidates.sort(key=lambda row: (row[0], row[1], row[2]))
    _, _, _, witness, names = candidates[0]
    return witness, names


def _build_hypotheses(
    *,
    locked_window: Sequence[float] | None,
    branch_witness_interval: Sequence[float] | None,
    pairwise_coherent: bool,
    triple_coherent: bool,
    contraction_ok: bool,
    contraction_ratio: float | None,
    lower_anchor_compatible: bool,
    upper_anchor_compatible: bool,
    eventual_branch_coherence: bool,
    unique_local_crossings_fraction: float | None,
    residual_tail_budget: float | None,
    uniqueness_margin: float | None,
    threshold_identification_ready: bool,
    threshold_identification_margin: float | None,
) -> list[TransportLockedThresholdUniquenessHypothesisRow]:
    witness_width = _interval_width(branch_witness_interval)
    return [
        TransportLockedThresholdUniquenessHypothesisRow(
            name='transport_locked_window_nonempty',
            satisfied=bool(locked_window is not None),
            source='transport-aware identification seam',
            note='The identified threshold window and the transport-compatible interval intersect to form a nonempty locked window.',
            margin=_interval_width(locked_window),
        ),
        TransportLockedThresholdUniquenessHypothesisRow(
            name='branch_witness_interval_nonempty',
            satisfied=bool(branch_witness_interval is not None),
            source='late transport/pairwise/triple/global/tail interval intersection',
            note='A late coherent suffix of the transport chain and the locked window admit a common witness interval for a surviving threshold branch.',
            margin=witness_width,
        ),
        TransportLockedThresholdUniquenessHypothesisRow(
            name='eventual_branch_coherence',
            satisfied=bool(eventual_branch_coherence),
            source='transport-certified / pairwise / triple chain coherence',
            note='The late transport chain behaves like a single coherent branch rather than two incompatible continuation tracks.',
            margin=None,
        ),
        TransportLockedThresholdUniquenessHypothesisRow(
            name='eventual_nesting_or_contraction',
            satisfied=bool(contraction_ok),
            source='late transport-layer width profile',
            note='The late witness-building intervals exhibit genuine suffix contraction, even if a coarser upstream layer widens slightly.',
            margin=None if contraction_ratio is None else float(contraction_ratio),
        ),
        TransportLockedThresholdUniquenessHypothesisRow(
            name='pairwise_transport_coherent',
            satisfied=bool(pairwise_coherent),
            source='pairwise-transport-chain control',
            note='Pairwise continuation compatibility is strong enough to support a single branch witness.',
            margin=None,
        ),
        TransportLockedThresholdUniquenessHypothesisRow(
            name='triple_transport_cocycle_coherent',
            satisfied=bool(triple_coherent),
            source='triple-transport-cocycle control',
            note='Triple cocycle coherence does not indicate a branch bifurcation inside the locked window.',
            margin=None,
        ),
        TransportLockedThresholdUniquenessHypothesisRow(
            name='lower_anchor_compatible',
            satisfied=bool(lower_anchor_compatible),
            source='golden lower neighborhood anchor',
            note='The witness interval remains on the threshold side of the lower persistence anchor.',
            margin=None,
        ),
        TransportLockedThresholdUniquenessHypothesisRow(
            name='upper_anchor_compatible',
            satisfied=bool(upper_anchor_compatible),
            source='upper compatible corridor / upper-tail audit',
            note='The witness interval remains inside the compatible upper corridor used by the transport shell.',
            margin=None,
        ),
        TransportLockedThresholdUniquenessHypothesisRow(
            name='local_crossing_certification_majority',
            satisfied=bool(unique_local_crossings_fraction is not None and unique_local_crossings_fraction >= 0.5),
            source='transport-certified local branch data',
            note='A majority of the late transport-certified crossings are derivative-backed or otherwise locally unique.',
            margin=None if unique_local_crossings_fraction is None else float(unique_local_crossings_fraction),
        ),
        TransportLockedThresholdUniquenessHypothesisRow(
            name='locked_window_beats_residual_tail_budget',
            satisfied=bool(uniqueness_margin is not None and uniqueness_margin > 0.0),
            source='locked-window geometry versus residual tail budgets',
            note='The residual tail budget is too small to permit two distinct admissible branch limits inside the current locked window.',
            margin=None if uniqueness_margin is None else float(uniqueness_margin),
        ),
        TransportLockedThresholdUniquenessHypothesisRow(
            name='residual_tail_budget_explicit',
            satisfied=residual_tail_budget is not None,
            source='transport/pairwise/triple/explicit-error budgets',
            note='The late witness interval is accompanied by an explicit residual tail budget.',
            margin=None if residual_tail_budget is None else float(residual_tail_budget),
        ),
        TransportLockedThresholdUniquenessHypothesisRow(
            name='transport_locked_witness_identifies_threshold_branch',
            satisfied=bool(threshold_identification_ready),
            source='transport-locked uniqueness promotion',
            note='The coherent locked-window witness is now narrow and transport-pinned enough to serve as a theorem-facing certificate for the selected threshold branch rather than only a uniqueness hint.',
            margin=None if threshold_identification_margin is None else float(threshold_identification_margin),
        ),
    ]


def build_transport_locked_threshold_uniqueness_certificate(
    *,
    theorem_v_certificate: Mapping[str, Any],
    transport_interval: Sequence[float] | None = None,
    identified_window: Sequence[float] | None = None,
    locked_window: Sequence[float] | None = None,
    tail_budget_multiplier: float = 2.0,
) -> TransportLockedThresholdUniquenessCertificate:
    theorem_v_shell = unwrap_theorem_v_shell(theorem_v_certificate)
    family_label = str(theorem_v_shell.get('family_label', 'unknown-family'))
    front = dict(theorem_v_shell.get('convergence_front', {}))
    relation = dict(front.get('relation', {}))
    transport_interval = None if transport_interval is None else [float(transport_interval[0]), float(transport_interval[1])]
    if transport_interval is None:
        transport_interval = _extract_transport_interval(theorem_v_shell)
    identified_window = None if identified_window is None else [float(identified_window[0]), float(identified_window[1])]
    locked_window = None if locked_window is None else [float(locked_window[0]), float(locked_window[1])]
    if locked_window is None and transport_interval is not None and identified_window is not None:
        locked_window = _intersect_intervals((transport_interval, identified_window))

    core_intervals, _ = _extract_core_intervals(front)
    explicit_suffix_interval, explicit_suffix_labels, explicit_suffix_contracting, explicit_suffix_ratio, explicit_suffix_source = _extract_explicit_late_suffix_interval(front)
    ordered_intervals = []
    if explicit_suffix_interval is not None:
        ordered_intervals.append((explicit_suffix_source, explicit_suffix_interval))
    ordered_intervals.extend((name, core_intervals[name]) for name in CORE_INTERVAL_SOURCES if name in core_intervals)
    branch_witness_interval, witness_source_names = _select_late_branch_witness(
        locked_window=locked_window,
        ordered_intervals=ordered_intervals,
    )
    if explicit_suffix_interval is not None:
        witness_source_names = list(dict.fromkeys(witness_source_names))
    branch_witness_width = _interval_width(branch_witness_interval)

    transport = dict(front.get('transport_certified_control', {}))
    pairwise = dict(front.get('pairwise_transport_control', {}))
    triple = dict(front.get('triple_transport_cocycle_control', {}))
    upper_tail_status = relation.get('upper_tail_status')

    pair_chain_intersection = _interval_from_payload(pairwise, ('pair_chain_intersection_lo', 'pair_chain_intersection_hi'))
    triple_chain_intersection = _interval_from_payload(triple, ('triple_chain_intersection_lo', 'triple_chain_intersection_hi'))

    pairwise_coherent = bool(
        _is_closed_status(pairwise.get('theorem_status'))
        and (pair_chain_intersection is not None or _interval_from_payload(pairwise, ('limit_interval_lo', 'limit_interval_hi')) is not None)
    )
    triple_coherent = bool(
        _is_closed_status(triple.get('theorem_status'))
        and (triple_chain_intersection is not None or _interval_from_payload(triple, ('limit_interval_lo', 'limit_interval_hi')) is not None)
    )

    contraction_source_names, contraction_profile = _extract_width_profile(front, core_intervals)
    eventual_nesting = len(contraction_profile) >= 2 and _monotone_nonincreasing(contraction_profile)
    late_tail_contracting = bool(
        len(contraction_profile) >= 3
        and (
            _eventual_monotone_nonincreasing(contraction_profile, min_suffix_len=3)
            or contraction_profile[-1] <= 0.8 * min(contraction_profile[:-1])
        )
    )
    contraction_ok = bool(eventual_nesting or late_tail_contracting or explicit_suffix_contracting)
    contraction_ratio = None
    if explicit_suffix_ratio is not None:
        contraction_ratio = float(explicit_suffix_ratio)
    elif len(contraction_profile) >= 2 and contraction_profile[-1] > 0.0:
        contraction_ratio = float(max(contraction_profile[:-1]) / contraction_profile[-1])

    unique_local_crossings_fraction = _max_optional([
        transport.get('derivative_backed_fraction'),
        transport.get('endpoint_transport_fraction'),
        transport.get('midpoint_transport_fraction'),
    ])
    if unique_local_crossings_fraction is not None:
        unique_local_crossings_fraction = min(float(unique_local_crossings_fraction), 1.0)

    explicit = dict(front.get('theorem_v_explicit_error_control', {}))
    explicit_tail_budget = _max_optional([
        explicit.get('last_monotone_total_error_radius'),
        explicit.get('last_raw_total_error_radius'),
    ])
    transport_tail_budget = _max_optional([
        transport.get('telescoping_tail_bound'),
        transport.get('last_transport_step_bound'),
    ])
    pairwise_tail_budget = _max_optional([
        pairwise.get('telescoping_pair_tail_bound'),
        pairwise.get('last_pair_step_bound'),
    ])
    triple_tail_budget = _max_optional([
        triple.get('telescoping_triple_tail_bound'),
    ])
    residual_tail_budget = _max_optional([
        explicit_tail_budget,
        transport_tail_budget,
        pairwise_tail_budget,
        triple_tail_budget,
    ])

    lower_bound = _safe_float(relation.get('lower_bound'))
    lower_window_hi = _safe_float(relation.get('lower_window_hi'))
    lower_anchor_compatible = bool(
        branch_witness_interval is not None
        and ((lower_window_hi is not None and float(lower_window_hi) <= float(branch_witness_interval[0]) + 1e-15)
             or (lower_bound is not None and float(lower_bound) <= float(branch_witness_interval[0]) + 1e-15))
    )
    upper_anchor_compatible = bool(
        branch_witness_interval is not None
        and transport_interval is not None
        and _is_subset(branch_witness_interval, transport_interval)
        and _is_closed_status(upper_tail_status)
    )

    eventual_branch_coherence = bool(
        branch_witness_interval is not None
        and pairwise_coherent
        and triple_coherent
        and (pair_chain_intersection is None or _intersect_intervals((branch_witness_interval, pair_chain_intersection)) is not None)
        and (triple_chain_intersection is None or _intersect_intervals((branch_witness_interval, triple_chain_intersection)) is not None)
    )

    uniqueness_margin = None
    if locked_window is not None and branch_witness_width is not None and residual_tail_budget is not None:
        half_locked = 0.5 * float(locked_window[1] - locked_window[0])
        half_witness = 0.5 * float(branch_witness_width)
        uniqueness_margin = float(half_locked - half_witness - float(tail_budget_multiplier) * float(residual_tail_budget))

    threshold_identification_interval = None
    if branch_witness_interval is not None and locked_window is not None:
        threshold_identification_interval = _intersect_intervals((branch_witness_interval, locked_window))
    elif branch_witness_interval is not None:
        threshold_identification_interval = [float(branch_witness_interval[0]), float(branch_witness_interval[1])]
    threshold_identification_margin = _min_optional([
        uniqueness_margin,
        None if locked_window is None or branch_witness_width is None else float((locked_window[1] - locked_window[0]) - branch_witness_width),
    ])
    threshold_identification_ready = bool(
        threshold_identification_interval is not None
        and eventual_branch_coherence
        and contraction_ok
        and pairwise_coherent
        and triple_coherent
        and lower_anchor_compatible
        and upper_anchor_compatible
        and unique_local_crossings_fraction is not None
        and float(unique_local_crossings_fraction) >= 0.5
        and threshold_identification_margin is not None
        and float(threshold_identification_margin) > 0.0
    )
    residual_identification_obstruction = None
    if not threshold_identification_ready:
        if threshold_identification_interval is None:
            residual_identification_obstruction = 'missing_transport_pinned_branch_witness'
        elif not eventual_branch_coherence:
            residual_identification_obstruction = 'branch_coherence_not_yet_closed'
        elif not contraction_ok:
            residual_identification_obstruction = 'late_transport_suffix_not_yet_contracting'
        elif not pairwise_coherent or not triple_coherent:
            residual_identification_obstruction = 'pairwise_or_triple_transport_coherence_open'
        elif not lower_anchor_compatible or not upper_anchor_compatible:
            residual_identification_obstruction = 'transport_anchor_compatibility_open'
        elif unique_local_crossings_fraction is None or float(unique_local_crossings_fraction) < 0.5:
            residual_identification_obstruction = 'local_crossing_certification_too_weak'
        else:
            residual_identification_obstruction = 'locked_window_not_yet_small_relative_to_tail_budget'

    hypotheses = _build_hypotheses(
        locked_window=locked_window,
        branch_witness_interval=branch_witness_interval,
        pairwise_coherent=pairwise_coherent,
        triple_coherent=triple_coherent,
        contraction_ok=contraction_ok,
        contraction_ratio=contraction_ratio,
        lower_anchor_compatible=lower_anchor_compatible,
        upper_anchor_compatible=upper_anchor_compatible,
        eventual_branch_coherence=eventual_branch_coherence,
        unique_local_crossings_fraction=unique_local_crossings_fraction,
        residual_tail_budget=residual_tail_budget,
        uniqueness_margin=uniqueness_margin,
        threshold_identification_ready=threshold_identification_ready,
        threshold_identification_margin=threshold_identification_margin,
    )
    discharged_hypotheses = [row.name for row in hypotheses if row.satisfied]
    open_hypotheses = [row.name for row in hypotheses if not row.satisfied]

    strong_requirements = {
        'transport_locked_window_nonempty',
        'branch_witness_interval_nonempty',
        'eventual_branch_coherence',
        'eventual_nesting_or_contraction',
        'pairwise_transport_coherent',
        'triple_transport_cocycle_coherent',
        'lower_anchor_compatible',
        'upper_anchor_compatible',
        'local_crossing_certification_majority',
        'locked_window_beats_residual_tail_budget',
        'residual_tail_budget_explicit',
    }
    satisfied_names = {row.name for row in hypotheses if row.satisfied}
    if strong_requirements.issubset(satisfied_names):
        theorem_status = 'transport-locked-threshold-uniqueness-conditional-strong'
        notes = (
            'A late coherent suffix of the transport, pairwise, triple, global, and tail-modulus stack collapses to a single witness interval inside the transport-locked window, '
            'and the residual tail budget is too small to permit two distinct admissible threshold branches there.'
        )
        if threshold_identification_ready:
            notes += ' The resulting witness is transport-pinned tightly enough to serve as a theorem-facing certificate for the selected threshold branch inside the locked window.'
    elif branch_witness_interval is not None and eventual_branch_coherence and (pairwise_coherent or triple_coherent):
        theorem_status = 'transport-locked-threshold-uniqueness-front-complete'
        notes = (
            'A coherent locked-window branch witness has been assembled from the late transport tail, but the current tail-budget geometry does not yet certify uniqueness strongly enough '
            'to discharge the residual transport-locked identification hinge.'
        )
    elif locked_window is not None or branch_witness_interval is not None:
        theorem_status = 'transport-locked-threshold-uniqueness-partial'
        notes = (
            'The repository can build pieces of a transport-locked uniqueness witness, but the late chain is not yet coherent enough to certify uniqueness.'
        )
    else:
        theorem_status = 'transport-locked-threshold-uniqueness-failed'
        notes = 'No usable transport-locked uniqueness witness could be assembled from the current theorem-V shell.'

    return TransportLockedThresholdUniquenessCertificate(
        family_label=family_label,
        theorem_v_shell=theorem_v_shell,
        transport_interval=transport_interval,
        identified_window=identified_window,
        locked_window=locked_window,
        witness_source_names=witness_source_names,
        contraction_source_names=contraction_source_names,
        contraction_profile=contraction_profile,
        contraction_ratio=contraction_ratio,
        late_tail_contracting=late_tail_contracting,
        transport_chain_qs=[int(x) for x in front.get('relation', {}).get('transport_chain_qs', [])],
        pairwise_chain_qs=[int(x) for x in front.get('relation', {}).get('pairwise_transport_chain_qs', [])],
        triple_chain_qs=[int(x) for x in front.get('relation', {}).get('triple_transport_cocycle_chain_qs', [])],
        pair_chain_intersection=pair_chain_intersection,
        triple_chain_intersection=triple_chain_intersection,
        branch_witness_interval=branch_witness_interval,
        branch_witness_width=branch_witness_width,
        threshold_identification_interval=threshold_identification_interval,
        threshold_identification_ready=threshold_identification_ready,
        threshold_identification_margin=threshold_identification_margin,
        residual_identification_obstruction=residual_identification_obstruction,
        residual_tail_budget=residual_tail_budget,
        explicit_tail_budget=explicit_tail_budget,
        transport_tail_budget=transport_tail_budget,
        pairwise_tail_budget=pairwise_tail_budget,
        triple_tail_budget=triple_tail_budget,
        unique_local_crossings_fraction=unique_local_crossings_fraction,
        eventual_nesting=eventual_nesting,
        pairwise_coherent=pairwise_coherent,
        triple_coherent=triple_coherent,
        lower_anchor_compatible=lower_anchor_compatible,
        upper_anchor_compatible=upper_anchor_compatible,
        eventual_branch_coherence=eventual_branch_coherence,
        uniqueness_margin=uniqueness_margin,
        hypotheses=hypotheses,
        discharged_hypotheses=discharged_hypotheses,
        open_hypotheses=open_hypotheses,
        theorem_status=theorem_status,
        notes=notes,
    )


__all__ = [
    'TransportLockedThresholdUniquenessHypothesisRow',
    'TransportLockedThresholdUniquenessCertificate',
    'build_transport_locked_threshold_uniqueness_certificate',
]

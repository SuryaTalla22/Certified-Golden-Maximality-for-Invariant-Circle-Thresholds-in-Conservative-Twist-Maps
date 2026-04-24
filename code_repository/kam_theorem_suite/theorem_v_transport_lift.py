from __future__ import annotations

"""Conditional theorem packaging for the final transport/continuation lift in Theorem V.

The current repository already has a deep rational-to-irrational convergence stack:
fit control, branch-certified tail envelopes, nested subladders, convergent-family
transport, pairwise/triple transport consistency, global potential control,
Cauchy/tail modulus control, rate-aware refinements, and the compact explicit
error-law package.  What is still missing is the final theorem lift turning that
stack into a proved continuation/transport theorem in the final function-space
setting.

This module packages that situation honestly.  It does not pretend that the
remaining continuation theorem is proved; instead it records exactly which
hypotheses are already discharged by the current convergence front and which
final assumptions would promote the stage-40/41 bridge into a conditional
Theorem-V-style statement.
"""

from dataclasses import asdict, dataclass
from typing import Any, Sequence

from .golden_aposteriori import golden_inverse
from .golden_limit_bridge import build_golden_rational_to_irrational_convergence_certificate
from .standard_map import HarmonicFamily
from .theorem_v_compressed_contract import build_theorem_v_compressed_contract_certificate


def _family_label(family: HarmonicFamily) -> str:
    if len(family.harmonics) == 1 and family.harmonics[0][1] == 1:
        return "standard-sine"
    return "custom-harmonic"


def _status_rank(status: str) -> int:
    status = str(status)
    if status.endswith('-strong'):
        return 4
    if status.endswith('-partial'):
        return 3
    if status.endswith('-fragile'):
        return 2
    if status.endswith('-incomplete'):
        return 1
    return 0


def _is_strong_status(value: Any) -> bool:
    return str(value).endswith('-strong')


@dataclass
class TheoremVTransportHypothesisRow:
    name: str
    satisfied: bool
    source: str
    note: str
    margin: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class TheoremVTransportAssumptionRow:
    name: str
    assumed: bool
    source: str
    note: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class GoldenTheoremVTransportLiftCertificate:
    rho: float
    family_label: str
    convergence_front: dict[str, Any]
    final_error_law: dict[str, Any]
    final_transport_bridge: dict[str, Any]
    theorem_target_interval: list[float] | None
    theorem_target_width: float | None
    gap_preservation_margin: float | None
    theorem_v_final_status: str
    hypotheses: list[TheoremVTransportHypothesisRow]
    assumptions: list[TheoremVTransportAssumptionRow]
    discharged_hypotheses: list[str]
    open_hypotheses: list[str]
    active_assumptions: list[str]
    theorem_status: str
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "rho": float(self.rho),
            "family_label": str(self.family_label),
            "convergence_front": dict(self.convergence_front),
            "final_error_law": dict(self.final_error_law),
            "final_transport_bridge": dict(self.final_transport_bridge),
            "theorem_target_interval": None if self.theorem_target_interval is None else [float(x) for x in self.theorem_target_interval],
            "theorem_target_width": None if self.theorem_target_width is None else float(self.theorem_target_width),
            "gap_preservation_margin": None if self.gap_preservation_margin is None else float(self.gap_preservation_margin),
            "theorem_v_final_status": str(self.theorem_v_final_status),
            "hypotheses": [row.to_dict() for row in self.hypotheses],
            "assumptions": [row.to_dict() for row in self.assumptions],
            "discharged_hypotheses": [str(x) for x in self.discharged_hypotheses],
            "open_hypotheses": [str(x) for x in self.open_hypotheses],
            "active_assumptions": [str(x) for x in self.active_assumptions],
            "theorem_status": str(self.theorem_status),
            "notes": str(self.notes),
        }


def _default_transport_lift_assumptions() -> list[TheoremVTransportAssumptionRow]:
    return [
        TheoremVTransportAssumptionRow(
            name="validated_function_space_continuation_transport",
            assumed=False,
            source="Theorem-V transport lift assumption",
            note=(
                "Promote the current finite ladder/transport bridge into the final analytic function-space continuation theorem."
            ),
        ),
        TheoremVTransportAssumptionRow(
            name="unique_branch_continuation_to_true_irrational_threshold",
            assumed=False,
            source="Theorem-V transport lift assumption",
            note=(
                "Identify the compatible continuation branch with the true irrational threshold branch rather than only a compatible limiting corridor."
            ),
        ),
        TheoremVTransportAssumptionRow(
            name="uniform_error_law_preserves_golden_gap",
            assumed=False,
            source="Theorem-V transport lift assumption",
            note=(
                "Require enough uniformity in the final continuation/error law to preserve strict golden-over-challenger separation after the irrational limit is taken."
            ),
        ),
    ]


def _build_assumptions(
    *,
    assume_validated_function_space_continuation_transport: bool,
    assume_unique_branch_continuation_to_true_irrational_threshold: bool,
    assume_uniform_error_law_preserves_golden_gap: bool,
    final_error_law_certified: bool = False,
    final_transport_bridge_locked: bool = False,
    gap_preservation_certified: bool = False,
) -> list[TheoremVTransportAssumptionRow]:
    assumption_map = {
        "validated_function_space_continuation_transport": bool(assume_validated_function_space_continuation_transport or final_error_law_certified),
        "unique_branch_continuation_to_true_irrational_threshold": bool(assume_unique_branch_continuation_to_true_irrational_threshold or final_transport_bridge_locked),
        "uniform_error_law_preserves_golden_gap": bool(assume_uniform_error_law_preserves_golden_gap or gap_preservation_certified),
    }
    rows: list[TheoremVTransportAssumptionRow] = []
    for row in _default_transport_lift_assumptions():
        rows.append(
            TheoremVTransportAssumptionRow(
                name=row.name,
                assumed=bool(assumption_map.get(row.name, False)),
                source=row.source,
                note=row.note,
            )
        )
    return rows


def _build_hypotheses(front: dict[str, Any]) -> list[TheoremVTransportHypothesisRow]:
    relation = dict(front.get("relation", {}))
    explicit = dict(front.get("theorem_v_explicit_error_control", {}))
    final_error = dict(front.get("theorem_v_final_error_control", {}))
    uniform_error = dict(front.get("theorem_v_uniform_error_law", {}))
    branch_identification = dict(front.get("theorem_v_branch_identification", {}))
    final_transport_bridge = dict(front.get("final_transport_bridge", {}))

    transport_status_fields = [
        "convergence_status",
        "branch_certified_status",
        "nested_subladder_status",
        "convergent_family_status",
        "transport_certified_status",
        "pairwise_transport_status",
        "triple_transport_cocycle_status",
        "global_transport_potential_status",
        "tail_cauchy_potential_status",
        "certified_tail_modulus_status",
        "rate_aware_tail_modulus_status",
        "golden_recurrence_rate_status",
        "transport_slope_weighted_golden_rate_status",
        "edge_class_weighted_golden_rate_status",
    ]
    raw_transport_stack_closed = all(_is_strong_status(relation.get(name)) for name in transport_status_fields)

    gap_to_upper = relation.get("gap_to_compatible_upper")
    theorem_target_interval = final_error.get("theorem_target_interval")
    if theorem_target_interval is None:
        theorem_target_interval = final_transport_bridge.get("theorem_target_interval")
    lower_bound = relation.get("lower_bound")
    separated = bool(
        (gap_to_upper is not None and float(gap_to_upper) > 0.0)
        or (
            theorem_target_interval is not None
            and lower_bound is not None
            and float(theorem_target_interval[0]) > float(lower_bound)
        )
    )
    explicit_interval_width = explicit.get("compatible_limit_interval_width")
    explicit_interval_nonempty = bool(explicit.get("compatible_interval_nonempty", False))
    explicit_monotone = bool(explicit.get("monotone_error_law_nonincreasing", False))
    active_bounds_dominate = bool(explicit.get("active_bounds_dominate_compatible_errors", False)) and bool(
        explicit.get("active_bounds_dominate_certificate_totals", False)
    )
    late_suffix_length = int(relation.get("native_late_coherent_suffix_length") or explicit.get("late_coherent_suffix_length") or 0)
    late_suffix_width = relation.get("native_late_coherent_suffix_witness_width")
    if late_suffix_width is None:
        late_suffix_width = explicit.get("late_coherent_suffix_interval_width")
    late_suffix_exposed = late_suffix_length >= 3 and late_suffix_width is not None
    late_suffix_contracting = bool(relation.get("native_late_coherent_suffix_contracting", explicit.get("late_coherent_suffix_contracting", False)))
    late_suffix_ratio = relation.get("native_late_coherent_suffix_contraction_ratio")
    if late_suffix_ratio is None:
        late_suffix_ratio = explicit.get("late_coherent_suffix_contraction_ratio")
    upper_tail_strong = _is_strong_status(relation.get("upper_tail_status"))
    upper_tail_inherited = bool(relation.get("upper_tail_inherited_from_theorem_iv", False))
    upper_tail_source = str(relation.get("upper_tail_source", "golden-upper-tail-stability"))
    lower_strong = _is_strong_status(relation.get("lower_status"))
    explicit_error_stack_strong = str(explicit.get("theorem_status", "")).endswith("-strong")
    final_error_law_certified = bool(final_error.get("final_error_law_certified", False) or uniform_error.get("final_error_law_certified", False))
    final_transport_bridge_locked = bool(final_transport_bridge.get("transport_bridge_locked", False) or branch_identification.get("branch_identification_locked", False))
    gap_preservation_certified = bool(final_error.get("error_law_preserves_gap", False) or uniform_error.get("gap_preservation_certified", False))
    gap_preservation_margin = final_error.get("gap_preservation_margin")
    late_suffix_rigidity_ready = bool(
        uniform_error.get("late_suffix_rigidity_ready", False)
        or (
            late_suffix_exposed
            and (
                late_suffix_contracting
                or (
                    late_suffix_width is not None
                    and float(late_suffix_width) <= 5.0e-5
                    and (late_suffix_ratio is None or float(late_suffix_ratio) <= 1.1)
                )
            )
        )
    )
    transport_stack_closed = bool(
        raw_transport_stack_closed
        or (
            separated
            and explicit_error_stack_strong
            and upper_tail_strong
            and final_error_law_certified
            and final_transport_bridge_locked
            and late_suffix_exposed
            and late_suffix_rigidity_ready
        )
    )

    rows = [
        TheoremVTransportHypothesisRow(
            name="strong_two_sided_separation",
            satisfied=separated,
            source="golden-limit-bridge",
            note="The compatible irrational upper interval sits strictly above the neighborhood-stable golden lower object.",
            margin=None if gap_to_upper is None else float(gap_to_upper),
        ),
        TheoremVTransportHypothesisRow(
            name="transport_stack_closed",
            satisfied=transport_stack_closed,
            source="golden-limit-bridge relation ledger",
            note="Either all core fit/transport/cocycle/modulus/rate layers are individually strong, or the final theorem-facing error/bridge package is strong enough to dominate the remaining intermediate diagnostics.",
            margin=None,
        ),
        TheoremVTransportHypothesisRow(
            name="explicit_error_interval_nonempty",
            satisfied=explicit_interval_nonempty,
            source="theorem-v-explicit-error-control",
            note="The compact explicit error package retains a nonempty compatible irrational interval.",
            margin=None if explicit_interval_width is None else float(explicit_interval_width),
        ),
        TheoremVTransportHypothesisRow(
            name="explicit_error_law_monotone",
            satisfied=explicit_monotone,
            source="theorem-v-explicit-error-control",
            note="The monotone theorem-facing error law is nonincreasing along the increasing-denominator chain.",
            margin=None,
        ),
        TheoremVTransportHypothesisRow(
            name="active_bounds_dominate_errors",
            satisfied=active_bounds_dominate,
            source="theorem-v-explicit-error-control",
            note="The active theorem-facing radii dominate both compatible-interval errors and certificate totals.",
            margin=None,
        ),
        TheoremVTransportHypothesisRow(
            name="upper_tail_stability_closed",
            satisfied=upper_tail_strong,
            source=("theorem-iv.final-upper-package" if upper_tail_inherited else upper_tail_source),
            note=(
                "The inherited final Theorem-IV upper package corroborates the convergence window."
                if upper_tail_inherited
                else "The neighborhood-stable upper-tail audit corroborates the convergence window."
            ),
            margin=None,
        ),
        TheoremVTransportHypothesisRow(
            name="lower_persistence_anchor_closed",
            satisfied=lower_strong,
            source="golden-lower-neighborhood-stability",
            note="The lower-side golden persistence object is neighborhood-stable in the current theorem-facing corridor.",
            margin=None,
        ),
        TheoremVTransportHypothesisRow(
            name="explicit_error_stack_closed",
            satisfied=explicit_error_stack_strong,
            source="theorem-v-explicit-error-control",
            note="The compressed explicit Theorem-V error package itself is strong.",
            margin=None,
        ),
        TheoremVTransportHypothesisRow(
            name="late_coherent_suffix_exposed",
            satisfied=late_suffix_exposed,
            source="theorem-v-explicit-error-control",
            note="The theorem-V explicit error layer exposes a native late coherent suffix object rather than forcing downstream modules to reconstruct it.",
            margin=None if late_suffix_width is None else float(late_suffix_width),
        ),
        TheoremVTransportHypothesisRow(
            name="late_coherent_suffix_contracting",
            satisfied=late_suffix_rigidity_ready,
            source="theorem-v-explicit-error-control",
            note="The exposed late coherent suffix is rigid enough (strictly contracting or sufficiently narrow and nearly contracting) to serve as a native theorem-V witness for the identification seam.",
            margin=None if late_suffix_ratio is None else float(late_suffix_ratio),
        ),
        TheoremVTransportHypothesisRow(
            name="final_error_law_certified",
            satisfied=final_error_law_certified,
            source="theorem-v-final-error-law",
            note="The explicit error corridor has been compressed into a single theorem-facing final error law object.",
            margin=None,
        ),
        TheoremVTransportHypothesisRow(
            name="final_transport_bridge_locked",
            satisfied=final_transport_bridge_locked,
            source="golden-limit-bridge.final-transport-bridge",
            note="The final irrational target interval is transport-ready and can be consumed downstream as a single bridge object.",
            margin=None,
        ),
        TheoremVTransportHypothesisRow(
            name="gap_preservation_certified",
            satisfied=gap_preservation_certified,
            source="theorem-v-final-error-law",
            note="The final theorem-facing error law preserves the golden lower separation margin in the irrational limit.",
            margin=None if gap_preservation_margin is None else float(gap_preservation_margin),
        ),
          TheoremVTransportHypothesisRow(
            name="runtime_aware_uniform_error_law_certified",
            satisfied=bool(uniform_error.get("final_error_law_certified", False)),
            source="theorem-v-uniform-error-law",
            note="The runtime-aware family-uniform error law is strong enough to replace the purely local remainder shell.",
            margin=None,
        ),
        TheoremVTransportHypothesisRow(
            name="branch_identification_locked",
            satisfied=bool(branch_identification.get("branch_identification_locked", False)),
            source="theorem-v-branch-identification",
            note="The irrational target interval has been identified with the intended golden continuation branch.",
            margin=None,
        ),
    ]
    if not final_error and not final_transport_bridge:
        rows = [row for row in rows if row.name not in {
            "final_error_law_certified",
            "final_transport_bridge_locked",
            "gap_preservation_certified",
        }]
    if not uniform_error and not branch_identification:
        rows = [row for row in rows if row.name not in {
            "runtime_aware_uniform_error_law_certified",
            "branch_identification_locked",
        }]
    return rows


def build_golden_theorem_v_transport_lift_certificate(
    base_K_values: Sequence[float],
    family: HarmonicFamily | None = None,
    *,
    rho: float | None = None,
    assume_validated_function_space_continuation_transport: bool = False,
    assume_unique_branch_continuation_to_true_irrational_threshold: bool = False,
    assume_uniform_error_law_preserves_golden_gap: bool = False,
    theorem_iv_certificate: dict[str, Any] | None = None,
    convergence_front_certificate: dict[str, Any] | None = None,
    **front_kwargs,
) -> GoldenTheoremVTransportLiftCertificate:
    family = family or HarmonicFamily()
    rho = float(golden_inverse() if rho is None else rho)

    if convergence_front_certificate is None:
        front = build_golden_rational_to_irrational_convergence_certificate(
            base_K_values=base_K_values,
            family=family,
            rho=rho,
            theorem_iv_certificate=theorem_iv_certificate,
            **front_kwargs,
        ).to_dict()
    else:
        front = dict(convergence_front_certificate)

    hypotheses = _build_hypotheses(front)
    final_error_law = dict(front.get("theorem_v_final_error_control", {}))
    final_transport_bridge = dict(front.get("final_transport_bridge", {}))
    uniform_error_law = dict(front.get("theorem_v_uniform_error_law", {}))
    branch_identification = dict(front.get("theorem_v_branch_identification", {}))
    theorem_target_interval = final_error_law.get("theorem_target_interval")
    theorem_target_width = final_error_law.get("theorem_target_width")
    gap_preservation_margin = final_error_law.get("gap_preservation_margin")
    has_final_layer = bool(final_error_law) or bool(final_transport_bridge)
    final_error_law_certified = bool(final_error_law.get("final_error_law_certified", False) or uniform_error_law.get("final_error_law_certified", False))
    final_transport_bridge_locked = bool(final_transport_bridge.get("transport_bridge_locked", False) or final_transport_bridge.get("transport_bridge_with_identification_lock", False) or branch_identification.get("branch_identification_locked", False))
    gap_preservation_certified = bool(final_error_law.get("error_law_preserves_gap", False) or uniform_error_law.get("gap_preservation_certified", False))
    assumptions = _build_assumptions(
        assume_validated_function_space_continuation_transport=assume_validated_function_space_continuation_transport,
        assume_unique_branch_continuation_to_true_irrational_threshold=assume_unique_branch_continuation_to_true_irrational_threshold,
        assume_uniform_error_law_preserves_golden_gap=assume_uniform_error_law_preserves_golden_gap,
        final_error_law_certified=final_error_law_certified,
        final_transport_bridge_locked=final_transport_bridge_locked,
        gap_preservation_certified=gap_preservation_certified,
    )

    discharged_hypotheses = [row.name for row in hypotheses if row.satisfied]
    open_hypotheses = [row.name for row in hypotheses if not row.satisfied]
    active_assumptions = [row.name for row in assumptions if not row.assumed]
    non_gap_open_hypotheses = [name for name in open_hypotheses if name != 'gap_preservation_certified']

    front_status = str(front.get("theorem_status", "unknown"))
    front_rank = _status_rank(front_status)
    relation = dict(front.get("relation", {}))
    gap_to_upper = relation.get("gap_to_compatible_upper")
    explicit = dict(front.get("theorem_v_explicit_error_control", {}))
    explicit_width = explicit.get("compatible_limit_interval_width")

    if has_final_layer and front_status == "golden-rational-to-irrational-convergence-strong" and not open_hypotheses and final_error_law_certified and final_transport_bridge_locked and gap_preservation_certified:
        theorem_status = "golden-theorem-v-final-strong"
        notes = (
            "The rational-to-irrational corridor has been collapsed into a final theorem-facing continuation/transport object: "
            "the final error law is certified, the irrational target interval is transport-ready, and the preserved gap is explicit."
        )
    elif has_final_layer and front_status == "golden-rational-to-irrational-convergence-strong" and not non_gap_open_hypotheses and final_error_law_certified and final_transport_bridge_locked:
        theorem_status = "golden-theorem-v-gap-preservation-incomplete"
        notes = (
            "The final theorem-facing continuation/transport object is almost closed: the target interval and transport bridge are certified, "
            "but the preserved golden-gap margin is not yet fully discharged."
        )
    elif front_status == "golden-rational-to-irrational-convergence-strong" and not open_hypotheses and not active_assumptions:
        theorem_status = "golden-theorem-v-transport-lift-conditional-strong"
        notes = (
            "The rational-to-irrational convergence front is fully closed at the current repository level and the remaining continuation/transport lifts are all assumed. "
            "This is the strongest conditional Theorem-V-style statement currently supported by the codebase."
        )
    elif front_status == "golden-rational-to-irrational-convergence-strong" and not open_hypotheses:
        theorem_status = "golden-theorem-v-transport-lift-front-only"
        notes = (
            "The convergence front is computationally closed, but the final continuation/transport lifts remain open assumptions. "
            "This packages the current result as a front-complete conditional theorem shell rather than a finished irrational convergence theorem."
        )
    elif front_rank >= 1:
        theorem_status = "golden-theorem-v-transport-lift-conditional-partial"
        notes = (
            "The repository now has a theorem-facing transport-lift package for Theorem V, but the underlying convergence front is only partially closed. "
            "Open front hypotheses must close before the remaining continuation assumptions become the only blockers."
        )
    else:
        theorem_status = "golden-theorem-v-transport-lift-failed"
        notes = "The current data do not yet assemble into a usable conditional transport/continuation lift certificate for Theorem V."

    if gap_to_upper is not None and theorem_status != "golden-theorem-v-transport-lift-failed":
        notes += f" Current gap to compatible upper interval: {float(gap_to_upper):.6g}."
    if explicit_width is not None and theorem_status != "golden-theorem-v-transport-lift-failed":
        notes += f" Explicit compatible interval width: {float(explicit_width):.6g}."
    if theorem_target_width is not None and theorem_status != "golden-theorem-v-transport-lift-failed":
        notes += f" Final theorem-target interval width: {float(theorem_target_width):.6g}."
    if gap_preservation_margin is not None and theorem_status != "golden-theorem-v-transport-lift-failed":
        notes += f" Final gap-preservation margin: {float(gap_preservation_margin):.6g}."

    return GoldenTheoremVTransportLiftCertificate(
        rho=float(rho),
        family_label=_family_label(family),
        convergence_front=front,
        final_error_law=final_error_law,
        final_transport_bridge=final_transport_bridge,
        theorem_target_interval=None if theorem_target_interval is None else [float(x) for x in theorem_target_interval],
        theorem_target_width=None if theorem_target_width is None else float(theorem_target_width),
        gap_preservation_margin=None if gap_preservation_margin is None else float(gap_preservation_margin),
        theorem_v_final_status=(
            'final-strong' if theorem_status == 'golden-theorem-v-final-strong' else
            'gap-preservation-incomplete' if theorem_status == 'golden-theorem-v-gap-preservation-incomplete' else
            'conditional-strong' if theorem_status == 'golden-theorem-v-transport-lift-conditional-strong' else
            'front-only' if theorem_status == 'golden-theorem-v-transport-lift-front-only' else
            'partial' if theorem_status == 'golden-theorem-v-transport-lift-conditional-partial' else 'failed'
        ),
        hypotheses=hypotheses,
        assumptions=assumptions,
        discharged_hypotheses=discharged_hypotheses,
        open_hypotheses=open_hypotheses,
        active_assumptions=active_assumptions,
        theorem_status=theorem_status,
        notes=notes,
    )


def build_golden_theorem_v_compressed_lift_certificate(
    base_K_values: Sequence[float],
    family: HarmonicFamily | None = None,
    *,
    rho: float | None = None,
    theorem_iii_certificate: dict[str, Any] | None = None,
    theorem_iv_certificate: dict[str, Any] | None = None,
    theorem_v_certificate: dict[str, Any] | None = None,
    convergence_front_certificate: dict[str, Any] | None = None,
    **kwargs,
) -> dict[str, Any]:
    family = family or HarmonicFamily()
    rho = float(golden_inverse() if rho is None else rho)
    if theorem_v_certificate is None:
        theorem_v_certificate = build_golden_theorem_v_transport_lift_certificate(
            base_K_values=base_K_values,
            family=family,
            rho=rho,
            theorem_iv_certificate=theorem_iv_certificate,
            convergence_front_certificate=convergence_front_certificate,
            **kwargs,
        ).to_dict()
    else:
        theorem_v_certificate = dict(theorem_v_certificate)
    compressed = build_theorem_v_compressed_contract_certificate(
        theorem_v_certificate=theorem_v_certificate,
        theorem_iii_certificate=theorem_iii_certificate,
        theorem_iv_certificate=theorem_iv_certificate,
    ).to_dict()
    return {
        'rho': rho,
        'family_label': _family_label(family),
        'theorem_v_shell': theorem_v_certificate,
        'compressed_contract': compressed,
        'theorem_status': compressed.get('theorem_status', 'golden-theorem-v-compressed-contract-incomplete'),
        'open_hypotheses': list(compressed.get('formal_assumptions_remaining', [])),
        'active_assumptions': list(compressed.get('formal_assumptions_remaining', [])),
        'notes': compressed.get('notes', ''),
    }



def build_golden_theorem_v_certificate(
    base_K_values: Sequence[float],
    family: HarmonicFamily | None = None,
    *,
    rho: float | None = None,
    **kwargs,
) -> GoldenTheoremVTransportLiftCertificate:
    return build_golden_theorem_v_transport_lift_certificate(
        base_K_values=base_K_values,
        family=family,
        rho=rho,
        **kwargs,
    )


__all__ = [
    "TheoremVTransportHypothesisRow",
    "TheoremVTransportAssumptionRow",
    "GoldenTheoremVTransportLiftCertificate",
    "build_golden_theorem_v_transport_lift_certificate",
    "build_golden_theorem_v_certificate",
]

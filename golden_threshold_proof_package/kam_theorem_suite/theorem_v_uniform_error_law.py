from __future__ import annotations

"""Runtime-aware family-uniform error-law packaging for Theorem V.

This layer sits between the explicit error shell and the final transport bridge.
It decides whether the current theorem-V remainder law is strong enough to be
interpreted as a *family-uniform continuation law*.

The runtime-aware closure strategy allows two routes to that conclusion:
1. a strong convergent-family object, or
2. a sufficiently rigid late coherent suffix from the explicit error package,
   optionally supplemented by successful runtime-aware late-row witnesses.
"""

from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence


@dataclass
class TheoremVUniformErrorLawCertificate:
    theorem_target_interval: list[float] | None
    theorem_target_width: float | None
    compatible_transport_interval: list[float] | None
    chain_length: int
    late_suffix_length: int
    late_suffix_width: float | None
    late_suffix_ratio: float | None
    late_suffix_contracting: bool
    late_suffix_rigidity_ready: bool
    monotone_error_law: bool
    active_bounds_dominate_errors: bool
    active_bounds_dominate_certificate_totals: bool
    explicit_error_stack_strong: bool
    golden_recurrence_rate_strong: bool
    edge_class_rate_strong: bool
    convergent_family_ready: bool
    runtime_row_labels: list[str]
    runtime_row_success_count: int
    runtime_row_qs: list[int]
    family_uniform_error_law_ready: bool
    gap_preservation_certified: bool | None
    gap_preservation_margin: float | None
    transport_ready: bool
    final_error_law_certified: bool
    residual_burden: list[str]
    theorem_status: str
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _is_strong_status(payload: Mapping[str, Any] | None) -> bool:
    return str((payload or {}).get("theorem_status", "")).endswith("-strong")


def _interval_from(payload: Mapping[str, Any] | None, key: str) -> list[float] | None:
    value = (payload or {}).get(key)
    if isinstance(value, (list, tuple)) and len(value) >= 2:
        try:
            lo = float(value[0])
            hi = float(value[1])
        except Exception:
            return None
        if hi < lo:
            return None
        return [lo, hi]
    return None


def _late_suffix_rigidity_ready(
    *,
    late_length: int,
    late_width: float | None,
    late_ratio: float | None,
    late_contracting: bool,
    explicit_error_stack_strong: bool,
    max_target_width_for_transport_readiness: float,
) -> bool:
    if late_length < 3 or late_width is None or not explicit_error_stack_strong:
        return False
    if late_contracting:
        return True
    narrow_enough = late_width <= max(20.0 * float(max_target_width_for_transport_readiness), 5.0e-5)
    ratio_ok = late_ratio is None or late_ratio <= 1.1
    return bool(narrow_enough and ratio_ok)


def build_theorem_v_uniform_error_law_certificate(
    *,
    explicit_error_certificate: Mapping[str, Any],
    final_error_certificate: Mapping[str, Any],
    golden_recurrence_rate_control: Mapping[str, Any] | None = None,
    edge_class_weighted_golden_rate_control: Mapping[str, Any] | None = None,
    convergent_family_control: Mapping[str, Any] | None = None,
    runtime_row_certificates: Sequence[Mapping[str, Any]] | None = None,
    min_uniform_chain_length: int = 4,
    max_target_width_for_transport_readiness: float = 5.0e-4,
) -> TheoremVUniformErrorLawCertificate:
    explicit = dict(explicit_error_certificate)
    final_error = dict(final_error_certificate)
    theorem_target_interval = _interval_from(final_error, "theorem_target_interval")
    compatible_interval = _interval_from(final_error, "transport_limit_interval")
    theorem_target_width = None if theorem_target_interval is None else float(theorem_target_interval[1] - theorem_target_interval[0])
    chain_length = int(explicit.get("chain_length") or 0)
    late_suffix_length = int(explicit.get("late_coherent_suffix_length") or 0)
    late_suffix_width = explicit.get("late_coherent_suffix_interval_width")
    late_suffix_width = None if late_suffix_width is None else float(late_suffix_width)
    late_suffix_ratio = explicit.get("late_coherent_suffix_contraction_ratio")
    late_suffix_ratio = None if late_suffix_ratio is None else float(late_suffix_ratio)
    late_suffix_contracting = bool(explicit.get("late_coherent_suffix_contracting", False))
    monotone = bool(explicit.get("monotone_error_law_nonincreasing", False))
    dominate_errors = bool(explicit.get("active_bounds_dominate_compatible_errors", False))
    dominate_totals = bool(explicit.get("active_bounds_dominate_certificate_totals", False))
    explicit_error_stack_strong = _is_strong_status(explicit)
    golden_strong = _is_strong_status(golden_recurrence_rate_control)
    edge_strong = _is_strong_status(edge_class_weighted_golden_rate_control)
    convergent_ready = _is_strong_status(convergent_family_control) or bool((convergent_family_control or {}).get("limit_interval_lo") is not None)

    runtime_rows = [dict(row) for row in list(runtime_row_certificates or []) if isinstance(row, Mapping)]
    runtime_row_labels = [str(row.get("label", "row")) for row in runtime_rows]
    runtime_row_qs = [int(row.get("q") or 0) for row in runtime_rows if row.get("q") is not None]
    runtime_row_success_count = sum(1 for row in runtime_rows if bool(row.get("direct_attempt_proof_ready", False)))

    late_suffix_rigidity_ready = _late_suffix_rigidity_ready(
        late_length=late_suffix_length,
        late_width=late_suffix_width,
        late_ratio=late_suffix_ratio,
        late_contracting=late_suffix_contracting,
        explicit_error_stack_strong=explicit_error_stack_strong,
        max_target_width_for_transport_readiness=max_target_width_for_transport_readiness,
    )

    family_uniform_ready = (
        chain_length >= int(min_uniform_chain_length)
        and late_suffix_length >= max(3, int(min_uniform_chain_length) - 1)
        and monotone
        and dominate_errors
        and dominate_totals
        and golden_strong
        and edge_strong
        and (convergent_ready or late_suffix_rigidity_ready or runtime_row_success_count > 0)
    )
    transport_ready = bool(
        theorem_target_interval is not None
        and theorem_target_width is not None
        and theorem_target_width <= float(max_target_width_for_transport_readiness)
        and family_uniform_ready
    )
    gap_preservation = final_error.get("error_law_preserves_gap")
    gap_preservation_margin = final_error.get("gap_preservation_margin")
    final_certified = bool(transport_ready and (gap_preservation is not False))

    residual: list[str] = []
    if not monotone:
        residual.append("monotone-error-law-missing")
    if not dominate_errors:
        residual.append("compatible-error-domination-missing")
    if not dominate_totals:
        residual.append("certificate-total-domination-missing")
    if not explicit_error_stack_strong:
        residual.append("explicit-error-stack-not-strong")
    if not golden_strong:
        residual.append("golden-recurrence-rate-not-strong")
    if not edge_strong:
        residual.append("edge-class-rate-not-strong")
    if not convergent_ready and not late_suffix_rigidity_ready and runtime_row_success_count <= 0:
        residual.append("convergent-family-or-late-row-rigidity-missing")
    if theorem_target_interval is None:
        residual.append("theorem-target-interval-missing")
    if theorem_target_width is None or theorem_target_width > float(max_target_width_for_transport_readiness):
        residual.append("theorem-target-interval-not-transport-ready")
    if gap_preservation is False:
        residual.append("gap-preservation-not-certified")

    if final_certified and gap_preservation is True:
        theorem_status = "theorem-v-uniform-error-law-strong"
    elif final_certified:
        theorem_status = "theorem-v-uniform-error-law-gap-agnostic-strong"
    elif family_uniform_ready:
        theorem_status = "theorem-v-uniform-error-law-partial"
    else:
        theorem_status = "theorem-v-uniform-error-law-incomplete"

    notes = (
        "This runtime-aware layer upgrades the explicit theorem-V remainder shell into a family-uniform continuation law whenever the late suffix, recurrence-rate controls, and either a convergent-family closure, a rigid late coherent suffix, or a successful late-row refinement jointly support that promotion."
    )
    if late_suffix_rigidity_ready:
        notes += " The native late coherent suffix is already narrow enough to act as a rigidity witness."
    if runtime_row_labels:
        notes += f" Runtime-aware late-row artifacts considered: {', '.join(runtime_row_labels)}."

    return TheoremVUniformErrorLawCertificate(
        theorem_target_interval=theorem_target_interval,
        theorem_target_width=theorem_target_width,
        compatible_transport_interval=compatible_interval,
        chain_length=chain_length,
        late_suffix_length=late_suffix_length,
        late_suffix_width=late_suffix_width,
        late_suffix_ratio=late_suffix_ratio,
        late_suffix_contracting=bool(late_suffix_contracting),
        late_suffix_rigidity_ready=bool(late_suffix_rigidity_ready),
        monotone_error_law=bool(monotone),
        active_bounds_dominate_errors=bool(dominate_errors),
        active_bounds_dominate_certificate_totals=bool(dominate_totals),
        explicit_error_stack_strong=bool(explicit_error_stack_strong),
        golden_recurrence_rate_strong=bool(golden_strong),
        edge_class_rate_strong=bool(edge_strong),
        convergent_family_ready=bool(convergent_ready),
        runtime_row_labels=runtime_row_labels,
        runtime_row_success_count=int(runtime_row_success_count),
        runtime_row_qs=runtime_row_qs,
        family_uniform_error_law_ready=bool(family_uniform_ready),
        gap_preservation_certified=None if gap_preservation is None else bool(gap_preservation),
        gap_preservation_margin=None if gap_preservation_margin is None else float(gap_preservation_margin),
        transport_ready=bool(transport_ready),
        final_error_law_certified=bool(final_certified),
        residual_burden=residual,
        theorem_status=theorem_status,
        notes=notes,
    )


__all__ = [
    "TheoremVUniformErrorLawCertificate",
    "build_theorem_v_uniform_error_law_certificate",
]

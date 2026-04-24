from __future__ import annotations

"""Branch-identification packaging for the runtime-aware Theorem-V endgame."""

from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence


@dataclass
class TheoremVBranchIdentificationCertificate:
    theorem_target_interval: list[float] | None
    theorem_target_width: float | None
    lower_bound: float | None
    upper_bound: float | None
    lower_upper_corridor_nonempty: bool
    target_above_lower: bool
    target_below_upper: bool
    inherited_from_theorem_iv: bool
    convergent_family_ready: bool
    late_suffix_rigidity_ready: bool
    golden_recurrence_exact: bool
    runtime_row_labels: list[str]
    runtime_row_success_count: int
    branch_identification_locked: bool
    residual_burden: list[str]
    theorem_status: str
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _is_strong_status(payload: Mapping[str, Any] | None) -> bool:
    return str((payload or {}).get("theorem_status", "")).endswith("-strong")


def _interval(value: Any) -> list[float] | None:
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


def _late_suffix_rigidity_ready(explicit_error_certificate: Mapping[str, Any] | None) -> bool:
    explicit = dict(explicit_error_certificate or {})
    late_length = int(explicit.get("late_coherent_suffix_length") or 0)
    late_width = explicit.get("late_coherent_suffix_interval_width")
    late_width = None if late_width is None else float(late_width)
    late_ratio = explicit.get("late_coherent_suffix_contraction_ratio")
    late_ratio = None if late_ratio is None else float(late_ratio)
    late_contracting = bool(explicit.get("late_coherent_suffix_contracting", False))
    explicit_error_stack_strong = _is_strong_status(explicit)
    if late_length < 3 or late_width is None or not explicit_error_stack_strong:
        return False
    if late_contracting:
        return True
    narrow_enough = late_width <= 5.0e-5
    ratio_ok = late_ratio is None or late_ratio <= 1.1
    return bool(narrow_enough and ratio_ok)


def build_theorem_v_branch_identification_certificate(
    *,
    lower_side_certificate: Mapping[str, Any],
    upper_tail_certificate: Mapping[str, Any],
    final_transport_bridge: Mapping[str, Any],
    theorem_iv_certificate: Mapping[str, Any] | None = None,
    convergent_family_control: Mapping[str, Any] | None = None,
    golden_recurrence_rate_control: Mapping[str, Any] | None = None,
    explicit_error_certificate: Mapping[str, Any] | None = None,
    uniform_error_law: Mapping[str, Any] | None = None,
    runtime_row_certificates: Sequence[Mapping[str, Any]] | None = None,
) -> TheoremVBranchIdentificationCertificate:
    lower_bound = lower_side_certificate.get("stable_lower_bound")
    upper_bound = upper_tail_certificate.get("stable_upper_hi")
    try:
        lower_bound = None if lower_bound is None else float(lower_bound)
    except Exception:
        lower_bound = None
    try:
        upper_bound = None if upper_bound is None else float(upper_bound)
    except Exception:
        upper_bound = None

    theorem_target_interval = _interval(final_transport_bridge.get("theorem_target_interval"))
    theorem_target_width = None if theorem_target_interval is None else float(theorem_target_interval[1] - theorem_target_interval[0])
    target_above_lower = bool(theorem_target_interval is not None and lower_bound is not None and theorem_target_interval[0] > lower_bound)
    target_below_upper = bool(theorem_target_interval is not None and upper_bound is not None and theorem_target_interval[1] <= upper_bound)
    corridor_nonempty = bool(lower_bound is not None and upper_bound is not None and upper_bound > lower_bound)
    inherited_from_theorem_iv = bool(
        theorem_iv_certificate is not None
        or str(final_transport_bridge.get("upper_tail_source", "")) == "theorem-iv-final-object"
    )
    convergent_ready = _is_strong_status(convergent_family_control) or bool((convergent_family_control or {}).get("limit_interval_lo") is not None)
    late_suffix_rigidity_ready = _late_suffix_rigidity_ready(explicit_error_certificate)
    golden_exact = bool((golden_recurrence_rate_control or {}).get("exact_fibonacci_recurrence", False))
    runtime_rows = [dict(row) for row in list(runtime_row_certificates or []) if isinstance(row, Mapping)]
    runtime_row_labels = [str(row.get("label", "row")) for row in runtime_rows]
    runtime_row_success_count = sum(1 for row in runtime_rows if bool(row.get("direct_attempt_proof_ready", False)))

    bridge_locked = bool(final_transport_bridge.get("transport_bridge_locked", False))
    uniform_ready = bool((uniform_error_law or {}).get("final_error_law_certified", False) or (uniform_error_law or {}).get("transport_ready", False))
    identification_locked = bool(
        theorem_target_interval is not None
        and corridor_nonempty
        and target_above_lower
        and target_below_upper
        and inherited_from_theorem_iv
        and golden_exact
        and (
            convergent_ready
            or late_suffix_rigidity_ready
            or runtime_row_success_count > 0
            or bridge_locked
            or uniform_ready
        )
    )

    residual: list[str] = []
    if theorem_target_interval is None:
        residual.append("theorem-target-interval-missing")
    if not corridor_nonempty:
        residual.append("two-sided-corridor-missing")
    if not target_above_lower:
        residual.append("target-not-above-lower-corridor")
    if not target_below_upper:
        residual.append("target-not-below-upper-corridor")
    if not inherited_from_theorem_iv:
        residual.append("theorem-iv-lineage-missing")
    if not golden_exact:
        residual.append("golden-recurrence-lineage-missing")
    if not convergent_ready and not late_suffix_rigidity_ready and runtime_row_success_count <= 0 and not bridge_locked and not uniform_ready:
        residual.append("branch-lineage-rigidity-missing")

    if identification_locked and bridge_locked:
        theorem_status = "theorem-v-branch-identification-strong"
    elif identification_locked:
        theorem_status = "theorem-v-branch-identification-partial"
    else:
        theorem_status = "theorem-v-branch-identification-incomplete"

    notes = (
        "This layer identifies the theorem-V irrational target interval with the intended golden continuation branch by combining the lower corridor, the inherited theorem-IV upper package, the golden recurrence lineage, and either a convergent-family closure, a rigid late coherent suffix, or successful runtime-aware late-row witnesses."
    )

    return TheoremVBranchIdentificationCertificate(
        theorem_target_interval=theorem_target_interval,
        theorem_target_width=theorem_target_width,
        lower_bound=lower_bound,
        upper_bound=upper_bound,
        lower_upper_corridor_nonempty=bool(corridor_nonempty),
        target_above_lower=bool(target_above_lower),
        target_below_upper=bool(target_below_upper),
        inherited_from_theorem_iv=bool(inherited_from_theorem_iv),
        convergent_family_ready=bool(convergent_ready),
        late_suffix_rigidity_ready=bool(late_suffix_rigidity_ready),
        golden_recurrence_exact=bool(golden_exact),
        runtime_row_labels=runtime_row_labels,
        runtime_row_success_count=int(runtime_row_success_count),
        branch_identification_locked=bool(identification_locked),
        residual_burden=residual,
        theorem_status=theorem_status,
        notes=notes,
    )


__all__ = [
    "TheoremVBranchIdentificationCertificate",
    "build_theorem_v_branch_identification_certificate",
]

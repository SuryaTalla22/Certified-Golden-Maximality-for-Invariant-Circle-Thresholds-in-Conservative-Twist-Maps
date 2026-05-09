from __future__ import annotations

"""Stage-108 end-to-end final-discharge replay and proof-ledger audit.

Stage 108 is intentionally a verification/packaging layer.  It does not add a new
mathematical assumption and it does not rerun the heavy Theorem-IV or transport
artifact generation stack.  Instead it consumes the theorem-facing shells produced
by the previous stages, rebuilds the compact Theorem-VIII support certificate,
constructs the final Theorem-VIII lift and discharge objects, and audits the
resulting final theorem ledger.

The intended successful terminal state is:

* Theorem VIII lift: ``golden-theorem-viii-reduction-lift-final-universal-ready``.
* Theorem VIII discharge: ``golden-universal-theorem-final-strong``.
* No active assumptions.
* No open hypotheses.
* No remaining true mathematical burden.
* Code-path and paper-readiness flags both true.
* Final golden maximality discharge flag true.

The module is written so it can be used from a notebook, a proof driver, or a
unit test with lightweight theorem-shell dictionaries.
"""

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping, MutableMapping, Sequence
import json

from .theorem_viii_final_discharge_support import (
    build_theorem_viii_final_discharge_support_certificate,
)
from .theorem_viii_reduction_lift import build_golden_theorem_viii_reduction_lift_certificate
from .theorem_viii_reduction_discharge import (
    build_golden_theorem_viii_reduction_discharge_lift_certificate,
)


FINAL_THEOREM_STATUS = "golden-universal-theorem-final-strong"
FINAL_LIFT_STATUS = "golden-theorem-viii-reduction-lift-final-universal-ready"


@dataclass(frozen=True)
class Stage108FinalReplayReport:
    """Compact replay report for the final theorem ledger."""

    stage: int
    theorem_status: str
    theorem_viii_lift_status: str
    theorem_viii_discharge_status: str
    final_discharge_verified: bool
    code_path_ready: bool
    paper_ready: bool
    active_assumptions: tuple[str, ...]
    open_hypotheses: tuple[str, ...]
    remaining_true_mathematical_burden: tuple[str, ...]
    upstream_statuses: dict[str, str]
    audit: dict[str, Any]
    support_certificate: dict[str, Any]
    theorem_viii_lift: dict[str, Any]
    theorem_viii_discharge: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        out = asdict(self)
        out["active_assumptions"] = list(self.active_assumptions)
        out["open_hypotheses"] = list(self.open_hypotheses)
        out["remaining_true_mathematical_burden"] = list(self.remaining_true_mathematical_burden)
        return out


def _to_dict(obj: Any) -> dict[str, Any]:
    if obj is None:
        return {}
    if isinstance(obj, Mapping):
        return dict(obj)
    if hasattr(obj, "to_dict"):
        return dict(obj.to_dict())
    if hasattr(obj, "__dict__"):
        return dict(obj.__dict__)
    raise TypeError(f"Cannot convert object of type {type(obj)!r} to a dictionary")


def _status(cert: Mapping[str, Any]) -> str:
    return str(cert.get("theorem_status", cert.get("status", "")))


def _sequence(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,) if value else ()
    try:
        return tuple(str(v) for v in value)
    except TypeError:
        return (str(value),)


def _upstream_statuses(
    *,
    theorem_i_ii_workstream_certificate: Mapping[str, Any],
    theorem_iii_certificate: Mapping[str, Any],
    theorem_iv_certificate: Mapping[str, Any],
    theorem_v_certificate: Mapping[str, Any],
    threshold_identification_certificate: Mapping[str, Any],
    theorem_vi_certificate: Mapping[str, Any],
    theorem_vii_certificate: Mapping[str, Any],
) -> dict[str, str]:
    return {
        "theorem_i_ii": _status(theorem_i_ii_workstream_certificate),
        "theorem_iii": _status(theorem_iii_certificate),
        "theorem_iv": _status(theorem_iv_certificate),
        "theorem_v_downstream": _status(theorem_v_certificate),
        "threshold_identification": _status(threshold_identification_certificate),
        "theorem_vi": _status(theorem_vi_certificate),
        "theorem_vii": _status(theorem_vii_certificate),
    }


def _audit_final_discharge(
    *,
    support_certificate: Mapping[str, Any],
    theorem_viii_lift: Mapping[str, Any],
    theorem_viii_discharge: Mapping[str, Any],
    upstream_statuses: Mapping[str, str],
) -> dict[str, Any]:
    active_assumptions = _sequence(theorem_viii_discharge.get("active_assumptions"))
    open_hypotheses = _sequence(theorem_viii_discharge.get("open_hypotheses"))
    remaining_burden = _sequence(theorem_viii_discharge.get("remaining_true_mathematical_burden"))

    required_support_flags = {
        "all_viii_assumptions_dischargeable": bool(
            support_certificate.get("all_viii_assumptions_dischargeable")
        ),
        "final_reduction_implication": bool(
            support_certificate.get(
                "proves_final_reduction_from_identification_envelope_and_exhaustion_to_golden_maximality"
            )
        ),
        "gl2z_normalization": bool(
            support_certificate.get("proves_gl2z_orbit_uniqueness_and_normalization_closed")
        ),
        "universality_matching": bool(
            support_certificate.get("proves_final_universality_class_matches_reduction_statement")
        ),
    }

    readiness_flags = {
        "lift_final_universal_ready": _status(theorem_viii_lift) == FINAL_LIFT_STATUS,
        "discharge_final_strong": _status(theorem_viii_discharge) == FINAL_THEOREM_STATUS,
        "no_active_assumptions": len(active_assumptions) == 0,
        "no_open_hypotheses": len(open_hypotheses) == 0,
        "no_remaining_true_mathematical_burden": len(remaining_burden) == 0,
        "code_path_ready": bool(theorem_viii_discharge.get("final_certificate_ready_for_code_path")),
        "paper_ready": bool(theorem_viii_discharge.get("final_certificate_ready_for_paper")),
        "final_golden_maximality_discharge": bool(
            theorem_viii_discharge.get("final_golden_maximality_discharge")
        ),
        "reduction_geometry_strong": str(
            theorem_viii_discharge.get("current_reduction_geometry_status", "")
        )
        in {
            "current-reduction-geometry-strong",
            "final-reduction-geometry-strong",
            "stage108-final-reduction-geometry-strong",
        },
    }

    upstream_flags = {
        "theorem_i_ii_final": "papergrade-final" in upstream_statuses.get("theorem_i_ii", "")
        or upstream_statuses.get("theorem_i_ii", "").endswith("-strong"),
        "theorem_iii_final": "theorem-iii-final" in upstream_statuses.get("theorem_iii", "")
        or upstream_statuses.get("theorem_iii", "").endswith("-strong"),
        "theorem_iv_final": "theorem-iv-final" in upstream_statuses.get("theorem_iv", "")
        or upstream_statuses.get("theorem_iv", "").endswith("-strong"),
        "theorem_v_downstream_strong": "compressed-contract-strong"
        in upstream_statuses.get("theorem_v_downstream", "")
        or upstream_statuses.get("theorem_v_downstream", "").endswith("-strong"),
        "identification_front_closed": "front-complete"
        in upstream_statuses.get("threshold_identification", "")
        or upstream_statuses.get("threshold_identification", "").endswith("-strong"),
        "theorem_vi_promoted": (
            "screened-one-variable-strong" in upstream_statuses.get("theorem_vi", "")
            or upstream_statuses.get("theorem_vi", "").endswith("-strong")
        ),
        "theorem_vii_final": (
            "exhaustion-discharge-lift-conditional-strong"
            in upstream_statuses.get("theorem_vii", "")
            or upstream_statuses.get("theorem_vii", "").endswith("-strong")
        ),
    }

    failed = [
        key
        for group in (required_support_flags, readiness_flags, upstream_flags)
        for key, value in group.items()
        if not value
    ]

    return {
        "status": "stage108-final-discharge-audit-passed" if not failed else "stage108-final-discharge-audit-failed",
        "required_support_flags": required_support_flags,
        "readiness_flags": readiness_flags,
        "upstream_flags": upstream_flags,
        "failed_checks": failed,
        "active_assumptions": list(active_assumptions),
        "open_hypotheses": list(open_hypotheses),
        "remaining_true_mathematical_burden": list(remaining_burden),
    }


def build_stage108_final_discharge_replay_report(
    *,
    theorem_i_ii_workstream_certificate: Mapping[str, Any],
    theorem_iii_certificate: Mapping[str, Any],
    theorem_iv_certificate: Mapping[str, Any],
    theorem_v_certificate: Mapping[str, Any],
    threshold_identification_certificate: Mapping[str, Any],
    theorem_vi_certificate: Mapping[str, Any],
    theorem_vii_certificate: Mapping[str, Any],
    base_K_values: Sequence[float] = (0.971635, 0.971637),
    family_label: str = "standard-sine",
    representative_label: str = "golden",
    normalization_convention: str = "continued-fraction-positive-reduced-golden-orbit",
    theorem_viii_final_discharge_support_certificate: Mapping[str, Any] | None = None,
) -> Stage108FinalReplayReport:
    """Replay the final Stage-108 theorem ledger and return an audited report."""

    workstream = _to_dict(theorem_i_ii_workstream_certificate)
    thm3 = _to_dict(theorem_iii_certificate)
    thm4 = _to_dict(theorem_iv_certificate)
    thm5 = _to_dict(theorem_v_certificate)
    ident = _to_dict(threshold_identification_certificate)
    thm6 = _to_dict(theorem_vi_certificate)
    thm7 = _to_dict(theorem_vii_certificate)

    support = _to_dict(theorem_viii_final_discharge_support_certificate)
    if not support:
        support = build_theorem_viii_final_discharge_support_certificate(
            threshold_identification_certificate=ident,
            theorem_i_ii_workstream_certificate=workstream,
            theorem_iii_certificate=thm3,
            theorem_iv_certificate=thm4,
            theorem_v_certificate=thm5,
            theorem_vi_certificate=thm6,
            theorem_vii_certificate=thm7,
            family_label=family_label,
            representative_label=representative_label,
            normalization_convention=normalization_convention,
        )

    lift = build_golden_theorem_viii_reduction_lift_certificate(
        base_K_values=base_K_values,
        theorem_i_ii_workstream_certificate=workstream,
        theorem_iii_certificate=thm3,
        theorem_iv_certificate=thm4,
        theorem_v_certificate=thm5,
        threshold_identification_discharge_certificate=ident,
        theorem_vi_envelope_discharge_certificate=thm6,
        theorem_vii_exhaustion_discharge_certificate=thm7,
        theorem_viii_final_discharge_support_certificate=support,
    ).to_dict()

    discharge = build_golden_theorem_viii_reduction_discharge_lift_certificate(
        base_K_values=base_K_values,
        baseline_theorem_viii_certificate=lift,
        theorem_viii_certificate=lift,
        theorem_vii_exhaustion_discharge_certificate=thm7,
        theorem_vi_envelope_discharge_certificate=thm6,
        threshold_identification_discharge_certificate=ident,
        theorem_i_ii_workstream_certificate=workstream,
        theorem_viii_final_discharge_support_certificate=support,
    ).to_dict()

    upstream = _upstream_statuses(
        theorem_i_ii_workstream_certificate=workstream,
        theorem_iii_certificate=thm3,
        theorem_iv_certificate=thm4,
        theorem_v_certificate=thm5,
        threshold_identification_certificate=ident,
        theorem_vi_certificate=thm6,
        theorem_vii_certificate=thm7,
    )
    audit = _audit_final_discharge(
        support_certificate=support,
        theorem_viii_lift=lift,
        theorem_viii_discharge=discharge,
        upstream_statuses=upstream,
    )

    active = _sequence(discharge.get("active_assumptions"))
    open_hypotheses = _sequence(discharge.get("open_hypotheses"))
    remaining = _sequence(discharge.get("remaining_true_mathematical_burden"))
    final_verified = audit.get("status") == "stage108-final-discharge-audit-passed"

    return Stage108FinalReplayReport(
        stage=108,
        theorem_status=FINAL_THEOREM_STATUS if final_verified else _status(discharge),
        theorem_viii_lift_status=_status(lift),
        theorem_viii_discharge_status=_status(discharge),
        final_discharge_verified=final_verified,
        code_path_ready=bool(discharge.get("final_certificate_ready_for_code_path")),
        paper_ready=bool(discharge.get("final_certificate_ready_for_paper")),
        active_assumptions=active,
        open_hypotheses=open_hypotheses,
        remaining_true_mathematical_burden=remaining,
        upstream_statuses=dict(upstream),
        audit=audit,
        support_certificate=dict(support),
        theorem_viii_lift=dict(lift),
        theorem_viii_discharge=dict(discharge),
    )


def save_stage108_final_discharge_artifacts(
    report: Stage108FinalReplayReport | Mapping[str, Any],
    output_dir: str | Path,
) -> dict[str, str]:
    """Save a compact Stage-108 replay artifact set.

    The saved objects are small replay ledgers, not regenerated heavy theorem
    caches.  They are suitable for local inspection but are intentionally not
    included automatically in patch bundles.
    """

    if hasattr(report, "to_dict"):
        report_dict = report.to_dict()  # type: ignore[union-attr]
    else:
        report_dict = dict(report)

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    payloads = {
        "stage108_final_discharge_replay.json": report_dict,
        "stage108_final_theorem_viii_object.json": report_dict.get("theorem_viii_discharge", {}),
        "stage108_final_proof_ledger.json": {
            "stage": 108,
            "theorem_status": report_dict.get("theorem_status"),
            "final_discharge_verified": report_dict.get("final_discharge_verified"),
            "code_path_ready": report_dict.get("code_path_ready"),
            "paper_ready": report_dict.get("paper_ready"),
            "upstream_statuses": report_dict.get("upstream_statuses", {}),
            "audit": report_dict.get("audit", {}),
        },
    }

    paths: dict[str, str] = {}
    for name, payload in payloads.items():
        path = out / name
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        paths[name] = str(path)
    return paths


def assert_stage108_final_discharge_verified(report: Stage108FinalReplayReport | Mapping[str, Any]) -> None:
    """Raise an AssertionError with useful details if final discharge is not clean."""

    report_dict = report.to_dict() if hasattr(report, "to_dict") else dict(report)
    audit = dict(report_dict.get("audit", {}))
    if not report_dict.get("final_discharge_verified"):
        failed = audit.get("failed_checks", [])
        raise AssertionError(f"Stage-108 final discharge was not verified; failed checks: {failed}")
    if report_dict.get("theorem_viii_discharge_status") != FINAL_THEOREM_STATUS:
        raise AssertionError(
            "Unexpected final discharge status: "
            f"{report_dict.get('theorem_viii_discharge_status')!r}"
        )
    for field in ("active_assumptions", "open_hypotheses", "remaining_true_mathematical_burden"):
        if report_dict.get(field):
            raise AssertionError(f"Stage-108 final discharge has nonempty {field}: {report_dict.get(field)}")

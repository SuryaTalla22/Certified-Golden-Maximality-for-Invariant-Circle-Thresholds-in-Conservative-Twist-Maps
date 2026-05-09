from __future__ import annotations

"""Runtime-aware late-row refinement helpers for Theorem V.

These builders implement the *staged decision layer* from the runtime-aware
closure plan:

1. predict a narrow seed window cheaply,
2. decide whether a direct theorem-mode attempt is justified under the current
   runtime budget, and
3. if allowed, run the existing theorem-IV-style local methodology on the
   predicted window.

The default path is intentionally conservative: it records timing, seeds, and
recommendations even when a direct attempt is skipped.
"""

from dataclasses import asdict, dataclass
import time
from typing import Any, Mapping, Sequence

from .obstruction_atlas import ApproximantWindowSpec
from .standard_map import HarmonicFamily
from .theorem_iv_methodology import (
    get_theorem_iv_methodology_profile,
    methodology_localize_theorem_iv_crossing,
)
from .theorem_v_seed_prediction import (
    decide_runtime_aware_row_attempt,
    predict_future_golden_row_seed,
)


@dataclass
class TheoremVRuntimeAwareRowCertificate:
    label: str
    p: int
    q: int
    seed_prediction: dict[str, Any]
    attempt_decision: dict[str, Any]
    direct_attempt_performed: bool
    direct_attempt_seconds: float
    direct_attempt_status: str
    direct_attempt_success: bool
    direct_attempt_proof_ready: bool
    selected_window_lo: float
    selected_window_hi: float
    selected_window_width: float
    selected_center: float
    methodology_frontend: dict[str, Any] | None
    theorem_status: str
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)



def _build_row_spec(seed: Mapping[str, Any], p: int, q: int) -> ApproximantWindowSpec:
    lo = float(seed["predictive_window_lo"])
    hi = float(seed["predictive_window_hi"])
    center = float(seed["predictive_center"])
    half_width = 0.5 * float(seed["predictive_window_width"])
    band_offset = max(5.0e-2, 20.0 * half_width)
    band_half_width = max(2.0e-2, 10.0 * half_width)
    return ApproximantWindowSpec(
        p=int(p),
        q=int(q),
        crossing_K_lo=float(lo),
        crossing_K_hi=float(hi),
        band_search_lo=float(center + band_offset - band_half_width),
        band_search_hi=float(center + band_offset + band_half_width),
        label=f"gold-{int(p)}/{int(q)}",
    )


def build_runtime_aware_theorem_v_row_certificate(
    ladder: Mapping[str, Any] | None,
    *,
    p: int,
    q: int,
    family: HarmonicFamily | None = None,
    theorem_target_interval: Sequence[float] | None = None,
    explicit_error_certificate: Mapping[str, Any] | None = None,
    allow_direct_refinement: bool = False,
    budget_hours: float = 8.0,
    hard_q_cap: int = 400,
    reference_q: int = 233,
    reference_hours: float = 6.0,
    scaling_exponent: float = 2.3,
    target_residue: float = 0.25,
) -> TheoremVRuntimeAwareRowCertificate:
    family = family or HarmonicFamily()
    seed = predict_future_golden_row_seed(
        ladder,
        p=p,
        q=q,
        theorem_target_interval=theorem_target_interval,
        explicit_error_certificate=explicit_error_certificate,
        reference_q=reference_q,
        reference_hours=reference_hours,
        scaling_exponent=scaling_exponent,
        direct_recommendation_hours=budget_hours,
    ).to_dict()
    decision = decide_runtime_aware_row_attempt(
        seed,
        budget_hours=budget_hours,
        allow_direct_refinement=allow_direct_refinement,
        hard_q_cap=hard_q_cap,
    ).to_dict()

    selected_lo = float(seed["predictive_window_lo"])
    selected_hi = float(seed["predictive_window_hi"])
    selected_width = float(seed["predictive_window_width"])
    selected_center = float(seed["predictive_center"])
    direct_attempt_performed = False
    direct_attempt_success = False
    direct_attempt_proof_ready = False
    direct_attempt_status = str(decision["decision"])
    methodology_frontend: dict[str, Any] | None = None
    dt = 0.0

    if bool(decision["attempt_direct_refinement"]):
        direct_attempt_performed = True
        spec = _build_row_spec(seed, int(p), int(q))
        profile = get_theorem_iv_methodology_profile(int(p), int(q))
        t0 = time.perf_counter()
        frontend = methodology_localize_theorem_iv_crossing(
            spec,
            family=family,
            target_residue=target_residue,
            profile=profile,
            predictive_hint_center=float(seed["predictive_center"]),
            previous_entry_dicts=list((ladder or {}).get("approximants") or []),
            enable_high_precision=True,
        )
        dt = time.perf_counter() - t0
        methodology_frontend = dict(frontend)
        selected_lo = float(frontend.get("K_lo", selected_lo))
        selected_hi = float(frontend.get("K_hi", selected_hi))
        selected_width = float(frontend.get("width", selected_width))
        selected_center = 0.5 * (selected_lo + selected_hi)
        direct_attempt_success = bool(frontend.get("success", False))
        direct_attempt_proof_ready = bool(frontend.get("proof_ready", False))
        if direct_attempt_proof_ready:
            direct_attempt_status = "theorem-mode-local-success"
        elif direct_attempt_success:
            direct_attempt_status = "direct-attempt-nonproof-success"
        else:
            direct_attempt_status = str(frontend.get("status", "direct-attempt-failed"))

    if direct_attempt_proof_ready:
        theorem_status = "runtime-aware-row-proof-ready"
        notes = (
            "A seeded narrow-window theorem-mode attempt succeeded; this late row can now feed the transport/tail closure layers directly."
        )
    elif direct_attempt_performed:
        theorem_status = "runtime-aware-row-attempted-not-closed"
        notes = (
            "A seeded narrow-window theorem-mode attempt was run, but it did not produce a proof-ready local certificate. "
            "The artifact is still useful as a diagnostic for whether more runtime should be spent on this row."
        )
    else:
        theorem_status = "runtime-aware-row-skipped"
        notes = (
            "No direct theorem-mode row attempt was made.  The predictive seed and estimated runtime were recorded so the closure pipeline can decide whether transport/tail strengthening is preferable to brute-force local certification."
        )

    return TheoremVRuntimeAwareRowCertificate(
        label=f"gold-{int(p)}/{int(q)}",
        p=int(p),
        q=int(q),
        seed_prediction=seed,
        attempt_decision=decision,
        direct_attempt_performed=bool(direct_attempt_performed),
        direct_attempt_seconds=float(dt),
        direct_attempt_status=direct_attempt_status,
        direct_attempt_success=bool(direct_attempt_success),
        direct_attempt_proof_ready=bool(direct_attempt_proof_ready),
        selected_window_lo=float(selected_lo),
        selected_window_hi=float(selected_hi),
        selected_window_width=float(selected_width),
        selected_center=float(selected_center),
        methodology_frontend=methodology_frontend,
        theorem_status=theorem_status,
        notes=notes,
    )


__all__ = [
    "TheoremVRuntimeAwareRowCertificate",
    "build_runtime_aware_theorem_v_row_certificate",
]

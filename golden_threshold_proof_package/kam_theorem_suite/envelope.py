from __future__ import annotations

from typing import Any, Dict, Mapping, Sequence

import numpy as np
import pandas as pd


def isotonic_regression(x: Sequence[float], y: Sequence[float], weights: Sequence[float] | None = None) -> np.ndarray:
    """Pool-adjacent-violators algorithm for nondecreasing isotonic regression."""
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    order = np.argsort(x)
    y = y[order]
    w = np.ones_like(y) if weights is None else np.asarray(weights, dtype=float)[order]

    blocks = [{"start": i, "end": i, "weight": w[i], "mean": y[i]} for i in range(len(y))]
    i = 0
    while i < len(blocks) - 1:
        if blocks[i]["mean"] <= blocks[i + 1]["mean"]:
            i += 1
            continue
        total_w = blocks[i]["weight"] + blocks[i + 1]["weight"]
        total_m = (blocks[i]["weight"] * blocks[i]["mean"] + blocks[i + 1]["weight"] * blocks[i + 1]["mean"]) / total_w
        merged = {
            "start": blocks[i]["start"],
            "end": blocks[i + 1]["end"],
            "weight": total_w,
            "mean": total_m,
        }
        blocks[i:i + 2] = [merged]
        i = max(0, i - 1)

    out = np.empty(len(y), dtype=float)
    for block in blocks:
        out[block["start"]: block["end"] + 1] = block["mean"]

    inv_order = np.empty_like(order)
    inv_order[order] = np.arange(len(order))
    return out[inv_order]


def conservative_eta_envelope(df: pd.DataFrame, eta_col: str = "eta_approx") -> pd.DataFrame:
    """Build conservative isotonic envelopes from certified threshold intervals.

    Required columns:
      - eta_col
      - threshold_lo
      - threshold_hi
      - is_golden (bool)
    """
    out = df.copy().sort_values(eta_col).reset_index(drop=True)
    out["iso_upper_nondec"] = isotonic_regression(out[eta_col], out["threshold_hi"])
    out["iso_lower_nondec"] = isotonic_regression(out[eta_col], out["threshold_lo"])
    return out


def panel_gap_summary(df: pd.DataFrame, eta_col: str = "eta_approx") -> Dict[str, float]:
    env = conservative_eta_envelope(df, eta_col=eta_col)
    if "is_golden" not in env:
        raise ValueError("DataFrame must include is_golden")
    golden = env[env["is_golden"]].copy()
    if golden.empty:
        raise ValueError("No golden row present")
    golden_lower = float(golden["threshold_lo"].max())
    nongolden_max_upper = float(env.loc[~env["is_golden"], "threshold_hi"].max())
    golden_eta = float(golden[eta_col].max())
    nongolden_eta_max = float(env.loc[~env["is_golden"], eta_col].max())
    env_gap = golden_lower - nongolden_max_upper
    return {
        "golden_lower_bound": golden_lower,
        "nongolden_max_upper_bound": nongolden_max_upper,
        "raw_gap": env_gap,
        "golden_eta": golden_eta,
        "nongolden_eta_max": nongolden_eta_max,
    }


def build_eta_statement_mode_certificate(
    df: pd.DataFrame | Sequence[dict[str, Any]],
    *,
    eta_col: str = "eta_approx",
    threshold_lo_col: str = "threshold_lo",
    threshold_hi_col: str = "threshold_hi",
    top_gap_scale: float | None = None,
    min_rows_for_mode_lock: int = 3,
    one_variable_relative_spread_tol: float = 0.25,
    two_variable_relative_spread_tol: float = 0.75,
    monotonicity_relative_tol: float = 0.25,
    eta_group_decimals: int = 12,
) -> Dict[str, Any]:
    """Build a theorem-facing statement-mode certificate from finite eta-panel evidence.

    The current repository cannot *prove* the final Theorem VI statement mode here, but it can
    quantify whether the present finite panel supports a one-variable eta law, suggests that an
    extra covariate is needed, or remains inconclusive.
    """
    if not isinstance(df, pd.DataFrame):
        df = pd.DataFrame(list(df))
    if df.empty:
        return {
            "candidate_mode": "unresolved",
            "mode_lock_status": "insufficient-panel-data",
            "status": "statement-mode-certificate-unresolved",
            "row_count": 0,
            "unique_eta_count": 0,
            "duplicate_eta_bucket_count": 0,
            "max_within_eta_spread": None,
            "monotonicity_defect": None,
            "support_scale": None,
            "one_variable_spread_tol": None,
            "two_variable_spread_tol": None,
            "monotonicity_tol": None,
            "evidence_margin": None,
            "residual_obstruction": "no exploratory eta-panel data are currently available",
        }

    required = {eta_col, threshold_lo_col, threshold_hi_col}
    missing = required.difference(df.columns)
    if missing:
        return {
            "candidate_mode": "unresolved",
            "mode_lock_status": "panel-columns-missing",
            "status": "statement-mode-certificate-unresolved",
            "row_count": int(len(df)),
            "unique_eta_count": None,
            "duplicate_eta_bucket_count": None,
            "max_within_eta_spread": None,
            "monotonicity_defect": None,
            "support_scale": None,
            "one_variable_spread_tol": None,
            "two_variable_spread_tol": None,
            "monotonicity_tol": None,
            "evidence_margin": None,
            "residual_obstruction": f"missing required columns: {sorted(missing)}",
        }

    work = df[[eta_col, threshold_lo_col, threshold_hi_col]].copy()
    work = work.dropna(subset=[eta_col, threshold_lo_col, threshold_hi_col]).reset_index(drop=True)
    if work.empty:
        return {
            "candidate_mode": "unresolved",
            "mode_lock_status": "panel-rows-incomplete",
            "status": "statement-mode-certificate-unresolved",
            "row_count": 0,
            "unique_eta_count": 0,
            "duplicate_eta_bucket_count": 0,
            "max_within_eta_spread": None,
            "monotonicity_defect": None,
            "support_scale": None,
            "one_variable_spread_tol": None,
            "two_variable_spread_tol": None,
            "monotonicity_tol": None,
            "evidence_margin": None,
            "residual_obstruction": "all candidate eta-panel rows were incomplete",
        }

    work["threshold_center"] = 0.5 * (work[threshold_lo_col] + work[threshold_hi_col])
    work["eta_bucket"] = work[eta_col].astype(float).round(eta_group_decimals)

    grouped = work.groupby("eta_bucket", sort=True)
    eta_groups = grouped.agg(
        eta_center=(eta_col, "mean"),
        threshold_lo_min=(threshold_lo_col, "min"),
        threshold_hi_max=(threshold_hi_col, "max"),
        threshold_center_mean=("threshold_center", "mean"),
        count=(eta_col, "size"),
    ).reset_index(drop=True)
    eta_groups["within_eta_spread"] = eta_groups["threshold_hi_max"] - eta_groups["threshold_lo_min"]

    row_count = int(len(work))
    unique_eta_count = int(len(eta_groups))
    duplicate_eta_bucket_count = int((eta_groups["count"] > 1).sum())
    max_within_eta_spread = float(eta_groups["within_eta_spread"].max())

    centers = work.sort_values(eta_col)["threshold_center"].to_numpy(dtype=float)
    etas = work.sort_values(eta_col)[eta_col].to_numpy(dtype=float)
    iso = isotonic_regression(etas, centers)
    monotonicity_defect = float(np.max(np.abs(centers - iso))) if len(centers) else 0.0

    raw_threshold_scale = float(work[threshold_hi_col].max() - work[threshold_lo_col].min())
    support_scale = top_gap_scale
    if support_scale is None or float(support_scale) <= 0.0:
        support_scale = raw_threshold_scale if raw_threshold_scale > 0.0 else float(max_within_eta_spread)
    support_scale = float(max(float(support_scale), 1.0e-12))

    one_tol = float(max(1.0e-12, one_variable_relative_spread_tol * support_scale))
    two_tol = float(max(one_tol, two_variable_relative_spread_tol * support_scale))
    mono_tol = float(max(1.0e-12, monotonicity_relative_tol * support_scale))

    if duplicate_eta_bucket_count > 0 and max_within_eta_spread > two_tol:
        candidate_mode = "two-variable"
        mode_lock_status = "two-variable-supported"
        status = "statement-mode-certificate-two-variable-supported"
        evidence_margin = float(max_within_eta_spread - two_tol)
        residual_obstruction = "the current panel exhibits a repeated-eta spread larger than the two-variable tolerance, so eta alone is not yet a stable sufficient statistic"
    elif row_count >= min_rows_for_mode_lock and monotonicity_defect <= mono_tol and max_within_eta_spread <= one_tol:
        candidate_mode = "one-variable"
        mode_lock_status = "one-variable-supported"
        status = "statement-mode-certificate-one-variable-supported"
        evidence_margin = float(min(one_tol - max_within_eta_spread, mono_tol - monotonicity_defect))
        residual_obstruction = "promote the current finite eta-only evidence into a theorem-grade one-variable envelope law"
    else:
        candidate_mode = "unresolved"
        mode_lock_status = "statement-mode-unresolved"
        status = "statement-mode-certificate-unresolved"
        evidence_margin = None
        if row_count < min_rows_for_mode_lock:
            residual_obstruction = "the current eta panel is too small to lock the statement mode"
        elif monotonicity_defect > mono_tol:
            residual_obstruction = "the current eta panel still shows monotonicity defect too large to certify a one-variable envelope law"
        else:
            residual_obstruction = "the current eta panel is consistent with more than one final statement mode at the present resolution"

    return {
        "candidate_mode": candidate_mode,
        "mode_lock_status": mode_lock_status,
        "status": status,
        "row_count": row_count,
        "unique_eta_count": unique_eta_count,
        "duplicate_eta_bucket_count": duplicate_eta_bucket_count,
        "max_within_eta_spread": max_within_eta_spread,
        "monotonicity_defect": monotonicity_defect,
        "support_scale": support_scale,
        "one_variable_spread_tol": one_tol,
        "two_variable_spread_tol": two_tol,
        "monotonicity_tol": mono_tol,
        "evidence_margin": evidence_margin,
        "residual_obstruction": residual_obstruction,
        "eta_group_rows": eta_groups.to_dict(orient="records"),
    }


def build_eta_mode_obstruction_certificate(
    statement_mode_certificate: Mapping[str, Any] | None,
    *,
    one_variable_obstruction_margin: float | None = None,
) -> Dict[str, Any]:
    """Package whether the current finite panel obstructs an eta-only law."""

    cert = dict(statement_mode_certificate or {})
    candidate_mode = str(cert.get("candidate_mode", "unresolved"))
    mode_lock_status = str(cert.get("mode_lock_status", "statement-mode-unresolved"))
    evidence_margin = cert.get("evidence_margin")
    evidence_margin = None if evidence_margin is None else float(evidence_margin)
    obstruction_margin = evidence_margin if one_variable_obstruction_margin is None else float(one_variable_obstruction_margin)

    if candidate_mode == "two-variable" and "two-variable-supported" in mode_lock_status:
        obstruction_status = "one-variable-obstruction-certified"
        one_variable_obstruction_certified = True
        two_variable_need_supported = True
        residual_obstruction = (
            "the finite eta panel already obstructs an eta-only reduction, so any final Theorem VI "
            "statement must either be corrected two-variable or explain away the present obstruction"
        )
    elif candidate_mode == "one-variable" and "one-variable-supported" in mode_lock_status:
        obstruction_status = "no-certified-one-variable-obstruction"
        one_variable_obstruction_certified = False
        two_variable_need_supported = False
        residual_obstruction = (
            "the current finite panel does not obstruct a one-variable eta law, but it still does "
            "not certify the final theorem-grade reduction"
        )
    else:
        obstruction_status = "one-variable-obstruction-unresolved"
        one_variable_obstruction_certified = False
        two_variable_need_supported = False
        residual_obstruction = (
            "the present panel does not yet resolve whether eta alone is obstructed or whether the "
            "unresolved spread is only a finite-resolution artifact"
        )

    return {
        "candidate_mode": candidate_mode,
        "mode_lock_status": mode_lock_status,
        "obstruction_status": obstruction_status,
        "one_variable_obstruction_certified": one_variable_obstruction_certified,
        "two_variable_need_supported": two_variable_need_supported,
        "obstruction_margin": obstruction_margin,
        "source_status": None if cert.get("status") is None else str(cert.get("status")),
        "residual_obstruction": residual_obstruction,
    }


def build_eta_mode_reduction_certificate(
    statement_mode_certificate: Mapping[str, Any] | None,
    *,
    mode_obstruction_certificate: Mapping[str, Any] | None = None,
    current_local_top_gap_status: str | None = None,
    anchor_globalization_certificate: Mapping[str, Any] | None = None,
    global_nongolden_ceiling_certificate: Mapping[str, Any] | None = None,
) -> Dict[str, Any]:
    """Distinguish diagnostic mode support from theorem-grade mode reduction.

    Stage 85 strengthens this layer by allowing one-variable mode to become theorem-grade
    when the finite mode certificate, anchor globalization witness, and global challenger
    ceiling all align strongly enough to support a true eta-only reduction.
    """

    cert = dict(statement_mode_certificate or {})
    obstruction = dict(mode_obstruction_certificate or build_eta_mode_obstruction_certificate(cert))
    candidate_mode = str(cert.get("candidate_mode", "unresolved"))
    mode_lock_status = str(cert.get("mode_lock_status", "statement-mode-unresolved"))
    current_local_top_gap_status = None if current_local_top_gap_status is None else str(current_local_top_gap_status)
    anchor_global = dict(anchor_globalization_certificate or {})
    ceiling = dict(global_nongolden_ceiling_certificate or {})

    anchor_status = str(anchor_global.get('anchor_globalization_status', 'anchor-globalization-unavailable'))
    anchor_ready = bool(anchor_global.get('anchor_ready_for_global_envelope', False))
    anchor_transport_locked = bool(anchor_global.get('anchor_transport_locked', False))
    anchor_identification_locked = bool(anchor_global.get('anchor_identification_locked', False))
    ceiling_status = str(ceiling.get('global_ceiling_status', 'global-ceiling-unavailable'))
    ceiling_margin = ceiling.get('global_gap_margin')
    ceiling_margin = None if ceiling_margin is None else float(ceiling_margin)
    ceiling_certified = bool(ceiling.get('global_ceiling_theorem_certified', False)) or ('strong' in ceiling_status or 'certified' in ceiling_status)
    local_top_gap_strong = bool(current_local_top_gap_status and current_local_top_gap_status.endswith('strong'))

    if obstruction.get("one_variable_obstruction_certified", False) and candidate_mode == "two-variable":
        theorem_mode = "two-variable"
        theorem_mode_status = "two-variable-reduction-certified-from-obstruction"
        reduction_certified = True
        reduction_margin = obstruction.get("obstruction_margin")
        remaining_burden = "prove the corrected two-variable envelope theorem in the final theorem norm structure"
    elif (
        candidate_mode == "one-variable"
        and "one-variable-supported" in mode_lock_status
        and local_top_gap_strong
        and anchor_ready
        and anchor_transport_locked
        and anchor_identification_locked
        and ceiling_certified
        and ceiling_margin is not None
        and ceiling_margin > 0.0
    ):
        theorem_mode = "one-variable"
        theorem_mode_status = "one-variable-reduction-certified-globalized"
        reduction_certified = True
        reduction_margin = min(float(cert.get("evidence_margin") or ceiling_margin), ceiling_margin)
        remaining_burden = "none"
    elif (
        candidate_mode == "one-variable"
        and "one-variable-supported" in mode_lock_status
        and current_local_top_gap_status in {"current-local-top-gap-strong", "current-local-top-gap-screened-domination-positive"}
        and anchor_ready
        and anchor_transport_locked
        and anchor_identification_locked
    ):
        theorem_mode = "one-variable"
        theorem_mode_status = "one-variable-reduction-certified-screened-panel"
        reduction_certified = True
        reduction_margin = cert.get("evidence_margin")
        remaining_burden = (
            "the local screened-panel geometry now certifies the one-variable Theorem VI reduction; "
            "the remaining burden is global challenger exhaustion beyond the present trusted panel, which is deferred to Theorem VII"
        )
    elif candidate_mode == "one-variable" and "one-variable-supported" in mode_lock_status:
        theorem_mode = "unresolved"
        theorem_mode_status = "one-variable-diagnostic-support-only"
        reduction_certified = False
        reduction_margin = cert.get("evidence_margin")
        if current_local_top_gap_status and current_local_top_gap_status.endswith("strong"):
            remaining_burden = (
                "the screened-panel geometry supports a one-variable reading, but the final one-variable "
                "reduction is not yet theorem-grade/global"
            )
        else:
            remaining_burden = "promote the current finite eta-only diagnostic into a theorem-grade one-variable reduction"
    else:
        theorem_mode = "unresolved"
        theorem_mode_status = "statement-mode-reduction-unresolved"
        reduction_certified = False
        reduction_margin = cert.get("evidence_margin")
        remaining_burden = (
            "the present finite data do not yet reduce Theorem VI to a theorem-grade one-variable or "
            "corrected two-variable final statement"
        )

    return {
        "candidate_mode": candidate_mode,
        "diagnostic_mode_lock_status": mode_lock_status,
        "theorem_mode": theorem_mode,
        "theorem_mode_status": theorem_mode_status,
        "reduction_certified": reduction_certified,
        "reduction_margin": None if reduction_margin is None else float(reduction_margin),
        "source_status": None if cert.get("status") is None else str(cert.get("status")),
        "current_local_top_gap_status": current_local_top_gap_status,
        "anchor_globalization_status": anchor_status,
        "anchor_globalization_ready": anchor_ready,
        "global_ceiling_status": ceiling_status,
        "global_ceiling_theorem_certified": bool(ceiling.get('global_ceiling_theorem_certified', False)),
        "global_ceiling_margin": ceiling_margin,
        "remaining_burden": remaining_burden,
    }

def build_eta_global_envelope_certificate(
    *,
    golden_lower_witness: float | None,
    nongolden_global_upper_ceiling: float | None,
    mode_reduction_certificate: Mapping[str, Any] | None = None,
    ceiling_decomposition: Mapping[str, Any] | None = None,
    theorem_mode: str | None = None,
) -> Dict[str, Any]:
    """Assemble a theorem-facing global envelope candidate."""

    mode_cert = dict(mode_reduction_certificate or {})
    theorem_mode = str(theorem_mode or mode_cert.get("theorem_mode", "unresolved"))
    reduction_certified = bool(mode_cert.get("reduction_certified", False))
    decomposition = dict(ceiling_decomposition or {})
    ceiling_status = decomposition.get("global_ceiling_status")
    if ceiling_status is None:
        ceiling_status = "global-ceiling-unavailable" if nongolden_global_upper_ceiling is None else "global-ceiling-partial"
    else:
        ceiling_status = str(ceiling_status)

    strict_top_gap_margin = None
    if golden_lower_witness is not None and nongolden_global_upper_ceiling is not None:
        strict_top_gap_margin = float(golden_lower_witness - nongolden_global_upper_ceiling)

    strict_positive = bool(strict_top_gap_margin is not None and strict_top_gap_margin > 0.0)
    theorem_certified = bool(reduction_certified and strict_positive and ('strong' in ceiling_status or 'certified' in ceiling_status))
    if golden_lower_witness is None or nongolden_global_upper_ceiling is None:
        theorem_status = "global-envelope-candidate-unavailable"
        remaining_burden = "the global envelope candidate is missing either the golden lower witness or the nongolden global ceiling"
    elif not reduction_certified:
        theorem_status = "global-envelope-candidate-mode-unresolved"
        remaining_burden = "the challenger ceiling is available, but the final theorem mode has not yet been reduced beyond diagnostic support"
    elif "strong" not in ceiling_status and "certified" not in ceiling_status:
        theorem_status = "global-envelope-candidate-globalization-incomplete"
        remaining_burden = "the theorem mode is reduced, but the nongolden ceiling is not yet globally certified"
    elif strict_positive:
        theorem_status = f"global-envelope-theorem-{theorem_mode}-certified"
        remaining_burden = "none"
    else:
        theorem_status = f"global-envelope-candidate-{theorem_mode}-nonpositive-gap"
        remaining_burden = "the current global ceiling still reaches or exceeds the golden lower witness"

    return {
        "theorem_mode": theorem_mode,
        "mode_reduction_certified": reduction_certified,
        "golden_lower_witness": None if golden_lower_witness is None else float(golden_lower_witness),
        "nongolden_global_upper_ceiling": None if nongolden_global_upper_ceiling is None else float(nongolden_global_upper_ceiling),
        "ceiling_decomposition": decomposition,
        "global_ceiling_status": ceiling_status,
        "strict_top_gap_margin": None if strict_top_gap_margin is None else float(strict_top_gap_margin),
        "strict_top_gap_positive": strict_positive,
        "theorem_certified": theorem_certified,
        "theorem_status": theorem_status,
        "remaining_burden": remaining_burden,
    }

def build_strict_golden_top_gap_theorem_candidate(
    global_envelope_certificate: Mapping[str, Any] | None,
) -> Dict[str, Any]:
    """Package the theorem-facing strict golden top-gap candidate."""

    cert = dict(global_envelope_certificate or {})
    theorem_mode = str(cert.get("theorem_mode", "unresolved"))
    margin = cert.get("strict_top_gap_margin")
    margin = None if margin is None else float(margin)
    strict_positive = bool(cert.get("strict_top_gap_positive", False))
    ceiling_status = str(cert.get("global_ceiling_status", "global-ceiling-unavailable"))
    mode_reduction_certified = bool(cert.get("mode_reduction_certified", False))
    envelope_theorem_certified = bool(cert.get('theorem_certified', False))

    if strict_positive and mode_reduction_certified and envelope_theorem_certified and ("strong" in ceiling_status or "certified" in ceiling_status):
        status = f"strict-golden-top-gap-theorem-{theorem_mode}-certified"
        certified = True
        remaining_burden = "none"
    elif strict_positive:
        status = "strict-golden-top-gap-globalization-incomplete"
        certified = False
        remaining_burden = (
            "the global gap is positive on the current ceiling object, but either the final theorem mode or the global ceiling certification is still incomplete"
        )
    elif margin is None:
        status = "strict-golden-top-gap-global-unavailable"
        certified = False
        remaining_burden = "the current global envelope candidate does not yet supply a comparable golden lower witness and nongolden ceiling"
    else:
        status = "strict-golden-top-gap-nonpositive"
        certified = False
        remaining_burden = "the current global nongolden ceiling still reaches or exceeds the golden lower witness"

    return {
        "theorem_mode": theorem_mode,
        "global_strict_top_gap_margin": margin,
        "global_strict_top_gap_positive": strict_positive,
        "global_strict_top_gap_certified": certified,
        "global_strict_top_gap_status": status,
        "global_ceiling_status": ceiling_status,
        "envelope_theorem_certified": envelope_theorem_certified,
        "remaining_burden": remaining_burden,
    }

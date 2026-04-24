from __future__ import annotations

"""Theorem-V upper-side reuse helpers.

This module lets Theorem V inherit as much upper-side work as possible from the
finalized Theorem-IV line.  The main reuse path is:

1. load the strongest available Theorem-IV upper-shift report from the staged
   cache (preferring the baseline shift),
2. recycle its already-certified approximant atlas entries, including the
   transported tail rows, as the ladder consumed by the Theorem-V transport
   stack, and
3. expose the final Theorem-IV upper bridge as the refined/asymptotic upper
   witness so Theorem V does not rebuild a weaker legacy upper ladder.

The output is shaped to look like a golden supercritical obstruction
certificate, because the current Theorem-V builders only need that schema and do
not require the original builder provenance.
"""

from dataclasses import asdict, dataclass
import json
from pathlib import Path
import re
from typing import Any, Mapping

from .golden_aposteriori import golden_inverse


@dataclass
class TheoremVInheritedUpperSeedCertificate:
    rho: float
    family_label: str
    target_residue: float
    crossing_center: float
    crossing_half_width: float
    band_offset: float
    band_width: float
    generated_convergents: list[dict[str, Any]]
    ladder: dict[str, Any]
    refined: dict[str, Any]
    asymptotic_audit: dict[str, Any]
    selected_upper_source: str
    selected_upper_lo: float | None
    selected_upper_hi: float | None
    selected_upper_width: float | None
    earliest_hyperbolic_band_lo: float | None
    latest_hyperbolic_band_hi: float | None
    successful_crossing_count: int
    successful_band_count: int
    theorem_status: str
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


_SHIFT_REPORT_RE = re.compile(r"^theorem_iv_upper_shift_(?P<token>.+)_report\.json$")


def _repo_stage_cache_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "artifacts" / "final_discharge" / "stage_cache"


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _status_rank(status: str) -> int:
    status = str(status)
    if status.endswith("-strong"):
        return 4
    if status.endswith("-moderate"):
        return 3
    if status.endswith("-weak"):
        return 2
    if status.endswith("-fragile"):
        return 1
    return 0


def _parse_shift_token(token: str) -> float:
    if token == "0":
        return 0.0
    sign = -1.0 if token.startswith("m") else 1.0
    core = token[1:] if token.startswith("m") else token
    if "p" in core:
        left, right = core.split("p", 1)
        if left == "":
            left = "0"
        return sign * float(f"{left}.{right}")
    return sign * float(core)


def _normalize_bridge_payload(payload: Mapping[str, Any] | None) -> Mapping[str, Any] | None:
    if not isinstance(payload, Mapping):
        return None
    selected = payload.get("selected_bridge")
    if isinstance(selected, Mapping):
        return selected
    return payload


def _select_theorem_iv_upper_bridge(theorem_iv_certificate: Mapping[str, Any]) -> Mapping[str, Any]:
    nonexistence_front = theorem_iv_certificate.get("nonexistence_front")
    if not isinstance(nonexistence_front, Mapping):
        raise ValueError("Theorem-IV certificate does not expose a nonexistence_front payload.")

    search_order = (
        nonexistence_front.get("upper_bridge_profile"),
        nonexistence_front.get("upper_tail_aware_neighborhood"),
        nonexistence_front.get("upper_support_core_neighborhood"),
        nonexistence_front.get("upper_bridge_promotion"),
        nonexistence_front.get("upper_bridge"),
    )
    for candidate in search_order:
        bridge = _normalize_bridge_payload(candidate)
        if isinstance(bridge, Mapping) and bridge.get("certified_upper_lo") is not None and bridge.get("certified_upper_hi") is not None:
            return bridge
    raise ValueError("Theorem-IV certificate does not expose a reusable upper bridge.")


def _pick_shift_report(stage_cache_dir: Path, preferred_shift: float) -> tuple[dict[str, Any], float, Path]:
    candidates: list[tuple[float, int, float, Path, dict[str, Any]]] = []
    for path in stage_cache_dir.glob("theorem_iv_upper_shift_*_report.json"):
        match = _SHIFT_REPORT_RE.match(path.name)
        if match is None:
            continue
        token = match.group("token")
        try:
            shift = _parse_shift_token(token)
        except Exception:
            continue
        payload = _load_json(path)
        if not isinstance(payload, dict):
            continue
        status = str(payload.get("theorem_status", "unknown"))
        rank = _status_rank(status)
        candidates.append((abs(shift - float(preferred_shift)), -rank, abs(shift), path, payload))
    if not candidates:
        raise FileNotFoundError("No theorem-IV upper-shift reports were found in the stage cache.")
    candidates.sort(key=lambda item: (item[0], item[1], item[2], item[3].name))
    _, _, shift_abs, path, payload = candidates[0]
    shift = _parse_shift_token(_SHIFT_REPORT_RE.match(path.name).group("token"))  # type: ignore[union-attr]
    return payload, float(shift), path


def _approx_entry(entry: Mapping[str, Any]) -> dict[str, Any]:
    out = dict(entry)
    lo = out.get("crossing_root_window_lo")
    hi = out.get("crossing_root_window_hi")
    if out.get("crossing_center") is None and lo is not None and hi is not None:
        out["crossing_center"] = 0.5 * (float(lo) + float(hi))
    if out.get("crossing_root_window_width") is None and lo is not None and hi is not None:
        out["crossing_root_window_width"] = float(hi) - float(lo)
    return out


def _generated_convergents(entries: list[dict[str, Any]], rho: float) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for entry in entries:
        p = int(entry.get("p", 0) or 0)
        q = int(entry.get("q", 0) or 0)
        crossing_lo = entry.get("crossing_window_input_lo", entry.get("crossing_root_window_lo"))
        crossing_hi = entry.get("crossing_window_input_hi", entry.get("crossing_root_window_hi"))
        band_lo = entry.get("band_search_lo", entry.get("hyperbolic_band_lo"))
        band_hi = entry.get("band_search_hi", entry.get("hyperbolic_band_hi"))
        rho_pq = float(p / q) if q else 0.0
        out.append(
            {
                "p": p,
                "q": q,
                "label": str(entry.get("label", f"gold-{p}/{q}")),
                "rho": rho_pq,
                "rho_error": abs(rho_pq - float(rho)),
                "crossing_K_lo": None if crossing_lo is None else float(crossing_lo),
                "crossing_K_hi": None if crossing_hi is None else float(crossing_hi),
                "band_search_lo": None if band_lo is None else float(band_lo),
                "band_search_hi": None if band_hi is None else float(band_hi),
            }
        )
    return out


def build_golden_supercritical_obstruction_certificate_from_theorem_iv(
    theorem_iv_certificate: Mapping[str, Any],
    *,
    preferred_shift: float = 0.0,
    stage_cache_dir: str | Path | None = None,
    target_residue: float = 0.25,
) -> TheoremVInheritedUpperSeedCertificate:
    stage_cache = Path(stage_cache_dir) if stage_cache_dir is not None else _repo_stage_cache_dir()
    shift_report, realized_shift, report_path = _pick_shift_report(stage_cache, preferred_shift)
    atlas = dict(shift_report.get("atlas") or {})
    entries = [_approx_entry(entry) for entry in list(atlas.get("entries") or []) if isinstance(entry, Mapping)]
    if not entries:
        raise ValueError("Selected theorem-IV upper-shift report does not contain atlas entries.")

    bridge = _select_theorem_iv_upper_bridge(theorem_iv_certificate)
    nonexistence_front = theorem_iv_certificate.get("nonexistence_front")
    nonexistence_front = dict(nonexistence_front) if isinstance(nonexistence_front, Mapping) else {}
    tail_stability = dict(nonexistence_front.get("upper_tail_stability") or {})
    contradiction_summary = dict(theorem_iv_certificate.get("contradiction_summary") or {})

    stable_tail_qs = [int(x) for x in bridge.get("certified_tail_qs", tail_stability.get("stable_tail_qs", []))]
    stable_tail_start_q = bridge.get("certified_tail_start_q", tail_stability.get("stable_tail_start_q"))
    if stable_tail_start_q is None and stable_tail_qs:
        stable_tail_start_q = min(stable_tail_qs)

    upper_lo = bridge.get("certified_upper_lo")
    upper_hi = bridge.get("certified_upper_hi")
    upper_w = bridge.get("certified_upper_width")
    barrier_lo = bridge.get("certified_barrier_lo", tail_stability.get("stable_barrier_lo"))
    barrier_hi = bridge.get("certified_barrier_hi", tail_stability.get("stable_barrier_hi"))

    crossing_los = [float(e["crossing_root_window_lo"]) for e in entries if e.get("crossing_root_window_lo") is not None]
    crossing_his = [float(e["crossing_root_window_hi"]) for e in entries if e.get("crossing_root_window_hi") is not None]
    band_los = [float(e["hyperbolic_band_lo"]) for e in entries if e.get("hyperbolic_band_lo") is not None]
    band_his = [float(e["hyperbolic_band_hi"]) for e in entries if e.get("hyperbolic_band_hi") is not None]
    crossing_centers = [float(e["crossing_center"]) for e in entries if e.get("crossing_center") is not None]

    successful_crossings = len(crossing_los)
    successful_bands = len(band_los)
    family_label = str(theorem_iv_certificate.get("family_label", "standard-sine"))
    rho = float(theorem_iv_certificate.get("rho", golden_inverse()))
    theorem_iv_status = str(theorem_iv_certificate.get("theorem_status", "unknown"))
    contradiction_certified = bool(theorem_iv_certificate.get("nonexistence_contradiction_certified", False))

    ladder = {
        "approximants": entries,
        "successful_crossing_count": successful_crossings,
        "successful_band_count": successful_bands,
        "best_crossing_lower_bound": None if upper_lo is None else float(upper_lo),
        "best_crossing_upper_bound": None if upper_hi is None else float(upper_hi),
        "crossing_union_lo": None if not crossing_los else float(min(crossing_los)),
        "crossing_union_hi": None if not crossing_his else float(max(crossing_his)),
        "crossing_union_width": None if not crossing_los or not crossing_his else float(max(crossing_his) - min(crossing_los)),
        "crossing_intersection_lo": None if upper_lo is None else float(upper_lo),
        "crossing_intersection_hi": None if upper_hi is None else float(upper_hi),
        "crossing_intersection_width": None if upper_w is None else float(upper_w),
        "crossing_center_median": None if not crossing_centers else float(sorted(crossing_centers)[len(crossing_centers) // 2]),
        "earliest_band_lo": None if barrier_lo is None else float(barrier_lo),
        "latest_band_hi": None if barrier_hi is None else float(barrier_hi),
        "band_union_width": None if barrier_lo is None or barrier_hi is None else float(float(barrier_hi) - float(barrier_lo)),
        "ladder_quality": "strong" if contradiction_certified and theorem_iv_status.endswith("-strong") else "moderate",
        "notes": (
            "Inherited directly from theorem-IV shift-cache artifacts so the theorem-V transport stack can reuse the already certified upper-side ladder."
        ),
    }

    refined = {
        "best_refined_crossing_lower_bound": None if upper_lo is None else float(upper_lo),
        "best_refined_crossing_upper_bound": None if upper_hi is None else float(upper_hi),
        "best_refined_crossing_width": None if upper_w is None else float(upper_w),
        "selected_cluster_index": 0,
        "selected_cluster_member_qs": [int(x) for x in (stable_tail_qs or [e.get("q") for e in entries if e.get("q") is not None])],
        "refinement_status": "theorem-iv-inherited-upper-seed",
    }

    asymptotic_audit = {
        "audited_upper_lo": None if upper_lo is None else float(upper_lo),
        "audited_upper_hi": None if upper_hi is None else float(upper_hi),
        "audited_upper_width": None if upper_w is None else float(upper_w),
        "audited_upper_source_threshold": None if stable_tail_start_q is None else int(stable_tail_start_q),
        "stable_tail_q_threshold": None if stable_tail_start_q is None else int(stable_tail_start_q),
        "status": "asymptotically-stable-upper-ladder" if contradiction_certified and theorem_iv_status.endswith("-strong") else "theorem-iv-inherited-upper-ladder",
        "notes": "Asymptotic upper ladder witness inherited from the final Theorem-IV bridge rather than recomputed.",
    }

    if contradiction_certified and theorem_iv_status.endswith("-strong"):
        theorem_status = "golden-supercritical-obstruction-strong"
    elif upper_lo is not None and upper_hi is not None:
        theorem_status = "golden-supercritical-obstruction-moderate"
    else:
        theorem_status = "golden-supercritical-obstruction-weak"

    crossing_center = float(0.5 * (float(upper_lo) + float(upper_hi))) if upper_lo is not None and upper_hi is not None else float(crossing_centers[-1] if crossing_centers else 0.0)
    crossing_half_width = float(0.5 * float(upper_w)) if upper_w is not None else 0.0
    band_offset = float(barrier_lo - crossing_center) if barrier_lo is not None else 0.0
    band_width = float(barrier_hi - barrier_lo) if barrier_lo is not None and barrier_hi is not None else 0.0

    notes = (
        "Theorem-V upper seed inherited from finalized Theorem-IV artifacts. "
        f"Selected shift-cache report: {report_path.name} (realized shift {realized_shift:+.6g}). "
        "The ladder entries, including the transported tail rows, are reused directly so the transport stack does not rebuild a weaker legacy upper ladder. "
        f"Theorem-IV status: {theorem_iv_status}."
    )
    if stable_tail_qs:
        notes += f" Reused certified tail denominators: {stable_tail_qs}."
    if contradiction_summary.get("tail_stability_certified") is not None:
        notes += f" Tail stability certified: {bool(contradiction_summary.get('tail_stability_certified'))}."

    return TheoremVInheritedUpperSeedCertificate(
        rho=rho,
        family_label=family_label,
        target_residue=float(target_residue),
        crossing_center=crossing_center,
        crossing_half_width=float(crossing_half_width),
        band_offset=float(band_offset),
        band_width=float(band_width),
        generated_convergents=_generated_convergents(entries, rho),
        ladder=ladder,
        refined=refined,
        asymptotic_audit=asymptotic_audit,
        selected_upper_source="theorem-iv-final-object",
        selected_upper_lo=None if upper_lo is None else float(upper_lo),
        selected_upper_hi=None if upper_hi is None else float(upper_hi),
        selected_upper_width=None if upper_w is None else float(upper_w),
        earliest_hyperbolic_band_lo=None if barrier_lo is None else float(barrier_lo),
        latest_hyperbolic_band_hi=None if barrier_hi is None else float(barrier_hi),
        successful_crossing_count=int(successful_crossings),
        successful_band_count=int(successful_bands),
        theorem_status=theorem_status,
        notes=notes,
    )


__all__ = [
    "TheoremVInheritedUpperSeedCertificate",
    "build_golden_supercritical_obstruction_certificate_from_theorem_iv",
]

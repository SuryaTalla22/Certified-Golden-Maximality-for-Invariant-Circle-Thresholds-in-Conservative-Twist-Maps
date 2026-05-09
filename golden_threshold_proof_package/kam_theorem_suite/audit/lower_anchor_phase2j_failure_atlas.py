from __future__ import annotations

"""Phase-2J failure atlas for lower-anchor analytic rescue.

The Phase-2I result made the problem precise: the full lower-anchor K-range is
covered by artifacts, but eight later rows have negative analytic radii margins.
This module converts that state into a local rescue plan.  It reads the merged
candidate, recomputes every margin from raw Y/Z/T/r fields, classifies dominant
failure terms, assigns old-solver-style adaptive profiles, and emits JSON/CSV
and shell scripts for targeted reruns.
"""

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence
import csv
import json
import math
import shlex

from .lower_anchor_phase2j_rescue_profiles import (
    Phase2JRescueProfile,
    build_profile_for_failure,
    subdivide_segment,
)


@dataclass(frozen=True)
class Phase2JFailureRow:
    segment_id: str
    K_lo: float
    K_hi: float
    K_mid: float
    theorem_ready: bool
    certified: bool
    closure_level: str
    N: int
    sigma: float
    residual_Y: float
    linear_defect_Z: float
    linear_term_Zr: float
    tail_bound_T: float
    radius_r: float
    recomputed_margin: float
    stored_margin: float | None
    margin_mismatch: bool
    small_divisor_min: float | None
    small_divisor_inverse_bound: float | None
    failure_reasons: tuple[str, ...]
    dominant_failure_term: str
    failure_type: str
    suggested_rescue: str
    profile: Phase2JRescueProfile

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["failure_reasons"] = list(self.failure_reasons)
        data["profile"] = self.profile.to_dict()
        return data


@dataclass(frozen=True)
class Phase2JRescueVariant:
    variant_id: str
    parent_segment_id: str
    rescue_segment_id: str
    K_lo: float
    K_hi: float
    K_mid: float
    profile_name: str
    n_values: tuple[int, ...]
    oversample_factor: int
    sigma_cap: float
    max_wall_seconds: float
    candidate_name: str
    command: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["n_values"] = list(self.n_values)
        data["command"] = list(self.command)
        return data


@dataclass(frozen=True)
class Phase2JFailureAtlas:
    schema: str
    candidate_path: str
    strict_report_path: str | None
    total_segment_count: int
    failed_segment_count: int
    theorem_ready_count: int
    min_margin: float | None
    failed_rows: tuple[Phase2JFailureRow, ...]
    rescue_variants: tuple[Phase2JRescueVariant, ...]
    recommendations: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "candidate_path": self.candidate_path,
            "strict_report_path": self.strict_report_path,
            "total_segment_count": self.total_segment_count,
            "failed_segment_count": self.failed_segment_count,
            "theorem_ready_count": self.theorem_ready_count,
            "min_margin": self.min_margin,
            "failed_rows": [r.to_dict() for r in self.failed_rows],
            "rescue_variants": [v.to_dict() for v in self.rescue_variants],
            "recommendations": list(self.recommendations),
        }


def load_json(path: str | Path) -> dict[str, Any]:
    data = json.loads(Path(path).read_text())
    if not isinstance(data, dict):
        raise ValueError(f"expected JSON object at {path}")
    return data


def candidate_rows(candidate: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows = candidate.get("anchor_segments", candidate.get("segments", candidate.get("candidate_segments", [])))
    if not isinstance(rows, list):
        return []
    return [dict(row) for row in rows if isinstance(row, Mapping)]


def _f(row: Mapping[str, Any], key: str, default: float = 0.0) -> float:
    try:
        out = float(row.get(key, default))
    except Exception:
        return float(default)
    return out if math.isfinite(out) else float(default)


def recompute_terms(row: Mapping[str, Any]) -> tuple[float, float, float, float, float, float]:
    y = _f(row, "residual_Y")
    z = _f(row, "linear_defect_Z")
    t = _f(row, "tail_bound_T")
    r = _f(row, "radius_r")
    zr = z * r
    margin = r - (y + zr + t)
    return y, z, zr, t, r, margin


def _stored_margin(row: Mapping[str, Any]) -> float | None:
    if row.get("radii_margin") is None:
        return None
    try:
        out = float(row.get("radii_margin"))
    except Exception:
        return None
    return out if math.isfinite(out) else None


def classify_failure(row: Mapping[str, Any]) -> tuple[str, str, str]:
    y, z, zr, t, r, margin = recompute_terms(row)
    terms = {"residual_Y": y, "linear_defect_Zr": zr, "tail_bound_T": t}
    dominant = max(terms, key=lambda key: terms[key] if math.isfinite(terms[key]) else -math.inf)
    reasons = {str(x) for x in (row.get("failure_reasons", []) or [])}
    if r <= 0.0:
        ftype = "radius_failure"
        rescue = "rerun with local radius retry ladder and validated finite-dimensional solve"
    elif not row.get("certified", False):
        ftype = "analytic_margin_failure"
        rescue = "rerun with predictive high-precision refinement, K-bisection, and profile-specific N/sigma/oversampling sweeps"
    elif row.get("finite_dimensional_only", False):
        ftype = "finite_only_failure"
        rescue = "rerun with Phase-2E direct modewise radii ledger enabled"
    elif margin <= 0.0:
        ftype = "analytic_margin_failure"
        rescue = "bisect K interval and rerun dominant-term-specific profile"
    elif "modewise_residual_coefficients_unavailable" in reasons:
        ftype = "payload_missing_modewise_terms"
        rescue = "rerun with source_validation samples exported"
    else:
        ftype = "metadata_or_strict_ingestion_failure"
        rescue = "inspect theorem_facing/diagnostic flags and strict-ingestion metadata"
    if dominant == "tail_bound_T":
        rescue += "; tail dominates, prioritize larger N and smaller sigma caps"
    elif dominant == "residual_Y":
        rescue += "; residual dominates, prioritize predictive refinement and higher N"
    elif dominant == "linear_defect_Zr":
        rescue += "; linear term dominates, prioritize oversampling and radius profiling"
    return dominant, ftype, rescue


def build_failure_row(row: Mapping[str, Any]) -> Phase2JFailureRow:
    y, z, zr, t, r, margin = recompute_terms(row)
    stored = _stored_margin(row)
    dominant, ftype, rescue = classify_failure(row)
    profile = build_profile_for_failure({**dict(row), "dominant_failure_term": dominant}, dominant_failure_term=dominant)
    return Phase2JFailureRow(
        segment_id=str(row.get("segment_id", "unknown_segment")),
        K_lo=_f(row, "K_lo"),
        K_hi=_f(row, "K_hi"),
        K_mid=_f(row, "K_mid", 0.5 * (_f(row, "K_lo") + _f(row, "K_hi"))),
        theorem_ready=bool(row.get("theorem_ready", False)),
        certified=bool(row.get("certified", False)),
        closure_level=str(row.get("closure_level", "")),
        N=int(_f(row, "N", 0.0)),
        sigma=_f(row, "sigma"),
        residual_Y=float(y),
        linear_defect_Z=float(z),
        linear_term_Zr=float(zr),
        tail_bound_T=float(t),
        radius_r=float(r),
        recomputed_margin=float(margin),
        stored_margin=stored,
        margin_mismatch=bool(stored is not None and not math.isclose(stored, margin, rel_tol=1e-10, abs_tol=1e-15)),
        small_divisor_min=(None if row.get("small_divisor_min") is None else _f(row, "small_divisor_min")),
        small_divisor_inverse_bound=(None if row.get("small_divisor_inverse_bound") is None else _f(row, "small_divisor_inverse_bound")),
        failure_reasons=tuple(str(x) for x in (row.get("failure_reasons", []) or [])),
        dominant_failure_term=dominant,
        failure_type=ftype,
        suggested_rescue=rescue,
        profile=profile,
    )


def row_is_failed(row: Mapping[str, Any]) -> bool:
    _, _, _, _, _, margin = recompute_terms(row)
    return bool(
        not row.get("theorem_ready", False)
        or not row.get("certified", False)
        or bool(row.get("finite_dimensional_only", False))
        or str(row.get("closure_level", "")) != "analytic_theorem_closure"
        or margin <= 0.0
    )


def _n_values_csv(values: Sequence[int]) -> str:
    return ",".join(str(int(x)) for x in values)


def build_rescue_variants(failed_rows: Sequence[Phase2JFailureRow], *, out_dir: str = "artifacts/proof_audit/lower_corridor/phase2j_rescue", table_dir: str = "tables/proof_audit/lower_corridor/phase2j_rescue", python_executable: str = "python", no_site: bool = False) -> list[Phase2JRescueVariant]:
    variants: list[Phase2JRescueVariant] = []
    for failure in failed_rows:
        for sub in subdivide_segment(failure.to_dict(), failure.profile):
            for overs in failure.profile.oversample_factors:
                for sigma in failure.profile.sigma_caps:
                    variant_id = f"{sub['segment_id']}_os{int(overs)}_sg{str(sigma).replace('.', 'p')}"
                    candidate_name = f"{variant_id}_candidate.json"
                    cmd = [str(python_executable)]
                    if no_site:
                        cmd.append("-S")
                    cmd.extend([
                        "scripts/audit/run_lower_anchor_phase2g_segment.py",
                        "--segment-id", str(sub["segment_id"]),
                        "--K-lo", repr(float(sub["K_lo"])),
                        "--K-hi", repr(float(sub["K_hi"])),
                        "--K-mid", repr(float(sub["K_mid"])),
                        "--N-values", _n_values_csv(failure.profile.n_values),
                        "--oversample-factor", str(int(overs)),
                        "--sigma-cap", repr(float(sigma)),
                        "--max-wall-seconds", repr(float(failure.profile.max_wall_seconds)),
                        "--out-dir", out_dir,
                        "--table-dir", table_dir,
                        "--candidate-name", candidate_name,
                    ])
                    variants.append(Phase2JRescueVariant(
                        variant_id=variant_id,
                        parent_segment_id=failure.segment_id,
                        rescue_segment_id=str(sub["segment_id"]),
                        K_lo=float(sub["K_lo"]),
                        K_hi=float(sub["K_hi"]),
                        K_mid=float(sub["K_mid"]),
                        profile_name=failure.profile.name,
                        n_values=failure.profile.n_values,
                        oversample_factor=int(overs),
                        sigma_cap=float(sigma),
                        max_wall_seconds=float(failure.profile.max_wall_seconds),
                        candidate_name=candidate_name,
                        command=tuple(cmd),
                    ))
    return variants


def build_failure_atlas(candidate_path: str | Path, *, strict_report_path: str | Path | None = None, max_variants_per_parent: int | None = None, python_executable: str = "python", no_site: bool = False) -> Phase2JFailureAtlas:
    cand_path = Path(candidate_path)
    candidate = load_json(cand_path)
    rows = candidate_rows(candidate)
    failed = [build_failure_row(row) for row in rows if row_is_failed(row)]
    ready_count = len(rows) - len(failed)
    variants = build_rescue_variants(failed, python_executable=python_executable, no_site=no_site)
    if max_variants_per_parent is not None:
        limited: list[Phase2JRescueVariant] = []
        counts: dict[str, int] = {}
        for v in variants:
            n = counts.get(v.parent_segment_id, 0)
            if n < int(max_variants_per_parent):
                limited.append(v)
                counts[v.parent_segment_id] = n + 1
        variants = limited
    margins = [recompute_terms(row)[-1] for row in rows]
    recommendations = [
        "Run Phase-2J rescue variants only for failed rows; do not rerun already theorem-ready rows.",
        "Prefer execution in a real theorem environment with genuine mpmath/numpy, not the lightweight fallback path.",
        "After rescue variants are generated, select the best theorem-ready subsegments, merge with segments 000--001, and rerun strict Phase-2B ingestion.",
        "Do not weaken the Phase-2B strict gate; negative margins must trigger smaller K segments or stronger analytic profiles.",
    ]
    return Phase2JFailureAtlas(
        schema="phase2j_lower_anchor_failure_atlas_v1",
        candidate_path=cand_path.as_posix(),
        strict_report_path=None if strict_report_path is None else Path(strict_report_path).as_posix(),
        total_segment_count=len(rows),
        failed_segment_count=len(failed),
        theorem_ready_count=ready_count,
        min_margin=(None if not margins else float(min(margins))),
        failed_rows=tuple(failed),
        rescue_variants=tuple(variants),
        recommendations=tuple(recommendations),
    )


def write_failure_atlas_outputs(atlas: Phase2JFailureAtlas, *, out_json: str | Path, out_csv: str | Path, script_out: str | Path, dry_run_script_out: str | Path | None = None) -> dict[str, Any]:
    out_json = Path(out_json); out_csv = Path(out_csv); script_out = Path(script_out)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    script_out.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(atlas.to_dict(), indent=2, sort_keys=True) + "\n")
    fields = [
        "segment_id", "K_lo", "K_hi", "K_mid", "N", "sigma", "residual_Y", "linear_term_Zr", "tail_bound_T", "radius_r", "recomputed_margin", "dominant_failure_term", "failure_type", "profile_name", "suggested_rescue",
    ]
    with out_csv.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for row in atlas.failed_rows:
            d = row.to_dict()
            d["profile_name"] = row.profile.name
            writer.writerow({k: d.get(k) for k in fields})

    lines = ["#!/usr/bin/env bash", "set -euo pipefail", "export PYTHONPATH=\"$(pwd):${PYTHONPATH:-}\"", "", "# AUTO-GENERATED Phase-2J adaptive rescue script."]
    for variant in atlas.rescue_variants:
        lines.append(" ".join(shlex.quote(x) for x in variant.command))
    script_out.write_text("\n".join(lines) + "\n")
    script_out.chmod(0o755)
    dry_path = None
    if dry_run_script_out is not None:
        dry_path = Path(dry_run_script_out)
        dry_path.parent.mkdir(parents=True, exist_ok=True)
        dry_lines = ["#!/usr/bin/env bash", "set -euo pipefail", "export PYTHONPATH=\"$(pwd):${PYTHONPATH:-}\"", "", "# AUTO-GENERATED dry-run Phase-2J rescue script."]
        for variant in atlas.rescue_variants:
            cmd = list(variant.command) + ["--dry-run"]
            dry_lines.append(" ".join(shlex.quote(x) for x in cmd))
        dry_path.write_text("\n".join(dry_lines) + "\n")
        dry_path.chmod(0o755)
    return {
        "atlas_path": out_json.as_posix(),
        "csv_path": out_csv.as_posix(),
        "script_path": script_out.as_posix(),
        "dry_run_script_path": None if dry_path is None else dry_path.as_posix(),
        "failed_segment_count": atlas.failed_segment_count,
        "rescue_variant_count": len(atlas.rescue_variants),
        "min_margin": atlas.min_margin,
    }


__all__ = [
    "Phase2JFailureAtlas",
    "Phase2JFailureRow",
    "Phase2JRescueVariant",
    "build_failure_atlas",
    "build_failure_row",
    "build_rescue_variants",
    "candidate_rows",
    "classify_failure",
    "recompute_terms",
    "row_is_failed",
    "write_failure_atlas_outputs",
]

"""Phase 2Q collar-chain assembler for Theorem III lower-anchor closure.

This module is deliberately JSON-first and dependency-light.  It consumes
Phase-2P theorem-ready segment candidates, verifies that every segment is
promotable, verifies collar interval adjacency/coverage, and exports a single
proof-carrying chain audit artifact.

The module does not rerun Newton, Phase 2O, or Phase 2P.  Its only job is to
make the collar chain theorem-facing by checking that every segment already has
its own local theorem-facing certificate and that the segment intervals form a
continuous chain.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import csv
import glob
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

SCHEMA_VERSION = "phase2q_collar_chain_audit_v1"
CANDIDATE_SCHEMA_VERSION = "phase2q_collar_chain_candidate_v1"


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_json(path: str | Path) -> dict[str, Any]:
    p = Path(path)
    return json.loads(p.read_text())


def write_json(path: str | Path, data: Mapping[str, Any]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2, sort_keys=False) + "\n")


def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _as_float(value: Any, *, field_name: str) -> float:
    if value is None:
        raise ValueError(f"missing numeric field {field_name}")
    try:
        x = float(value)
    except Exception as exc:  # pragma: no cover - defensive path
        raise ValueError(f"field {field_name} is not numeric: {value!r}") from exc
    if not math.isfinite(x):
        raise ValueError(f"field {field_name} is not finite: {value!r}")
    return x


def _get_first_segment(data: Mapping[str, Any]) -> Mapping[str, Any]:
    segs = data.get("anchor_segments")
    if isinstance(segs, list) and segs:
        first = segs[0]
        if isinstance(first, Mapping):
            return first
    return {}


def _get_selected_row(data: Mapping[str, Any]) -> Mapping[str, Any]:
    row = data.get("selected_phase2p_row")
    if isinstance(row, Mapping):
        return row
    seg = _get_first_segment(data)
    row = seg.get("phase2p_ledger") or seg.get("selected_phase2p_row")
    if isinstance(row, Mapping):
        return row
    return {}


def _path_to_default_segment_id(path: str | Path, data: Mapping[str, Any]) -> str:
    seg = _get_first_segment(data)
    row = _get_selected_row(data)
    for obj in (seg, row, data):
        value = obj.get("segment_id") if isinstance(obj, Mapping) else None
        if isinstance(value, str) and value:
            return value
    return Path(path).stem


def _extract_interval(data: Mapping[str, Any], path: str | Path) -> tuple[float, float, float | None]:
    seg = _get_first_segment(data)
    row = _get_selected_row(data)
    k_lo = seg.get("K_lo", row.get("K_lo"))
    k_hi = seg.get("K_hi", row.get("K_hi"))
    k_mid = seg.get("K_mid", row.get("K_mid"))
    return (
        _as_float(k_lo, field_name=f"{path}:K_lo"),
        _as_float(k_hi, field_name=f"{path}:K_hi"),
        None if k_mid is None else _as_float(k_mid, field_name=f"{path}:K_mid"),
    )


def _safe_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


@dataclass(frozen=True)
class Phase2QConfig:
    """Configuration for chain assembly.

    overlap_tolerance is a gap tolerance, not a required overlap.  Adjacent
    intervals pass if next.K_lo <= previous.K_hi + overlap_tolerance.
    minimum_overlap is optional; if positive, every adjacent pair must overlap
    by at least that amount.
    """

    expected_start: float | None = None
    expected_end: float | None = None
    expected_regime_i_hi: float | None = None
    final_anchor_hi: float | None = None
    overlap_tolerance: float = 1.0e-10
    minimum_overlap: float | None = None
    min_segment_margin: float = 0.0
    require_phase2p_closure: bool = True
    require_no_failure_fields: bool = True
    require_theorem_facing: bool = True
    require_promotion_allowed: bool = True
    allow_duplicate_intervals: bool = False
    strict: bool = True


@dataclass
class SegmentAudit:
    index: int
    path: str
    sha256: str
    segment_id: str
    K_lo: float
    K_hi: float
    K_mid: float | None
    width: float
    theorem_facing: bool
    promotion_allowed: bool
    closure_level: str | None
    theorem_ready: bool
    radii_margin: float | None
    tail_T: float | None
    allowable_tail_max: float | None
    tail_slack: float | None
    sigma: float | None
    tail_cutoff: int | None
    model_name: str | None
    failure_fields: list[Any] = field(default_factory=list)
    failure_reasons: list[Any] = field(default_factory=list)
    validation_failures: list[str] = field(default_factory=list)

    @property
    def interval_key(self) -> tuple[float, float]:
        return (self.K_lo, self.K_hi)

    @property
    def locally_valid(self) -> bool:
        return not self.validation_failures


@dataclass
class ChainAdjacency:
    left_segment_id: str
    right_segment_id: str
    left_K_hi: float
    right_K_lo: float
    overlap: float
    gap: float
    passed: bool
    failure_reason: str | None = None


@dataclass
class ChainAuditResult:
    schema: str
    status: str
    generated_at_utc: str
    theorem_facing: bool
    promotion_allowed: bool
    closure_level: str
    segment_count: int
    covered_K_lo: float | None
    covered_K_hi: float | None
    min_segment_margin: float | None
    min_tail_slack: float | None
    min_overlap: float | None
    final_anchor_reached: bool
    expected_start_satisfied: bool | None
    expected_end_satisfied: bool | None
    regime_i_handoff_satisfied: bool | None
    failure_fields: list[str]
    config: dict[str, Any]
    segments: list[dict[str, Any]]
    adjacency: list[dict[str, Any]]


def discover_candidate_paths(
    *,
    candidates: Sequence[str] | None = None,
    candidate_globs: Sequence[str] | None = None,
) -> list[str]:
    """Resolve explicit paths and glob patterns into a sorted unique path list."""
    paths: list[str] = []
    for item in candidates or []:
        if not item:
            continue
        # Allow comma-separated values in addition to repeated CLI flags.
        for token in str(item).split(","):
            token = token.strip()
            if token:
                paths.append(token)
    for pat in candidate_globs or []:
        if not pat:
            continue
        for token in str(pat).split(","):
            token = token.strip()
            if token:
                paths.extend(glob.glob(token))
    # Preserve deterministic order by path, while de-duplicating.
    seen: set[str] = set()
    out: list[str] = []
    for p in sorted(paths):
        if p not in seen:
            seen.add(p)
            out.append(p)
    return out


def load_segment_candidate(path: str | Path, cfg: Phase2QConfig) -> SegmentAudit:
    data = load_json(path)
    p = str(path)
    seg = _get_first_segment(data)
    row = _get_selected_row(data)
    k_lo, k_hi, k_mid = _extract_interval(data, p)
    if k_hi <= k_lo:
        width = float("nan")
    else:
        width = k_hi - k_lo

    failure_fields = _safe_list(data.get("failure_fields"))
    failure_reasons = _safe_list(row.get("failure_reasons") or seg.get("failure_reasons"))
    theorem_facing = bool(data.get("theorem_facing", False))
    promotion_allowed = bool(data.get("promotion_allowed", False))
    closure_level = data.get("closure_level")
    theorem_ready = bool(row.get("theorem_ready", seg.get("theorem_ready", False)))

    radii_margin = row.get("radii_margin", seg.get("radii_margin"))
    tail_T = row.get("tail_T", seg.get("tail_bound_T", seg.get("tail_T")))
    allowable_tail_max = row.get("allowable_tail_max", seg.get("allowable_tail_max"))
    sigma = row.get("sigma", seg.get("sigma"))
    tail_cutoff = row.get("tail_cutoff", seg.get("tail_cutoff"))
    model_name = row.get("model_name", seg.get("model_name"))

    rm = None if radii_margin is None else _as_float(radii_margin, field_name=f"{p}:radii_margin")
    tt = None if tail_T is None else _as_float(tail_T, field_name=f"{p}:tail_T")
    atm = None if allowable_tail_max is None else _as_float(allowable_tail_max, field_name=f"{p}:allowable_tail_max")
    tail_slack = None if tt is None or atm is None else atm - tt
    sig = None if sigma is None else _as_float(sigma, field_name=f"{p}:sigma")
    tc = None if tail_cutoff is None else int(tail_cutoff)

    failures: list[str] = []
    if not math.isfinite(width) or width <= 0:
        failures.append("nonpositive_segment_width")
    if cfg.require_theorem_facing and not theorem_facing:
        failures.append("candidate_not_theorem_facing")
    if cfg.require_promotion_allowed and not promotion_allowed:
        failures.append("candidate_not_promotion_allowed")
    if cfg.require_phase2p_closure:
        if closure_level != "phase2p_modewise_tail_closure":
            failures.append("closure_level_not_phase2p_modewise_tail_closure")
        if not theorem_ready:
            failures.append("selected_phase2p_row_not_theorem_ready")
    if cfg.require_no_failure_fields and failure_fields:
        failures.append("candidate_failure_fields_nonempty")
    if failure_reasons:
        failures.append("selected_row_failure_reasons_nonempty")
    if rm is None:
        failures.append("missing_radii_margin")
    elif rm <= cfg.min_segment_margin:
        failures.append("radii_margin_not_strictly_above_minimum")
    if tt is None:
        failures.append("missing_tail_T")
    if atm is None:
        failures.append("missing_allowable_tail_max")
    if tt is not None and atm is not None and not (tt < atm):
        failures.append("tail_bound_not_below_allowable_tail_max")

    return SegmentAudit(
        index=-1,
        path=p,
        sha256=sha256_file(p),
        segment_id=_path_to_default_segment_id(p, data),
        K_lo=k_lo,
        K_hi=k_hi,
        K_mid=k_mid,
        width=width,
        theorem_facing=theorem_facing,
        promotion_allowed=promotion_allowed,
        closure_level=str(closure_level) if closure_level is not None else None,
        theorem_ready=theorem_ready,
        radii_margin=rm,
        tail_T=tt,
        allowable_tail_max=atm,
        tail_slack=tail_slack,
        sigma=sig,
        tail_cutoff=tc,
        model_name=str(model_name) if model_name is not None else None,
        failure_fields=failure_fields,
        failure_reasons=failure_reasons,
        validation_failures=failures,
    )


def sort_and_index_segments(segments: Sequence[SegmentAudit]) -> list[SegmentAudit]:
    sorted_segments = sorted(segments, key=lambda s: (s.K_lo, s.K_hi, s.path))
    out: list[SegmentAudit] = []
    for i, s in enumerate(sorted_segments):
        d = asdict(s)
        d["index"] = i
        out.append(SegmentAudit(**d))
    return out


def validate_adjacency(
    segments: Sequence[SegmentAudit],
    cfg: Phase2QConfig,
) -> list[ChainAdjacency]:
    rows: list[ChainAdjacency] = []
    for left, right in zip(segments, segments[1:]):
        overlap = left.K_hi - right.K_lo
        gap = max(0.0, right.K_lo - left.K_hi)
        passed = True
        reason = None
        if right.K_lo > left.K_hi + cfg.overlap_tolerance:
            passed = False
            reason = "positive_gap_between_adjacent_segments"
        if cfg.minimum_overlap is not None and overlap < cfg.minimum_overlap:
            passed = False
            reason = "overlap_below_required_minimum"
        rows.append(
            ChainAdjacency(
                left_segment_id=left.segment_id,
                right_segment_id=right.segment_id,
                left_K_hi=left.K_hi,
                right_K_lo=right.K_lo,
                overlap=overlap,
                gap=gap,
                passed=passed,
                failure_reason=reason,
            )
        )
    return rows


def validate_duplicate_intervals(
    segments: Sequence[SegmentAudit],
    cfg: Phase2QConfig,
) -> list[str]:
    if cfg.allow_duplicate_intervals:
        return []
    failures: list[str] = []
    seen: dict[tuple[float, float], str] = {}
    for s in segments:
        key = s.interval_key
        if key in seen:
            failures.append(f"duplicate_interval:{seen[key]}:{s.segment_id}")
        else:
            seen[key] = s.segment_id
    return failures


def assemble_phase2q_chain(
    candidate_paths: Sequence[str | Path],
    cfg: Phase2QConfig,
) -> ChainAuditResult:
    if not candidate_paths:
        return ChainAuditResult(
            schema=SCHEMA_VERSION,
            status="phase2q-chain-no-candidates",
            generated_at_utc=_now_iso(),
            theorem_facing=False,
            promotion_allowed=False,
            closure_level="phase2q_chain_not_closed",
            segment_count=0,
            covered_K_lo=None,
            covered_K_hi=None,
            min_segment_margin=None,
            min_tail_slack=None,
            min_overlap=None,
            final_anchor_reached=False,
            expected_start_satisfied=None,
            expected_end_satisfied=None,
            regime_i_handoff_satisfied=None,
            failure_fields=["no_candidate_paths_provided"],
            config=asdict(cfg),
            segments=[],
            adjacency=[],
        )

    loaded = [load_segment_candidate(p, cfg) for p in candidate_paths]
    segments = sort_and_index_segments(loaded)
    adjacency = validate_adjacency(segments, cfg)

    failures: list[str] = []
    failures.extend(validate_duplicate_intervals(segments, cfg))
    for s in segments:
        for f in s.validation_failures:
            failures.append(f"segment:{s.segment_id}:{f}")
    for a in adjacency:
        if not a.passed:
            failures.append(f"adjacency:{a.left_segment_id}->{a.right_segment_id}:{a.failure_reason}")

    covered_lo = segments[0].K_lo if segments else None
    covered_hi = max(s.K_hi for s in segments) if segments else None
    min_margin = min((s.radii_margin for s in segments if s.radii_margin is not None), default=None)
    min_tail_slack = min((s.tail_slack for s in segments if s.tail_slack is not None), default=None)
    min_overlap = min((a.overlap for a in adjacency), default=None)

    expected_start_satisfied: bool | None = None
    if cfg.expected_start is not None and covered_lo is not None:
        expected_start_satisfied = covered_lo <= cfg.expected_start + cfg.overlap_tolerance
        if not expected_start_satisfied:
            failures.append("expected_start_not_covered")

    expected_end_satisfied: bool | None = None
    if cfg.expected_end is not None and covered_hi is not None:
        expected_end_satisfied = covered_hi + cfg.overlap_tolerance >= cfg.expected_end
        if not expected_end_satisfied:
            failures.append("expected_end_not_reached")

    regime_i_handoff_satisfied: bool | None = None
    if cfg.expected_regime_i_hi is not None and segments:
        first = segments[0]
        # The first collar segment must touch or overlap the certified Regime-I end.
        regime_i_handoff_satisfied = first.K_lo <= cfg.expected_regime_i_hi + cfg.overlap_tolerance and first.K_hi + cfg.overlap_tolerance >= cfg.expected_regime_i_hi
        if not regime_i_handoff_satisfied:
            failures.append("regime_i_handoff_not_covered_by_first_segment")

    final_anchor_reached = False
    if cfg.final_anchor_hi is not None and covered_hi is not None:
        final_anchor_reached = covered_hi + cfg.overlap_tolerance >= cfg.final_anchor_hi
        if not final_anchor_reached:
            failures.append("final_anchor_hi_not_reached")
    elif cfg.expected_end is not None and covered_hi is not None:
        final_anchor_reached = covered_hi + cfg.overlap_tolerance >= cfg.expected_end

    all_local_valid = all(s.locally_valid for s in segments)
    all_adjacent = all(a.passed for a in adjacency)
    closed = bool(segments) and all_local_valid and all_adjacent and not failures
    status = "phase2q-chain-theorem-ready" if closed else "phase2q-chain-not-closed"

    return ChainAuditResult(
        schema=SCHEMA_VERSION,
        status=status,
        generated_at_utc=_now_iso(),
        theorem_facing=closed,
        promotion_allowed=closed,
        closure_level="phase2q_collar_chain_closure" if closed else "phase2q_chain_not_closed",
        segment_count=len(segments),
        covered_K_lo=covered_lo,
        covered_K_hi=covered_hi,
        min_segment_margin=min_margin,
        min_tail_slack=min_tail_slack,
        min_overlap=min_overlap,
        final_anchor_reached=final_anchor_reached,
        expected_start_satisfied=expected_start_satisfied,
        expected_end_satisfied=expected_end_satisfied,
        regime_i_handoff_satisfied=regime_i_handoff_satisfied,
        failure_fields=failures,
        config=asdict(cfg),
        segments=[asdict(s) for s in segments],
        adjacency=[asdict(a) for a in adjacency],
    )


def report_to_dict(result: ChainAuditResult) -> dict[str, Any]:
    return asdict(result)


def build_phase2q_candidate(result: ChainAuditResult) -> dict[str, Any]:
    closed = result.theorem_facing and result.promotion_allowed and not result.failure_fields
    return {
        "schema": CANDIDATE_SCHEMA_VERSION,
        "source": "Phase-2Q collar-chain assembler",
        "generated_at_utc": result.generated_at_utc,
        "theorem_layer": "III",
        "claim": "Phase-2P theorem-ready collar segments form a continuous lower-anchor collar chain",
        "theorem_facing": closed,
        "promotion_allowed": closed,
        "closure_level": "phase2q_collar_chain_closure" if closed else "phase2q_chain_not_closed",
        "failure_fields": [] if closed else list(result.failure_fields),
        "chain_summary": {
            "segment_count": result.segment_count,
            "covered_K_lo": result.covered_K_lo,
            "covered_K_hi": result.covered_K_hi,
            "min_segment_margin": result.min_segment_margin,
            "min_tail_slack": result.min_tail_slack,
            "min_overlap": result.min_overlap,
            "final_anchor_reached": result.final_anchor_reached,
            "expected_start_satisfied": result.expected_start_satisfied,
            "expected_end_satisfied": result.expected_end_satisfied,
            "regime_i_handoff_satisfied": result.regime_i_handoff_satisfied,
        },
        "derived_booleans": {
            "all_segments_theorem_facing": all(s.get("theorem_facing") for s in result.segments),
            "all_segments_promotion_allowed": all(s.get("promotion_allowed") for s in result.segments),
            "all_segments_phase2p_ready": all(s.get("theorem_ready") for s in result.segments),
            "all_segment_failure_fields_empty": all(not s.get("failure_fields") for s in result.segments),
            "all_selected_failure_reasons_empty": all(not s.get("failure_reasons") for s in result.segments),
            "all_adjacency_checks_passed": all(a.get("passed") for a in result.adjacency),
            "chain_theorem_ready": closed,
        },
        "segments": result.segments,
        "adjacency": result.adjacency,
        "config": result.config,
    }


def write_segment_csv(path: str | Path, result: ChainAuditResult) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "index",
        "segment_id",
        "K_lo",
        "K_hi",
        "width",
        "radii_margin",
        "tail_T",
        "allowable_tail_max",
        "tail_slack",
        "sigma",
        "tail_cutoff",
        "model_name",
        "theorem_facing",
        "promotion_allowed",
        "theorem_ready",
        "closure_level",
        "validation_failures",
        "path",
        "sha256",
    ]
    with p.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for s in result.segments:
            row = {k: s.get(k) for k in fields}
            row["validation_failures"] = ";".join(s.get("validation_failures") or [])
            writer.writerow(row)


def print_report_summary(result: ChainAuditResult) -> dict[str, Any]:
    return {
        "status": result.status,
        "theorem_facing": result.theorem_facing,
        "promotion_allowed": result.promotion_allowed,
        "closure_level": result.closure_level,
        "segment_count": result.segment_count,
        "covered_K_lo": result.covered_K_lo,
        "covered_K_hi": result.covered_K_hi,
        "min_segment_margin": result.min_segment_margin,
        "min_tail_slack": result.min_tail_slack,
        "min_overlap": result.min_overlap,
        "final_anchor_reached": result.final_anchor_reached,
        "expected_start_satisfied": result.expected_start_satisfied,
        "expected_end_satisfied": result.expected_end_satisfied,
        "regime_i_handoff_satisfied": result.regime_i_handoff_satisfied,
        "failure_fields": result.failure_fields,
    }

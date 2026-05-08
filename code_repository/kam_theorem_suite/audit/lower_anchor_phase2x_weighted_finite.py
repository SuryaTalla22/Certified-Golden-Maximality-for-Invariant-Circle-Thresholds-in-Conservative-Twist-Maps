from __future__ import annotations

"""Phase 2X utilities: failure autopsy and targeted finite-ledger rescue planning.

This module is intentionally conservative.  It does not declare a new theorem-
ready certificate from algebraic post-processing alone.  It ranks failed Phase
2P/2U/2V candidates, estimates which proof-budget component is limiting, and
constructs narrow rerun profiles for existing theorem-facing validators
(Phase 2N, 2O, and 2P).  Any promoted candidate must still be produced by the
existing fail-closed Phase 2P validator.
"""

from dataclasses import asdict, dataclass
from decimal import Decimal, getcontext
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence
import csv
import json
import math
import re

getcontext().prec = 80

THREAD_LIMIT_ENV = {
    "OMP_NUM_THREADS": "1",
    "MKL_NUM_THREADS": "1",
    "OPENBLAS_NUM_THREADS": "1",
    "VECLIB_MAXIMUM_THREADS": "1",
    "NUMEXPR_NUM_THREADS": "1",
    "BLIS_NUM_THREADS": "1",
}


@dataclass(frozen=True)
class FailedPieceRecord:
    index: int | None
    label: str | None
    segment_id: str | None
    path: str | None
    K_lo: float | None
    K_hi: float | None
    K_mid: float | None
    theorem_ready: bool
    theorem_facing: bool
    promotion_allowed: bool
    model_name: str | None
    sigma: float | None
    radius_r: float | None
    radius_multiplier: float | None
    finite_contraction_q: float | None
    tail_cutoff: int | None
    radii_margin: float | None
    tail_T: float | None
    allowable_tail_max: float | None
    tail_response_bound: float | None
    nonlinear_guard: float | None
    failure_reasons: tuple[str, ...]
    source_kind: str = "unknown"

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["failure_reasons"] = list(self.failure_reasons)
        return d


@dataclass(frozen=True)
class AutopsyRow:
    record: FailedPieceRecord
    gap_to_close: float | None
    tail_over_allowable_ratio: float | None
    nonlinear_fraction_of_tail: float | None
    q_room: float | None
    bucket: str
    recommended_rescue: str
    priority_score: float
    estimated_radius_multiplier_to_close: float | None

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["record"] = self.record.to_dict()
        return d


def dec(x: str | int | float | Decimal) -> Decimal:
    return x if isinstance(x, Decimal) else Decimal(str(x))


def fmt_dec(x: Decimal, places: int = 12) -> str:
    q = Decimal(1).scaleb(-places)
    y = x.quantize(q)
    s = format(y, "f")
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return s


def finite_float(x: Any, default: float | None = None) -> float | None:
    try:
        y = float(x)
    except Exception:
        return default
    return y if math.isfinite(y) else default


def finite_int(x: Any, default: int | None = None) -> int | None:
    y = finite_float(x)
    if y is None:
        return default
    return int(y)


def load_json(path: str | Path) -> dict[str, Any]:
    p = Path(path)
    data = json.loads(p.read_text())
    if not isinstance(data, Mapping):
        raise ValueError(f"expected JSON object in {path}")
    return dict(data)


def write_json(path: str | Path, data: Any) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    tmp.replace(p)


def write_csv(path: str | Path, rows: Sequence[Mapping[str, Any]], fieldnames: Sequence[str]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(fieldnames), extrasaction="ignore")
        w.writeheader()
        for row in rows:
            w.writerow(row)


def parse_float_csv(raw: str | Sequence[float], *, positive: bool = False) -> tuple[float, ...]:
    if isinstance(raw, str):
        vals = [x.strip() for x in raw.split(",") if x.strip()]
    else:
        vals = list(raw)
    out: list[float] = []
    for v in vals:
        x = finite_float(v)
        if x is None:
            continue
        if positive and x <= 0.0:
            continue
        if x not in out:
            out.append(float(x))
    return tuple(out)


def parse_int_csv(raw: str | Sequence[int], *, positive: bool = True) -> tuple[int, ...]:
    if isinstance(raw, str):
        vals = [x.strip() for x in raw.split(",") if x.strip()]
    else:
        vals = list(raw)
    out: list[int] = []
    for v in vals:
        x = finite_int(v)
        if x is None:
            continue
        if positive and x <= 0:
            continue
        if x not in out:
            out.append(int(x))
    return tuple(out)


def _as_map(x: Any) -> Mapping[str, Any]:
    return x if isinstance(x, Mapping) else {}


def _failure_tuple(x: Any) -> tuple[str, ...]:
    if isinstance(x, str):
        return (x,) if x else tuple()
    if isinstance(x, Sequence) and not isinstance(x, (str, bytes)):
        return tuple(str(y) for y in x if str(y))
    return tuple()


def infer_piece_index(path_or_label: str | None) -> int | None:
    if not path_or_label:
        return None
    m = re.search(r"p(\d{4})", str(path_or_label))
    if m:
        return int(m.group(1))
    m = re.search(r"piece[_-]?(\d+)", str(path_or_label))
    if m:
        return int(m.group(1))
    return None


def record_from_candidate(path: str | Path, *, source_kind: str = "candidate") -> FailedPieceRecord:
    p = Path(path)
    data = load_json(p)
    row = _as_map(data.get("selected_phase2p_row"))
    if not row:
        row = _as_map(data.get("best_theorem_eligible"))
    seg = _as_map((data.get("anchor_segments") or [{}])[0] if isinstance(data.get("anchor_segments"), list) else {})
    if not seg:
        seg = _as_map(data.get("input_summary"))
    label = str(data.get("label") or data.get("segment_id") or row.get("segment_id") or p.stem)
    idx = infer_piece_index(str(p)) or infer_piece_index(label)
    k_lo = finite_float(seg.get("K_lo"), finite_float(row.get("K_lo")))
    k_hi = finite_float(seg.get("K_hi"), finite_float(row.get("K_hi")))
    k_mid = finite_float(seg.get("K_mid"), None)
    if k_mid is None and k_lo is not None and k_hi is not None:
        k_mid = 0.5 * (k_lo + k_hi)
    return FailedPieceRecord(
        index=idx,
        label=label,
        segment_id=str(data.get("segment_id") or row.get("segment_id") or label),
        path=str(p),
        K_lo=k_lo,
        K_hi=k_hi,
        K_mid=k_mid,
        theorem_ready=bool(row.get("theorem_ready")),
        theorem_facing=bool(data.get("theorem_facing")),
        promotion_allowed=bool(data.get("promotion_allowed")),
        model_name=None if row.get("model_name") is None else str(row.get("model_name")),
        sigma=finite_float(row.get("sigma")),
        radius_r=finite_float(row.get("radius_r")),
        radius_multiplier=finite_float(row.get("radius_multiplier")),
        finite_contraction_q=finite_float(row.get("finite_contraction_q")),
        tail_cutoff=finite_int(row.get("tail_cutoff")),
        radii_margin=finite_float(row.get("radii_margin")),
        tail_T=finite_float(row.get("tail_T")),
        allowable_tail_max=finite_float(row.get("allowable_tail_max")),
        tail_response_bound=finite_float(row.get("tail_response_bound")),
        nonlinear_guard=finite_float(row.get("nonlinear_guard")),
        failure_reasons=_failure_tuple(row.get("failure_reasons") or data.get("failure_fields")),
        source_kind=source_kind,
    )


def record_from_summary_row(row: Mapping[str, Any], *, source_kind: str = "summary") -> FailedPieceRecord:
    path = row.get("path")
    idx = finite_int(row.get("index"), infer_piece_index(str(path)) or infer_piece_index(str(row.get("label"))))
    k_lo = finite_float(row.get("K_lo"))
    k_hi = finite_float(row.get("K_hi"))
    k_mid = finite_float(row.get("K_mid"))
    if k_mid is None and k_lo is not None and k_hi is not None:
        k_mid = 0.5 * (k_lo + k_hi)
    return FailedPieceRecord(
        index=idx,
        label=None if row.get("label") is None else str(row.get("label")),
        segment_id=None if row.get("segment_id") is None else str(row.get("segment_id")),
        path=None if path is None else str(path),
        K_lo=k_lo,
        K_hi=k_hi,
        K_mid=k_mid,
        theorem_ready=bool(row.get("theorem_ready")),
        theorem_facing=bool(row.get("theorem_facing")),
        promotion_allowed=bool(row.get("promotion_allowed")),
        model_name=None if row.get("model_name") is None else str(row.get("model_name")),
        sigma=finite_float(row.get("sigma")),
        radius_r=finite_float(row.get("radius_r")),
        radius_multiplier=finite_float(row.get("radius_multiplier")),
        finite_contraction_q=finite_float(row.get("finite_contraction_q")),
        tail_cutoff=finite_int(row.get("tail_cutoff")),
        radii_margin=finite_float(row.get("radii_margin")),
        tail_T=finite_float(row.get("tail_T")),
        allowable_tail_max=finite_float(row.get("allowable_tail_max")),
        tail_response_bound=finite_float(row.get("tail_response_bound")),
        nonlinear_guard=finite_float(row.get("nonlinear_guard")),
        failure_reasons=_failure_tuple(row.get("failure_reasons") or row.get("failure_fields")),
        source_kind=source_kind,
    )


def records_from_summary(summary_path: str | Path) -> list[FailedPieceRecord]:
    data = load_json(summary_path)
    out: list[FailedPieceRecord] = []
    for r in data.get("best_failed_rows", []) or []:
        if isinstance(r, Mapping):
            out.append(record_from_summary_row(r, source_kind="best_failed_rows"))
    # Include selected rows from per-piece results if present.
    for r in data.get("results", []) or []:
        if not isinstance(r, Mapping):
            continue
        sel = r.get("selected")
        if isinstance(sel, Mapping):
            merged = dict(sel)
            for k in ("index", "piece_label", "segment_id", "K_lo", "K_hi", "K_mid"):
                if k in r and k not in merged:
                    merged[k] = r[k]
            if "label" not in merged and r.get("piece_label"):
                merged["label"] = r.get("piece_label")
            out.append(record_from_summary_row(merged, source_kind="results.selected"))
        cand = r.get("phase2p_candidate")
        if cand and Path(str(cand)).exists():
            try:
                out.append(record_from_candidate(str(cand), source_kind="results.candidate"))
            except Exception:
                pass
    # Dedupe by path or interval.
    seen: set[tuple[Any, ...]] = set()
    deduped: list[FailedPieceRecord] = []
    for r in out:
        key = (r.path, r.index, r.K_lo, r.K_hi)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(r)
    return deduped


def autopsy_record(record: FailedPieceRecord) -> AutopsyRow:
    margin = record.radii_margin
    tail = record.tail_T
    allowable = record.allowable_tail_max
    q = record.finite_contraction_q
    nonlin = record.nonlinear_guard
    tail_resp = record.tail_response_bound
    gap = None if margin is None else max(0.0, -margin)
    ratio = None
    if tail is not None and allowable is not None and allowable > 0.0:
        ratio = tail / allowable
    nonlin_frac = None
    if nonlin is not None and tail is not None and tail > 0.0:
        nonlin_frac = nonlin / tail
    q_room = None if q is None else 1.0 - q

    failures = set(record.failure_reasons)
    if record.theorem_ready:
        bucket = "already_closed"
        rec = "no_action"
        score = -1.0
    elif q is not None and q >= 1.0:
        bucket = "q_over_one"
        rec = "better_finite_inverse_or_n_lift"
        score = 1000.0 + (gap or 1.0)
    elif q is not None and q > 0.97:
        bucket = "q_boundary_near_miss"
        rec = "weighted_norm_or_targeted_n_lift"
        score = 100.0 + (gap or 1.0)
    elif gap is not None and gap < 5.0e-8:
        bucket = "safe_q_small_gap" if (q is None or q < 0.95) else "near_q_small_gap"
        rec = "radius_shell_plus_weighted_nonlinear_guard"
        score = gap
    elif "analytic_radii_margin_not_safely_positive" in failures:
        bucket = "tail_or_guard_dominated"
        rec = "coefficient_guard_or_n_lift"
        score = 10.0 + (gap or 1.0)
    else:
        bucket = "other"
        rec = "inspect_manually"
        score = 1e6

    estimated = None
    if tail is not None and allowable is not None and allowable > 0.0:
        estimated = max(1.0, tail / allowable)
    return AutopsyRow(
        record=record,
        gap_to_close=gap,
        tail_over_allowable_ratio=ratio,
        nonlinear_fraction_of_tail=nonlin_frac,
        q_room=q_room,
        bucket=bucket,
        recommended_rescue=rec,
        priority_score=float(score),
        estimated_radius_multiplier_to_close=estimated,
    )


def autopsy_records(records: Iterable[FailedPieceRecord]) -> list[AutopsyRow]:
    rows = [autopsy_record(r) for r in records]
    rows.sort(key=lambda x: (x.record.theorem_ready, x.priority_score, x.gap_to_close if x.gap_to_close is not None else 1e99))
    return rows


def row_to_csv_flat(a: AutopsyRow) -> dict[str, Any]:
    r = a.record
    return {
        "index": r.index,
        "label": r.label,
        "segment_id": r.segment_id,
        "K_lo": r.K_lo,
        "K_hi": r.K_hi,
        "path": r.path,
        "bucket": a.bucket,
        "recommended_rescue": a.recommended_rescue,
        "priority_score": a.priority_score,
        "gap_to_close": a.gap_to_close,
        "tail_over_allowable_ratio": a.tail_over_allowable_ratio,
        "q_room": a.q_room,
        "theorem_ready": r.theorem_ready,
        "radii_margin": r.radii_margin,
        "tail_T": r.tail_T,
        "allowable_tail_max": r.allowable_tail_max,
        "tail_response_bound": r.tail_response_bound,
        "nonlinear_guard": r.nonlinear_guard,
        "finite_contraction_q": r.finite_contraction_q,
        "radius_r": r.radius_r,
        "radius_multiplier": r.radius_multiplier,
        "sigma": r.sigma,
        "tail_cutoff": r.tail_cutoff,
        "model_name": r.model_name,
        "failure_reasons": ";".join(r.failure_reasons),
        "source_kind": r.source_kind,
    }


AUTOPSY_CSV_FIELDS = [
    "index", "label", "segment_id", "K_lo", "K_hi", "path", "bucket", "recommended_rescue",
    "priority_score", "gap_to_close", "tail_over_allowable_ratio", "q_room", "theorem_ready",
    "radii_margin", "tail_T", "allowable_tail_max", "tail_response_bound", "nonlinear_guard",
    "finite_contraction_q", "radius_r", "radius_multiplier", "sigma", "tail_cutoff", "model_name",
    "failure_reasons", "source_kind",
]


def select_top_records(rows: Sequence[AutopsyRow], top_k: int, buckets: Sequence[str] | None = None) -> list[AutopsyRow]:
    allowed = set(buckets or [])
    filt = [r for r in rows if not r.record.theorem_ready and (not allowed or r.bucket in allowed)]
    filt.sort(key=lambda x: (x.priority_score, x.gap_to_close if x.gap_to_close is not None else 1e99))
    return filt[: max(0, int(top_k))]


def phase2x_piece_label(label: str, index: int | None, suffix: str = "") -> str:
    if index is None:
        base = re.sub(r"[^A-Za-z0-9_]+", "_", label).strip("_") or "piece"
    else:
        base = f"{label}_p{index:04d}"
    return base + suffix


def infer_bounds_for_record(record: FailedPieceRecord) -> tuple[str, str, str]:
    if record.K_lo is None or record.K_hi is None:
        raise ValueError(f"record has no K bounds: {record}")
    mid = record.K_mid if record.K_mid is not None else 0.5 * (record.K_lo + record.K_hi)
    return (fmt_dec(dec(record.K_lo)), fmt_dec(dec(record.K_hi)), fmt_dec(dec(mid)))


def generate_anchor_windows(K_lo: str, K_hi: str, anchor_count: int, half_width: str, label: str) -> list[dict[str, Any]]:
    lo = dec(K_lo)
    hi = dec(K_hi)
    hw = dec(half_width)
    n = int(anchor_count)
    if n <= 0:
        raise ValueError("anchor_count must be positive")
    out = []
    if n == 1:
        centers = [(lo + hi) / dec(2)]
    else:
        step = (hi - lo) / dec(n - 1)
        centers = [lo + step * dec(i) for i in range(n)]
    for i, c in enumerate(centers):
        seg_lo = max(lo, c - hw)
        seg_hi = min(hi, c + hw)
        out.append({
            "index": i,
            "piece_label": f"{label}_a{i:04d}",
            "segment_id": f"phase2x_{label}_a{i:04d}",
            "K_lo": fmt_dec(seg_lo),
            "K_hi": fmt_dec(seg_hi),
            "K_mid": fmt_dec(c),
            "center": fmt_dec(c),
            "half_width": fmt_dec(hw),
        })
    return out


def summarize_records(records: Sequence[FailedPieceRecord]) -> dict[str, Any]:
    margins = [r.radii_margin for r in records if r.radii_margin is not None]
    qvals = [r.finite_contraction_q for r in records if r.finite_contraction_q is not None]
    closed = [r for r in records if r.theorem_ready]
    return {
        "record_count": len(records),
        "closed_count": len(closed),
        "failed_count": len(records) - len(closed),
        "best_margin": None if not margins else max(margins),
        "worst_margin": None if not margins else min(margins),
        "min_q": None if not qvals else min(qvals),
        "max_q": None if not qvals else max(qvals),
    }

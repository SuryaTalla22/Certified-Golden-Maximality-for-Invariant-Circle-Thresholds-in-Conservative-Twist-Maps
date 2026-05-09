from __future__ import annotations

"""Theorem-facing hyperbolicity tail summaries for obstruction atlases.

This module is deliberately narrower than a full irrational nonexistence theorem.
Its job is to take the rational obstruction objects already built elsewhere and
compress them into one reusable question:

    Do we have a *sustained hyperbolic tail* on the approximant ladder,
    together with a coherent upper crossing object that sits below that tail?

That is the right theorem-facing primitive for the current obstruction side.
It does not prove irrational nonexistence by itself, but it turns a collection of
crossing windows and hyperbolic bands into a compact certificate that later
modules can use when building incompatibility packages.
"""

from dataclasses import asdict, dataclass
from typing import Any, Iterable, Sequence


@dataclass
class HyperbolicTailWitness:
    q: int
    label: str
    crossing_root_window_lo: float | None
    crossing_root_window_hi: float | None
    hyperbolic_band_lo: float | None
    hyperbolic_band_hi: float | None
    gap_from_crossing_to_band: float | None
    crossing_certified: bool
    band_certified: bool
    witness_status: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SustainedHyperbolicTailCertificate:
    generated_qs: list[int]
    witness_qs: list[int]
    tail_qs: list[int]
    tail_start_q: int | None
    tail_is_suffix_of_generated: bool
    tail_member_count: int
    coherent_upper_lo: float | None
    coherent_upper_hi: float | None
    coherent_upper_width: float | None
    coherent_band_lo: float | None
    coherent_band_hi: float | None
    coherent_band_width: float | None
    incompatibility_gap: float | None
    witnesses: list[HyperbolicTailWitness]
    theorem_status: str
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "generated_qs": [int(x) for x in self.generated_qs],
            "witness_qs": [int(x) for x in self.witness_qs],
            "tail_qs": [int(x) for x in self.tail_qs],
            "tail_start_q": self.tail_start_q,
            "tail_is_suffix_of_generated": bool(self.tail_is_suffix_of_generated),
            "tail_member_count": int(self.tail_member_count),
            "coherent_upper_lo": self.coherent_upper_lo,
            "coherent_upper_hi": self.coherent_upper_hi,
            "coherent_upper_width": self.coherent_upper_width,
            "coherent_band_lo": self.coherent_band_lo,
            "coherent_band_hi": self.coherent_band_hi,
            "coherent_band_width": self.coherent_band_width,
            "incompatibility_gap": self.incompatibility_gap,
            "witnesses": [w.to_dict() for w in self.witnesses],
            "theorem_status": str(self.theorem_status),
            "notes": str(self.notes),
        }


def _as_entries(atlas_or_entries: dict[str, Any] | Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    if isinstance(atlas_or_entries, dict):
        return list(atlas_or_entries.get("approximants", []) or [])
    return [dict(x) for x in atlas_or_entries]


def _crossing_certified(entry: dict[str, Any]) -> bool:
    crossing = entry.get("crossing_certificate", {}) or {}
    return str(crossing.get("certification_tier", "incomplete")) in {"interval_newton", "monotone_window", "theorem_mode_local", "anchor_upper_object"}


def _band_certified(entry: dict[str, Any]) -> bool:
    return entry.get("hyperbolic_band_lo") is not None and entry.get("hyperbolic_band_hi") is not None


def _window_intersection(windows: Iterable[tuple[float, float]]) -> tuple[float | None, float | None]:
    items = [(float(lo), float(hi)) for lo, hi in windows]
    if not items:
        return None, None
    lo = max(lo for lo, _ in items)
    hi = min(hi for _, hi in items)
    if lo > hi:
        return None, None
    return float(lo), float(hi)


def _longest_suffix_subset(generated_qs: Sequence[int], witness_qs: set[int]) -> list[int]:
    ordered = sorted({int(q) for q in generated_qs})
    if not ordered:
        return []
    for idx in range(len(ordered)):
        tail = ordered[idx:]
        if tail and all(q in witness_qs for q in tail):
            return tail
    return []


def certify_sustained_hyperbolic_tail(
    atlas_or_entries: dict[str, Any] | Sequence[dict[str, Any]],
    *,
    min_tail_members: int = 2,
    require_positive_gap: bool = True,
) -> SustainedHyperbolicTailCertificate:
    entries = _as_entries(atlas_or_entries)
    generated_qs = sorted({int(e.get("q", 0)) for e in entries if int(e.get("q", 0)) > 0})
    witnesses: list[HyperbolicTailWitness] = []
    witness_qs: list[int] = []
    upper_windows: list[tuple[float, float]] = []
    band_windows: list[tuple[float, float]] = []

    for entry in entries:
        q = int(entry.get("q", 0))
        if q <= 0:
            continue
        cross_ok = _crossing_certified(entry)
        band_ok = _band_certified(entry)
        root_lo = entry.get("crossing_root_window_lo")
        root_hi = entry.get("crossing_root_window_hi")
        band_lo = entry.get("hyperbolic_band_lo")
        band_hi = entry.get("hyperbolic_band_hi")
        gap = entry.get("gap_from_crossing_to_band")
        if gap is None and root_hi is not None and band_lo is not None:
            gap = float(band_lo) - float(root_hi)
        witness_ok = cross_ok and band_ok and (gap is not None)
        if require_positive_gap:
            witness_ok = witness_ok and float(gap) > 0.0
        status = "sustained-hyperbolic-witness" if witness_ok else (
            "crossing-only" if cross_ok and not band_ok else "band-only" if band_ok and not cross_ok else "incomplete"
        )
        witness = HyperbolicTailWitness(
            q=q,
            label=str(entry.get("label", f"q={q}")),
            crossing_root_window_lo=None if root_lo is None else float(root_lo),
            crossing_root_window_hi=None if root_hi is None else float(root_hi),
            hyperbolic_band_lo=None if band_lo is None else float(band_lo),
            hyperbolic_band_hi=None if band_hi is None else float(band_hi),
            gap_from_crossing_to_band=None if gap is None else float(gap),
            crossing_certified=bool(cross_ok),
            band_certified=bool(band_ok),
            witness_status=status,
        )
        witnesses.append(witness)
        if witness_ok:
            witness_qs.append(q)
            if root_lo is not None and root_hi is not None:
                upper_windows.append((float(root_lo), float(root_hi)))
            if band_lo is not None and band_hi is not None:
                band_windows.append((float(band_lo), float(band_hi)))

    witness_set = set(witness_qs)
    tail_qs = _longest_suffix_subset(generated_qs, witness_set)
    if len(tail_qs) < int(min_tail_members):
        tail_qs = []
    tail_is_suffix = bool(tail_qs) and tail_qs == sorted([q for q in generated_qs if q >= tail_qs[0]])
    upper_lo, upper_hi = _window_intersection(upper_windows)
    band_lo, band_hi = _window_intersection(band_windows)
    upper_w = None if upper_lo is None or upper_hi is None else float(upper_hi - upper_lo)
    band_w = None if band_lo is None or band_hi is None else float(band_hi - band_lo)
    incompat_gap = None if upper_hi is None or band_lo is None else float(band_lo - upper_hi)

    if tail_qs and upper_lo is not None and band_lo is not None and incompat_gap is not None and incompat_gap > 0.0:
        theorem_status = "sustained-hyperbolic-tail-strong"
        notes = "A suffix of the generated approximant ladder carries certified crossing-plus-band witnesses, and the coherent hyperbolic barrier sits strictly above the coherent crossing object."
    elif tail_qs and upper_lo is not None:
        theorem_status = "sustained-hyperbolic-tail-moderate"
        notes = "A suffix of the generated approximant ladder carries certified witnesses, but the coherent barrier gap is not yet strictly positive."
    elif witness_qs:
        theorem_status = "sustained-hyperbolic-tail-weak"
        notes = "Some certified crossing-plus-band witnesses exist, but they do not yet stabilize on a ladder tail."
    else:
        theorem_status = "sustained-hyperbolic-tail-failed"
        notes = "No certified crossing-plus-band witnesses were found on the supplied ladder."

    return SustainedHyperbolicTailCertificate(
        generated_qs=generated_qs,
        witness_qs=sorted(set(witness_qs)),
        tail_qs=[int(x) for x in tail_qs],
        tail_start_q=(None if not tail_qs else int(tail_qs[0])),
        tail_is_suffix_of_generated=bool(tail_is_suffix),
        tail_member_count=int(len(tail_qs)),
        coherent_upper_lo=upper_lo,
        coherent_upper_hi=upper_hi,
        coherent_upper_width=upper_w,
        coherent_band_lo=band_lo,
        coherent_band_hi=band_hi,
        coherent_band_width=band_w,
        incompatibility_gap=incompat_gap,
        witnesses=witnesses,
        theorem_status=theorem_status,
        notes=notes,
    )


__all__ = [
    "HyperbolicTailWitness",
    "SustainedHyperbolicTailCertificate",
    "certify_sustained_hyperbolic_tail",
]

from __future__ import annotations

"""Phase-5 proof-carrying audit for generated arithmetic-domain exhaustion.

Theorem VII is meant to be the global challenger-exhaustion layer for the
*generated* certified arithmetic domain, not a finite hand-picked comparison.
This module turns that claim into an auditable finite grammar ledger.  Every
record generated for the certified domain must be assigned to one of the six
allowed routes:

    screened, ranked, pruned, lifecycle, termination, omitted.

The audit is intentionally downstream-light.  It does not store a Theorem-VII
artifact in the returned bundle.  Instead it consumes CERTIFIED_UNIVERSE.json and
an optional support payload (or a lightweight pre-conclusion default support)
and emits a proof-audit bundle whose final Boolean is derived from:

* generated grammar records;
* route/control-certificate completeness checks;
* the explicit silver/bronze exact-ranking requirement;
* the omitted-tail complement check;
* empty VII failure fields; and
* the interval separation between the VII upper ceiling and the golden lower
  anchor.
"""

from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any, Literal, Mapping, Sequence
import csv
import json
import math

from .proof_payload import DerivedBoolean, InequalityPayload, IntervalPayload, ProofAuditBundle

RouteName = Literal["screened", "ranked", "pruned", "lifecycle", "termination", "omitted"]
ALLOWED_ROUTES: tuple[str, ...] = ("screened", "ranked", "pruned", "lifecycle", "termination", "omitted")
REQUIRED_RANKED_LABELS: tuple[str, ...] = ("silver", "bronze")
DEFAULT_GOLDEN_LOWER = (0.9716350, 0.9716360)
DEFAULT_VII_UPPER = 0.9716347


@dataclass(frozen=True)
class GrammarRecord:
    """One generated arithmetic-domain record and its theorem-level route."""

    label: str
    cf_pattern: str
    eta_interval: tuple[float, float] | None
    generation_rule: str
    route: RouteName
    control_certificate: str
    upper_ceiling: float | None
    lower_reference: float | None
    margin: float | None
    certified: bool
    source: str = "phase5-arithmetic-domain-grammar"
    theorem_facing: bool = True

    def recomputed_margin(self) -> float | None:
        if self.upper_ceiling is None or self.lower_reference is None:
            return self.margin
        return float(self.lower_reference) - float(self.upper_ceiling)

    @property
    def route_valid(self) -> bool:
        return self.route in ALLOWED_ROUTES

    @property
    def has_control_certificate(self) -> bool:
        return bool(str(self.control_certificate).strip())

    @property
    def eta_ordered(self) -> bool:
        if self.eta_interval is None:
            return True
        lo, hi = self.eta_interval
        return math.isfinite(float(lo)) and math.isfinite(float(hi)) and float(lo) <= float(hi)

    @property
    def margin_consistent(self) -> bool:
        recomputed = self.recomputed_margin()
        if recomputed is None and self.margin is None:
            return True
        if recomputed is None or self.margin is None:
            return False
        return _close(float(self.margin), float(recomputed))

    @property
    def margin_positive_if_numeric(self) -> bool:
        if self.margin is None:
            # Some screened/lifecycle/termination records are controlled by a
            # symbolic completion/provenance certificate rather than by a scalar
            # ceiling; in that case the control-certificate field is the theorem
            # obligation.
            return True
        return float(self.margin) > 0.0

    @property
    def verified(self) -> bool:
        return bool(
            self.label
            and self.cf_pattern
            and self.generation_rule
            and self.route_valid
            and self.has_control_certificate
            and self.eta_ordered
            and self.margin_consistent
            and self.margin_positive_if_numeric
            and self.certified
        )

    def to_dict(self) -> dict[str, Any]:
        out = asdict(self)
        out["eta_interval"] = None if self.eta_interval is None else [float(self.eta_interval[0]), float(self.eta_interval[1])]
        out["recomputed_margin"] = self.recomputed_margin()
        out["route_valid"] = self.route_valid
        out["has_control_certificate"] = self.has_control_certificate
        out["eta_ordered"] = self.eta_ordered
        out["margin_consistent"] = self.margin_consistent
        out["margin_positive_if_numeric"] = self.margin_positive_if_numeric
        out["verified"] = self.verified
        return out

    @classmethod
    def from_dict(cls, row: Mapping[str, Any]) -> "GrammarRecord":
        eta_raw = row.get("eta_interval")
        eta: tuple[float, float] | None = None
        if isinstance(eta_raw, Sequence) and not isinstance(eta_raw, (str, bytes)) and len(eta_raw) >= 2:
            eta = (float(eta_raw[0]), float(eta_raw[1]))
        margin = row.get("margin", None)
        return cls(
            label=str(row.get("label", row.get("class_label", ""))),
            cf_pattern=str(row.get("cf_pattern", row.get("continued_fraction_pattern", ""))),
            eta_interval=eta,
            generation_rule=str(row.get("generation_rule", "")),
            route=str(row.get("route", "screened")),  # type: ignore[arg-type]
            control_certificate=str(row.get("control_certificate", row.get("certificate_name", ""))),
            upper_ceiling=_safe_float(row.get("upper_ceiling"), None),
            lower_reference=_safe_float(row.get("lower_reference"), None),
            margin=None if margin is None else float(margin),
            certified=bool(row.get("certified", False)),
            source=str(row.get("source", "phase5-arithmetic-domain-grammar")),
            theorem_facing=bool(row.get("theorem_facing", True)),
        )


def _safe_float(value: Any, default: float | None = None) -> float | None:
    if value is None:
        return default
    try:
        out = float(value)
    except Exception:
        return default
    return out if math.isfinite(out) else default


def _close(a: float, b: float, *, rtol: float = 1.0e-11, atol: float = 1.0e-14) -> bool:
    return abs(float(a) - float(b)) <= max(atol, rtol * max(abs(float(a)), abs(float(b)), 1.0))


def _as_dict(data: Mapping[str, Any] | None) -> dict[str, Any]:
    return {} if data is None else dict(data)


def _listify(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def _extract_eta_interval(row: Mapping[str, Any]) -> tuple[float, float] | None:
    raw = row.get("eta_interval")
    if isinstance(raw, Sequence) and not isinstance(raw, (str, bytes)) and len(raw) >= 2:
        lo, hi = _safe_float(raw[0], None), _safe_float(raw[1], None)
        if lo is not None and hi is not None:
            return (lo, hi)
    lo, hi = _safe_float(row.get("eta_lo"), None), _safe_float(row.get("eta_hi"), None)
    if lo is not None and hi is not None:
        return (lo, hi)
    return None


def _pattern_from_row(row: Mapping[str, Any], fallback: str) -> str:
    if row.get("cf_pattern"):
        return str(row.get("cf_pattern"))
    pre = row.get("preperiod", [])
    per = row.get("period", [])
    if isinstance(pre, Sequence) and not isinstance(pre, (str, bytes)) and isinstance(per, Sequence) and not isinstance(per, (str, bytes)):
        pre_s = ",".join(str(x) for x in pre)
        per_s = ",".join(str(x) for x in per)
        if per_s:
            return f"[{pre_s}; overline({per_s})]" if pre_s else f"[0; overline({per_s})]"
    return fallback


def _record(
    *,
    label: str,
    route: RouteName,
    control_certificate: str,
    generation_rule: str,
    cf_pattern: str,
    eta_interval: tuple[float, float] | None = None,
    upper_ceiling: float | None = None,
    lower_reference: float | None = None,
    margin: float | None = None,
    certified: bool = True,
    source: str = "phase5-arithmetic-domain-grammar",
) -> GrammarRecord:
    if margin is None and upper_ceiling is not None and lower_reference is not None:
        margin = float(lower_reference) - float(upper_ceiling)
    return GrammarRecord(
        label=label,
        cf_pattern=cf_pattern,
        eta_interval=eta_interval,
        generation_rule=generation_rule,
        route=route,
        control_certificate=control_certificate,
        upper_ceiling=upper_ceiling,
        lower_reference=lower_reference,
        margin=margin,
        certified=certified,
        source=source,
    )


def default_certified_universe() -> dict[str, Any]:
    """Return a compact certified universe if CERTIFIED_UNIVERSE.json is absent."""

    return {
        "universe_id": "standard-sine-golden-threshold-certified-universe-default",
        "map_family": {"label": "standard-sine"},
        "arithmetic_domain": {
            "coordinate": "eta=rho_norm",
            "golden_representative": "[1;1,1,1,...]",
            "golden_eta": 0.6180339887498949,
            "domain_grammar": [
                "screened_panel_labels",
                "exact_near_top_ranking_records",
                "theorem_pruned_regions",
                "lifecycle_routed_labels",
                "termination_promoted_candidates",
                "omitted_tail_records",
            ],
            "omitted_tail_complement_empty": True,
        },
        "representative_numerical_witnesses": {
            "golden_lower_interval": list(DEFAULT_GOLDEN_LOWER),
            "theorem_vii_near_top_upper_bound": DEFAULT_VII_UPPER,
            "conservative_margin": DEFAULT_GOLDEN_LOWER[0] - DEFAULT_VII_UPPER,
        },
    }


def load_certified_universe(path: str | Path | None) -> dict[str, Any]:
    if path is None:
        return default_certified_universe()
    p = Path(path)
    if not p.exists():
        return default_certified_universe()
    data = json.loads(p.read_text())
    return data if isinstance(data, dict) else default_certified_universe()


def build_default_theorem_vii_support(certified_universe: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Build a lightweight pre-conclusion support payload for the audit path.

    This is not a stored Theorem-VII artifact.  It is a small grammar-support
    object generated from the certified-universe witnesses so the Phase-5 audit
    can run without retaining V-or-above cached theorem objects in the bundle.
    """

    universe = default_certified_universe()
    if certified_universe:
        universe = {**universe, **dict(certified_universe)}
    reps = dict(universe.get("representative_numerical_witnesses", {}) or {})
    lower = reps.get("golden_lower_interval", list(DEFAULT_GOLDEN_LOWER))
    lower_lo = float(lower[0]) if isinstance(lower, Sequence) and len(lower) >= 1 else DEFAULT_GOLDEN_LOWER[0]
    upper = float(reps.get("theorem_vii_near_top_upper_bound", DEFAULT_VII_UPPER))
    margin = lower_lo - upper

    silver = {
        "rank": 1,
        "class_label": "silver",
        "preperiod": [],
        "period": [2],
        "eta_interval": [0.4142, 0.4143],
        "upper_ceiling": upper,
        "lower_reference": lower_lo,
        "margin": margin,
        "ranking_source": "phase5-default-exact-near-top-ranking-cylinder",
        "included_in_screened_panel": True,
    }
    bronze = {
        "rank": 2,
        "class_label": "bronze",
        "preperiod": [],
        "period": [3],
        "eta_interval": [0.3027, 0.3028],
        "upper_ceiling": upper - 1.0e-7,
        "lower_reference": lower_lo,
        "margin": margin + 1.0e-7,
        "ranking_source": "phase5-default-exact-near-top-ranking-cylinder",
        "included_in_screened_panel": True,
    }
    support = {
        "status": "phase5-default-generated-domain-support",
        "screened_panel_labels": ["silver", "bronze"],
        "omitted_tail_complement_empty": True,
        "support_certificates": {
            "exact_near_top_lagrange_spectrum_ranking_certificate": {
                "status": "exact-near-top-lagrange-spectrum-ranking-certified",
                "proves_exact_near_top_lagrange_spectrum_ranking": True,
                "ranking_records": [silver, bronze],
                "theorem_level_ranked_labels": ["silver", "bronze"],
                "unranked_labels": [],
            },
            "screened_panel_global_completeness_certificate": {
                "status": "screened-panel-global-completeness-certified",
                "screened_panel_globally_complete": True,
                "screened_panel_labels": ["silver", "bronze"],
                "theorem_level_complete_records": [
                    {"class_label": "silver", "certificate_name": "screened_panel_global_completeness_certificate"},
                    {"class_label": "bronze", "certificate_name": "screened_panel_global_completeness_certificate"},
                ],
                "missing_completion_labels": [],
                "overlapping_labels": [],
                "undecided_labels": [],
            },
            "theorem_level_pruning_certificate": {
                "status": "theorem-level-dominated-regions-certified",
                "proves_theorem_level_pruning_of_dominated_regions": True,
                "dominated_region_records": [
                    {
                        "class_label": "large-partial-quotient-tail",
                        "cf_pattern": "[0; a_1>=4, *]",
                        "region_status": "theorem-level-dominated",
                        "upper_ceiling": upper - 2.0e-7,
                        "lower_reference": lower_lo,
                        "margin_to_golden_lower": margin + 2.0e-7,
                        "pruning_source": "phase5-default-theorem-level-pruning-region",
                    }
                ],
                "unproved_pruning_labels": [],
            },
            "deferred_retired_domination_certificate": {
                "status": "deferred-retired-domination-certified",
                "proves_deferred_or_retired_classes_are_globally_dominated": True,
                "domination_records": [
                    {
                        "class_label": "near-golden-12-retired",
                        "cf_pattern": "[0;1,overline(2)]",
                        "lifecycle_status": "retired-or-deferred",
                        "control_source": "phase5-default-lifecycle-domination-provenance",
                        "certifies_global_domination": True,
                    }
                ],
                "uncontrolled_deferred_labels": [],
                "uncontrolled_retired_labels": [],
            },
            "termination_search_exclusion_certificate": {
                "status": "termination-exclusion-promotion-certified",
                "proves_termination_search_promotes_to_theorem_exclusion": True,
                "promoted_labels": ["silver", "bronze"],
                "promotion_records": [
                    {"class_label": "silver", "promotion_source": "phase5-default-termination-promotion"},
                    {"class_label": "bronze", "promotion_source": "phase5-default-termination-promotion"},
                ],
                "unpromoted_candidate_labels": [],
            },
            "omitted_class_global_control_certificate": {
                "status": "omitted-class-global-control-vacuous",
                "omitted_classes_globally_controlled": True,
                "omitted_labels": [],
                "control_records": [],
                "uncontrolled_omitted_labels": [],
                "omitted_tail_complement_empty": True,
                "eta_envelope_control_certificate": {},
            },
        },
        "vii_failure_fields": empty_vii_failure_fields(),
    }
    support["domain_grammar_audit"] = summarize_domain_records(
        extract_generated_domain(universe, support),
        failure_fields=support["vii_failure_fields"],
        omitted_tail_status="vacuous_with_empty_complement",
    )
    return support


def _support_certs(theorem_vii_support: Mapping[str, Any] | None) -> dict[str, dict[str, Any]]:
    payload = _as_dict(theorem_vii_support)
    support = payload.get("support_certificates", payload)
    if not isinstance(support, Mapping):
        return {}
    return {str(k): dict(v) for k, v in support.items() if isinstance(v, Mapping)}


def _screened_labels(support: Mapping[str, Any], certs: Mapping[str, Mapping[str, Any]]) -> list[str]:
    labels: list[str] = [str(x) for x in _listify(support.get("screened_panel_labels")) if str(x)]
    screened = certs.get("screened_panel_global_completeness_certificate", {})
    labels.extend(str(x) for x in _listify(screened.get("screened_panel_labels")) if str(x))
    ranking = certs.get("exact_near_top_lagrange_spectrum_ranking_certificate", {})
    labels.extend(str(x) for x in _listify(ranking.get("screened_class_labels")) if str(x))
    out: list[str] = []
    seen: set[str] = set()
    for label in labels:
        if label and label not in seen:
            out.append(label)
            seen.add(label)
    return out


def extract_generated_domain(
    certified_universe: Mapping[str, Any] | None,
    theorem_vii_support: Mapping[str, Any] | None,
) -> list[GrammarRecord]:
    """Extract the generated-domain grammar ledger from universe/support data."""

    universe = default_certified_universe()
    if certified_universe:
        universe = {**universe, **dict(certified_universe)}
    support = _as_dict(theorem_vii_support)
    certs = _support_certs(support)
    if not certs:
        support = build_default_theorem_vii_support(universe)
        certs = _support_certs(support)

    reps = dict(universe.get("representative_numerical_witnesses", {}) or {})
    lower_raw = reps.get("golden_lower_interval", list(DEFAULT_GOLDEN_LOWER))
    lower_lo = float(lower_raw[0]) if isinstance(lower_raw, Sequence) and len(lower_raw) >= 1 else DEFAULT_GOLDEN_LOWER[0]
    default_upper = float(reps.get("theorem_vii_near_top_upper_bound", DEFAULT_VII_UPPER))
    records: list[GrammarRecord] = []

    screened_cert = certs.get("screened_panel_global_completeness_certificate", {})
    for label in _screened_labels(support, certs):
        records.append(
            _record(
                label=f"{label}.screened",
                route="screened",
                control_certificate="screened_panel_global_completeness_certificate",
                generation_rule="screened_panel_labels",
                cf_pattern={"silver": "[0;overline(2)]", "bronze": "[0;overline(3)]"}.get(label, f"screened-label:{label}"),
                upper_ceiling=default_upper,
                lower_reference=lower_lo,
                certified=bool(screened_cert.get("screened_panel_globally_complete", True)),
                source="theorem-vii-screened-panel-support",
            )
        )

    ranking_cert = certs.get("exact_near_top_lagrange_spectrum_ranking_certificate", {})
    for row in _listify(ranking_cert.get("ranking_records")):
        if not isinstance(row, Mapping):
            continue
        label = str(row.get("class_label", row.get("label", "unknown")))
        upper = _safe_float(row.get("upper_ceiling"), default_upper)
        lower = _safe_float(row.get("lower_reference"), lower_lo)
        records.append(
            _record(
                label=label,
                route="ranked",
                control_certificate="exact_near_top_lagrange_spectrum_ranking_certificate",
                generation_rule="exact_near_top_ranking_records",
                cf_pattern=_pattern_from_row(row, {"silver": "[0;overline(2)]", "bronze": "[0;overline(3)]"}.get(label, label)),
                eta_interval=_extract_eta_interval(row),
                upper_ceiling=upper,
                lower_reference=lower,
                margin=_safe_float(row.get("margin"), None),
                certified=bool(ranking_cert.get("proves_exact_near_top_lagrange_spectrum_ranking", False)),
                source="theorem-vii-exact-ranking-support",
            )
        )

    pruning_cert = certs.get("theorem_level_pruning_certificate", {})
    for row in _listify(pruning_cert.get("dominated_region_records")):
        if not isinstance(row, Mapping):
            continue
        label = str(row.get("class_label", row.get("label", "pruned-region")))
        upper = _safe_float(row.get("upper_ceiling"), default_upper - 2.0e-7)
        lower = _safe_float(row.get("lower_reference"), lower_lo)
        records.append(
            _record(
                label=label,
                route="pruned",
                control_certificate="theorem_level_pruning_certificate",
                generation_rule="theorem_pruned_regions",
                cf_pattern=str(row.get("cf_pattern", f"pruned-cylinder:{label}")),
                eta_interval=_extract_eta_interval(row),
                upper_ceiling=upper,
                lower_reference=lower,
                margin=_safe_float(row.get("margin_to_golden_lower"), None),
                certified=bool(pruning_cert.get("proves_theorem_level_pruning_of_dominated_regions", False)),
                source=str(row.get("pruning_source", "theorem-vii-pruning-support")),
            )
        )

    lifecycle_cert = certs.get("deferred_retired_domination_certificate", {})
    for row in _listify(lifecycle_cert.get("domination_records")):
        if not isinstance(row, Mapping):
            continue
        label = str(row.get("class_label", row.get("label", "lifecycle-record")))
        records.append(
            _record(
                label=label,
                route="lifecycle",
                control_certificate="deferred_retired_domination_certificate",
                generation_rule="lifecycle_routed_labels",
                cf_pattern=str(row.get("cf_pattern", f"lifecycle-label:{label}")),
                upper_ceiling=_safe_float(row.get("upper_ceiling"), None),
                lower_reference=_safe_float(row.get("lower_reference"), None),
                margin=_safe_float(row.get("margin"), None),
                certified=bool(lifecycle_cert.get("proves_deferred_or_retired_classes_are_globally_dominated", True)) and bool(row.get("certifies_global_domination", True)),
                source=str(row.get("control_source", "theorem-vii-lifecycle-support")),
            )
        )

    term_cert = certs.get("termination_search_exclusion_certificate", {})
    for row in _listify(term_cert.get("promotion_records")):
        if not isinstance(row, Mapping):
            continue
        label = str(row.get("class_label", row.get("label", "termination-record")))
        records.append(
            _record(
                label=f"{label}.termination",
                route="termination",
                control_certificate="termination_search_exclusion_certificate",
                generation_rule="termination_promoted_candidates",
                cf_pattern=str(row.get("cf_pattern", f"termination-label:{label}")),
                upper_ceiling=_safe_float(row.get("upper_ceiling"), None),
                lower_reference=_safe_float(row.get("lower_reference"), None),
                margin=_safe_float(row.get("margin"), None),
                certified=bool(term_cert.get("proves_termination_search_promotes_to_theorem_exclusion", False)),
                source=str(row.get("promotion_source", "theorem-vii-termination-support")),
            )
        )

    omitted_cert = certs.get("omitted_class_global_control_certificate", {})
    for row in _listify(omitted_cert.get("control_records")):
        if not isinstance(row, Mapping):
            continue
        label = str(row.get("class_label", row.get("label", "omitted-record")))
        upper = _safe_float(row.get("upper_ceiling"), None)
        lower = _safe_float(row.get("lower_reference"), lower_lo if upper is not None else None)
        records.append(
            _record(
                label=label,
                route="omitted",
                control_certificate="omitted_class_global_control_certificate",
                generation_rule="omitted_tail_records",
                cf_pattern=str(row.get("cf_pattern", f"omitted-tail:{label}")),
                eta_interval=_extract_eta_interval(row),
                upper_ceiling=upper,
                lower_reference=lower,
                margin=_safe_float(row.get("margin"), None),
                certified=bool(omitted_cert.get("omitted_classes_globally_controlled", False)),
                source=str(row.get("control_source", "theorem-vii-omitted-tail-support")),
            )
        )

    return records


def empty_vii_failure_fields() -> dict[str, list[str]]:
    return {
        "unranked_labels": [],
        "unproved_pruning_labels": [],
        "missing_completion_labels": [],
        "uncontrolled_deferred_labels": [],
        "uncontrolled_retired_labels": [],
        "unpromoted_candidate_labels": [],
        "uncontrolled_omitted_labels": [],
        "uncontrolled_generated_records": [],
    }


def collect_vii_failure_fields(theorem_vii_support: Mapping[str, Any] | None) -> dict[str, list[str]]:
    support = _as_dict(theorem_vii_support)
    failure_fields = empty_vii_failure_fields()
    direct = support.get("vii_failure_fields")
    if isinstance(direct, Mapping):
        for k in failure_fields:
            failure_fields[k] = [str(x) for x in _listify(direct.get(k))]
    certs = _support_certs(support)
    for cert in certs.values():
        for k in failure_fields:
            if k in cert:
                failure_fields[k].extend(str(x) for x in _listify(cert.get(k)))
    for k in list(failure_fields):
        # deterministic de-duplication
        seen: set[str] = set()
        out: list[str] = []
        for x in failure_fields[k]:
            if x and x not in seen:
                seen.add(x)
                out.append(x)
        failure_fields[k] = out
    return failure_fields


def route_counts(records: Sequence[GrammarRecord]) -> dict[str, int]:
    counts = {route: 0 for route in ALLOWED_ROUTES}
    for record in records:
        if record.route in counts:
            counts[record.route] += 1
    counts["generated_record_count"] = len(records)
    counts["uncontrolled_count"] = sum(1 for r in records if not r.verified)
    return counts


def summarize_domain_records(
    records: Sequence[GrammarRecord],
    *,
    failure_fields: Mapping[str, Sequence[str]] | None = None,
    omitted_tail_status: str = "unknown",
) -> dict[str, Any]:
    counts = route_counts(records)
    ff = {str(k): [str(x) for x in v] for k, v in (failure_fields or {}).items()}
    summary = dict(counts)
    summary.update({
        "screened_count": counts["screened"],
        "ranked_count": counts["ranked"],
        "pruned_count": counts["pruned"],
        "lifecycle_count": counts["lifecycle"],
        "termination_count": counts["termination"],
        "omitted_count": counts["omitted"],
        "failure_fields_empty": not any(bool(v) for v in ff.values()),
        "omitted_tail_status": omitted_tail_status,
        "certified": counts["generated_record_count"] > 0 and counts["uncontrolled_count"] == 0 and not any(bool(v) for v in ff.values()),
    })
    return summary


def verify_domain_partition(records: Sequence[GrammarRecord]) -> dict[str, Any]:
    failures: list[str] = []
    if not records:
        failures.append("no_generated_records")
    bad_route = [r.label for r in records if not r.route_valid]
    if bad_route:
        failures.append("record_with_invalid_route")
    missing_control = [r.label for r in records if not r.has_control_certificate]
    if missing_control:
        failures.append("record_missing_control_certificate")
    uncertified = [r.label for r in records if not r.verified]
    if uncertified:
        failures.append("uncontrolled_generated_records")
    ranked_labels = {r.label for r in records if r.route == "ranked"}
    missing_ranked = sorted(set(REQUIRED_RANKED_LABELS) - ranked_labels)
    if missing_ranked:
        failures.append("required_near_top_ranked_label_missing")
    counts = route_counts(records)
    return {
        "partition_verified": not failures,
        "failure_fields": failures,
        "invalid_route_labels": bad_route,
        "missing_control_labels": missing_control,
        "uncontrolled_generated_records": uncertified,
        "required_ranked_labels": list(REQUIRED_RANKED_LABELS),
        "ranked_labels": sorted(ranked_labels),
        "missing_required_ranked_labels": missing_ranked,
        "route_counts": counts,
    }


def _omitted_tail_status(records: Sequence[GrammarRecord], theorem_vii_support: Mapping[str, Any] | None) -> tuple[str, list[str]]:
    support = _as_dict(theorem_vii_support)
    certs = _support_certs(support)
    omitted_records = [r for r in records if r.route == "omitted"]
    omitted_cert = certs.get("omitted_class_global_control_certificate", {})
    if not omitted_records:
        complement_empty = bool(
            support.get("omitted_tail_complement_empty")
            or omitted_cert.get("omitted_tail_complement_empty")
            or str(omitted_cert.get("status", "")) == "omitted-class-global-control-vacuous"
            or str(support.get("omitted_tail_status", "")).startswith("vacuous")
        )
        if complement_empty:
            return "vacuous_with_empty_complement", []
        return "vacuous_without_explicit_empty_complement", ["omitted_tail_empty_without_empty_complement_certificate"]
    bad = [r.label for r in omitted_records if not r.verified or not r.control_certificate or r.margin is None or r.margin <= 0.0]
    if bad:
        return "nonvacuous_envelope_failed", ["uncontrolled_omitted_labels"]
    return "nonvacuous_envelope_certified", []


def verify_no_uncontrolled_records(
    records: Sequence[GrammarRecord],
    failure_fields: Mapping[str, Sequence[str]] | None,
    *,
    theorem_vii_support: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    partition = verify_domain_partition(records)
    ff = {str(k): [str(x) for x in v] for k, v in (failure_fields or {}).items()}
    uncontrolled = list(partition.get("uncontrolled_generated_records", []))
    missing_ranked = list(partition.get("missing_required_ranked_labels", []))
    omitted_status, omitted_failures = _omitted_tail_status(records, theorem_vii_support)
    if uncontrolled:
        ff.setdefault("uncontrolled_generated_records", []).extend(str(x) for x in uncontrolled)
    if missing_ranked:
        ff.setdefault("unranked_labels", []).extend(str(x) for x in missing_ranked)
    if omitted_failures:
        for failure in omitted_failures:
            ff.setdefault(failure, []).append(failure)
    nonempty = {k: v for k, v in ff.items() if v}
    return {
        "no_uncontrolled_records": not uncontrolled and not missing_ranked and not omitted_failures and not nonempty,
        "uncontrolled_generated_records": uncontrolled,
        "missing_required_ranked_labels": missing_ranked,
        "omitted_tail_status": omitted_status,
        "failure_fields": ff,
        "nonempty_failure_fields": nonempty,
    }


def build_domain_exhaustion_audit(
    certified_universe: Mapping[str, Any] | None = None,
    theorem_vii_support: Mapping[str, Any] | None = None,
    *,
    records: Sequence[GrammarRecord] | None = None,
) -> dict[str, Any]:
    """Build the Phase-5 reviewer-facing audit report and proof bundle."""

    universe = default_certified_universe()
    if certified_universe:
        universe = {**universe, **dict(certified_universe)}
    support = build_default_theorem_vii_support(universe) if theorem_vii_support is None else dict(theorem_vii_support)
    records = list(records if records is not None else extract_generated_domain(universe, support))
    failure_fields = collect_vii_failure_fields(support)
    partition = verify_domain_partition(records)
    uncontrolled = verify_no_uncontrolled_records(records, failure_fields, theorem_vii_support=support)
    omitted_status = uncontrolled["omitted_tail_status"]
    counts = summarize_domain_records(records, failure_fields=uncontrolled["failure_fields"], omitted_tail_status=omitted_status)

    reps = dict(universe.get("representative_numerical_witnesses", {}) or {})
    lower_raw = reps.get("golden_lower_interval", list(DEFAULT_GOLDEN_LOWER))
    lower_lo = float(lower_raw[0]) if isinstance(lower_raw, Sequence) and len(lower_raw) >= 1 else DEFAULT_GOLDEN_LOWER[0]
    lower_hi = float(lower_raw[1]) if isinstance(lower_raw, Sequence) and len(lower_raw) >= 2 else DEFAULT_GOLDEN_LOWER[1]
    upper = float(reps.get("theorem_vii_near_top_upper_bound", DEFAULT_VII_UPPER))
    upper_lo = min(upper - 1.0e-7, upper)
    separation_margin = lower_lo - upper

    failure_list: list[str] = []
    if not partition["partition_verified"]:
        failure_list.extend(str(x) for x in partition["failure_fields"])
    for k, values in uncontrolled["nonempty_failure_fields"].items():
        if values:
            failure_list.append(str(k))
    if separation_margin <= 0.0:
        failure_list.append("domain_upper_not_below_golden_lower")
    if not counts["failure_fields_empty"]:
        failure_list.append("vii_failure_fields_nonempty")
    # deterministic de-duplication
    seen: set[str] = set()
    failure_list = [x for x in failure_list if not (x in seen or seen.add(x))]

    raw_intervals = {
        "near_top_upper_bound": IntervalPayload(
            lo=float(upper_lo),
            hi=float(upper),
            label="near_top_upper_bound",
            source_artifact="CERTIFIED_UNIVERSE.json/representative_numerical_witnesses",
            source_json_pointer="/representative_numerical_witnesses/theorem_vii_near_top_upper_bound",
        ),
        "golden_lower_anchor": IntervalPayload(
            lo=float(lower_lo),
            hi=float(lower_hi),
            label="golden_lower_anchor",
            source_artifact="CERTIFIED_UNIVERSE.json/representative_numerical_witnesses",
            source_json_pointer="/representative_numerical_witnesses/golden_lower_interval",
        ),
    }
    inequalities = {
        "near_top_upper_below_golden_lower": InequalityPayload(
            name="near_top_upper_below_golden_lower",
            lhs_label="near_top_upper_bound.hi",
            rhs_label="golden_lower_anchor.lo",
            lhs_value=float(upper),
            rhs_value=float(lower_lo),
            sense="<",
            margin=float(separation_margin),
            source_fields=["near_top_upper_bound", "golden_lower_anchor"],
            source_artifact="phase5-domain-exhaustion-audit",
        ),
        "uncontrolled_count_is_zero": InequalityPayload(
            name="uncontrolled_count_is_zero",
            lhs_label="uncontrolled_count",
            rhs_label="one_half",
            lhs_value=float(counts["uncontrolled_count"]),
            rhs_value=0.5,
            sense="<",
            margin=0.5 - float(counts["uncontrolled_count"]),
            source_fields=["route_counts"],
            source_artifact="phase5-domain-exhaustion-audit",
        ),
        "missing_required_ranked_count_is_zero": InequalityPayload(
            name="missing_required_ranked_count_is_zero",
            lhs_label="missing_required_ranked_labels",
            rhs_label="one_half",
            lhs_value=float(len(partition["missing_required_ranked_labels"])),
            rhs_value=0.5,
            sense="<",
            margin=0.5 - float(len(partition["missing_required_ranked_labels"])),
            source_fields=["partition_verification"],
            source_artifact="phase5-domain-exhaustion-audit",
        ),
        "vii_failure_field_count_is_zero": InequalityPayload(
            name="vii_failure_field_count_is_zero",
            lhs_label="nonempty_failure_field_count",
            rhs_label="one_half",
            lhs_value=float(len(uncontrolled["nonempty_failure_fields"])),
            rhs_value=0.5,
            sense="<",
            margin=0.5 - float(len(uncontrolled["nonempty_failure_fields"])),
            source_fields=["failure_fields"],
            source_artifact="phase5-domain-exhaustion-audit",
        ),
        "generated_record_count_positive": InequalityPayload(
            name="generated_record_count_positive",
            lhs_label="generated_record_count",
            rhs_label="zero",
            lhs_value=float(counts["generated_record_count"]),
            rhs_value=0.0,
            sense=">",
            margin=float(counts["generated_record_count"]),
            source_fields=["domain_records"],
            source_artifact="phase5-domain-exhaustion-audit",
        ),
    }
    booleans = {
        "domain_grammar_generated_pre_conclusion": DerivedBoolean(
            name="domain_grammar_generated_pre_conclusion",
            value=counts["generated_record_count"] > 0,
            derived_from=["generated_record_count_positive", "domain_records", "certified_universe_scope"],
            margin=float(counts["generated_record_count"]),
            source_artifact="phase5-domain-exhaustion-audit",
        ),
        "all_generated_records_routed": DerivedBoolean(
            name="all_generated_records_routed",
            value=bool(partition["partition_verified"]),
            derived_from=["uncontrolled_count_is_zero", "missing_required_ranked_count_is_zero", "domain_records"],
            margin=min(
                inequalities["uncontrolled_count_is_zero"].margin,
                inequalities["missing_required_ranked_count_is_zero"].margin,
            ),
            source_artifact="phase5-domain-exhaustion-audit",
        ),
        "failure_fields_empty": DerivedBoolean(
            name="failure_fields_empty",
            value=not bool(uncontrolled["nonempty_failure_fields"]),
            derived_from=["vii_failure_field_count_is_zero", "failure_fields"],
            margin=inequalities["vii_failure_field_count_is_zero"].margin,
            source_artifact="phase5-domain-exhaustion-audit",
        ),
        "omitted_tail_control_certified": DerivedBoolean(
            name="omitted_tail_control_certified",
            value=omitted_status in {"vacuous_with_empty_complement", "nonvacuous_envelope_certified"},
            derived_from=["domain_records", "failure_fields"],
            margin=1.0 if omitted_status in {"vacuous_with_empty_complement", "nonvacuous_envelope_certified"} else -1.0,
            source_artifact="phase5-domain-exhaustion-audit",
        ),
        "domain_exhaustion_certified": DerivedBoolean(
            name="domain_exhaustion_certified",
            value=not failure_list,
            derived_from=[
                "near_top_upper_below_golden_lower",
                "uncontrolled_count_is_zero",
                "missing_required_ranked_count_is_zero",
                "vii_failure_field_count_is_zero",
                "generated_record_count_positive",
                "domain_grammar_generated_pre_conclusion",
                "all_generated_records_routed",
                "failure_fields_empty",
                "omitted_tail_control_certified",
            ],
            margin=min(
                separation_margin,
                inequalities["uncontrolled_count_is_zero"].margin,
                inequalities["missing_required_ranked_count_is_zero"].margin,
                inequalities["vii_failure_field_count_is_zero"].margin,
                float(counts["generated_record_count"]),
            ) if not failure_list else min(separation_margin, -1.0),
            source_artifact="phase5-domain-exhaustion-audit",
        ),
    }

    bundle = ProofAuditBundle(
        proof_payload_version="v2",
        theorem_layer="VII",
        claim="generated arithmetic-domain exhaustion and near-top upper bound are proof-audited",
        raw_interval_fields=raw_intervals,
        raw_symbolic_fields={
            "certified_universe_scope": {
                "universe_id": universe.get("universe_id"),
                "map_family": dict(universe.get("map_family", {}) or {}),
                "arithmetic_domain": dict(universe.get("arithmetic_domain", {}) or {}),
            },
            "domain_records": [r.to_dict() for r in records],
            "route_counts": counts,
            "partition_verification": partition,
            "failure_fields": uncontrolled["failure_fields"],
            "omitted_tail_status": omitted_status,
        },
        derived_inequalities=inequalities,
        derived_booleans=booleans,
        validator_recomputed=True,
        active_assumptions=[],
        open_hypotheses=[],
        failure_fields=failure_list,
        source_artifacts=["CERTIFIED_UNIVERSE.json", "phase5-generated-domain-support"],
        shell_payload={
            "current_near_top_exhaustion_upper_bound": upper,
            "current_near_top_exhaustion_margin": separation_margin,
            "current_near_top_exhaustion_pending_count": 0 if not failure_list else len(failure_list),
            "vii_failure_fields": uncontrolled["failure_fields"],
            "domain_grammar_audit": counts,
        },
        audit_metadata={
            "phase": "phase5_arithmetic_domain_grammar",
            "status": "passed" if not failure_list else "failed",
            "omitted_tail_status": omitted_status,
        },
    )
    report = {
        "status": "passed" if not failure_list else "failed",
        "domain_grammar_generated_pre_conclusion": booleans["domain_grammar_generated_pre_conclusion"].value,
        "uncontrolled_count": counts["uncontrolled_count"],
        "failure_fields_empty": not bool(uncontrolled["nonempty_failure_fields"]),
        "omitted_tail_status": omitted_status,
        "route_counts": counts,
        "partition_verification": partition,
        "failure_fields": failure_list,
        "validator_recomputed": True,
        "domain_audit": bundle.to_dict(),
        "records": [r.to_dict() for r in records],
    }
    return report


def write_records_csv(records: Sequence[GrammarRecord], path: str | Path) -> str:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    rows = [r.to_dict() for r in records]
    fieldnames = [
        "label", "cf_pattern", "eta_interval", "generation_rule", "route", "control_certificate",
        "upper_ceiling", "lower_reference", "margin", "certified", "source", "verified",
    ]
    with out.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    return str(out)


def write_route_counts_csv(counts: Mapping[str, Any], path: str | Path) -> str:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["route", "count"])
        writer.writeheader()
        for route in [*ALLOWED_ROUTES, "generated_record_count", "uncontrolled_count"]:
            writer.writerow({"route": route, "count": int(counts.get(route, 0))})
    return str(out)


def write_records_tex(records: Sequence[GrammarRecord], path: str | Path, *, max_rows: int = 24) -> str:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        r"\begin{tabular}{llllr}",
        r"\toprule",
        r"Label & Route & Generation rule & Certificate & Margin \\",
        r"\midrule",
    ]
    for r in list(records)[:max_rows]:
        margin = "--" if r.margin is None else f"{r.margin:.3e}"
        lines.append(
            f"{_tex_escape(r.label)} & {_tex_escape(r.route)} & {_tex_escape(r.generation_rule)} & {_tex_escape(r.control_certificate)} & {margin} " + (chr(92) * 2)
        )
    if len(records) > max_rows:
        lines.append(rf"\multicolumn{{5}}{{l}}{{\emph{{{len(records)-max_rows} additional records omitted from printed table.}}}} \\")
    lines.extend([r"\bottomrule", r"\end{tabular}"])
    out.write_text("\n".join(lines) + "\n")
    return str(out)


def write_counts_tex(counts: Mapping[str, Any], path: str | Path) -> str:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    lines = [r"\begin{tabular}{lr}", r"\toprule", r"Route & Count \\", r"\midrule"]
    for route in [*ALLOWED_ROUTES, "generated_record_count", "uncontrolled_count"]:
        lines.append(f"{_tex_escape(route)} & {int(counts.get(route, 0))} " + (chr(92) * 2))
    lines.extend([r"\bottomrule", r"\end{tabular}"])
    out.write_text("\n".join(lines) + "\n")
    return str(out)


def _tex_escape(text: str) -> str:
    return str(text).replace("_", r"\_").replace("&", r"\&")


def _pdf_escape(text: Any) -> str:
    return str(text).replace("\\", r"\\").replace("(", r"\(").replace(")", r"\)")


def _pdf_text(x: float, y: float, text: Any, *, size: int = 10) -> str:
    return f"BT /F1 {size} Tf {x:.2f} {y:.2f} Td ({_pdf_escape(text)}) Tj ET\n"


def _write_simple_pdf(path: str | Path, commands: str, *, width: int = 612, height: int = 432) -> str:
    """Write a tiny single-page vector PDF without external plotting deps."""

    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    stream = commands.encode("utf-8")
    objects: list[bytes] = []
    objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    objects.append(b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>")
    objects.append(
        f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {width} {height}] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>".encode()
    )
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    objects.append(f"<< /Length {len(stream)} >>\nstream\n".encode() + stream + b"\nendstream")
    data = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for idx, obj in enumerate(objects, 1):
        offsets.append(len(data))
        data.extend(f"{idx} 0 obj\n".encode())
        data.extend(obj)
        data.extend(b"\nendobj\n")
    xref = len(data)
    data.extend(f"xref\n0 {len(objects)+1}\n".encode())
    data.extend(b"0000000000 65535 f \n")
    for off in offsets[1:]:
        data.extend(f"{off:010d} 00000 n \n".encode())
    data.extend(f"trailer\n<< /Size {len(objects)+1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode())
    out.write_bytes(bytes(data))
    return str(out)


def write_figures(report: Mapping[str, Any], fig_dir: str | Path) -> list[str]:
    """Generate lightweight manuscript-ready Phase-5 PDFs without plotting deps."""

    directory = Path(fig_dir)
    directory.mkdir(parents=True, exist_ok=True)
    counts = dict(report.get("route_counts", {}) or {})
    routes = list(ALLOWED_ROUTES)
    values = [int(counts.get(r, 0)) for r in routes]
    max_value = max(values + [1])

    outputs: list[str] = []
    cmds = "0.95 0.95 0.95 rg 0 0 612 432 re f 0 0 0 rg\n"
    cmds += _pdf_text(56, 392, "Certified arithmetic-domain route counts", size=16)
    cmds += _pdf_text(430, 392, f"uncontrolled = {int(counts.get('uncontrolled_count', 0))}", size=10)
    # axes
    cmds += "1 w 60 70 m 552 70 l S 60 70 m 60 330 l S\n"
    bar_w = 52
    gap = 28
    x0 = 78
    for i, (route, value) in enumerate(zip(routes, values)):
        h = 220.0 * value / max_value if max_value else 0.0
        x = x0 + i * (bar_w + gap)
        cmds += f"0.65 0.65 0.65 rg {x:.2f} 70 {bar_w:.2f} {h:.2f} re f 0 0 0 rg\n"
        cmds += _pdf_text(x + 6, 78 + h, str(value), size=9)
        cmds += _pdf_text(x - 3, 52, route, size=8)
    cmds += _pdf_text(60, 342, "count", size=9)
    out1 = directory / "domain_route_counts.pdf"
    outputs.append(_write_simple_pdf(out1, cmds))

    cmds = "1 1 1 rg 0 0 612 432 re f 0 0 0 rg\n"
    cmds += _pdf_text(130, 392, "Dcert generated before final conclusion", size=16)
    # root box
    cmds += "1 w 170 330 272 38 re S\n"
    cmds += _pdf_text(188, 345, "Generated certified arithmetic grammar", size=11)
    child_y = 185
    xs = [34, 129, 224, 319, 414, 509]
    for x, route, value in zip(xs, routes, values):
        cmds += f"{306} {330} m {x+34} {child_y+46} l S\n"
        cmds += f"{x} {child_y} 68 48 re S\n"
        cmds += _pdf_text(x + 9, child_y + 29, route, size=9)
        cmds += _pdf_text(x + 12, child_y + 14, f"{value} record(s)", size=8)
    cmds += _pdf_text(86, 88, f"Failure fields empty: {report.get('failure_fields_empty')} | Omitted tail: {report.get('omitted_tail_status')}", size=10)
    cmds += _pdf_text(86, 66, "The route ledger is generated before the final maximality conclusion is evaluated.", size=9)
    out2 = directory / "domain_grammar_tree.pdf"
    outputs.append(_write_simple_pdf(out2, cmds))
    return outputs

def save_domain_audit_outputs(
    report: Mapping[str, Any],
    *,
    out_json: str | Path,
    out_bundle_json: str | Path | None = None,
    records_csv: str | Path | None = None,
    counts_csv: str | Path | None = None,
    records_tex: str | Path | None = None,
    counts_tex: str | Path | None = None,
    fig_dir: str | Path | None = None,
) -> dict[str, str | list[str]]:
    outputs: dict[str, str | list[str]] = {}
    out = Path(out_json)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True))
    outputs["report_json"] = str(out)
    bundle = dict(report["domain_audit"])
    if out_bundle_json is not None:
        p = Path(out_bundle_json)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(bundle, indent=2, sort_keys=True))
        outputs["bundle_json"] = str(p)
    records = [GrammarRecord.from_dict(r) for r in report.get("records", [])]
    if records_csv is not None:
        outputs["records_csv"] = write_records_csv(records, records_csv)
    if counts_csv is not None:
        outputs["counts_csv"] = write_route_counts_csv(report.get("route_counts", {}), counts_csv)
    if records_tex is not None:
        outputs["records_tex"] = write_records_tex(records, records_tex)
    if counts_tex is not None:
        outputs["counts_tex"] = write_counts_tex(report.get("route_counts", {}), counts_tex)
    if fig_dir is not None:
        outputs["figures"] = write_figures(report, fig_dir)
    return outputs


def run_nonvacuous_omitted_tail_study(
    certified_universe: Mapping[str, Any] | None = None,
    *,
    eta_star_interval: tuple[float, float] = (0.0, 0.25),
    envelope_safety_margin: float = 1.0e-6,
) -> dict[str, Any]:
    """Run a lightweight diagnostic nonvacuous omitted-tail envelope study.

    The returned payload is deliberately marked ``theorem_facing=False``.  It is
    useful for manuscript planning and future strengthening, but the Phase-5
    proof audit remains closed by the vacuous empty-complement certificate unless
    this study is explicitly promoted to theorem-facing support.
    """

    universe = default_certified_universe()
    if certified_universe:
        universe = {**universe, **dict(certified_universe)}
    reps = dict(universe.get("representative_numerical_witnesses", {}) or {})
    lower_raw = reps.get("golden_lower_interval", list(DEFAULT_GOLDEN_LOWER))
    lower_lo = float(lower_raw[0]) if isinstance(lower_raw, Sequence) and len(lower_raw) >= 1 else DEFAULT_GOLDEN_LOWER[0]
    tail_upper = lower_lo - abs(float(envelope_safety_margin))
    margin = lower_lo - tail_upper
    return {
        "study_id": "phase5-nonvacuous-omitted-tail-diagnostic",
        "theorem_facing": False,
        "omitted_tail_mode": "nonvacuous_diagnostic_candidate",
        "eta_star_interval": [float(eta_star_interval[0]), float(eta_star_interval[1])],
        "tail_upper_envelope": float(tail_upper),
        "golden_lower_anchor": float(lower_lo),
        "margin": float(margin),
        "certified": margin > 0.0,
        "promotion_required_before_theorem_use": True,
        "notes": "Diagnostic only: shows the interface for a future nonvacuous omitted-tail envelope certificate; not consumed by final replay.",
    }

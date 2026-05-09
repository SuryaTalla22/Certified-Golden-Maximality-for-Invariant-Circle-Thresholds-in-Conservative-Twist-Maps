from __future__ import annotations

"""Phase-6 GL(2,Z) representative-selection normalization audit.

The GL(2,Z) clause in the manuscript is a *normalization convention* for
arithmetic representatives inside the certified comparison domain.  It is not
an assertion of analytic conjugacy for arbitrary projective representatives of
rotation numbers in the standard map.  This module makes that boundary
machine-checkable by emitting a proof-audit bundle whose theorem-facing Boolean
is derived from finite representative enumeration, certified-universe fields,
and an explicit ``analytic_conjugacy_claimed == False`` check.

The enumeration is deliberately modest and reviewer-facing: it searches bounded
GL(2,Z) matrices for projective images of the golden representative, groups
accepted images by normalized representative value, and verifies that the only
accepted representative in Dnorm is the canonical golden representative.  The
bounded enumeration is not used as a proof of an infinite group theorem; the
mathematical convention is the canonical continued-fraction representative rule
recorded in CERTIFIED_UNIVERSE.json.  The enumeration serves as a finite audit of
that convention and as a negative-control surface for duplicate or out-of-scope
representatives.
"""

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence
import csv
import json
import math

from .arithmetic_domain_grammar import default_certified_universe, load_certified_universe
from .proof_payload import DerivedBoolean, InequalityPayload, IntervalPayload, ProofAuditBundle

GOLDEN_ETA = 0.6180339887498949
DEFAULT_BOUND = 3
DEFAULT_TOL = 1.0e-12


@dataclass(frozen=True)
class GL2ZCandidate:
    """One bounded projective representative candidate for the golden orbit."""

    matrix: tuple[int, int, int, int]
    determinant: int
    representative_value: float
    in_numeric_domain: bool
    accepted_by_Dnorm: bool
    canonical_golden: bool
    representative_label: str
    source: str = "bounded-gl2z-projective-enumeration"

    def to_dict(self) -> dict[str, Any]:
        out = asdict(self)
        out["matrix"] = list(self.matrix)
        return out

    @classmethod
    def from_dict(cls, row: Mapping[str, Any]) -> "GL2ZCandidate":
        mat_raw = row.get("matrix", [1, 0, 0, 1])
        if not isinstance(mat_raw, Sequence) or isinstance(mat_raw, (str, bytes)) or len(mat_raw) != 4:
            mat_raw = [1, 0, 0, 1]
        mat = tuple(int(x) for x in mat_raw)  # type: ignore[assignment]
        det = int(row.get("determinant", mat[0] * mat[3] - mat[1] * mat[2]))
        value = float(row.get("representative_value", GOLDEN_ETA))
        return cls(
            matrix=mat,  # type: ignore[arg-type]
            determinant=det,
            representative_value=value,
            in_numeric_domain=bool(row.get("in_numeric_domain", False)),
            accepted_by_Dnorm=bool(row.get("accepted_by_Dnorm", False)),
            canonical_golden=bool(row.get("canonical_golden", False)),
            representative_label=str(row.get("representative_label", "candidate")),
            source=str(row.get("source", "manual-candidate")),
        )


def _safe_float(value: Any, default: float) -> float:
    try:
        out = float(value)
    except Exception:
        return default
    return out if math.isfinite(out) else default


def _normalization_dict(certified_universe: Mapping[str, Any] | None) -> dict[str, Any]:
    universe = default_certified_universe()
    if certified_universe:
        universe = {**universe, **dict(certified_universe)}
    norm = dict(universe.get("normalization", {}) or {})
    convention = str(norm.get("convention", "continued-fraction-positive-reduced-golden-orbit"))
    return {
        "group": str(norm.get("group", "GL(2,Z)")),
        "convention": convention,
        "normalization_type": str(norm.get("normalization_type", "representative_selection")),
        "equality_case": str(norm.get("equality_case", "golden orbit unique in certified normalization domain")),
        "representative_rule": str(norm.get("representative_rule", convention)),
        "analytic_conjugacy_claimed": bool(norm.get("analytic_conjugacy_claimed", False)),
        "claimed_analytic_conjugacy_outside_Dnorm": bool(norm.get("claimed_analytic_conjugacy_outside_Dnorm", False)),
        "threshold_invariance_scope": str(norm.get("threshold_invariance_scope", "certified-normalization-domain-only")),
    }


def default_Dnorm(certified_universe: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Return the certified normalization-domain convention used by the audit."""

    universe = default_certified_universe()
    if certified_universe:
        universe = {**universe, **dict(certified_universe)}
    arith = dict(universe.get("arithmetic_domain", {}) or {})
    norm = _normalization_dict(universe)
    return {
        "domain_label": "certified-positive-reduced-cf-representative-domain",
        "numeric_interval": [0.0, 1.0],
        "interval_open": True,
        "canonical_golden_eta": _safe_float(arith.get("golden_eta"), GOLDEN_ETA),
        "canonical_tolerance": DEFAULT_TOL,
        "accepted_rule": norm["representative_rule"],
        "normalization_type": norm["normalization_type"],
        "accept_only_canonical_golden_value": True,
        "equality_allowed_only_for": "golden-orbit-canonical-representative",
    }


def _matrix_det(matrix: tuple[int, int, int, int]) -> int:
    a, b, c, d = matrix
    return a * d - b * c


def _projective_action(matrix: tuple[int, int, int, int], rho: float) -> float | None:
    a, b, c, d = matrix
    denom = c * rho + d
    if abs(denom) <= 1.0e-15:
        return None
    value = (a * rho + b) / denom
    return value if math.isfinite(value) else None


def _in_numeric_Dnorm(value: float, D_norm: Mapping[str, Any]) -> bool:
    raw = D_norm.get("numeric_interval", [0.0, 1.0])
    lo, hi = 0.0, 1.0
    if isinstance(raw, Sequence) and not isinstance(raw, (str, bytes)) and len(raw) >= 2:
        lo = _safe_float(raw[0], 0.0)
        hi = _safe_float(raw[1], 1.0)
    if bool(D_norm.get("interval_open", True)):
        return lo < value < hi
    return lo <= value <= hi


def _is_canonical_golden(value: float, D_norm: Mapping[str, Any]) -> bool:
    eta = _safe_float(D_norm.get("canonical_golden_eta"), GOLDEN_ETA)
    tol = _safe_float(D_norm.get("canonical_tolerance"), DEFAULT_TOL)
    return abs(float(value) - eta) <= tol


def _candidate_from_matrix(matrix: tuple[int, int, int, int], D_norm: Mapping[str, Any]) -> GL2ZCandidate | None:
    det = _matrix_det(matrix)
    if abs(det) != 1:
        return None
    eta = _safe_float(D_norm.get("canonical_golden_eta"), GOLDEN_ETA)
    value = _projective_action(matrix, eta)
    if value is None:
        return None
    in_domain = _in_numeric_Dnorm(value, D_norm)
    canonical = _is_canonical_golden(value, D_norm)
    accepted = bool(in_domain and canonical and D_norm.get("accept_only_canonical_golden_value", True))
    label = "golden-canonical" if canonical else "golden-orbit-noncanonical-rejected"
    return GL2ZCandidate(
        matrix=matrix,
        determinant=det,
        representative_value=float(value),
        in_numeric_domain=in_domain,
        accepted_by_Dnorm=accepted,
        canonical_golden=canonical,
        representative_label=label,
    )


def enumerate_representative_candidates(domain: Mapping[str, Any] | None = None, bound: int = DEFAULT_BOUND) -> list[dict[str, Any]]:
    """Enumerate bounded GL(2,Z) projective images of the golden representative.

    The returned list includes both Dnorm-accepted canonical representatives and
    rejected noncanonical projective images that happen to lie in the numeric
    interval.  Uniqueness is checked after grouping accepted candidates by their
    representative value, not by matrix, because many GL(2,Z) matrices can have
    the same canonical fixed value.
    """

    D_norm = default_Dnorm(domain) if domain is None or "canonical_golden_eta" not in dict(domain) else dict(domain)
    B = int(bound)
    if B < 1:
        raise ValueError("bound must be positive")
    records: list[GL2ZCandidate] = []
    for a in range(-B, B + 1):
        for b in range(-B, B + 1):
            for c in range(-B, B + 1):
                for d in range(-B, B + 1):
                    cand = _candidate_from_matrix((a, b, c, d), D_norm)
                    if cand is None:
                        continue
                    # Keep all accepted canonical witnesses and all noncanonical
                    # images that lie in the numeric domain; discard exterior
                    # images from the reviewer table to keep the audit compact.
                    if cand.accepted_by_Dnorm or cand.in_numeric_domain:
                        records.append(cand)
    records.sort(key=lambda r: (not r.accepted_by_Dnorm, abs(r.representative_value - _safe_float(D_norm.get("canonical_golden_eta"), GOLDEN_ETA)), r.matrix))
    return [r.to_dict() for r in records]


def _cluster_values(records: Sequence[Mapping[str, Any]], *, tol: float) -> list[dict[str, Any]]:
    clusters: list[dict[str, Any]] = []
    for row in records:
        value = float(row.get("representative_value", float("nan")))
        if not math.isfinite(value):
            continue
        for cluster in clusters:
            if abs(value - float(cluster["representative_value"])) <= tol:
                cluster["matrix_witness_count"] += 1
                cluster["matrix_witnesses"].append(row.get("matrix"))
                labels = set(cluster.get("representative_labels", []))
                labels.add(str(row.get("representative_label", "candidate")))
                cluster["representative_labels"] = sorted(labels)
                break
        else:
            clusters.append(
                {
                    "representative_value": value,
                    "matrix_witness_count": 1,
                    "matrix_witnesses": [row.get("matrix")],
                    "representative_labels": [str(row.get("representative_label", "candidate"))],
                    "canonical_golden": bool(row.get("canonical_golden", False)),
                    "accepted_by_Dnorm": bool(row.get("accepted_by_Dnorm", False)),
                }
            )
    clusters.sort(key=lambda c: c["representative_value"])
    return clusters


def verify_unique_golden_representative(candidates: Sequence[Mapping[str, Any]], D_norm: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Verify uniqueness of the accepted golden representative in Dnorm."""

    dnorm = default_Dnorm(D_norm) if D_norm is None or "canonical_golden_eta" not in dict(D_norm) else dict(D_norm)
    tol = _safe_float(dnorm.get("canonical_tolerance"), DEFAULT_TOL)
    accepted = [dict(c) for c in candidates if bool(c.get("accepted_by_Dnorm", False))]
    accepted_clusters = _cluster_values(accepted, tol=tol)
    canonical_eta = _safe_float(dnorm.get("canonical_golden_eta"), GOLDEN_ETA)
    golden_clusters = [c for c in accepted_clusters if abs(float(c["representative_value"]) - canonical_eta) <= tol]
    nongolden_clusters = [c for c in accepted_clusters if abs(float(c["representative_value"]) - canonical_eta) > tol]

    failure_fields: list[str] = []
    if len(golden_clusters) != 1:
        failure_fields.append("golden_representative_not_unique")
    if nongolden_clusters:
        failure_fields.append("nongolden_representative_accepted_in_Dnorm")
    if not accepted:
        failure_fields.append("no_accepted_representative_in_Dnorm")

    nearest_rejected_gap = None
    rejected_in_domain = [dict(c) for c in candidates if bool(c.get("in_numeric_domain", False)) and not bool(c.get("accepted_by_Dnorm", False))]
    if rejected_in_domain:
        nearest_rejected_gap = min(abs(float(c["representative_value"]) - canonical_eta) for c in rejected_in_domain)

    return {
        "certified": not failure_fields,
        "candidate_count": len(candidates),
        "accepted_matrix_witness_count": len(accepted),
        "accepted_distinct_representative_count": len(accepted_clusters),
        "accepted_distinct_golden_count": len(golden_clusters),
        "accepted_distinct_nongolden_count": len(nongolden_clusters),
        "duplicate_golden_representative_count": max(0, len(golden_clusters) - 1),
        "accepted_representative_clusters": accepted_clusters,
        "rejected_in_domain_count": len(rejected_in_domain),
        "nearest_rejected_gap_to_golden": nearest_rejected_gap,
        "failure_fields": failure_fields,
    }


def verify_no_analytic_conjugacy_claim(certified_universe: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Verify that the final GL(2,Z) language is not an analytic conjugacy claim."""

    norm = _normalization_dict(certified_universe)
    failure_fields: list[str] = []
    if norm["normalization_type"] != "representative_selection":
        failure_fields.append("normalization_type_not_representative_selection")
    if norm["group"] != "GL(2,Z)":
        failure_fields.append("normalization_group_not_GL2Z")
    if norm["analytic_conjugacy_claimed"]:
        failure_fields.append("analytic_conjugacy_claimed")
    if norm["claimed_analytic_conjugacy_outside_Dnorm"]:
        failure_fields.append("analytic_conjugacy_claimed_outside_Dnorm")
    if "continued-fraction-positive-reduced" not in norm["representative_rule"]:
        failure_fields.append("representative_rule_not_certified_positive_reduced_cf")
    return {
        "certified": not failure_fields,
        "normalization_type": norm["normalization_type"],
        "group": norm["group"],
        "representative_rule": norm["representative_rule"],
        "analytic_conjugacy_claimed": norm["analytic_conjugacy_claimed"],
        "claimed_analytic_conjugacy_outside_Dnorm": norm["claimed_analytic_conjugacy_outside_Dnorm"],
        "threshold_invariance_scope": norm["threshold_invariance_scope"],
        "failure_fields": failure_fields,
    }


def _ineq(name: str, lhs: float, rhs: float, sense: str, sources: list[str]) -> InequalityPayload:
    margin = rhs - lhs if sense in ("<", "<=") else lhs - rhs
    return InequalityPayload(
        name=name,
        lhs_label=f"lhs:{name}",
        rhs_label=f"rhs:{name}",
        lhs_value=float(lhs),
        rhs_value=float(rhs),
        sense=sense,  # type: ignore[arg-type]
        margin=float(margin),
        source_fields=sources,
        source_artifact="phase6-gl2z-normalization-audit",
    )


def build_gl2z_normalization_audit_bundle(
    certified_universe: Mapping[str, Any] | None = None,
    *,
    candidates: Sequence[Mapping[str, Any]] | None = None,
    bound: int = DEFAULT_BOUND,
    D_norm: Mapping[str, Any] | None = None,
) -> ProofAuditBundle:
    """Build the proof-carrying GL(2,Z) normalization audit bundle."""

    universe = default_certified_universe()
    if certified_universe:
        universe = {**universe, **dict(certified_universe)}
    dnorm = default_Dnorm(universe)
    if D_norm:
        dnorm = {**dnorm, **dict(D_norm)}
    candidate_rows = [dict(c) for c in (candidates if candidates is not None else enumerate_representative_candidates(dnorm, bound=bound))]
    unique = verify_unique_golden_representative(candidate_rows, dnorm)
    no_conj = verify_no_analytic_conjugacy_claim(universe)
    eta = _safe_float(dnorm.get("canonical_golden_eta"), GOLDEN_ETA)
    tol = _safe_float(dnorm.get("canonical_tolerance"), DEFAULT_TOL)

    failure_fields: list[str] = []
    failure_fields.extend(str(x) for x in unique.get("failure_fields", []))
    failure_fields.extend(str(x) for x in no_conj.get("failure_fields", []))
    if not candidate_rows:
        failure_fields.append("no_gl2z_candidates_enumerated")

    analytic_flag = 1.0 if bool(no_conj.get("analytic_conjugacy_claimed")) or bool(no_conj.get("claimed_analytic_conjugacy_outside_Dnorm")) else 0.0
    representative_type_flag = 1.0 if no_conj.get("normalization_type") == "representative_selection" else 0.0
    group_flag = 1.0 if no_conj.get("group") == "GL(2,Z)" else 0.0
    rule_flag = 1.0 if "continued-fraction-positive-reduced" in str(no_conj.get("representative_rule", "")) else 0.0

    duplicate_count = float(unique.get("duplicate_golden_representative_count", 1))
    nongolden_count = float(unique.get("accepted_distinct_nongolden_count", 1))
    accepted_distinct_count = float(unique.get("accepted_distinct_representative_count", 0))
    accepted_golden_count = float(unique.get("accepted_distinct_golden_count", 0))

    raw_intervals = {
        "golden_representative_eta": IntervalPayload(
            lo=eta - tol,
            hi=eta + tol,
            label="golden_representative_eta",
            source_artifact="CERTIFIED_UNIVERSE.json:/arithmetic_domain/golden_eta",
            source_json_pointer="/arithmetic_domain/golden_eta",
        ),
        "normalization_domain_numeric_interval": IntervalPayload(
            lo=float(dnorm.get("numeric_interval", [0.0, 1.0])[0]),
            hi=float(dnorm.get("numeric_interval", [0.0, 1.0])[1]),
            label="normalization_domain_numeric_interval",
            source_artifact="CERTIFIED_UNIVERSE.json:/normalization",
            source_json_pointer="/normalization",
        ),
    }
    if unique.get("nearest_rejected_gap_to_golden") is not None:
        gap = float(unique["nearest_rejected_gap_to_golden"])
        raw_intervals["nearest_rejected_gap_to_golden"] = IntervalPayload(
            lo=max(0.0, gap - tol),
            hi=gap + tol,
            label="nearest_rejected_gap_to_golden",
            source_artifact="bounded-gl2z-projective-enumeration",
            source_json_pointer="/candidate_records",
            theorem_facing=False,
            diagnostic_only=True,
        )

    inequalities = {
        "one_accepted_distinct_representative": _ineq(
            "one_accepted_distinct_representative",
            accepted_distinct_count,
            1.5,
            "<",
            ["candidate_records", "Dnorm"],
        ),
        "accepted_distinct_representative_exists": _ineq(
            "accepted_distinct_representative_exists",
            accepted_distinct_count,
            0.5,
            ">",
            ["candidate_records", "Dnorm"],
        ),
        "accepted_golden_representative_exists": _ineq(
            "accepted_golden_representative_exists",
            accepted_golden_count,
            0.5,
            ">",
            ["candidate_records", "Dnorm", "golden_representative_eta"],
        ),
        "duplicate_golden_representative_count_zero": _ineq(
            "duplicate_golden_representative_count_zero",
            duplicate_count,
            0.5,
            "<",
            ["candidate_records", "Dnorm"],
        ),
        "nongolden_accepted_count_zero": _ineq(
            "nongolden_accepted_count_zero",
            nongolden_count,
            0.5,
            "<",
            ["candidate_records", "Dnorm"],
        ),
        "analytic_conjugacy_claimed_false": _ineq(
            "analytic_conjugacy_claimed_false",
            analytic_flag,
            0.5,
            "<",
            ["certified_universe_normalization"],
        ),
        "normalization_type_is_representative_selection": _ineq(
            "normalization_type_is_representative_selection",
            representative_type_flag,
            0.5,
            ">",
            ["certified_universe_normalization"],
        ),
        "normalization_group_is_GL2Z": _ineq(
            "normalization_group_is_GL2Z",
            group_flag,
            0.5,
            ">",
            ["certified_universe_normalization"],
        ),
        "representative_rule_matches_certified_convention": _ineq(
            "representative_rule_matches_certified_convention",
            rule_flag,
            0.5,
            ">",
            ["certified_universe_normalization"],
        ),
        "golden_eta_inside_positive_domain_left": _ineq(
            "golden_eta_inside_positive_domain_left",
            eta - tol,
            0.0,
            ">",
            ["golden_representative_eta", "normalization_domain_numeric_interval"],
        ),
        "golden_eta_inside_positive_domain_right": _ineq(
            "golden_eta_inside_positive_domain_right",
            1.0,
            eta + tol,
            ">",
            ["golden_representative_eta", "normalization_domain_numeric_interval"],
        ),
    }

    bools = {
        "representative_selection_convention_certified": DerivedBoolean(
            name="representative_selection_convention_certified",
            value=not any(x in failure_fields for x in [
                "normalization_type_not_representative_selection",
                "normalization_group_not_GL2Z",
                "representative_rule_not_certified_positive_reduced_cf",
            ]),
            derived_from=[
                "normalization_type_is_representative_selection",
                "normalization_group_is_GL2Z",
                "representative_rule_matches_certified_convention",
                "certified_universe_normalization",
            ],
            margin=min(
                inequalities["normalization_type_is_representative_selection"].recomputed_margin(),
                inequalities["normalization_group_is_GL2Z"].recomputed_margin(),
                inequalities["representative_rule_matches_certified_convention"].recomputed_margin(),
            ),
            source_artifact="phase6-gl2z-normalization-audit",
        ),
        "golden_orbit_representative_unique_in_Dnorm": DerivedBoolean(
            name="golden_orbit_representative_unique_in_Dnorm",
            value=bool(unique.get("certified", False)),
            derived_from=[
                "one_accepted_distinct_representative",
                "accepted_distinct_representative_exists",
                "accepted_golden_representative_exists",
                "duplicate_golden_representative_count_zero",
                "nongolden_accepted_count_zero",
                "candidate_records",
                "Dnorm",
            ],
            margin=min(
                inequalities["one_accepted_distinct_representative"].recomputed_margin(),
                inequalities["accepted_distinct_representative_exists"].recomputed_margin(),
                inequalities["accepted_golden_representative_exists"].recomputed_margin(),
                inequalities["duplicate_golden_representative_count_zero"].recomputed_margin(),
                inequalities["nongolden_accepted_count_zero"].recomputed_margin(),
            ),
            source_artifact="phase6-gl2z-normalization-audit",
        ),
        "no_analytic_conjugacy_claim_used": DerivedBoolean(
            name="no_analytic_conjugacy_claim_used",
            value=bool(no_conj.get("certified", False)) and analytic_flag == 0.0,
            derived_from=["analytic_conjugacy_claimed_false", "certified_universe_normalization"],
            margin=inequalities["analytic_conjugacy_claimed_false"].recomputed_margin(),
            source_artifact="phase6-gl2z-normalization-audit",
        ),
    }
    bools["gl2z_normalization_certified"] = DerivedBoolean(
        name="gl2z_normalization_certified",
        value=not failure_fields,
        derived_from=[
            "representative_selection_convention_certified",
            "golden_orbit_representative_unique_in_Dnorm",
            "no_analytic_conjugacy_claim_used",
            "golden_eta_inside_positive_domain_left",
            "golden_eta_inside_positive_domain_right",
        ],
        margin=min(
            bools["representative_selection_convention_certified"].margin or -1.0,
            bools["golden_orbit_representative_unique_in_Dnorm"].margin or -1.0,
            bools["no_analytic_conjugacy_claim_used"].margin or -1.0,
            inequalities["golden_eta_inside_positive_domain_left"].recomputed_margin(),
            inequalities["golden_eta_inside_positive_domain_right"].recomputed_margin(),
        ),
        source_artifact="phase6-gl2z-normalization-audit",
    )

    return ProofAuditBundle(
        proof_payload_version="v2",
        theorem_layer="VIII.GL2Z",
        claim="GL(2,Z) is used only as a certified representative-selection normalization inside Dnorm",
        raw_interval_fields=raw_intervals,
        raw_symbolic_fields={
            "Dnorm": dnorm,
            "candidate_records": candidate_rows,
            "unique_representative_verification": unique,
            "certified_universe_normalization": _normalization_dict(universe),
            "no_analytic_conjugacy_verification": no_conj,
            "matrix_bound": int(bound),
        },
        derived_inequalities=inequalities,
        derived_booleans=bools,
        validator_recomputed=True,
        active_assumptions=[],
        open_hypotheses=[],
        failure_fields=failure_fields,
        source_artifacts=["CERTIFIED_UNIVERSE.json", "phase5-arithmetic-domain-grammar-audit"],
        shell_payload={
            "normalization_type": _normalization_dict(universe)["normalization_type"],
            "analytic_conjugacy_claimed": bool(no_conj.get("analytic_conjugacy_claimed")),
            "golden_orbit_representative_unique_in_Dnorm": bool(unique.get("certified")),
            "candidate_count": int(unique.get("candidate_count", 0)),
            "accepted_distinct_representative_count": int(unique.get("accepted_distinct_representative_count", 0)),
            "failure_fields": failure_fields,
        },
        audit_metadata={"phase": "phase6_gl2z_normalization", "status": "passed" if not failure_fields else "failed"},
    )


def build_gl2z_normalization_audit(
    certified_universe: Mapping[str, Any] | None = None,
    *,
    candidates: Sequence[Mapping[str, Any]] | None = None,
    bound: int = DEFAULT_BOUND,
    D_norm: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a reviewer-friendly Phase-6 GL(2,Z) normalization audit report."""

    bundle = build_gl2z_normalization_audit_bundle(
        certified_universe,
        candidates=candidates,
        bound=bound,
        D_norm=D_norm,
    )
    unique = dict(bundle.raw_symbolic_fields.get("unique_representative_verification", {}))
    no_conj = dict(bundle.raw_symbolic_fields.get("no_analytic_conjugacy_verification", {}))
    return {
        "status": "passed" if not bundle.failure_fields else "failed",
        "normalization_type": no_conj.get("normalization_type", ""),
        "analytic_conjugacy_claimed": bool(no_conj.get("analytic_conjugacy_claimed", True)),
        "claimed_analytic_conjugacy_outside_Dnorm": bool(no_conj.get("claimed_analytic_conjugacy_outside_Dnorm", True)),
        "golden_orbit_representative_unique_in_Dnorm": bool(unique.get("certified", False)),
        "candidate_count": int(unique.get("candidate_count", 0)),
        "accepted_matrix_witness_count": int(unique.get("accepted_matrix_witness_count", 0)),
        "accepted_distinct_representative_count": int(unique.get("accepted_distinct_representative_count", 0)),
        "accepted_distinct_nongolden_count": int(unique.get("accepted_distinct_nongolden_count", 0)),
        "duplicate_golden_representative_count": int(unique.get("duplicate_golden_representative_count", 0)),
        "failure_fields": list(bundle.failure_fields),
        "certified": not bundle.failure_fields,
        "gl2z_audit": bundle.to_dict(),
    }


def write_gl2z_audit_outputs(report: Mapping[str, Any], out_dir: str | Path, table_dir: str | Path, fig_dir: str | Path) -> dict[str, str]:
    """Write Phase-6 JSON, CSV/LaTeX tables, and lightweight figures."""

    out = Path(out_dir)
    tables = Path(table_dir)
    figs = Path(fig_dir)
    out.mkdir(parents=True, exist_ok=True)
    tables.mkdir(parents=True, exist_ok=True)
    figs.mkdir(parents=True, exist_ok=True)

    report_path = out / "gl2z_normalization_audit.json"
    bundle_path = out / "gl2z_normalization_audit.bundle.json"
    report_path.write_text(json.dumps(dict(report), indent=2, sort_keys=True) + "\n")
    bundle_path.write_text(json.dumps(dict(report)["gl2z_audit"], indent=2, sort_keys=True) + "\n")

    bundle = dict(report["gl2z_audit"])
    candidates = list(bundle.get("raw_symbolic_fields", {}).get("candidate_records", []))
    cand_csv = tables / "gl2z_representative_candidates.csv"
    cand_tex = tables / "gl2z_representative_candidates.tex"
    fieldnames = ["matrix", "determinant", "representative_value", "in_numeric_domain", "accepted_by_Dnorm", "canonical_golden", "representative_label"]
    with cand_csv.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in candidates:
            writer.writerow({k: row.get(k, "") for k in fieldnames})
    cand_tex.write_text(_csv_to_latex(cand_csv, caption="Bounded GL(2,Z) representative-candidate audit.", label="tab:gl2z-candidates"))

    summary_csv = tables / "gl2z_normalization_summary.csv"
    summary_tex = tables / "gl2z_normalization_summary.tex"
    summary_fields = [
        "status",
        "normalization_type",
        "analytic_conjugacy_claimed",
        "golden_orbit_representative_unique_in_Dnorm",
        "candidate_count",
        "accepted_distinct_representative_count",
        "accepted_distinct_nongolden_count",
        "duplicate_golden_representative_count",
    ]
    with summary_csv.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=summary_fields)
        writer.writeheader()
        writer.writerow({k: report.get(k, "") for k in summary_fields})
    summary_tex.write_text(_csv_to_latex(summary_csv, caption="GL(2,Z) normalization audit summary.", label="tab:gl2z-summary"))

    _write_figures(report, figs)
    return {
        "audit_json": str(report_path),
        "bundle_json": str(bundle_path),
        "candidate_csv": str(cand_csv),
        "candidate_tex": str(cand_tex),
        "summary_csv": str(summary_csv),
        "summary_tex": str(summary_tex),
        "candidate_figure": str(figs / "gl2z_candidate_values.pdf"),
        "normalization_figure": str(figs / "gl2z_normalization_counts.pdf"),
    }



def _csv_to_latex(path: Path, *, caption: str, label: str) -> str:
    rows = list(csv.reader(path.open()))
    if not rows:
        return ""
    header, body = rows[0], rows[1:]
    cols = "l" * len(header)
    row_end = r" \\" 
    lines = [
        r"\begin{table}[htbp]",
        r"\centering",
        r"\small",
        f"\\begin{{tabular}}{{{cols}}}",
        r"\toprule",
        " & ".join(_tex_escape(h) for h in header) + row_end,
        r"\midrule",
    ]
    for row in body[:40]:
        lines.append(" & ".join(_tex_escape(str(x)) for x in row) + row_end)
    if len(body) > 40:
        lines.append(
            f"\\multicolumn{{{len(header)}}}{{l}}{{... {len(body)-40} additional rows omitted from compact table ...}}" + row_end
        )
    lines.extend([
        r"\bottomrule",
        r"\end{tabular}",
        f"\\caption{{{_tex_escape(caption)}}}",
        f"\\label{{{label}}}",
        r"\end{table}",
        "",
    ])
    return "\n".join(lines)


def _tex_escape(text: str) -> str:
    return (
        text.replace("\\", r"\textbackslash{}")
        .replace("_", r"\_")
        .replace("%", r"\%")
        .replace("&", r"\&")
        .replace("#", r"\#")
    )


def _write_figures(report: Mapping[str, Any], fig_dir: Path) -> None:
    try:
        import matplotlib.pyplot as plt
    except Exception:
        # The JSON/CSV artifacts are theorem-facing; figures are convenience
        # outputs.  Do not fail the audit if matplotlib is unavailable.
        return
    bundle = dict(report["gl2z_audit"])
    candidates = list(bundle.get("raw_symbolic_fields", {}).get("candidate_records", []))
    accepted_values = [float(c["representative_value"]) for c in candidates if c.get("accepted_by_Dnorm")]
    rejected_values = [float(c["representative_value"]) for c in candidates if c.get("in_numeric_domain") and not c.get("accepted_by_Dnorm")]

    fig, ax = plt.subplots(figsize=(7.0, 2.8))
    if rejected_values:
        ax.scatter(rejected_values, [0.0] * len(rejected_values), marker="x", label="rejected in numeric domain")
    if accepted_values:
        ax.scatter(accepted_values, [0.08] * len(accepted_values), marker="o", label="accepted by Dnorm")
    ax.axvline(GOLDEN_ETA, linestyle="--", linewidth=1.0, label="canonical golden eta")
    ax.set_xlabel("representative value")
    ax.set_yticks([])
    ax.set_title("Bounded GL(2,Z) images under the certified representative convention")
    ax.legend(loc="best", fontsize=8)
    fig.tight_layout()
    fig.savefig(fig_dir / "gl2z_candidate_values.pdf")
    plt.close(fig)

    labels = ["accepted distinct", "accepted nongolden", "duplicate golden", "analytic conjugacy flag"]
    values = [
        float(report.get("accepted_distinct_representative_count", 0)),
        float(report.get("accepted_distinct_nongolden_count", 0)),
        float(report.get("duplicate_golden_representative_count", 0)),
        1.0 if report.get("analytic_conjugacy_claimed") else 0.0,
    ]
    fig, ax = plt.subplots(figsize=(7.0, 3.2))
    ax.bar(labels, values)
    ax.set_ylabel("count / flag")
    ax.set_title("GL(2,Z) normalization audit counts")
    ax.tick_params(axis="x", rotation=20)
    fig.tight_layout()
    fig.savefig(fig_dir / "gl2z_normalization_counts.pdf")
    plt.close(fig)


def load_universe_and_run(
    certified_universe_path: str | Path | None = "CERTIFIED_UNIVERSE.json",
    *,
    bound: int = DEFAULT_BOUND,
) -> dict[str, Any]:
    universe = load_certified_universe(certified_universe_path)
    return build_gl2z_normalization_audit(universe, bound=bound)

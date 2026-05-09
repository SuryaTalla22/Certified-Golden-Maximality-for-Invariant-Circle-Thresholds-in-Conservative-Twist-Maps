from __future__ import annotations

"""Phase-2C lower-anchor regeneration attempt utilities.

This module is the honest follow-up to Phase 2B.  It drives the existing
finite-dimensional invariant-circle validators across the missing interval
between the cached lower-corridor endpoint and the near-critical golden lower
anchor, writes a candidate-shaped JSON file, and records why that file is or is
not promotable.

The default output is deliberately diagnostic-only.  A positive collocation
Newton/radii margin at a near-critical K value is useful evidence, but it is not
by itself an infinite-dimensional KAM certificate.  The module therefore refuses
to mark an output theorem-facing unless every segment also carries a positive
analytic theorem-closure margin.
"""

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Mapping, Sequence
import csv
import json
import math
import time

DEFAULT_EXISTING_RIGHT = 0.265
DEFAULT_FINAL_ANCHOR = (0.9716350, 0.9716360)
GOLDEN_INVERSE = (math.sqrt(5.0) - 1.0) / 2.0


@dataclass(frozen=True)
class LowerAnchorRegenerationConfig:
    start_K: float = DEFAULT_EXISTING_RIGHT
    final_anchor_lo: float = DEFAULT_FINAL_ANCHOR[0]
    final_anchor_hi: float = DEFAULT_FINAL_ANCHOR[1]
    n_segments: int = 10
    overlap: float = 1.0e-7
    N: int = 32
    oversample_factor: int = 2
    include_analytic_probe: bool = True
    analytic_probe_N_values: tuple[int, ...] = (32, 64)
    analytic_probe_at: tuple[str, ...] = ("last",)
    sigma_cap: float = 0.02
    theorem_facing_policy: str = "require-positive-analytic-margin"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class LowerAnchorValidationRecord:
    segment_id: str
    K_lo: float
    K_hi: float
    K_mid: float
    N: int
    finite_success: bool
    eta: float
    B_norm: float
    lipschitz_bound: float
    radius_r: float
    finite_radii_margin: float
    contraction_bound: float
    residual_inf: float
    residual_l2: float
    oversampled_residual_inf: float
    fourier_tail_l2: float
    bridge_quality: str
    solver_iterations: int
    elapsed_seconds: float
    analytic_probe_attempted: bool = False
    analytic_theorem_status: str | None = None
    analytic_theorem_margin: float | None = None
    weighted_residual_l1: float | None = None
    tail_bridge_bound_l1: float | None = None
    relative_correction_to_graph: float | None = None
    analytic_probe_failure: str | None = None
    closure_level: str = "finite_dimensional_collocation_only"
    theorem_ready: bool = False
    failure_reasons: list[str] = field(default_factory=list)

    @property
    def finite_radii_lhs(self) -> float:
        return float(self.radius_r - self.finite_radii_margin)

    @property
    def phase2b_linear_defect_Z(self) -> float:
        # Phase 2B expects lhs = Y + Z*r + T.  The finite collocation validator
        # uses eta + 0.5*B*L*r^2 < r, so for the fixed accepted radius we encode
        # Z := 0.5*B*L*r and T := 0.
        if not all(math.isfinite(x) for x in (self.B_norm, self.lipschitz_bound, self.radius_r)):
            return float("nan")
        return float(0.5 * self.B_norm * self.lipschitz_bound * self.radius_r)

    def to_candidate_row(self, *, source_artifact: str) -> dict[str, Any]:
        margin = float(self.radius_r - (self.eta + self.phase2b_linear_defect_Z * self.radius_r))
        return {
            "segment_id": self.segment_id,
            "K_lo": float(self.K_lo),
            "K_hi": float(self.K_hi),
            "K_mid": float(self.K_mid),
            "rho": float(GOLDEN_INVERSE),
            "N": int(self.N),
            "sigma": 0.0,
            "norm_name": "finite-dimensional-collocation-radii-polynomial",
            "residual_Y": float(self.eta),
            "linear_defect_Z": float(self.phase2b_linear_defect_Z),
            "tail_bound_T": 0.0,
            "radius_r": float(self.radius_r),
            "radii_margin": float(margin),
            "small_divisor_min": 5.0e-2,
            "small_divisor_inverse_bound": 2.0e1,
            "small_divisor_source": "diagnostic-default-golden-bound-not-theorem-facing",
            "source_module": "kam_theorem_suite.torus_validator.validate_invariant_circle_graph",
            "source_artifact": source_artifact,
            "certified": bool(self.finite_success and margin > 0.0),
            "finite_dimensional_only": True,
            "closure_level": self.closure_level,
            "theorem_ready": bool(self.theorem_ready),
            "analytic_probe_attempted": bool(self.analytic_probe_attempted),
            "analytic_theorem_status": self.analytic_theorem_status,
            "analytic_theorem_margin": self.analytic_theorem_margin,
            "failure_reasons": list(self.failure_reasons),
        }

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["finite_radii_lhs"] = self.finite_radii_lhs
        d["phase2b_linear_defect_Z"] = self.phase2b_linear_defect_Z
        return d


@dataclass(frozen=True)
class LowerAnchorRegenerationReport:
    schema: str
    status: str
    config: LowerAnchorRegenerationConfig
    records: list[LowerAnchorValidationRecord]
    candidate_path: str | None
    theorem_facing: bool
    diagnostic_only: bool
    promotion_allowed: bool
    theorem_ready_record_count: int
    finite_success_count: int
    final_anchor_reached_by_grid: bool
    min_finite_margin: float | None
    min_analytic_margin: float | None
    failure_fields: list[str]
    notes: str

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["config"] = self.config.to_dict()
        d["records"] = [r.to_dict() for r in self.records]
        return d


def build_overlapping_grid(*, start_K: float = DEFAULT_EXISTING_RIGHT, final_anchor_hi: float = DEFAULT_FINAL_ANCHOR[1], n_segments: int = 10, overlap: float = 1.0e-7) -> list[tuple[float, float, float]]:
    if n_segments <= 0:
        raise ValueError("n_segments must be positive")
    start_K = float(start_K)
    end_K = float(final_anchor_hi)
    if end_K <= start_K:
        raise ValueError("final_anchor_hi must be greater than start_K")
    edges = [start_K + (end_K - start_K) * i / n_segments for i in range(n_segments + 1)]
    rows: list[tuple[float, float, float]] = []
    for i in range(n_segments):
        lo = edges[i] - float(overlap)
        hi = edges[i + 1] if i == n_segments - 1 else edges[i + 1] + float(overlap)
        mid = 0.5 * (edges[i] + edges[i + 1])
        rows.append((float(lo), float(hi), float(mid)))
    return rows


def _finite_margin(val: Any) -> float:
    try:
        return float(val.radius - (val.eta + 0.5 * val.B_norm * val.lipschitz_bound * val.radius * val.radius))
    except Exception:
        return float("nan")


def _should_probe(index: int, count: int, probe_at: Sequence[str]) -> bool:
    labels = {str(x).lower() for x in probe_at}
    return "all" in labels or ("first" in labels and index == 0) or ("middle" in labels and index == count // 2) or ("last" in labels and index == count - 1)


def _failure_reasons(*, finite_success: bool, finite_margin: float, analytic_attempted: bool, analytic_margin: float | None, theorem_ready: bool, analytic_failure: str | None) -> list[str]:
    out: list[str] = []
    if not finite_success:
        out.append("finite_validator_failed")
    if not math.isfinite(finite_margin) or finite_margin <= 0.0:
        out.append("finite_radii_margin_nonpositive")
    if not analytic_attempted:
        out.append("analytic_closure_not_attempted")
    elif analytic_margin is None or not math.isfinite(float(analytic_margin)) or float(analytic_margin) <= 0.0:
        out.append("analytic_theorem_margin_nonpositive")
    if analytic_failure is not None:
        out.append("analytic_probe_exception")
    if not theorem_ready:
        out.append("not_theorem_ready")
    return out


def build_mock_regeneration_report(records: Sequence[Mapping[str, Any]], config: LowerAnchorRegenerationConfig | None = None) -> LowerAnchorRegenerationReport:
    """Build a report from supplied records; used by tests and offline audits."""
    cfg = config or LowerAnchorRegenerationConfig()
    allowed = set(LowerAnchorValidationRecord.__dataclass_fields__)
    recs = [LowerAnchorValidationRecord(**{k: v for k, v in dict(r).items() if k in allowed}) for r in records]
    finite_margins = [r.finite_radii_margin for r in recs if math.isfinite(r.finite_radii_margin)]
    analytic_margins = [float(r.analytic_theorem_margin) for r in recs if r.analytic_theorem_margin is not None and math.isfinite(float(r.analytic_theorem_margin))]
    theorem_ready_count = sum(1 for r in recs if r.theorem_ready)
    finite_success_count = sum(1 for r in recs if r.finite_success and r.finite_radii_margin > 0.0)
    final_reached = bool(recs and max(r.K_hi for r in recs) >= cfg.final_anchor_hi and min(r.K_lo for r in recs) <= cfg.start_K)
    failure_fields: list[str] = []
    if finite_success_count != len(recs):
        failure_fields.append("some_finite_segments_failed")
    if theorem_ready_count != len(recs):
        failure_fields.append("analytic_theorem_closure_not_established_for_all_segments")
    if not final_reached:
        failure_fields.append("grid_does_not_reach_final_anchor")
    theorem_facing = bool(theorem_ready_count == len(recs) and recs and final_reached)
    diagnostic_only = not theorem_facing
    return LowerAnchorRegenerationReport(
        schema="phase2c_lower_anchor_regeneration_report_v1",
        status="theorem-ready-candidate-generated" if theorem_facing else "diagnostic-finite-candidate-generated",
        config=cfg,
        records=recs,
        candidate_path=None,
        theorem_facing=theorem_facing,
        diagnostic_only=diagnostic_only,
        promotion_allowed=bool(theorem_facing and not failure_fields),
        theorem_ready_record_count=theorem_ready_count,
        finite_success_count=finite_success_count,
        final_anchor_reached_by_grid=final_reached,
        min_finite_margin=None if not finite_margins else float(min(finite_margins)),
        min_analytic_margin=None if not analytic_margins else float(min(analytic_margins)),
        failure_fields=failure_fields,
        notes="Report built from precomputed/mock records.",
    )


def run_lower_anchor_regeneration(config: LowerAnchorRegenerationConfig | None = None) -> LowerAnchorRegenerationReport:
    cfg = config or LowerAnchorRegenerationConfig()
    try:
        from kam_theorem_suite.torus_validator import validate_invariant_circle_graph
        from kam_theorem_suite.golden_aposteriori import build_golden_aposteriori_certificate
    except Exception as exc:
        return LowerAnchorRegenerationReport(
            schema="phase2c_lower_anchor_regeneration_report_v1",
            status="failed-numeric-stack-unavailable",
            config=cfg,
            records=[],
            candidate_path=None,
            theorem_facing=False,
            diagnostic_only=True,
            promotion_allowed=False,
            theorem_ready_record_count=0,
            finite_success_count=0,
            final_anchor_reached_by_grid=False,
            min_finite_margin=None,
            min_analytic_margin=None,
            failure_fields=["numeric_lower_stack_unavailable"],
            notes=f"Could not import numeric lower stack: {exc!r}",
        )

    rows = build_overlapping_grid(start_K=cfg.start_K, final_anchor_hi=cfg.final_anchor_hi, n_segments=cfg.n_segments, overlap=cfg.overlap)
    records: list[LowerAnchorValidationRecord] = []
    for idx, (K_lo, K_hi, K_mid) in enumerate(rows):
        t0 = time.time()
        val = validate_invariant_circle_graph(GOLDEN_INVERSE, float(K_mid), N=int(cfg.N), oversample_factor=int(cfg.oversample_factor))
        elapsed = time.time() - t0
        fm = _finite_margin(val)
        analytic_attempted = bool(cfg.include_analytic_probe and _should_probe(idx, len(rows), cfg.analytic_probe_at))
        analytic_status = None
        analytic_margin = None
        weighted_residual_l1 = None
        tail_bridge_bound_l1 = None
        relative_correction = None
        analytic_failure = None
        if analytic_attempted:
            try:
                ac = build_golden_aposteriori_certificate(
                    float(K_mid),
                    N_values=tuple(int(x) for x in cfg.analytic_probe_N_values),
                    oversample_factor=max(2, int(cfg.oversample_factor)),
                    sigma_cap=float(cfg.sigma_cap),
                    use_multiresolution=True,
                ).to_dict()
                analytic_status = str(ac.get("analytic_theorem_status") or ac.get("theorem_status"))
                analytic_margin = None if ac.get("analytic_theorem_margin") is None else float(ac.get("analytic_theorem_margin"))
                weighted_residual_l1 = None if ac.get("weighted_residual_l1") is None else float(ac.get("weighted_residual_l1"))
                tail_bridge_bound_l1 = None if ac.get("tail_bridge_bound_l1") is None else float(ac.get("tail_bridge_bound_l1"))
                relative_correction = None if ac.get("relative_correction_to_graph") is None else float(ac.get("relative_correction_to_graph"))
            except Exception as exc:
                analytic_failure = repr(exc)
        theorem_ready = bool(
            val.success and math.isfinite(fm) and fm > 0.0 and analytic_attempted
            and analytic_margin is not None and math.isfinite(float(analytic_margin)) and float(analytic_margin) > 0.0
            and analytic_status in {"analytic-torus-bridge-strong", "analytic-torus-bridge-moderate", "golden-aposteriori-bridge-strong", "golden-aposteriori-bridge-moderate"}
        )
        records.append(LowerAnchorValidationRecord(
            segment_id=f"phase2c_anchor_segment_{idx:03d}",
            K_lo=float(K_lo), K_hi=float(K_hi), K_mid=float(K_mid), N=int(cfg.N),
            finite_success=bool(val.success), eta=float(val.eta), B_norm=float(val.B_norm), lipschitz_bound=float(val.lipschitz_bound), radius_r=float(val.radius),
            finite_radii_margin=float(fm), contraction_bound=float(val.contraction_bound), residual_inf=float(val.residual_inf), residual_l2=float(val.residual_l2),
            oversampled_residual_inf=float(val.oversampled_residual_inf), fourier_tail_l2=float(val.fourier_tail_l2), bridge_quality=str(val.bridge_quality),
            solver_iterations=int(val.solver_iterations), elapsed_seconds=float(elapsed), analytic_probe_attempted=analytic_attempted,
            analytic_theorem_status=analytic_status, analytic_theorem_margin=analytic_margin, weighted_residual_l1=weighted_residual_l1,
            tail_bridge_bound_l1=tail_bridge_bound_l1, relative_correction_to_graph=relative_correction, analytic_probe_failure=analytic_failure,
            closure_level="analytic_theorem_closure" if theorem_ready else "finite_dimensional_collocation_only", theorem_ready=theorem_ready,
            failure_reasons=_failure_reasons(finite_success=bool(val.success), finite_margin=fm, analytic_attempted=analytic_attempted, analytic_margin=analytic_margin, theorem_ready=theorem_ready, analytic_failure=analytic_failure),
        ))
    return build_mock_regeneration_report([r.to_dict() for r in records], cfg)


def build_candidate_json(report: LowerAnchorRegenerationReport, *, source_artifact: str) -> dict[str, Any]:
    return {
        "schema": "phase2c_lower_anchor_candidate_v1",
        "theorem_facing": bool(report.theorem_facing),
        "diagnostic_only": bool(report.diagnostic_only),
        "promotion_allowed": bool(report.promotion_allowed),
        "closure_level": "analytic_theorem_closure" if report.promotion_allowed else "finite_dimensional_collocation_only",
        "source": "actual finite-dimensional lower-anchor regeneration attempt",
        "config": report.config.to_dict(),
        "failure_fields": list(report.failure_fields),
        "notes": report.notes,
        "anchor_segments": [r.to_candidate_row(source_artifact=source_artifact) for r in report.records],
        "raw_validation_records": [r.to_dict() for r in report.records],
    }


def write_regeneration_csv(records: Sequence[LowerAnchorValidationRecord], path: str | Path) -> None:
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["segment_id", "K_lo", "K_hi", "K_mid", "N", "finite_success", "finite_radii_margin", "contraction_bound", "bridge_quality", "analytic_probe_attempted", "analytic_theorem_status", "analytic_theorem_margin", "theorem_ready", "closure_level", "failure_reasons"]
    with path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields); writer.writeheader()
        for r in records:
            d = r.to_dict(); d["failure_reasons"] = ";".join(r.failure_reasons)
            writer.writerow({k: d.get(k) for k in fields})


def write_regeneration_tex(records: Sequence[LowerAnchorValidationRecord], path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    bs = chr(92)
    lines = [
        "% AUTO-GENERATED by lower_anchor_regeneration.py; do not edit manually.",
        bs + "begin{tabular}{lrrrrrl}",
        bs + "hline",
        "Segment & $K_{" + bs + "min}$ & $K_{" + bs + "max}$ & $N$ & finite margin & analytic margin & status " + bs + bs,
        bs + "hline",
    ]
    for r in records:
        am = "--" if r.analytic_theorem_margin is None else f"{r.analytic_theorem_margin:.3e}"
        status = "ready" if r.theorem_ready else "diagnostic"
        lines.append(f"{r.segment_id} & {r.K_lo:.6f} & {r.K_hi:.6f} & {r.N:d} & {r.finite_radii_margin:.3e} & {am} & {status} " + bs + bs)
    lines.extend([bs + "hline", bs + "end{tabular}", ""])
    path.write_text("\n".join(lines))


def write_regeneration_figures(records: Sequence[LowerAnchorValidationRecord], fig_dir: str | Path) -> list[str]:
    fig_dir = Path(fig_dir); fig_dir.mkdir(parents=True, exist_ok=True)
    if not records:
        return []
    try:
        import matplotlib.pyplot as plt
    except Exception:
        return []
    paths: list[str] = []
    xs = [r.K_mid for r in records]
    finite = [r.finite_radii_margin for r in records]
    fig = plt.figure(figsize=(7.2, 4.2)); ax = fig.add_subplot(111)
    ax.plot(xs, finite, marker="o"); ax.axhline(0.0, linewidth=0.8)
    ax.set_xlabel("K"); ax.set_ylabel("finite-dimensional radii margin"); ax.set_title("Phase-2C finite lower-anchor regeneration margins")
    fig.tight_layout(); p = fig_dir / "lower_anchor_regeneration_finite_margins.pdf"; fig.savefig(p); plt.close(fig); paths.append(str(p))
    ax_x = [r.K_mid for r in records if r.analytic_theorem_margin is not None]
    ay = [float(r.analytic_theorem_margin) for r in records if r.analytic_theorem_margin is not None]
    fig = plt.figure(figsize=(7.2, 4.2)); ax = fig.add_subplot(111)
    if ax_x: ax.plot(ax_x, ay, marker="o")
    ax.axhline(0.0, linewidth=0.8); ax.set_xlabel("K"); ax.set_ylabel("analytic theorem margin"); ax.set_title("Phase-2C analytic closure probe")
    fig.tight_layout(); p = fig_dir / "lower_anchor_regeneration_analytic_probe.pdf"; fig.savefig(p); plt.close(fig); paths.append(str(p))
    return paths


def write_regeneration_outputs(report: LowerAnchorRegenerationReport, *, out_dir: str | Path, table_dir: str | Path, fig_dir: str | Path | None = None, candidate_name: str = "lower_anchor_finite_dimensional_candidate.json") -> dict[str, Any]:
    out_dir = Path(out_dir); table_dir = Path(table_dir); out_dir.mkdir(parents=True, exist_ok=True); table_dir.mkdir(parents=True, exist_ok=True)
    candidate_path = out_dir / candidate_name
    report_path = out_dir / "lower_anchor_regeneration_report.json"
    csv_path = table_dir / "lower_anchor_regeneration_records.csv"
    tex_path = table_dir / "lower_anchor_regeneration_records.tex"
    candidate = build_candidate_json(report, source_artifact=str(candidate_path))
    candidate_path.write_text(json.dumps(candidate, indent=2, sort_keys=True) + "\n")
    rd = report.to_dict(); rd["candidate_path"] = str(candidate_path)
    report_path.write_text(json.dumps(rd, indent=2, sort_keys=True) + "\n")
    write_regeneration_csv(report.records, csv_path); write_regeneration_tex(report.records, tex_path)
    figs: list[str] = []
    if fig_dir is not None:
        figs = write_regeneration_figures(report.records, fig_dir)
    return {"status": report.status, "promotion_allowed": report.promotion_allowed, "diagnostic_only": report.diagnostic_only, "failure_fields": list(report.failure_fields), "report_path": str(report_path), "candidate_path": str(candidate_path), "csv_path": str(csv_path), "tex_path": str(tex_path), "figure_paths": figs}

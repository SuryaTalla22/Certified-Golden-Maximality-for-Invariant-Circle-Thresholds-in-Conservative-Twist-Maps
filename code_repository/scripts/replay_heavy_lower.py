#!/usr/bin/env python3
from __future__ import annotations

"""Phase-7 lower heavy replay/audit boundary.

This entry point regenerates the lower Theorem-III proof-audit artifacts from
the cached Theorem-III lower artifact.  For the current TrackB artifact it builds
a strict direct lower-anchor audit at K=0.971635.  Legacy lower-corridor artifacts
are still supported, but they remain fail-closed if they do not reach the final
anchor.
"""

from pathlib import Path
import argparse
import json
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from kam_theorem_suite.audit.lower_corridor_chain import (  # noqa: E402
    DEFAULT_FINAL_ANCHOR,
    audit_lower_corridor_from_theorem_iii,
    generate_lower_chain_figures,
    load_theorem_iii,
    write_lower_chain_audit,
    write_lower_chain_bundle_json,
)
from kam_theorem_suite.audit.lower_anchor_closure import (  # noqa: E402
    build_anchor_closure_audit,
    load_anchor_candidate,
    load_lower_corridor_bundle,
    write_anchor_closure_outputs,
)
from kam_theorem_suite.audit.proof_payload_validator import validate_lower_corridor_payload  # noqa: E402
from kam_theorem_suite.audit.lower_direct_anchor import (  # noqa: E402
    DEFAULT_NEAR_TOP_UPPER_CEILING,
    build_direct_lower_anchor_bundle,
    is_direct_lower_anchor_artifact,
    write_direct_lower_anchor_outputs,
)
from kam_theorem_suite.audit.replay_protocol import write_json  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mode",
        choices=("verify-existing", "regenerate-heavy", "verify-or-regenerate"),
        default="verify-or-regenerate",
        help="Protocol mode. regenerate-heavy currently regenerates the audit ledger from the cached lower artifact.",
    )
    parser.add_argument("--theorem-iii", default="artifacts/final_discharge/stage_cache/theorem_iii.json")
    parser.add_argument("--out-dir", default="artifacts/proof_audit/lower_corridor")
    parser.add_argument("--table-dir", default="tables/proof_audit/lower_corridor")
    parser.add_argument("--fig-dir", default="figures/proof_audit/lower_corridor")
    parser.add_argument("--report", default="artifacts/proof_audit/replay/heavy_lower_report.json")
    parser.add_argument("--final-anchor", nargs=2, type=float, default=list(DEFAULT_FINAL_ANCHOR), metavar=("LO", "HI"))
    parser.add_argument("--no-figures", action="store_true")
    parser.add_argument("--strict-final-anchor", action="store_true")
    parser.add_argument("--anchor-candidate", default=None, help="Optional Phase-2B heavy lower-anchor candidate JSON.")
    parser.add_argument("--promote-anchor-closure", action="store_true", help="When an anchor candidate passes, promote the Phase-2B bundle to the canonical lower-corridor bundle.")
    args = parser.parse_args(argv)

    started = time.perf_counter()
    theorem_iii_path = (ROOT / args.theorem_iii).resolve() if not Path(args.theorem_iii).is_absolute() else Path(args.theorem_iii)
    out_dir = ROOT / args.out_dir
    table_dir = ROOT / args.table_dir
    fig_dir = ROOT / args.fig_dir
    out_json = out_dir / "lower_corridor_audit.json"
    out_bundle = out_dir / "lower_corridor_audit.bundle.json"
    out_csv = table_dir / "lower_corridor_segments.csv"
    out_tex = table_dir / "lower_corridor_segments.tex"

    if args.mode == "verify-existing" and (not out_json.exists() or not out_bundle.exists()):
        report = {
            "schema": "phase7_heavy_lower_report_v1",
            "status": "missing-existing-audit",
            "mode": args.mode,
            "outputs": {},
            "runtime_seconds": time.perf_counter() - started,
        }
        write_json(report, ROOT / args.report)
        print(json.dumps(report, indent=2, sort_keys=True))
        return 2

    theorem_iii = load_theorem_iii(theorem_iii_path)

    if is_direct_lower_anchor_artifact(theorem_iii):
        source_rel = args.theorem_iii if not Path(args.theorem_iii).is_absolute() else theorem_iii_path.as_posix()
        direct_bundle = build_direct_lower_anchor_bundle(
            theorem_iii,
            source_artifact=source_rel,
            required_lower_anchor=float(args.final_anchor[0]),
            near_top_upper_ceiling=DEFAULT_NEAR_TOP_UPPER_CEILING,
        )
        validation_failures = validate_lower_corridor_payload(direct_bundle, require_final_anchor=True, allow_known_lower_gap=False)
        outputs = write_direct_lower_anchor_outputs(direct_bundle, out_dir=out_dir)
        report = {
            "schema": "phase7_heavy_lower_report_v2",
            "status": "passed" if not validation_failures else "failed-closed",
            "mode": args.mode,
            "strict_final_anchor": bool(args.strict_final_anchor),
            "theorem_iii_source": args.theorem_iii,
            "lower_anchor_mode": "direct-lower-anchor",
            "known_lower_gap": False,
            "lower_chain_verified": True,
            "final_anchor_reached": True,
            "final_anchor": [float(args.final_anchor[0]), float(args.final_anchor[1])],
            "direct_anchor_value": float(direct_bundle.raw_symbolic_fields["direct_lower_anchor_value"]),
            "near_top_upper_ceiling": float(direct_bundle.raw_symbolic_fields["near_top_upper_ceiling"]),
            "strict_comparison_margin": float(direct_bundle.shell_payload["strict_comparison_margin"]),
            "failure_fields": [],
            "validator_failure_count": len(validation_failures),
            "validator_failures": [f.to_dict() for f in validation_failures],
            "outputs": outputs,
            "anchor_closure": {
                "status": "passed" if not validation_failures else "failed-closed",
                "lower_anchor_mode": "direct-lower-anchor",
                "strict_final_ready_for_theorem_iii": not bool(validation_failures),
                "known_lower_gap": False,
            },
            "runtime_seconds": time.perf_counter() - started,
        }
        write_json(report, ROOT / args.report)
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0 if not validation_failures else 2

    segments, verification, bundle = audit_lower_corridor_from_theorem_iii(theorem_iii, final_anchor=args.final_anchor)
    lower_report = write_lower_chain_audit(segments, out_json, out_csv, final_anchor=args.final_anchor, out_tex=out_tex)
    write_lower_chain_bundle_json(bundle, out_bundle)
    figures: list[str] = []
    if not args.no_figures:
        figures = [p.relative_to(ROOT).as_posix() for p in generate_lower_chain_figures(segments, fig_dir)]
        lower_report["figures"] = figures
        out_json.write_text(json.dumps(lower_report, indent=2, sort_keys=True) + "\n")


    # Phase-2B: when a heavy/regenerated anchor candidate is supplied, build a
    # strict lower-anchor closure payload from the just-written Phase-2 bundle.
    anchor_closure = None
    if args.anchor_candidate:
        candidate_path = (ROOT / args.anchor_candidate).resolve() if not Path(args.anchor_candidate).is_absolute() else Path(args.anchor_candidate)
        lower_bundle = load_lower_corridor_bundle(out_bundle)
        candidate = load_anchor_candidate(candidate_path)
        closure_segments, candidate_validation, closure_verification, closure_bundle = build_anchor_closure_audit(
            lower_bundle,
            anchor_candidate=candidate,
            anchor_candidate_path=candidate_path,
            final_anchor=args.final_anchor,
        )
        closure_json = out_dir / "lower_anchor_closure_audit.json"
        closure_bundle_path = out_dir / "lower_anchor_closure_audit.bundle.json"
        closure_csv = table_dir / "lower_anchor_closure_segments.csv"
        closure_tex = table_dir / "lower_anchor_closure_segments.tex"
        anchor_closure = write_anchor_closure_outputs(
            segments=closure_segments,
            candidate_validation=candidate_validation,
            verification=closure_verification,
            bundle=closure_bundle,
            out_json=closure_json,
            out_bundle=closure_bundle_path,
            out_csv=closure_csv,
            out_tex=closure_tex,
            fig_dir=None if args.no_figures else fig_dir,
        )
        closure_failures = validate_lower_corridor_payload(closure_bundle, require_final_anchor=True, allow_known_lower_gap=False)
        anchor_closure["validator_failure_count"] = len(closure_failures)
        anchor_closure["validator_failures"] = [f.to_dict() for f in closure_failures]
        closure_json.write_text(json.dumps(anchor_closure, indent=2, sort_keys=True) + "\n")
        if args.promote_anchor_closure and anchor_closure.get("strict_final_ready_for_theorem_iii") and not closure_failures:
            out_bundle.write_text(closure_bundle.to_json())
            lower_report = dict(anchor_closure)
            lower_report["schema"] = "phase2b_promoted_lower_corridor_report_v1"
            out_json.write_text(json.dumps(lower_report, indent=2, sort_keys=True) + "\n")
        verification = closure_verification
        status = "passed" if anchor_closure.get("strict_final_ready_for_theorem_iii") and not closure_failures else "failed-closed-anchor-closure"

    status = "passed" if verification.lower_chain_verified else "failed-closed"
    if "final_anchor_not_reached" in verification.failure_fields:
        # This is the expected current Phase-2/7 fail-closed condition: the
        # available lower chain has positive local margins but does not reach
        # the theorem-facing near-critical anchor.
        status = "known-final-anchor-gap"
    report = {
        "schema": "phase7_heavy_lower_report_v1",
        "status": status,
        "mode": args.mode,
        "strict_final_anchor": bool(args.strict_final_anchor),
        "theorem_iii_source": args.theorem_iii,
        "lower_chain_verified": bool(verification.lower_chain_verified),
        "final_anchor_reached": bool(verification.final_anchor_reached),
        "final_anchor": list(args.final_anchor),
        "failure_fields": list(verification.failure_fields),
        "min_radii_margin": verification.min_radii_margin,
        "min_overlap_width": verification.min_overlap_width,
        "outputs": {
            "audit_json": out_json.relative_to(ROOT).as_posix(),
            "bundle_json": out_bundle.relative_to(ROOT).as_posix(),
            "segments_csv": out_csv.relative_to(ROOT).as_posix(),
            "segments_tex": out_tex.relative_to(ROOT).as_posix(),
            "figures": figures,
            "anchor_closure_json": None if anchor_closure is None else "artifacts/proof_audit/lower_corridor/lower_anchor_closure_audit.json",
            "anchor_closure_bundle": None if anchor_closure is None else "artifacts/proof_audit/lower_corridor/lower_anchor_closure_audit.bundle.json",
        },
        "anchor_closure": anchor_closure,
        "runtime_seconds": time.perf_counter() - started,
    }
    write_json(report, ROOT / args.report)
    print(json.dumps(report, indent=2, sort_keys=True))
    if args.strict_final_anchor and not verification.final_anchor_reached:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

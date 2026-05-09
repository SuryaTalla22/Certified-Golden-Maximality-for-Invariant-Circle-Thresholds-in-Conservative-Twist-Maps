#!/usr/bin/env python3
from __future__ import annotations

"""Phase-2B lower-anchor closure runner.

By default this script is fail-closed: it validates the existing Phase-2 lower
corridor and writes a Phase-2B report saying that a regenerated/supplied heavy
lower-anchor candidate is required.  To promote Theorem III, pass
``--candidate PATH`` where PATH contains theorem-facing anchor segments with raw
``Y, Z, T, r`` fields.  The script validates the candidate, links it to the
Phase-2 corridor, and writes an upgraded lower-corridor proof-audit bundle.
"""

from pathlib import Path
import argparse
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from kam_theorem_suite.audit.lower_anchor_closure import (  # noqa: E402
    build_anchor_closure_audit,
    load_anchor_candidate,
    load_lower_corridor_bundle,
    write_anchor_candidate_template,
    write_anchor_closure_outputs,
)
from kam_theorem_suite.audit.lower_corridor_chain import DEFAULT_FINAL_ANCHOR  # noqa: E402
from kam_theorem_suite.audit.proof_payload_validator import validate_lower_corridor_payload  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lower-bundle", default="artifacts/proof_audit/lower_corridor/lower_corridor_audit.bundle.json")
    parser.add_argument("--candidate", default=None, help="Optional heavy lower-anchor candidate JSON.")
    parser.add_argument("--out-dir", default="artifacts/proof_audit/lower_corridor")
    parser.add_argument("--table-dir", default="tables/proof_audit/lower_corridor")
    parser.add_argument("--fig-dir", default="figures/proof_audit/lower_corridor")
    parser.add_argument("--final-anchor", nargs=2, type=float, default=list(DEFAULT_FINAL_ANCHOR), metavar=("LO", "HI"))
    parser.add_argument("--write-template", default=None, help="Write a diagnostic candidate template and exit.")
    parser.add_argument("--promote", action="store_true", help="If the candidate passes, also overwrite lower_corridor_audit.bundle.json with the upgraded bundle.")
    parser.add_argument("--strict", action="store_true", help="Return nonzero unless the Phase-2B closure is strict-final-ready.")
    parser.add_argument("--no-figures", action="store_true")
    args = parser.parse_args(argv)

    if args.write_template:
        path = write_anchor_candidate_template(ROOT / args.write_template, final_anchor=args.final_anchor)
        print(json.dumps({"status": "template-written", "path": path.relative_to(ROOT).as_posix()}, indent=2, sort_keys=True))
        return 0

    lower_path = ROOT / args.lower_bundle
    lower_bundle = load_lower_corridor_bundle(lower_path)
    candidate = None
    candidate_path = None
    if args.candidate:
        candidate_path = ROOT / args.candidate
        candidate = load_anchor_candidate(candidate_path)

    segments, candidate_validation, verification, bundle = build_anchor_closure_audit(
        lower_bundle,
        anchor_candidate=candidate,
        anchor_candidate_path=candidate_path,
        final_anchor=args.final_anchor,
    )

    out_dir = ROOT / args.out_dir
    table_dir = ROOT / args.table_dir
    fig_dir = ROOT / args.fig_dir
    out_json = out_dir / "lower_anchor_closure_audit.json"
    out_bundle = out_dir / "lower_anchor_closure_audit.bundle.json"
    out_csv = table_dir / "lower_anchor_closure_segments.csv"
    out_tex = table_dir / "lower_anchor_closure_segments.tex"

    report = write_anchor_closure_outputs(
        segments=segments,
        candidate_validation=candidate_validation,
        verification=verification,
        bundle=bundle,
        out_json=out_json,
        out_bundle=out_bundle,
        out_csv=out_csv,
        out_tex=out_tex,
        fig_dir=None if args.no_figures else fig_dir,
    )
    failures = validate_lower_corridor_payload(bundle, require_final_anchor=True, allow_known_lower_gap=False)
    report["validator_failure_count"] = len(failures)
    report["validator_failures"] = [f.to_dict() for f in failures]
    out_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")

    strict_ready = bool(report["strict_final_ready_for_theorem_iii"] and not failures)
    if args.promote and strict_ready:
        promoted = out_dir / "lower_corridor_audit.bundle.json"
        promoted.write_text(bundle.to_json())
        # Also write a wrapper JSON at the canonical path for humans.
        canonical_report = out_dir / "lower_corridor_audit.json"
        canonical = dict(report)
        canonical["schema"] = "phase2b_promoted_lower_corridor_report_v1"
        canonical["promoted_from"] = out_bundle.relative_to(ROOT).as_posix()
        canonical_report.write_text(json.dumps(canonical, indent=2, sort_keys=True) + "\n")
        report["promoted_bundle"] = promoted.relative_to(ROOT).as_posix()
        out_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")

    summary = {
        "schema": "phase2b_lower_anchor_closure_cli_summary_v1",
        "status": report["status"],
        "strict_final_ready_for_theorem_iii": strict_ready,
        "candidate_present": candidate is not None,
        "known_lower_gap": not strict_ready,
        "failure_fields": report["failure_fields"],
        "validator_failure_count": len(failures),
        "outputs": {
            "audit_json": out_json.relative_to(ROOT).as_posix(),
            "bundle_json": out_bundle.relative_to(ROOT).as_posix(),
            "segments_csv": out_csv.relative_to(ROOT).as_posix(),
            "segments_tex": out_tex.relative_to(ROOT).as_posix(),
        },
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    if args.strict and not strict_ready:
        return 2
    return 0 if (strict_ready or not args.strict) else 2


if __name__ == "__main__":
    raise SystemExit(main())

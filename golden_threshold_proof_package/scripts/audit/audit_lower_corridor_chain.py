#!/usr/bin/env python3
from __future__ import annotations

"""Run the Phase-2 lower-corridor proof-carrying chain audit.

The script writes both a reviewer-friendly report and the raw ProofAuditBundle.
By default it exits with status 0 even when the current repository fails the
near-critical final-anchor reach check, because the fail-closed report is itself
a useful artifact.  Pass ``--strict`` to turn audit failure into a nonzero exit.
"""

from pathlib import Path
import argparse
import json
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from kam_theorem_suite.audit.lower_corridor_chain import (  # noqa: E402
    DEFAULT_FINAL_ANCHOR,
    audit_lower_corridor_from_theorem_iii,
    generate_lower_chain_figures,
    load_theorem_iii,
    write_lower_chain_audit,
    write_lower_chain_bundle_json,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--theorem-iii",
        default="artifacts/final_discharge/stage_cache/theorem_iii.json",
        help="Path to the cached Theorem-III lower artifact.",
    )
    parser.add_argument(
        "--out-json",
        default="artifacts/proof_audit/lower_corridor/lower_corridor_audit.json",
        help="Reviewer-facing JSON report path.",
    )
    parser.add_argument(
        "--out-bundle-json",
        default="artifacts/proof_audit/lower_corridor/lower_corridor_audit.bundle.json",
        help="Raw ProofAuditBundle JSON path.",
    )
    parser.add_argument(
        "--out-csv",
        default="tables/proof_audit/lower_corridor/lower_corridor_segments.csv",
        help="CSV segment ledger path.",
    )
    parser.add_argument(
        "--out-tex",
        default="tables/proof_audit/lower_corridor/lower_corridor_segments.tex",
        help="LaTeX segment table path.",
    )
    parser.add_argument(
        "--fig-dir",
        default="figures/proof_audit/lower_corridor",
        help="Directory for lower-chain margin/resolution/overlap figures.",
    )
    parser.add_argument(
        "--final-anchor",
        nargs=2,
        type=float,
        default=list(DEFAULT_FINAL_ANCHOR),
        metavar=("LO", "HI"),
        help="The theorem-facing near-critical lower anchor to test.",
    )
    parser.add_argument("--no-figures", action="store_true", help="Skip PDF figure generation.")
    parser.add_argument("--strict", action="store_true", help="Exit nonzero if the lower-chain audit fails.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    theorem_iii_path = (REPO_ROOT / args.theorem_iii).resolve() if not Path(args.theorem_iii).is_absolute() else Path(args.theorem_iii)
    theorem_iii = load_theorem_iii(theorem_iii_path)
    segments, verification, bundle = audit_lower_corridor_from_theorem_iii(
        theorem_iii, final_anchor=args.final_anchor
    )

    out_json = REPO_ROOT / args.out_json
    out_csv = REPO_ROOT / args.out_csv
    out_tex = REPO_ROOT / args.out_tex
    out_bundle = REPO_ROOT / args.out_bundle_json
    fig_dir = REPO_ROOT / args.fig_dir

    report = write_lower_chain_audit(
        segments,
        out_json,
        out_csv,
        final_anchor=args.final_anchor,
        out_tex=out_tex,
    )
    write_lower_chain_bundle_json(bundle, out_bundle)
    figures: list[str] = []
    if not args.no_figures:
        figures = [p.relative_to(REPO_ROOT).as_posix() for p in generate_lower_chain_figures(segments, fig_dir)]
        report["figures"] = figures
        out_json.write_text(json.dumps(report, indent=2))

    print(json.dumps({
        "status": report["status"],
        "lower_chain_verified": verification.lower_chain_verified,
        "final_anchor_reached": verification.final_anchor_reached,
        "final_anchor": list(args.final_anchor),
        "min_radii_margin": verification.min_radii_margin,
        "min_overlap_width": verification.min_overlap_width,
        "failure_fields": verification.failure_fields,
        "report": out_json.relative_to(REPO_ROOT).as_posix(),
        "bundle": out_bundle.relative_to(REPO_ROOT).as_posix(),
        "csv": out_csv.relative_to(REPO_ROOT).as_posix(),
        "tex": out_tex.relative_to(REPO_ROOT).as_posix(),
        "figures": figures,
    }, indent=2))

    if args.strict and not verification.lower_chain_verified:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

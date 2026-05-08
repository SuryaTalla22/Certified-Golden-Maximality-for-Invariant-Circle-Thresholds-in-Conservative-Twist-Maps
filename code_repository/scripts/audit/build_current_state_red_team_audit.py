#!/usr/bin/env python3
from __future__ import annotations

"""Build the Phase-1 current-state red-team audit JSON.

By default this command writes the audit artifact and exits with status 0 even
when the audit records a theorem gap; use ``--strict`` to make the command fail
when the compact lower anchor is not derivable from the cached lower artifact.
"""

from pathlib import Path
import argparse
import json
import sys


def _insert_repo_on_path(repository_root: Path) -> None:
    root = repository_root.resolve()
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository-root", default=".")
    parser.add_argument(
        "--theorem-iii-artifact",
        default="artifacts/final_discharge/stage_cache/theorem_iii.json",
        help="Path relative to repository root unless absolute.",
    )
    parser.add_argument("--output", default="artifacts/proof_audit/current_state_red_team_audit.json")
    parser.add_argument("--strict", action="store_true", help="Exit nonzero if the red-team audit fails.")
    args = parser.parse_args()

    root = Path(args.repository_root).resolve()
    _insert_repo_on_path(root)
    from kam_theorem_suite.audit.current_state_red_team import build_current_state_red_team_report

    artifact = Path(args.theorem_iii_artifact)
    if not artifact.is_absolute():
        artifact = root / artifact
    report = build_current_state_red_team_report(artifact)
    out = Path(args.output)
    if not out.is_absolute():
        out = root / out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(f"wrote {out}")
    print(json.dumps(report["summary"], indent=2, sort_keys=True))
    if args.strict and report["status"] != "passed":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

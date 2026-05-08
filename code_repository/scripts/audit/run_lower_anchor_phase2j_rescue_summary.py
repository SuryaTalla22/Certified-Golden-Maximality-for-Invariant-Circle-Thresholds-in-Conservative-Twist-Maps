#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from kam_theorem_suite.audit.lower_anchor_phase2j_adaptive_rescue import summarize_rescue_directory


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Summarize Phase-2J rescue candidates produced by the rescue script.")
    p.add_argument("--atlas", default="artifacts/proof_audit/lower_corridor/lower_anchor_phase2j_failure_atlas.json")
    p.add_argument("--rescue-dir", default="artifacts/proof_audit/lower_corridor/phase2j_rescue")
    p.add_argument("--out", default="artifacts/proof_audit/lower_corridor/lower_anchor_phase2j_rescue_summary.json")
    args = p.parse_args(argv)
    summary = summarize_rescue_directory(
        atlas_path=ROOT / args.atlas if not Path(args.atlas).is_absolute() else Path(args.atlas),
        rescue_dir=ROOT / args.rescue_dir if not Path(args.rescue_dir).is_absolute() else Path(args.rescue_dir),
    )
    out = ROOT / args.out if not Path(args.out).is_absolute() else Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary.to_dict(), indent=2, sort_keys=True) + "\n")
    print(json.dumps(summary.to_dict(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

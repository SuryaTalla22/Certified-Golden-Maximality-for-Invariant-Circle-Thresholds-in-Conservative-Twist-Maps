#!/usr/bin/env python3
from __future__ import annotations

"""Run the minimal paper-facing final replay.

This script uses compact theorem-facing shells and does not consume or regenerate
heavy Theorem-IV artifacts.  It is intended for quick referee/audit smoke checks.
Use ``replay_downstream_from_cache.py`` for the cache-backed downstream replay.
"""

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from kam_theorem_suite.lightweight_stage108_stubs import install_lightweight_stage108_stubs
install_lightweight_stage108_stubs()

from kam_theorem_suite.paper_replay_inputs import (
    BASE_K_VALUES,
    build_minimal_theorem_shells,
    validate_paper_replay_shells,
)
from kam_theorem_suite.theorem_final_discharge_replay import (
    assert_stage108_final_discharge_verified,
    build_stage108_final_discharge_replay_report,
    save_stage108_final_discharge_artifacts,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        default="artifacts/paper_replay/minimal",
        help="Directory for compact replay JSON outputs.",
    )
    args = parser.parse_args()

    shells = build_minimal_theorem_shells()
    validate_paper_replay_shells(shells, require_cached_upstream=False)
    report = build_stage108_final_discharge_replay_report(
        theorem_i_ii_workstream_certificate=shells[0],
        theorem_iii_certificate=shells[1],
        theorem_iv_certificate=shells[2],
        theorem_v_certificate=shells[3],
        threshold_identification_certificate=shells[4],
        theorem_vi_certificate=shells[5],
        theorem_vii_certificate=shells[6],
        base_K_values=BASE_K_VALUES,
    )
    assert_stage108_final_discharge_verified(report)
    paths = save_stage108_final_discharge_artifacts(report, Path(args.out))
    print(json.dumps({"status": "ok", "outputs": paths, "theorem_status": report.theorem_status}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

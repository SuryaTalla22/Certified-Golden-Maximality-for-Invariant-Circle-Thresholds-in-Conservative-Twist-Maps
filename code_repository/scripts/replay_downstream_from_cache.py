#!/usr/bin/env python3
from __future__ import annotations

"""Replay V-and-beyond final-discharge logic from cached I--II/III/IV objects.

Unlike ``replay_minimal.py``, this script is fail-closed by default.  It requires
cached upstream artifacts and verifies their SHA256 hashes against
``HASHES.sha256`` when the ledger is present.  A synthetic fallback is available
only through the explicit ``--allow-synthetic-upstream`` flag and should not be
used for publication claims.
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
    PaperReplayValidationError,
    build_minimal_theorem_shells,
    build_shells_from_stage_cache,
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
        "--stage-cache",
        default="artifacts/final_discharge/stage_cache",
        help="Directory containing cached theorem_i_ii/theorem_iii/theorem_iv JSON objects.",
    )
    parser.add_argument(
        "--hashes",
        default="HASHES.sha256",
        help="SHA256 ledger to verify required cached artifacts. Use --no-hash-check to disable.",
    )
    parser.add_argument(
        "--no-hash-check",
        action="store_true",
        help="Require cache files but skip comparison against HASHES.sha256.",
    )
    parser.add_argument(
        "--allow-synthetic-upstream",
        action="store_true",
        help="Use compact synthetic upstream shells if cache verification fails. Not for publication claims.",
    )
    parser.add_argument(
        "--out",
        default="artifacts/paper_replay/downstream_from_cache",
        help="Directory for compact replay JSON outputs.",
    )
    args = parser.parse_args()

    try:
        shells = build_shells_from_stage_cache(
            args.stage_cache,
            repository_root=ROOT,
            hash_ledger=None if args.no_hash_check else args.hashes,
            require_cache=True,
        )
        validate_paper_replay_shells(shells, require_cached_upstream=True)
        replay_mode = "downstream-from-verified-cache"
    except PaperReplayValidationError as exc:
        if not args.allow_synthetic_upstream:
            print(f"cache-backed downstream replay failed closed: {exc}", file=sys.stderr)
            return 2
        shells = build_minimal_theorem_shells()
        validate_paper_replay_shells(shells, require_cached_upstream=False)
        replay_mode = "synthetic-upstream-explicitly-allowed"

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
    print(
        json.dumps(
            {
                "status": "ok",
                "replay_mode": replay_mode,
                "outputs": paths,
                "theorem_status": report.theorem_status,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

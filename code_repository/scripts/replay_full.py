#!/usr/bin/env python3
from __future__ import annotations

"""Full archival replay stub.

This script is intentionally fail-closed in the paper-facing snapshot.  A true
full replay must regenerate the heavy Theorem-IV cache, then run the downstream
replay from the regenerated cache, regenerate `ARTIFACT_MANIFEST.tsv`, and verify
`HASHES.sha256`.  Until the heavy stage command is wired here, this script must
not be cited as a one-command full reproduction path.
"""

import argparse
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--acknowledge-archival-stub",
        action="store_true",
        help="Acknowledge that this snapshot does not configure heavy Theorem-IV regeneration.",
    )
    args = parser.parse_args()
    message = (
        "Full archival replay is not configured in this paper-facing snapshot. "
        "Use scripts/replay_minimal.py for smoke checks and "
        "scripts/replay_downstream_from_cache.py for the cache-backed referee replay. "
        "Wire the heavy Theorem-IV regeneration command here before describing this "
        "script as a full one-command reproduction path."
    )
    if args.acknowledge_archival_stub:
        print(message)
    else:
        print(message, file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

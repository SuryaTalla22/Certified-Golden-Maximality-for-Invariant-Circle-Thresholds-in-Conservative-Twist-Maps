from __future__ import annotations

from pathlib import Path
import sys
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import json

from kam_theorem_suite.obstruction_atlas import ApproximantWindowSpec
from kam_theorem_suite.proof_driver import build_multi_approximant_atlas_report
from kam_theorem_suite.standard_map import HarmonicFamily

def main() -> None:
    family = HarmonicFamily()
    specs = [
        ApproximantWindowSpec(3, 5, 0.9738, 0.9742, 1.04, 1.06, label="gold-3/5"),
        ApproximantWindowSpec(5, 8, 0.96, 0.98, 1.04, 1.06, label="gold-5/8"),
        ApproximantWindowSpec(8, 13, 0.96, 0.98, 1.04, 1.06, label="gold-8/13"),
    ]
    report = build_multi_approximant_atlas_report(
        specs,
        family,
        auto_localize_crossing=True,
        initial_subdivisions=2,
        max_depth=2,
    )
    outdir = Path(__file__).resolve().parents[1] / "outputs"
    outdir.mkdir(exist_ok=True)
    outpath = outdir / "demo_obstruction_atlas.json"
    outpath.write_text(json.dumps(report, indent=2))
    print(json.dumps({
        "atlas_status": report["atlas_status"],
        "fully_certified_count": report["fully_certified_count"],
        "crossing_only_count": report["crossing_only_count"],
        "failed_count": report["failed_count"],
        "output": str(outpath),
    }, indent=2))

if __name__ == "__main__":
    main()

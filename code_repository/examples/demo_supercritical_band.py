from __future__ import annotations

from pathlib import Path
import sys
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import json

from kam_theorem_suite.proof_driver import build_supercritical_band_report_driver
from kam_theorem_suite.standard_map import HarmonicFamily

def main() -> None:
    family = HarmonicFamily()
    report = build_supercritical_band_report_driver(
        3,
        5,
        1.04,
        1.06,
        family,
        initial_subdivisions=2,
        max_depth=2,
    )
    outdir = Path(__file__).resolve().parents[1] / "outputs"
    outdir.mkdir(exist_ok=True)
    outpath = outdir / "demo_supercritical_band.json"
    outpath.write_text(json.dumps(report, indent=2))
    print(json.dumps({
        "status": report["status"],
        "longest_band_lo": report["longest_band_lo"],
        "longest_band_hi": report["longest_band_hi"],
        "coverage_fraction": report["coverage_fraction"],
        "output": str(outpath),
    }, indent=2))

if __name__ == "__main__":
    main()

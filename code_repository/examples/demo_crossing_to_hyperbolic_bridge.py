from __future__ import annotations

from pathlib import Path
import sys
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import json

from kam_theorem_suite.proof_driver import build_crossing_to_hyperbolic_bridge_report
from kam_theorem_suite.standard_map import HarmonicFamily

def main() -> None:
    family = HarmonicFamily()
    report = build_crossing_to_hyperbolic_bridge_report(
        3,
        5,
        0.97,
        0.975,
        1.04,
        1.06,
        family,
        initial_subdivisions=2,
        max_depth=2,
    )
    outdir = Path(__file__).resolve().parents[1] / "outputs"
    outdir.mkdir(exist_ok=True)
    outpath = outdir / "demo_crossing_to_hyperbolic_bridge.json"
    outpath.write_text(json.dumps(report, indent=2))
    print(json.dumps({
        "status": report["status"],
        "root_window": [
            report["crossing_certificate"]["certified_root_window_lo"],
            report["crossing_certificate"]["certified_root_window_hi"],
        ],
        "band": [
            report["band_report"]["longest_band_lo"],
            report["band_report"]["longest_band_hi"],
        ],
        "gap": report["first_supercritical_gap"],
        "output": str(outpath),
    }, indent=2))

if __name__ == "__main__":
    main()

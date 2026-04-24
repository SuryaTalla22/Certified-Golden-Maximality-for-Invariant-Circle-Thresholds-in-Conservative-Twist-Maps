from __future__ import annotations

from pathlib import Path
import sys
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import json

from kam_theorem_suite.proof_driver import build_crossing_window_report, build_periodic_class_report
from kam_theorem_suite.standard_map import HarmonicFamily

def main() -> None:
    fam = HarmonicFamily()
    crossing = build_crossing_window_report(3, 5, 0.969, 0.972, fam)
    golden = build_periodic_class_report((1,))

    out = {
        "crossing": crossing.to_dict(),
        "golden": golden.to_dict(),
    }
    out_path = ROOT / "outputs" / "demo_crossing_window.json"
    out_path.write_text(json.dumps(out, indent=2))
    print(f"Wrote {out_path}")

if __name__ == "__main__":
    main()

from __future__ import annotations

from pathlib import Path
import sys
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from kam_theorem_suite.crossing_certificate import certify_unique_crossing_window
from kam_theorem_suite.standard_map import HarmonicFamily

def main() -> None:
    fam = HarmonicFamily()
    cert = certify_unique_crossing_window(3, 5, 0.9738, 0.9742, fam)
    print("tier:", cert.certification_tier)
    print("message:", cert.message)
    print("root window:", cert.certified_root_window_lo, cert.certified_root_window_hi)
    print("barrier:", cert.supercritical_barrier_lo, cert.supercritical_barrier_hi)

if __name__ == "__main__":
    main()

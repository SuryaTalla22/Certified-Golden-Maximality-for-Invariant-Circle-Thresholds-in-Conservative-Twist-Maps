from __future__ import annotations
from pathlib import Path
import sys
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
from kam_theorem_suite.proof_driver import build_multiresolution_existence_crossing_bridge_report
from kam_theorem_suite.standard_map import HarmonicFamily
GOLDEN = (5.0 ** 0.5 - 1.0) / 2.0
if __name__ == '__main__':
    rep = build_multiresolution_existence_crossing_bridge_report(rho=GOLDEN, K_values=[0.5, 0.6, 0.7], p=3, q=5, crossing_K_lo=0.969, crossing_K_hi=0.972, family=HarmonicFamily(), N_values=(32, 48, 64), quality_floor='weak')
    print(rep['relation'])

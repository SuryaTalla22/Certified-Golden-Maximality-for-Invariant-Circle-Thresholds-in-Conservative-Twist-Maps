from __future__ import annotations
from pathlib import Path
import sys
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
from kam_theorem_suite.proof_driver import build_multiresolution_torus_validation_report
from kam_theorem_suite.standard_map import HarmonicFamily
GOLDEN = (5.0 ** 0.5 - 1.0) / 2.0
if __name__ == '__main__':
    rep = build_multiresolution_torus_validation_report(rho=GOLDEN, K=0.5, family=HarmonicFamily(), N_values=(32, 48, 64))
    print({'atlas_quality': rep['atlas_quality'], 'finest_success_N': rep['finest_success_N'], 'success_count': rep['success_count'], 'comparison_pair_stable': [c['pair_stable'] for c in rep['comparisons']]})

from __future__ import annotations

import json
import math

from kam_theorem_suite.proof_driver import build_analytic_torus_validation_report
from kam_theorem_suite.standard_map import HarmonicFamily


def main() -> None:
    rho = (math.sqrt(5.0) - 1.0) / 2.0
    report = build_analytic_torus_validation_report(rho=rho, K=0.3, family=HarmonicFamily(), N=64, sigma_cap=0.02)
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()

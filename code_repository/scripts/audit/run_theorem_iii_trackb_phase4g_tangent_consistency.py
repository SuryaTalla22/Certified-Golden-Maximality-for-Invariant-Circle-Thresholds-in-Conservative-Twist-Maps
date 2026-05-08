#!/usr/bin/env python
from __future__ import annotations
import argparse
from kam_theorem_suite.lower_param.tangent_consistency_audit import run_phase4g_tangent_consistency


def main() -> None:
    ap = argparse.ArgumentParser(description="Track B Phase 4g tangent/embedding consistency audit (diagnostic only).")
    ap.add_argument("--npz", action="append", required=True, help="Embedding npz to audit. Can be repeated.")
    ap.add_argument("--grid-factors", default="1,2,4", help="Comma-separated evaluation grid multipliers.")
    ap.add_argument("--force-sign", type=int, choices=[-1, 1], default=None, help="Force standard-map sine sign convention.")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    factors = [int(x) for x in args.grid_factors.split(",") if x.strip()]
    run_phase4g_tangent_consistency(args.npz, args.out_dir, factors, args.force_sign, args.force)


if __name__ == "__main__":
    main()

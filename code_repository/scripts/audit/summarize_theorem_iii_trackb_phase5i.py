#!/usr/bin/env python3
from __future__ import annotations

import argparse
from kam_theorem_suite.lower_param.phase5i_nonlinear_tail import summarize_json


def main() -> None:
    p = argparse.ArgumentParser(description="Summarize Phase 5I compact report.")
    p.add_argument("summary_json")
    p.add_argument("--out", default=None)
    args = p.parse_args()
    summarize_json(args.summary_json, args.out)


if __name__ == "__main__":
    main()

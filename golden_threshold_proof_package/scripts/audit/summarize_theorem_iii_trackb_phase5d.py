#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from kam_theorem_suite.lower_param.phase5d_certificate_scaffold import read_json


def main() -> None:
    ap = argparse.ArgumentParser(description="Print compact Phase 5D assembly summary.")
    ap.add_argument("summary_json", help="Path to phase5d_assembly_summary.json or certificate scaffold JSON.")
    ap.add_argument("--top", type=int, default=20)  # retained for interface consistency
    args = ap.parse_args()
    payload = read_json(args.summary_json)

    if payload.get("schema") == "theorem_iii_trackb_phase5d_certificate_scaffold_v1":
        b = payload["interval_backend_bounds"]
        compact = {
            "schema": "theorem_iii_trackb_phase5d_compact_report_v1",
            "status": "phase5d-certificate-scaffold-compact",
            "diagnostic_only": payload.get("diagnostic_only"),
            "theorem_facing": payload.get("theorem_facing"),
            "promotion_allowed": payload.get("promotion_allowed"),
            "K": payload["seed"]["K"],
            "M": payload["seed"]["M"],
            "nu": payload["validation_parameters"]["nu"],
            "radius": payload["validation_parameters"]["radius"],
            "cutoff_spec": payload["validation_parameters"]["cutoff_spec"],
            "tail_start_frac": payload["validation_parameters"]["tail_start_frac"],
            "Y_interval_upper": b["Y_interval_upper"],
            "Z_interval_upper": b["Z_interval_upper"],
            "Q_interval_upper": b["Q_interval_upper"],
            "radii_margin_interval_lower_reported": b["radii_margin_interval_lower_reported"],
            "radii_margin_interval_lower_recomputed": b["radii_margin_interval_lower_recomputed"],
            "radii_relative_margin_interval_lower": b["radii_relative_margin_interval_lower"],
            "dominant_interval_term": b["dominant_interval_term"],
            "active_assumptions_count": len(payload.get("active_assumptions", [])),
            "open_hypotheses_count": len(payload.get("open_hypotheses", [])),
        }
    else:
        compact = {
            "schema": "theorem_iii_trackb_phase5d_compact_report_v1",
            "status": payload.get("status"),
            "diagnostic_only": payload.get("diagnostic_only"),
            "theorem_facing": payload.get("theorem_facing"),
            "promotion_allowed": payload.get("promotion_allowed"),
            "certificate_path": payload.get("certificate_path"),
            "replay_path": payload.get("replay_path"),
            "replay_passed": payload.get("replay_passed"),
            "negative_controls_passed": payload.get("negative_controls_passed"),
            "selected_candidate": payload.get("selected_candidate"),
            "failed_replay_checks": payload.get("failed_replay_checks", []),
            "active_assumptions": payload.get("active_assumptions", []),
            "open_hypotheses": payload.get("open_hypotheses", []),
            "next_phase_recommendation": payload.get("next_phase_recommendation"),
        }
    print(json.dumps(compact, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

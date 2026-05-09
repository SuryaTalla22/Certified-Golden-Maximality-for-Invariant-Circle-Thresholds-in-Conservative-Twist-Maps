#!/usr/bin/env python
from __future__ import annotations

import argparse
from pathlib import Path
import json


def load(path: str | Path):
    p = Path(path)
    if not p.exists():
        return {"MISSING": str(p)}
    return json.loads(p.read_text())


def thin_record(r):
    flags = r.get("availability_flags", {}) or {}
    return {
        "index": r.get("index"),
        "K_lo": r.get("K_lo"),
        "K_hi": r.get("K_hi"),
        "bucket": r.get("bucket"),
        "artifact_exists": r.get("artifact_exists"),
        "raw_data_stage1_ready": r.get("raw_data_stage1_ready"),
        "input_row_margin": r.get("input_row_margin"),
        "input_row_q": r.get("input_row_q"),
        "tail_guard_ready": flags.get("enough_for_tail_guard_prototype"),
        "diagonal_scaling_ready": flags.get("enough_for_diagonal_scaling_prototype"),
        "fhl_probe_ready": flags.get("enough_for_fhl_export_probe"),
        "has_samples": flags.get("has_source_samples"),
        "has_coeffs": flags.get("has_fourier_coefficients"),
        "has_residuals": flags.get("has_residual_coefficients_or_samples"),
        "has_matrix": flags.get("has_finite_matrix_or_jacobian"),
        "has_inverse": flags.get("has_approx_inverse_or_preconditioner"),
        "has_tail_profile": flags.get("has_modewise_tail_profile"),
        "missing": r.get("missing_for_full_stage1_success"),
        "candidate_path": r.get("candidate_path"),
        "residual_probe": r.get("raw_residual_recompute_probe"),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Print compact Phase 2AA-A raw-data audit report.")
    ap.add_argument("--audit", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    audit = load(args.audit)
    records = audit.get("records", []) if isinstance(audit, dict) else []
    summary = audit.get("summary", {}) if isinstance(audit, dict) else {}
    # Prioritize failures and pilot rows in the printed report.
    pilots = [r for r in records if r.get("index") in {5, 133, 114, 119, 142, 131, 120, 15, 155, 11}]
    not_ready = [r for r in records if not r.get("raw_data_stage1_ready")]
    compact = {
        "report_name": "phase2aa_stage1_raw_data_fast_report",
        "audit_path": args.audit,
        "summary": summary,
        "pilot_records": [thin_record(r) for r in pilots[:20]],
        "first_not_ready_records": [thin_record(r) for r in not_ready[:20]],
        "next_actions": summary.get("next_actions"),
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(compact, indent=2, sort_keys=True) + "\n")
    print(json.dumps(compact, indent=2, sort_keys=True))
    print(f"WROTE: {out}")


if __name__ == "__main__":
    main()

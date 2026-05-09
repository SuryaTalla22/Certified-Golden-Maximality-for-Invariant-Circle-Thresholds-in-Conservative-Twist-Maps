from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence
import math

import numpy as np

from .phase4i_common import (
    derivative_l1_nu,
    ensure_dir,
    fft_coeff,
    l1_nu,
    load_seed,
    modes,
    scalar_residual_on_grid_from_core,
    sanitize_float_tag,
    shell_summaries,
    spectral_derivative,
    top_modes,
    write_json,
    csv_write,
)


@dataclass
class ForensicsConfig:
    npz_path: str
    grid_factors: Sequence[int]
    nu_grid: Sequence[float]
    out_dir: str
    omega_override: Optional[float] = None
    force: bool = False
    sign: int = 1
    top_count: int = 30


def forensic_record_path(out_dir: str, npz_path: str) -> Path:
    return Path(out_dir) / "records" / (Path(npz_path).stem + ".phase4i_forensics.json")


def audit_seed_spectrum(cfg: ForensicsConfig) -> Dict[str, Any]:
    seed = load_seed(cfg.npz_path, omega_override=cfg.omega_override)
    out_path = forensic_record_path(cfg.out_dir, cfg.npz_path)
    if out_path.exists() and not cfg.force:
        import json
        with open(out_path, "r", encoding="utf-8") as f:
            return json.load(f)

    rows_by_grid: List[Dict[str, Any]] = []
    native_R = scalar_residual_on_grid_from_core(seed.u, seed.K, seed.omega, seed.M, sign=cfg.sign)
    native_dR = spectral_derivative(native_R)
    for gf in cfg.grid_factors:
        L = int(seed.M * int(gf))
        R = scalar_residual_on_grid_from_core(seed.u, seed.K, seed.omega, L, sign=cfg.sign)
        dR = spectral_derivative(R)
        c_abs = np.abs(fft_coeff(R))
        dc_abs = np.abs(fft_coeff(dR))
        nu_rows = []
        for nu in cfg.nu_grid:
            nu_rows.append({
                "nu": float(nu),
                "residual_l1_nu": l1_nu(R, float(nu)),
                "derivative_residual_l1_nu": derivative_l1_nu(R, float(nu)),
                "u_l1_nu_native_interp": l1_nu(seed.u if L == seed.M else R*0 + 0, float(nu)) if L == seed.M else None,
            })
        rows_by_grid.append({
            "grid_factor": int(gf),
            "grid_size": int(L),
            "scalar_residual_linf": float(np.max(np.abs(R))),
            "derivative_residual_linf": float(np.max(np.abs(dR))),
            "residual_l1": float(np.sum(c_abs)),
            "derivative_residual_l1": float(np.sum(dc_abs)),
            "nu_rows": nu_rows,
            "residual_shells": shell_summaries(c_abs),
            "derivative_residual_shells": shell_summaries(dc_abs),
            "top_residual_modes": top_modes(R, cfg.top_count, derivative_weight=False),
            "top_derivative_residual_modes": top_modes(R, cfg.top_count, derivative_weight=True),
        })

    record = {
        "schema": "theorem_iii_trackb_phase4i_forensics_record_v1",
        "diagnostic_only": True,
        "theorem_facing": False,
        "promotion_allowed": False,
        "npz_path": cfg.npz_path,
        "K": float(seed.K),
        "M": int(seed.M),
        "omega": float(seed.omega),
        "native_scalar_residual_linf": float(np.max(np.abs(native_R))),
        "native_derivative_residual_linf": float(np.max(np.abs(native_dR))),
        "native_derivative_to_scalar_linf_ratio": float(np.max(np.abs(native_dR)) / max(np.max(np.abs(native_R)), 1e-300)),
        "max_scalar_residual_linf_over_grids": float(max(r["scalar_residual_linf"] for r in rows_by_grid)),
        "max_derivative_residual_linf_over_grids": float(max(r["derivative_residual_linf"] for r in rows_by_grid)),
        "grid_rows": rows_by_grid,
    }
    write_json(out_path, record)
    return record


def compact_row(record: Dict[str, Any]) -> Dict[str, Any]:
    grid_rows = record.get("grid_rows", [])
    worst_der = max(grid_rows, key=lambda r: r.get("derivative_residual_linf", 0.0)) if grid_rows else {}
    worst_res = max(grid_rows, key=lambda r: r.get("scalar_residual_linf", 0.0)) if grid_rows else {}
    return {
        "K": record.get("K"),
        "M": record.get("M"),
        "npz_path": record.get("npz_path"),
        "native_scalar_residual_linf": record.get("native_scalar_residual_linf"),
        "native_derivative_residual_linf": record.get("native_derivative_residual_linf"),
        "native_derivative_to_scalar_linf_ratio": record.get("native_derivative_to_scalar_linf_ratio"),
        "max_scalar_residual_linf_over_grids": record.get("max_scalar_residual_linf_over_grids"),
        "max_derivative_residual_linf_over_grids": record.get("max_derivative_residual_linf_over_grids"),
        "worst_scalar_grid_size": worst_res.get("grid_size"),
        "worst_derivative_grid_size": worst_der.get("grid_size"),
        "record_path": str(forensic_record_path(Path(record.get("npz_path", ".")).parent.as_posix(), record.get("npz_path", ""))) if False else "",
    }


def run_phase4i_forensics(
    npz_paths: Sequence[str],
    grid_factors: Sequence[int],
    nu_grid: Sequence[float],
    out_dir: str,
    workers: int = 1,
    omega_override: Optional[float] = None,
    force: bool = False,
) -> Dict[str, Any]:
    ensure_dir(Path(out_dir) / "records")
    cfgs = [
        ForensicsConfig(str(p), grid_factors, nu_grid, out_dir, omega_override=omega_override, force=force)
        for p in npz_paths
    ]
    if workers and workers > 1 and len(cfgs) > 1:
        from concurrent.futures import ProcessPoolExecutor
        with ProcessPoolExecutor(max_workers=min(int(workers), len(cfgs))) as ex:
            records = list(ex.map(audit_seed_spectrum, cfgs))
    else:
        records = [audit_seed_spectrum(c) for c in cfgs]
    rows = []
    for rec in records:
        row = compact_row(rec)
        row["record_path"] = str(forensic_record_path(out_dir, rec["npz_path"]))
        rows.append(row)
    rows.sort(key=lambda r: (r.get("max_derivative_residual_linf_over_grids") or math.inf))
    summary = {
        "schema": "theorem_iii_trackb_phase4i_forensics_summary_v1",
        "status": "phase4i-spectral-forensics-complete",
        "diagnostic_only": True,
        "counts": {"tasks": len(cfgs), "completed_records": len(records)},
        "parameters": {
            "grid_factors": list(map(int, grid_factors)),
            "nu_grid": list(map(float, nu_grid)),
            "workers_requested": int(workers),
            "workers_used": min(int(workers), len(cfgs)) if workers else 1,
        },
        "top_candidates": rows,
    }
    write_json(Path(out_dir) / "phase4i_forensics_summary.json", summary)
    csv_write(Path(out_dir) / "phase4i_forensics_results.csv", rows)
    return summary

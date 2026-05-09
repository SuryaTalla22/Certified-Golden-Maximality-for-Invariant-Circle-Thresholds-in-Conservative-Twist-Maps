#!/usr/bin/env python3
from __future__ import annotations

"""One-command regeneration and verification of the theorem-facing proof chain.

This script is the command-line successor to the old end-to-end notebook.  It
regenerates theorem-facing artifacts in the correct dependency order:

  1. Theorem I/II workstream certificate.
  2. Theorem IV upper/lower obstruction stack.
  3. Track-B Theorem III lower-anchor certificate, installed into stage_cache.
  4. Theorem V and downstream identification/VI/VII/VIII discharge objects.
  5. Final replay/validation commands and a regenerated hash ledger.

The script is intentionally explicit and cache-aware.  With --from-scratch it
removes theorem-facing stage-cache outputs before rebuilding.  It does not use
notebooks and it does not rely on the frozen HASHES.sha256 file, because a fresh
independent regeneration may legitimately produce different artifact bytes due
to timestamps or ordering while still passing theorem-facing replay.
"""

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping


def _bootstrap_project_root(start: Path | None = None) -> Path:
    """Make the local package importable before theorem-suite imports run."""
    start = (start or Path.cwd()).resolve()
    for cand in [start, *start.parents]:
        if (cand / "kam_theorem_suite").is_dir() and (cand / "scripts").is_dir():
            return cand
    # If the script is launched from scripts/, also try its parent.
    script_parent = Path(__file__).resolve().parent.parent
    if (script_parent / "kam_theorem_suite").is_dir() and (script_parent / "scripts").is_dir():
        return script_parent
    raise RuntimeError("Could not locate repository root containing kam_theorem_suite/ and scripts/.")


_BOOTSTRAP_PROJECT_ROOT = _bootstrap_project_root()
if str(_BOOTSTRAP_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_BOOTSTRAP_PROJECT_ROOT))

for _key in [
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "NUMEXPR_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
]:
    os.environ.setdefault(_key, "1")

import numpy as np

from kam_theorem_suite import proof_driver
from kam_theorem_suite.standard_map import HarmonicFamily
from kam_theorem_suite.golden_supercritical import generate_golden_convergent_specs
from kam_theorem_suite.adaptive_incompatibility import (
    build_adaptive_incompatibility_entry_certificate,
    build_adaptive_incompatibility_atlas_certificate_from_entries,
    build_golden_adaptive_incompatibility_certificate_from_atlas,
)
from kam_theorem_suite.adaptive_tail_coherence import (
    build_golden_adaptive_tail_coherence_certificate_from_entries,
)
from kam_theorem_suite.theorem_iv_tail_transport import (
    build_golden_tail_band_transport_certificate,
    make_tail_transport_entry_dicts,
)


def find_project_root(start: Path | None = None) -> Path:
    start = (start or Path.cwd()).resolve()
    for cand in [start, *start.parents]:
        if (cand / "kam_theorem_suite").is_dir() and (cand / "scripts").is_dir():
            return cand
    raise RuntimeError("Could not locate repository root containing kam_theorem_suite/ and scripts/.")


PROJECT_ROOT = find_project_root()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

BASE_K_VALUES = [0.20, 0.25]
CHALLENGER_SPECS = None
FAMILY = HarmonicFamily()
ARTIFACT_DIR = PROJECT_ROOT / "artifacts" / "final_discharge"
STAGE_CACHE_DIR = ARTIFACT_DIR / "stage_cache"


def now_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def relpath(path: Path, root: Path = PROJECT_ROOT) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except Exception:
        return str(path)


def jsonable(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {str(k): jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [jsonable(v) for v in obj]
    if isinstance(obj, np.ndarray):
        return jsonable(obj.tolist())
    if isinstance(obj, (np.integer, np.floating, np.bool_)):
        return obj.item()
    if isinstance(obj, Path):
        return str(obj)
    if hasattr(obj, "to_dict"):
        try:
            return jsonable(obj.to_dict())
        except Exception:
            pass
    if hasattr(obj, "tolist") and not isinstance(obj, (str, bytes)):
        try:
            return jsonable(obj.tolist())
        except Exception:
            pass
    return obj


def dump_json(path: Path, obj: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(jsonable(obj), indent=2, sort_keys=True), encoding="utf-8")
    print(f"Wrote {relpath(path)}", flush=True)
    return path


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def clean_paths(paths: Iterable[Path], *, dry_run: bool = False) -> None:
    for path in paths:
        if path.exists():
            print(f"Removing {relpath(path)}")
            if dry_run:
                continue
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()


def stage_cache_path(name: str) -> Path:
    return STAGE_CACHE_DIR / f"{name}.json"


def build_or_load_stage(
    name: str,
    builder: Callable[[], Any],
    *,
    use_cache: bool,
    force_rebuild: bool,
    timings: dict[str, Any],
) -> tuple[Any, Path]:
    path = stage_cache_path(name)
    path.parent.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    source = "built"
    print(f"\nStarting stage: {name}", flush=True)
    if use_cache and path.exists() and not force_rebuild:
        obj = load_json(path)
        source = "cache"
    else:
        obj = builder()
        dump_json(path, obj)
    dt = time.time() - t0
    timings[name] = {"source": source, "seconds": dt, "cache_path": relpath(path)}
    print(f"[{source}] {name}: {dt:.2f}s", flush=True)
    return obj, path


def safe_stage_name_component(value: Any) -> str:
    text = str(value).replace("+", "p").replace("-", "m").replace(".", "p")
    return "".join(ch for ch in text if ch.isalnum() or ch == "_")


def theorem_iv_upper_params(live_kwargs: dict[str, Any]) -> dict[str, Any]:
    return {
        "rho": live_kwargs.get("rho"),
        "crossing_center": live_kwargs.get("crossing_center", 0.971635406),
        "atlas_shifts": tuple(live_kwargs.get("atlas_shifts", (-6.0e-4, -3.0e-4, 0.0, 3.0e-4, 6.0e-4))),
        "n_terms": live_kwargs.get("n_terms", 10),
        "keep_last": live_kwargs.get("keep_last", 6),
        "min_q": live_kwargs.get("min_q", 5),
        "max_q": live_kwargs.get("max_q"),
        "crossing_half_width": live_kwargs.get("crossing_half_width", 2.5e-3),
        "band_offset": live_kwargs.get("band_offset", 5.5e-2),
        "band_width": live_kwargs.get("band_width", 3.0e-2),
        "target_residue": live_kwargs.get("target_residue", 0.25),
        "crossing_max_depth": live_kwargs.get("crossing_max_depth", 5),
        "crossing_min_width": live_kwargs.get("crossing_min_width", 5e-4),
        "crossing_n_pieces": live_kwargs.get("crossing_n_pieces", 2),
        "band_initial_subdivisions": live_kwargs.get("band_initial_subdivisions", 4),
        "band_max_depth": live_kwargs.get("band_max_depth", 4),
        "band_min_width": live_kwargs.get("band_min_width", 5e-4),
        "min_tail_members": live_kwargs.get("min_tail_members", 2),
        "min_cluster_size": live_kwargs.get("min_cluster_size", 2),
        "min_q_support_fraction": live_kwargs.get("min_q_support_fraction", 0.6),
        "min_entry_tail_coverage": live_kwargs.get("min_entry_tail_coverage", 0.75),
        "min_tail_support_fraction": live_kwargs.get("min_tail_support_fraction", 0.75),
        "tail_replacement_min_q": live_kwargs.get("tail_replacement_min_q", 144),
    }


def theorem_iv_lower_stage_kwargs(live_kwargs: dict[str, Any]) -> dict[str, Any]:
    return {
        "rho": live_kwargs.get("rho"),
        "lower_shift_grid": live_kwargs.get("lower_shift_grid", (-0.015, 0.0, 0.015)),
        "lower_resolution_sets": live_kwargs.get("lower_resolution_sets", ((64, 96, 128), (80, 112, 144))),
        "sigma_cap": live_kwargs.get("sigma_cap", 0.04),
        "use_multiresolution": live_kwargs.get("use_multiresolution", True),
        "oversample_factor": live_kwargs.get("oversample_factor", 8),
        "lower_min_cluster_size": live_kwargs.get("lower_min_cluster_size", 2),
    }


def build_theorem_iv_upper_tail_coherence_staged(
    *,
    live_kwargs: dict[str, Any],
    use_cache: bool,
    force_rebuild: bool,
    timings: dict[str, Any],
) -> dict[str, Any]:
    params = theorem_iv_upper_params(live_kwargs)
    shift_reports = []
    for shift in params["atlas_shifts"]:
        shift_name = safe_stage_name_component(f"{shift:.6g}")
        specs = generate_golden_convergent_specs(
            rho=params["rho"],
            n_terms=params["n_terms"],
            keep_last=params["keep_last"],
            min_q=params["min_q"],
            max_q=params["max_q"],
            crossing_center=float(params["crossing_center"]) + float(shift),
            crossing_half_width=params["crossing_half_width"],
            band_offset=params["band_offset"],
            band_width=params["band_width"],
        )
        tail_replacement_min_q = int(params.get("tail_replacement_min_q", 144))
        anchor_specs = [s for s in specs if int(s.q) < tail_replacement_min_q]
        replacement_specs = [s for s in specs if int(s.q) >= tail_replacement_min_q]

        entry_dicts: list[dict[str, Any]] = []
        for spec in anchor_specs:
            spec_name = safe_stage_name_component(spec.label)
            stage_name = f"theorem_iv_upper_shift_{shift_name}_{spec_name}"
            entry, _ = build_or_load_stage(
                stage_name,
                lambda spec=spec, entry_dicts=entry_dicts: build_adaptive_incompatibility_entry_certificate(
                    spec.to_approximant_window_spec(),
                    family=FAMILY,
                    target_residue=params["target_residue"],
                    crossing_max_depth=params["crossing_max_depth"],
                    crossing_min_width=params["crossing_min_width"],
                    crossing_n_pieces=params["crossing_n_pieces"],
                    band_initial_subdivisions=params["band_initial_subdivisions"],
                    band_max_depth=params["band_max_depth"],
                    band_min_width=params["band_min_width"],
                    use_seed_propagation=True,
                    previous_entry_dicts=entry_dicts,
                ).to_dict(),
                use_cache=use_cache,
                force_rebuild=force_rebuild,
                timings=timings,
            )
            entry_dicts.append(entry)

        tail_transport = None
        if replacement_specs:
            replacement_window_specs = [s.to_approximant_window_spec() for s in replacement_specs]
            tail_transport, _ = build_or_load_stage(
                f"theorem_iv_upper_shift_{shift_name}_tail_transport",
                lambda entry_dicts=entry_dicts, replacement_window_specs=replacement_window_specs: build_golden_tail_band_transport_certificate(
                    entry_dicts,
                    replacement_window_specs,
                    family=FAMILY,
                    rho=params["rho"],
                    target_residue=params["target_residue"],
                    explicit_tail_cutoff_q=max(int(e["q"]) for e in entry_dicts) if entry_dicts else int(params["tail_replacement_min_q"]) - 1,
                ).to_dict(),
                use_cache=use_cache,
                force_rebuild=force_rebuild,
                timings=timings,
            )
            derived_rows = {int(r["q"]): r for r in (tail_transport or {}).get("derived_rows", [])}
            derived_specs = [s for s in replacement_specs if int(s.q) in derived_rows]
            missing_specs = [s for s in replacement_specs if int(s.q) not in derived_rows]
            if derived_specs:
                entry_dicts.extend(make_tail_transport_entry_dicts(tail_transport, [s.to_approximant_window_spec() for s in derived_specs]))
            for spec in missing_specs:
                spec_name = safe_stage_name_component(spec.label)
                stage_name = f"theorem_iv_upper_shift_{shift_name}_{spec_name}"
                entry, _ = build_or_load_stage(
                    stage_name,
                    lambda spec=spec: build_adaptive_incompatibility_entry_certificate(
                        spec.to_approximant_window_spec(),
                        family=FAMILY,
                        target_residue=params["target_residue"],
                        crossing_max_depth=params["crossing_max_depth"],
                        crossing_min_width=params["crossing_min_width"],
                        crossing_n_pieces=params["crossing_n_pieces"],
                        band_initial_subdivisions=params["band_initial_subdivisions"],
                        band_max_depth=params["band_max_depth"],
                        band_min_width=params["band_min_width"],
                        use_seed_propagation=True,
                    ).to_dict(),
                    use_cache=use_cache,
                    force_rebuild=force_rebuild,
                    timings=timings,
                )
                entry_dicts.append(entry)

        shift_report, _ = build_or_load_stage(
            f"theorem_iv_upper_shift_{shift_name}_report",
            lambda entry_dicts=entry_dicts, shift=shift, specs=specs, tail_transport=tail_transport: build_golden_adaptive_incompatibility_certificate_from_atlas(
                build_adaptive_incompatibility_atlas_certificate_from_entries(
                    entry_dicts,
                    family=FAMILY,
                    min_tail_members=params["min_tail_members"],
                ),
                family=FAMILY,
                rho=float(specs[-1].rho if specs else (params["rho"] if params["rho"] is not None else 0.0)),
                generated_convergents=[s.to_dict() for s in specs],
            ).to_dict(),
            use_cache=use_cache,
            force_rebuild=force_rebuild,
            timings=timings,
        )
        shift_reports.append({
            "atlas_shift": float(shift),
            "crossing_center": float(params["crossing_center"]) + float(shift),
            "theorem_status": str(shift_report.get("theorem_status", "unknown")),
            "selected_upper_lo": shift_report.get("selected_upper_lo"),
            "selected_upper_hi": shift_report.get("selected_upper_hi"),
            "selected_barrier_lo": shift_report.get("selected_barrier_lo"),
            "selected_barrier_hi": shift_report.get("selected_barrier_hi"),
            "incompatibility_gap": shift_report.get("incompatibility_gap"),
            "witness_qs": [int(x) for x in (((shift_report.get("atlas", {}) or {}).get("hyperbolic_tail", {}) or {}).get("witness_qs", []))],
            "exact_tail_qs": [int(x) for x in (((shift_report.get("atlas", {}) or {}).get("hyperbolic_tail", {}) or {}).get("tail_qs", []))],
            "generated_qs": [int(x) for x in (((shift_report.get("atlas", {}) or {}).get("hyperbolic_tail", {}) or {}).get("generated_qs", []))],
            "tail_transport_certificate": tail_transport,
            "report": shift_report,
        })

    theorem_iv_upper_tail_coherence, _ = build_or_load_stage(
        "theorem_iv_upper_tail_coherence",
        lambda: build_golden_adaptive_tail_coherence_certificate_from_entries(
            shift_reports,
            family=FAMILY,
            rho=params["rho"],
            crossing_center=params["crossing_center"],
            atlas_shifts=params["atlas_shifts"],
            min_cluster_size=params["min_cluster_size"],
            min_tail_members=params["min_tail_members"],
            min_q_support_fraction=params["min_q_support_fraction"],
            min_entry_tail_coverage=params["min_entry_tail_coverage"],
            min_tail_support_fraction=params["min_tail_support_fraction"],
        ).to_dict(),
        use_cache=use_cache,
        force_rebuild=force_rebuild,
        timings=timings,
    )
    return theorem_iv_upper_tail_coherence


def build_theorem_i_ii_and_iv(*, live_kwargs: dict[str, Any], use_cache: bool, force_rebuild: bool, timings: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    theorem_i_ii, _ = build_or_load_stage(
        "theorem_i_ii",
        lambda: proof_driver.build_golden_theorem_i_ii_report(family=FAMILY, **live_kwargs),
        use_cache=use_cache,
        force_rebuild=force_rebuild,
        timings=timings,
    )
    theorem_iv_lower_neighborhood, _ = build_or_load_stage(
        "theorem_iv_lower_neighborhood",
        lambda: proof_driver.build_golden_theorem_iv_lower_neighborhood_report(
            base_K_values=BASE_K_VALUES,
            family=FAMILY,
            **theorem_iv_lower_stage_kwargs(live_kwargs),
        ),
        use_cache=use_cache,
        force_rebuild=force_rebuild,
        timings=timings,
    )
    theorem_iv_upper_tail_coherence = build_theorem_iv_upper_tail_coherence_staged(
        live_kwargs=live_kwargs,
        use_cache=use_cache,
        force_rebuild=force_rebuild,
        timings=timings,
    )
    theorem_iv_upper_bridge, _ = build_or_load_stage(
        "theorem_iv_upper_bridge",
        lambda: proof_driver.build_golden_incompatibility_theorem_bridge_report(
            family=FAMILY,
            adaptive_tail_coherence_certificate=theorem_iv_upper_tail_coherence,
            **live_kwargs,
        ),
        use_cache=use_cache,
        force_rebuild=force_rebuild,
        timings=timings,
    )
    theorem_iv_upper_bridge_promotion, _ = build_or_load_stage(
        "theorem_iv_upper_bridge_promotion",
        lambda: proof_driver.build_golden_incompatibility_strict_bridge_report(
            family=FAMILY,
            adaptive_tail_coherence_certificate=theorem_iv_upper_tail_coherence,
            **live_kwargs,
        ),
        use_cache=use_cache,
        force_rebuild=force_rebuild,
        timings=timings,
    )
    theorem_iv_upper_support_core, _ = build_or_load_stage(
        "theorem_iv_upper_support_core",
        lambda: proof_driver.build_golden_adaptive_support_core_neighborhood_report(
            family=FAMILY,
            baseline_tail_coherence_certificate=theorem_iv_upper_tail_coherence,
            **live_kwargs,
        ),
        use_cache=use_cache,
        force_rebuild=force_rebuild,
        timings=timings,
    )
    theorem_iv_upper_tail_aware, _ = build_or_load_stage(
        "theorem_iv_upper_tail_aware",
        lambda: proof_driver.build_golden_adaptive_tail_aware_neighborhood_report(
            family=FAMILY,
            baseline_tail_coherence_certificate=theorem_iv_upper_tail_coherence,
            support_core_neighborhood_certificate=theorem_iv_upper_support_core,
            **live_kwargs,
        ),
        use_cache=use_cache,
        force_rebuild=force_rebuild,
        timings=timings,
    )
    theorem_iv_upper_tail_stability, _ = build_or_load_stage(
        "theorem_iv_upper_tail_stability",
        lambda: proof_driver.build_golden_adaptive_tail_stability_report(family=FAMILY, **live_kwargs),
        use_cache=use_cache,
        force_rebuild=force_rebuild,
        timings=timings,
    )
    theorem_iv_upper_bridge_profile, _ = build_or_load_stage(
        "theorem_iv_upper_bridge_profile",
        lambda: proof_driver.build_golden_incompatibility_bridge_profile_report(
            family=FAMILY,
            adaptive_tail_coherence_certificate=theorem_iv_upper_tail_coherence,
            **live_kwargs,
        ),
        use_cache=use_cache,
        force_rebuild=force_rebuild,
        timings=timings,
    )
    theorem_iv, _ = build_or_load_stage(
        "theorem_iv",
        lambda: proof_driver.build_golden_theorem_iv_report(
            base_K_values=BASE_K_VALUES,
            family=FAMILY,
            lower_neighborhood_stability_certificate=theorem_iv_lower_neighborhood,
            upper_tail_coherence_certificate=theorem_iv_upper_tail_coherence,
            upper_bridge_certificate=theorem_iv_upper_bridge,
            upper_bridge_promotion_certificate=theorem_iv_upper_bridge_promotion,
            upper_support_core_neighborhood_certificate=theorem_iv_upper_support_core,
            upper_tail_aware_neighborhood_certificate=theorem_iv_upper_tail_aware,
            upper_tail_stability_certificate=theorem_iv_upper_tail_stability,
            upper_bridge_profile_certificate=theorem_iv_upper_bridge_profile,
            **live_kwargs,
        ),
        use_cache=use_cache,
        force_rebuild=force_rebuild,
        timings=timings,
    )
    return theorem_i_ii, theorem_iv


def run_theorem_iii_trackb(*, args: argparse.Namespace, stamp: str) -> dict[str, Any]:
    cmd = [
        sys.executable,
        "scripts/regenerate_theorem_iii_trackb_from_scratch.py",
        "--workers", str(args.workers),
        "--copy-to-stage-cache",
        "--theorem-i-artifact", "artifacts/final_discharge/stage_cache/theorem_i_ii.json",
        "--theorem-ii-artifact", "artifacts/final_discharge/stage_cache/theorem_i_ii.json",
        "--theorem-iv-artifact", "artifacts/final_discharge/stage_cache/theorem_iv.json",
        "--logs-dir", f"artifacts/full_regeneration/{stamp}/logs/theorem_iii_trackb",
        "--manifest-out", f"artifacts/full_regeneration/{stamp}/theorem_iii_trackb_regeneration_manifest.json",
    ]
    if args.force:
        cmd.append("--force")
    if args.from_scratch:
        cmd.append("--from-scratch")
    if args.dry_run:
        cmd.append("--dry-run")
    if args.skip_phase5a:
        cmd.append("--skip-phase5a")
    if args.skip_phase5b:
        cmd.append("--skip-phase5b")
    print(f"\n[theorem_iii_trackb] $ {' '.join(cmd)}", flush=True)
    t0 = time.time()
    if args.dry_run:
        rc = 0
    else:
        env = os.environ.copy()
        env["PYTHONPATH"] = str(PROJECT_ROOT) + (os.pathsep + env.get("PYTHONPATH", "") if env.get("PYTHONPATH") else "")
        rc = subprocess.call(cmd, cwd=PROJECT_ROOT, env=env)
    dt = time.time() - t0
    if rc != 0:
        raise SystemExit(f"Theorem III Track-B regeneration failed with exit code {rc}.")
    manifest_path = PROJECT_ROOT / f"artifacts/full_regeneration/{stamp}/theorem_iii_trackb_regeneration_manifest.json"
    return {
        "cmd": cmd,
        "returncode": rc,
        "elapsed_seconds": dt,
        "manifest": relpath(manifest_path),
    }




def _compact_list(value: Any, *, max_items: int | None = 50) -> list[str]:
    """Return a small string list suitable for final acceptance summaries."""
    if value is None:
        return []
    if isinstance(value, (str, bytes)):
        items = [value]
    else:
        try:
            items = list(value)
        except TypeError:
            items = [value]
    out = [str(x) for x in items]
    if max_items is not None and len(out) > max_items:
        return out[:max_items] + [f"... truncated {len(out) - max_items} additional entries ..."]
    return out


def _compact_theorem_status_entry(label: str, obj: Mapping[str, Any]) -> dict[str, Any]:
    """Small theorem-status row that avoids embedding multi-GB certificate payloads."""
    remaining_true = _compact_list(obj.get("remaining_true_mathematical_burden", []), max_items=25)
    paper_workstream = _compact_list(obj.get("remaining_workstream_paper_grade_burden", []), max_items=25)
    paper_exhaustion = _compact_list(obj.get("remaining_exhaustion_paper_grade_burden", []), max_items=25)
    active = _compact_list(obj.get("active_assumptions", []), max_items=25)
    upstream = _compact_list(obj.get("upstream_active_assumptions", []), max_items=25)
    local = _compact_list(obj.get("local_active_assumptions", []), max_items=25)
    return {
        "label": label,
        "theorem_status": obj.get("theorem_status") or obj.get("status") or obj.get("certificate_status"),
        "statement_mode": obj.get("statement_mode"),
        "final_certificate_ready_for_code_path": bool(obj.get("final_certificate_ready_for_code_path", False)),
        "final_certificate_ready_for_paper": bool(obj.get("final_certificate_ready_for_paper", False)),
        "remaining_true_mathematical_burden": remaining_true,
        "remaining_workstream_paper_grade_burden": paper_workstream,
        "remaining_exhaustion_paper_grade_burden": paper_exhaustion,
        "active_assumptions": active,
        "upstream_active_assumptions": upstream,
        "local_active_assumptions": local,
        "active_assumption_count": len(active),
        "upstream_active_assumption_count": len(upstream),
        "local_active_assumption_count": len(local),
    }


def _compact_geometry_summary(theorem_viii: Mapping[str, Any]) -> dict[str, Any]:
    geom = theorem_viii.get("current_reduction_geometry_summary")
    if isinstance(geom, Mapping):
        out = dict(geom)
    else:
        out = {}
    # Keep only the reviewer-facing scalar/status fields.  Avoid copying any large witness arrays.
    keep = {
        "available", "status", "minimum_certified_margin", "source",
        "golden_lower_endpoint", "nongolden_upper_endpoint", "final_endpoint_margin",
        "delta_final", "margin", "endpoint_gap",
    }
    compact = {str(k): jsonable(v) for k, v in out.items() if str(k) in keep or isinstance(v, (str, int, float, bool, type(None)))}
    if "available" not in compact:
        compact["available"] = bool(out)
    return compact


def build_compact_live_theorem_program_report(
    *,
    theorem_i_ii: Mapping[str, Any],
    theorem_iv: Mapping[str, Any],
    theorem_v: Mapping[str, Any],
    identification: Mapping[str, Any],
    theorem_vi: Mapping[str, Any],
    theorem_vii: Mapping[str, Any],
    theorem_viii: Mapping[str, Any],
) -> dict[str, Any]:
    """Build a small final status report without embedding giant theorem objects.

    The full Theorem VIII discharge object can be several GB.  The old status
    report embedded all subreports, causing a second multi-GB JSON serialization
    at the end of a successful regeneration.  This compact report preserves the
    theorem-facing acceptance fields used by the top-level acceptance checks and
    records stage-cache paths/hashes for auditability, while leaving the full
    objects in artifacts/final_discharge/stage_cache/.
    """
    theorem_status_summary = {
        "theorem_i_ii": _compact_theorem_status_entry("Theorems I-II", theorem_i_ii),
        "theorem_iv": _compact_theorem_status_entry("Theorem IV", theorem_iv),
        "theorem_v": _compact_theorem_status_entry("Theorem V", theorem_v),
        "identification_seam": _compact_theorem_status_entry("Identification seam", identification),
        "theorem_vi": _compact_theorem_status_entry("Theorem VI", theorem_vi),
        "theorem_vii": _compact_theorem_status_entry("Theorem VII", theorem_vii),
        "theorem_viii": _compact_theorem_status_entry("Theorem VIII", theorem_viii),
    }
    geometry = _compact_geometry_summary(theorem_viii)
    true_burden = _compact_list(theorem_viii.get("remaining_true_mathematical_burden", []), max_items=None)
    paper_grade = sorted({
        *_compact_list(theorem_viii.get("remaining_workstream_paper_grade_burden", []), max_items=None),
        *_compact_list(theorem_viii.get("remaining_exhaustion_paper_grade_burden", []), max_items=None),
    })
    implementation_summary = {
        "discharge_aware": True,
        "overall_theorem_status": theorem_status_summary["theorem_viii"].get("theorem_status"),
        "overall_statement_mode": theorem_status_summary["theorem_viii"].get("statement_mode"),
        "current_reduction_geometry_available": bool(geometry.get("available", False)),
        "current_reduction_geometry_status": None if geometry.get("status") is None else str(geometry.get("status")),
        "current_reduction_geometry_minimum_certified_margin": geometry.get("minimum_certified_margin"),
        "current_reduction_geometry_source": geometry.get("source"),
        "theorem_viii_final_status": None if theorem_viii.get("theorem_status") is None else str(theorem_viii.get("theorem_status")),
        "final_universal_theorem_ready_for_code_path": bool(theorem_viii.get("final_certificate_ready_for_code_path", False)),
        "final_universal_theorem_ready_for_paper": bool(theorem_viii.get("final_certificate_ready_for_paper", False)),
        "true_mathematical_burden_remaining": true_burden,
        "paper_grade_burden_remaining": paper_grade,
        "workstream_residual_caveat": _compact_list(theorem_viii.get("remaining_workstream_paper_grade_burden", []), max_items=None),
        "compact_report": True,
        "compact_report_reason": "Full subreports are kept as stage-cache artifacts; this report stores only acceptance/status fields to avoid duplicating multi-GB theorem objects.",
    }
    stage_cache_files = {}
    for name in [
        "theorem_i_ii", "theorem_iii", "theorem_iv", "theorem_v_compressed", "identification_theorem",
        "theorem_vi_discharge", "theorem_vii_discharge", "theorem_viii_base", "theorem_viii_discharge",
    ]:
        path = stage_cache_path(name)
        if path.exists():
            stage_cache_files[name] = {
                "path": relpath(path),
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
    return {
        "report_kind": "golden-theorem-program-discharge-status-report-compact",
        "discharge_aware": True,
        "compact_report": True,
        "theorem_status_summary": theorem_status_summary,
        "theorem_status_rows": list(theorem_status_summary.values()),
        "current_reduction_geometry_summary": geometry,
        "current_reduction_geometry_available": implementation_summary["current_reduction_geometry_available"],
        "current_reduction_geometry_status": implementation_summary["current_reduction_geometry_status"],
        "current_reduction_geometry_minimum_certified_margin": implementation_summary["current_reduction_geometry_minimum_certified_margin"],
        "implementation_summary": implementation_summary,
        "subreports": {
            # Compact, acceptance-facing summaries only.  Full objects remain in stage_cache.
            "theorem_i_ii": theorem_status_summary["theorem_i_ii"],
            "theorem_iv": theorem_status_summary["theorem_iv"],
            "theorem_v": theorem_status_summary["theorem_v"],
            "identification_seam": theorem_status_summary["identification_seam"],
            "theorem_vi": theorem_status_summary["theorem_vi"],
            "theorem_vii": theorem_status_summary["theorem_vii"],
            "theorem_viii": {
                **theorem_status_summary["theorem_viii"],
                "remaining_true_mathematical_burden": true_burden,
                "remaining_workstream_paper_grade_burden": _compact_list(theorem_viii.get("remaining_workstream_paper_grade_burden", []), max_items=None),
                "remaining_exhaustion_paper_grade_burden": _compact_list(theorem_viii.get("remaining_exhaustion_paper_grade_burden", []), max_items=None),
            },
        },
        "stage_cache_files": stage_cache_files,
    }


def build_downstream_from_stage_cache(*, live_kwargs: dict[str, Any], use_cache: bool, force_rebuild: bool, timings: dict[str, Any]) -> dict[str, Any]:
    theorem_i_ii = load_json(stage_cache_path("theorem_i_ii"))
    theorem_iii = load_json(stage_cache_path("theorem_iii"))
    theorem_iv = load_json(stage_cache_path("theorem_iv"))

    theorem_v_bundle, _ = build_or_load_stage(
        "theorem_v",
        lambda: proof_driver.build_golden_theorem_v_batched_report(
            base_K_values=BASE_K_VALUES,
            family=FAMILY,
            theorem_iii_certificate=theorem_iii,
            theorem_iv_certificate=theorem_iv,
            use_cache=use_cache,
            force_rebuild=force_rebuild,
            **live_kwargs,
        ),
        use_cache=use_cache,
        force_rebuild=force_rebuild,
        timings=timings,
    )
    if isinstance(theorem_v_bundle, dict) and "stage_timings" in theorem_v_bundle:
        for stage_name, stage_meta in (theorem_v_bundle.get("stage_timings") or {}).items():
            timings[f"theorem_v::{stage_name}"] = stage_meta
    theorem_v_raw = dict((theorem_v_bundle or {}).get("certificate", theorem_v_bundle))
    theorem_v = dict((theorem_v_bundle or {}).get("downstream_certificate") or (theorem_v_bundle or {}).get("compressed_certificate") or theorem_v_raw)

    identification_shell, _ = build_or_load_stage(
        "identification_shell",
        lambda: proof_driver.build_golden_theorem_ii_to_v_identification_report(
            base_K_values=BASE_K_VALUES,
            family=FAMILY,
            theorem_iii_certificate=theorem_iii,
            theorem_iv_certificate=theorem_iv,
            theorem_v_certificate=theorem_v_raw,
            theorem_v_compressed_certificate=theorem_v,
            **live_kwargs,
        ),
        use_cache=use_cache,
        force_rebuild=force_rebuild,
        timings=timings,
    )
    identification_discharge, _ = build_or_load_stage(
        "identification_discharge",
        lambda: proof_driver.build_golden_theorem_ii_to_v_identification_discharge_report(
            base_K_values=BASE_K_VALUES,
            family=FAMILY,
            theorem_i_ii_certificate=theorem_i_ii,
            theorem_ii_to_v_identification_certificate=identification_shell,
            **live_kwargs,
        ),
        use_cache=use_cache,
        force_rebuild=force_rebuild,
        timings=timings,
    )
    identification_transport_discharge, _ = build_or_load_stage(
        "identification_transport_discharge",
        lambda: proof_driver.build_golden_theorem_ii_to_v_identification_transport_discharge_report(
            base_K_values=BASE_K_VALUES,
            family=FAMILY,
            theorem_v_certificate=theorem_v_raw,
            threshold_identification_discharge_certificate=identification_discharge,
            **live_kwargs,
        ),
        use_cache=use_cache,
        force_rebuild=force_rebuild,
        timings=timings,
    )
    identification, _ = build_or_load_stage(
        "identification_theorem",
        lambda: proof_driver.build_golden_theorem_ii_to_v_identification_theorem_report(
            base_K_values=BASE_K_VALUES,
            family=FAMILY,
            threshold_identification_transport_discharge_certificate=identification_transport_discharge,
            **live_kwargs,
        ),
        use_cache=use_cache,
        force_rebuild=force_rebuild,
        timings=timings,
    )
    theorem_vi_base, _ = build_or_load_stage(
        "theorem_vi_base",
        lambda: proof_driver.build_golden_theorem_vi_report(
            base_K_values=BASE_K_VALUES,
            family=FAMILY,
            threshold_identification_certificate=identification,
            **live_kwargs,
        ),
        use_cache=use_cache,
        force_rebuild=force_rebuild,
        timings=timings,
    )
    theorem_vi, _ = build_or_load_stage(
        "theorem_vi_discharge",
        lambda: proof_driver.build_golden_theorem_vi_discharge_report(
            base_K_values=BASE_K_VALUES,
            family=FAMILY,
            theorem_vi_certificate=theorem_vi_base,
            threshold_identification_transport_discharge_certificate=identification_transport_discharge,
            **live_kwargs,
        ),
        use_cache=use_cache,
        force_rebuild=force_rebuild,
        timings=timings,
    )
    theorem_vii_base, _ = build_or_load_stage(
        "theorem_vii_base",
        lambda: proof_driver.build_golden_theorem_vii_report(
            base_K_values=BASE_K_VALUES,
            challenger_specs=CHALLENGER_SPECS,
            family=FAMILY,
            theorem_vi_envelope_discharge_certificate=theorem_vi,
            **live_kwargs,
        ),
        use_cache=use_cache,
        force_rebuild=force_rebuild,
        timings=timings,
    )
    theorem_vii, _ = build_or_load_stage(
        "theorem_vii_discharge",
        lambda: proof_driver.build_golden_theorem_vii_discharge_report(
            base_K_values=BASE_K_VALUES,
            challenger_specs=CHALLENGER_SPECS,
            family=FAMILY,
            theorem_vii_certificate=theorem_vii_base,
            theorem_vi_envelope_discharge_certificate=theorem_vi,
            **live_kwargs,
        ),
        use_cache=use_cache,
        force_rebuild=force_rebuild,
        timings=timings,
    )
    theorem_viii_base, _ = build_or_load_stage(
        "theorem_viii_base",
        lambda: proof_driver.build_golden_theorem_viii_report(
            base_K_values=BASE_K_VALUES,
            family=FAMILY,
            theorem_iii_certificate=theorem_iii,
            theorem_iv_certificate=theorem_iv,
            theorem_v_certificate=theorem_v,
            threshold_identification_certificate=identification,
            theorem_vi_certificate=theorem_vi_base,
            theorem_vii_certificate=theorem_vii_base,
            theorem_i_ii_workstream_certificate=theorem_i_ii,
            **live_kwargs,
        ),
        use_cache=use_cache,
        force_rebuild=force_rebuild,
        timings=timings,
    )
    theorem_viii, _ = build_or_load_stage(
        "theorem_viii_discharge",
        lambda: proof_driver.build_golden_theorem_viii_discharge_report(
            base_K_values=BASE_K_VALUES,
            family=FAMILY,
            baseline_theorem_viii_certificate=theorem_viii_base,
            theorem_vii_exhaustion_discharge_certificate=theorem_vii,
            theorem_vi_envelope_discharge_certificate=theorem_vi,
            threshold_identification_discharge_certificate=identification_discharge,
            theorem_i_ii_workstream_certificate=theorem_i_ii,
            **live_kwargs,
        ),
        use_cache=use_cache,
        force_rebuild=force_rebuild,
        timings=timings,
    )
    live_report, _ = build_or_load_stage(
        "live_theorem_program_discharge_report_summary_cache",
        lambda: build_compact_live_theorem_program_report(
            theorem_i_ii=theorem_i_ii,
            theorem_iv=theorem_iv,
            theorem_v=theorem_v,
            identification=identification,
            theorem_vi=theorem_vi,
            theorem_vii=theorem_vii,
            theorem_viii=theorem_viii,
        ),
        use_cache=use_cache,
        force_rebuild=force_rebuild,
        timings=timings,
    )
    return live_report


def acceptance_snapshot(report: dict[str, Any]) -> dict[str, Any]:
    summary = report.get("implementation_summary", {})
    theorem_viii = (report.get("subreports") or {}).get("theorem_viii", {})
    geometry = report.get("current_reduction_geometry_summary", {})
    return {
        "overall_theorem_status": summary.get("overall_theorem_status"),
        "theorem_viii_final_status": summary.get("theorem_viii_final_status"),
        "current_reduction_geometry_available": bool(summary.get("current_reduction_geometry_available", False)),
        "current_reduction_geometry_status": summary.get("current_reduction_geometry_status"),
        "final_universal_theorem_ready_for_code_path": bool(summary.get("final_universal_theorem_ready_for_code_path", False)),
        "final_universal_theorem_ready_for_paper": bool(summary.get("final_universal_theorem_ready_for_paper", False)),
        "true_mathematical_burden_remaining": list(summary.get("true_mathematical_burden_remaining", []) or []),
        "paper_grade_burden_remaining": list(summary.get("paper_grade_burden_remaining", []) or []),
        "theorem_viii_remaining_true_mathematical_burden": list(theorem_viii.get("remaining_true_mathematical_burden", []) or []),
        "geometry_status": geometry.get("status"),
        "geometry_minimum_certified_margin": geometry.get("minimum_certified_margin"),
    }


def acceptance_checks(snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    checks = [
        ("theorem_viii final status exists", bool(snapshot.get("theorem_viii_final_status")), snapshot.get("theorem_viii_final_status")),
        ("current reduction geometry available", bool(snapshot.get("current_reduction_geometry_available")), snapshot.get("current_reduction_geometry_available")),
        ("current reduction geometry strong", snapshot.get("current_reduction_geometry_status") == "current-reduction-geometry-strong", snapshot.get("current_reduction_geometry_status")),
        ("no true mathematical burden remains", len(snapshot.get("true_mathematical_burden_remaining", [])) == 0, snapshot.get("true_mathematical_burden_remaining")),
        ("code-path final certificate ready", bool(snapshot.get("final_universal_theorem_ready_for_code_path", False)), snapshot.get("final_universal_theorem_ready_for_code_path")),
        ("paper-grade final certificate ready", bool(snapshot.get("final_universal_theorem_ready_for_paper", False)), snapshot.get("final_universal_theorem_ready_for_paper")),
        ("no paper-grade burden remains", len(snapshot.get("paper_grade_burden_remaining", [])) == 0, snapshot.get("paper_grade_burden_remaining")),
    ]
    return [{"check": name, "passed": bool(passed), "value": value} for name, passed, value in checks]


def run_command(name: str, cmd: list[str], *, logs_dir: Path, dry_run: bool = False) -> dict[str, Any]:
    logs_dir.mkdir(parents=True, exist_ok=True)
    stdout_path = logs_dir / f"{name}.stdout.log"
    stderr_path = logs_dir / f"{name}.stderr.log"
    print(f"\n[{name}] $ {' '.join(cmd)}", flush=True)
    t0 = time.time()
    if dry_run:
        stdout_path.write_text("DRY RUN: command not executed.\n" + " ".join(cmd) + "\n", encoding="utf-8")
        stderr_path.write_text("", encoding="utf-8")
        rc = 0
    else:
        env = os.environ.copy()
        env["PYTHONPATH"] = str(PROJECT_ROOT) + (os.pathsep + env.get("PYTHONPATH", "") if env.get("PYTHONPATH") else "")
        with stdout_path.open("w", encoding="utf-8") as out, stderr_path.open("w", encoding="utf-8") as err:
            rc = subprocess.call(cmd, cwd=PROJECT_ROOT, stdout=out, stderr=err, env=env)
    dt = time.time() - t0
    result = {
        "name": name,
        "cmd": cmd,
        "returncode": int(rc),
        "elapsed_seconds": dt,
        "stdout_log": relpath(stdout_path),
        "stderr_log": relpath(stderr_path),
        "passed": rc == 0,
    }
    print(f"[{name}] exit={rc} elapsed={dt:.2f}s", flush=True)
    if rc != 0:
        raise SystemExit(f"Verification command {name!r} failed with exit code {rc}. See logs in {relpath(logs_dir)}")
    return result


def write_regenerated_hashes(paths: list[Path], out_path: Path) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    for path in sorted({p for p in paths if p.exists() and p.is_file()}):
        lines.append(f"{sha256_file(path)}  {relpath(path)}\n")
    out_path.write_text("".join(lines), encoding="utf-8")
    return out_path


def collect_hash_paths() -> list[Path]:
    paths = list(STAGE_CACHE_DIR.glob("*.json"))
    paths.extend([
        PROJECT_ROOT / "artifacts/proof_audit/theorem_iii_trackb/phase4i_selected_seed/K0p9716350000_M8192_H1_SELECTED.npz",
        PROJECT_ROOT / "artifacts/proof_audit/theorem_iii_trackb/phase5d_certificate_scaffold_selected_seed/theorem_iii_trackb_phase5d_certificate_scaffold.json",
        PROJECT_ROOT / "artifacts/proof_audit/theorem_iii_trackb/phase5k_independent_replay/phase5k_formal_interval_attachment_PROMOTED.json",
        PROJECT_ROOT / "artifacts/proof_audit/theorem_iii_trackb/phase6_final_integration/theorem_iii_trackb_PHASE6_FINAL_LOWER_ANCHOR_CERTIFICATE.json",
        PROJECT_ROOT / "CERTIFIED_UNIVERSE.json",
        PROJECT_ROOT / "ARTIFACT_MANIFEST.tsv",
    ])
    return paths


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Regenerate theorem-facing artifacts and verify the proof chain from scratch.")
    p.add_argument("--workers", type=int, default=max(1, os.cpu_count() or 1), help="Worker count passed to theorem-facing generation stages.")
    p.add_argument("--force", action="store_true", help="Force rebuilding of cacheable stages.")
    p.add_argument("--from-scratch", action="store_true", help="Remove theorem-facing stage cache and Track-B outputs before rebuilding.")
    p.add_argument("--dry-run", action="store_true", help="Print/log intended commands without executing subprocess stages.")
    p.add_argument("--use-cache", action="store_true", help="Allow existing stage-cache files unless --force is also set. Default is rebuild in this from-scratch harness.")
    p.add_argument("--skip-phase5a", action="store_true", help="Skip diagnostic Theorem-III Phase 5A.")
    p.add_argument("--skip-phase5b", action="store_true", help="Skip diagnostic Theorem-III Phase 5B.")
    p.add_argument("--skip-theorem-iii", action="store_true", help="Use an existing artifacts/final_discharge/stage_cache/theorem_iii.json instead of invoking the Track-B regeneration child. Useful when resuming after a downstream verification-only failure.")
    p.add_argument("--skip-verification", action="store_true", help="Skip final replay/validation commands.")
    p.add_argument("--strict-frozen-hash-check", action="store_true", help="During full regeneration, require regenerated stage-cache artifacts to match the frozen HASHES.sha256 ledger. This is usually only appropriate for archived replay, not fresh reconstruction, because regenerated JSON bytes may legitimately differ from the frozen archive while still passing theorem-facing validation.")
    p.add_argument("--run-focused-tests", action="store_true", help="Also run focused pytest tests after replay verification.")
    p.add_argument("--fail-on-acceptance", action="store_true", help="Exit nonzero if final acceptance checks are not all satisfied.")
    p.add_argument("--stamp", default=None, help="Override output stamp for artifacts/full_regeneration/<stamp>.")
    return p


def main() -> None:
    args = build_parser().parse_args()
    stamp = args.stamp or now_stamp()
    full_root = PROJECT_ROOT / "artifacts" / "full_regeneration" / stamp
    logs_dir = full_root / "logs"
    timings: dict[str, Any] = {}
    live_kwargs: dict[str, Any] = {}
    use_cache = bool(args.use_cache)
    force_rebuild = bool(args.force or args.from_scratch)

    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    STAGE_CACHE_DIR.mkdir(parents=True, exist_ok=True)

    if args.from_scratch:
        clean_paths([
            STAGE_CACHE_DIR,
            PROJECT_ROOT / "artifacts/proof_audit/theorem_iii_trackb",
        ], dry_run=args.dry_run)
        STAGE_CACHE_DIR.mkdir(parents=True, exist_ok=True)

    if args.dry_run:
        planned = {
            "schema": "full_theorem_regeneration_dry_run_plan_v1",
            "status": "dry-run",
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "project_root": str(PROJECT_ROOT),
            "note": "Top-level dry-run does not execute theorem construction. It records the intended regeneration route. Run the Theorem III child script with --dry-run to inspect each Track-B subcommand.",
            "top_level_route": [
                "build Theorem I/II stage-cache object",
                "build Theorem IV upper/lower obstruction and tail-coherence stage-cache objects",
                "run scripts/regenerate_theorem_iii_trackb_from_scratch.py and install theorem_iii.json",
                "build Theorem V, identification, Theorem VI, Theorem VII, and Theorem VIII from regenerated stage_cache",
                "run replay_minimal.py, replay_downstream_from_cache.py (--no-hash-check unless --strict-frozen-hash-check is passed), validate_proof_payloads.py, and optional focused tests",
                "write compact live status report, FULL_REGENERATION_MANIFEST.json, and REGENERATED_HASHES.sha256",
            ],
            "canonical_command": f"{sys.executable} scripts/regenerate_all_theorems_from_scratch.py --from-scratch --force --workers {args.workers} --run-focused-tests --fail-on-acceptance",
            "theorem_iii_child_dry_run_command": f"{sys.executable} scripts/regenerate_theorem_iii_trackb_from_scratch.py --from-scratch --force --workers {args.workers} --copy-to-stage-cache --dry-run",
        }
        dump_json(full_root / "DRY_RUN_PLAN.json", planned)
        print("Dry-run plan written. No theorem construction was executed.")
        return

    print("\n=== Stage A: build Theorem I/II and Theorem IV ===", flush=True)
    build_theorem_i_ii_and_iv(live_kwargs=live_kwargs, use_cache=use_cache, force_rebuild=force_rebuild, timings=timings)

    print("\n=== Stage B: regenerate Track-B Theorem III and install it into stage_cache ===", flush=True)
    theorem_iii_stage_cache = stage_cache_path("theorem_iii")
    if args.skip_theorem_iii or (args.use_cache and theorem_iii_stage_cache.exists() and not force_rebuild):
        theorem_iii_run = {
            "skipped": True,
            "reason": "existing stage-cache theorem_iii.json reused",
            "cache_path": relpath(theorem_iii_stage_cache),
            "sha256": sha256_file(theorem_iii_stage_cache) if theorem_iii_stage_cache.exists() else None,
        }
        print(f"[cache] theorem_iii: reusing {relpath(theorem_iii_stage_cache)}", flush=True)
    else:
        theorem_iii_run = run_theorem_iii_trackb(args=args, stamp=stamp)

    print("\n=== Stage C: build Theorem V and downstream final discharge from regenerated stage_cache ===", flush=True)
    live_report = build_downstream_from_stage_cache(live_kwargs=live_kwargs, use_cache=use_cache, force_rebuild=force_rebuild, timings=timings)
    live_report_path = dump_json(full_root / "live_theorem_program_discharge_report.json", live_report)
    snapshot = acceptance_snapshot(live_report)
    checks = acceptance_checks(snapshot)
    checks_path = dump_json(full_root / "acceptance_checks.json", {"snapshot": snapshot, "checks": checks})

    verification_results: list[dict[str, Any]] = []
    if not args.skip_verification:
        print("\n=== Stage D: theorem-facing replay and validation ===", flush=True)
        verification_results.append(run_command("replay_minimal", [sys.executable, "scripts/replay_minimal.py"], logs_dir=logs_dir / "verification", dry_run=args.dry_run))
        downstream_replay_cmd = [sys.executable, "scripts/replay_downstream_from_cache.py"]
        if not args.strict_frozen_hash_check:
            downstream_replay_cmd.append("--no-hash-check")
        verification_results.append(run_command("replay_downstream_from_cache", downstream_replay_cmd, logs_dir=logs_dir / "verification", dry_run=args.dry_run))
        verification_results.append(run_command("validate_proof_payloads", [sys.executable, "scripts/validate_proof_payloads.py"], logs_dir=logs_dir / "verification", dry_run=args.dry_run))
        if args.run_focused_tests:
            verification_results.append(run_command(
                "focused_pytest",
                [
                    sys.executable, "-m", "pytest", "-q",
                    "tests/test_trackb_phase6_final_integration.py",
                    "tests/test_proof_payload_negative_controls.py",
                    "tests/test_replay_heavy_audit_protocol.py",
                    "tests/test_theorem_iv_cache_inventory.py",
                    "tests/test_upper_obstruction_audit.py",
                ],
                logs_dir=logs_dir / "verification",
                dry_run=args.dry_run,
            ))

    hash_ledger = write_regenerated_hashes(collect_hash_paths(), full_root / "REGENERATED_HASHES.sha256")
    final_manifest = {
        "schema": "full_theorem_from_scratch_regeneration_manifest_v1",
        "status": "ok",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "project_root": str(PROJECT_ROOT),
        "parameters": {
            "workers": args.workers,
            "force": args.force,
            "from_scratch": args.from_scratch,
            "use_cache": args.use_cache,
            "skip_verification": args.skip_verification,
            "run_focused_tests": args.run_focused_tests,
            "strict_frozen_hash_check": args.strict_frozen_hash_check,
            "skip_theorem_iii": args.skip_theorem_iii,
        },
        "theorem_iii_run": theorem_iii_run,
        "stage_timings": timings,
        "acceptance_snapshot": snapshot,
        "acceptance_checks": checks,
        "verification_results": verification_results,
        "live_report_path": relpath(live_report_path),
        "acceptance_checks_path": relpath(checks_path),
        "regenerated_hash_ledger": relpath(hash_ledger),
        "stage_cache_files": [relpath(p) for p in sorted(STAGE_CACHE_DIR.glob("*.json"))],
    }
    manifest_path = dump_json(full_root / "FULL_REGENERATION_MANIFEST.json", final_manifest)

    failed_checks = [c for c in checks if not c.get("passed")]
    print("\n=== Full regeneration summary ===")
    print(f"Manifest: {relpath(manifest_path)}")
    print(f"Live report: {relpath(live_report_path)}")
    print(f"Regenerated hash ledger: {relpath(hash_ledger)}")
    print(f"Acceptance checks failed: {len(failed_checks)}")
    for check in failed_checks:
        print(f"  - {check['check']}: {check['value']}")
    if args.fail_on_acceptance and failed_checks:
        raise SystemExit("Final acceptance checks did not all pass.")


if __name__ == "__main__":
    main()

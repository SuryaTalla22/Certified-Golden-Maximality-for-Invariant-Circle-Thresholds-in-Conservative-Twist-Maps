#!/usr/bin/env python3
"""Phase 2R automated collar pipeline.

This script orchestrates the now-successful lower-anchor collar workflow:

    Phase 2N single-segment solve/audit
    -> Phase 2O tail/radius pre-audit
    -> Phase 2P strict modewise tail closure
    -> Phase 2Q collar-chain assembly

It is intentionally a thin, transparent orchestration layer over the existing
scripts.  It does not replace the theorem-facing validators.  It calls them,
checks their JSON outputs, copies theorem-ready candidates to stable names, and
reruns the chain assembler after each newly closed collar segment.

Typical use from the repository root after collars 000 and 001 are already
closed:

    python scripts/audit/run_lower_anchor_phase2r_auto_collar_pipeline.py \
      --start-index 2 \
      --target-hi 0.971636

For a safer first pass:

    python scripts/audit/run_lower_anchor_phase2r_auto_collar_pipeline.py \
      --start-index 2 \
      --stop-index 2
"""


import argparse
import json
import math
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass, asdict
from decimal import Decimal, getcontext
from pathlib import Path
from typing import Iterable, Sequence

getcontext().prec = 40

ROOT = Path.cwd()

PHASE2N_DIR = Path("artifacts/proof_audit/lower_corridor/phase2n_probes")
PHASE2O_DIR = Path("artifacts/proof_audit/lower_corridor/phase2o_tail_radius")
PHASE2P_DIR = Path("artifacts/proof_audit/lower_corridor/phase2p_modewise_tail")
PHASE2Q_DIR = Path("artifacts/proof_audit/lower_corridor/phase2q_chain")
PHASE2R_DIR = Path("artifacts/proof_audit/lower_corridor/phase2r_auto")
REPLAY_DIR = Path("artifacts/proof_audit/replay")
TABLE_2O_DIR = Path("tables/proof_audit/lower_corridor/phase2o_tail_radius")
TABLE_2P_DIR = Path("tables/proof_audit/lower_corridor/phase2p_modewise_tail")
TABLE_2Q_DIR = Path("tables/proof_audit/lower_corridor/phase2q_chain")

BASE_LO = Decimal("0.9600001")
BASE_HI = Decimal("0.9605002")
STEP = Decimal("0.0005")
DEFAULT_REGIME_I_HI = Decimal("0.9600001")


@dataclass
class SegmentSpec:
    index: int
    lo: Decimal
    hi: Decimal
    mid: Decimal
    partial_final: bool = False

    @property
    def label(self) -> str:
        return f"{self.index:03d}"

    @property
    def phase2n_segment_id(self) -> str:
        return f"phase2n_collar_{self.label}"


def fmt_dec(x: Decimal) -> str:
    """Stable decimal formatting for command-line arguments."""
    s = format(x, "f")
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return s


def sigma_slug(sigma: str) -> str:
    # Match the slug convention used by the Phase 2N filenames: 0.0001 -> 0p0001.
    return str(sigma).replace(".", "p").replace("-", "m")


def parse_csv_arg(value: str) -> str:
    return ",".join(part.strip() for part in value.split(",") if part.strip())


def mkdirs() -> None:
    for p in [
        PHASE2N_DIR,
        PHASE2O_DIR,
        PHASE2P_DIR,
        PHASE2Q_DIR,
        PHASE2R_DIR,
        REPLAY_DIR,
        TABLE_2O_DIR,
        TABLE_2P_DIR,
        TABLE_2Q_DIR,
    ]:
        p.mkdir(parents=True, exist_ok=True)


def load_json(path: Path) -> dict:
    with path.open("r") as f:
        return json.load(f)


def _parse_float_set_csv(value: str) -> set[float]:
    out: set[float] = set()
    for part in str(value).split(","):
        part = part.strip()
        if not part:
            continue
        try:
            out.add(float(part))
        except Exception:
            pass
    return out


def _phase2o_candidate_source_scan(candidate: Path) -> Path | None:
    if not candidate.exists():
        return None
    try:
        data = load_json(candidate)
    except Exception:
        return None
    paths: list[str] = []
    if data.get("source_artifact"):
        paths.append(str(data["source_artifact"]))
    for seg in data.get("anchor_segments", []) or []:
        if isinstance(seg, dict) and seg.get("source_artifact"):
            paths.append(str(seg["source_artifact"]))
    for raw in paths:
        p = Path(raw)
        if not p.is_absolute() and not p.exists():
            p = candidate.parent / raw
        if p.exists():
            return p
    return None


def phase2o_has_requested_radius_coverage(candidate: Path, requested_csv: str) -> bool:
    """Return True when an existing Phase 2O candidate came from a scan broad enough for this run.

    Older Phase 2R runs used only tiny multipliers such as 1.0,1.02,1.05.
    Collar 011 showed that Phase 2P may need to combine a much larger
    theorem-eligible radius row with the modewise tail response.  Therefore a
    resumed run must refresh stale Phase 2O candidates whose source scan did
    not include the requested radius multipliers.
    """
    requested = _parse_float_set_csv(requested_csv)
    if not requested:
        return True
    scan = _phase2o_candidate_source_scan(candidate)
    if scan is None:
        return False
    try:
        data = load_json(scan)
    except Exception:
        return False
    present: set[float] = set()
    cfg = data.get("config") if isinstance(data.get("config"), dict) else {}
    for x in cfg.get("radius_multipliers", []) or []:
        try:
            present.add(float(x))
        except Exception:
            pass
    for row in data.get("rows", []) or []:
        if isinstance(row, dict) and row.get("radius_multiplier") is not None:
            try:
                present.add(float(row["radius_multiplier"]))
            except Exception:
                pass
    # Tolerate tiny string/float conversion differences.
    for req in requested:
        if not any(abs(req - have) <= 1e-14 * max(1.0, abs(req)) for have in present):
            return False
    return True


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        json.dump(data, f, indent=2, sort_keys=True)
        f.write("\n")


def stream_command(cmd: Sequence[str], log_path: Path, *, dry_run: bool = False) -> int:
    """Run a command, streaming output to terminal and log file."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    printable = " ".join(cmd)
    header = f"\n$ {printable}\n"
    print(header, flush=True)
    with log_path.open("a") as log:
        log.write(header)
        log.flush()
        if dry_run:
            log.write("[dry-run] command not executed\n")
            print("[dry-run] command not executed", flush=True)
            return 0
        proc = subprocess.Popen(
            list(cmd),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        assert proc.stdout is not None
        for line in proc.stdout:
            print(line, end="", flush=True)
            log.write(line)
            log.flush()
        return proc.wait()


def run_checked(cmd: Sequence[str], log_path: Path, *, dry_run: bool = False) -> None:
    rc = stream_command(cmd, log_path, dry_run=dry_run)
    if rc != 0:
        raise RuntimeError(f"command failed with return code {rc}: {' '.join(cmd)}")


def segment_for_index(index: int, target_hi: Decimal | None = None) -> SegmentSpec:
    lo = BASE_LO + STEP * Decimal(index)
    hi_nominal = BASE_HI + STEP * Decimal(index)
    hi = hi_nominal
    partial = False
    if target_hi is not None and hi_nominal > target_hi:
        hi = target_hi
        partial = True
    mid = (lo + hi) / Decimal(2)
    if hi <= lo:
        raise ValueError(f"segment {index} has non-positive width: lo={lo}, hi={hi}")
    return SegmentSpec(index=index, lo=lo, hi=hi, mid=mid, partial_final=partial)


def stop_index_for_target(target_hi: Decimal) -> int:
    """Smallest index whose nominal hi reaches target_hi."""
    if target_hi <= BASE_HI:
        return 0
    raw = (target_hi - BASE_HI) / STEP
    return int(math.ceil(float(raw)))


def phase2n_summary_path(spec: SegmentSpec) -> Path:
    return PHASE2N_DIR / f"{spec.phase2n_segment_id}_phase2n_batch_summary.json"


def phase2n_single_path(spec: SegmentSpec, N: str, oversample: str, sigma_cap: str) -> Path:
    return PHASE2N_DIR / f"{spec.phase2n_segment_id}_N{N}_os{oversample}_sg{sigma_slug(sigma_cap)}.json"


def phase2o_candidate_path(spec: SegmentSpec) -> Path:
    return PHASE2O_DIR / f"phase2o_collar_{spec.label}_tail_radius_candidate.json"


def phase2p_candidate_path(spec: SegmentSpec) -> Path:
    return PHASE2P_DIR / f"phase2p_collar_{spec.label}_modewise_tail_candidate.json"


def phase2p_ready_path(index: int) -> Path:
    return PHASE2P_DIR / f"phase2p_collar_{index:03d}_THEOREM_READY_candidate.json"


def known_ready_path(index: int) -> Path | None:
    candidates = []
    if index == 0:
        candidates.extend([
            PHASE2P_DIR / "phase2p_collar_000_FULL_THEOREM_READY_candidate.json",
            PHASE2P_DIR / "phase2p_collar_000_THEOREM_READY_candidate.json",
        ])
    candidates.append(phase2p_ready_path(index))
    candidates.extend(sorted(PHASE2P_DIR.glob(f"phase2p_collar_{index:03d}*THEOREM_READY*candidate.json")))
    for p in candidates:
        if p.exists():
            return p
    return None


def is_theorem_ready_candidate(path: Path) -> tuple[bool, dict]:
    if not path.exists():
        return False, {}
    data = load_json(path)
    ok = (
        data.get("theorem_facing") is True
        and data.get("promotion_allowed") is True
        and not data.get("failure_fields")
    )
    row = data.get("selected_phase2p_row") or {}
    if row:
        ok = ok and row.get("theorem_ready") is True and not row.get("failure_reasons")
    return bool(ok), data


def find_seed_for_index(index: int, N: str, oversample: str, sigma_cap: str) -> Path | None:
    if index <= 0:
        return None
    prev = index - 1
    spec = segment_for_index(prev)
    direct = phase2n_single_path(spec, N, oversample, sigma_cap)
    if direct.exists():
        return direct
    # Existing collar 000 may have been generated with the full_os16 name.
    patterns = [
        f"phase2n_collar_{prev:03d}*N{N}_os{oversample}_sg{sigma_slug(sigma_cap)}.json",
        f"phase2n_collar_{prev:03d}*N{N}_os{oversample}*.json",
    ]
    for pat in patterns:
        hits = [p for p in sorted(PHASE2N_DIR.glob(pat)) if "summary" not in p.name and "candidate" not in p.name]
        if hits:
            return hits[-1]
    return None


def collect_ready_candidates_through(max_index: int, *, allow_placeholders: bool = False) -> list[Path]:
    """Collect theorem-ready candidate paths through max_index.

    In normal execution every path must exist and pass promotion checks.  In
    dry-run mode, later collars may not exist yet, so allow_placeholders=True
    returns the canonical future theorem-ready path for missing collars.  This
    keeps dry-run useful without pretending any theorem artifact exists.
    """
    paths: list[Path] = []
    missing: list[int] = []
    for i in range(0, max_index + 1):
        p = known_ready_path(i)
        if p is None:
            if allow_placeholders:
                p = phase2p_ready_path(i)
                paths.append(p)
            else:
                missing.append(i)
        else:
            paths.append(p)
    if missing:
        raise FileNotFoundError(f"missing theorem-ready candidates for collars: {missing}")
    return paths


def should_pass_final_anchor(expected_end: Decimal, final_anchor_hi: str | None, tolerance: str) -> bool:
    """Return True only when the assembled chain is intended to reach the final anchor.

    Phase 2Q treats --final-anchor-hi as a theorem obligation.  Passing it to
    an intermediate chain is therefore incorrect: the chain should close as an
    intermediate collar audit, while final_anchor_hi should be reserved for the
    final partial chain whose expected end reaches the requested final anchor.
    """
    if not final_anchor_hi:
        return False
    anchor = Decimal(str(final_anchor_hi))
    tol = Decimal(str(tolerance))
    return expected_end + tol >= anchor


def run_phase2n(spec: SegmentSpec, args: argparse.Namespace, *, dry_run: bool) -> Path:
    summary = phase2n_summary_path(spec)
    if summary.exists() and args.resume and not args.force:
        print(f"[resume] Phase 2N summary exists for collar {spec.label}: {summary}")
        return summary

    cmd = [
        sys.executable,
        "scripts/audit/run_lower_anchor_phase2n_batch.py",
        "--segment-id", spec.phase2n_segment_id,
        "--K-lo", fmt_dec(spec.lo),
        "--K-hi", fmt_dec(spec.hi),
        "--K-mid", fmt_dec(spec.mid),
        "--N-values", args.N_values,
        "--oversample-factors", args.oversample_factors,
        "--sigma-caps", args.sigma_caps,
        "--timeout-seconds", str(args.timeout_seconds),
        "--skip-existing",
    ]
    # Seed only when using a single N/oversample/sigma setting.  This matches the current proof workflow.
    N0 = args.N_values.split(",")[0].strip()
    os0 = args.oversample_factors.split(",")[0].strip()
    sg0 = args.sigma_caps.split(",")[0].strip()
    seed = find_seed_for_index(spec.index, N0, os0, sg0)
    if seed is not None:
        cmd.extend(["--seed-json", str(seed)])
        print(f"[seed] collar {spec.label} uses seed: {seed}")
    elif spec.index > 0:
        print(f"[warning] no seed found for collar {spec.label}; Phase 2N will run unseeded")

    log = REPLAY_DIR / f"phase2r_collar_{spec.label}_phase2n.log"
    run_checked(cmd, log, dry_run=dry_run)
    return summary


def run_phase2o(spec: SegmentSpec, args: argparse.Namespace, *, dry_run: bool) -> Path:
    out = PHASE2O_DIR / f"phase2o_collar_{spec.label}_tail_radius_scan.json"
    csv = TABLE_2O_DIR / f"phase2o_collar_{spec.label}_tail_radius_scan.csv"
    cand = phase2o_candidate_path(spec)
    if cand.exists() and args.resume and not args.force:
        if phase2o_has_requested_radius_coverage(cand, args.phase2o_radius_multipliers):
            print(f"[resume] Phase 2O candidate exists for collar {spec.label}: {cand}")
            return cand
        print(
            f"[refresh] Phase 2O candidate for collar {spec.label} is stale for requested "
            f"radius multipliers ({args.phase2o_radius_multipliers}); regenerating: {cand}"
        )
    cmd = [
        sys.executable,
        "scripts/audit/run_lower_anchor_phase2o_radius_tail_scan.py",
        "--input", str(phase2n_summary_path(spec)),
        "--out", str(out),
        "--csv", str(csv),
        "--candidate-out", str(cand),
        "--radius-multipliers", args.phase2o_radius_multipliers,
        "--sigma-values", args.phase2o_sigma_values,
        "--tail-band-fractions", args.phase2o_tail_band_fractions,
        "--tail-safety-factors", args.phase2o_tail_safety_factors,
    ]
    log = REPLAY_DIR / f"phase2r_collar_{spec.label}_phase2o.log"
    run_checked(cmd, log, dry_run=dry_run)
    return cand


def run_phase2p(spec: SegmentSpec, args: argparse.Namespace, *, dry_run: bool) -> Path:
    out = PHASE2P_DIR / f"phase2p_collar_{spec.label}_modewise_tail_scan.json"
    csv = TABLE_2P_DIR / f"phase2p_collar_{spec.label}_modewise_tail_scan.csv"
    cand = phase2p_candidate_path(spec)
    if cand.exists() and args.resume and not args.force:
        ok, _ = is_theorem_ready_candidate(cand)
        if ok:
            print(f"[resume] Phase 2P candidate already theorem-ready for collar {spec.label}: {cand}")
            return cand
    cmd = [
        sys.executable,
        "scripts/audit/run_lower_anchor_phase2p_modewise_tail_scan.py",
        "--input", str(phase2o_candidate_path(spec)),
        "--out", str(out),
        "--csv", str(csv),
        "--candidate-out", str(cand),
        "--sigma-values", args.phase2p_sigma_values,
        "--tail-cutoffs", args.phase2p_tail_cutoffs,
        "--oversample-factors", args.phase2p_oversample_factors,
    ]
    log = REPLAY_DIR / f"phase2r_collar_{spec.label}_phase2p.log"
    run_checked(cmd, log, dry_run=dry_run)
    return cand


def promote_ready_candidate(spec: SegmentSpec, candidate: Path, *, dry_run: bool = False) -> Path:
    dest = phase2p_ready_path(spec.index)
    if dry_run:
        print(f"[dry-run] would validate theorem readiness and copy {candidate} -> {dest}")
        return dest

    ok, data = is_theorem_ready_candidate(candidate)
    if not ok:
        brief = {
            "theorem_facing": data.get("theorem_facing"),
            "promotion_allowed": data.get("promotion_allowed"),
            "closure_level": data.get("closure_level"),
            "failure_fields": data.get("failure_fields"),
            "selected_phase2p_row": {
                k: (data.get("selected_phase2p_row") or {}).get(k)
                for k in ["theorem_ready", "radii_margin", "tail_T", "allowable_tail_max", "failure_reasons"]
            },
        }
        raise RuntimeError(f"Phase 2P candidate for collar {spec.label} is not theorem-ready: {json.dumps(brief, indent=2)}")
    shutil.copyfile(candidate, dest)
    print(f"[promote] collar {spec.label}: {dest}")
    return dest


def run_phase2q(max_index: int, expected_end: Decimal, args: argparse.Namespace, *, dry_run: bool) -> Path:
    candidates = collect_ready_candidates_through(max_index, allow_placeholders=dry_run)
    out = PHASE2Q_DIR / f"phase2q_collar_000_{max_index:03d}_chain_audit.json"
    csv = TABLE_2Q_DIR / f"phase2q_collar_000_{max_index:03d}_chain_segments.csv"
    cand = PHASE2Q_DIR / f"phase2q_collar_000_{max_index:03d}_chain_candidate.json"
    cmd = [
        sys.executable,
        "scripts/audit/run_lower_anchor_phase2q_chain_assembler.py",
    ]
    for p in candidates:
        cmd.extend(["--candidate", str(p)])
    cmd.extend([
        "--expected-start", fmt_dec(BASE_LO),
        "--expected-end", fmt_dec(expected_end),
        "--expected-regime-i-hi", str(args.expected_regime_i_hi),
        "--overlap-tolerance", str(args.overlap_tolerance),
        "--out", str(out),
        "--csv", str(csv),
        "--candidate-out", str(cand),
    ])
    pass_final_anchor = should_pass_final_anchor(expected_end, args.final_anchor_hi, args.overlap_tolerance)
    if args.final_anchor_hi and not pass_final_anchor:
        print(
            f"[phase2q] intermediate chain ends at {fmt_dec(expected_end)}; "
            f"not passing --final-anchor-hi {args.final_anchor_hi} until the final chain."
        )
    if pass_final_anchor:
        cmd.extend(["--final-anchor-hi", str(args.final_anchor_hi)])
    log = REPLAY_DIR / f"phase2r_collar_000_{max_index:03d}_phase2q.log"
    run_checked(cmd, log, dry_run=dry_run)

    if not dry_run:
        data = load_json(cand)
        if not (data.get("theorem_facing") and data.get("promotion_allowed") and not data.get("failure_fields")):
            raise RuntimeError(f"Phase 2Q chain did not close through collar {max_index:03d}: {json.dumps(data, indent=2)[:2000]}")
    return cand


def inspect_existing_chain(args: argparse.Namespace) -> int:
    found = []
    for p in sorted(PHASE2P_DIR.glob("phase2p_collar_*THEOREM_READY_candidate.json")):
        found.append(str(p))
    if (PHASE2P_DIR / "phase2p_collar_000_FULL_THEOREM_READY_candidate.json").exists():
        found.append(str(PHASE2P_DIR / "phase2p_collar_000_FULL_THEOREM_READY_candidate.json"))
    unique_found = sorted(set(found))
    print(json.dumps({"ready_candidate_count": len(unique_found), "ready_candidates": unique_found}, indent=2))
    return 0


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Automate Phase 2N -> 2O -> 2P -> 2Q collar propagation.")
    p.add_argument("--start-index", type=int, default=2, help="First collar index to generate. Use 2 after collars 000 and 001 are closed.")
    p.add_argument("--stop-index", type=int, default=None, help="Last collar index to generate, inclusive. If omitted, derived from --target-hi.")
    p.add_argument("--target-hi", type=str, default=None, help="Final K upper anchor. If set, stop-index is derived and final segment may be partial.")
    p.add_argument("--final-anchor-hi", type=str, default=None, help="Pass-through final anchor target to Phase 2Q, e.g. 0.971636.")
    p.add_argument("--expected-regime-i-hi", type=str, default=str(DEFAULT_REGIME_I_HI))
    p.add_argument("--overlap-tolerance", type=str, default="1e-10")

    p.add_argument("--N-values", default="1024")
    p.add_argument("--oversample-factors", default="16")
    p.add_argument("--sigma-caps", default="0.0001")
    p.add_argument("--timeout-seconds", type=float, default=1200.0)

    p.add_argument(
        "--phase2o-radius-multipliers",
        default="1.0,1.02,1.05,1.25,1.5,1.75,2.0,2.25,2.5,2.75,3.0,3.5,4.0,5.0,6.0",
        help=(
            "Radius multipliers for Phase 2O.  The default is intentionally broad "
            "because Phase 2P now scans all theorem-eligible Phase 2O rows and may "
            "need larger radius rows even when Phase 2O's scalar-tail score prefers x1."
        ),
    )
    p.add_argument("--phase2o-sigma-values", default="0.0001,0.00001,0.000005,0.0000025,0.000001")
    p.add_argument("--phase2o-tail-band-fractions", default="0.5,0.65,0.75,0.85")
    p.add_argument("--phase2o-tail-safety-factors", default="2,4,8,16")

    p.add_argument("--phase2p-sigma-values", default="0.0001,0.000075,0.00005,0.000025,0.00001,0.000005,0.0000025,0.000001")
    p.add_argument("--phase2p-tail-cutoffs", default="1024,2048,4096,8192,16384")
    p.add_argument("--phase2p-oversample-factors", default="16")

    p.add_argument("--summary-out", default=str(PHASE2R_DIR / "phase2r_auto_run_summary.json"))
    p.add_argument("--resume", action=argparse.BooleanOptionalAction, default=True, help="Reuse existing summaries/candidates when possible.")
    p.add_argument("--force", action="store_true", help="Rerun phases even when outputs exist.")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--assemble-only", action="store_true", help="Do not run 2N/2O/2P; only run 2Q through --stop-index.")
    p.add_argument("--no-assemble-after-each", action="store_true", help="Only assemble once after the final requested collar.")
    p.add_argument("--inspect-existing", action="store_true", help="Print discovered theorem-ready candidates and exit.")
    return p


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    args.N_values = parse_csv_arg(args.N_values)
    args.oversample_factors = parse_csv_arg(args.oversample_factors)
    args.sigma_caps = parse_csv_arg(args.sigma_caps)
    args.phase2o_radius_multipliers = parse_csv_arg(args.phase2o_radius_multipliers)
    args.phase2o_sigma_values = parse_csv_arg(args.phase2o_sigma_values)
    args.phase2o_tail_band_fractions = parse_csv_arg(args.phase2o_tail_band_fractions)
    args.phase2o_tail_safety_factors = parse_csv_arg(args.phase2o_tail_safety_factors)
    args.phase2p_sigma_values = parse_csv_arg(args.phase2p_sigma_values)
    args.phase2p_tail_cutoffs = parse_csv_arg(args.phase2p_tail_cutoffs)
    args.phase2p_oversample_factors = parse_csv_arg(args.phase2p_oversample_factors)

    mkdirs()
    if args.inspect_existing:
        return inspect_existing_chain(args)

    target_hi = Decimal(args.target_hi) if args.target_hi else None
    if args.stop_index is None:
        if target_hi is None:
            raise SystemExit("Either --stop-index or --target-hi is required.")
        stop_index = stop_index_for_target(target_hi)
    else:
        stop_index = args.stop_index

    if stop_index < args.start_index and not args.assemble_only:
        raise SystemExit(f"stop-index {stop_index} is before start-index {args.start_index}")

    run_summary: dict = {
        "status": "phase2r-started",
        "start_index": args.start_index,
        "stop_index": stop_index,
        "target_hi": args.target_hi,
        "final_anchor_hi": args.final_anchor_hi,
        "segments": [],
        "chain_candidates": [],
    }
    write_json(Path(args.summary_out), run_summary)

    try:
        if args.assemble_only:
            end_spec = segment_for_index(stop_index, target_hi)
            chain = run_phase2q(stop_index, end_spec.hi, args, dry_run=args.dry_run)
            run_summary["chain_candidates"].append(str(chain))
        else:
            for idx in range(args.start_index, stop_index + 1):
                spec = segment_for_index(idx, target_hi)
                print("\n" + "=" * 80)
                print(f"COLLAR {spec.label}: [{fmt_dec(spec.lo)}, {fmt_dec(spec.hi)}], mid={fmt_dec(spec.mid)}, partial={spec.partial_final}")
                print("=" * 80)

                existing = known_ready_path(idx)
                if existing is not None and args.resume and not args.force:
                    ok, _ = is_theorem_ready_candidate(existing)
                    if ok:
                        print(f"[resume] collar {spec.label} already theorem-ready: {existing}")
                        promoted = existing
                    else:
                        raise RuntimeError(f"existing ready-named candidate is not theorem-ready: {existing}")
                else:
                    phase2n = run_phase2n(spec, args, dry_run=args.dry_run)
                    phase2o = run_phase2o(spec, args, dry_run=args.dry_run)
                    phase2p = run_phase2p(spec, args, dry_run=args.dry_run)
                    promoted = promote_ready_candidate(spec, phase2p, dry_run=args.dry_run)

                seg_record = {
                    "index": idx,
                    "label": spec.label,
                    "K_lo": fmt_dec(spec.lo),
                    "K_hi": fmt_dec(spec.hi),
                    "partial_final": spec.partial_final,
                    "ready_candidate": str(promoted),
                }
                run_summary["segments"].append(seg_record)
                write_json(Path(args.summary_out), run_summary)

                if not args.no_assemble_after_each:
                    chain = run_phase2q(idx, spec.hi, args, dry_run=args.dry_run)
                    run_summary["chain_candidates"].append(str(chain))
                    write_json(Path(args.summary_out), run_summary)

            if args.no_assemble_after_each:
                final_spec = segment_for_index(stop_index, target_hi)
                chain = run_phase2q(stop_index, final_spec.hi, args, dry_run=args.dry_run)
                run_summary["chain_candidates"].append(str(chain))

        run_summary["status"] = "phase2r-complete"
        write_json(Path(args.summary_out), run_summary)
        print("\nPhase 2R complete.")
        print(json.dumps(run_summary, indent=2))
        return 0
    except Exception as exc:
        run_summary["status"] = "phase2r-failed"
        run_summary["error"] = str(exc)
        write_json(Path(args.summary_out), run_summary)
        print("\nPhase 2R failed:", exc, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

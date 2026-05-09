#!/bin/bash
set -euo pipefail

python - <<'PY'
import json
import subprocess
import sys
from pathlib import Path

repo = Path(".").resolve()
atlas_path = repo / "artifacts/proof_audit/lower_corridor/lower_anchor_phase2j_failure_atlas.json"
out_dir = repo / "artifacts/proof_audit/lower_corridor/phase2j_rescue"
table_dir = repo / "tables/proof_audit/lower_corridor/phase2j_rescue"
log_dir = repo / "artifacts/proof_audit/lower_corridor/phase2l_logs"

out_dir.mkdir(parents=True, exist_ok=True)
table_dir.mkdir(parents=True, exist_ok=True)
log_dir.mkdir(parents=True, exist_ok=True)

atlas = json.loads(atlas_path.read_text())
failed_rows = atlas.get("failed_rows", [])

def encode_sigma(x):
    return str(x).replace(".", "p").replace("-", "m")

def candidate_ready(path):
    if not path.exists():
        return False
    try:
        data = json.loads(path.read_text())
    except Exception:
        return False
    for row in data.get("anchor_segments", []):
        if row.get("theorem_ready") or row.get("certified"):
            return True
    return False

jobs = []

for row in failed_rows:
    parent = row["segment_id"]
    K_lo = float(row["K_lo"])
    K_hi = float(row["K_hi"])
    profile = row.get("profile", {})
    split_count = int(profile.get("split_count", 1))
    overlap = float(profile.get("overlap", 1e-7))

    n_values = profile.get("n_values", [256, 384, 512])
    oversamples = profile.get("oversample_factors", [16])
    sigmas = profile.get("sigma_caps", [0.005])
    max_wall = float(profile.get("max_wall_seconds", 2400.0))

    width = (K_hi - K_lo) / split_count

    for i in range(split_count):
        sub_lo = K_lo + i * width
        sub_hi = K_lo + (i + 1) * width

        # Add small overlap except at global endpoints.
        if i > 0:
            sub_lo -= overlap
        if i < split_count - 1:
            sub_hi += overlap

        sub_mid = 0.5 * (sub_lo + sub_hi)
        sub_id = f"{parent}_phase2j_sub{i:02d}"

        # Use all listed sigma caps with the largest oversample first for robustness.
        # If this is too many, interrupt and narrow later.
        for osamp in oversamples:
            for sigma in sigmas:
                cand_name = f"{sub_id}_os{osamp}_sg{encode_sigma(sigma)}_candidate.json"
                cand_path = out_dir / cand_name
                if candidate_ready(cand_path):
                    continue

                cmd = [
                    sys.executable,
                    "scripts/audit/run_lower_anchor_phase2g_segment.py",
                    "--segment-id", sub_id,
                    "--K-lo", repr(sub_lo),
                    "--K-hi", repr(sub_hi),
                    "--K-mid", repr(sub_mid),
                    "--N-values", ",".join(str(n) for n in n_values),
                    "--oversample-factor", str(osamp),
                    "--sigma-cap", str(sigma),
                    "--max-wall-seconds", str(max_wall),
                    "--out-dir", str(out_dir.relative_to(repo)),
                    "--table-dir", str(table_dir.relative_to(repo)),
                    "--candidate-name", cand_name,
                ]
                jobs.append((sub_id, cand_name, cmd))

print(f"Planned missing-subsegment jobs: {len(jobs)}")

for idx, (sub_id, cand_name, cmd) in enumerate(jobs, 1):
    print(f"\n[{idx}/{len(jobs)}] running {cand_name}", flush=True)
    stdout_path = log_dir / f"{cand_name}.stdout.log"
    stderr_path = log_dir / f"{cand_name}.stderr.log"

    with stdout_path.open("w") as out, stderr_path.open("w") as err:
        rc = subprocess.call(cmd, stdout=out, stderr=err)

    print(f"return code: {rc}", flush=True)
    if rc != 0:
        print(f"  stderr: {stderr_path}", flush=True)

print("\nDone running missing subsegments.")
PY

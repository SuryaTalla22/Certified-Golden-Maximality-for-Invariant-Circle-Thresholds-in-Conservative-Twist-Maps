# Referee audit protocol

This protocol is the recommended path for a referee or artifact evaluator who
wants to check the paper-facing proof package without rerunning the heavy
Theorem-IV construction.

## 1. Inspect theorem scope

Open `CERTIFIED_UNIVERSE.json` and confirm that the manuscript theorem uses the
same:

- map family and forcing label;
- arithmetic domain and partition grammar;
- threshold functional;
- golden representative;
- `GL(2,Z)` normalization convention;
- replay levels.

## 2. Inspect artifact manifest and hashes

Open:

```text
ARTIFACT_MANIFEST.tsv
HASHES.sha256
```

The manifest should list every JSON artifact in
`artifacts/final_discharge/stage_cache/`.  The hash ledger should include those
artifacts plus the core paper-facing audit files.

Verify hashes:

```bash
sha256sum -c HASHES.sha256
```

## 3. Run minimal replay

```bash
python scripts/replay_minimal.py --out artifacts/paper_replay/minimal
```

Confirm that the generated replay reports:

```text
theorem_status = golden-universal-theorem-final-strong
final_discharge_verified = true
active_assumptions = []
open_hypotheses = []
remaining_true_mathematical_burden = []
```

## 4. Run downstream replay from cached heavy upstream artifacts

```bash
python scripts/replay_downstream_from_cache.py \
  --out artifacts/paper_replay/downstream_from_cache
```

This command should report:

```text
replay_mode = downstream-from-verified-cache
```

If the cache is missing or hashes do not match, the script should fail closed.
Synthetic fallback is available only with:

```bash
python scripts/replay_downstream_from_cache.py --allow-synthetic-upstream
```

and should not be used as publication evidence.

## 5. Run publication-facing tests and negative controls

```bash
pytest -q tests/test_paper_replay_scripts.py tests/test_negative_final_replay_controls.py
```

The negative controls should verify that raw transport shells, nonfinal global
exhaustion, branch/chart mismatch, margin erosion, omitted-label failures, cache
absence, and hash mismatch are rejected.

## 6. Treat full Theorem-IV regeneration as a deep archival audit

`replay_full.py` is intentionally fail-closed in this snapshot.  Full
Theorem-IV regeneration is computationally intensive and must be wired to the
archival heavy-regeneration command before it is treated as a one-command full
replay.  The release metadata should record the hardware and runtime for that
path.

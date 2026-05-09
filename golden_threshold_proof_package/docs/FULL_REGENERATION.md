# Regenerating the theorem-facing proof artifacts

This document describes the full-regeneration path added by the overlay.

The repository already contains cached theorem-facing artifacts and lightweight replay scripts.  Those are the right tools for ordinary verification of the archived bundle.  The full-regeneration scripts in this overlay are for the stronger audit question: can the theorem-facing artifacts be rebuilt from construction scripts and then replayed?

## Added scripts

### `scripts/regenerate_all_theorems_from_scratch.py`

Reviewer-facing top-level command.  It runs the full dependency chain:

1. Build the Theorem I/II workstream certificate.
2. Build the Theorem IV upper/lower obstruction stack, including adaptive incompatibility, tail transport, tail coherence, bridge promotion, support-core, tail-aware, tail-stability, and bridge-profile objects.
3. Run Track-B Theorem III regeneration and install the Phase-6 final lower-anchor certificate into `artifacts/final_discharge/stage_cache/theorem_iii.json`.
4. Build Theorem V, the identification objects, Theorem VI, Theorem VII, and Theorem VIII from the regenerated stage-cache objects.
5. Run theorem-facing replay/validation commands.
6. Write a fresh manifest and regenerated hash ledger under `artifacts/full_regeneration/<stamp>/`.

### `scripts/regenerate_theorem_iii_trackb_from_scratch.py`

Explicit Track-B Theorem III construction harness.  It runs the theorem-facing Track-B phases:

1. Phase 1 seed construction.
2. Phase 4F oversampled least-squares polish.
3. Phase 4I H1 polish and canonical seed selection.
4. Phase 5C interval backend, plus optional Phase 5A/5B diagnostics.
5. Phase 5D certificate scaffold.
6. Phase 5F/5FB/5GB/5H/5I/5J/5K formal attachment and promotion chain.
7. Phase 5E final promotion gate.
8. Phase 6 final integration and replay.
9. Optional installation of the Phase-6 final artifact as `artifacts/final_discharge/stage_cache/theorem_iii.json`.

The Theorem III harness deliberately bypasses the older `proof_driver.build_golden_theorem_iii_report()` path.  The theorem-facing lower-anchor object is the Track-B Phase-6 artifact, not the historical a posteriori prototype object.

## Installing the overlay

From outside the repository, unpack the overlay and copy it into the repository root:

```bash
unzip kam_full_regeneration_overlay.zip -d /tmp/kam_full_regeneration_overlay
rsync -av /tmp/kam_full_regeneration_overlay/ /path/to/code_repository/
cd /path/to/code_repository
```

Create or activate an environment with the repository dependencies.  For a fresh environment:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -e ".[dev]"
```

If the project already has a working environment, activate it instead.  The regeneration scripts also prepend the repository root to `PYTHONPATH` for child processes, but the numerical dependencies still need to be installed.

## Inspecting the plan without running heavy stages

Top-level dry run:

```bash
python scripts/regenerate_all_theorems_from_scratch.py --dry-run --workers 64
```

Track-B Theorem III subcommand dry run:

```bash
python scripts/regenerate_theorem_iii_trackb_from_scratch.py \
  --from-scratch \
  --force \
  --workers 64 \
  --copy-to-stage-cache \
  --dry-run
```

The top-level dry run writes a plan to `artifacts/full_regeneration/<stamp>/DRY_RUN_PLAN.json`.  The Track-B dry run writes logs and a command manifest without requiring the heavy numerical outputs to exist.

## Full independent regeneration

Run the theorem-facing full-regeneration command from the repository root:

```bash
python scripts/regenerate_all_theorems_from_scratch.py \
  --from-scratch \
  --force \
  --workers 64 \
  --run-focused-tests \
  --fail-on-acceptance
```

Adjust `--workers` to match the available hardware.  The command is expected to take substantially longer than the lightweight replay scripts because Theorem III and Theorem IV are regenerated rather than read from cache.

## Resuming after an interrupted run

If a run stops after producing useful intermediate outputs, resume with cache reuse:

```bash
python scripts/regenerate_all_theorems_from_scratch.py \
  --use-cache \
  --workers 64 \
  --run-focused-tests \
  --fail-on-acceptance
```

Use `--force` together with `--use-cache` only when you intentionally want cacheable stages rebuilt.

## Theorem III only

To regenerate only the Track-B Theorem III lower-anchor object and install it into the final-discharge stage cache:

```bash
python scripts/regenerate_theorem_iii_trackb_from_scratch.py \
  --from-scratch \
  --force \
  --workers 64 \
  --copy-to-stage-cache
```

The installed output is:

```text
artifacts/final_discharge/stage_cache/theorem_iii.json
```

The source Phase-6 artifact is:

```text
artifacts/proof_audit/theorem_iii_trackb/phase6_final_integration/theorem_iii_trackb_PHASE6_FINAL_LOWER_ANCHOR_CERTIFICATE.json
```

## Outputs of a full run

A successful full run writes:

```text
artifacts/full_regeneration/<stamp>/FULL_REGENERATION_MANIFEST.json
artifacts/full_regeneration/<stamp>/live_theorem_program_discharge_report.json
artifacts/full_regeneration/<stamp>/acceptance_checks.json
artifacts/full_regeneration/<stamp>/REGENERATED_HASHES.sha256
artifacts/full_regeneration/<stamp>/logs/
```

The `FULL_REGENERATION_MANIFEST.json` is the main audit object.  It records the run parameters, the Track-B Theorem III regeneration manifest, stage timings, acceptance checks, replay/validation results, regenerated hash ledger path, and final stage-cache files.

## Hash ledgers

The repository's frozen `HASHES.sha256` verifies the archived bundle.  A full independent regeneration may produce different bytes because manifests, timestamps, command logs, and ordering can change.  For regenerated outputs, use the run-specific ledger:

```bash
sha256sum -c artifacts/full_regeneration/<stamp>/REGENERATED_HASHES.sha256
```

Do not interpret a mismatch against the frozen `HASHES.sha256` as a theorem failure after a fresh regeneration.  The theorem-facing checks are the replay/validation commands and the regenerated run manifest.

## Replay commands run by the top-level script

Unless `--skip-verification` is passed, the top-level script runs:

```bash
python scripts/replay_minimal.py
python scripts/replay_downstream_from_cache.py
python scripts/validate_proof_payloads.py
```

With `--run-focused-tests`, it also runs focused theorem/audit tests covering Track-B Phase 6, proof-payload negative controls, heavy-audit replay protocol, Theorem-IV cache inventory, and upper-obstruction audit behavior.

## Relationship to `scripts/replay_full.py`

`scripts/replay_full.py` is intentionally fail-closed in the current repository.  The full-regeneration entry point added by this overlay is `scripts/regenerate_all_theorems_from_scratch.py`.  Reviewers should use the regeneration script for live construction and the lightweight replay scripts for ordinary archived-artifact verification.

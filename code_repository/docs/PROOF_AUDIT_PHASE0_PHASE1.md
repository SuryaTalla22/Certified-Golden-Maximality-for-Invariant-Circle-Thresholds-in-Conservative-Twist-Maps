# Phase 0/1 Proof-Audit Upgrade

This repository snapshot adds a fail-closed proof-audit namespace for the first
step of the 95+ manuscript implementation plan.

## What was added

- `kam_theorem_suite/audit/proof_payload.py`: JSON-serialisable dataclasses for
  raw intervals, derived inequalities, derived Booleans, and audit bundles.
- `kam_theorem_suite/audit/proof_bundle_validator.py`: fail-closed validation of
  theorem-facing audit bundles. Empty bundles, trusted Booleans, diagnostic-only
  theorem fields, nonpositive margins, unknown dependencies, and mismatched
  stored/recomputed margins are rejected.
- `kam_theorem_suite/audit/stage_cache_extractors.py`: lightweight extractors for
  cached stage artifacts.
- `kam_theorem_suite/audit/current_state_red_team.py`: current-state audit that
  checks whether the cached Theorem-III lower artifact supports the compact
  near-critical lower anchor used by the paper replay.
- `kam_theorem_suite/audit/artifact_shell_builder.py`: Phase-1 replay-shell
  builders that refuse to construct theorem-facing shells unless the relevant
  proof-audit bundle is valid.
- `kam_theorem_suite/paper_replay_inputs.py`: new
  `build_shells_from_proof_audit(...)` entry point.
- `scripts/audit/`: layout bootstrap, current-state red-team audit, and
  proof-audit replay helper scripts.
- `tests/test_phase0_phase1_proof_audit.py`: Phase-0/1 regression and negative
  controls.

## Important current-state result

The generated artifact
`artifacts/proof_audit/current_state_red_team_audit.json` is expected to fail in
this repository snapshot.  It reports that the cached Theorem-III lower artifact
supports a lower interval ending at `0.265`, while the compact replay claims a
near-critical lower anchor ending at `0.971636`.  The resulting margin is
negative:

```text
0.265 - 0.971636 = -0.706636
```

This is intentional.  The new audit layer exposes the exact proof-carrying gap
that Phase 2 must close: a near-critical lower-corridor continuation chain must
be generated and consumed as raw proof payload before the proof-audit replay can
replace the compact shell replay.

## Useful commands

```bash
python scripts/audit/bootstrap_proof_audit_layout.py --repository-root .
python scripts/audit/build_current_state_red_team_audit.py --repository-root .
python scripts/audit/replay_from_proof_audit.py \
  artifacts/proof_audit/current_state_red_team_audit.json \
  --repository-root . --allow-missing-layers --expect-fail
python scripts/replay_minimal.py --out artifacts/paper_replay/minimal
```

The minimal replay remains a compact smoke test.  The proof-audit path is the
new theorem-facing direction and is intentionally stricter.

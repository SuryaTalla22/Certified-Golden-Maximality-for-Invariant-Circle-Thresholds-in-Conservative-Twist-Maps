# Phase 7: Heavy Replay and Proof-Carrying Verification Protocol

Phase 7 adds a tiered replay protocol around the proof-audit artifacts produced
in Phases 0--6.  The goal is not to hide expensive computations behind compact
status fields, but to make the replay boundary explicit and fail-closed.

## Entry points

- `scripts/replay_heavy_lower.py` regenerates the lower-corridor audit ledger
  from the cached Theorem-III artifact and writes a replay-level report.  In the
  current snapshot this exposes the known fail-closed condition that the visible
  lower chain does not reach the near-critical final anchor.
- `scripts/replay_heavy_upper.py` regenerates the upper-obstruction audit from
  the Theorem-IV promotion artifact and verifies the analytic-incompatibility
  margin.
- `scripts/replay_artifact_audit_suite.py` validates the proof-audit bundles,
  checks the replay audit manifest hashes, and attempts strict artifact-derived
  final replay only when all bundles are final-ready.
- `scripts/replay_full_verified.py` runs the tiered lower, upper, transport,
  arithmetic-domain, GL(2,Z), and artifact-suite checks in sequence.
- `scripts/replay_full.py` remains a fail-closed sentinel.  It now points to
  `scripts/replay_full_verified.py` for the Phase-7 protocol.

## Current status

The Phase-7 protocol completes with status `passed-with-known-lower-gap` when
`--allow-known-lower-gap` is used.  This is intentional.  It means the replay
infrastructure is functioning, all non-lower audit bundles validate, hashes are
checked, and the remaining lower near-critical anchor gap is reported rather
than silently promoted to theorem evidence.

Strict final mode remains fail-closed until a proof-carrying lower continuation
artifact reaches the near-critical final anchor.

## Generated outputs

- `artifacts/proof_audit/replay/heavy_lower_report.json`
- `artifacts/proof_audit/replay/heavy_upper_report.json`
- `artifacts/proof_audit/replay/artifact_audit_suite_report.json`
- `artifacts/proof_audit/replay/full_verified_report.json`
- `artifacts/proof_audit/replay/replay_audit_manifest.json`
- `artifacts/proof_audit/replay/replay_runtime_table.json`

The manifest hash-pins the Phase-0--6 proof-audit bundles consumed by the fast
artifact suite.  Tampering with a bundle while leaving status strings unchanged
is rejected by either the hash manifest or the proof-payload validator.

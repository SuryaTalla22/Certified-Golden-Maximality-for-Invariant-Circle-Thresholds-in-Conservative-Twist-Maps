# Phase 8: Validator Hardening and Negative Controls

Phase 8 adds the hardened proof-payload validation boundary.  Earlier phases
created proof-audit bundles and layer-specific ledgers.  This phase prevents the
final replay from accepting theorem-facing status strings unless the relevant
Booleans are derived from raw interval or symbolic payloads and the critical
inequalities are recomputed against those raw fields.

## New module

`kam_theorem_suite/audit/proof_payload_validator.py`

Core public functions:

- `require_derived_boolean(payload, name)` rejects absent, false, trusted, diagnostic-only, or dependency-free theorem-facing Booleans.
- `recompute_interval_inequality(payload, inequality_name)` recomputes the stored scalar inequality margin.
- `verify_no_trusted_final_booleans(payload)` rejects any trusted theorem-facing Boolean.
- `verify_payload_hash_and_content(payload)` checks diagnostic/theorem-facing separation and returns a stable content hash.
- `validate_layer_payload(payload, ...)` dispatches to layer-specific hardened validation.
- `validate_proof_audit_bundle(path_or_payload, ...)` validates a single payload or the standard `artifacts/proof_audit` directory.

Layer-specific validators additionally check theorem-critical raw-field links:

- Theorem III lower corridor: recomputes segment radii margins from `Y + Zr + T < r`, checks overlap/final-anchor inequalities, and rejects a true `lower_chain_verified` Boolean if any raw segment fails.
- Theorem IV upper obstruction: recomputes obstruction separation from `certified_barrier_interval.lo - certified_upper_interval.hi` and rejects stale incompatibility margins after raw endpoint perturbations.
- Theorem V transport: recomputes component totals, remaining gap, target-width formulas, and raw interval enclosure of the budget ledger.
- Theorem VII domain exhaustion: checks every generated record has a valid route and control certificate, nonempty failure fields are rejected, and near-top upper bound is below the golden lower anchor.
- Theorem VIII GL(2,Z): checks representative selection rather than analytic conjugacy, one accepted distinct representative, no accepted nongolden representative, and no duplicated golden representative.

## Final replay integration

`validate_paper_replay_shells(..., require_proof_audit_payloads=True)` now requires embedded proof-audit payloads and revalidates them through the hardened validators.  Compact smoke replay remains available for lightweight regression tests, but the proof-audit path no longer trusts compact Booleans such as:

- `analytic_incompatibility_certified`,
- `preserves_golden_gap`,
- `domain_exhaustion_certified`,
- `gl2z_normalization_certified`.

The artifact-derived shell builders now attach the full proof-audit bundle to the shell fields consumed by final replay:

- `proof_audit_bundle`,
- `upper_obstruction_audit`,
- `transport_budget_audit`,
- `domain_audit_bundle`,
- `gl2z_audit_bundle`.

## CLI

Run the hardened directory validator while allowing the known Phase-2 lower-anchor gap:

```bash
python -S scripts/audit/validate_proof_payloads.py --allow-known-lower-gap
```

Run it in strict mode:

```bash
python -S scripts/audit/validate_proof_payloads.py
```

Strict mode currently fails, as expected, because the lower-corridor proof-carrying chain still does not reach the near-critical final anchor.

## Negative controls

`tests/test_proof_payload_negative_controls.py` implements the required Phase-8 controls:

1. `analytic_incompatibility_certified=true` with negative/raw-inconsistent upper margin fails.
2. `transport_gap_preservation_certified=true` while transport budget exceeds available gap fails.
3. `lower_chain_verified=true` while a segment radii margin is negative fails.
4. `domain_exhaustion_certified=true` with an uncontrolled generated record fails.
5. `gl2z_normalization_certified=true` with a duplicate golden representative fails.
6. Preserved status strings with perturbed raw endpoints fail.
7. Removed source fields used by derived inequalities fail.
8. Diagnostic artifacts with the same endpoint numbers are rejected.

## Current status

The hardened validator passes all closed audit layers and still reports the known lower gap honestly:

- permissive reviewer path: `passed-with-known-lower-gap`,
- strict final path: `failed`, because `final_anchor_not_reached` remains in the Theorem-III lower payload.

This is the intended Phase-8 state: the validator is now stricter than the compact replay, and strict final readiness remains blocked only by the already-known lower near-critical continuation issue rather than by trusted status strings.

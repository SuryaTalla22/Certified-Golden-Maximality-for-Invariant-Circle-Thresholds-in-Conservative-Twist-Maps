# Track B Phase 5G-c: Promotion-gate recognition patch

Phase 5G-b writes component evidence in a nested `formal_evidence` dictionary.  The existing Phase 5E promotion gate recognized only top-level boolean flags, so it still reported `outward_rounded_residual_proof` and `small_divisor_proof` as missing even though the corrected component attachment contained them.

This overlay patches `phase5e_promotion_gate.py` so each required evidence key may be recognized from:

1. a top-level literal `true`,
2. `formal_evidence[<key>] == true`, or
3. a legacy `formal_evidence_true_flags` list.

The patch remains strict: truthy strings or integers do not count.  The gate must still reject fail-closed until all remaining formal evidence flags are true.

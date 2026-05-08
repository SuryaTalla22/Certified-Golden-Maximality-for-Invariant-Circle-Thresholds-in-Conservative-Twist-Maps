#!/usr/bin/env bash
set -euo pipefail

# Phase 6 downstream regeneration helper.
# This script does NOT guess repo-specific final generator arguments.  It prints the
# validated promoted Theorem III path and lists likely generator scripts to run.

export THEOREM_I_ARTIFACT="artifacts/final_discharge/stage_cache/theorem_i_ii.json"
export THEOREM_II_ARTIFACT="artifacts/final_discharge/stage_cache/theorem_i_ii.json"
export THEOREM_III_ARTIFACT="artifacts/proof_audit/theorem_iii_trackb/phase6_final_integration/theorem_iii_trackb_PHASE6_FINAL_LOWER_ANCHOR_CERTIFICATE.json"
export THEOREM_IV_ARTIFACT="artifacts/final_discharge/stage_cache/theorem_iv.json"
export PHASE6_DOWNSTREAM_OUT="artifacts/proof_audit/final_integration_regenerated"

mkdir -p "$PHASE6_DOWNSTREAM_OUT"

echo "Theorem I artifact:   $THEOREM_I_ARTIFACT"
echo "Theorem II artifact:  $THEOREM_II_ARTIFACT"
echo "Theorem III artifact: $THEOREM_III_ARTIFACT"
echo "Theorem IV artifact:  $THEOREM_IV_ARTIFACT"
echo "Downstream out:       $PHASE6_DOWNSTREAM_OUT"

echo
echo "Likely final-integration/regeneration scripts in this repo:"
find scripts -type f   \( -iname '*theorem*final*.py' -o -iname '*global*replay*.py' -o -iname '*proof*graph*.py' -o -iname '*certificate*index*.py' -o -iname '*audit*summary*.py' -o -iname '*paper*certificate*.py' \)   | sort || true

echo
echo "Suggested workflow:"
echo "  1. Replace the old Theorem III input with: $THEOREM_III_ARTIFACT"
echo "  2. Re-run the repository's existing full theorem graph / proof-audit generators."
echo "  3. Verify generated artifacts cite K=0.971635, nu=1.001, radius=3e-5, cutoff=full."
echo "  4. Verify no generated artifact references the obsolete Theorem III artifact."

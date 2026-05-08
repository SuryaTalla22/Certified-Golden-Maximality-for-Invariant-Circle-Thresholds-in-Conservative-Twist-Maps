# Track B Phase 5K: Global backend and independent replay promotion gate

Phase 5K is the final lower-anchor promotion scaffold.  It does not introduce new
analytic constants.  It verifies that all local and graph-integration formal
components already attached in Phases 5G--5J are present, hash-bound to the exact
Phase 5D certificate scaffold, and threshold-compatible.

The phase has two steps:

1. `generate_theorem_iii_trackb_phase5k_global_backend.py` builds a global backend
   candidate attachment.  This sets `formal_interval_backend=true` but keeps
   `independent_replay_passed=false`, so Phase 5E must still reject it.
2. `run_theorem_iii_trackb_phase5k_independent_replay.py` independently replays
   the candidate, runs negative controls, and emits a promoted attachment only if
   all checks pass.  This promoted attachment sets both global flags true.

After Phase 5K replay, rerun Phase 5E with the promoted attachment.  The expected
outcome is an accepted theorem-facing lower-anchor certificate.  This object still
certifies only the direct lower anchor; it does not by itself certify a full
parameter interval or mesh corridor.

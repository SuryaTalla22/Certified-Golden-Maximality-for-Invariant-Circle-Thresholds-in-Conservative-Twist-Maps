# Track B Phase 5F-b: Certificate-hash binding patch

Phase 5F-b is a small integrity patch.  It does **not** create theorem-facing evidence.
It adds the exact Phase 5D scaffold byte-level SHA256 hash to the top level of the
Phase 5F attachment candidate, because the Phase 5E promotion gate expects that
field before it can distinguish a real formal-evidence failure from an attachment
metadata binding failure.

Expected outcome:

- Phase 5F-b binding replay passes.
- Phase 5E still rejects fail-closed.
- After rerunning Phase 5E, the only remaining formal-attachment failures should be
  the intentionally false formal evidence flags.

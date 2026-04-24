# Certificate glossary

This glossary gives the paper-facing meaning of the main certificate families.
It is intentionally shorter than the code documentation; the manuscript supplies
the mathematical statements and this file identifies the audit role of each
object.

| Certificate family | Meaning in the proof package |
|---|---|
| Workstream / Theorems I--II | Fixes the certified family, normalization conventions, and foundational workstream objects consumed downstream. |
| Theorem III lower corridor | Supplies the persistence-side lower anchor and lower-corridor compatibility required by threshold identification. |
| Theorem IV upper obstruction | Supplies the obstruction/nonexistence-side upper object, including support-core, tail-coherence, tail-stability, and analytic-incompatibility checks. |
| Compressed Theorem V contract | The theorem-facing rational-to-irrational transport object.  This is the downstream proof object; raw diagnostic transport shells are not consumed. |
| Threshold identification | Aligns lower, upper, and transport objects into a common threshold branch and checks branch/chart compatibility. |
| Theorem VI envelope/top-gap | Proves the screened one-variable envelope/top-gap interface and hands global challenger obligations to Theorem VII. |
| Theorem VII global exhaustion | Certifies that every nongolden challenger is ranked, pruned, panel-complete, lifecycle-dominated, termination-promoted, or omitted-tail controlled. |
| Theorem VIII final reduction | Converts identification, envelope control, and global exhaustion into the final golden maximality theorem with `GL(2,Z)` normalization and universe matching. |
| Stage/final replay | Regenerates the terminal theorem ledger and verifies that no active assumptions, open hypotheses, or remaining mathematical burden remain. |
| Artifact manifest | Lists generated theorem/cache artifacts, their mathematical role, and SHA256 hash. |
| Hash ledger | Machine-checkable SHA256 ledger for artifacts and core audit files. |
| Negative controls | Tests that deliberately perturb theorem-facing fields and must be rejected by the validator. |

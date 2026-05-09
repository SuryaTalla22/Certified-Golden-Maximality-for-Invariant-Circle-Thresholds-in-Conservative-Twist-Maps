# Phase 2H: Lower-Anchor Execution and Merge Controller

Phase 2H adds the orchestration layer after the Phase 2G adaptive-refinement planner. It inventories available lower-anchor segment candidates, identifies missing or non-theorem-ready segments, writes a reproducible missing-segment execution script, records merge inputs, and emits a fail-closed status report before strict Phase-2B ingestion.

The current packaged state contains the Phase 2F chunk for segments 000--001 and does not yet contain the eight remaining executed segment candidates. Therefore the generated status report is intentionally non-promotable:

- ready segments: 2
- missing segments: 8
- final anchor reached by available segments: false
- promotion allowed: false

This is the correct fail-closed outcome. The next expensive action is to run `scripts/audit/run_phase2h_missing_segments.sh`, merge all resulting candidates, and run strict Phase-2B ingestion.

Promotion remains blocked until every segment has analytic theorem closure, positive recomputed radii margin, positive overlap, and coverage through `[0.971635, 0.971636]`.

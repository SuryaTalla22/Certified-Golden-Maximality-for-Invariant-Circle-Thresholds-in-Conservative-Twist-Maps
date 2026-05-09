# Phase 5I-b NaN-safe serialization patch

This corrective overlay preserves the Phase 5I mathematical logic and only fixes JSON serialization. Some optional diagnostic fields inherited from older component records may be represented internally as `NaN` when unavailable. Phase 5I writes with `allow_nan=False`, so these optional non-finite values caused generation to abort before the fail-closed attachment could be written.

The patch adds a serialization-boundary sanitizer that converts optional non-finite float values to `null` while keeping required proof quantities separately checked for finiteness by the component validators. The generated compact report records how many optional non-finite values were sanitized.

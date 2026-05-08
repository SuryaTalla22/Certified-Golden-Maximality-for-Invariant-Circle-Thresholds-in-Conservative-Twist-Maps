from __future__ import annotations

"""Small extractors for theorem-facing fields in cached stage artifacts.

The functions here intentionally extract only lightweight scalar/interval fields.
They do not rerun any heavy numerical solve and they do not certify a theorem by
existence alone; certification happens in :mod:`proof_bundle_validator` and in
higher-level audit builders.
"""

from pathlib import Path
from typing import Any, Mapping, Sequence
import json


def load_json(path: str | Path) -> dict[str, Any]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(p)
    data = json.loads(p.read_text())
    if not isinstance(data, dict):
        raise TypeError(f"expected JSON object at {p}, got {type(data).__name__}")
    return data


def json_pointer_get(data: Mapping[str, Any], pointer: str, default: Any = None) -> Any:
    """Return the value at an RFC-6901-like JSON pointer, or ``default``."""

    if pointer in ("", "/"):
        return data
    current: Any = data
    for raw_part in pointer.strip("/").split("/"):
        part = raw_part.replace("~1", "/").replace("~0", "~")
        if isinstance(current, Mapping):
            if part not in current:
                return default
            current = current[part]
        elif isinstance(current, Sequence) and not isinstance(current, (str, bytes, bytearray)):
            try:
                current = current[int(part)]
            except Exception:
                return default
        else:
            return default
    return current


def as_interval(value: Any, *, label: str, source_artifact: str = "", source_json_pointer: str = "") -> tuple[float, float]:
    """Coerce a two-element JSON array into a scalar interval."""

    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)) or len(value) != 2:
        raise ValueError(f"{label} is not a two-element interval: {value!r}")
    return (float(value[0]), float(value[1]))


def extract_theorem_iii_lower_fields(theorem_iii_path: str | Path) -> dict[str, Any]:
    """Extract lower-side intervals used by the Phase-1 red-team audit."""

    path = Path(theorem_iii_path)
    data = load_json(path)
    certified = as_interval(
        json_pointer_get(data, "/certified_below_threshold_interval"),
        label="certified_below_threshold_interval",
        source_artifact=path.as_posix(),
        source_json_pointer="/certified_below_threshold_interval",
    )
    neighborhood = json_pointer_get(data, "/lower_neighborhood_closure/stable_lower_interval", None)
    stable_lower_interval = None
    if neighborhood is not None:
        stable_lower_interval = as_interval(
            neighborhood,
            label="stable_lower_interval",
            source_artifact=path.as_posix(),
            source_json_pointer="/lower_neighborhood_closure/stable_lower_interval",
        )
    stable_lower_bound = json_pointer_get(data, "/lower_neighborhood_closure/stable_certified_lower_bound", None)
    return {
        "source_artifact": path.as_posix(),
        "certified_below_threshold_interval": certified,
        "stable_lower_interval": stable_lower_interval,
        "stable_certified_lower_bound": None if stable_lower_bound is None else float(stable_lower_bound),
        "theorem_status": str(data.get("theorem_iii_final_status", data.get("theorem_status", ""))),
        "residual_theorem_iii_burden": list(data.get("residual_theorem_iii_burden", [])),
    }

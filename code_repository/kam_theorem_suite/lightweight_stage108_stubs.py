from __future__ import annotations

"""Install lightweight stubs for Stage-108 paper-facing replay.

The final replay modules import some heavy builder modules even when compact
shell dictionaries are supplied.  These stubs make the minimal replay independent
of optional numerical dependencies and Theorem-IV regeneration.  They are used
only by paper-facing smoke scripts/tests; archival replay should import the real
builders.
"""

from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
import sys
from typing import Any


class _Obj:
    def __init__(self, d: dict[str, Any] | None = None):
        self.d = d or {}

    def to_dict(self) -> dict[str, Any]:
        return dict(self.d)


@dataclass
class LightweightHarmonicFamily:
    harmonics: tuple = ((1.0, 1),)


def _build_stub(**_: Any) -> _Obj:
    return _Obj({"theorem_status": "stub-front-complete", "open_hypotheses": [], "active_assumptions": []})


def _stub_module(qualified_name: str, **attrs: Any) -> None:
    module = ModuleType(qualified_name)
    for key, value in attrs.items():
        setattr(module, key, value)
    sys.modules[qualified_name] = module


def install_lightweight_stage108_stubs() -> None:
    """Install stubs for heavy upstream builders used by final replay imports."""

    pkg_name = "kam_theorem_suite"
    pkg_path = Path(__file__).resolve().parent
    package = sys.modules.get(pkg_name)
    if package is None:
        package = ModuleType(pkg_name)
        package.__path__ = [str(pkg_path)]  # type: ignore[attr-defined]
        sys.modules[pkg_name] = package
    elif not hasattr(package, "__path__"):
        package.__path__ = [str(pkg_path)]  # type: ignore[attr-defined]

    _stub_module(f"{pkg_name}.standard_map", HarmonicFamily=LightweightHarmonicFamily)
    _stub_module(
        f"{pkg_name}.golden_aposteriori",
        build_golden_theorem_iii_certificate=_build_stub,
        golden_inverse=lambda: 0.6180339887498948,
    )
    _stub_module(f"{pkg_name}.theorem_iv_analytic_lift", build_golden_theorem_iv_certificate=_build_stub)
    _stub_module(f"{pkg_name}.theorem_v_transport_lift", build_golden_theorem_v_certificate=_build_stub, build_golden_theorem_v_compressed_lift_certificate=lambda **kwargs: {"compressed_contract": {"theorem_status": "golden-theorem-v-compressed-contract-strong"}, "theorem_status": "golden-theorem-v-compressed-contract-strong"})
    _stub_module(
        f"{pkg_name}.threshold_identification_lift",
        build_golden_theorem_ii_to_v_identification_certificate=_build_stub,
    )
    _stub_module(f"{pkg_name}.theorem_vi_envelope_lift", build_golden_theorem_vi_certificate=_build_stub)
    _stub_module(f"{pkg_name}.theorem_vii_exhaustion_lift", build_golden_theorem_vii_certificate=_build_stub)
    _stub_module(
        f"{pkg_name}.theorem_vii_exhaustion_discharge",
        build_golden_theorem_vii_discharge_certificate=_build_stub,
    )
    _stub_module(
        f"{pkg_name}.theorem_i_ii_workstream_lift",
        build_golden_theorem_i_ii_workstream_lift_certificate=_build_stub,
        build_golden_theorem_i_ii_certificate=_build_stub,
    )
    _stub_module(
        f"{pkg_name}.threshold_identification_discharge",
        RESIDUAL_LOCAL_IDENTIFICATION_ASSUMPTION="localized_identification_hinge",
    )
    _stub_module(
        f"{pkg_name}.threshold_identification_transport_discharge",
        RESIDUAL_TRANSPORT_LOCKED_IDENTIFICATION_ASSUMPTION="transport_locked_identification_hinge",
    )

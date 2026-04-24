from __future__ import annotations

"""Batched/staged builders for Theorem V.

These helpers mirror the staged Theorem-IV workflow: expensive Theorem-V pieces
can be built as individually timed/cacheable stages so users can inspect where
runtime is going and resume interrupted runs without rebuilding everything.
"""

from inspect import signature
import json
from pathlib import Path
import time
from typing import Any, Callable, Mapping

from .branch_certified_limit_control import build_branch_certified_irrational_limit_certificate
from .certified_tail_modulus_control import build_certified_tail_modulus_certificate
from .convergent_family_limit_control import build_convergent_family_limit_certificate
from .edge_class_weighted_golden_rate_control import build_edge_class_weighted_golden_rate_certificate
from .global_transport_potential_control import build_global_transport_potential_certificate
from .golden_aposteriori import golden_inverse
from .golden_limit_bridge import (
    build_final_transport_bridge_certificate,
    build_golden_rational_to_irrational_convergence_certificate,
)
from .golden_lower_neighborhood_stability import build_golden_lower_neighborhood_stability_certificate
from .golden_recurrence_rate_control import build_golden_recurrence_rate_certificate
from .golden_supercritical import build_golden_supercritical_obstruction_certificate
from .golden_upper_tail_stability import (
    build_golden_upper_tail_stability_certificate,
    build_golden_upper_tail_stability_certificate_from_theorem_iv,
)
from .irrational_limit_control import build_rational_irrational_convergence_certificate
from .nested_subladder_limit_control import build_nested_subladder_limit_certificate
from .pairwise_transport_chain_control import build_pairwise_transport_chain_limit_certificate
from .rate_aware_tail_modulus_control import build_rate_aware_tail_modulus_certificate
from .standard_map import HarmonicFamily
from .tail_cauchy_potential_control import build_tail_cauchy_potential_certificate
from .theorem_v_error_control import build_theorem_v_explicit_error_certificate, build_theorem_v_final_error_law_certificate
from .theorem_v_transport_lift import (
    build_golden_theorem_v_transport_lift_certificate,
    build_golden_theorem_v_compressed_lift_certificate,
)
from .theorem_v_uniform_error_law import build_theorem_v_uniform_error_law_certificate
from .theorem_v_branch_identification import build_theorem_v_branch_identification_certificate
from .theorem_v_row_refinement import build_runtime_aware_theorem_v_row_certificate
from .theorem_v_upper_seed import build_golden_supercritical_obstruction_certificate_from_theorem_iv
from .transport_certified_limit_control import build_transport_certified_limit_certificate
from .transport_slope_weighted_golden_rate_control import build_transport_slope_weighted_golden_rate_certificate
from .triple_transport_cocycle_control import build_triple_transport_cocycle_limit_certificate


def _repo_stage_cache_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "artifacts" / "final_discharge" / "stage_cache" / "theorem_v_batches"


def _filter_kwargs(fn: Callable[..., Any], kwargs: Mapping[str, Any]) -> dict[str, Any]:
    params = signature(fn).parameters
    return {k: v for k, v in kwargs.items() if k in params}


def _jsonify(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {str(k): _jsonify(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_jsonify(v) for v in obj]
    if hasattr(obj, "to_dict"):
        try:
            return _jsonify(obj.to_dict())
        except Exception:
            pass
    return obj


def _as_dict(obj: Any) -> dict[str, Any]:
    if isinstance(obj, dict):
        return obj
    if hasattr(obj, "to_dict"):
        return dict(obj.to_dict())
    return dict(obj)


def _stage_path(stage_cache_dir: Path, name: str) -> Path:
    return stage_cache_dir / f"{name}.json"


def _build_or_load_stage(
    name: str,
    builder: Callable[[], Any],
    *,
    stage_cache_dir: Path,
    use_cache: bool,
    force_rebuild: bool,
    timings: dict[str, Any],
) -> dict[str, Any]:
    path = _stage_path(stage_cache_dir, name)
    if use_cache and not force_rebuild and path.exists():
        payload = json.loads(path.read_text(encoding="utf-8"))
        timings[name] = {
            "source": "cache",
            "seconds": 0.0,
            "cache_path": str(path),
        }
        return payload
    t0 = time.perf_counter()
    payload = _jsonify(builder())
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    timings[name] = {
        "source": "built",
        "seconds": time.perf_counter() - t0,
        "cache_path": str(path),
    }
    return payload


def build_golden_rational_to_irrational_convergence_certificate_batched(
    base_K_values,
    family: HarmonicFamily | None = None,
    *,
    rho: float | None = None,
    theorem_iii_certificate: Mapping[str, Any] | None = None,
    theorem_iv_certificate: Mapping[str, Any] | None = None,
    use_cache: bool = True,
    force_rebuild: bool = False,
    stage_cache_dir: str | Path | None = None,
    **kwargs,
) -> dict[str, Any]:
    family = family or HarmonicFamily()
    rho = float(golden_inverse() if rho is None else rho)
    cache_dir = Path(stage_cache_dir) if stage_cache_dir is not None else _repo_stage_cache_dir()
    timings: dict[str, Any] = {}

    lower = _build_or_load_stage(
        "theorem_v_lower",
        lambda: build_golden_lower_neighborhood_stability_certificate(
            base_K_values=base_K_values,
            family=family,
            rho=rho,
            **_filter_kwargs(build_golden_lower_neighborhood_stability_certificate, kwargs),
        ),
        stage_cache_dir=cache_dir,
        use_cache=use_cache,
        force_rebuild=force_rebuild,
        timings=timings,
    )

    def _upper_builder():
        if theorem_iv_certificate is not None and kwargs.get("reuse_theorem_iv_upper_seed", True):
            return build_golden_supercritical_obstruction_certificate_from_theorem_iv(
                theorem_iv_certificate,
                preferred_shift=float(kwargs.get("theorem_iv_preferred_shift", 0.0)),
                stage_cache_dir=kwargs.get("theorem_iv_stage_cache_dir"),
                target_residue=float(kwargs.get("target_residue", 0.25)),
            )
        return build_golden_supercritical_obstruction_certificate(
            family=family,
            rho=rho,
            **_filter_kwargs(build_golden_supercritical_obstruction_certificate, kwargs),
        )

    upper = _build_or_load_stage(
        "theorem_v_upper_seed",
        _upper_builder,
        stage_cache_dir=cache_dir,
        use_cache=use_cache,
        force_rebuild=force_rebuild,
        timings=timings,
    )

    def _upper_tail_builder():
        if theorem_iv_certificate is not None:
            return build_golden_upper_tail_stability_certificate_from_theorem_iv(theorem_iv_certificate)
        return build_golden_upper_tail_stability_certificate(
            family=family,
            rho=rho,
            **_filter_kwargs(build_golden_upper_tail_stability_certificate, kwargs),
        )

    upper_tail = _build_or_load_stage(
        "theorem_v_upper_tail",
        _upper_tail_builder,
        stage_cache_dir=cache_dir,
        use_cache=use_cache,
        force_rebuild=force_rebuild,
        timings=timings,
    )

    ladder = dict(upper.get("ladder") or {})
    refined = dict(upper.get("refined") or {})
    asymptotic_audit = dict(upper.get("asymptotic_audit") or {})
    family_label = "standard-sine" if len(family.harmonics) == 1 and family.harmonics[0][1] == 1 else "custom-harmonic"

    convergence = _build_or_load_stage(
        "theorem_v_convergence",
        lambda: build_rational_irrational_convergence_certificate(
            ladder,
            refined=refined,
            asymptotic_audit=asymptotic_audit,
            rho_target=rho,
            family_label=family_label,
            **_filter_kwargs(build_rational_irrational_convergence_certificate, kwargs),
        ),
        stage_cache_dir=cache_dir,
        use_cache=use_cache,
        force_rebuild=force_rebuild,
        timings=timings,
    )
    branch = _build_or_load_stage(
        "theorem_v_branch_certified",
        lambda: build_branch_certified_irrational_limit_certificate(
            ladder,
            refined=refined,
            asymptotic_audit=asymptotic_audit,
            rho_target=rho,
            family_label=family_label,
            **_filter_kwargs(build_branch_certified_irrational_limit_certificate, kwargs),
        ),
        stage_cache_dir=cache_dir,
        use_cache=use_cache,
        force_rebuild=force_rebuild,
        timings=timings,
    )
    nested = _build_or_load_stage(
        "theorem_v_nested_subladder",
        lambda: build_nested_subladder_limit_certificate(
            ladder,
            refined=refined,
            asymptotic_audit=asymptotic_audit,
            rho_target=rho,
            family_label=family_label,
            **_filter_kwargs(build_nested_subladder_limit_certificate, kwargs),
        ),
        stage_cache_dir=cache_dir,
        use_cache=use_cache,
        force_rebuild=force_rebuild,
        timings=timings,
    )
    convergent = _build_or_load_stage(
        "theorem_v_convergent_family",
        lambda: build_convergent_family_limit_certificate(
            ladder,
            rho_target=rho,
            family_label=family_label,
            **_filter_kwargs(build_convergent_family_limit_certificate, kwargs),
        ),
        stage_cache_dir=cache_dir,
        use_cache=use_cache,
        force_rebuild=force_rebuild,
        timings=timings,
    )
    transport = _build_or_load_stage(
        "theorem_v_transport_certified",
        lambda: build_transport_certified_limit_certificate(
            ladder,
            rho_target=rho,
            family_label=family_label,
            **_filter_kwargs(build_transport_certified_limit_certificate, kwargs),
        ),
        stage_cache_dir=cache_dir,
        use_cache=use_cache,
        force_rebuild=force_rebuild,
        timings=timings,
    )
    pairwise = _build_or_load_stage(
        "theorem_v_pairwise_transport",
        lambda: build_pairwise_transport_chain_limit_certificate(
            ladder,
            rho_target=rho,
            family_label=family_label,
            **_filter_kwargs(build_pairwise_transport_chain_limit_certificate, kwargs),
        ),
        stage_cache_dir=cache_dir,
        use_cache=use_cache,
        force_rebuild=force_rebuild,
        timings=timings,
    )
    triple = _build_or_load_stage(
        "theorem_v_triple_transport_cocycle",
        lambda: build_triple_transport_cocycle_limit_certificate(
            ladder,
            rho_target=rho,
            family_label=family_label,
            **_filter_kwargs(build_triple_transport_cocycle_limit_certificate, kwargs),
        ),
        stage_cache_dir=cache_dir,
        use_cache=use_cache,
        force_rebuild=force_rebuild,
        timings=timings,
    )
    global_potential = _build_or_load_stage(
        "theorem_v_global_transport_potential",
        lambda: build_global_transport_potential_certificate(
            ladder,
            rho_target=rho,
            family_label=family_label,
            **_filter_kwargs(build_global_transport_potential_certificate, kwargs),
        ),
        stage_cache_dir=cache_dir,
        use_cache=use_cache,
        force_rebuild=force_rebuild,
        timings=timings,
    )
    tail_cauchy = _build_or_load_stage(
        "theorem_v_tail_cauchy_potential",
        lambda: build_tail_cauchy_potential_certificate(
            ladder,
            rho_target=rho,
            family_label=family_label,
            **_filter_kwargs(build_tail_cauchy_potential_certificate, kwargs),
        ),
        stage_cache_dir=cache_dir,
        use_cache=use_cache,
        force_rebuild=force_rebuild,
        timings=timings,
    )
    certified_modulus = _build_or_load_stage(
        "theorem_v_certified_tail_modulus",
        lambda: build_certified_tail_modulus_certificate(
            ladder,
            rho_target=rho,
            family_label=family_label,
            **_filter_kwargs(build_certified_tail_modulus_certificate, kwargs),
        ),
        stage_cache_dir=cache_dir,
        use_cache=use_cache,
        force_rebuild=force_rebuild,
        timings=timings,
    )
    rate_modulus = _build_or_load_stage(
        "theorem_v_rate_aware_tail_modulus",
        lambda: build_rate_aware_tail_modulus_certificate(
            ladder,
            rho_target=rho,
            family_label=family_label,
            **_filter_kwargs(build_rate_aware_tail_modulus_certificate, kwargs),
        ),
        stage_cache_dir=cache_dir,
        use_cache=use_cache,
        force_rebuild=force_rebuild,
        timings=timings,
    )
    golden_rate = _build_or_load_stage(
        "theorem_v_golden_recurrence_rate",
        lambda: build_golden_recurrence_rate_certificate(
            ladder,
            rho_target=rho,
            family_label=family_label,
            **_filter_kwargs(build_golden_recurrence_rate_certificate, kwargs),
        ),
        stage_cache_dir=cache_dir,
        use_cache=use_cache,
        force_rebuild=force_rebuild,
        timings=timings,
    )
    transport_weighted = _build_or_load_stage(
        "theorem_v_transport_slope_weighted_golden_rate",
        lambda: build_transport_slope_weighted_golden_rate_certificate(
            ladder,
            rho_target=rho,
            family_label=family_label,
            **_filter_kwargs(build_transport_slope_weighted_golden_rate_certificate, kwargs),
        ),
        stage_cache_dir=cache_dir,
        use_cache=use_cache,
        force_rebuild=force_rebuild,
        timings=timings,
    )
    edge_weighted = _build_or_load_stage(
        "theorem_v_edge_class_weighted_golden_rate",
        lambda: build_edge_class_weighted_golden_rate_certificate(
            ladder,
            rho_target=rho,
            family_label=family_label,
            **_filter_kwargs(build_edge_class_weighted_golden_rate_certificate, kwargs),
        ),
        stage_cache_dir=cache_dir,
        use_cache=use_cache,
        force_rebuild=force_rebuild,
        timings=timings,
    )

    explicit_error = _build_or_load_stage(
        "theorem_v_explicit_error",
        lambda: build_theorem_v_explicit_error_certificate(
            ladder,
            refined=refined,
            asymptotic_audit=asymptotic_audit,
            rho_target=rho,
            family_label=family_label,
            convergence_control=convergence,
            branch_certified_control=branch,
            nested_subladder_control=nested,
            convergent_family_control=convergent,
            transport_certified_control=transport,
            pairwise_transport_control=pairwise,
            triple_transport_cocycle_control=triple,
            global_transport_potential_control=global_potential,
            tail_cauchy_potential_control=tail_cauchy,
            certified_tail_modulus_control=certified_modulus,
            rate_aware_tail_modulus_control=rate_modulus,
            golden_recurrence_rate_control=golden_rate,
            transport_slope_weighted_golden_rate_control=transport_weighted,
            edge_class_weighted_golden_rate_control=edge_weighted,
            **_filter_kwargs(build_theorem_v_explicit_error_certificate, kwargs),
        ),
        stage_cache_dir=cache_dir,
        use_cache=use_cache,
        force_rebuild=force_rebuild,
        timings=timings,
    )
    final_error = _build_or_load_stage(
        "theorem_v_final_error",
        lambda: build_theorem_v_final_error_law_certificate(
            explicit_error_certificate=explicit_error,
            reference_lower_bound=lower.get("stable_lower_bound"),
            min_uniform_chain_length=max(3, int(kwargs.get("tail_cauchy_min_chain_length", 4))),
        ),
        stage_cache_dir=cache_dir,
        use_cache=use_cache,
        force_rebuild=force_rebuild,
        timings=timings,
    )
    # Re-evaluate the runtime-aware rows once the explicit/final error shells expose a theorem target interval.
    runtime_row_233_377 = _build_or_load_stage(
        "theorem_v_runtime_row_233_377",
        lambda: build_runtime_aware_theorem_v_row_certificate(
            ladder,
            p=233,
            q=377,
            family=family,
            theorem_target_interval=final_error.get("theorem_target_interval"),
            explicit_error_certificate=explicit_error,
            allow_direct_refinement=bool(kwargs.get("runtime_aware_allow_direct_rows", False)),
            budget_hours=float(kwargs.get("runtime_aware_budget_hours_233_377", 8.0)),
            hard_q_cap=int(kwargs.get("runtime_aware_direct_q_cap", 400)),
            reference_q=int(kwargs.get("runtime_aware_reference_q", 233)),
            reference_hours=float(kwargs.get("runtime_aware_reference_hours", 6.0)),
            scaling_exponent=float(kwargs.get("runtime_aware_scaling_exponent", 2.3)),
            target_residue=float(kwargs.get("target_residue", 0.25)),
        ),
        stage_cache_dir=cache_dir,
        use_cache=use_cache,
        force_rebuild=force_rebuild,
        timings=timings,
    )
    runtime_row_377_610 = _build_or_load_stage(
        "theorem_v_runtime_row_377_610",
        lambda: build_runtime_aware_theorem_v_row_certificate(
            ladder,
            p=377,
            q=610,
            family=family,
            theorem_target_interval=final_error.get("theorem_target_interval"),
            explicit_error_certificate=explicit_error,
            allow_direct_refinement=bool(kwargs.get("runtime_aware_allow_direct_rows", False)),
            budget_hours=float(kwargs.get("runtime_aware_budget_hours_377_610", 18.0)),
            hard_q_cap=int(kwargs.get("runtime_aware_direct_q_cap", 400)),
            reference_q=int(kwargs.get("runtime_aware_reference_q", 233)),
            reference_hours=float(kwargs.get("runtime_aware_reference_hours", 6.0)),
            scaling_exponent=float(kwargs.get("runtime_aware_scaling_exponent", 2.3)),
            target_residue=float(kwargs.get("target_residue", 0.25)),
        ),
        stage_cache_dir=cache_dir,
        use_cache=use_cache,
        force_rebuild=force_rebuild,
        timings=timings,
    )
    uniform_error = _build_or_load_stage(
        "theorem_v_uniform_error_law",
        lambda: build_theorem_v_uniform_error_law_certificate(
            explicit_error_certificate=explicit_error,
            final_error_certificate=final_error,
            golden_recurrence_rate_control=golden_rate,
            edge_class_weighted_golden_rate_control=edge_weighted,
            convergent_family_control=convergent,
            runtime_row_certificates=[runtime_row_233_377, runtime_row_377_610],
            min_uniform_chain_length=max(3, int(kwargs.get("tail_cauchy_min_chain_length", 4))),
        ),
        stage_cache_dir=cache_dir,
        use_cache=use_cache,
        force_rebuild=force_rebuild,
        timings=timings,
    )
    branch_identification = _build_or_load_stage(
        "theorem_v_branch_identification",
        lambda: build_theorem_v_branch_identification_certificate(
            lower_side_certificate=lower,
            upper_tail_certificate=upper_tail,
            final_transport_bridge=final_error,
            theorem_iv_certificate=theorem_iv_certificate,
            convergent_family_control=convergent,
            golden_recurrence_rate_control=golden_rate,
            explicit_error_certificate=explicit_error,
            uniform_error_law=uniform_error,
            runtime_row_certificates=[runtime_row_233_377, runtime_row_377_610],
        ),
        stage_cache_dir=cache_dir,
        use_cache=use_cache,
        force_rebuild=force_rebuild,
        timings=timings,
    )
    final_transport_bridge = _build_or_load_stage(
        "theorem_v_final_transport_bridge",
        lambda: build_final_transport_bridge_certificate(
            final_error,
            theorem_iv_certificate=theorem_iv_certificate,
            upper_tail=upper_tail,
            uniform_error_law=uniform_error,
            branch_identification=branch_identification,
        ),
        stage_cache_dir=cache_dir,
        use_cache=use_cache,
        force_rebuild=force_rebuild,
        timings=timings,
    )

    certificate = _build_or_load_stage(
        "theorem_v_front",
        lambda: build_golden_rational_to_irrational_convergence_certificate(
            base_K_values=base_K_values,
            family=family,
            rho=rho,
            theorem_iv_certificate=theorem_iv_certificate,
            lower_side_certificate=lower,
            upper_side_certificate=upper,
            upper_tail_stability_certificate=upper_tail,
            convergence_control_certificate=convergence,
            branch_certified_control_certificate=branch,
            nested_subladder_control_certificate=nested,
            convergent_family_control_certificate=convergent,
            transport_certified_control_certificate=transport,
            pairwise_transport_control_certificate=pairwise,
            triple_transport_cocycle_control_certificate=triple,
            global_transport_potential_control_certificate=global_potential,
            tail_cauchy_potential_control_certificate=tail_cauchy,
            certified_tail_modulus_control_certificate=certified_modulus,
            rate_aware_tail_modulus_control_certificate=rate_modulus,
            golden_recurrence_rate_control_certificate=golden_rate,
            transport_slope_weighted_golden_rate_control_certificate=transport_weighted,
            edge_class_weighted_golden_rate_control_certificate=edge_weighted,
            theorem_v_explicit_error_control_certificate=explicit_error,
            theorem_v_final_error_control_certificate=final_error,
            theorem_v_uniform_error_law_certificate=uniform_error,
            theorem_v_branch_identification_certificate=branch_identification,
            runtime_row_233_377_certificate=runtime_row_233_377,
            runtime_row_377_610_certificate=runtime_row_377_610,
            final_transport_bridge_certificate=final_transport_bridge,
            **kwargs,
        ),
        stage_cache_dir=cache_dir,
        use_cache=use_cache,
        force_rebuild=force_rebuild,
        timings=timings,
    )
    return {
        "certificate": certificate,
        "stage_timings": timings,
        "stage_cache_dir": str(cache_dir),
    }


def build_golden_theorem_v_certificate_batched(
    base_K_values,
    family: HarmonicFamily | None = None,
    *,
    rho: float | None = None,
    theorem_iii_certificate: Mapping[str, Any] | None = None,
    theorem_iv_certificate: Mapping[str, Any] | None = None,
    use_cache: bool = True,
    force_rebuild: bool = False,
    stage_cache_dir: str | Path | None = None,
    **kwargs,
) -> dict[str, Any]:
    front_bundle = build_golden_rational_to_irrational_convergence_certificate_batched(
        base_K_values=base_K_values,
        family=family,
        rho=rho,
        theorem_iv_certificate=theorem_iv_certificate,
        use_cache=use_cache,
        force_rebuild=force_rebuild,
        stage_cache_dir=stage_cache_dir,
        **kwargs,
    )
    cache_dir = Path(front_bundle["stage_cache_dir"])
    timings = dict(front_bundle.get("stage_timings") or {})
    family = family or HarmonicFamily()
    rho = float(golden_inverse() if rho is None else rho)
    theorem_v = _build_or_load_stage(
        "theorem_v_lift",
        lambda: build_golden_theorem_v_transport_lift_certificate(
            base_K_values=base_K_values,
            family=family,
            rho=rho,
            theorem_iv_certificate=theorem_iv_certificate,
            convergence_front_certificate=front_bundle["certificate"],
            **_filter_kwargs(build_golden_theorem_v_transport_lift_certificate, kwargs),
        ),
        stage_cache_dir=cache_dir,
        use_cache=use_cache,
        force_rebuild=force_rebuild,
        timings=timings,
    )
    theorem_v_compressed = _build_or_load_stage(
        "theorem_v_compressed",
        lambda: build_golden_theorem_v_compressed_lift_certificate(
            base_K_values=base_K_values,
            family=family,
            rho=rho,
            theorem_iii_certificate=theorem_iii_certificate,
            theorem_iv_certificate=theorem_iv_certificate,
            theorem_v_certificate=theorem_v,
            convergence_front_certificate=front_bundle["certificate"],
            **_filter_kwargs(build_golden_theorem_v_compressed_lift_certificate, kwargs),
        ),
        stage_cache_dir=cache_dir,
        use_cache=use_cache,
        force_rebuild=force_rebuild,
        timings=timings,
    )
    return {
        "certificate": theorem_v,
        "compressed_certificate": theorem_v_compressed,
        "downstream_certificate": theorem_v_compressed,
        "convergence_front": front_bundle["certificate"],
        "stage_timings": timings,
        "stage_cache_dir": str(cache_dir),
    }


__all__ = [
    "build_golden_rational_to_irrational_convergence_certificate_batched",
    "build_golden_theorem_v_certificate_batched",
]

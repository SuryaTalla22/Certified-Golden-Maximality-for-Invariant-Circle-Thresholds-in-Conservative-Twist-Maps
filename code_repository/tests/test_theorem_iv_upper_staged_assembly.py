from kam_theorem_suite.adaptive_incompatibility import (
    build_adaptive_incompatibility_atlas_certificate_from_entries,
    build_golden_adaptive_incompatibility_certificate_from_atlas,
)
from kam_theorem_suite.adaptive_tail_coherence import build_golden_adaptive_tail_coherence_certificate_from_entries
from kam_theorem_suite.standard_map import HarmonicFamily


def _entry(label, q, lo, hi, blo, bhi):
    return {
        "p": 1,
        "q": q,
        "label": label,
        "crossing_window_input_lo": lo,
        "crossing_window_input_hi": hi,
        "band_search_lo": blo,
        "band_search_hi": bhi,
        "adaptive_crossing": {"status": "interval_newton"},
        "localized_crossing_source": "adaptive-interval-newton",
        "crossing_root_window_lo": lo,
        "crossing_root_window_hi": hi,
        "crossing_root_window_width": hi - lo,
        "band_report": {"longest_band_lo": blo, "longest_band_hi": bhi},
        "hyperbolic_band_lo": blo,
        "hyperbolic_band_hi": bhi,
        "hyperbolic_band_width": bhi - blo,
        "gap_from_crossing_to_band": blo - hi,
        "status": "adaptive-crossing-plus-band",
        "notes": "stub",
    }


def test_upper_staged_assembly_helpers_close_simple_case():
    family = HarmonicFamily()
    atlas = build_adaptive_incompatibility_atlas_certificate_from_entries(
        [_entry("1/8", 8, 0.90, 0.91, 0.95, 0.97), _entry("2/13", 13, 0.905, 0.912, 0.952, 0.969)],
        family=family,
        min_tail_members=2,
    )
    golden = build_golden_adaptive_incompatibility_certificate_from_atlas(
        atlas,
        family=family,
        rho=0.618,
        generated_convergents=[{"q": 8}, {"q": 13}],
    )
    assert golden.theorem_status in {"golden-adaptive-incompatibility-strong", "golden-adaptive-incompatibility-moderate"}

    coherence = build_golden_adaptive_tail_coherence_certificate_from_entries(
        [
            {
                "atlas_shift": -0.0003,
                "crossing_center": 0.97,
                "theorem_status": golden.theorem_status,
                "selected_upper_lo": golden.selected_upper_lo,
                "selected_upper_hi": golden.selected_upper_hi,
                "selected_barrier_lo": golden.selected_barrier_lo,
                "selected_barrier_hi": golden.selected_barrier_hi,
                "incompatibility_gap": golden.incompatibility_gap,
                "witness_qs": [8, 13],
                "exact_tail_qs": [8, 13],
                "generated_qs": [8, 13],
                "report": golden.to_dict(),
            },
            {
                "atlas_shift": 0.0003,
                "crossing_center": 0.971,
                "theorem_status": golden.theorem_status,
                "selected_upper_lo": golden.selected_upper_lo,
                "selected_upper_hi": golden.selected_upper_hi,
                "selected_barrier_lo": golden.selected_barrier_lo,
                "selected_barrier_hi": golden.selected_barrier_hi,
                "incompatibility_gap": golden.incompatibility_gap,
                "witness_qs": [8, 13],
                "exact_tail_qs": [8, 13],
                "generated_qs": [8, 13],
                "report": golden.to_dict(),
            },
        ],
        family=family,
        rho=0.618,
        min_cluster_size=2,
        min_tail_members=2,
    )
    assert coherence.theorem_status in {
        "golden-adaptive-tail-coherence-strong",
        "golden-adaptive-tail-coherence-moderate",
    }

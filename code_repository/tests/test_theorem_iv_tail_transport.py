from __future__ import annotations

from kam_theorem_suite.obstruction_atlas import ApproximantWindowSpec
from kam_theorem_suite.theorem_iv_tail_transport import (
    build_golden_tail_band_transport_certificate,
    build_pairwise_band_transport_certificate,
    extract_tail_band_anchor,
    make_tail_transport_entry_dicts,
)


def _anchor_entry(p, q, label, cross_lo, cross_hi, band_lo, band_hi, margin):
    width = band_hi - band_lo
    return {
        'p': p,
        'q': q,
        'label': label,
        'crossing_root_window_lo': cross_lo,
        'crossing_root_window_hi': cross_hi,
        'hyperbolic_band_lo': band_lo,
        'hyperbolic_band_hi': band_hi,
        'gap_from_crossing_to_band': band_lo - cross_hi,
        'adaptive_crossing': {'status': 'theorem_mode_local'},
        'band_report': {
            'certified_band_count': 1,
            'best_band': {
                'K_lo': band_lo,
                'K_hi': band_hi,
                'width': width,
                'g_interval_lo': margin,
                'g_interval_hi': margin + 0.1,
                'hyperbolicity_margin': margin + 1.0,
            },
        },
    }


def test_pairwise_band_transport_certificate_strong():
    left = extract_tail_band_anchor(_anchor_entry(21, 34, 'g2134', 0.97, 0.971, 1.03180, 1.03210, 0.6))
    right = extract_tail_band_anchor(_anchor_entry(34, 55, 'g3455', 0.9705, 0.9711, 1.03178, 1.03202, 0.7))
    cert = build_pairwise_band_transport_certificate(left, right)
    assert cert.transport_status == 'pairwise-band-transport-strong'
    assert cert.center_drift < cert.width_floor


def test_tail_transport_certificate_builds_strong(monkeypatch):
    anchors = [
        _anchor_entry(21, 34, 'g2134', 0.97035, 0.97050, 1.03150, 1.03180, 0.6),
        _anchor_entry(34, 55, 'g3455', 0.97036, 0.97049, 1.03152, 1.03172, 0.8),
        _anchor_entry(55, 89, 'g5589', 0.97037, 0.97048, 1.03154, 1.03164, 1.2),
    ]
    specs = [
        ApproximantWindowSpec(89, 144, 0.968, 0.973, 1.026, 1.056, 'g89144'),
        ApproximantWindowSpec(144, 233, 0.968, 0.973, 1.026, 1.056, 'g144233'),
    ]

    calls = []

    def fake_localize(spec, **kwargs):
        calls.append(int(spec.q))
        center = 1.03135 if int(spec.q) == 144 else 1.03130
        half_width = 5.0e-5 if int(spec.q) == 144 else 4.0e-5
        cert = {
            'K_lo': center - half_width,
            'K_hi': center + half_width,
            'proof_ready': True,
            'g_interval_lo': 0.9,
            'g_interval_hi': 1.1,
            'hyperbolicity_margin': 5.0,
            'method': 'transport_local_band',
            'message': 'mock transport-local-band success',
        }
        return {
            'proof_ready': True,
            'predictive_center': center,
            'prediction_source': 'mock fit',
            'certificate': cert,
        }

    monkeypatch.setattr(
        'kam_theorem_suite.theorem_iv_tail_transport.methodology_localize_hyperbolic_band',
        fake_localize,
    )

    cert = build_golden_tail_band_transport_certificate(anchors, specs, explicit_tail_cutoff_q=89)
    data = cert.to_dict()
    assert data['theorem_status'] == 'golden-theorem-iv-tail-transport-strong'
    assert data['all_replacement_rows_proof_ready'] is True
    assert data['all_replacement_rows_above_anchor_upper'] is True
    assert data['replacement_qs'] == [144, 233]
    assert calls == [144, 233]

    entry_dicts = make_tail_transport_entry_dicts(cert, specs)
    assert len(entry_dicts) == 2
    assert all(e['status'] == 'tail-transport-derived' for e in entry_dicts)
    assert all(e['gap_from_crossing_to_band'] > 0.0 for e in entry_dicts)



def _accepted_window_only_anchor_entry(p, q, label, cross_lo, cross_hi, band_lo, band_hi, margin):
    width = band_hi - band_lo
    return {
        'p': p,
        'q': q,
        'label': label,
        'crossing_root_window_lo': cross_lo,
        'crossing_root_window_hi': cross_hi,
        'hyperbolic_band_lo': band_lo,
        'hyperbolic_band_hi': band_hi,
        'gap_from_crossing_to_band': band_lo - cross_hi,
        'adaptive_crossing': {
            'status': 'theorem_mode_local',
            'methodology_frontend': {'proof_ready': True},
        },
        'band_report': {
            'certified_band_count': 1,
            'best_band': {
                'K_lo': band_lo,
                'K_hi': band_hi,
                'width': width,
            },
            'accepted_windows': [
                {
                    'K_lo': band_lo,
                    'K_hi': band_hi,
                    'g_interval_lo': margin,
                    'g_interval_hi': margin + 0.1,
                    'hyperbolicity_margin': margin + 2.0,
                    'proof_ready': True,
                }
            ],
        },
    }


def test_extract_tail_band_anchor_uses_accepted_window_certificate_geometry():
    anchor = extract_tail_band_anchor(
        _accepted_window_only_anchor_entry(13, 21, 'g1321', 0.9702, 0.9703, 1.0321, 1.0329, 0.75)
    )
    assert anchor.band_center == 0.5 * (1.0321 + 1.0329)
    assert anchor.band_half_width == 0.5 * (1.0329 - 1.0321)
    assert anchor.band_margin == 0.75


def test_tail_transport_uses_anchor_envelope_even_without_crossing_intersection(monkeypatch):
    anchors = [
        _accepted_window_only_anchor_entry(13, 21, 'g1321', 0.97010, 0.97020, 1.03210, 1.03290, 0.8),
        _accepted_window_only_anchor_entry(21, 34, 'g2134', 0.97110, 0.97120, 1.03380, 1.03420, 1.2),
        _accepted_window_only_anchor_entry(34, 55, 'g3455', 0.97210, 0.97220, 1.03520, 1.03550, 1.4),
        _accepted_window_only_anchor_entry(55, 89, 'g5589', 0.97310, 0.97320, 1.03630, 1.03640, 1.8),
    ]
    specs = [
        ApproximantWindowSpec(89, 144, 0.968, 0.975, 1.026, 1.056, 'g89144'),
    ]

    def fake_localize(spec, **kwargs):
        assert abs(kwargs['crossing_root_hi'] - 0.97320) < 1e-12
        return {
            'proof_ready': True,
            'certificate': {
                'K_lo': 1.03645,
                'K_hi': 1.03655,
                'proof_ready': True,
                'g_interval_lo': 0.9,
                'g_interval_hi': 1.1,
                'hyperbolicity_margin': 4.0,
            },
        }

    monkeypatch.setattr(
        'kam_theorem_suite.theorem_iv_tail_transport.methodology_localize_hyperbolic_band',
        fake_localize,
    )

    cert = build_golden_tail_band_transport_certificate(anchors, specs, explicit_tail_cutoff_q=89)
    data = cert.to_dict()
    assert data['theorem_status'] == 'golden-theorem-iv-tail-transport-strong'
    assert abs(data['anchor_upper_hi'] - 0.97320) < 1e-12
    assert data['anchor_tail_summary']['theorem_status'] == 'anchor-upper-envelope-strong'
    assert data['all_replacement_rows_above_anchor_upper'] is True

import os
import sys
from pprint import pprint

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from kam_theorem_suite.adaptive_incompatibility import build_adaptive_incompatibility_atlas_certificate
from kam_theorem_suite.obstruction_atlas import ApproximantWindowSpec

specs = [
    ApproximantWindowSpec(3, 5, 0.95, 0.99, 1.02, 1.05, label="3/5"),
    ApproximantWindowSpec(5, 8, 0.95, 0.99, 1.02, 1.05, label="5/8"),
]

cert = build_adaptive_incompatibility_atlas_certificate(
    specs,
    crossing_max_depth=5,
    crossing_min_width=5e-4,
    band_initial_subdivisions=1,
    band_max_depth=3,
    band_min_width=1e-3,
    min_tail_members=1,
)

payload = cert.to_dict()
pprint(
    {
        "theorem_status": payload["theorem_status"],
        "interval_newton_count": payload["interval_newton_count"],
        "fully_certified_count": payload["fully_certified_count"],
        "coherent_upper": (payload["coherent_upper_lo"], payload["coherent_upper_hi"]),
        "coherent_band": (payload["coherent_band_lo"], payload["coherent_band_hi"]),
        "incompatibility_gap": payload["incompatibility_gap"],
        "entry_statuses": [(e["label"], e["adaptive_crossing"]["status"], e["status"]) for e in payload["entries"]],
    }
)

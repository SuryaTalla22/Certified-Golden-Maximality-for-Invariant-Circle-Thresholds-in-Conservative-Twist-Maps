from __future__ import annotations

"""Phase-9 reviewer-facing proof-audit notebook helpers.

The repository intentionally keeps these notebooks lightweight.  They do not
rerun expensive Theorem-IV or near-critical lower solves; instead they read the
proof-carrying audit payloads produced by Phases 2--8, recompute/check the
visible margins, and write small summary JSON files.  The notebooks are meant
for a skeptical referee who wants a guided tour of the audit artifacts without
having to inspect every module first.

No third-party notebook library is required.  The helpers below write valid
``.ipynb`` JSON directly and execute notebook code cells with ordinary Python
``exec`` for CI/preflight testing.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence
import contextlib
import io
import json
import os
import traceback


@dataclass(frozen=True)
class ProofAuditNotebookSpec:
    filename: str
    title: str
    purpose: str
    summary_filename: str


EXPECTED_NOTEBOOKS: tuple[ProofAuditNotebookSpec, ...] = (
    ProofAuditNotebookSpec(
        "00_audit_index_and_environment.ipynb",
        "Proof-Audit Index and Environment",
        "Check that the repository contains the Phase-2--8 audit payloads and summarize their status.",
        "00_audit_index_and_environment_summary.json",
    ),
    ProofAuditNotebookSpec(
        "01_lower_corridor_chain_audit.ipynb",
        "Lower-Corridor Chain Audit",
        "Inspect the lower-corridor proof-carrying chain and record the current known final-anchor gap.",
        "01_lower_corridor_chain_summary.json",
    ),
    ProofAuditNotebookSpec(
        "02_upper_obstruction_margin_audit.ipynb",
        "Upper Obstruction and Analytic-Incompatibility Margin Audit",
        "Inspect the upper obstruction margin ledger and verify the positive analytic-incompatibility margin.",
        "02_upper_obstruction_margin_summary.json",
    ),
    ProofAuditNotebookSpec(
        "03_transport_budget_audit.ipynb",
        "Transport Budget Audit",
        "Inspect the decomposed transport budget and verify that the charged budget fits below the available gap.",
        "03_transport_budget_summary.json",
    ),
    ProofAuditNotebookSpec(
        "04_arithmetic_domain_exhaustion_audit.ipynb",
        "Arithmetic-Domain Exhaustion Audit",
        "Inspect generated-domain route counts and verify that no generated record is uncontrolled.",
        "04_arithmetic_domain_summary.json",
    ),
    ProofAuditNotebookSpec(
        "05_gl2z_normalization_audit.ipynb",
        "GL(2,Z) Normalization Audit",
        "Inspect representative-selection evidence and verify that no analytic-conjugacy claim is consumed.",
        "05_gl2z_normalization_summary.json",
    ),
    ProofAuditNotebookSpec(
        "06_replay_validator_audit.ipynb",
        "Replay and Hardened Validator Audit",
        "Run the hardened validator in reviewer mode and confirm that strict mode still fails on the known lower gap.",
        "06_replay_validator_summary.json",
    ),
    ProofAuditNotebookSpec(
        "07_reviewer_dashboard.ipynb",
        "Reviewer Dashboard",
        "Collect the Phase-9 notebook summaries into one compact reviewer-facing dashboard.",
        "07_reviewer_dashboard_summary.json",
    ),
)


COMMON_PREAMBLE = """from pathlib import Path\nimport csv\nimport json\nimport subprocess\nimport sys\nimport os\n\nROOT = Path.cwd()\nif not (ROOT / 'kam_theorem_suite').exists():\n    raise RuntimeError(f'Run this notebook from the repository root, got {ROOT}')\nAUDIT = ROOT / 'artifacts/proof_audit'\nOUT = AUDIT / 'notebooks'\nOUT.mkdir(parents=True, exist_ok=True)\n\ndef load_json(rel):\n    path = ROOT / rel\n    if not path.exists():\n        raise FileNotFoundError(path)\n    with path.open() as f:\n        return json.load(f)\n\ndef write_summary(name, data):\n    path = OUT / name\n    if os.environ.get('PHASE9_NOTEBOOK_DRY_RUN') != '1':\n        path.write_text(json.dumps(data, indent=2, sort_keys=True) + '\\n')\n    print(json.dumps(data, indent=2, sort_keys=True))\n    return path\n"""


def _md(text: str) -> dict[str, Any]:
    return {"cell_type": "markdown", "metadata": {}, "source": _lines(text)}


def _code(text: str) -> dict[str, Any]:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": _lines(text),
    }


def _lines(text: str) -> list[str]:
    if not text.endswith("\n"):
        text += "\n"
    return text.splitlines(keepends=True)


def _notebook(cells: Sequence[dict[str, Any]]) -> dict[str, Any]:
    return {
        "cells": list(cells),
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "pygments_lexer": "ipython3"},
            "proof_audit_phase": 9,
            "notebook_policy": "reviewer-facing, lightweight, generated from audit JSON/CSV payloads",
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def _header(spec: ProofAuditNotebookSpec) -> str:
    return f"""# {spec.title}\n\n**Purpose.** {spec.purpose}\n\nThese notebooks are reviewer-facing guides over generated proof-audit payloads. They intentionally do not store or regenerate Theorem V-or-above stage-cache artifacts. Each notebook writes a small JSON summary under `artifacts/proof_audit/notebooks/`.\n"""


def _standard_first_cells(spec: ProofAuditNotebookSpec) -> list[dict[str, Any]]:
    return [_md(_header(spec)), _code(COMMON_PREAMBLE)]


def _cells_for(spec: ProofAuditNotebookSpec) -> list[dict[str, Any]]:
    cells = _standard_first_cells(spec)
    name = spec.filename
    if name.startswith("00_"):
        cells += [
            _md("## Audit payload inventory\n\nThis cell checks the Phase-2--8 audit payloads and records their top-level statuses."),
            _code(
                """required = {
    'lower': 'artifacts/proof_audit/lower_corridor/lower_corridor_audit.json',
    'upper': 'artifacts/proof_audit/upper_obstruction/upper_obstruction_audit.json',
    'transport': 'artifacts/proof_audit/transport_budget/transport_budget_audit.json',
    'domain': 'artifacts/proof_audit/arithmetic_domain/arithmetic_domain_audit.json',
    'gl2z': 'artifacts/proof_audit/gl2z_normalization/gl2z_normalization_audit.json',
    'replay': 'artifacts/proof_audit/replay/phase8_hardened_validator_report.json',
}
statuses = {}
missing = []
for key, rel in required.items():
    path = ROOT / rel
    if not path.exists():
        missing.append(rel)
        continue
    data = load_json(rel)
    statuses[key] = data.get('status', data.get('certified'))
assert not missing, missing
summary = {
    'notebook': '00_audit_index_and_environment',
    'repository_root': ROOT.as_posix(),
    'payload_statuses': statuses,
    'known_lower_gap_expected': True,
    'phase9_role': 'index_and_preflight',
}
write_summary('00_audit_index_and_environment_summary.json', summary)
"""
            ),
        ]
    elif name.startswith("01_"):
        cells += [
            _md("## Lower-chain margins and the known final-anchor gap\n\nThis notebook verifies the local extracted lower-chain fields and records that the current artifact still fails closed before the near-critical final anchor."),
            _code(
                """audit = load_json('artifacts/proof_audit/lower_corridor/lower_corridor_audit.json')
segments = audit.get('segments', [])
assert segments, 'lower audit has no segments'
min_segment_margin = min(float(s['radii_margin']) for s in segments)
assert min_segment_margin > 0.0, min_segment_margin
assert audit.get('status') == 'failed', audit.get('status')
assert audit.get('final_anchor_reached') is False
assert 'final_anchor_not_reached' in audit.get('failure_fields', [])
summary = {
    'notebook': '01_lower_corridor_chain_audit',
    'status': audit.get('status'),
    'segment_count': len(segments),
    'min_radii_margin': float(audit.get('min_radii_margin', min_segment_margin)),
    'min_segment_margin_recomputed': min_segment_margin,
    'min_overlap_width': float(audit.get('min_overlap_width', 0.0)),
    'final_anchor': audit.get('final_anchor'),
    'final_anchor_reached': bool(audit.get('final_anchor_reached')),
    'known_lower_gap': 'final_anchor_not_reached' in audit.get('failure_fields', []),
    'failure_fields': audit.get('failure_fields', []),
}
write_summary('01_lower_corridor_chain_summary.json', summary)
"""
            ),
        ]
    elif name.startswith("02_"):
        cells += [
            _md("## Upper obstruction margin ledger\n\nThis cell checks that the analytic-incompatibility margin is positive and no upper-obstruction failure fields remain."),
            _code(
                """audit = load_json('artifacts/proof_audit/upper_obstruction/upper_obstruction_audit.json')
assert audit.get('status') == 'passed', audit.get('status')
assert audit.get('analytic_incompatibility_certified') is True
margin = float(audit['analytic_incompatibility_margin'])
assert margin > 0.0, margin
assert audit.get('failure_fields') == []
summary = {
    'notebook': '02_upper_obstruction_margin_audit',
    'status': audit.get('status'),
    'analytic_incompatibility_margin': margin,
    'gap_minus_upper_width': float(audit.get('gap_minus_upper_width', 0.0)),
    'gap_to_localization_ratio': float(audit.get('gap_to_localization_ratio', 0.0)),
    'tail_qs': audit.get('tail_qs', []),
    'failure_fields': audit.get('failure_fields', []),
}
write_summary('02_upper_obstruction_margin_summary.json', summary)
"""
            ),
        ]
    elif name.startswith("03_"):
        cells += [
            _md("## Transport budget derivation\n\nThis cell recomputes the transport budget charge from its displayed components and verifies that the remaining margin is positive."),
            _code(
                """audit = load_json('artifacts/proof_audit/transport_budget/transport_budget_audit.json')
assert audit.get('status') == 'passed', audit.get('status')
components = audit.get('components', [])
assert components, 'missing transport components'
component_sum = sum(float(c.get('charged', c.get('value', 0.0))) for c in components)
# The audit may include outward-rounding conventions; tolerate tiny representation differences.
assert abs(component_sum - float(audit['total_charged'])) < 1e-15, (component_sum, audit['total_charged'])
remaining = float(audit['remaining_margin'])
assert remaining > 0.0, remaining
assert float(audit['total_charged']) < float(audit['available_gap'])
summary = {
    'notebook': '03_transport_budget_audit',
    'status': audit.get('status'),
    'component_count': len(components),
    'available_gap': float(audit['available_gap']),
    'total_charged': float(audit['total_charged']),
    'component_sum_recomputed': component_sum,
    'remaining_margin': remaining,
    'margin_ratio': float(audit.get('margin_ratio', 0.0)),
    'failure_fields': audit.get('failure_fields', []),
}
write_summary('03_transport_budget_summary.json', summary)
"""
            ),
        ]
    elif name.startswith("04_"):
        cells += [
            _md("## Arithmetic generated-domain exhaustion\n\nThis cell summarizes the generated records and route counts, confirming that no generated record is uncontrolled."),
            _code(
                """audit = load_json('artifacts/proof_audit/arithmetic_domain/arithmetic_domain_audit.json')
assert audit.get('status') == 'passed', audit.get('status')
records = audit.get('records', [])
assert records, 'domain audit has no records'
assert int(audit.get('uncontrolled_count', -1)) == 0
assert audit.get('failure_fields') == []
route_counts = audit.get('route_counts', {})
summary = {
    'notebook': '04_arithmetic_domain_exhaustion_audit',
    'status': audit.get('status'),
    'generated_record_count': len(records),
    'uncontrolled_count': int(audit.get('uncontrolled_count', 0)),
    'route_counts': route_counts,
    'omitted_tail_status': audit.get('omitted_tail_status'),
    'failure_fields_empty': bool(audit.get('failure_fields_empty')),
}
write_summary('04_arithmetic_domain_summary.json', summary)
"""
            ),
        ]
    elif name.startswith("05_"):
        cells += [
            _md("## GL(2,Z) representative-selection audit\n\nThis cell checks that the normalization audit is a representative-selection convention and does not assert analytic conjugacy outside the certified normalization domain."),
            _code(
                """audit = load_json('artifacts/proof_audit/gl2z_normalization/gl2z_normalization_audit.json')
assert audit.get('status') == 'passed', audit.get('status')
assert audit.get('normalization_type') == 'representative_selection'
assert audit.get('analytic_conjugacy_claimed') is False
assert int(audit.get('accepted_distinct_representative_count', -1)) == 1
assert int(audit.get('duplicate_golden_representative_count', -1)) == 0
assert audit.get('failure_fields') == []
summary = {
    'notebook': '05_gl2z_normalization_audit',
    'status': audit.get('status'),
    'candidate_count': int(audit.get('candidate_count', 0)),
    'accepted_matrix_witness_count': int(audit.get('accepted_matrix_witness_count', 0)),
    'accepted_distinct_representative_count': int(audit.get('accepted_distinct_representative_count', 0)),
    'duplicate_golden_representative_count': int(audit.get('duplicate_golden_representative_count', 0)),
    'analytic_conjugacy_claimed': bool(audit.get('analytic_conjugacy_claimed')),
    'failure_fields': audit.get('failure_fields', []),
}
write_summary('05_gl2z_normalization_summary.json', summary)
"""
            ),
        ]
    elif name.startswith("06_"):
        cells += [
            _md("## Hardened validator reviewer-mode check\n\nReviewer mode allows the known Phase-2 lower-anchor gap while still hardening every other theorem-facing payload. Strict mode must continue to fail until the near-critical lower-corridor artifact is supplied."),
            _code(
                """from kam_theorem_suite.audit.proof_payload_validator import validate_proof_audit_bundle

reviewer_report = validate_proof_audit_bundle(AUDIT, allow_known_lower_gap=True)
reviewer_path = OUT / 'validator_reviewer_mode_report.json'

if os.environ.get('PHASE9_NOTEBOOK_DRY_RUN') != '1':
    reviewer_path.write_text(json.dumps(reviewer_report, indent=2, sort_keys=True) + '\\n')
assert reviewer_report.get('status') == 'passed-with-known-lower-gap', reviewer_report
strict_report = validate_proof_audit_bundle(AUDIT, allow_known_lower_gap=False)
strict_path = OUT / 'validator_strict_mode_report.json'

if os.environ.get('PHASE9_NOTEBOOK_DRY_RUN') != '1':
    strict_path.write_text(json.dumps(strict_report, indent=2, sort_keys=True) + '\\n')
assert strict_report.get('status') == 'failed', 'strict mode should fail until final lower anchor is reached'
summary = {
    'notebook': '06_replay_validator_audit',
    'reviewer_mode_status': reviewer_report.get('status'),
    'reviewer_mode_failure_count': int(reviewer_report.get('failure_count', 0)),
    'strict_mode_status': strict_report.get('status'),
    'strict_mode_failure_count': int(strict_report.get('failure_count', 0)),
    'strict_final_ready': bool(reviewer_report.get('strict_final_ready')),
    'known_lower_gap': bool(reviewer_report.get('known_lower_gap')),
}
write_summary('06_replay_validator_summary.json', summary)
"""
            ),
        ]
    elif name.startswith("07_"):
        cells += [
            _md("## Reviewer dashboard\n\nThis cell collects the notebook summaries into one dashboard JSON. Run notebooks 00--06 before this notebook."),
            _code(
                """summary_names = [
    '00_audit_index_and_environment_summary.json',
    '01_lower_corridor_chain_summary.json',
    '02_upper_obstruction_margin_summary.json',
    '03_transport_budget_summary.json',
    '04_arithmetic_domain_summary.json',
    '05_gl2z_normalization_summary.json',
    '06_replay_validator_summary.json',
]
summaries = {}
missing = []
for name in summary_names:
    path = OUT / name
    if not path.exists():
        missing.append(name)
    else:
        summaries[name] = json.loads(path.read_text())
assert not missing, missing
all_nonlower_layers_passed = all([
    summaries['02_upper_obstruction_margin_summary.json']['status'] == 'passed',
    summaries['03_transport_budget_summary.json']['status'] == 'passed',
    summaries['04_arithmetic_domain_summary.json']['status'] == 'passed',
    summaries['05_gl2z_normalization_summary.json']['status'] == 'passed',
    summaries['06_replay_validator_summary.json']['reviewer_mode_status'] == 'passed-with-known-lower-gap',
])
dashboard = {
    'notebook': '07_reviewer_dashboard',
    'phase9_status': 'passed-with-known-lower-gap' if all_nonlower_layers_passed else 'failed',
    'strict_final_ready': False,
    'known_lower_gap': True,
    'all_nonlower_layers_passed': all_nonlower_layers_passed,
    'summary_files': summary_names,
    'next_mathematical_blocker': 'supply/regenerate near-critical lower-corridor final-anchor proof payload',
}
write_summary('07_reviewer_dashboard_summary.json', dashboard)
"""
            ),
        ]
    else:
        raise KeyError(name)
    return cells


def write_proof_audit_notebooks(
    *,
    repository_root: str | Path = ".",
    notebook_dir: str | Path = "notebooks/proof_audit",
    overwrite: bool = True,
) -> dict[str, Any]:
    root = Path(repository_root).resolve()
    out_dir = (root / notebook_dir).resolve() if not Path(notebook_dir).is_absolute() else Path(notebook_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[dict[str, Any]] = []
    for spec in EXPECTED_NOTEBOOKS:
        path = out_dir / spec.filename
        if path.exists() and not overwrite:
            action = "skipped"
        else:
            nb = _notebook(_cells_for(spec))
            path.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n")
            action = "written"
        written.append(
            {
                "filename": spec.filename,
                "path": path.relative_to(root).as_posix() if path.is_relative_to(root) else path.as_posix(),
                "title": spec.title,
                "purpose": spec.purpose,
                "summary_filename": spec.summary_filename,
                "action": action,
            }
        )
    inventory = {
        "schema": "phase9_proof_audit_notebook_inventory_v1",
        "notebook_count": len(written),
        "notebooks": written,
        "policy": "lightweight reviewer-facing notebooks generated from audit JSON/CSV payloads",
        "known_lower_gap_expected": True,
    }
    inv_path = out_dir / "NOTEBOOK_INVENTORY.json"
    inv_path.write_text(json.dumps(inventory, indent=2, sort_keys=True) + "\n")
    return inventory


def load_notebook(path: str | Path) -> dict[str, Any]:
    data = json.loads(Path(path).read_text())
    if data.get("nbformat") != 4 or "cells" not in data:
        raise ValueError(f"not a valid nbformat-v4 notebook: {path}")
    return data


def notebook_code_cells(path: str | Path) -> list[str]:
    nb = load_notebook(path)
    cells = []
    for cell in nb.get("cells", []):
        if cell.get("cell_type") == "code":
            src = cell.get("source", "")
            if isinstance(src, list):
                src = "".join(src)
            cells.append(str(src))
    return cells


def execute_notebook_code_cells(path: str | Path, *, repository_root: str | Path = ".") -> dict[str, Any]:
    """Execute code cells from a generated notebook as a CI preflight.

    This is intentionally stricter and simpler than an interactive Jupyter run:
    cells are executed sequentially in one namespace, from the repository root,
    and any exception fails the notebook.  The function captures stdout/stderr so
    the report can be committed without bloating the notebooks themselves.
    """

    nb_path = Path(path).resolve()
    root = Path(repository_root).resolve()
    ns: dict[str, Any] = {"__name__": "__phase9_proof_audit_notebook__"}
    stdout_buffer = io.StringIO()
    stderr_buffer = io.StringIO()
    old_cwd = Path.cwd()
    code_cells = notebook_code_cells(nb_path)
    try:
        os.chdir(root)
        with contextlib.redirect_stdout(stdout_buffer), contextlib.redirect_stderr(stderr_buffer):
            for index, source in enumerate(code_cells):
                compiled = compile(source, f"{nb_path.name}:cell{index}", "exec")
                exec(compiled, ns, ns)
        status = "passed"
        error = None
    except Exception as exc:  # pragma: no cover - exercised by negative test
        status = "failed"
        error = {"type": type(exc).__name__, "message": str(exc), "traceback": traceback.format_exc()[-4000:]}
    finally:
        os.chdir(old_cwd)
    return {
        "notebook": nb_path.name,
        "path": nb_path.as_posix(),
        "status": status,
        "code_cell_count": len(code_cells),
        "stdout_tail": stdout_buffer.getvalue()[-4000:],
        "stderr_tail": stderr_buffer.getvalue()[-4000:],
        "error": error,
    }


def execute_proof_audit_notebooks(
    *,
    repository_root: str | Path = ".",
    notebook_dir: str | Path = "notebooks/proof_audit",
    out_path: str | Path = "artifacts/proof_audit/notebooks/phase9_notebook_execution_report.json",
) -> dict[str, Any]:
    root = Path(repository_root).resolve()
    nb_dir = (root / notebook_dir).resolve() if not Path(notebook_dir).is_absolute() else Path(notebook_dir).resolve()
    results = []
    for spec in EXPECTED_NOTEBOOKS:
        path = nb_dir / spec.filename
        if not path.exists():
            results.append({"notebook": spec.filename, "path": path.as_posix(), "status": "missing", "error": {"message": "notebook missing"}})
            continue
        results.append(execute_notebook_code_cells(path, repository_root=root))
    failed = [r for r in results if r.get("status") != "passed"]
    report = {
        "schema": "phase9_proof_audit_notebook_execution_v1",
        "status": "passed" if not failed else "failed",
        "notebook_count": len(results),
        "failed_count": len(failed),
        "known_lower_gap_expected": True,
        "results": results,
    }
    out = (root / out_path).resolve() if not Path(out_path).is_absolute() else Path(out_path).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return report


def validate_proof_audit_notebook_inventory(
    *,
    repository_root: str | Path = ".",
    notebook_dir: str | Path = "notebooks/proof_audit",
) -> list[str]:
    root = Path(repository_root).resolve()
    nb_dir = (root / notebook_dir).resolve() if not Path(notebook_dir).is_absolute() else Path(notebook_dir).resolve()
    failures: list[str] = []
    for spec in EXPECTED_NOTEBOOKS:
        path = nb_dir / spec.filename
        if not path.exists():
            failures.append(f"missing notebook: {spec.filename}")
            continue
        try:
            nb = load_notebook(path)
        except Exception as exc:
            failures.append(f"invalid notebook {spec.filename}: {exc}")
            continue
        if not any(cell.get("cell_type") == "markdown" for cell in nb.get("cells", [])):
            failures.append(f"notebook has no markdown cells: {spec.filename}")
        if not any(cell.get("cell_type") == "code" for cell in nb.get("cells", [])):
            failures.append(f"notebook has no code cells: {spec.filename}")
        text = json.dumps(nb)
        forbidden_paths = [
            "artifacts/final_discharge/stage_cache/theorem_v",
            "artifacts/final_discharge/stage_cache/theorem_vi",
            "artifacts/final_discharge/stage_cache/theorem_vii",
            "artifacts/final_discharge/stage_cache/theorem_viii",
            "artifacts/final_discharge/stage_cache/stage108",
        ]
        for forbidden in forbidden_paths:
            if forbidden in text.lower():
                failures.append(f"notebook references forbidden stored downstream artifact path {forbidden}: {spec.filename}")
    return failures

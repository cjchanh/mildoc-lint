"""CLI entrypoint smoke tests.

These tests verify that the renamed `mildoc-lint` entrypoint works and that
the CLI reports its version and help correctly.
"""
from __future__ import annotations

import io
from contextlib import redirect_stderr, redirect_stdout

import pytest

from cds_mildoc import __version__
from cds_mildoc.cli import build_parser, main


def test_parser_prog_name_is_mildoc_lint() -> None:
    parser = build_parser()
    assert parser.prog == "mildoc-lint"


def test_version_string_reports_mildoc_lint() -> None:
    parser = build_parser()
    buf = io.StringIO()
    with pytest.raises(SystemExit) as excinfo:
        with redirect_stdout(buf), redirect_stderr(buf):
            parser.parse_args(["--version"])
    assert excinfo.value.code == 0
    assert f"mildoc-lint {__version__}" in buf.getvalue()


def test_lint_examples_runs_without_crash(tmp_path) -> None:
    out = tmp_path / "out.json"
    rc = main(["lint", "examples", "--profile", "all", "--format", "json", "--out", str(out)])
    assert rc in (0, 1), f"unexpected exit code {rc}"
    assert out.exists() and out.stat().st_size > 0


def test_lint_accepts_multiple_paths(tmp_path) -> None:
    """Multiple file paths aggregate into one result (enables the pre-commit hook)."""
    import json

    out = tmp_path / "multi.json"
    rc = main(
        [
            "lint",
            "examples/good_training_opord.md",
            "examples/bad_cui_order.md",
            "--profile",
            "all",
            "--format",
            "json",
            "--out",
            str(out),
        ]
    )
    assert rc in (0, 1)
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["documents_scanned"] == 2
    # result.path stays a single valid path, never a joined display string
    assert "," not in (data["path"] or "")


def test_json_report_is_stable_without_runtime_timestamp(tmp_path) -> None:
    out1 = tmp_path / "out1.json"
    out2 = tmp_path / "out2.json"
    args = ["lint", "examples/good_training_opord.md", "--profile", "all", "--format", "json"]
    assert main([*args, "--out", str(out1)]) in (0, 1)
    assert main([*args, "--out", str(out2)]) in (0, 1)
    assert out1.read_text(encoding="utf-8") == out2.read_text(encoding="utf-8")


def test_lint_accepts_rule_pack_overlay(tmp_path) -> None:
    import json

    doc = tmp_path / "pii.md"
    overlay = tmp_path / "unit.yaml"
    out = tmp_path / "out.json"
    doc.write_text("Marine: Synthetic Example SSN 123-45-6789\n", encoding="utf-8")
    overlay.write_text(
        """- rule_id: pii.ssn
  severity: warn
  profile: pii
  source:
    title: "Unit Privacy Review SOP"
    url: "https://example.invalid/unit-privacy-review"
    retrieved_at_utc: "2026-06-20T00:00:00Z"
  testimony: "Unit overlay changes only local severity for exposed SSN review."
  fail_closed: true
""",
        encoding="utf-8",
    )

    rc = main(
        [
            "lint",
            str(doc),
            "--profile",
            "pii",
            "--rule-pack",
            str(overlay),
            "--fail-on",
            "error",
            "--format",
            "json",
            "--out",
            str(out),
        ]
    )

    assert rc == 0
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["findings"][0]["rule_id"] == "pii.ssn"
    assert data["findings"][0]["severity"] == "warn"

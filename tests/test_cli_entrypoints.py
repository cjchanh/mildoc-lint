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


def test_json_report_is_stable_without_runtime_timestamp(tmp_path) -> None:
    out1 = tmp_path / "out1.json"
    out2 = tmp_path / "out2.json"
    args = ["lint", "examples/good_training_opord.md", "--profile", "all", "--format", "json"]
    assert main([*args, "--out", str(out1)]) in (0, 1)
    assert main([*args, "--out", str(out2)]) in (0, 1)
    assert out1.read_text(encoding="utf-8") == out2.read_text(encoding="utf-8")

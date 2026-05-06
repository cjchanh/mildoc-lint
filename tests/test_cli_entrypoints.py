"""CLI entrypoint smoke tests.

These tests verify that the renamed `mildoc-lint` entrypoint works and that
the CLI reports its version and help correctly.
"""
from __future__ import annotations

import io
from contextlib import redirect_stderr, redirect_stdout

import pytest

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
    assert "mildoc-lint 0.1.0" in buf.getvalue()


def test_lint_examples_runs_without_crash(tmp_path) -> None:
    out = tmp_path / "out.json"
    rc = main(["lint", "examples", "--profile", "all", "--format", "json", "--out", str(out)])
    assert rc in (0, 1), f"unexpected exit code {rc}"
    assert out.exists() and out.stat().st_size > 0

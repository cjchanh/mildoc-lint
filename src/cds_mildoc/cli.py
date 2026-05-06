from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .engine import PROFILE_ALIASES, lint_path
from .models import Severity
from .references import AUTHORITIES
from .reporters import exit_code, render_json, render_sarif, render_text
from .templates import TEMPLATES, render_template


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mildoc-lint",
        description="Local-first linter for CUI markings, PII indicators, O-SMEAC orders, naval correspondence, and NAMP/CSEC records.",
    )
    parser.add_argument("--version", action="version", version="mildoc-lint 0.1.0")
    sub = parser.add_subparsers(dest="command", required=True)

    lint = sub.add_parser("lint", help="lint one document or a directory of documents")
    lint.add_argument("path", help="file or directory to scan")
    lint.add_argument(
        "--profile",
        default="default",
        help="profile: " + ", ".join(sorted(PROFILE_ALIASES)) + " or comma list of cui,pii,osmeac,naval,namp",
    )
    lint.add_argument("--no-recursive", action="store_true", help="do not recurse through directories")
    lint.add_argument("--format", choices=["text", "json", "sarif"], default="text", help="output format")
    lint.add_argument("--out", help="write output to file")
    lint.add_argument("--fail-on", default="error", help="exit nonzero on severity: info, warn, error, blocker")

    new = sub.add_parser("new", help="print a document skeleton")
    new.add_argument("template", choices=sorted(TEMPLATES), help="template name")
    new.add_argument("--out", help="write template to file")

    namp = sub.add_parser("namp", help="NAMP/CSEC convenience commands")
    namp_sub = namp.add_subparsers(dest="namp_command", required=True)
    namp_check = namp_sub.add_parser("check", help="scan a NAMP/CSEC folder or record")
    namp_check.add_argument("path", help="file or directory to scan")
    namp_check.add_argument("--format", choices=["text", "json", "sarif"], default="text")
    namp_check.add_argument("--out")
    namp_check.add_argument("--fail-on", default="warn")

    rules = sub.add_parser("rules", help="print built-in public rule authorities")
    rules.add_argument("--format", choices=["text", "json"], default="text")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "lint":
            result = lint_path(args.path, profile=args.profile, recursive=not args.no_recursive)
            rendered = _render_result(result, args.format)
            _emit(rendered, args.out)
            return exit_code(result, Severity.parse(args.fail_on))

        if args.command == "new":
            rendered = render_template(args.template)
            _emit(rendered, args.out)
            return 0

        if args.command == "namp" and args.namp_command == "check":
            result = lint_path(args.path, profile="namp", recursive=True)
            rendered = _render_result(result, args.format)
            _emit(rendered, args.out)
            return exit_code(result, Severity.parse(args.fail_on))

        if args.command == "rules":
            if args.format == "json":
                import json

                _emit(json.dumps(AUTHORITIES, indent=2, sort_keys=True), None)
            else:
                lines = ["Built-in public authorities:"]
                for key, ref in sorted(AUTHORITIES.items()):
                    lines.append(f"- {key}: {ref['title']} ({ref['url']})")
                _emit("\n".join(lines), None)
            return 0

    except Exception as exc:
        print(f"mildoc-lint: {exc}", file=sys.stderr)
        return 2

    parser.print_help()
    return 2


def _render_result(result, fmt: str) -> str:
    if fmt == "json":
        return render_json(result)
    if fmt == "sarif":
        return render_sarif(result)
    return render_text(result)


def _emit(rendered: str, out: str | None) -> None:
    if out:
        Path(out).write_text(rendered + ("" if rendered.endswith("\n") else "\n"), encoding="utf-8")
    else:
        print(rendered)

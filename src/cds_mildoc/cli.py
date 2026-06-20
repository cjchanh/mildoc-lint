from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from ._version import __version__
from .archivist import (
    diff_documents,
    ingest_document,
    init_db,
    lint_with_receipt,
    status_for,
)
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
    parser.add_argument("--version", action="version", version=f"mildoc-lint {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    lint = sub.add_parser("lint", help="lint one or more documents or directories")
    lint.add_argument("paths", nargs="+", metavar="path", help="one or more files or directories to scan")
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

    archivist = sub.add_parser("archivist", help="local receipt and provenance ledger")
    arch_sub = archivist.add_subparsers(dest="arch_command", required=True)

    arch_init = arch_sub.add_parser("init", help="initialize the local Archivist database")
    arch_init.add_argument("--db-path", help="override default .mildoc/archivist.sqlite3 location")

    arch_ingest = arch_sub.add_parser("ingest", help="record a document in the ledger")
    arch_ingest.add_argument("path")
    arch_ingest.add_argument("--profile", default="mildoc")
    arch_ingest.add_argument("--case", default="default")
    arch_ingest.add_argument("--db-path")
    arch_ingest.add_argument("--format", choices=["text", "json"], default="text")

    arch_lint = arch_sub.add_parser("lint", help="lint a document and emit a receipt")
    arch_lint.add_argument("path")
    arch_lint.add_argument("--profile", default="mildoc")
    arch_lint.add_argument("--write-receipt", action="store_true")
    arch_lint.add_argument("--db-path")
    arch_lint.add_argument("--format", choices=["text", "json"], default="text")

    arch_status = arch_sub.add_parser("status", help="show last receipt for a document")
    arch_status.add_argument("path")
    arch_status.add_argument("--db-path")
    arch_status.add_argument("--format", choices=["text", "json"], default="text")

    arch_gate = arch_sub.add_parser("gate", help="fail-closed gate based on receipt + findings")
    arch_gate.add_argument("path")
    arch_gate.add_argument("--profile", default="mildoc")
    arch_gate.add_argument("--require-pass", action="store_true")
    arch_gate.add_argument("--require-sources", action="store_true")
    arch_gate.add_argument("--require-no-pii", action="store_true")
    arch_gate.add_argument("--db-path")
    arch_gate.add_argument("--format", choices=["text", "json"], default="text")

    arch_diff = arch_sub.add_parser("diff", help="compare last receipts of two documents")
    arch_diff.add_argument("old_path")
    arch_diff.add_argument("new_path")
    arch_diff.add_argument("--db-path")
    arch_diff.add_argument("--format", choices=["text", "json"], default="text")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "lint":
            result = lint_path(args.paths[0], profile=args.profile, recursive=not args.no_recursive)
            for extra in args.paths[1:]:
                result.extend(lint_path(extra, profile=args.profile, recursive=not args.no_recursive))
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
                _emit(json.dumps(AUTHORITIES, indent=2, sort_keys=True), None)
            else:
                lines = ["Built-in public authorities:"]
                for key, ref in sorted(AUTHORITIES.items()):
                    lines.append(f"- {key}: {ref['title']} ({ref['url']})")
                _emit("\n".join(lines), None)
            return 0

        if args.command == "archivist":
            return _archivist_dispatch(args)

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


def _resolve_db_path(arg: str | None) -> Path | None:
    return Path(arg).expanduser().resolve() if arg else None


def _archivist_dispatch(args: argparse.Namespace) -> int:
    db_path = _resolve_db_path(getattr(args, "db_path", None))
    fmt = getattr(args, "format", "text")

    if args.arch_command == "init":
        path = init_db(db_path)
        msg = {"status": "ok", "db_path": str(path)}
        _emit(json.dumps(msg) if fmt == "json" else f"archivist: db initialized at {path}", None)
        return 0

    if args.arch_command == "ingest":
        info = ingest_document(args.path, profile=args.profile, case=args.case, db_path=db_path)
        if fmt == "json":
            _emit(json.dumps(info, sort_keys=True), None)
        else:
            _emit(
                f"archivist: ingested {info['path']}\n"
                f"  document_sha256={info['document_sha256']}\n"
                f"  profile={info['profile']} case={info['case']}",
                None,
            )
        return 0

    if args.arch_command == "lint":
        result = lint_with_receipt(
            args.path,
            profile=args.profile,
            write=args.write_receipt,
            db_path=db_path,
        )
        if fmt == "json":
            _emit(json.dumps(result["receipt"], sort_keys=True), None)
        else:
            r = result["receipt"]
            _emit(
                f"archivist: receipt {r['receipt_sha256']}\n"
                f"  decision={r['decision']} findings={result['findings_count']}\n"
                f"  document_sha256={r['document_sha256']}\n"
                f"  rule_pack_sha256={r['rule_pack_sha256']}\n"
                f"  written={'yes' if args.write_receipt else 'no'}",
                None,
            )
        return 1 if result["decision"] == "BLOCKED" else 0

    if args.arch_command == "status":
        info = status_for(args.path, db_path=db_path)
        if fmt == "json":
            _emit(json.dumps(info, sort_keys=True, default=str), None)
        else:
            if info["has_receipt"]:
                last = info["last_receipt"]
                _emit(
                    f"archivist: status for {info['path']}\n"
                    f"  document_sha256={info['document_sha256']}\n"
                    f"  last_decision={last.get('decision')}\n"
                    f"  last_receipt_sha256={last.get('receipt_sha256')}\n"
                    f"  last_created_at_utc={last.get('created_at_utc')}",
                    None,
                )
            else:
                _emit(
                    f"archivist: status for {info['path']}\n"
                    f"  document_sha256={info['document_sha256']}\n"
                    f"  last_decision=NONE (no prior receipt)",
                    None,
                )
        return 0

    if args.arch_command == "gate":
        result = lint_with_receipt(
            args.path,
            profile=args.profile,
            write=False,
            require_pass=args.require_pass,
            require_sources=args.require_sources,
            require_no_pii=args.require_no_pii,
            db_path=db_path,
        )
        if fmt == "json":
            _emit(json.dumps(result["receipt"], sort_keys=True), None)
        else:
            r = result["receipt"]
            _emit(
                f"archivist: gate decision={r['decision']} findings={result['findings_count']}",
                None,
            )
        return 1 if result["decision"] == "BLOCKED" else 0

    if args.arch_command == "diff":
        info = diff_documents(args.old_path, args.new_path, db_path=db_path)
        if fmt == "json":
            _emit(json.dumps(info, sort_keys=True, default=str), None)
        else:
            _emit(
                f"archivist: diff\n"
                f"  old_sha={info['old']['document_sha256']} new_sha={info['new']['document_sha256']}\n"
                f"  sha_changed={info['sha_changed']}\n"
                f"  decision: {info['old_decision']} -> {info['new_decision']}",
                None,
            )
        return 0

    print(f"mildoc-lint: unknown archivist command: {args.arch_command}", file=sys.stderr)
    return 2

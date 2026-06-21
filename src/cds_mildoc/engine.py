from __future__ import annotations

from pathlib import Path
from typing import Sequence

from .models import Document, Finding, LintResult, Severity
from .packs import RulePackCatalog, load_rule_packs
from .parsers import ParserError, iter_paths, load_document
from .rules import cui, namp, naval, osmeac, pii

PROFILE_ALIASES = {
    "all": ["cui", "pii", "osmeac", "naval", "namp"],
    "default": ["cui", "pii", "osmeac", "naval"],
    "mildoc": ["cui", "pii", "osmeac", "naval", "namp"],
    "maildoc": ["cui", "pii", "naval"],
    "cui": ["cui", "pii"],
    "pii": ["pii"],
    "osmeac": ["osmeac"],
    "orders": ["osmeac", "cui", "pii"],
    "naval": ["naval", "cui", "pii"],
    "namp": ["namp", "cui", "pii"],
    "csec": ["namp", "cui", "pii"],
}


def expand_profile(profile: str) -> list[str]:
    key = profile.lower().strip()
    if key in PROFILE_ALIASES:
        return PROFILE_ALIASES[key]
    pieces = [p.strip().lower() for p in key.split(",") if p.strip()]
    unknown = [p for p in pieces if p not in {"cui", "pii", "osmeac", "naval", "namp"}]
    if unknown:
        raise ValueError(f"unknown profile(s): {', '.join(unknown)}")
    return pieces or PROFILE_ALIASES["default"]


def lint_document(
    doc: Document,
    profile: str = "default",
    rule_packs: Sequence[str | Path] | None = None,
) -> list[Finding]:
    catalog = load_rule_packs(rule_packs)
    checks = expand_profile(profile)
    findings: list[Finding] = []
    if "pii" in checks:
        findings.extend(pii.check(doc))
    if "cui" in checks:
        findings.extend(cui.check(doc))
    if "osmeac" in checks:
        findings.extend(osmeac.check(doc, forced=(profile.lower() in {"osmeac", "orders", "all"})))
    if "naval" in checks:
        findings.extend(naval.check(doc, forced=(profile.lower() in {"naval", "all", "maildoc"})))
    if "namp" in checks:
        findings.extend(namp.check(doc, forced=(profile.lower() in {"namp", "csec", "all"})))

    for finding in findings:
        if finding.path is None:
            finding.path = doc.path
    _apply_pack_metadata(findings, catalog)
    return sorted(findings, key=_finding_sort_key)


def lint_path(
    path: str | Path,
    profile: str = "default",
    recursive: bool = True,
    rule_packs: Sequence[str | Path] | None = None,
) -> LintResult:
    paths = iter_paths(path, recursive=recursive)
    aggregate = LintResult(path=str(path), findings=[], documents_scanned=0)
    if not paths:
        aggregate.findings.append(
            Finding(
                rule_id="parser.no_supported_files",
                severity=Severity.WARN,
                message="No supported files found. Supported: txt, md, rst, docx, pdf with optional dependency.",
                path=str(path),
                recommendation="Pass a file path or a directory containing supported document files.",
            )
        )
        return aggregate

    for p in paths:
        try:
            doc = load_document(p)
        except ParserError as exc:
            aggregate.findings.append(
                Finding(
                    rule_id="parser.error",
                    severity=Severity.ERROR,
                    message=str(exc),
                    path=str(p),
                    recommendation="Install optional parser dependencies or convert the document to text/Markdown/DOCX.",
                )
            )
            aggregate.documents_scanned += 1
            continue
        aggregate.findings.extend(lint_document(doc, profile=profile, rule_packs=rule_packs))
        aggregate.documents_scanned += 1

    aggregate.findings.sort(key=_finding_sort_key)
    return aggregate


def _apply_pack_metadata(findings: list[Finding], catalog: RulePackCatalog) -> None:
    for finding in findings:
        record = catalog.require(finding.rule_id)
        finding.severity = record.severity
        finding.source = record.source_text
        finding.testimony = record.testimony


def _finding_sort_key(f: Finding) -> tuple[int, str, int, str]:
    return (-int(f.severity), f.path or "", f.line or 0, f.rule_id)

from __future__ import annotations

import re

from cds_mildoc.models import Document, Finding, Severity
from cds_mildoc.references import source

from .util import first_matching_line, likely_heading, normalized_lines, redact_sensitive

INVALID_BANNER_RE = re.compile(
    r"^\s*(?:U\s*//\s*CUI|UNCLASSIFIED\s*//\s*CUI|CUI\s*//\s*[A-Z0-9/ -]+|CONTROLLED|CONTROLLED\s+UNCLASSIFIED\s+INFORMATION)\s*$",
    re.IGNORECASE,
)
CUI_BANNER_RE = re.compile(r"^\s*CUI\s*$", re.IGNORECASE)
DI_CONTROLLED_BY_RE = re.compile(r"^\s*Controlled\s+by\s*:", re.IGNORECASE)
DI_CATEGORY_RE = re.compile(r"^\s*(?:CUI\s+)?Categor(?:y|ies)\s*:", re.IGNORECASE)
DI_LDC_RE = re.compile(r"^\s*(?:LDC|Limited\s+Dissemination\s+Control|Distribution\s+Statement)\s*:", re.IGNORECASE)
DI_POC_RE = re.compile(r"^\s*POC\s*:", re.IGNORECASE)
PORTION_RE = re.compile(r"^\s*\((?:U|CUI|CUI//[A-Z0-9, -]+|[A-Z]{2,8})\)\s+")
LEGACY_RE = re.compile(r"\b(?:FOUO|For Official Use Only|SBU|Sensitive But Unclassified)\b", re.IGNORECASE)


def check(doc: Document) -> list[Finding]:
    findings: list[Finding] = []
    lines = doc.lines
    text_lower = doc.text.lower()

    cui_context = _has_cui_context(doc)

    for i, line in enumerate(lines, start=1):
        if INVALID_BANNER_RE.match(line):
            findings.append(
                Finding(
                    rule_id="cui.invalid_banner",
                    severity=Severity.ERROR,
                    message="Invalid or legacy CUI banner form detected.",
                    line=i,
                    column=1,
                    snippet=line.strip(),
                    recommendation='Use standalone "CUI" for the banner/footer. Put categories and dissemination controls in the designation indicator block.',
                    source=source("DOD_CUI_MARKING_2024"),
                    tags=["cui", "marking"],
                )
            )

    for match in LEGACY_RE.finditer(doc.text):
        line_no = doc.text[: match.start()].count("\n") + 1
        findings.append(
            Finding(
                rule_id="cui.legacy_marking",
                severity=Severity.WARN,
                message="Legacy/supplemental control marking detected.",
                line=line_no,
                column=1,
                snippet=redact_sensitive(lines[line_no - 1] if line_no - 1 < len(lines) else match.group(0)),
                recommendation="Review whether current CUI marking is required; do not rely on legacy labels as the control scheme.",
                source=source("DODI_5200_48"),
                tags=["cui", "marking"],
            )
        )

    if not cui_context:
        return findings

    findings.extend(_check_banners(doc))
    findings.extend(_check_designation_indicator(doc))
    findings.extend(_check_portion_consistency(doc))

    if "unclassified//cui" in text_lower or "u//cui" in text_lower:
        first = first_matching_line(lines, r"(?:unclassified\s*//\s*cui|u\s*//\s*cui)")
        findings.append(
            Finding(
                rule_id="cui.do_not_prefix_unclassified",
                severity=Severity.ERROR,
                message='DoD CUI guidance says not to add "UNCLASSIFIED" before "CUI" in the banner.',
                line=first[0] if first else None,
                snippet=first[1].strip() if first else None,
                recommendation='Change the banner/footer to standalone "CUI" and keep category/dissemination data in the DI block.',
                source=source("DOD_CUI_MARKING_2024"),
                tags=["cui", "marking"],
            )
        )

    return findings


def _has_cui_context(doc: Document) -> bool:
    lower = doc.text.lower()
    triggers = [
        "controlled by:",
        "cui category",
        "cui categories",
        "limited dissemination control",
        "controlled unclassified information",
        "//cui",
    ]
    if any(t in lower for t in triggers):
        return True
    exact_cui_lines = sum(1 for _, line in normalized_lines(doc) if CUI_BANNER_RE.match(line))
    return exact_cui_lines > 0


def _check_banners(doc: Document) -> list[Finding]:
    findings: list[Finding] = []
    pages = doc.pages()
    for page_num, (start_line, page_lines) in enumerate(pages, start=1):
        significant = [(idx, line.strip()) for idx, line in enumerate(page_lines, start=start_line) if line.strip()]
        if not significant:
            continue
        top_window = significant[:6]
        bottom_window = significant[-6:]
        top_ok = any(CUI_BANNER_RE.match(line) for _, line in top_window)
        bottom_ok = any(CUI_BANNER_RE.match(line) for _, line in bottom_window)
        if not top_ok:
            findings.append(
                Finding(
                    rule_id="cui.missing_top_banner",
                    severity=Severity.ERROR,
                    message=f'Missing standalone "CUI" top banner on logical page {page_num}.',
                    line=significant[0][0],
                    column=1,
                    snippet=significant[0][1],
                    recommendation='Place standalone "CUI" at the top of each page/logical page containing CUI.',
                    source=source("DOD_CUI_MARKING_2024"),
                    tags=["cui", "marking"],
                )
            )
        if not bottom_ok:
            findings.append(
                Finding(
                    rule_id="cui.missing_bottom_banner",
                    severity=Severity.ERROR,
                    message=f'Missing standalone "CUI" bottom/footer banner on logical page {page_num}.',
                    line=significant[-1][0],
                    column=1,
                    snippet=significant[-1][1],
                    recommendation='Place standalone "CUI" at the bottom/footer of each page/logical page containing CUI.',
                    source=source("DOD_CUI_MARKING_2024"),
                    tags=["cui", "marking"],
                )
            )
    return findings


def _check_designation_indicator(doc: Document) -> list[Finding]:
    findings: list[Finding] = []
    lines = doc.lines
    has_controlled_by = any(DI_CONTROLLED_BY_RE.match(line) for line in lines)
    has_category = any(DI_CATEGORY_RE.match(line) for line in lines)
    has_ldc = any(DI_LDC_RE.match(line) for line in lines)
    has_poc = any(DI_POC_RE.match(line) for line in lines)

    if not has_controlled_by and not has_category and not has_ldc and not has_poc:
        findings.append(
            Finding(
                rule_id="cui.missing_designation_indicator",
                severity=Severity.ERROR,
                message="Missing CUI designation indicator block.",
                line=1,
                column=1,
                recommendation="Add a DI block with Controlled by, CUI Category, LDC or Distribution Statement, and POC.",
                source=source("DOD_CUI_DI_BLOCK"),
                tags=["cui", "marking"],
            )
        )
        return findings

    checks = [
        (has_controlled_by, "cui.di_missing_controlled_by", "Missing DI block line: Controlled by:"),
        (has_category, "cui.di_missing_category", "Missing DI block line: CUI Category:"),
        (has_ldc, "cui.di_missing_ldc_or_distribution", "Missing DI block line: LDC: or Distribution Statement:"),
        (has_poc, "cui.di_missing_poc", "Missing DI block line: POC:"),
    ]
    anchor = _first_di_line(lines)
    for ok, rule_id, message in checks:
        if not ok:
            findings.append(
                Finding(
                    rule_id=rule_id,
                    severity=Severity.ERROR,
                    message=message,
                    line=anchor,
                    column=1,
                    recommendation="Complete the CUI designation indicator block on the first/title page.",
                    source=source("DOD_CUI_DI_BLOCK"),
                    tags=["cui", "marking"],
                )
            )
    return findings


def _first_di_line(lines: list[str]) -> int:
    for idx, line in enumerate(lines, start=1):
        if any(regex.match(line) for regex in (DI_CONTROLLED_BY_RE, DI_CATEGORY_RE, DI_LDC_RE, DI_POC_RE)):
            return idx
    return 1


def _check_portion_consistency(doc: Document) -> list[Finding]:
    lines = doc.lines
    has_portions = any(PORTION_RE.match(line) for line in lines)
    if not has_portions:
        return [
            Finding(
                rule_id="cui.portion_marking_recommended",
                severity=Severity.INFO,
                message="No portion markings detected. They are optional for unclassified DoD CUI documents but recommended by DoD training guidance.",
                line=1,
                recommendation="For higher-assurance drafts, portion mark titles, subjects, paragraphs, bullets, figures, charts, and tables consistently.",
                source=source("DOD_CUI_MARKING_2024"),
                tags=["cui", "marking"],
            )
        ]

    findings: list[Finding] = []
    for idx, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped or CUI_BANNER_RE.match(stripped) or likely_heading(stripped):
            continue
        if any(regex.match(stripped) for regex in (DI_CONTROLLED_BY_RE, DI_CATEGORY_RE, DI_LDC_RE, DI_POC_RE)):
            continue
        if PORTION_RE.match(stripped):
            continue
        if len(stripped) > 40 and re.match(r"^(?:\d+\.|[a-z]\.|\-|\*)?\s*[A-Za-z0-9]", stripped):
            findings.append(
                Finding(
                    rule_id="cui.inconsistent_portion_marking",
                    severity=Severity.WARN,
                    message="Some portion markings exist, but this content line appears unmarked.",
                    line=idx,
                    column=1,
                    snippet=redact_sensitive(stripped[:160]),
                    recommendation="If portion markings are used, apply them to all required portions consistently.",
                    source=source("DOD_CUI_MARKING_2024"),
                    tags=["cui", "marking"],
                )
            )
            if len(findings) >= 10:
                break
    return findings

from __future__ import annotations

import re

from cds_mildoc.models import Document, Finding, Severity
from cds_mildoc.references import source

from .util import line_number_for_match, redact_sensitive

SSN_RE = re.compile(r"(?<!\d)(?!000|666|9\d\d)(\d{3})[- ]?(?!00)(\d{2})[- ]?(?!0000)(\d{4})(?!\d)")
EDIPI_CONTEXT_RE = re.compile(
    r"(?i)\b(?:edipi|dod\s*id(?:entification)?\s*(?:number)?|dodid)\b[^\n\r]{0,40}\b\d{10}\b"
)
DOB_RE = re.compile(r"(?i)\b(?:dob|date\s+of\s+birth)\b\s*[:\-]?\s*\d{1,2}[/-]\d{1,2}[/-]\d{2,4}")
PASSPORT_RE = re.compile(r"(?i)\bpassport\s*(?:no\.?|number|#)?\s*[:\-]?\s*[A-Z0-9]{6,9}\b")
BANK_RE = re.compile(r"(?i)\b(?:routing\s+number|account\s+number)\b\s*[:\-]?\s*[0-9 -]{6,20}")

CUI_CATEGORY_HINTS = {
    r"\bexport[- ]controlled\b": "export-control language",
    r"\bitar\b": "ITAR language",
    r"\bear99\b": "EAR language",
    r"\bcti\b": "controlled technical information acronym",
    r"\bcontrolled technical information\b": "controlled technical information",
    r"\bopsec\b": "OPSEC language",
    r"\bnnpi\b": "naval nuclear propulsion information acronym",
    r"\bproprietary\b": "proprietary information language",
}


def check(doc: Document) -> list[Finding]:
    findings: list[Finding] = []
    findings.extend(_regex_findings(doc, SSN_RE, "pii.ssn", "Possible SSN detected.", Severity.ERROR))
    findings.extend(_regex_findings(doc, EDIPI_CONTEXT_RE, "pii.edipi", "Possible EDIPI/DoD ID detected.", Severity.WARN))
    findings.extend(_regex_findings(doc, DOB_RE, "pii.dob", "Possible date-of-birth field detected.", Severity.WARN))
    findings.extend(_regex_findings(doc, PASSPORT_RE, "pii.passport", "Possible passport number detected.", Severity.WARN))
    findings.extend(_regex_findings(doc, BANK_RE, "pii.financial", "Possible financial account field detected.", Severity.WARN))

    lower = doc.text.lower()
    has_cui_marking = "cui" in lower or "controlled by:" in lower or "cui category" in lower
    if not has_cui_marking:
        for pattern, label in CUI_CATEGORY_HINTS.items():
            match = re.search(pattern, doc.text, re.IGNORECASE)
            if match:
                line, col = line_number_for_match(doc.text, match.start())
                findings.append(
                    Finding(
                        rule_id="cui.possible_unmarked_category",
                        severity=Severity.WARN,
                        message=f"Possible CUI category indicator without visible CUI marking: {label}.",
                        line=line,
                        column=col,
                        snippet=redact_sensitive(doc.lines[line - 1] if line - 1 < len(doc.lines) else match.group(0)),
                        recommendation="Review the source authority and mark/control the document if the content qualifies as CUI.",
                        source=source("DODI_5200_48"),
                        tags=["cui", "pii"],
                    )
                )
                break
    return findings


def _regex_findings(doc: Document, regex: re.Pattern[str], rule_id: str, message: str, severity: Severity) -> list[Finding]:
    findings: list[Finding] = []
    for match in regex.finditer(doc.text):
        line, col = line_number_for_match(doc.text, match.start())
        line_text = doc.lines[line - 1] if line - 1 < len(doc.lines) else match.group(0)
        findings.append(
            Finding(
                rule_id=rule_id,
                severity=severity,
                message=message,
                line=line,
                column=col,
                snippet=redact_sensitive(line_text),
                recommendation="Remove, redact, or confirm proper authorization, marking, and handling before distribution.",
                source=source("NIST_800_171R3"),
                tags=["pii", "cui"],
            )
        )
    return findings

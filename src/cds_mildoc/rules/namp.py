from __future__ import annotations

import re

from cds_mildoc.models import Document, Finding, Severity
from cds_mildoc.references import source

NAMP_EXPLICIT_RE = re.compile(r"\b(?:NAMP|CSEC|COMNAVAIRFORINST\s*4790\.2|OOMA|NALCOMIS)\b", re.IGNORECASE)
NAMP_HINT_RE = re.compile(
    r"\b(?:maintenance|QA|quality assurance|audit|discrepanc(?:y|ies)|work center|FOD|tool control|MALS)\b",
    re.IGNORECASE,
)
DATE_RE = re.compile(r"\b(?:\d{4}-\d{2}-\d{2}|\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{1,2}\s+(?:JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)\s+\d{2,4})\b", re.IGNORECASE)

FIELD_PATTERNS = {
    "reference": re.compile(r"\b(?:ref(?:erence)?|COMNAVAIRFORINST|NAMP|MCO|SECNAV|local instruction|LOI)\b", re.IGNORECASE),
    "discrepancy": re.compile(r"\b(?:discrepanc(?:y|ies)|deficienc(?:y|ies)|finding|non[- ]?compliance|gap)\b", re.IGNORECASE),
    "corrective_action": re.compile(r"\b(?:corrective action|correction|mitigation|root cause|RCA|fix|remediation)\b", re.IGNORECASE),
    "owner": re.compile(r"\b(?:owner|OPR|responsible|POC|work center|division|branch|shop)\b", re.IGNORECASE),
    "due_date": re.compile(r"\b(?:due|ECD|estimated completion|suspense|completion date|target date)\b", re.IGNORECASE),
    "status": re.compile(r"\b(?:open|closed|in progress|status|complete|completed|verified|accepted)\b", re.IGNORECASE),
    "evidence": re.compile(r"\b(?:evidence|attachment|photo|log|record|screenshot|MDR|work order|QA stamp|signature)\b", re.IGNORECASE),
}


def check(doc: Document, forced: bool = False) -> list[Finding]:
    if not forced and not _likely_namp(doc.text):
        return []

    findings: list[Finding] = []
    text = doc.text
    if not re.search(r"\b(?:NAMP|CSEC|COMNAVAIRFORINST\s*4790\.2)\b", text, re.IGNORECASE):
        findings.append(
            Finding(
                rule_id="namp.reference_absent",
                severity=Severity.WARN,
                message="Maintenance/audit language detected without a visible NAMP/CSEC reference.",
                line=1,
                recommendation="Tie the record to the governing NAMP/CSEC/local checklist reference used for the inspection or discrepancy.",
                source=source("NAVAIR_NAMP_CSEC"),
                tags=["namp", "csec", "readiness"],
            )
        )

    present = {name: bool(regex.search(text)) for name, regex in FIELD_PATTERNS.items()}
    for name, ok in present.items():
        if not ok:
            findings.append(
                Finding(
                    rule_id=f"namp.missing_{name}",
                    severity=Severity.WARN if name in {"evidence", "status"} else Severity.ERROR,
                    message=f"NAMP/CSEC-style record may be missing field: {name.replace('_', ' ')}.",
                    line=1,
                    recommendation="For audit/discrepancy readiness, capture reference, discrepancy, owner, corrective action, due date/status, and evidence.",
                    source=source("NAVAIR_CSEC_HELP"),
                    tags=["namp", "csec", "readiness"],
                )
            )

    if present.get("due_date") and not DATE_RE.search(text):
        findings.append(
            Finding(
                rule_id="namp.due_date_not_parseable",
                severity=Severity.WARN,
                message="Due/suspense language detected, but no parseable date was found.",
                line=1,
                recommendation="Use an unambiguous date format such as YYYY-MM-DD.",
                source=source("NAVAIR_CSEC_HELP"),
                tags=["namp", "csec", "readiness"],
            )
        )

    if len(findings) == 0:
        findings.append(
            Finding(
                rule_id="namp.record_shape_ok",
                severity=Severity.INFO,
                message="NAMP/CSEC-style record includes the baseline fields checked by the open-core linter.",
                line=1,
                source=source("NAVAIR_CSEC_HELP"),
                tags=["namp", "csec", "readiness"],
            )
        )
    return findings


def _likely_namp(text: str) -> bool:
    if NAMP_EXPLICIT_RE.search(text):
        return True
    # Avoid treating ordinary orders with a single "discrepancy" word as maintenance records.
    return len(NAMP_HINT_RE.findall(text)) >= 2

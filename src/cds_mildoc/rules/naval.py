from __future__ import annotations

import re

from cds_mildoc.models import Document, Finding, Severity
from cds_mildoc.references import source

LABEL_RE = re.compile(r"^\s*(From|To|Via|Subj|Ref|Encl)\s*:\s*(.*)$", re.IGNORECASE)
SUBJECT_RE = re.compile(r"^\s*Subj\s*:\s*(.+)$", re.IGNORECASE)


def check(doc: Document, forced: bool = False) -> list[Finding]:
    labels = _labels(doc.lines)
    if not forced and not {"from", "to", "subj"}.intersection(labels):
        return []

    findings: list[Finding] = []
    for required in ["from", "to", "subj"]:
        if required not in labels:
            findings.append(
                Finding(
                    rule_id=f"naval.missing_{required}",
                    severity=Severity.ERROR,
                    message=f"Missing naval correspondence label: {required.title() if required != 'subj' else 'Subj'}:",
                    line=1,
                    recommendation="Use standard naval correspondence line labels: From:, To:, Subj:, and add Via:/Ref:/Encl: as needed.",
                    source=source("SECNAV_5216_5"),
                    tags=["naval", "correspondence"],
                )
            )

    findings.extend(_check_order(labels))
    findings.extend(_check_subject(doc))

    if re.search(r"^\s*Subject\s*:", doc.text, re.IGNORECASE | re.MULTILINE):
        line = _line_of(doc.lines, r"^\s*Subject\s*:")
        findings.append(
            Finding(
                rule_id="naval.subject_label_not_subj",
                severity=Severity.WARN,
                message='Use "Subj:" rather than "Subject:" in naval correspondence.',
                line=line,
                recommendation='Rename the label to "Subj:".',
                source=source("SECNAV_5216_5"),
                tags=["naval", "correspondence"],
            )
        )
    return findings


def _labels(lines: list[str]) -> dict[str, int]:
    out: dict[str, int] = {}
    for idx, line in enumerate(lines, start=1):
        match = LABEL_RE.match(line)
        if match:
            out.setdefault(match.group(1).lower(), idx)
    return out


def _check_order(labels: dict[str, int]) -> list[Finding]:
    findings: list[Finding] = []
    sequence = ["from", "to", "via", "subj", "ref", "encl"]
    present = [(label, labels[label]) for label in sequence if label in labels]
    for (left_label, left_line), (right_label, right_line) in zip(present, present[1:]):
        if left_line > right_line:
            findings.append(
                Finding(
                    rule_id="naval.label_order",
                    severity=Severity.WARN,
                    message=f"Naval correspondence labels appear out of expected order: {left_label.title()} after {right_label.title()}.",
                    line=left_line,
                    recommendation="Order common labels as From, To, Via, Subj, Ref, Encl.",
                    source=source("SECNAV_5216_5"),
                    tags=["naval", "correspondence"],
                )
            )
            break
    return findings


def _check_subject(doc: Document) -> list[Finding]:
    findings: list[Finding] = []
    for idx, line in enumerate(doc.lines, start=1):
        match = SUBJECT_RE.match(line)
        if not match:
            continue
        subject = match.group(1).strip()
        if subject != subject.upper():
            findings.append(
                Finding(
                    rule_id="naval.subject_not_uppercase",
                    severity=Severity.WARN,
                    message="Subj line should normally be all caps.",
                    line=idx,
                    snippet=line.strip(),
                    recommendation="Convert the Subj content to uppercase.",
                    source=source("SECNAV_5216_5"),
                    tags=["naval", "correspondence"],
                )
            )
        if subject.endswith((".", ";", ":", ",")):
            findings.append(
                Finding(
                    rule_id="naval.subject_punctuation",
                    severity=Severity.WARN,
                    message="Subj line appears to end with punctuation.",
                    line=idx,
                    snippet=line.strip(),
                    recommendation="Remove terminal punctuation from the Subj line unless required by a local template.",
                    source=source("SECNAV_5216_5"),
                    tags=["naval", "correspondence"],
                )
            )
    return findings


def _line_of(lines: list[str], pattern: str) -> int:
    regex = re.compile(pattern, re.IGNORECASE)
    for idx, line in enumerate(lines, start=1):
        if regex.search(line):
            return idx
    return 1

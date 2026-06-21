from __future__ import annotations

import re

from cds_mildoc.models import Document, Finding, Severity
from cds_mildoc.references import source

from .util import redact_sensitive

ORDER_HINT_RE = re.compile(r"\b(?:OPORD|OPLAN|WARNORD|WARNO|FRAGORD|FRAGO|O-?SMEAC|SMEAC|operation order|combat order)\b", re.IGNORECASE)

# Optional leading enumerator: a number ("1."), a letter ("a."), or a bullet
# ("-", "*", "•"). Documents are commonly reformatted with bullets instead of
# numbers; section detection must survive that.
_ENUM = r"(?:[-*•]\s+|\d{1,2}\.?\s*|[a-z]\.\s*)?"

SECTION_PATTERNS: dict[str, re.Pattern[str]] = {
    "orientation": re.compile(rf"^\s*{_ENUM}(?:orientation(?:\s+brief)?)\b", re.IGNORECASE),
    "situation": re.compile(rf"^\s*{_ENUM}(?:situation)\b", re.IGNORECASE),
    "mission": re.compile(rf"^\s*{_ENUM}(?:mission)\b", re.IGNORECASE),
    "execution": re.compile(rf"^\s*{_ENUM}(?:execution)\b", re.IGNORECASE),
    "admin_logistics": re.compile(
        rf"^\s*{_ENUM}(?:admin(?:istration)?\s*(?:and|&)\s*logistics|administration\s+and\s+logistics|service\s+and\s+support|sustainment)\b",
        re.IGNORECASE,
    ),
    "command_signal": re.compile(rf"^\s*{_ENUM}(?:command\s*(?:and|&)\s*signals?)\b", re.IGNORECASE),
}

SECTION_DISPLAY = {
    "orientation": "Orientation",
    "situation": "Situation",
    "mission": "Mission",
    "execution": "Execution",
    "admin_logistics": "Administration and Logistics",
    "command_signal": "Command and Signal",
}

MISSION_WHEN_RE = re.compile(r"\b(?:NLT|NET|on order|upon|at \d{3,4}|\d{1,2}\s*(?:JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)|\d{1,2}[/-]\d{1,2})\b", re.IGNORECASE)
MISSION_WHERE_RE = re.compile(r"\b(?:vicinity|vic\.?|grid|objective|OBJ|zone|area|AO|AA|BP|checkpoint|CP|route)\b", re.IGNORECASE)
MISSION_PURPOSE_RE = re.compile(r"\b(?:in order to|IOT|so that|purpose)\b", re.IGNORECASE)
MISSION_TASK_RE = re.compile(r"\b(?:seize(?:s|d|ing)?|secure(?:s|d|ing)?|destroy(?:s|ed|ing)?|disrupt(?:s|ed|ing)?|support(?:s|ed|ing)?|conduct(?:s|ed|ing)?|provide(?:s|d|ing)?|move(?:s|d|ing)?|defend(?:s|ed|ing)?|attack(?:s|ed|ing)?|clear(?:s|ed|ing)?|screen(?:s|ed|ing)?|guard(?:s|ed|ing)?|recon(?:noiter)?(?:s|ed|ing)?|establish(?:es|ed|ing)?|maintain(?:s|ed|ing)?|evacuate(?:s|d|ing)?|inspect(?:s|ed|ing)?|train(?:s|ed|ing)?)\b", re.IGNORECASE)


def check(doc: Document, forced: bool = False) -> list[Finding]:
    if not forced and not ORDER_HINT_RE.search(doc.text):
        return []

    findings: list[Finding] = []
    sections = _find_sections(doc.lines)

    for key in ["situation", "mission", "execution", "admin_logistics", "command_signal"]:
        if key not in sections:
            findings.append(
                Finding(
                    rule_id=f"osmeac.missing_{key}",
                    severity=Severity.ERROR,
                    message=f"Missing O-SMEAC/SMEAC section: {SECTION_DISPLAY[key]}.",
                    line=1,
                    recommendation="Use the five-paragraph order structure: Situation, Mission, Execution, Administration and Logistics, Command and Signal.",
                    source=source("USMC_OSMEAC_FGHT1004"),
                    tags=["orders", "osmeac"],
                )
            )

    if "orientation" not in sections:
        findings.append(
            Finding(
                rule_id="osmeac.orientation_absent",
                severity=Severity.INFO,
                message="No Orientation brief detected. O-SMEAC includes Orientation before SMEAC when required.",
                line=1,
                recommendation="For terrain-dependent or training orders, add a concise orientation before Situation.",
                source=source("USMC_OSMEAC_FGHT1004"),
                tags=["orders", "osmeac"],
            )
        )

    if "mission" in sections:
        findings.extend(_check_mission(doc, sections))
    if "execution" in sections:
        findings.extend(_check_execution(doc, sections))
    if _is_fragord(doc):
        findings.extend(_check_fragord(doc, sections))
    if _is_warnord(doc):
        findings.extend(_check_warnord(doc, sections))

    return findings


def _find_sections(lines: list[str]) -> dict[str, int]:
    sections: dict[str, int] = {}
    for idx, line in enumerate(lines, start=1):
        for key, regex in SECTION_PATTERNS.items():
            if regex.search(line.strip()):
                sections.setdefault(key, idx)
    return sections


def _section_text(doc: Document, sections: dict[str, int], section: str) -> str:
    if section not in sections:
        return ""
    start = sections[section]  # 1-indexed line of the section header
    later = [line for key, line in sections.items() if key != section and line > start]
    end = min(later) if later else len(doc.lines) + 1
    # Include the header line itself: the mission/execution content is commonly
    # written on the same line as the label ("2. Mission. <statement>"). Slicing
    # from `start` (1-indexed) into a 0-indexed list dropped that line, which made
    # the mission/execution heuristics read empty text and fire false positives.
    return "\n".join(doc.lines[start - 1:end - 1]).strip()


def _check_mission(doc: Document, sections: dict[str, int]) -> list[Finding]:
    text = _section_text(doc, sections, "mission")
    # A FRAGORD that defers the mission ("Mission. No change.") is not an
    # incomplete mission statement; do not flag it.
    if re.search(r"\bno\s+changes?\b", text, re.IGNORECASE):
        return []
    line = sections.get("mission", 1)
    findings: list[Finding] = []
    # Search as flowing text: word-wrap can split a multi-word cue ("in order\nto")
    # across a line break, which would otherwise defeat the phrase patterns.
    flat = re.sub(r"\s+", " ", text)
    checks = [
        (MISSION_TASK_RE.search(flat), "task/action verb"),
        (MISSION_WHEN_RE.search(flat), "when/timing cue"),
        (MISSION_WHERE_RE.search(flat), "where/location cue"),
        (MISSION_PURPOSE_RE.search(flat), "why/purpose cue"),
    ]
    missing = [name for ok, name in checks if not ok]
    if missing:
        findings.append(
            Finding(
                rule_id="osmeac.mission_incomplete_heuristic",
                severity=Severity.WARN,
                message="Mission statement may be incomplete; missing heuristic cues: " + ", ".join(missing) + ".",
                line=line,
                snippet=redact_sensitive(text.splitlines()[0][:180]) if text else None,
                recommendation="Tighten Mission around who, what, when, where, and why/purpose. Prefer one clear sentence.",
                source=source("USMC_OSMEAC_FGHT1004"),
                tags=["orders", "osmeac"],
            )
        )
    if len([ln for ln in text.splitlines() if ln.strip()]) > 4:
        findings.append(
            Finding(
                rule_id="osmeac.mission_too_long",
                severity=Severity.WARN,
                message="Mission section appears long for a mission statement.",
                line=line,
                recommendation="Compress the mission statement; move details to Execution or Admin/Logistics.",
                source=source("USMC_OSMEAC_FGHT1004"),
                tags=["orders", "osmeac"],
            )
        )
    return findings


def _check_execution(doc: Document, sections: dict[str, int]) -> list[Finding]:
    text = _section_text(doc, sections, "execution")
    line = sections.get("execution", 1)
    lowered = re.sub(r"\s+", " ", text).lower()
    expected = [
        ("commander", "commander's intent"),
        ("concept", "concept of operations"),
        ("task", "tasks to subordinate units"),
        ("coordinating", "coordinating instructions"),
    ]
    missing = [label for token, label in expected if token not in lowered]
    if not missing:
        return []
    return [
        Finding(
            rule_id="osmeac.execution_missing_common_subelements",
            severity=Severity.WARN,
            message="Execution section may be missing common subelements: " + ", ".join(missing) + ".",
            line=line,
            recommendation="Add only subelements needed to make subordinate action clear and coordinated.",
            source=source("USMC_OSMEAC_FGHT1004"),
            tags=["orders", "osmeac"],
        )
    ]


def _is_fragord(doc: Document) -> bool:
    return bool(re.search(r"\b(?:FRAGORD|FRAGO|fragmentary order)\b", doc.text, re.IGNORECASE))


def _is_warnord(doc: Document) -> bool:
    return bool(re.search(r"\b(?:WARNORD|WARNO|warning order)\b", doc.text, re.IGNORECASE))


def _check_fragord(doc: Document, sections: dict[str, int]) -> list[Finding]:
    findings: list[Finding] = []
    if not re.search(r"\b(?:base order|base opord|to\s+opord|references?|ref:)\b", doc.text, re.IGNORECASE):
        findings.append(
            Finding(
                rule_id="osmeac.fragord_missing_base_order",
                severity=Severity.ERROR,
                message="FRAGORD/FRAGO detected without a visible base order/reference.",
                line=1,
                recommendation="Identify the base order or reference being modified.",
                source=source("USMC_COMBAT_ORDERS_FOUNDATIONS"),
                tags=["orders", "fragord"],
            )
        )
    missing_sections = [key for key in ["situation", "mission", "execution", "admin_logistics", "command_signal"] if key not in sections]
    if missing_sections and not re.search(r"\bno\s+change(?:s)?\b", doc.text, re.IGNORECASE):
        findings.append(
            Finding(
                rule_id="osmeac.fragord_no_change_absent",
                severity=Severity.WARN,
                message="FRAGORD omits sections without visible 'No change' language.",
                line=1,
                recommendation="For unchanged sections, state the section name and 'No changes' to reduce ambiguity.",
                source=source("USMC_COMBAT_ORDERS_FOUNDATIONS"),
                tags=["orders", "fragord"],
            )
        )
    return findings


def _check_warnord(doc: Document, sections: dict[str, int]) -> list[Finding]:
    findings: list[Finding] = []
    if not re.search(r"\b(?:timeline|time line|schedule|backbrief|rehearsal|inspection|PCC|PCI)\b", doc.text, re.IGNORECASE):
        findings.append(
            Finding(
                rule_id="osmeac.warnord_prep_time_missing",
                severity=Severity.INFO,
                message="WARNORD detected without visible preparation timeline/PCC/PCI/rehearsal cues.",
                line=1,
                recommendation="A WARNORD should maximize subordinate preparation time; include known timeline/prep events when available.",
                source=source("USMC_COMBAT_ORDERS_FOUNDATIONS"),
                tags=["orders", "warnord"],
            )
        )
    if "mission" not in sections and "execution" not in sections:
        findings.append(
            Finding(
                rule_id="osmeac.warnord_too_sparse",
                severity=Severity.WARN,
                message="WARNORD appears too sparse: no Mission or Execution section detected.",
                line=1,
                recommendation="Publish early, but include the pertinent higher-order information already known.",
                source=source("USMC_COMBAT_ORDERS_FOUNDATIONS"),
                tags=["orders", "warnord"],
            )
        )
    return findings

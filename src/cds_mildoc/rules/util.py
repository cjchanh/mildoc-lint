from __future__ import annotations

import re
from collections.abc import Iterable

from cds_mildoc.models import Document


def line_number_for_match(text: str, start: int) -> tuple[int, int]:
    before = text[:start]
    line = before.count("\n") + 1
    last_nl = before.rfind("\n")
    col = start + 1 if last_nl < 0 else start - last_nl
    return line, col


def first_matching_line(lines: Iterable[str], pattern: str, flags: int = re.IGNORECASE) -> tuple[int, str] | None:
    regex = re.compile(pattern, flags)
    for i, line in enumerate(lines, start=1):
        if regex.search(line):
            return i, line
    return None


def redact_sensitive(value: str) -> str:
    value = re.sub(r"\b(\d{3})[- ]?(\d{2})[- ]?(\d{4})\b", r"***-**-****", value)
    value = re.sub(r"(?i)(edipi|dod\s*id|dodid)([^\d]{0,20})(\d{10})", r"\1\2**********", value)
    value = re.sub(r"\b\d{10}\b", "**********", value)
    value = re.sub(r"\b\d{1,2}([/-])\d{1,2}\1\d{2,4}\b", "**/**/****", value)
    return value.strip()


def normalized_lines(doc: Document) -> list[tuple[int, str]]:
    return [(idx, line.strip()) for idx, line in enumerate(doc.lines, start=1)]


def likely_heading(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    if len(stripped) > 90:
        return False
    if stripped.endswith(":"):
        return True
    if re.match(r"^(\d+\.|[a-zA-Z]\.|\([a-zA-Z0-9]+\))\s+[A-Z][A-Za-z0-9 &'/-]+:?$", stripped):
        return True
    return stripped.isupper() and len(stripped.split()) <= 9

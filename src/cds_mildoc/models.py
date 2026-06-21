from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import IntEnum
from pathlib import Path
from typing import Any


class Severity(IntEnum):
    INFO = 10
    WARN = 20
    ERROR = 30
    BLOCKER = 40

    @classmethod
    def parse(cls, value: str) -> "Severity":
        normalized = value.strip().upper()
        aliases = {"WARNING": "WARN", "ERR": "ERROR", "FAIL": "ERROR", "FATAL": "BLOCKER"}
        normalized = aliases.get(normalized, normalized)
        try:
            return cls[normalized]
        except KeyError as exc:
            names = ", ".join(s.name.lower() for s in cls)
            raise ValueError(f"unknown severity '{value}', expected one of: {names}") from exc

    def __str__(self) -> str:
        return self.name.lower()


@dataclass(slots=True)
class Finding:
    rule_id: str
    severity: Severity
    message: str
    path: str | None = None
    line: int | None = None
    column: int | None = None
    snippet: str | None = None
    recommendation: str | None = None
    source: str | None = None
    testimony: str | None = None
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["severity"] = str(self.severity)
        return data

    @property
    def location(self) -> str:
        bits: list[str] = []
        if self.path:
            bits.append(self.path)
        if self.line is not None:
            bits.append(str(self.line))
            if self.column is not None:
                bits.append(str(self.column))
        return ":".join(bits) if bits else "<document>"


@dataclass(slots=True)
class Document:
    text: str
    path: str | None = None
    kind: str = "text"
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def lines(self) -> list[str]:
        return self.text.splitlines()

    @property
    def name(self) -> str:
        if self.path:
            return Path(self.path).name
        return "<document>"

    def pages(self) -> list[tuple[int, list[str]]]:
        """Return 1-indexed page tuples for text split on form-feed.

        DOCX and Markdown do not expose reliable pagination without a layout engine. For those
        formats this returns one logical page. Plain text can use form-feed characters to make
        the top/bottom CUI checks deterministic.
        """
        raw_pages = self.text.split("\f") if "\f" in self.text else [self.text]
        pages: list[tuple[int, list[str]]] = []
        line_cursor = 1
        for raw in raw_pages:
            page_lines = raw.splitlines()
            pages.append((line_cursor, page_lines))
            line_cursor += max(len(page_lines), 1)
        return pages


@dataclass(slots=True)
class LintResult:
    path: str | None
    findings: list[Finding]
    documents_scanned: int = 1
    parser_warnings: list[str] = field(default_factory=list)

    def extend(self, other: "LintResult") -> None:
        self.findings.extend(other.findings)
        self.documents_scanned += other.documents_scanned
        self.parser_warnings.extend(other.parser_warnings)

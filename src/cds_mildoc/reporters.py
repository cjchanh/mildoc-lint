from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from .models import LintResult, Severity


def render_text(result: LintResult) -> str:
    lines: list[str] = []
    counts = Counter(str(f.severity) for f in result.findings)
    lines.append(
        f"mildoc-lint: scanned {result.documents_scanned} document(s), "
        f"findings={len(result.findings)} "
        f"blocker={counts.get('blocker', 0)} error={counts.get('error', 0)} warn={counts.get('warn', 0)} info={counts.get('info', 0)}"
    )
    if not result.findings:
        lines.append("No findings.")
        return "\n".join(lines)

    for finding in result.findings:
        lines.append("")
        lines.append(f"[{str(finding.severity).upper()}] {finding.rule_id} @ {finding.location}")
        lines.append(f"  {finding.message}")
        if finding.snippet:
            lines.append(f"  snippet: {finding.snippet}")
        if finding.recommendation:
            lines.append(f"  fix: {finding.recommendation}")
        if finding.source:
            lines.append(f"  source: {finding.source}")
    return "\n".join(lines)


def render_json(result: LintResult) -> str:
    payload = {
        "tool": "mildoc-lint",
        "path": result.path,
        "documents_scanned": result.documents_scanned,
        "findings": [f.to_dict() for f in result.findings],
    }
    return json.dumps(payload, indent=2, sort_keys=True)


def render_sarif(result: LintResult) -> str:
    rules: dict[str, dict[str, Any]] = {}
    sarif_results: list[dict[str, Any]] = []
    for finding in result.findings:
        rules.setdefault(
            finding.rule_id,
            {
                "id": finding.rule_id,
                "name": finding.rule_id,
                "shortDescription": {"text": finding.message[:120]},
                "help": {"text": finding.recommendation or finding.message},
                "properties": {"tags": finding.tags},
            },
        )
        level = _sarif_level(finding.severity)
        artifact_uri = finding.path or result.path or "<document>"
        region: dict[str, Any] = {}
        if finding.line is not None:
            region["startLine"] = finding.line
        if finding.column is not None:
            region["startColumn"] = finding.column
        sarif_results.append(
            {
                "ruleId": finding.rule_id,
                "level": level,
                "message": {"text": finding.message},
                "locations": [
                    {
                        "physicalLocation": {
                            "artifactLocation": {"uri": Path(artifact_uri).as_posix()},
                            "region": region,
                        }
                    }
                ],
                "properties": {
                    "severity": str(finding.severity),
                    "recommendation": finding.recommendation,
                    "source": finding.source,
                    "snippet": finding.snippet,
                },
            }
        )

    payload = {
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "mildoc-lint",
                        "rules": list(rules.values()),
                    }
                },
                "results": sarif_results,
            }
        ],
    }
    return json.dumps(payload, indent=2, sort_keys=True)


def exit_code(result: LintResult, fail_on: Severity) -> int:
    return 1 if any(f.severity >= fail_on for f in result.findings) else 0


def _sarif_level(severity: Severity) -> str:
    if severity >= Severity.ERROR:
        return "error"
    if severity == Severity.WARN:
        return "warning"
    return "note"

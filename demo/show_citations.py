#!/usr/bin/env python3
"""Print each finding's cited authority from mildoc-lint JSON on stdin.

Reads the output of `mildoc-lint lint ... --format json` and prints a compact
table: rule id, severity, and the public authority the finding cites. A finding
with no external `source` is labeled an in-house heuristic, so the reader can
always tell a cited-to-authority check from a heuristic one.

Stdlib only. No network, no third-party dependencies.
"""
from __future__ import annotations

import json
import sys


def main() -> int:
    data = json.load(sys.stdin)
    findings = data.get("findings", [])
    if not findings:
        print("  (no findings)")
        return 0
    width = max(len(f["rule_id"]) for f in findings)
    for f in findings:
        source = f.get("source") or "in-house heuristic (no external authority cited)"
        print(f"  {f['rule_id']:<{width}}  {f['severity'].upper():<7}  {source}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Receipt manifest generation, persistence, and decision computation.

A receipt is a content-addressed record of a single lint run. Identical inputs
MUST produce identical receipts. The receipt's `decision` field is computed
from the run's findings under fail-closed gate conditions.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Optional

from .db import default_db_path, get_db, init_db
from .hashing import receipt_hash

RECEIPT_SCHEMA = "mildoc.receipt.v1"

# Rule IDs that always BLOCK regardless of caller --require-* flags.
# Coupled to engine rule taxonomy; renames in the engine MUST update this set.
UNCONDITIONAL_BLOCK_RULES = frozenset({
    "cui.missing_designation_indicator",
    "osmeac.fragord_missing_base_order",
    "namp.missing_evidence",
})


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def generate_receipt(
    *,
    document_sha256: str,
    rule_pack_sha256: str,
    source_set_sha256: str,
    findings_sha256: str,
    decision: str,
    profile: str,
    tool_version: str,
    parent_receipt_sha256: Optional[str] = None,
    created_at_utc: Optional[str] = None,
) -> dict[str, Any]:
    if decision not in {"PASS", "WARN", "FAIL", "BLOCKED"}:
        raise ValueError(f"invalid decision: {decision}")
    manifest: dict[str, Any] = {
        "schema": RECEIPT_SCHEMA,
        "tool": "mildoc-lint",
        "version": tool_version,
        "profile": profile,
        "document_sha256": document_sha256,
        "rule_pack_sha256": rule_pack_sha256,
        "source_set_sha256": source_set_sha256,
        "findings_sha256": findings_sha256,
        "decision": decision,
        "parent_receipt_sha256": parent_receipt_sha256,
        "created_at_utc": created_at_utc if created_at_utc is not None else _utc_now_iso(),
    }
    manifest["receipt_sha256"] = receipt_hash(manifest)
    return manifest


def write_receipt(
    receipt: dict[str, Any],
    activity_id: str,
    *,
    db_path: Optional[Path] = None,
    document_id: Optional[str] = None,
    ndjson_path: Optional[Path] = None,
) -> None:
    required = {
        "schema",
        "tool",
        "version",
        "profile",
        "document_sha256",
        "rule_pack_sha256",
        "source_set_sha256",
        "findings_sha256",
        "decision",
        "created_at_utc",
        "receipt_sha256",
    }
    missing = required - set(receipt.keys())
    if missing:
        raise ValueError(f"receipt missing required fields: {sorted(missing)}")

    resolved_db = db_path if db_path is not None else default_db_path()
    init_db(resolved_db)
    conn = get_db(resolved_db)
    try:
        conn.execute(
            """
            INSERT OR IGNORE INTO receipts (
                receipt_id, activity_id, document_id, receipt_sha256,
                parent_receipt_sha256, decision, created_at_utc, manifest_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                receipt["receipt_sha256"],
                activity_id,
                document_id,
                receipt["receipt_sha256"],
                receipt.get("parent_receipt_sha256"),
                receipt["decision"],
                receipt["created_at_utc"],
                json.dumps(receipt, sort_keys=True, separators=(",", ":")),
            ),
        )
        conn.commit()
    finally:
        conn.close()

    nd_path = ndjson_path if ndjson_path is not None else (resolved_db.parent / "receipts.ndjson")
    nd_path.parent.mkdir(parents=True, exist_ok=True)
    with open(nd_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(receipt, sort_keys=True, separators=(",", ":")) + "\n")


def load_last_receipt(
    document_sha256: str,
    *,
    db_path: Optional[Path] = None,
) -> Optional[dict[str, Any]]:
    resolved_db = db_path if db_path is not None else default_db_path()
    if not resolved_db.exists():
        return None
    conn = get_db(resolved_db)
    try:
        row = conn.execute(
            """
            SELECT r.manifest_json
            FROM receipts r
            JOIN documents d ON r.document_id = d.document_id
            WHERE d.content_sha256 = ?
            ORDER BY r.created_at_utc DESC
            LIMIT 1
            """,
            (document_sha256,),
        ).fetchone()
    finally:
        conn.close()
    if row is None:
        return None
    return json.loads(row[0])


def compute_decision(
    findings: Iterable[Any],
    *,
    require_pass: bool = False,
    require_sources: bool = False,
    require_no_pii: bool = False,
    document_changed_since_last_pass: bool = False,
    rule_pack_changed_since_last_pass: bool = False,
) -> str:
    findings_list = list(findings)

    if document_changed_since_last_pass or rule_pack_changed_since_last_pass:
        return "BLOCKED"

    severities = [_severity_str(f) for f in findings_list]
    has_blocker = any(s == "blocker" for s in severities)
    has_error = any(s == "error" for s in severities)
    has_warn = any(s == "warn" for s in severities)

    if has_blocker:
        return "BLOCKED"

    rule_ids = [_rule_id(f) for f in findings_list]

    if any(r in UNCONDITIONAL_BLOCK_RULES for r in rule_ids):
        return "BLOCKED"

    if require_no_pii and any(r.startswith("pii.") for r in rule_ids):
        return "BLOCKED"

    if require_sources and any(_source_missing(f) for f in findings_list):
        return "BLOCKED"

    if require_pass and has_error:
        return "BLOCKED"

    if has_error:
        return "FAIL"
    if has_warn:
        return "WARN"
    return "PASS"


def _severity_str(finding: Any) -> str:
    sev = getattr(finding, "severity", None)
    if sev is None and isinstance(finding, dict):
        sev = finding.get("severity")
    if sev is None:
        return "info"
    s = str(sev).lower()
    if "blocker" in s:
        return "blocker"
    if "error" in s:
        return "error"
    if "warn" in s:
        return "warn"
    return "info"


def _rule_id(finding: Any) -> str:
    rid = getattr(finding, "rule_id", None)
    if rid is None and isinstance(finding, dict):
        rid = finding.get("rule_id", "")
    return str(rid or "")


def _source_missing(finding: Any) -> bool:
    src = getattr(finding, "source", None)
    if src is None and isinstance(finding, dict):
        src = finding.get("source")
    return not bool(src)

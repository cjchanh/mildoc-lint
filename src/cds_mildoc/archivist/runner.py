"""Orchestration: ingest → lint → receipt.

Sits between the CLI and the persistence/hashing primitives so the CLI stays
thin and tests can call orchestration directly.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from uuid import uuid4

from .._version import __version__
from ..engine import expand_profile, lint_document
from ..packs import RulePackRecord, load_rule_packs, rule_pack_hash
from ..parsers import load_document
from .db import default_db_path, get_db, init_db
from .hashing import (
    content_hash,
    document_hash,
    finding_hash,
)
from .receipts import (
    compute_decision,
    generate_receipt,
    load_last_receipt,
    write_receipt,
)

TOOL_VERSION = __version__


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _rules_signature(profile: str) -> tuple[str, str]:
    """Compute rule-pack and source-set hashes for a given profile.

    Bound to the declarative built-in rule packs and the profile's enabled rule
    modules. Deterministic given a fixed pack set.
    """
    enabled = expand_profile(profile)
    records = load_rule_packs().records_for_profiles(enabled)
    return (rule_pack_hash(records), _source_set_hash(records))


def _source_set_hash(records: list[RulePackRecord]) -> str:
    sources_payload = {
        json.dumps(record.source.to_dict(), sort_keys=True, separators=(",", ":")): record.source.to_dict()
        for record in records
    }
    sources = [sources_payload[key] for key in sorted(sources_payload)]
    return content_hash(json.dumps(sources, sort_keys=True, separators=(",", ":")))


def ingest_document(
    path: str | Path,
    *,
    profile: str = "mildoc",
    case: str = "default",
    db_path: Optional[Path] = None,
) -> dict[str, Any]:
    p = Path(path).resolve()
    doc = load_document(p)
    doc_sha = document_hash(doc.text, str(p))
    document_id = doc_sha
    resolved_db = db_path if db_path is not None else default_db_path()
    init_db(resolved_db)
    conn = get_db(resolved_db)
    try:
        conn.execute(
            """
            INSERT OR IGNORE INTO documents
                (document_id, path, content_sha256, parser, created_at_utc)
            VALUES (?, ?, ?, ?, ?)
            """,
            (document_id, str(p), doc_sha, "mildoc-lint", _utc_now()),
        )
        conn.commit()
    finally:
        conn.close()
    return {
        "document_id": document_id,
        "document_sha256": doc_sha,
        "path": str(p),
        "profile": profile,
        "case": case,
    }


def lint_with_receipt(
    path: str | Path,
    *,
    profile: str = "mildoc",
    write: bool = False,
    require_pass: bool = False,
    require_sources: bool = False,
    require_no_pii: bool = False,
    db_path: Optional[Path] = None,
) -> dict[str, Any]:
    p = Path(path).resolve()
    doc = load_document(p)
    doc_sha = document_hash(doc.text, str(p))

    findings = lint_document(doc, profile=profile)
    rule_pack_sha, source_set_sha = _rules_signature(profile)
    findings_canonical = json.dumps(
        [
            {
                "rule_id": f.rule_id,
                "severity": str(f.severity),
                "message": f.message,
                "line": f.line,
                "source": f.source,
            }
            for f in findings
        ],
        sort_keys=True,
        separators=(",", ":"),
    )
    findings_sha = content_hash(findings_canonical)

    last = load_last_receipt(doc_sha, db_path=db_path)
    document_changed = False
    rule_pack_changed = False
    parent_receipt_sha = None
    if last is not None:
        parent_receipt_sha = last.get("receipt_sha256")
        if last.get("decision") == "PASS":
            if last.get("document_sha256") != doc_sha:
                document_changed = True
            if last.get("rule_pack_sha256") != rule_pack_sha:
                rule_pack_changed = True

    decision = compute_decision(
        findings,
        require_pass=require_pass,
        require_sources=require_sources,
        require_no_pii=require_no_pii,
        document_changed_since_last_pass=document_changed,
        rule_pack_changed_since_last_pass=rule_pack_changed,
    )

    activity_id = uuid4().hex
    started = _utc_now()
    activity_input_sha = content_hash(json.dumps({"document_sha256": doc_sha, "profile": profile}, sort_keys=True))

    receipt = generate_receipt(
        document_sha256=doc_sha,
        rule_pack_sha256=rule_pack_sha,
        source_set_sha256=source_set_sha,
        findings_sha256=findings_sha,
        decision=decision,
        profile=profile,
        tool_version=TOOL_VERSION,
        parent_receipt_sha256=parent_receipt_sha,
        created_at_utc=started,
    )

    if write:
        resolved_db = db_path if db_path is not None else default_db_path()
        init_db(resolved_db)
        ingest_document(p, profile=profile, db_path=resolved_db)
        conn = get_db(resolved_db)
        try:
            conn.execute(
                """
                INSERT OR IGNORE INTO activities (
                    activity_id, activity_type, tool_version, rule_pack_id,
                    input_sha256, output_sha256, status, started_at_utc, completed_at_utc
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    activity_id,
                    "lint_run",
                    TOOL_VERSION,
                    rule_pack_sha,
                    activity_input_sha,
                    findings_sha,
                    decision,
                    started,
                    _utc_now(),
                ),
            )
            for f in findings:
                fid = finding_hash(f.rule_id, f.message, f.snippet or "")
                conn.execute(
                    """
                    INSERT OR IGNORE INTO findings (
                        finding_id, document_id, rule_id, severity, status,
                        message, line, evidence_sha256, source_id, created_at_utc
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        fid,
                        doc_sha,
                        f.rule_id,
                        str(f.severity),
                        decision,
                        f.message,
                        f.line,
                        content_hash(f.snippet or ""),
                        f.source,
                        started,
                    ),
                )
            conn.commit()
        finally:
            conn.close()
        write_receipt(receipt, activity_id, db_path=resolved_db, document_id=doc_sha)

    return {
        "receipt": receipt,
        "findings_count": len(findings),
        "document_sha256": doc_sha,
        "decision": decision,
        "activity_id": activity_id,
    }


def status_for(path: str | Path, *, db_path: Optional[Path] = None) -> dict[str, Any]:
    p = Path(path).resolve()
    doc = load_document(p)
    doc_sha = document_hash(doc.text, str(p))
    last = load_last_receipt(doc_sha, db_path=db_path)
    return {
        "document_sha256": doc_sha,
        "path": str(p),
        "has_receipt": last is not None,
        "last_receipt": last,
    }


def diff_documents(
    old_path: str | Path,
    new_path: str | Path,
    *,
    db_path: Optional[Path] = None,
) -> dict[str, Any]:
    old = status_for(old_path, db_path=db_path)
    new = status_for(new_path, db_path=db_path)
    sha_changed = old["document_sha256"] != new["document_sha256"]
    old_decision = (old.get("last_receipt") or {}).get("decision")
    new_decision = (new.get("last_receipt") or {}).get("decision")
    return {
        "old": old,
        "new": new,
        "sha_changed": sha_changed,
        "decision_changed": old_decision != new_decision,
        "old_decision": old_decision,
        "new_decision": new_decision,
    }

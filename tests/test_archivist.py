"""Tests for the Archivist receipt engine."""
from __future__ import annotations

from pathlib import Path

import pytest

from cds_mildoc.archivist import (
    compute_decision,
    diff_documents,
    document_hash,
    generate_receipt,
    init_db,
    lint_with_receipt,
    load_last_receipt,
    status_for,
    write_receipt,
)
from cds_mildoc.cli import main as cli_main
from cds_mildoc.models import Finding, Severity


def _opord_text(suffix: str = "") -> str:
    return f"""OPORD 001 - SYNTHETIC

Orientation
Synthetic terrain.

1. Situation
Synthetic.

2. Mission
Team will conduct training NLT 2200 vicinity AO Bravo in order to validate procedures.

3. Execution
a. Commander's Intent
b. Concept of Operations
c. Tasks
d. Coordinating Instructions

4. Administration and Logistics
Synthetic admin.

5. Command and Signal
Synthetic command.
{suffix}
"""


def test_receipt_hash_is_deterministic() -> None:
    base = dict(
        document_sha256="d" * 64,
        rule_pack_sha256="r" * 64,
        source_set_sha256="s" * 64,
        findings_sha256="f" * 64,
        decision="PASS",
        profile="all",
        tool_version="0.2.0",
        created_at_utc="2026-05-06T00:00:00Z",
    )
    r1 = generate_receipt(**base)
    r2 = generate_receipt(**base)
    assert r1["receipt_sha256"] == r2["receipt_sha256"]
    assert r1 == r2


def test_receipt_hash_excludes_runtime_timestamp() -> None:
    base = dict(
        document_sha256="d" * 64,
        rule_pack_sha256="r" * 64,
        source_set_sha256="s" * 64,
        findings_sha256="f" * 64,
        decision="PASS",
        profile="all",
        tool_version="0.2.0",
    )
    r1 = generate_receipt(**base, created_at_utc="2026-05-06T00:00:00Z")
    r2 = generate_receipt(**base, created_at_utc="2026-05-06T00:00:01Z")
    assert r1["created_at_utc"] != r2["created_at_utc"]
    assert r1["receipt_sha256"] == r2["receipt_sha256"]


def test_document_hash_changes_with_content(tmp_path: Path) -> None:
    h1 = document_hash("alpha", path="x.md")
    h2 = document_hash("bravo", path="x.md")
    assert h1 != h2
    h3 = document_hash("alpha", path="y.md")
    assert h1 != h3


def test_init_db_is_idempotent(tmp_path: Path) -> None:
    db = tmp_path / ".mildoc" / "archivist.sqlite3"
    init_db(db)
    init_db(db)
    assert db.exists()
    import sqlite3

    conn = sqlite3.connect(db)
    try:
        names = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    finally:
        conn.close()
    assert {"documents", "sections", "claims", "sources", "rule_packs", "findings", "activities", "receipts"}.issubset(names)


def test_write_and_load_receipt_round_trip(tmp_path: Path) -> None:
    db = tmp_path / "ledger.sqlite3"
    init_db(db)
    import sqlite3

    conn = sqlite3.connect(db)
    try:
        conn.execute(
            "INSERT INTO documents (document_id, path, content_sha256, parser, created_at_utc) "
            "VALUES (?, ?, ?, ?, ?)",
            ("doc-sha-A", "/tmp/x.md", "doc-sha-A", "test", "2026-05-06T00:00:00Z"),
        )
        conn.commit()
    finally:
        conn.close()

    receipt = generate_receipt(
        document_sha256="doc-sha-A",
        rule_pack_sha256="rp-A",
        source_set_sha256="ss-A",
        findings_sha256="f-A",
        decision="PASS",
        profile="all",
        tool_version="0.2.0",
        created_at_utc="2026-05-06T00:00:01Z",
    )
    write_receipt(receipt, activity_id="act-A", db_path=db, document_id="doc-sha-A")

    loaded = load_last_receipt("doc-sha-A", db_path=db)
    assert loaded is not None
    assert loaded["receipt_sha256"] == receipt["receipt_sha256"]
    assert loaded["decision"] == "PASS"
    assert loaded["document_sha256"] == "doc-sha-A"


def test_compute_decision_blocks_on_changed_document() -> None:
    decision = compute_decision(
        [],
        document_changed_since_last_pass=True,
    )
    assert decision == "BLOCKED"


def test_compute_decision_blocks_on_changed_rule_pack() -> None:
    decision = compute_decision(
        [],
        rule_pack_changed_since_last_pass=True,
    )
    assert decision == "BLOCKED"


def test_compute_decision_require_pass_blocks_on_error() -> None:
    f = Finding(rule_id="cui.invalid_banner", severity=Severity.ERROR, message="x", source="DOD")
    assert compute_decision([f], require_pass=True) == "BLOCKED"
    assert compute_decision([f], require_pass=False) == "FAIL"


def test_compute_decision_require_no_pii_blocks_on_pii() -> None:
    f = Finding(rule_id="pii.ssn", severity=Severity.ERROR, message="x", source="NIST")
    assert compute_decision([f], require_no_pii=True) == "BLOCKED"


def test_compute_decision_require_sources_blocks_when_missing() -> None:
    f = Finding(rule_id="cui.unmarked", severity=Severity.WARN, message="x", source=None)
    assert compute_decision([f], require_sources=True) == "BLOCKED"
    g = Finding(rule_id="cui.unmarked", severity=Severity.WARN, message="x", source="DOD")
    assert compute_decision([g], require_sources=True) == "WARN"


def test_compute_decision_blocks_on_fragord_no_base_order() -> None:
    f = Finding(rule_id="osmeac.fragord_missing_base_order", severity=Severity.ERROR, message="x", source="USMC")
    assert compute_decision([f]) == "BLOCKED"


def test_lint_with_receipt_round_trip(tmp_path: Path) -> None:
    db = tmp_path / "ledger.sqlite3"
    doc_path = tmp_path / "opord.md"
    doc_path.write_text(_opord_text(), encoding="utf-8")
    result = lint_with_receipt(doc_path, profile="osmeac", write=True, db_path=db)
    assert "receipt" in result
    assert result["receipt"]["receipt_sha256"]
    assert result["receipt"]["document_sha256"] == document_hash(_opord_text(), str(doc_path.resolve()))


def test_archivist_lint_is_deterministic(tmp_path: Path) -> None:
    db = tmp_path / "ledger.sqlite3"
    doc_path = tmp_path / "opord.md"
    doc_path.write_text(_opord_text(), encoding="utf-8")
    fixed_kwargs = dict(profile="osmeac", write=False, db_path=db)
    r1 = lint_with_receipt(doc_path, **fixed_kwargs)
    r2 = lint_with_receipt(doc_path, **fixed_kwargs)
    assert r1["receipt"]["document_sha256"] == r2["receipt"]["document_sha256"]
    assert r1["receipt"]["rule_pack_sha256"] == r2["receipt"]["rule_pack_sha256"]
    assert r1["receipt"]["source_set_sha256"] == r2["receipt"]["source_set_sha256"]
    assert r1["receipt"]["findings_sha256"] == r2["receipt"]["findings_sha256"]


def test_status_reports_no_prior_receipt(tmp_path: Path) -> None:
    db = tmp_path / "ledger.sqlite3"
    init_db(db)
    doc_path = tmp_path / "x.md"
    doc_path.write_text("# X\n\nbody.\n", encoding="utf-8")
    info = status_for(doc_path, db_path=db)
    assert info["has_receipt"] is False
    assert info["last_receipt"] is None


def test_diff_reports_sha_change(tmp_path: Path) -> None:
    db = tmp_path / "ledger.sqlite3"
    init_db(db)
    a = tmp_path / "a.md"
    b = tmp_path / "b.md"
    a.write_text(_opord_text(), encoding="utf-8")
    b.write_text(_opord_text(suffix="extra"), encoding="utf-8")
    info = diff_documents(a, b, db_path=db)
    assert info["sha_changed"] is True


def test_receipts_ndjson_appends(tmp_path: Path) -> None:
    db = tmp_path / "ledger.sqlite3"
    init_db(db)
    nd = db.parent / "receipts.ndjson"
    import sqlite3

    conn = sqlite3.connect(db)
    try:
        conn.execute(
            "INSERT INTO documents (document_id, path, content_sha256, parser, created_at_utc) "
            "VALUES (?, ?, ?, ?, ?)",
            ("doc-A", "/tmp/x.md", "doc-A", "test", "2026-05-06T00:00:00Z"),
        )
        conn.commit()
    finally:
        conn.close()

    for i in range(3):
        receipt = generate_receipt(
            document_sha256="doc-A",
            rule_pack_sha256="rp",
            source_set_sha256="ss",
            findings_sha256=f"f-{i}",
            decision="PASS",
            profile="all",
            tool_version="0.2.0",
            created_at_utc=f"2026-05-06T00:00:0{i}Z",
        )
        write_receipt(receipt, activity_id=f"act-{i}", db_path=db, document_id="doc-A")
    assert nd.exists()
    lines = [ln for ln in nd.read_text(encoding="utf-8").splitlines() if ln.strip()]
    assert len(lines) == 3


def test_write_receipt_rejects_missing_required_field(tmp_path: Path) -> None:
    db = tmp_path / "ledger.sqlite3"
    init_db(db)
    bad = {"schema": "mildoc.receipt.v1", "decision": "PASS"}
    with pytest.raises(ValueError):
        write_receipt(bad, activity_id="act", db_path=db)


def test_generate_receipt_rejects_invalid_decision() -> None:
    with pytest.raises(ValueError):
        generate_receipt(
            document_sha256="d",
            rule_pack_sha256="r",
            source_set_sha256="s",
            findings_sha256="f",
            decision="OK",
            profile="all",
            tool_version="0.2.0",
        )


def test_cli_archivist_init_creates_db_at_custom_path(tmp_path: Path) -> None:
    db = tmp_path / "custom.sqlite3"
    rc = cli_main(["archivist", "init", "--db-path", str(db)])
    assert rc == 0
    assert db.exists()


def test_cli_archivist_lint_writes_receipt(tmp_path: Path) -> None:
    db = tmp_path / "ledger.sqlite3"
    doc_path = tmp_path / "opord.md"
    doc_path.write_text(_opord_text(), encoding="utf-8")
    rc = cli_main([
        "archivist", "lint", str(doc_path),
        "--profile", "osmeac",
        "--write-receipt",
        "--db-path", str(db),
        "--format", "json",
    ])
    assert rc in (0, 1)
    nd = db.parent / "receipts.ndjson"
    assert nd.exists()


def test_cli_archivist_gate_exits_one_on_blocked(tmp_path: Path, capsys) -> None:
    db = tmp_path / "ledger.sqlite3"
    bad = tmp_path / "bad.md"
    bad.write_text("CUI//CTI\n\nSynthetic content but missing DI block.\n", encoding="utf-8")
    rc = cli_main([
        "archivist", "gate", str(bad),
        "--profile", "cui",
        "--require-pass",
        "--db-path", str(db),
    ])
    assert rc == 1


def test_cli_archivist_gate_exits_zero_on_clean(tmp_path: Path) -> None:
    db = tmp_path / "ledger.sqlite3"
    doc_path = tmp_path / "namp.md"
    doc_path.write_text(
        "NAMP/CSEC Discrepancy Record\n"
        "Reference: synthetic checklist\n"
        "Discrepancy: synthetic.\n"
        "Owner/OPR: Synthetic Work Center\n"
        "Corrective Action: synthetic.\n"
        "Due Date: 2026-05-15\n"
        "Status: Open\n"
        "Evidence: SYN-001\n",
        encoding="utf-8",
    )
    rc = cli_main([
        "archivist", "gate", str(doc_path),
        "--profile", "namp",
        "--db-path", str(db),
    ])
    assert rc == 0

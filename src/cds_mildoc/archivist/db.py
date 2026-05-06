"""SQLite ledger for Archivist.

Schema mirrors the W3C PROV pattern: documents/sections/claims are entities,
activities are lint/parse runs, rule_packs/sources/agents underwrite findings,
receipts chain the activity outputs.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path


def default_db_path(cwd: Path | None = None) -> Path:
    base = cwd if cwd is not None else Path.cwd()
    return base / ".mildoc" / "archivist.sqlite3"


SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    document_id      TEXT PRIMARY KEY,
    path             TEXT NOT NULL,
    content_sha256   TEXT NOT NULL,
    parser           TEXT NOT NULL,
    created_at_utc   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sections (
    section_id     TEXT PRIMARY KEY,
    document_id    TEXT NOT NULL,
    heading        TEXT NOT NULL,
    start_line     INTEGER,
    end_line       INTEGER,
    text_sha256    TEXT NOT NULL,
    FOREIGN KEY(document_id) REFERENCES documents(document_id)
);

CREATE TABLE IF NOT EXISTS claims (
    claim_id       TEXT PRIMARY KEY,
    document_id    TEXT NOT NULL,
    section_id     TEXT,
    claim_text     TEXT NOT NULL,
    claim_sha256   TEXT NOT NULL,
    claim_type     TEXT NOT NULL,
    source_id      TEXT,
    status         TEXT NOT NULL,
    FOREIGN KEY(document_id) REFERENCES documents(document_id),
    FOREIGN KEY(section_id) REFERENCES sections(section_id)
);

CREATE TABLE IF NOT EXISTS sources (
    source_id          TEXT PRIMARY KEY,
    title              TEXT NOT NULL,
    url                TEXT,
    source_sha256      TEXT,
    retrieved_at_utc   TEXT,
    authority_level    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS rule_packs (
    rule_pack_id     TEXT PRIMARY KEY,
    name             TEXT NOT NULL,
    version          TEXT NOT NULL,
    rules_sha256     TEXT NOT NULL,
    sources_sha256   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS findings (
    finding_id       TEXT PRIMARY KEY,
    document_id      TEXT NOT NULL,
    rule_id          TEXT NOT NULL,
    severity         TEXT NOT NULL,
    status           TEXT NOT NULL,
    message          TEXT NOT NULL,
    line             INTEGER,
    evidence_sha256  TEXT,
    source_id        TEXT,
    created_at_utc   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS activities (
    activity_id        TEXT PRIMARY KEY,
    activity_type      TEXT NOT NULL,
    tool_version       TEXT NOT NULL,
    rule_pack_id       TEXT,
    input_sha256       TEXT NOT NULL,
    output_sha256      TEXT NOT NULL,
    status             TEXT NOT NULL,
    started_at_utc     TEXT NOT NULL,
    completed_at_utc   TEXT
);

CREATE TABLE IF NOT EXISTS receipts (
    receipt_id              TEXT PRIMARY KEY,
    activity_id             TEXT NOT NULL,
    document_id             TEXT,
    receipt_sha256          TEXT NOT NULL,
    parent_receipt_sha256   TEXT,
    decision                TEXT NOT NULL,
    created_at_utc          TEXT NOT NULL,
    manifest_json           TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_documents_content_sha256
    ON documents(content_sha256);
CREATE INDEX IF NOT EXISTS idx_receipts_document_id
    ON receipts(document_id);
CREATE INDEX IF NOT EXISTS idx_receipts_created_at
    ON receipts(created_at_utc);
"""


def init_db(db_path: Path | None = None) -> Path:
    path = db_path if db_path is not None else default_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()
    return path


def get_db(db_path: Path | None = None) -> sqlite3.Connection:
    path = db_path if db_path is not None else default_db_path()
    if not path.exists():
        init_db(path)
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

"""Archivist: local receipt and provenance ledger for mildoc-lint.

The Archivist records what was checked, against what rule pack, by what tool
version, with which sources, and what the decision was. Every meaningful object
gets a content hash. Every lint run produces a deterministic receipt that can
be chained, verified, and gated against.

This is not a compliance certification. It is a local document-assurance ledger.
"""
from __future__ import annotations

from .db import default_db_path, get_db, init_db
from .hashing import (
    claim_hash,
    content_hash,
    document_hash,
    finding_hash,
    receipt_hash,
    rule_pack_hash,
    section_hash,
)
from .receipts import (
    compute_decision,
    generate_receipt,
    load_last_receipt,
    write_receipt,
)
from .runner import (
    diff_documents,
    ingest_document,
    lint_with_receipt,
    status_for,
)

__all__ = [
    "default_db_path",
    "claim_hash",
    "compute_decision",
    "content_hash",
    "diff_documents",
    "document_hash",
    "finding_hash",
    "generate_receipt",
    "get_db",
    "ingest_document",
    "init_db",
    "lint_with_receipt",
    "load_last_receipt",
    "receipt_hash",
    "rule_pack_hash",
    "section_hash",
    "status_for",
    "write_receipt",
]

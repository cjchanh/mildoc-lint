"""Deterministic SHA-256 hashing primitives for the Archivist.

Every meaningful object in the receipt chain gets hashed via canonical JSON.
Determinism is the contract: identical inputs MUST produce identical hashes.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any


def content_hash(data: str | bytes) -> str:
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def _canonical(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def document_hash(text: str, path: str = "") -> str:
    normalized = text.strip()
    return content_hash(_canonical({"text": normalized, "path": path}))


def section_hash(heading: str, body: str) -> str:
    return content_hash(_canonical({"heading": heading.strip(), "body": body.strip()}))


def claim_hash(claim_text: str, location: str = "") -> str:
    return content_hash(_canonical({"claim": claim_text.strip(), "location": location}))


def finding_hash(rule_id: str, message: str, evidence: str = "") -> str:
    return content_hash(_canonical({"rule_id": rule_id, "message": message, "evidence": evidence}))


def rule_pack_hash(rules: dict[str, Any], sources: dict[str, Any]) -> str:
    return content_hash(_canonical({"rules": rules, "sources": sources}))


def receipt_hash(manifest: dict[str, Any]) -> str:
    payload = {k: v for k, v in manifest.items() if k != "receipt_sha256"}
    return content_hash(_canonical(payload))

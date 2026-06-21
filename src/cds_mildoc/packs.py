from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from functools import lru_cache
from importlib import resources
from pathlib import Path
from types import MappingProxyType
from typing import Any, Iterable, Mapping, Sequence

from .models import Severity

BUILTIN_PACK_FILES = ("cui.yaml", "pii.yaml", "osmeac.yaml", "naval.yaml", "namp.yaml")

_RULE_ID_RE = re.compile(r"^[a-z][a-z0-9_]*(?:\.[a-z0-9_]+)+$")
_PROFILE_RE = re.compile(r"^[a-z][a-z0-9_-]*$")
_UTC_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


class RulePackError(ValueError):
    """Raised when a rule pack cannot be trusted enough to load."""


@dataclass(frozen=True, slots=True)
class RuleSource:
    title: str
    url: str
    retrieved_at_utc: str

    def to_dict(self) -> dict[str, str]:
        return {
            "title": self.title,
            "url": self.url,
            "retrieved_at_utc": self.retrieved_at_utc,
        }


@dataclass(frozen=True, slots=True)
class RulePackRecord:
    rule_id: str
    severity: Severity
    profile: str
    source: RuleSource
    testimony: str
    fail_closed: bool

    @property
    def source_text(self) -> str:
        return f"{self.source.title} - {self.source.url}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "severity": str(self.severity),
            "profile": self.profile,
            "source": self.source.to_dict(),
            "testimony": self.testimony,
            "fail_closed": self.fail_closed,
        }


@dataclass(frozen=True, slots=True)
class RulePackCatalog:
    records: Mapping[str, RulePackRecord]
    rule_pack_hash: str
    source_set_hash: str

    def get(self, rule_id: str) -> RulePackRecord | None:
        return self.records.get(rule_id)

    def require(self, rule_id: str) -> RulePackRecord:
        record = self.get(rule_id)
        if record is None:
            raise RulePackError(f"rule_id has no rule-pack record: {rule_id}")
        return record

    def records_for_profiles(self, profiles: Iterable[str]) -> list[RulePackRecord]:
        enabled = set(profiles)
        return [record for record in self.records.values() if record.profile in enabled]


def load_rule_packs(extra_paths: Sequence[str | Path] | None = None) -> RulePackCatalog:
    """Load built-in packs plus optional overlay packs.

    Overlay packs may add metadata-only rule records or override metadata for an
    existing rule_id. The engine only applies records for findings actually
    emitted by Python implementations.
    """
    if not extra_paths:
        return load_builtin_rule_packs()
    return _load_overlayed_rule_packs(tuple(str(path) for path in extra_paths))


@lru_cache(maxsize=32)
def _load_overlayed_rule_packs(overlay_paths: tuple[str, ...]) -> RulePackCatalog:
    # Cached on the overlay path set so a multi-document scan with --rule-pack
    # parses each overlay once, not once per document.
    records = dict(load_builtin_rule_packs().records)
    for path in overlay_paths:
        _merge_records(records, _load_pack_path(Path(path)), source=path)
    return _catalog(records.values())


@lru_cache(maxsize=1)
def load_builtin_rule_packs() -> RulePackCatalog:
    records: list[RulePackRecord] = []
    for name in BUILTIN_PACK_FILES:
        pack = resources.files("cds_mildoc").joinpath("rule_packs").joinpath(name)
        records.extend(_records_from_text(pack.read_text(encoding="utf-8"), source=name))
    return _catalog(records)


def rule_pack_hash(records: Mapping[str, RulePackRecord] | Iterable[RulePackRecord]) -> str:
    record_iter: Iterable[RulePackRecord]
    if isinstance(records, Mapping):
        record_iter = records.values()
    else:
        record_iter = records
    payload = [record.to_dict() for record in sorted(record_iter, key=lambda r: r.rule_id)]
    return _hash_payload(payload)


def _load_pack_path(path: Path) -> list[RulePackRecord]:
    if not path.exists():
        raise RulePackError(f"rule pack does not exist: {path}")
    if not path.is_file():
        raise RulePackError(f"rule pack is not a file: {path}")
    return _records_from_text(path.read_text(encoding="utf-8"), source=str(path))


def _records_from_text(text: str, *, source: str) -> list[RulePackRecord]:
    raw_records = _parse_yaml_records(text, source=source)
    records = [_record_from_mapping(raw, source=source, index=i) for i, raw in enumerate(raw_records, start=1)]
    seen: set[str] = set()
    duplicates: list[str] = []
    for record in records:
        if record.rule_id in seen:
            duplicates.append(record.rule_id)
        seen.add(record.rule_id)
    if duplicates:
        raise RulePackError(f"{source}: duplicate rule_id(s): {', '.join(sorted(duplicates))}")
    return records


def _merge_records(target: dict[str, RulePackRecord], records: list[RulePackRecord], *, source: str) -> None:
    for record in records:
        if not record.fail_closed:
            raise RulePackError(f"{source}: overlay record must be fail_closed: {record.rule_id}")
        target[record.rule_id] = record


def _catalog(records: Iterable[RulePackRecord]) -> RulePackCatalog:
    record_list = sorted(records, key=lambda r: r.rule_id)
    ordered = {record.rule_id: record for record in record_list}
    if len(ordered) != len(record_list):
        raise RulePackError("duplicate rule_id in rule-pack catalog")
    return RulePackCatalog(
        records=MappingProxyType(ordered),
        rule_pack_hash=rule_pack_hash(ordered),
        source_set_hash=source_set_hash(ordered.values()),
    )


def source_set_hash(records: Iterable[RulePackRecord]) -> str:
    """Deterministic hash of the unique source set. Single source of truth —
    the Archivist receipt layer calls this rather than re-implementing it."""
    unique = {
        json.dumps(record.source.to_dict(), sort_keys=True, separators=(",", ":")): record.source.to_dict()
        for record in records
    }
    return _hash_payload([unique[key] for key in sorted(unique)])


def _hash_payload(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _record_from_mapping(data: Mapping[str, Any], *, source: str, index: int) -> RulePackRecord:
    required = {"rule_id", "severity", "profile", "source", "testimony", "fail_closed"}
    missing = required - set(data)
    extra = set(data) - required
    if missing or extra:
        details: list[str] = []
        if missing:
            details.append("missing " + ", ".join(sorted(missing)))
        if extra:
            details.append("unknown " + ", ".join(sorted(extra)))
        raise RulePackError(f"{source}: record {index}: " + "; ".join(details))

    rule_id = _expect_str(data["rule_id"], source, index, "rule_id")
    if not _RULE_ID_RE.match(rule_id):
        raise RulePackError(f"{source}: record {index}: invalid rule_id: {rule_id}")

    profile = _expect_str(data["profile"], source, index, "profile")
    if not _PROFILE_RE.match(profile):
        raise RulePackError(f"{source}: record {index}: invalid profile: {profile}")

    source_data = data["source"]
    if not isinstance(source_data, Mapping):
        raise RulePackError(f"{source}: record {index}: source must be a mapping")
    source_required = {"title", "url", "retrieved_at_utc"}
    source_missing = source_required - set(source_data)
    source_extra = set(source_data) - source_required
    if source_missing or source_extra:
        raise RulePackError(f"{source}: record {index}: invalid source fields")

    title = _expect_str(source_data["title"], source, index, "source.title")
    url = _expect_str(source_data["url"], source, index, "source.url")
    retrieved = _expect_str(source_data["retrieved_at_utc"], source, index, "source.retrieved_at_utc")
    if not _UTC_RE.match(retrieved):
        raise RulePackError(f"{source}: record {index}: source.retrieved_at_utc must be UTC Zulu time")

    fail_closed = data["fail_closed"]
    if fail_closed is not True:
        raise RulePackError(f"{source}: record {index}: fail_closed must be true")

    return RulePackRecord(
        rule_id=rule_id,
        severity=Severity.parse(_expect_str(data["severity"], source, index, "severity")),
        profile=profile,
        source=RuleSource(title=title, url=url, retrieved_at_utc=retrieved),
        testimony=_expect_str(data["testimony"], source, index, "testimony"),
        fail_closed=fail_closed,
    )


def _expect_str(value: Any, source: str, index: int, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RulePackError(f"{source}: record {index}: {field} must be a non-empty string")
    return value.strip()


def _parse_yaml_records(text: str, *, source: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    nested_key: str | None = None

    for lineno, raw_line in enumerate(text.splitlines(), start=1):
        if "\t" in raw_line:
            raise RulePackError(f"{source}:{lineno}: tabs are not supported in rule-pack YAML")
        line = _strip_comment(raw_line).rstrip()
        if not line.strip():
            continue

        indent = len(line) - len(line.lstrip(" "))
        stripped = line.strip()

        if indent == 0 and stripped.startswith("- "):
            if current is not None:
                records.append(current)
            current = {}
            nested_key = None
            rest = stripped[2:].strip()
            if rest:
                key, value = _split_key_value(rest, source, lineno)
                if value:
                    current[key] = _parse_scalar(value, source, lineno)
                else:
                    current[key] = {}
                    nested_key = key
            continue

        if current is None:
            raise RulePackError(f"{source}:{lineno}: expected a list item")

        if indent == 2:
            key, value = _split_key_value(stripped, source, lineno)
            if value:
                current[key] = _parse_scalar(value, source, lineno)
                nested_key = None
            else:
                current[key] = {}
                nested_key = key
            continue

        if indent == 4 and nested_key:
            container = current.get(nested_key)
            if not isinstance(container, dict):
                raise RulePackError(f"{source}:{lineno}: parent key is not a mapping")
            key, value = _split_key_value(stripped, source, lineno)
            if not value:
                raise RulePackError(f"{source}:{lineno}: nested mappings may not be empty")
            container[key] = _parse_scalar(value, source, lineno)
            continue

        raise RulePackError(f"{source}:{lineno}: unsupported indentation")

    if current is not None:
        records.append(current)
    if not records:
        raise RulePackError(f"{source}: rule pack has no records")
    return records


def _split_key_value(line: str, source: str, lineno: int) -> tuple[str, str]:
    key, sep, value = line.partition(":")
    if not sep:
        raise RulePackError(f"{source}:{lineno}: expected key: value")
    key = key.strip()
    if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", key):
        raise RulePackError(f"{source}:{lineno}: invalid key: {key}")
    return key, value.strip()


def _parse_scalar(raw: str, source: str, lineno: int) -> str | bool:
    if raw == "true":
        return True
    if raw == "false":
        return False
    if raw.startswith('"') and raw.endswith('"'):
        try:
            value = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise RulePackError(f"{source}:{lineno}: invalid quoted string") from exc
        if not isinstance(value, str):
            raise RulePackError(f"{source}:{lineno}: expected string scalar")
        return value
    if raw.startswith("'") and raw.endswith("'"):
        return raw[1:-1].replace("''", "'")
    return raw


def _strip_comment(line: str) -> str:
    in_single = False
    in_double = False
    escaped = False
    for idx, char in enumerate(line):
        if escaped:
            escaped = False
            continue
        if char == "\\" and in_double:
            escaped = True
            continue
        if char == "'" and not in_double:
            in_single = not in_single
            continue
        if char == '"' and not in_single:
            in_double = not in_double
            continue
        if char == "#" and not in_single and not in_double:
            return line[:idx]
    return line

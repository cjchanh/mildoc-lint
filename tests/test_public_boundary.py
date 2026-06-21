"""Public release boundary tests.

Enforces that:
1. README and docs do not contain unsupported compliance claims (banned-phrase list).
2. Required public-boundary files exist.
3. README contains the required disclaimers.
"""
from __future__ import annotations

from pathlib import Path

from cds_mildoc.packs import BUILTIN_PACK_FILES, load_builtin_rule_packs
from cds_mildoc.references import AUTHORITIES

REPO_ROOT = Path(__file__).resolve().parents[1]

BANNED_PHRASES = [
    "DoD approved",
    "CMMC compliant",
    "RMF ready",
    "certifies",
    "certified compliance",
    "full 30-item",
    "CY26Q2 checklist",
    "official DoD",
    "official Navy",
    "official USMC",
    "classification review assistant",
    "AI writes orders",
]

# Files that intentionally enumerate banned phrases for documentation purposes.
EXCLUDE_FROM_PHRASE_CHECK = {
    "docs/RELEASE_CHECKLIST.md",
    "CONTRIBUTING.md",
    "docs/CLAIMS_MAP.md",
    "tests/test_no_overclaim.py",
    "tests/test_public_boundary.py",
}

REQUIRED_PUBLIC_FILES = [
    "INTENT.md",
    "CONTRIBUTING.md",
    "docs/PUBLIC_BOUNDARY.md",
    "docs/CLAIMS_MAP.md",
    "docs/SOURCES.md",
    "docs/RELEASE_CHECKLIST.md",
]

REQUIRED_README_PHRASES = [
    "does not generate tactical plans",
    "does not certify",
    "synthetic examples",
]


def _scanned_markdown() -> list[Path]:
    files: list[Path] = []
    for top in ("README.md", "ROADMAP.md", "SECURITY.md", "THREAT_MODEL.md", "INTENT.md"):
        p = REPO_ROOT / top
        if p.exists():
            files.append(p)
    docs_dir = REPO_ROOT / "docs"
    if docs_dir.exists():
        files.extend(sorted(docs_dir.rglob("*.md")))
    out: list[Path] = []
    for f in files:
        rel = f.relative_to(REPO_ROOT).as_posix()
        if rel in EXCLUDE_FROM_PHRASE_CHECK:
            continue
        out.append(f)
    return out


def test_no_banned_phrases_in_public_docs() -> None:
    offenders: list[str] = []
    for md in _scanned_markdown():
        text = md.read_text(encoding="utf-8")
        for phrase in BANNED_PHRASES:
            if phrase.lower() in text.lower():
                offenders.append(f"{md.relative_to(REPO_ROOT)}: contains banned phrase '{phrase}'")
    assert not offenders, "Banned public-boundary phrases found:\n" + "\n".join(offenders)


def test_required_public_files_exist() -> None:
    missing: list[str] = []
    for rel in REQUIRED_PUBLIC_FILES:
        if not (REPO_ROOT / rel).exists():
            missing.append(rel)
    assert not missing, "Required public-boundary files missing:\n" + "\n".join(missing)


def test_readme_contains_required_disclaimers() -> None:
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8").lower()
    missing: list[str] = []
    for phrase in REQUIRED_README_PHRASES:
        if phrase.lower() not in readme:
            missing.append(phrase)
    assert not missing, "README missing required disclaimer phrases:\n" + "\n".join(missing)


def test_builtin_rule_packs_use_public_authority_sources() -> None:
    pack_dir = REPO_ROOT / "src" / "cds_mildoc" / "rule_packs"
    shipped_packs = {path.name for path in pack_dir.glob("*.yaml")}
    assert shipped_packs == set(BUILTIN_PACK_FILES)

    public_sources = {(ref["title"], ref["url"]) for ref in AUTHORITIES.values()}
    offenders: list[str] = []
    for record in load_builtin_rule_packs().records.values():
        source_key = (record.source.title, record.source.url)
        if source_key not in public_sources:
            offenders.append(f"{record.rule_id}: {record.source.title} ({record.source.url})")

    assert not offenders, "Rule packs cite non-public or unknown sources:\n" + "\n".join(offenders)

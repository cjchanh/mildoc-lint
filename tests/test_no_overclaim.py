"""Static check on repository Markdown for unsupported compliance claims.

The repository must not assert capabilities the code does not have. This test
enforces a banned-phrase list across README and ``docs/`` Markdown files.
Files that intentionally enumerate banned phrases for documentation (the
release checklist, the contributor guide, and the claims map) are excluded.
"""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

BANNED_PHRASES = [
    "DoD approved",
    "DoD certified",
    "CMMC compliant",
    "CMMC certified",
    "RMF ready",
    "RMF certified",
    "NIST 800-171 certified",
    "full 30-item checklist",
    "CY26Q2 checklist",
]

# Phrases that are only banned outside of negation/disclaimer context.
# We treat exact bare phrases as banned; the docs disclaim by writing things like
# "does not certify" or "is not a CMMC certification", which avoid the bare claim form.
CASE_INSENSITIVE_BANNED_BARE = [
    " certifies ",
    " certifies\n",
    " certifies.",
]


# RELEASE_CHECKLIST.md, CONTRIBUTING.md, and CLAIMS_MAP.md document what is
# banned, so they intentionally enumerate banned phrases. Exclude them.
EXCLUDE = {
    "docs/RELEASE_CHECKLIST.md",
    "CONTRIBUTING.md",
    "docs/CLAIMS_MAP.md",
}


def _markdown_files() -> list[Path]:
    files: list[Path] = []
    files.append(REPO_ROOT / "README.md")
    files.append(REPO_ROOT / "ROADMAP.md")
    files.append(REPO_ROOT / "SECURITY.md")
    files.append(REPO_ROOT / "THREAT_MODEL.md")
    docs_dir = REPO_ROOT / "docs"
    if docs_dir.exists():
        files.extend(sorted(docs_dir.rglob("*.md")))
    out: list[Path] = []
    for f in files:
        if not f.exists():
            continue
        rel = f.relative_to(REPO_ROOT).as_posix()
        if rel in EXCLUDE:
            continue
        out.append(f)
    return out


def test_no_banned_phrases_in_repo_markdown() -> None:
    offenders: list[str] = []
    for md in _markdown_files():
        text = md.read_text(encoding="utf-8")
        for phrase in BANNED_PHRASES:
            if phrase.lower() in text.lower():
                offenders.append(f"{md.relative_to(REPO_ROOT)}: contains banned phrase '{phrase}'")
    assert not offenders, "Banned compliance claims found:\n" + "\n".join(offenders)


def test_no_bare_certifies_in_repo_markdown() -> None:
    offenders: list[str] = []
    for md in _markdown_files():
        text = md.read_text(encoding="utf-8").lower()
        for phrase in CASE_INSENSITIVE_BANNED_BARE:
            if phrase in text:
                offenders.append(f"{md.relative_to(REPO_ROOT)}: contains bare '{phrase.strip()}'")
    assert not offenders, (
        "Bare certification verb found (use 'does not certify' or rephrase):\n"
        + "\n".join(offenders)
    )

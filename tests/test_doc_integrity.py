"""Regression test for generated-prose corruption.

Scans repository Markdown and Python sources for known textual-corruption
fragments. These fragments would not appear in clean prose; their presence
indicates a bad sed substitution, a copy-paste line-wrap error, or a partial
edit that left the document with broken sentences.
"""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

# Literal substrings that should never appear in clean prose.
# Each fragment is calibrated to detect the broken form WITHOUT matching the
# legitimate compound word it was originally truncated from. For example, we
# match " ing-authority " (with leading space) so we catch the corruption form
# but not "designating-authority" which has no space before "ing-authority".
CORRUPTION_FRAGMENTS = [
    "They ing-authority",         # explicit corruption form (sentence-start)
    " ing-authority call",        # space-isolated truncation
    " ing-authority decision",    # space-isolated truncation
    "tha s ",                     # mid-word break of "that"
    "tha t ",                     # spaced mid-word break of "that"
    "read round the",             # truncation of "read as ... ground the"
    "compliance claims.at ",      # docstring-mash of "claims." + "Static check that"
    "compliance claims. at ",     # space-separated mash variant
    "Markd own",                  # broken word "Markdown"
    "se parately",                # broken "separately"
    "eparately) f check",         # mash of "separately)" + "ruff check"
    "f check . passes",           # truncation of "ruff check . passes"
    " orders tha s",              # broken "orders that"
    "the code.\n\n",              # truncated standalone capability claim if it appears as paragraph
]

SCAN_GLOBS = [
    "README.md",
    "INTENT.md",
    "ROADMAP.md",
    "SECURITY.md",
    "THREAT_MODEL.md",
    "CONTRIBUTING.md",
]


def _scanned_files() -> list[Path]:
    files: list[Path] = []
    for rel in SCAN_GLOBS:
        p = REPO_ROOT / rel
        if p.exists():
            files.append(p)
    docs_dir = REPO_ROOT / "docs"
    if docs_dir.exists():
        files.extend(sorted(docs_dir.rglob("*.md")))
    tests_dir = REPO_ROOT / "tests"
    if tests_dir.exists():
        files.extend(sorted(tests_dir.rglob("*.py")))
    return files


def test_no_corruption_fragments_in_repo() -> None:
    self_path = Path(__file__).resolve()
    offenders: list[str] = []
    for f in _scanned_files():
        if f.resolve() == self_path:
            # This test enumerates the corruption fragments as data.
            # Skip self to avoid the test matching its own banned-phrase list.
            continue
        text = f.read_text(encoding="utf-8")
        for fragment in CORRUPTION_FRAGMENTS:
            if fragment in text:
                offenders.append(
                    f"{f.relative_to(REPO_ROOT)}: contains corruption fragment {fragment!r}"
                )
    assert not offenders, (
        "Generated-prose corruption fragments detected:\n" + "\n".join(offenders)
    )


def test_release_checklist_version_matches_pyproject() -> None:
    """Catch stale version references in the release checklist."""
    pyproject = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    # Extract the version line (single source of truth)
    version = None
    for line in pyproject.splitlines():
        line = line.strip()
        if line.startswith("version = "):
            version = line.split("=", 1)[1].strip().strip('"').strip("'")
            break
    assert version, "could not parse version from pyproject.toml"

    checklist = REPO_ROOT / "docs" / "RELEASE_CHECKLIST.md"
    if not checklist.exists():
        return  # checklist optional
    text = checklist.read_text(encoding="utf-8")
    expected = f"mildoc-lint {version}"
    assert expected in text, (
        f"docs/RELEASE_CHECKLIST.md does not reference current version {expected!r}"
    )

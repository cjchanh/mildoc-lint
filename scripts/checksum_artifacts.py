#!/usr/bin/env python3
"""Generate SHA-256 checksums for files in an artifact directory."""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

CHECKSUM_FILE = "SHA256SUMS"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _iter_artifact_files(root: Path) -> list[Path]:
    return sorted(
        p
        for p in root.iterdir()
        if p.is_file()
        and p.name != CHECKSUM_FILE
        and p.name != ".DS_Store"
    )


def write_checksums(root: Path) -> Path:
    if not root.exists() or not root.is_dir():
        raise FileNotFoundError(f"artifact directory does not exist: {root}")

    files = _iter_artifact_files(root)
    if not files:
        raise ValueError(f"artifact directory is empty: {root}")

    lines = []
    for path in files:
        rel = path.relative_to(root).as_posix()
        lines.append(f"{_sha256(path)}  {rel}")

    out = root / CHECKSUM_FILE
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Write SHA256SUMS for artifact files.")
    parser.add_argument("artifact_dir", help="directory containing artifact files")
    args = parser.parse_args()

    out = write_checksums(Path(args.artifact_dir).resolve())
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
